from __future__ import annotations

from fastapi import APIRouter

from .config import Settings, load_settings
from .env_utils import configured_names, env_value, setting_bool, setting_value


router = APIRouter(tags=["environment"])


@router.get("/env/validation")
def validate_environment_endpoint() -> dict:
    return validate_environment(load_settings())


def validate_environment(settings: Settings) -> dict:
    allow_real = setting_bool(
        settings,
        "allow_real_venue_calls",
        "ALLOW_REAL_VENUE_CALLS",
        "BUDDY_ENABLE_REAL_VENUE_CALLS",
        default=False,
    )
    test_number = setting_value(settings, "buddy_test_phone_number", "BUDDY_TEST_PHONE_NUMBER")
    twilio_credentials = _twilio_credentials_configured(settings)
    twilio_webhooks = _twilio_webhooks_configured(settings)
    bright_data_serp = _bright_data_serp_configured(settings)
    bright_data_browser = _bright_data_browser_configured(settings)
    supabase = _supabase_configured(settings)

    warnings = []
    errors = []
    if not allow_real and not test_number:
        errors.append("BUDDY_TEST_PHONE_NUMBER is required while real venue calls are disabled.")
    if twilio_credentials and not twilio_webhooks:
        warnings.append("Twilio credentials are present, but voice/media webhook URLs are incomplete.")
    if allow_real and not twilio_webhooks:
        errors.append("Real venue calls require TWILIO_VOICE_WEBHOOK_URL and TWILIO_MEDIA_STREAM_WS_URL.")
    if not bright_data_serp["configured"]:
        warnings.append("Bright Data SERP is not configured; public-web collection will use a local stub.")
    if not supabase["configured"]:
        warnings.append("Supabase is not fully configured; storage will remain process-local.")

    can_start_test_call = bool(twilio_credentials and twilio_webhooks and test_number)
    can_start_real_venue_call = bool(twilio_credentials and twilio_webhooks and allow_real)

    return {
        "ok": not errors,
        "app": {
            "environment": env_value("APP_ENV", "BUDDY_ENV") or settings.app_env,
            "public_url_configured": bool(env_value("PUBLIC_APP_URL", "BUDDY_PUBLIC_BASE_URL")),
            "backend_url_configured": bool(env_value("BACKEND_URL", "BUDDY_PUBLIC_BASE_URL")),
        },
        "call_safety": {
            "allow_real_venue_calls": allow_real,
            "test_number_configured": bool(test_number),
            "test_number_safety_active": bool(not allow_real and test_number),
            "can_start_test_call": can_start_test_call,
            "can_start_real_venue_call": can_start_real_venue_call,
        },
        "twilio": {
            "credentials_configured": twilio_credentials,
            "webhooks_configured": twilio_webhooks,
            "from_phone_configured": bool(
                setting_value(
                    settings,
                    "twilio_from_phone_number",
                    "TWILIO_FROM_PHONE_NUMBER",
                    "BUDDY_CALLER_ID",
                )
            ),
            "configured_env": configured_names(
                "TWILIO_ACCOUNT_SID",
                "TWILIO_AUTH_TOKEN",
                "TWILIO_FROM_PHONE_NUMBER",
                "BUDDY_CALLER_ID",
                "TWILIO_VOICE_WEBHOOK_URL",
                "TWILIO_MEDIA_STREAM_WS_URL",
                "TWILIO_STATUS_CALLBACK_URL",
            ),
        },
        "bright_data": {
            "serp": bright_data_serp,
            "browser_playwright": bright_data_browser,
        },
        "supabase": supabase,
        "warnings": warnings,
        "errors": errors,
    }


def _twilio_credentials_configured(settings: Settings) -> bool:
    return bool(
        setting_value(settings, "twilio_account_sid", "TWILIO_ACCOUNT_SID")
        and setting_value(settings, "twilio_auth_token", "TWILIO_AUTH_TOKEN")
        and setting_value(
            settings,
            "twilio_from_phone_number",
            "TWILIO_FROM_PHONE_NUMBER",
            "BUDDY_CALLER_ID",
        )
    )


def _twilio_webhooks_configured(settings: Settings) -> bool:
    return bool(
        setting_value(settings, "twilio_voice_webhook_url", "TWILIO_VOICE_WEBHOOK_URL")
        and setting_value(
            settings,
            "twilio_media_stream_ws_url",
            "TWILIO_MEDIA_STREAM_WS_URL",
            "RUNPOD_VOICE_WORKER_WS_URL",
        )
    )


def _bright_data_serp_configured(settings: Settings) -> dict:
    token = setting_value(
        settings,
        "bright_data_api_key",
        "BRIGHT_DATA_API_TOKEN",
        "BRIGHT_DATA_API_KEY",
    )
    zone = setting_value(settings, "bright_data_serp_zone", "BRIGHT_DATA_SERP_ZONE")
    return {
        "configured": bool(token and zone),
        "api_token_configured": bool(token),
        "serp_zone_configured": bool(zone),
        "base_url": env_value("BRIGHT_DATA_BASE_URL") or "https://api.brightdata.com",
    }


def _bright_data_browser_configured(settings: Settings) -> dict:
    api_type = (
        setting_value(
            settings,
            "bright_data_browser_api_type",
            "BRIGHT_DATA_BROWSER_API_TYPE",
        )
        or "playwright"
    )
    ws_url = setting_value(
        settings,
        "bright_data_browser_playwright_ws_url",
        "BRIGHT_DATA_BROWSER_PLAYWRIGHT_WS_URL",
    )
    return {
        "configured": api_type == "playwright" and bool(ws_url),
        "api_type": api_type,
        "playwright_ws_url_configured": bool(ws_url),
        "web_unlocker_zone_configured": bool(env_value("BRIGHT_DATA_WEB_UNLOCKER_ZONE")),
    }


def _supabase_configured(settings: Settings) -> dict:
    url = setting_value(settings, "supabase_url", "SUPABASE_URL")
    anon_key = setting_value(
        settings,
        "supabase_publishable_key",
        "SUPABASE_PUBLISHABLE_KEY",
        "SUPABASE_ANON_KEY",
    )
    service_key = setting_value(
        settings,
        "supabase_secret_key",
        "SUPABASE_SECRET_KEY",
        "SUPABASE_SERVICE_ROLE_KEY",
    )
    database_url = setting_value(settings, "database_url", "DATABASE_URL", "SUPABASE_DB_URL")
    missing = []
    if not url:
        missing.append("SUPABASE_URL")
    if not anon_key:
        missing.append("SUPABASE_ANON_KEY")
    if not service_key:
        missing.append("SUPABASE_SERVICE_ROLE_KEY")
    if not database_url:
        missing.append("SUPABASE_DB_URL")
    return {
        "configured": not missing,
        "url_configured": bool(url),
        "anon_key_configured": bool(anon_key),
        "service_role_key_configured": bool(service_key),
        "database_url_configured": bool(database_url),
        "missing": missing,
    }
