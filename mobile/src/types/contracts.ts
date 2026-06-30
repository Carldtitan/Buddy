export type UUID = string;
export type IsoDate = string;

export type AccessStatus = "green" | "yellow" | "red" | "unknown";

export type CheckStage =
  | "created"
  | "resolving_place"
  | "scraping_public_web"
  | "extracting_evidence"
  | "scoring_evidence"
  | "warming_voice_agent"
  | "calling_venue"
  | "parsing_call"
  | "generating_report"
  | "published"
  | "failed";

export type EvidenceSource =
  | "web"
  | "review"
  | "photo"
  | "official"
  | "call"
  | "community"
  | "map";

export type EvidenceFeature =
  | "entrance"
  | "restroom"
  | "seating"
  | "route"
  | "temporary_blocker"
  | "hours"
  | "unknown";

export type EvidencePolarity = "supports_access" | "contradicts_access" | "unknown";
export type TranscriptSpeaker = "buddy" | "venue" | "system";

export interface AccessNeeds {
  step_free_entrance: boolean;
  accessible_restroom: boolean;
  wheelchair_seating_or_path: boolean;
  avoid_temporary_blockers: boolean;
  notes?: string | null;
}

export interface PlaceInput {
  query: string;
  address?: string | null;
  phone?: string | null;
  website?: string | null;
  latitude?: number | null;
  longitude?: number | null;
}

export interface Place {
  id: UUID;
  name: string;
  address?: string | null;
  phone?: string | null;
  website?: string | null;
  latitude?: number | null;
  longitude?: number | null;
}

export interface EvidenceItem {
  id: UUID;
  source_type: EvidenceSource;
  source_url?: string | null;
  source_timestamp?: IsoDate | null;
  collected_at: IsoDate;
  title?: string | null;
  claim: string;
  feature: EvidenceFeature;
  polarity: EvidencePolarity;
  confidence: number;
  image_url?: string | null;
  raw: Record<string, unknown>;
}

export interface TranscriptTurn {
  speaker: TranscriptSpeaker;
  text: string;
  started_at?: IsoDate | null;
  ended_at?: IsoDate | null;
  confidence?: number | null;
}

export interface ExtractedCallFacts {
  step_free_entrance: "yes" | "no" | "unknown";
  accessible_restroom: "yes" | "no" | "unknown";
  wheelchair_seating_or_path: "yes" | "no" | "unknown";
  temporary_blockers: string[];
  confidence: number;
  notes: string;
  needs_followup: boolean;
}

export interface CallSession {
  id: UUID;
  check_id: UUID;
  to_phone: string;
  from_phone?: string | null;
  provider: "twilio" | "agentphone";
  status: "pending" | "warming" | "in_progress" | "completed" | "failed";
  transcript: TranscriptTurn[];
  conversation_summary?: string | null;
  extracted_facts: ExtractedCallFacts;
  recording_url?: string | null;
  started_at?: IsoDate | null;
  ended_at?: IsoDate | null;
}

export interface TimelineEvent {
  stage: CheckStage;
  message: string;
  created_at: IsoDate;
  metadata: Record<string, unknown>;
}

export interface AccessCheckCreate {
  place: PlaceInput;
  needs: AccessNeeds;
  requested_for?: IsoDate | null;
}

export interface MissingFact {
  feature: EvidenceFeature;
  question: string;
  reason: string;
  critical: boolean;
}

export interface EvidenceAnalysis {
  enough_evidence: boolean;
  missing_facts: MissingFact[];
  evidence: EvidenceItem[];
  preliminary_status: AccessStatus;
  preliminary_summary: string;
}

export interface RenderPayloadSection {
  title: string;
  items: string[];
}

export interface OpenUiPayload {
  target?: "react-native" | string;
  component?: "AccessibilityReport" | string;
  props?: {
    place?: Place | PlaceInput;
    status?: AccessStatus;
    summary?: string;
    recommendation?: string;
    sections?: RenderPayloadSection[];
    confidence?: number;
    expiresAt?: IsoDate;
    [key: string]: unknown;
  };
  [key: string]: unknown;
}

export interface FinalReport {
  status: AccessStatus;
  summary: string;
  recommendation: string;
  confirmed_facts: string[];
  risks: string[];
  unknowns: string[];
  evidence_ids: UUID[];
  evidence: EvidenceItem[];
  voice_conversation_summary?: string | null;
  voice_transcript: TranscriptTurn[];
  confidence: number;
  expires_at: IsoDate;
  generated_at: IsoDate;
  openui_payload?: OpenUiPayload | null;
}

export interface CommunityReport {
  id: UUID;
  check_id: UUID;
  place: Place;
  status: AccessStatus;
  public_summary: string;
  evidence_summary: string;
  voice_conversation_summary?: string | null;
  expires_at: IsoDate;
  created_at: IsoDate;
}

export interface AccessCheck {
  id: UUID;
  place: Place;
  needs: AccessNeeds;
  stage: CheckStage;
  timeline: TimelineEvent[];
  evidence: EvidenceItem[];
  analysis?: EvidenceAnalysis | null;
  call_session?: CallSession | null;
  final_report?: FinalReport | null;
  community_report?: CommunityReport | null;
  created_at: IsoDate;
  updated_at: IsoDate;
}
