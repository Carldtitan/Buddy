# Buddy Live Access

Buddy is a live accessibility confirmation assistant. It resolves a venue, gathers public accessibility evidence, decides what is still unknown, optionally warms a voice agent, places a guarded confirmation call, and publishes a short report for the mobile app and community view.

The shared Pydantic contracts in `contracts/` are the current source of truth while backend, mobile, Runpod, and worker implementations are being assembled. Current local development uses Bright Data SERP plus Browser API Playwright, Mapbox, Twilio, Supabase publishable/secret keys, Runpod Flash and voice worker URLs generated after deployment, and the built-in local UI renderer.

## Safety Default

Real venue calls are disabled by default. Keep `ALLOW_REAL_VENUE_CALLS=false` in local and staging environments. In that mode, every outbound call should go to `BUDDY_TEST_PHONE_NUMBER`, even when the venue payload contains a real phone number.

Only enable real venue calls after Twilio webhooks, consent/call policy, rate limits, allowlists, and manual QA are complete.

## Quick Start

```bash
cd /root/runpod-hack
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r buddy/backend/requirements.txt
cp buddy/.env.example buddy/.env
```

Run the backend API:

```bash
cd /root/runpod-hack
source .venv/bin/activate
PYTHONPATH=/root/runpod-hack python3 -m uvicorn buddy.backend.app.main:app --reload --host 0.0.0.0 --port 8000
```

Run the voice worker locally:

```bash
cd /root/runpod-hack/buddy/runpod_voice_worker
python3 -m pip install -r requirements.txt
python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 9000
```

Run tests and contract checks:

```bash
cd /root/runpod-hack
source .venv/bin/activate
PYTHONPATH=/root/runpod-hack python3 -m unittest discover -s buddy/backend/tests
PYTHONPATH=/root/runpod-hack python3 -m compileall buddy/contracts
```

## Documentation

- [Environment setup](docs/setup.md)
- [Architecture](docs/architecture.md)
- [Deployment notes](docs/deploy.md)
- [Model warmup flow](docs/model-warmup.md)

## Core Flow

1. Mobile app submits an `AccessCheckCreate` payload.
2. Backend resolves the place with Mapbox.
3. Backend gathers public evidence with Bright Data SERP and Browser API Playwright plus maps/place metadata.
4. Reasoning service scores evidence and returns missing critical facts.
5. If facts are missing, backend warms the Runpod voice worker.
6. Twilio places a guarded call. Local and staging calls route to `BUDDY_TEST_PHONE_NUMBER`.
7. Voice worker returns transcript turns and extracted facts.
8. Backend generates a `FinalReport` and optional `CommunityReport`.
9. The local renderer can transform `openui_payload` into React Native UI. Do not use paid OpenUI for this hack build.

## Environment Variables

Start from [.env.example](.env.example). Provider-specific dashboard locations and setup notes are in [docs/setup.md](docs/setup.md).
