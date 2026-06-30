import os
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from buddy.backend.app.config import Settings
from buddy.backend.app.env_validation import validate_environment
from buddy.backend.app.main import app


class EnvValidationTests(unittest.TestCase):
    def test_validation_requires_test_number_when_real_calls_are_disabled(self):
        with patch.dict(os.environ, {"BUDDY_DISABLE_DOTENV": "1"}, clear=True):
            payload = validate_environment(Settings())

        self.assertFalse(payload["ok"])
        self.assertIn("BUDDY_TEST_PHONE_NUMBER", payload["errors"][0])

    def test_validation_reports_test_number_safety(self):
        env = {
            "BUDDY_DISABLE_DOTENV": "1",
            "BUDDY_TEST_PHONE_NUMBER": "+15550000000",
            "BUDDY_ENABLE_REAL_VENUE_CALLS": "false",
            "TWILIO_ACCOUNT_SID": "sid",
            "TWILIO_AUTH_TOKEN": "token",
            "BUDDY_CALLER_ID": "+15551111111",
            "TWILIO_VOICE_WEBHOOK_URL": "https://example.test/voice",
            "TWILIO_MEDIA_STREAM_WS_URL": "wss://example.test/twilio-media",
        }
        with patch.dict(os.environ, env, clear=True):
            payload = validate_environment(Settings())

        self.assertTrue(payload["ok"])
        self.assertTrue(payload["call_safety"]["test_number_safety_active"])
        self.assertTrue(payload["call_safety"]["can_start_test_call"])
        self.assertFalse(payload["call_safety"]["can_start_real_venue_call"])

    def test_endpoint_is_registered(self):
        with patch.dict(
            os.environ,
            {"BUDDY_DISABLE_DOTENV": "1", "BUDDY_TEST_PHONE_NUMBER": "+15550000000"},
            clear=True,
        ):
            response = TestClient(app).get("/env/validation")

        self.assertEqual(response.status_code, 200)
        self.assertIn("call_safety", response.json())

    def test_twilio_webhook_alias_uses_worker_ws_url(self):
        with patch.dict(
            os.environ,
            {
                "BUDDY_DISABLE_DOTENV": "1",
                "RUNPOD_VOICE_WORKER_WS_URL": "wss://example.test/twilio-media",
            },
            clear=True,
        ):
            response = TestClient(app).post("/webhooks/twilio/voice")

        self.assertEqual(response.status_code, 200)
        self.assertIn("wss://example.test/twilio-media", response.text)


if __name__ == "__main__":
    unittest.main()
