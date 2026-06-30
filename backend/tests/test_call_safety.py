import unittest
from unittest.mock import patch

from buddy.backend.app.call_safety import choose_call_target
from buddy.backend.app.config import Settings


class CallSafetyTests(unittest.TestCase):
    def setUp(self):
        self._env = patch.dict("os.environ", {"BUDDY_DISABLE_DOTENV": "1"}, clear=True)
        self._env.start()

    def tearDown(self):
        self._env.stop()

    def test_defaults_to_test_number(self):
        decision = choose_call_target(
            "+15551234567",
            Settings(buddy_test_phone_number="+15550000000"),
        )

        self.assertEqual(decision.dial_phone, "+15550000000")
        self.assertTrue(decision.using_safety_override)

    def test_real_calls_must_be_explicit(self):
        decision = choose_call_target(
            "+15551234567",
            Settings(buddy_test_phone_number="+15550000000", allow_real_venue_calls=True),
        )

        self.assertEqual(decision.dial_phone, "+15551234567")
        self.assertFalse(decision.using_safety_override)

    def test_requires_test_number_when_real_calls_disabled(self):
        with self.assertRaises(ValueError):
            choose_call_target("+15551234567", Settings())

    def test_real_calls_require_venue_phone(self):
        with self.assertRaises(ValueError):
            choose_call_target(None, Settings(allow_real_venue_calls=True))


if __name__ == "__main__":
    unittest.main()
