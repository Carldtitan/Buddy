# Architecture

Buddy is organized around shared contracts first. Each service should read and write the models in `buddy/contracts/buddy_contracts.py` so mock services can be swapped for real providers without changing mobile UI code.

## Components

Mobile app:

- Creates access checks from a venue query, address, phone, website, and access needs.
- Shows timeline stages from `AccessCheck.timeline`.
- Renders `FinalReport` and optional `CommunityReport`.

Backend API:

- Owns orchestration, persistence, provider clients, and safety checks.
- Resolves places through Mapbox.
- Collects public search evidence through Bright Data SERP and page evidence through Bright Data Browser API with Playwright.
- Sends evidence and missing-fact prompts to Runpod Flash reasoning.
- Warms and coordinates the Runpod voice worker before Twilio call handoff.
- Saves transcripts, extracted facts, evidence, reports, and community reports in Supabase.

Runpod Flash reasoning endpoint:

- Receives place, needs, and evidence.
- Produces `EvidenceAnalysis`, missing facts, preliminary status, and report inputs.
- Can generate concise report summaries and recommendations.

Runpod voice worker:

- Loads STT, voice LLM, and TTS models.
- Accepts `VoiceWarmupRequest`.
- Handles low-latency venue conversation state during Twilio calls.
- Returns transcript turns and `ExtractedCallFacts`.

Twilio:

- Places outbound calls.
- Sends voice and status webhooks to the backend.
- Streams call media to the voice worker websocket at `/twilio-media`.
- Must route local/staging calls to `BUDDY_TEST_PHONE_NUMBER` while real calls are disabled.

Bright Data:

- Uses SERP API for discovery.
- Uses Browser API Playwright for official page, review, and photo evidence collection.
- Evidence is normalized into `EvidenceItem`.

Supabase:

- Stores checks, places, evidence, calls, reports, and public community report records.
- `SUPABASE_PUBLISHABLE_KEY` is browser/mobile safe only for reads allowed by RLS.
- `SUPABASE_SECRET_KEY` and `DATABASE_URL` are server-only.

Local renderer:

- Renders `FinalReport.openui_payload` into a React Native target when needed.
- Should be treated as a presentation service, not the source of truth.
- Replaces paid OpenUI for this hack build.

## Data Flow

1. Client posts `AccessCheckCreate`.
2. Backend creates `AccessCheck` at `created`.
3. Backend moves through `resolving_place`, `scraping_public_web`, `extracting_evidence`, and `scoring_evidence`.
4. Reasoning returns `EvidenceAnalysis`.
5. If evidence is enough, backend skips calling and generates the report.
6. If critical facts are missing, backend moves to `warming_voice_agent`.
7. Voice worker returns `VoiceWarmupResponse(ready=true)` from `RUNPOD_VOICE_WORKER_WARMUP_URL`.
8. Backend moves to `calling_venue` and asks Twilio to call either the venue or the test phone, depending on safety settings.
9. Backend receives transcript and facts, moves through `parsing_call` and `generating_report`.
10. Backend publishes `FinalReport` and optional `CommunityReport`, then moves to `published`.

## Stage Ownership

- `created`: backend.
- `resolving_place`: backend Mapbox client.
- `scraping_public_web`: backend Bright Data SERP and Browser API Playwright clients.
- `extracting_evidence`: backend evidence normalizer.
- `scoring_evidence`: Runpod reasoning endpoint.
- `warming_voice_agent`: backend plus Runpod voice worker.
- `calling_venue`: backend plus Twilio plus voice worker.
- `parsing_call`: voice worker or reasoning endpoint.
- `generating_report`: reasoning endpoint and backend formatter.
- `published`: backend persistence and API.
- `failed`: backend error handling.

## Safety Boundaries

Call safety belongs in backend orchestration, not only in the UI. Before every outbound call:

- Check `ALLOW_REAL_VENUE_CALLS`.
- If false, replace the destination with `BUDDY_TEST_PHONE_NUMBER`.
- Log the requested venue phone separately from the actual dialed number.
- Add a timeline event that identifies test-call mode without exposing private numbers in public reports.

Public reports should avoid publishing raw phone numbers, private call recordings, or unredacted transcript details that are not needed for accessibility confirmation.
