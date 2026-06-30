import os
import unittest
from unittest.mock import patch
from uuid import uuid4

from buddy.backend.app.config import Settings
from buddy.backend.app.twilio import TwilioCallOrchestrator
from buddy.contracts.buddy_contracts import CallSession


class TwilioSafetyTests(unittest.TestCase):
    def test_missing_webhooks_prevent_real_twilio_post(self):
        env = {
            "BUDDY_DISABLE_DOTENV": "1",
            "BUDDY_TEST_PHONE_NUMBER": "+15550000000",
            "TWILIO_ACCOUNT_SID": "sid",
            "TWILIO_AUTH_TOKEN": "token",
            "BUDDY_CALLER_ID": "+15551111111",
        }
        with patch.dict(os.environ, env, clear=True):
            with patch("buddy.backend.app.twilio.post_form") as post_form:
                session = TwilioCallOrchestrator(Settings()).start_call(
                    CallSession(check_id=uuid4(), to_phone=""),
                    "+15551234567",
                )

        self.assertEqual(session.status, "failed")
        post_form.assert_not_called()

    def test_test_number_safety_can_place_twilio_call_when_webhooks_exist(self):
        env = {
            "BUDDY_DISABLE_DOTENV": "1",
            "BUDDY_TEST_PHONE_NUMBER": "+15550000000",
            "TWILIO_ACCOUNT_SID": "sid",
            "TWILIO_AUTH_TOKEN": "token",
            "BUDDY_CALLER_ID": "+15551111111",
            "TWILIO_VOICE_WEBHOOK_URL": "https://example.test/voice",
            "TWILIO_MEDIA_STREAM_WS_URL": "wss://example.test/twilio-media",
        }
        with patch.dict(os.environ, env, clear=True):
            with patch("buddy.backend.app.twilio.post_form", return_value={"sid": "CA123"}) as post_form:
                session = TwilioCallOrchestrator(Settings()).start_call(
                    CallSession(check_id=uuid4(), to_phone=""),
                    "+15551234567",
                )

        self.assertEqual(session.status, "in_progress")
        self.assertEqual(session.to_phone, "+15550000000")
        payload = post_form.call_args.args[1]
        self.assertEqual(payload["To"], "+15550000000")
        self.assertEqual(payload["From"], "+15551111111")

    def test_no_network_call_when_test_number_missing(self):
        env = {
            "BUDDY_DISABLE_DOTENV": "1",
            "TWILIO_ACCOUNT_SID": "sid",
            "TWILIO_AUTH_TOKEN": "token",
            "BUDDY_CALLER_ID": "+15551111111",
            "TWILIO_VOICE_WEBHOOK_URL": "https://example.test/voice",
            "TWILIO_MEDIA_STREAM_WS_URL": "wss://example.test/twilio-media",
        }
        with patch.dict(os.environ, env, clear=True):
            with patch("buddy.backend.app.twilio.post_form") as post_form:
                with self.assertRaises(ValueError):
                    TwilioCallOrchestrator(Settings()).start_call(
                        CallSession(check_id=uuid4(), to_phone=""),
                        "+15551234567",
                    )

        post_form.assert_not_called()


if __name__ == "__main__":
    unittest.main()
