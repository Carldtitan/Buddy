# Environment Setup

Copy `buddy/.env.example` to `buddy/.env` and fill in the values below. Do not commit real secrets.

```bash
cd /root/runpod-hack
cp buddy/.env.example buddy/.env
```

## Required Safety Values

`ALLOW_REAL_VENUE_CALLS=false`

Real venue calls are disabled by default. Backend call orchestration must ignore venue phone numbers and send outbound calls to `BUDDY_TEST_PHONE_NUMBER` while this value is false.

`BUDDY_TEST_PHONE_NUMBER`

Use a verified phone that the team controls. For Twilio trial accounts, this must also be a verified caller ID in Twilio Console > Phone Numbers > Manage > Verified Caller IDs.

## App URLs

Local defaults:

- `PUBLIC_APP_URL=http://localhost:3000`
- `BACKEND_URL=http://localhost:8000`
- `UI_RENDERER=local`

Hosted `BACKEND_URL`, Twilio webhook URLs, Runpod worker URLs, and mobile/public app URLs are generated later when tunnels or deployments exist. Leave those values blank or local until the service URL is known.

## Bright Data

Use Bright Data SERP API for search result discovery and Bright Data Browser API with Playwright for page evidence collection.

Dashboard locations:

- API key: Bright Data Dashboard > Account settings > API tokens.
- SERP zone: Bright Data Dashboard > Proxies & Scraping Infrastructure > SERP API.
- Browser API endpoint: Bright Data Dashboard > Proxies & Scraping Infrastructure > Browser API.

Variables:

- `BRIGHT_DATA_API_KEY`: Bright Data API key.
- `BRIGHT_DATA_SERP_ZONE`: SERP API zone name.
- `BRIGHT_DATA_BROWSER_API_TYPE`: keep `playwright`.
- `BRIGHT_DATA_BROWSER_PLAYWRIGHT_WS_URL`: Playwright websocket URL from the Browser API zone.

## Mapbox

Use Mapbox for place resolution.

Dashboard locations:

- Access token: Mapbox Dashboard > Tokens.
- Usage and limits: Mapbox Dashboard > Statistics.

Variables:

- `MAPBOX_ACCESS_TOKEN`: Mapbox access token for place lookup.

## Runpod

Use Runpod for the Flash reasoning service and the warmable voice worker.

Dashboard locations:

- API key: Runpod Console > Settings > API Keys.
- Serverless endpoints and generated URLs: Runpod Console > Serverless > Endpoints.
- Endpoint logs: Runpod Console > Serverless > Endpoints > select endpoint > Logs.

Variables:

- `RUNPOD_API_KEY`: Runpod API key.
- `RUNPOD_FLASH_BASE_URL`: generated Flash service base URL after deploy.
- `RUNPOD_FLASH_APP_NAME`: usually `buddy`.
- `RUNPOD_FLASH_ENV`: usually `production` for the deployed Flash app.
- `RUNPOD_VOICE_WORKER_BASE_URL`: generated voice worker HTTP base URL.
- `RUNPOD_VOICE_WORKER_WS_URL`: generated voice worker websocket base URL.
- `RUNPOD_VOICE_WORKER_HEALTH_URL`: `${RUNPOD_VOICE_WORKER_BASE_URL}/health` once the base URL exists.
- `RUNPOD_VOICE_WORKER_WARMUP_URL`: `${RUNPOD_VOICE_WORKER_BASE_URL}/warmup` once the base URL exists.
- `RUNPOD_VOICE_WORKER_AUTH_TOKEN`: optional bearer token if the worker is protected.

## Twilio

Use Twilio for outbound voice calls and webhooks.

Dashboard locations:

- Account SID and Auth Token: Twilio Console > Account > API keys & tokens.
- Twilio phone number: Twilio Console > Phone Numbers > Manage > Active numbers.
- Trial verified recipient numbers: Twilio Console > Phone Numbers > Manage > Verified Caller IDs.
- Voice webhook configuration: Twilio Console > Phone Numbers > Manage > Active numbers > select number > Voice Configuration.
- Call logs: Twilio Console > Monitor > Logs > Calls.

Variables:

- `TWILIO_ACCOUNT_SID`: project Account SID.
- `TWILIO_AUTH_TOKEN`: project Auth Token or API key secret used by the server.
- `TWILIO_FROM_PHONE_NUMBER`: Twilio-owned number for outbound calls.
- `TWILIO_VOICE_WEBHOOK_URL`: public URL for `POST /api/twilio/voice`.
- `TWILIO_STATUS_CALLBACK_URL`: public URL for `POST /api/twilio/status`.
- `TWILIO_MEDIA_STREAM_WS_URL`: websocket URL for the voice worker `/twilio-media` endpoint.

For local webhook testing, expose the backend API with a tunnel such as `ngrok http 8000`, then set:

- `TWILIO_VOICE_WEBHOOK_URL=https://<tunnel-host>/api/twilio/voice`
- `TWILIO_STATUS_CALLBACK_URL=https://<tunnel-host>/api/twilio/status`

If the voice worker is local, expose it with a websocket-capable tunnel and set `TWILIO_MEDIA_STREAM_WS_URL=wss://<worker-tunnel-host>/twilio-media`.

## Supabase

Use Supabase for persisted checks, evidence, reports, and community report records once persistence is wired in.

Dashboard locations:

- Project URL and API keys: Supabase Dashboard > select project > Project Settings > API.
- Database password and pooled connection strings: Supabase Dashboard > select project > Project Settings > Database.
- SQL editor: Supabase Dashboard > select project > SQL Editor.
- Table editor: Supabase Dashboard > select project > Table Editor.
- Row Level Security policies: Supabase Dashboard > select project > Authentication > Policies or Table Editor > select table > RLS policies.

Variables:

- `SUPABASE_URL`: project URL.
- `SUPABASE_PUBLISHABLE_KEY`: browser/mobile-safe publishable key for reads allowed by RLS.
- `SUPABASE_SECRET_KEY`: backend-only secret key for writes and admin tasks.
- `DATABASE_URL`: database connection string for migrations or direct server access.

Keep `SUPABASE_SECRET_KEY` and `DATABASE_URL` out of mobile apps and frontend bundles.

## Local Renderer

Do not use paid OpenUI for the hack build. Keep `UI_RENDERER=local` and use the local renderer path for `FinalReport.openui_payload`.

No OpenUI API key or hosted OpenUI service URL is required.

## Local Commands

Install backend requirements:

```bash
cd /root/runpod-hack
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r buddy/backend/requirements.txt
```

Run the backend:

```bash
cd /root/runpod-hack
source .venv/bin/activate
PYTHONPATH=/root/runpod-hack python3 -m uvicorn buddy.backend.app.main:app --reload --host 0.0.0.0 --port 8000
```

Run the voice worker:

```bash
cd /root/runpod-hack/buddy/runpod_voice_worker
python3 -m pip install -r requirements.txt
python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 9000
```

Warm the local voice worker:

```bash
curl -sS -X POST http://localhost:9000/warmup \
  -H 'Content-Type: application/json' \
  -d '{"check_id":"local-check","models":{"stt":"Systran/faster-whisper-small","llm":"Qwen/Qwen2.5-1.5B-Instruct","tts":"hexgrad/Kokoro-82M"}}'
```

Expose local backend webhooks:

```bash
ngrok http 8000
```

Run tests:

```bash
cd /root/runpod-hack
source .venv/bin/activate
PYTHONPATH=/root/runpod-hack python3 -m unittest discover -s buddy/backend/tests
PYTHONPATH=/root/runpod-hack python3 -m compileall buddy/contracts
```
