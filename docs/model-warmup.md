# Model Warmup Flow

The voice path should warm models before Twilio dials. This prevents a venue employee from waiting while STT, LLM, or TTS models load.

## Contract

Warmup request:

```json
{
  "check_id": "00000000-0000-0000-0000-000000000000",
  "system_prompt": "You are Buddy, calling to confirm accessibility facts for a visitor.",
  "models": {
    "stt": "configured-stt-model",
    "llm": "configured-voice-llm",
    "tts": "configured-tts-model"
  }
}
```

Warmup response:

```json
{
  "ready": true,
  "stt_loaded": true,
  "llm_loaded": true,
  "tts_loaded": true,
  "message": "Voice worker is ready"
}
```

These map to `VoiceWarmupRequest` and `VoiceWarmupResponse` in `buddy/contracts/buddy_contracts.py`.

## Sequence

1. Backend decides a call is needed from `EvidenceAnalysis.missing_facts`.
2. Backend builds a concise system prompt from venue name, access needs, missing facts, and safety constraints.
3. Backend sends `VoiceWarmupRequest` to `RUNPOD_VOICE_WORKER_WARMUP_URL`.
4. Voice worker loads or verifies STT, voice LLM, and TTS models.
5. Voice worker returns `ready=true` only when all required models are loaded.
6. Backend creates a `CallSession` with status `warming`, then `pending`.
7. Backend checks call safety:
   - if `ALLOW_REAL_VENUE_CALLS=false`, set `to_phone=BUDDY_TEST_PHONE_NUMBER`;
   - if true, use the resolved venue phone only after production gates pass.
8. Backend asks Twilio to place the call.
9. Voice worker streams or receives call turns and returns transcript plus extracted facts.
10. Backend persists facts and generates the final report.

## Timeout Behavior

Use the backend request timeout for `RUNPOD_VOICE_WORKER_WARMUP_URL` as the hard limit for model warmup. The current backend warmup call uses a 180 second timeout.

If warmup times out:

- Do not place the Twilio call.
- Mark the timeline with `warming_voice_agent` failure details.
- Continue with a report that clearly lists missing facts, or return a retryable status to the client.

If one model fails to load:

- Return `ready=false`.
- Set the failed model flag to false.
- Put a human-readable reason in `message`.

## Prompt Shape

The warmup prompt should be short and operational:

- Identify Buddy.
- State that the call is only to confirm accessibility facts.
- Include the missing facts as questions.
- Instruct the agent not to ask for unrelated business information.
- Instruct the agent to end politely after facts are confirmed or unavailable.

Example:

```text
You are Buddy, calling to confirm accessibility before a visitor arrives today.
Ask whether there is a step-free entrance, whether customers can use an accessible restroom,
and whether there is a wheelchair-usable route to seating. Do not ask unrelated questions.
If the person cannot answer, thank them and end the call.
```

## Local Test Flow

Keep real calls disabled:

```bash
ALLOW_REAL_VENUE_CALLS=false
BUDDY_TEST_PHONE_NUMBER=+15555550100
```

Run the local voice worker:

```bash
cd /root/runpod-hack/buddy/runpod_voice_worker
python3 -m pip install -r requirements.txt
python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 9000
```

Warm the local worker:

```bash
curl -sS -X POST http://localhost:9000/warmup \
  -H 'Content-Type: application/json' \
  -d '{"check_id":"local-check","models":{"stt":"Systran/faster-whisper-small","llm":"Qwen/Qwen2.5-1.5B-Instruct","tts":"hexgrad/Kokoro-82M"}}'
```

Then exercise a check whose venue payload contains a fake or real-looking venue number. The call orchestration should still dial only `BUDDY_TEST_PHONE_NUMBER`.

Expected timeline:

- `created`
- `resolving_place`
- `scraping_public_web`
- `extracting_evidence`
- `scoring_evidence`
- `warming_voice_agent`
- `calling_venue`
- `parsing_call`
- `generating_report`
- `published`
