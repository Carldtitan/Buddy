# Buddy Runpod Voice Worker

FastAPI scaffold for Buddy's warmable voice worker.

## Auth

Set `BUDDY_VOICE_WORKER_AUTH_TOKEN`, `RUNPOD_VOICE_WORKER_AUTH_TOKEN`, or `VOICE_WORKER_AUTH_TOKEN` to require auth. HTTP callers can pass `Authorization: Bearer REDACTED, `X-Buddy-Voice-Token`, or `X-Runpod-Auth-Token`; Twilio Media Streams should include `?token=REDACTED or `?auth_token=REDACTED on the websocket URL. `GET /health` remains unauthenticated and reports whether auth is configured.

## Endpoints

- `GET /health` reports STT/LLM/TTS placeholder load state.
- `POST /warmup` loads STT/LLM/TTS placeholders and the system prompt before dialing. TODO hooks are in place for faster-whisper, Qwen, and Kokoro adapters.
- `WS /twilio-media` accepts Twilio Media Streams events and keeps transcripts derived from actual request text/STT results only.
- `POST /transcribe` accepts request audio or explicit text and returns request-derived transcription output.
- `POST /synthesize` returns placeholder encoded audio bytes for the supplied text.
- `POST /reason-next-question` selects the next planned or missing accessibility question.

Transcripts are generated only from request-derived text or future STT results. The placeholders are ready to be swapped for real STT, LLM, and TTS adapters while preserving the warmup contract.
