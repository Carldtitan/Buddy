# Buddy Backend

FastAPI orchestrator for Buddy accessibility checks.

## Run

```bash
uvicorn buddy.backend.app.main:app --reload
```

Check local readiness without exposing secret values:

```bash
curl http://localhost:8000/env/validation
```

## Environment

- `BRIGHT_DATA_API_TOKEN`, `BRIGHT_DATA_SERP_ZONE`: enables Bright Data SERP collection.
- `BRIGHT_DATA_BROWSER_PLAYWRIGHT_WS_URL`: enables Bright Data Browser Playwright connection metadata.
- `RUNPOD_FLASH_BASE_URL`: optional already-deployed Runpod Flash endpoint.
- `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_FROM_PHONE_NUMBER` or `BUDDY_CALLER_ID`: optional Twilio credentials.
- `TWILIO_VOICE_WEBHOOK_URL`, `TWILIO_MEDIA_STREAM_WS_URL`: required before Twilio can place a call.
- `BUDDY_TEST_PHONE_NUMBER`: required for call orchestration unless real calls are explicitly allowed.
- `ALLOW_REAL_VENUE_CALLS=true` or `BUDDY_ENABLE_REAL_VENUE_CALLS=true`: permits dialing the venue phone from the shared contract payload.

Storage is process-local memory for now.

See `supabase_schema.sql` for the optional Supabase table schema for checks,
call sessions, evidence, reports, and community reports.
