# Buddy

Buddy is a live accessibility assistant for the Runpod hack.
It takes a plain-English request, finds a place, gathers public evidence, reasons about what that evidence means, optionally calls your phone for verification, and returns a short answer that is easy to scan.

The app is built to feel like a chat product first, with a map shown by default and community reports on a separate page.

## What it does

1. The user types a natural-language request like "check whether the cafe near me has accessible entry and restroom access."
2. The backend resolves the place and gathers public evidence.
3. Bright Data helps fetch search results and page evidence.
4. Runpod hosts the reasoning and the voice worker so the call path can be warmed before dialing.
5. Twilio places the call.
6. The backend returns:
   - a concise conclusion,
   - a short English explanation,
   - the transcript,
   - a summary of the voice conversation,
   - supporting evidence,
   - and a community-ready report.

## Why this is a good use of sponsor tools

This project uses the sponsor tools for real work, not for decoration:

- Bright Data SERP API finds public web evidence quickly.
- Bright Data Browser API with Playwright captures harder-to-reach pages when search snippets are not enough.
- Runpod Flash hosts the reasoning layer that decides what evidence matters.
- Runpod voice worker hosts STT, LLM, and TTS for the phone flow and is warmed before calls to reduce lag.
- Twilio handles the actual phone call.
- Supabase is the persistence layer for checks, reports, and community posts.
- Mapbox powers place resolution and the map view.
- The local renderer turns structured report payloads into a readable mobile UI without needing paid OpenUI.

## Product shape

- `Check` page: the main chat-style flow with a map, the user prompt, evidence, transcript, and result summary.
- `Community` page: public reports, separated so the main task stays focused.
- `Call` flow: hidden behind a confirmation step so the app only calls after the evidence is gathered.

## Safety behavior

Real venue calls are disabled by default.
When `ALLOW_REAL_VENUE_CALLS=false`, Buddy dials `BUDDY_TEST_PHONE_NUMBER` instead of the venue.

That means:

- local testing is safe,
- demo calling can still work,
- and real venue calls only happen when you explicitly enable them.

## Twilio setup

Twilio is the part that most often trips people up.

If Twilio says "upgrade to a full account" during the call, that usually means:

- the account is still in trial mode, or
- the call is going to a number that is not verified for trial usage.

What you need:

1. Use a real Twilio Voice-capable account.
2. Buy or assign a Twilio phone number.
3. Make sure the backend webhooks are public HTTPS endpoints.
4. Make sure the voice worker websocket endpoint is public WSS.
5. If you are still on trial, verify the destination phone number in Twilio Console.
6. Keep `BUDDY_TEST_PHONE_NUMBER` set for safety testing.

The backend should point Twilio at:

- `TWILIO_VOICE_WEBHOOK_URL` for the TwiML response
- `TWILIO_STATUS_CALLBACK_URL` for call status
- `TWILIO_MEDIA_STREAM_WS_URL` for the Twilio Media Streams websocket

If the call cuts early, check Twilio Console > Monitor > Logs > Calls first.
That will tell you whether the failure is account policy, webhook, or stream related.

## Local development

```bash
cd /root/runpod-hack
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r buddy/backend/requirements.txt
cp buddy/.env.example buddy/.env
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

Run tests:

```bash
cd /root/runpod-hack
source .venv/bin/activate
PYTHONPATH=/root/runpod-hack python3 -m unittest discover -s buddy/backend/tests
PYTHONPATH=/root/runpod-hack python3 -m compileall buddy/contracts
```

## Important environment variables

Start with `buddy/.env.example`.

The main groups are:

- Bright Data: `BRIGHT_DATA_API_KEY`, `BRIGHT_DATA_SERP_ZONE`, `BRIGHT_DATA_BROWSER_PLAYWRIGHT_WS_URL`
- Mapbox: `MAPBOX_ACCESS_TOKEN`
- Runpod: `RUNPOD_API_KEY`, `RUNPOD_FLASH_BASE_URL`, `RUNPOD_VOICE_WORKER_BASE_URL`, `RUNPOD_VOICE_WORKER_WS_URL`, `RUNPOD_VOICE_WORKER_WARMUP_URL`
- Twilio: `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_FROM_PHONE_NUMBER`, `TWILIO_VOICE_WEBHOOK_URL`, `TWILIO_STATUS_CALLBACK_URL`, `TWILIO_MEDIA_STREAM_WS_URL`
- Supabase: `SUPABASE_URL`, `SUPABASE_PUBLISHABLE_KEY`, `SUPABASE_SECRET_KEY`, `DATABASE_URL`
- Safety: `ALLOW_REAL_VENUE_CALLS=false`, `BUDDY_TEST_PHONE_NUMBER`

## Repo layout

- `contracts/` shared request and response models
- `backend/` API, orchestration, Bright Data integration, Twilio, storage
- `runpod_voice_worker/` warmable STT/LLM/TTS voice service
- `runpod_llm_worker/` lightweight Runpod reasoning worker
- `mobile/` chat-style frontend with map and community pages
- `flash_app/` Runpod Flash app entrypoint
- `docs/` setup, deployment, and architecture notes

## Status philosophy

Buddy is designed to be useful in the real world, but the safest default is still a controlled demo path.
That is why the app emphasizes:

- natural language input,
- concise summaries,
- evidence instead of wall-of-text,
- and test-number calling by default.

