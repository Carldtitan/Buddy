from __future__ import annotations

from buddy.contracts.buddy_contracts import (
    AccessCheck,
    AccessCheckCreate,
    CallSession,
    CheckStage,
    CommunityReport,
    EvidenceAnalysis,
    Place,
    TimelineEvent,
)

from .bright_data import BrightDataCollector
from .config import Settings
from .flash import RunpodFlashClient
from .storage import InMemoryStore
from .twilio import TwilioCallOrchestrator


class BuddyOrchestrator:
    def __init__(self, settings: Settings, store: InMemoryStore) -> None:
        self._settings = settings
        self._store = store
        self._bright_data = BrightDataCollector(settings)
        self._flash = RunpodFlashClient(settings)
        self._twilio = TwilioCallOrchestrator(settings)

    def create_check(self, payload: AccessCheckCreate) -> AccessCheck:
        place = Place(
            name=payload.place.query,
            address=payload.place.address,
            phone=payload.place.phone,
            website=payload.place.website,
            latitude=payload.place.latitude,
            longitude=payload.place.longitude,
        )
        check = AccessCheck(place=place, needs=payload.needs)
        self._event(check, CheckStage.CREATED, "Accessibility check created.")
        self._store.save_check(check)
        return check

    def collect_public_web(self, check: AccessCheck) -> AccessCheck:
        self._event(check, CheckStage.SCRAPING_PUBLIC_WEB, "Collecting public web evidence.")
        check.evidence.extend(self._bright_data.collect(check.place))
        self._store.save_check(check)
        return check

    def analyze_evidence(self, check: AccessCheck) -> EvidenceAnalysis:
        self._event(check, CheckStage.SCORING_EVIDENCE, "Scoring accessibility evidence.")
        check.analysis = self._flash.analyze(check.place, check.evidence)
        self._store.save_check(check)
        return check.analysis

    def start_call(self, check: AccessCheck) -> CallSession:
        self._event(check, CheckStage.WARMING_VOICE_AGENT, "Preparing voice call.")
        session = check.call_session or CallSession(check_id=check.id, to_phone="")
        check.call_session = self._twilio.start_call(session, check.place.phone)
        self._event(check, CheckStage.CALLING_VENUE, "Venue call orchestration updated.")
        self._store.save_check(check)
        return check.call_session

    def finalize(self, check: AccessCheck) -> AccessCheck:
        if check.analysis is None:
            self.analyze_evidence(check)
        voice_summary = check.call_session.conversation_summary if check.call_session else None
        transcript = check.call_session.transcript if check.call_session else []
        self._event(check, CheckStage.GENERATING_REPORT, "Generating final report.")
        check.final_report = self._flash.report(check.place, check.analysis, voice_summary, transcript)
        check.community_report = CommunityReport(
            check_id=check.id,
            place=check.place,
            status=check.final_report.status,
            public_summary=check.final_report.summary,
            evidence_summary=check.final_report.recommendation,
            voice_conversation_summary=check.final_report.voice_conversation_summary,
            expires_at=check.final_report.expires_at,
        )
        self._store.save_community_report(check.community_report)
        self._event(check, CheckStage.PUBLISHED, "Final report published.")
        self._store.save_check(check)
        return check

    def run_default_flow(self, payload: AccessCheckCreate) -> AccessCheck:
        check = self.create_check(payload)
        self.collect_public_web(check)
        analysis = self.analyze_evidence(check)
        if not analysis.enough_evidence:
            self.start_call(check)
        return self.finalize(check)

    def _event(
        self,
        check: AccessCheck,
        stage: CheckStage,
        message: str,
        metadata: dict | None = None,
    ) -> None:
        check.stage = stage
        check.timeline.append(TimelineEvent(stage=stage, message=message, metadata=metadata or {}))

