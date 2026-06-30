# Deployment Notes

Buddy has three hosted surfaces for the hack build: backend API, Runpod Flash reasoning service, and Runpod voice worker. Mobile builds consume the backend API and public Supabase configuration. UI rendering uses the local renderer; do not provision paid OpenUI.

## Environments

Recommended progression:

- `local`: `.env`, local API, local or tunneled voice worker, real venue calls disabled.
- `staging`: hosted API, staging Supabase project, staging Runpod services, real venue calls disabled.
- `production`: production API, production Supabase project, production Runpod services, real venue calls enabled only after signoff.

Keep `ALLOW_REAL_VENUE_CALLS=false` for local and staging. Calls should go to `BUDDY_TEST_PHONE_NUMBER`.

## Backend API

Deploy requirements:

- Python 3.11 or 3.12.
- Install backend requirements from `buddy/backend/requirements.txt`.
- Set all backend secrets in the host secret manager.
- Expose HTTPS endpoints for Twilio webhooks.
- Configure health checks for the API process.

Start command:

```bash
cd /root/runpod-hack
PYTHONPATH=/root/runpod-hack python3 -m uvicorn buddy.backend.app.main:app --host 0.0.0.0 --port ${PORT:-8000}
```

Secrets needed:

- Bright Data API key, SERP zone, and Browser API Playwright websocket URL.
- Mapbox access token.
- Runpod API key and generated service URLs.
- Twilio SID, token, phone number, webhook URLs, and media stream websocket URL.
- Supabase URL, publishable key, secret key, and database URL.
- `UI_RENDERER=local`.

## Generated Service URLs

Fill service URLs after each deploy or tunnel is created:

- `BACKEND_URL`: hosted backend URL.
- `TWILIO_VOICE_WEBHOOK_URL`: `${BACKEND_URL}/api/twilio/voice`.
- `TWILIO_STATUS_CALLBACK_URL`: `${BACKEND_URL}/api/twilio/status`.
- `RUNPOD_FLASH_BASE_URL`: generated Runpod Flash service base URL.
- `RUNPOD_VOICE_WORKER_BASE_URL`: generated Runpod voice worker HTTP URL.
- `RUNPOD_VOICE_WORKER_WS_URL`: generated Runpod voice worker websocket URL.
- `RUNPOD_VOICE_WORKER_HEALTH_URL`: `${RUNPOD_VOICE_WORKER_BASE_URL}/health`.
- `RUNPOD_VOICE_WORKER_WARMUP_URL`: `${RUNPOD_VOICE_WORKER_BASE_URL}/warmup`.
- `TWILIO_MEDIA_STREAM_WS_URL`: `${RUNPOD_VOICE_WORKER_WS_URL}/twilio-media`.

## Twilio Webhooks

Set webhooks on the Twilio number:

- Twilio Console > Phone Numbers > Manage > Active numbers > select number > Voice Configuration.
- Voice webhook: `https://<api-host>/api/twilio/voice`.
- Status callback: `https://<api-host>/api/twilio/status`.
- Method: `POST`.

For local testing, use a tunnel and update the webhook URLs to the tunnel host.

## Supabase

Use separate Supabase projects for staging and production.

Deployment checklist:

- Apply migrations when Supabase persistence lands.
- Enable Row Level Security before exposing client reads.
- Store `SUPABASE_SECRET_KEY` and `DATABASE_URL` only in backend secrets.
- Expose only `SUPABASE_URL` and `SUPABASE_PUBLISHABLE_KEY` to mobile/frontend clients.
- Verify report tables do not expose private transcript or call recording fields through public policies.

Dashboard locations:

- API keys: Supabase Dashboard > Project Settings > API.
- Connection strings: Supabase Dashboard > Project Settings > Database.
- Policies: Supabase Dashboard > Authentication > Policies.

## Runpod Services

Deploy the Flash reasoning service and voice worker separately.

Dashboard locations:

- Create or edit service: Runpod Console > Serverless > Endpoints.
- API key: Runpod Console > Settings > API Keys.
- Logs: Runpod Console > Serverless > Endpoints > select endpoint > Logs.

Deployment checklist:

- Pin model and container versions.
- Set concurrency limits appropriate for call volume.
- Configure idle timeout with the expected warmup cost.
- Run the voice warmup request after deploy.
- Copy generated HTTP and websocket service URLs into backend secrets.

Voice worker local start command:

```bash
cd /root/runpod-hack/buddy/runpod_voice_worker
python3 -m pip install -r requirements.txt
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 9000
```

Voice worker warmup smoke test:

```bash
curl -sS -X POST "${RUNPOD_VOICE_WORKER_WARMUP_URL:-http://localhost:9000/warmup}" \
  -H 'Content-Type: application/json' \
  -d '{"check_id":"deploy-smoke","models":{"stt":"Systran/faster-whisper-small","llm":"Qwen/Qwen2.5-1.5B-Instruct","tts":"hexgrad/Kokoro-82M"}}'
```

## Local Renderer

Set `UI_RENDERER=local`. Do not configure `OPENUI_BASE_URL`, `OPENUI_API_KEY`, or a paid OpenUI service for the hack build.

## Verification Commands

Run tests before deploy:

```bash
cd /root/runpod-hack
source .venv/bin/activate
PYTHONPATH=/root/runpod-hack python3 -m unittest discover -s buddy/backend/tests
PYTHONPATH=/root/runpod-hack python3 -m compileall buddy/contracts
```

Check backend health:

```bash
curl -sS http://localhost:8000/health
```

## Production Gate For Real Calls

Before setting `ALLOW_REAL_VENUE_CALLS=true`:

- Confirm Twilio production account is approved and funded.
- Confirm call copy, consent posture, and opt-out handling.
- Add rate limits and a venue call allowlist or operator approval.
- Verify recordings are disabled unless legally reviewed.
- Verify retries cannot repeatedly call the same venue.
- Run a full staging test where the venue phone is real in the payload but the actual dialed number is `BUDDY_TEST_PHONE_NUMBER`.
