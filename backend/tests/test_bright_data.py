import os
import json
import unittest
from unittest.mock import patch

from buddy.backend.app.bright_data import (
    BrightDataBrowserPlaywright,
    BrightDataCollector,
    BrightDataSerpClient,
)
from buddy.backend.app.config import Settings
from buddy.contracts.buddy_contracts import Place


class BrightDataTests(unittest.TestCase):
    def test_collector_returns_stub_when_serp_is_not_configured(self):
        with patch.dict(os.environ, {"BUDDY_DISABLE_DOTENV": "1"}, clear=True):
            evidence = BrightDataCollector(Settings()).collect(Place(name="Cafe Example"))

        self.assertEqual(len(evidence), 1)
        self.assertEqual(evidence[0].raw["mode"], "stub")
        self.assertIn("BRIGHT_DATA_API_TOKEN", evidence[0].raw["required_env"])

    def REDACTED(self):
        env = {
            "BUDDY_DISABLE_DOTENV": "1",
            "BRIGHT_DATA_API_TOKEN": "token",
            "BRIGHT_DATA_SERP_ZONE": "serp_zone",
            "BRIGHT_DATA_BASE_URL": "https://bright.example",
        }
        with patch.dict(os.environ, env, clear=True):
            client = BrightDataSerpClient.from_settings(Settings())

        self.assertTrue(client.configured)
        self.assertEqual(client.api_token, "token")
        self.assertEqual(client.serp_zone, "serp_zone")
        self.assertEqual(client.base_url, "https://bright.example")

    def REDACTED(self):
        env = {
            "BUDDY_DISABLE_DOTENV": "1",
            "BRIGHT_DATA_BROWSER_PLAYWRIGHT_WS_URL": "wss://browser.example",
        }
        with patch.dict(os.environ, env, clear=True):
            browser = BrightDataBrowserPlaywright.from_settings(Settings())

        self.assertTrue(browser.configured)
        self.assertEqual(browser.playwright_connect_options()["ws_endpoint"], "wss://browser.example")

    def test_configured_collector_parses_serp_results(self):
        env = {
            "BUDDY_DISABLE_DOTENV": "1",
            "BRIGHT_DATA_API_TOKEN": "token",
            "BRIGHT_DATA_SERP_ZONE": "serp_zone",
        }
        response = {
            "organic": [
                {
                    "title": "Cafe Example accessibility",
                    "description": "Wheelchair accessible entrance and seating available.",
                    "url": "https://example.com/access",
                }
            ]
        }
        with patch.dict(os.environ, env, clear=True):
            with patch("buddy.backend.app.bright_data.post_json", return_value=response) as post_json:
                evidence = BrightDataCollector(Settings()).collect(Place(name="Cafe Example"))

        self.assertEqual(len(evidence), 1)
        self.assertEqual(evidence[0].polarity, "supports_access")
        post_json.assert_called_once()
        self.assertEqual(post_json.call_args.args[0], "https://api.brightdata.com/request")
        self.assertEqual(post_json.call_args.args[1]["zone"], "serp_zone")

    def test_configured_collector_parses_bright_data_body_string(self):
        env = {
            "BUDDY_DISABLE_DOTENV": "1",
            "BRIGHT_DATA_API_KEY": "token",
            "BRIGHT_DATA_SERP_ZONE": "buddy_serp",
        }
        response = {
            "status_code": 200,
            "body": json.dumps(
                {
                    "organic": [
                        {
                            "title": "Cafe Example",
                            "description": "ADA entrance and wheelchair accessible seating.",
                            "link": "https://example.com",
                        }
                    ]
                }
            ),
        }
        with patch.dict(os.environ, env, clear=True):
            with patch("buddy.backend.app.bright_data.post_json", return_value=response):
                evidence = BrightDataCollector(Settings()).collect(Place(name="Cafe Example"))

        self.assertEqual(len(evidence), 1)
        self.assertEqual(evidence[0].source_url, "https://example.com")
        self.assertEqual(evidence[0].polarity, "supports_access")


if __name__ == "__main__":
    unittest.main()
