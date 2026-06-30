from __future__ import annotations

from datetime import datetime, timedelta

from buddy.contracts.buddy_contracts import (
    AccessStatus,
    EvidenceAnalysis,
    EvidenceItem,
    FinalReport,
    MissingFact,
    Place,
)

from .config import Settings
from .http_client import post_json


class RunpodFlashClient:
    """Wrapper for an already deployed Runpod Flash endpoint.

    This intentionally does not use Runpod lifecycle APIs. Configure
    RUNPOD_FLASH_BASE_URL after deploying the Buddy Flash app if you want the
    backend to call hosted reasoning endpoints. Without it, the backend uses the
    same deterministic local rules so development can proceed safely.
    """

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def analyze(self, place: Place, evidence: list[EvidenceItem]) -> EvidenceAnalysis:
        if self._settings.runpod_flash_base_url:
            response = self._post("analyze", {"place": place.model_dump(mode="json"), "evidence": evidence})
            return EvidenceAnalysis.model_validate(response)
        return local_analyze(evidence)

    def report(
        self,
        place: Place,
        analysis: EvidenceAnalysis,
        voice_summary: str | None,
        transcript: list,
    ) -> FinalReport:
        if self._settings.runpod_flash_base_url:
            response = self._post(
                "report",
                {
                    "place": place.model_dump(mode="json"),
                    "analysis": analysis.model_dump(mode="json"),
                    "voice_summary": voice_summary,
                    "transcript": [turn.model_dump(mode="json") for turn in transcript],
                },
            )
            return FinalReport.model_validate(response)
        return local_report(analysis, voice_summary, transcript)

    def _post(self, task: str, payload: dict) -> dict:
        headers = {}
        if self._settings.runpod_api_key:
            headers["Authorization"] = f"Bearer {self._settings.runpod_api_key}"
        url = f"{self._settings.runpod_flash_base_url.rstrip('/')}/{task}"
        return post_json(
            url,
            {"task": task, "input": payload},
            headers=headers,
            timeout_seconds=60,
        )


def local_analyze(evidence: list[EvidenceItem]) -> EvidenceAnalysis:
    negative = [item for item in evidence if item.polarity == "contradicts_access"]
    positive = [item for item in evidence if item.polarity == "supports_access"]
    known_features = {item.feature for item in positive if item.confidence >= 0.55}
    missing: list[MissingFact] = []
    for feature, question in (
        ("entrance", "Is there an accessible entrance with no barrier for someone with mobility needs?"),
        ("restroom", "Is there an accessible restroom?"),
        ("seating", "Is there accessible interior seating or a navigable path inside?"),
    ):
        if feature not in known_features:
            missing.append(
                MissingFact(
                    feature=feature,
                    question=question,
                    reason="Public evidence did not confidently answer this.",
                    critical=True,
                )
            )

    if negative:
        status = AccessStatus.RED
    elif missing:
        status = AccessStatus.YELLOW if positive else AccessStatus.UNKNOWN
    else:
        status = AccessStatus.GREEN

    return EvidenceAnalysis(
        enough_evidence=len(missing) == 0 and bool(positive),
        missing_facts=missing,
        evidence=evidence,
        preliminary_status=status,
        preliminary_summary=_summary_for(status, len(positive), len(negative), len(missing)),
    )


def local_report(analysis: EvidenceAnalysis, voice_summary: str | None, transcript: list) -> FinalReport:
    status = analysis.preliminary_status
    confirmed = [
        item.claim for item in analysis.evidence if item.polarity == "supports_access" and item.confidence >= 0.55
    ]
    risks = [
        item.claim for item in analysis.evidence if item.polarity == "contradicts_access" and item.confidence >= 0.5
    ]
    unknowns = [fact.question for fact in analysis.missing_facts]
    if voice_summary and status == AccessStatus.UNKNOWN:
        status = AccessStatus.YELLOW

    return FinalReport(
        status=status,
        summary=analysis.preliminary_summary,
        recommendation=_recommendation_for(status),
        confirmed_facts=confirmed,
        risks=risks,
        unknowns=unknowns,
        evidence_ids=[item.id for item in analysis.evidence],
        evidence=analysis.evidence,
        voice_conversation_summary=voice_summary,
        voice_transcript=transcript,
        confidence=_confidence_for(status, analysis),
        expires_at=datetime.utcnow() + timedelta(hours=24),
        openui_payload=None,
    )


def _summary_for(status: AccessStatus, positives: int, negatives: int, missing: int) -> str:
    if status == AccessStatus.GREEN:
        return "Accessibility looks supported by the available evidence."
    if status == AccessStatus.RED:
        return f"{negatives} evidence item(s) indicate an accessibility barrier."
    if status == AccessStatus.YELLOW:
        return f"{positives} supportive item(s), with {missing} important unknown(s)."
    return "Buddy does not yet have enough evidence to judge accessibility."


def _recommendation_for(status: AccessStatus) -> str:
    if status == AccessStatus.GREEN:
        return "Reasonable to visit, while still confirming any day-of needs."
    if status == AccessStatus.RED:
        return "Avoid or call ahead unless the barrier is acceptable for this trip."
    if status == AccessStatus.YELLOW:
        return "Proceed with caution and verify the unknowns before relying on the venue."
    return "Collect more evidence or call the venue before making a plan."


def _confidence_for(status: AccessStatus, analysis: EvidenceAnalysis) -> float:
    if not analysis.evidence:
        return 0.15
    average = sum(item.confidence for item in analysis.evidence) / len(analysis.evidence)
    if status == AccessStatus.UNKNOWN:
        return min(average, 0.4)
    return min(max(average, 0.25), 0.9)
