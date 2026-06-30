from __future__ import annotations

from datetime import datetime

from buddy.contracts.buddy_contracts import CallSession, TranscriptTurn

from .call_safety import choose_call_target
from .config import Settings
from .env_utils import setting_value
from .http_client import post_form, post_json


class TwilioCallOrchestrator:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def start_call(self, session: CallSession, venue_phone: str | None) -> CallSession:
        decision = choose_call_target(venue_phone, self._settings)
        from_phone = self._from_phone()
        voice_webhook_url = self._voice_webhook_url()
        media_stream_url = self._media_stream_url()
        session.to_phone = decision.dial_phone
        session.from_phone = from_phone
        session.status = "warming"
        session.started_at = datetime.utcnow()
        session.transcript.append(
            TranscriptTurn(
                speaker="system",
                text=decision.reason,
                confidence=1.0,
            )
        )

        if not self._twilio_configured():
            session.status = "completed"
            session.ended_at = datetime.utcnow()
            session.conversation_summary = "Twilio is not configured; recorded a dry-run call session."
            session.extracted_facts.notes = "Dry run only. Configure Twilio credentials to place calls."
            session.extracted_facts.needs_followup = True
            return session

        missing_urls = []
        if not voice_webhook_url:
            missing_urls.append("TWILIO_VOICE_WEBHOOK_URL")
        if not media_stream_url:
            missing_urls.append("TWILIO_MEDIA_STREAM_WS_URL")
        if missing_urls:
            session.status = "failed"
            session.ended_at = datetime.utcnow()
            session.conversation_summary = (
                "Twilio credentials are present, but call webhooks are not configured yet."
            )
            session.extracted_facts.notes = f"Missing {', '.join(missing_urls)}."
            session.extracted_facts.needs_followup = True
            return session

        self._warm_voice_worker(session)

        account_sid = self._account_sid()
        url = f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Calls.json"
        payload = {
            "To": decision.dial_phone,
            "From": from_phone,
            "Url": voice_webhook_url,
            "Method": "POST",
        }
        status_callback_url = self._status_callback_url()
        if status_callback_url:
            payload["StatusCallback"] = status_callback_url
            payload["StatusCallbackMethod"] = "POST"

        response = post_form(
            url,
            payload,
            basic_auth=(self._account_sid() or "", self._auth_token() or ""),
            timeout_seconds=20,
        )
        session.status = "in_progress"
        session.recording_url = response.get("recording_url") or response.get("RecordingUrl")
        session.conversation_summary = "Twilio call has been started."
        session.transcript.append(
            TranscriptTurn(
                speaker="system",
                text=f"Twilio call started with SID {response.get('sid', 'unknown')}.",
                confidence=1.0,
            )
        )
        return session

    def _twilio_configured(self) -> bool:
        return bool(
            self._account_sid()
            and self._auth_token()
            and self._from_phone()
        )

    def _account_sid(self) -> str | None:
        return setting_value(self._settings, "twilio_account_sid", "TWILIO_ACCOUNT_SID")

    def _auth_token(self) -> str | None:
        return setting_value(self._settings, "twilio_auth_token", "TWILIO_AUTH_TOKEN")

    def _from_phone(self) -> str | None:
        return setting_value(
            self._settings,
            "twilio_from_phone_number",
            "TWILIO_FROM_PHONE_NUMBER",
            "BUDDY_CALLER_ID",
        )

    def _voice_webhook_url(self) -> str | None:
        return setting_value(self._settings, "twilio_voice_webhook_url", "TWILIO_VOICE_WEBHOOK_URL")

    def _status_callback_url(self) -> str | None:
        return setting_value(
            self._settings,
            "twilio_status_callback_url",
            "TWILIO_STATUS_CALLBACK_URL",
        )

    def _media_stream_url(self) -> str | None:
        return setting_value(
            self._settings,
            "twilio_media_stream_ws_url",
            "TWILIO_MEDIA_STREAM_WS_URL",
            "RUNPOD_VOICE_WORKER_WS_URL",
        )

    def _warm_voice_worker(self, session: CallSession) -> None:
        if not self._settings.runpod_voice_worker_warmup_url:
            session.transcript.append(
                TranscriptTurn(
                    speaker="system",
                    text="Voice worker warmup URL is not configured; skipping pre-call warmup.",
                    confidence=1.0,
                )
            )
            return

        headers = {}
        if self._settings.runpod_voice_worker_auth_token:
            headers["Authorization"] = f"Bearer {self._settings.runpod_voice_worker_auth_token}"

        try:
            response = post_json(
                self._settings.runpod_voice_worker_warmup_url,
                {
                    "check_id": str(session.check_id),
                    "models": {
                        "stt": "small.en",
                        "llm": "Qwen/Qwen2.5-1.5B-Instruct",
                        "tts": "hexgrad/Kokoro-82M",
                    },
                },
                headers=headers,
                timeout_seconds=180,
            )
            if not response.get("ready"):
                session.transcript.append(
                    TranscriptTurn(
                        speaker="system",
                        text="Voice worker warmup returned not ready, but the call will continue.",
                        confidence=1.0,
                    )
                )
                return
            session.transcript.append(
                TranscriptTurn(
                    speaker="system",
                    text="Voice worker reported ready before dialing.",
                    confidence=1.0,
                )
            )
        except Exception as exc:
            session.transcript.append(
                TranscriptTurn(
                    speaker="system",
                    text=f"Voice worker warmup failed, continuing with call: {exc}",
                    confidence=1.0,
                )
            )
