from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, HttpUrl


class AccessStatus(str, Enum):
    GREEN = "green"
    YELLOW = "yellow"
    RED = "red"
    UNKNOWN = "unknown"


class CheckStage(str, Enum):
    CREATED = "created"
    RESOLVING_PLACE = "resolving_place"
    SCRAPING_PUBLIC_WEB = "scraping_public_web"
    EXTRACTING_EVIDENCE = "extracting_evidence"
    SCORING_EVIDENCE = "scoring_evidence"
    WARMING_VOICE_AGENT = "warming_voice_agent"
    CALLING_VENUE = "calling_venue"
    PARSING_CALL = "parsing_call"
    GENERATING_REPORT = "generating_report"
    PUBLISHED = "published"
    FAILED = "failed"


class AccessNeeds(BaseModel):
    step_free_entrance: bool = True
    accessible_restroom: bool = True
    wheelchair_seating_or_path: bool = True
    avoid_temporary_blockers: bool = True
    notes: str | None = None


class PlaceInput(BaseModel):
    query: str
    address: str | None = None
    phone: str | None = None
    website: str | None = None
    latitude: float | None = None
    longitude: float | None = None


class Place(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    name: str
    address: str | None = None
    phone: str | None = None
    website: str | None = None
    latitude: float | None = None
    longitude: float | None = None


EvidenceSource = Literal["web", "review", "photo", "official", "call", "community", "map"]
EvidenceFeature = Literal[
    "entrance",
    "restroom",
    "seating",
    "route",
    "temporary_blocker",
    "hours",
    "unknown",
]
EvidencePolarity = Literal["supports_access", "contradicts_access", "unknown"]


class EvidenceItem(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    source_type: EvidenceSource
    source_url: str | None = None
    source_timestamp: datetime | None = None
    collected_at: datetime = Field(default_factory=datetime.utcnow)
    title: str | None = None
    claim: str
    feature: EvidenceFeature
    polarity: EvidencePolarity
    confidence: float = Field(ge=0.0, le=1.0)
    image_url: str | None = None
    raw: dict[str, Any] = Field(default_factory=dict)


TranscriptSpeaker = Literal["buddy", "venue", "system"]


class TranscriptTurn(BaseModel):
    speaker: TranscriptSpeaker
    text: str
    started_at: datetime | None = None
    ended_at: datetime | None = None
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)


class ExtractedCallFacts(BaseModel):
    step_free_entrance: Literal["yes", "no", "unknown"] = "unknown"
    accessible_restroom: Literal["yes", "no", "unknown"] = "unknown"
    wheelchair_seating_or_path: Literal["yes", "no", "unknown"] = "unknown"
    temporary_blockers: list[str] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    notes: str = ""
    needs_followup: bool = False


class CallSession(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    check_id: UUID
    to_phone: str
    from_phone: str | None = None
    provider: Literal["twilio", "agentphone"] = "twilio"
    status: Literal["pending", "warming", "in_progress", "completed", "failed"] = "pending"
    transcript: list[TranscriptTurn] = Field(default_factory=list)
    conversation_summary: str | None = None
    extracted_facts: ExtractedCallFacts = Field(default_factory=ExtractedCallFacts)
    recording_url: str | None = None
    started_at: datetime | None = None
    ended_at: datetime | None = None


class TimelineEvent(BaseModel):
    stage: CheckStage
    message: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = Field(default_factory=dict)


class AccessCheckCreate(BaseModel):
    place: PlaceInput
    needs: AccessNeeds = Field(default_factory=AccessNeeds)
    requested_for: datetime | None = None


class MissingFact(BaseModel):
    feature: EvidenceFeature
    question: str
    reason: str
    critical: bool = True


class EvidenceAnalysis(BaseModel):
    enough_evidence: bool
    missing_facts: list[MissingFact] = Field(default_factory=list)
    evidence: list[EvidenceItem] = Field(default_factory=list)
    preliminary_status: AccessStatus = AccessStatus.UNKNOWN
    preliminary_summary: str = ""


class FinalReport(BaseModel):
    status: AccessStatus
    summary: str
    recommendation: str
    confirmed_facts: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    unknowns: list[str] = Field(default_factory=list)
    evidence_ids: list[UUID] = Field(default_factory=list)
    evidence: list[EvidenceItem] = Field(default_factory=list)
    voice_conversation_summary: str | None = None
    voice_transcript: list[TranscriptTurn] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)
    expires_at: datetime
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    openui_payload: dict[str, Any] | None = None


class CommunityReport(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    check_id: UUID
    place: Place
    status: AccessStatus
    public_summary: str
    evidence_summary: str
    voice_conversation_summary: str | None = None
    expires_at: datetime
    created_at: datetime = Field(default_factory=datetime.utcnow)


class AccessCheck(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    place: Place
    needs: AccessNeeds
    stage: CheckStage = CheckStage.CREATED
    timeline: list[TimelineEvent] = Field(default_factory=list)
    evidence: list[EvidenceItem] = Field(default_factory=list)
    analysis: EvidenceAnalysis | None = None
    call_session: CallSession | None = None
    final_report: FinalReport | None = None
    community_report: CommunityReport | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class VoiceWarmupRequest(BaseModel):
    check_id: UUID
    system_prompt: str
    models: dict[str, str]


class VoiceWarmupResponse(BaseModel):
    ready: bool
    stt_loaded: bool
    llm_loaded: bool
    tts_loaded: bool
    message: str


class OpenUiRenderRequest(BaseModel):
    report: FinalReport
    place: Place
    target: Literal["react-native"] = "react-native"
