from __future__ import annotations

from dataclasses import dataclass

from .config import Settings
from .env_utils import setting_bool, setting_value


@dataclass(frozen=True)
class CallTargetDecision:
    requested_phone: str | None
    dial_phone: str
    using_safety_override: bool
    reason: str


def choose_call_target(requested_phone: str | None, settings: Settings) -> CallTargetDecision:
    """Choose the phone number Twilio may dial.

    Buddy never calls a venue phone number unless ALLOW_REAL_VENUE_CALLS=true.
    The default path dials BUDDY_TEST_PHONE_NUMBER so demos can exercise the
    orchestration without accidentally contacting a real venue.
    """
    allow_real_venue_calls = setting_bool(
        settings,
        "allow_real_venue_calls",
        "ALLOW_REAL_VENUE_CALLS",
        "BUDDY_ENABLE_REAL_VENUE_CALLS",
        default=False,
    )
    test_phone = setting_value(settings, "buddy_test_phone_number", "BUDDY_TEST_PHONE_NUMBER")

    if allow_real_venue_calls:
        if not requested_phone:
            raise ValueError("Venue phone is required when real venue calls are enabled.")
        return CallTargetDecision(
            requested_phone=requested_phone,
            dial_phone=requested_phone,
            using_safety_override=False,
            reason="ALLOW_REAL_VENUE_CALLS is true; dialing requested venue phone.",
        )

    if not test_phone:
        raise ValueError(
            "BUDDY_TEST_PHONE_NUMBER must be set unless ALLOW_REAL_VENUE_CALLS=true."
        )

    return CallTargetDecision(
        requested_phone=requested_phone,
        dial_phone=test_phone,
        using_safety_override=True,
        reason="Safety default active; dialing BUDDY_TEST_PHONE_NUMBER instead of venue.",
    )
