from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


ROOT_ENV = Path(__file__).resolve().parents[3] / ".env"
if ROOT_ENV.exists():
    load_dotenv(ROOT_ENV)


TRUE_VALUES = {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    app_env: str = "development"
    public_app_url: str = "http://localhost:3000"
    backend_url: str = "http://localhost:8000"
    ui_renderer: str = "local"
    bright_data_api_key: str | None = None
    bright_data_serp_zone: str | None = None
    bright_data_browser_api_type: str = "playwright"
    bright_data_browser_playwright_ws_url: str | None = None
    runpod_api_key: str | None = None
    runpod_flash_base_url: str | None = None
    runpod_flash_app_name: str = "buddy"
    runpod_flash_env: str = "production"
    runpod_voice_worker_base_url: str | None = None
    runpod_voice_worker_ws_url: str | None = None
    runpod_voice_worker_health_url: str | None = None
    runpod_voice_worker_warmup_url: str | None = None
    runpod_voice_worker_auth_token: str | None = None
    twilio_account_sid: str | None = None
    twilio_auth_token: str | None = None
    twilio_from_phone_number: str | None = None
    twilio_status_callback_url: str | None = None
    twilio_voice_webhook_url: str | None = None
    twilio_media_stream_ws_url: str | None = None
    buddy_test_phone_number: str | None = None
    allow_real_venue_calls: bool = False
    supabase_url: str | None = None
    supabase_publishable_key: str | None = None
    supabase_secret_key: str | None = None
    database_url: str | None = None


def env_bool(name: str, default: bool = False) -> bool:
    value = REDACTEDname)
    if value is None:
        return default
    return value.strip().lower() in TRUE_VALUES


def load_settings() -> Settings:
    return Settings(
        app_env=REDACTED"APP_ENV", "development"),
        public_app_url=REDACTED"PUBLIC_APP_URL", "http://localhost:3000"),
        backend_url=REDACTED"BACKEND_URL", "http://localhost:8000"),
        ui_renderer=REDACTED"UI_RENDERER", "local"),
        bright_data_api_key=REDACTED"BRIGHT_DATA_API_KEY"),
        bright_data_serp_zone=REDACTED"BRIGHT_DATA_SERP_ZONE"),
        bright_data_browser_api_type=REDACTED"BRIGHT_DATA_BROWSER_API_TYPE", "playwright"),
        bright_data_browser_playwright_ws_url=REDACTED"BRIGHT_DATA_BROWSER_PLAYWRIGHT_WS_URL"),
        runpod_api_key=REDACTED"RUNPOD_API_KEY"),
        runpod_flash_base_url=REDACTED"RUNPOD_FLASH_BASE_URL"),
        runpod_flash_app_name=REDACTED"RUNPOD_FLASH_APP_NAME", "buddy"),
        runpod_flash_env=REDACTED"RUNPOD_FLASH_ENV", "production"),
        runpod_voice_worker_base_url=REDACTED"RUNPOD_VOICE_WORKER_BASE_URL"),
        runpod_voice_worker_ws_url=REDACTED"RUNPOD_VOICE_WORKER_WS_URL"),
        runpod_voice_worker_health_url=REDACTED"RUNPOD_VOICE_WORKER_HEALTH_URL"),
        runpod_voice_worker_warmup_url=REDACTED"RUNPOD_VOICE_WORKER_WARMUP_URL"),
        runpod_voice_worker_auth_token=REDACTED"RUNPOD_VOICE_WORKER_AUTH_TOKEN"),
        twilio_account_sid=REDACTED"TWILIO_ACCOUNT_SID"),
        twilio_auth_token=REDACTED"TWILIO_AUTH_TOKEN"),
        twilio_from_phone_number=REDACTED"TWILIO_FROM_PHONE_NUMBER"),
        twilio_status_callback_url=REDACTED"TWILIO_STATUS_CALLBACK_URL"),
        twilio_voice_webhook_url=REDACTED"TWILIO_VOICE_WEBHOOK_URL"),
        twilio_media_stream_ws_url=REDACTED"TWILIO_MEDIA_STREAM_WS_URL"),
        buddy_test_phone_number=REDACTED"BUDDY_TEST_PHONE_NUMBER"),
        allow_real_venue_calls=env_bool("ALLOW_REAL_VENUE_CALLS", default=False),
        supabase_url=REDACTED"SUPABASE_URL"),
        supabase_publishable_key=REDACTED"SUPABASE_PUBLISHABLE_KEY"),
        supabase_secret_key=REDACTED"SUPABASE_SECRET_KEY"),
        database_url=REDACTED"DATABASE_URL"),
    )
