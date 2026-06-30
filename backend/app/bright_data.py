from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any
from urllib.parse import quote_plus

from buddy.contracts.buddy_contracts import EvidenceItem, Place

from .config import Settings
from .env_utils import env_value, setting_value
from .http_client import post_json


@dataclass(frozen=True)
class BrightDataSerpClient:
    api_token: str | None
    serp_zone: str | None
    base_url: str

    @classmethod
    def from_settings(cls, settings: Settings) -> "BrightDataSerpClient":
        return cls(
            api_token=setting_value(
                settings,
                "bright_data_api_key",
                "BRIGHT_DATA_API_TOKEN",
                "BRIGHT_DATA_API_KEY",
            ),
            serp_zone=setting_value(settings, "bright_data_serp_zone", "BRIGHT_DATA_SERP_ZONE"),
            base_url=env_value("BRIGHT_DATA_BASE_URL") or "https://api.brightdata.com",
        )

    @property
    def configured(self) -> bool:
        return bool(self.api_token and self.serp_zone)

    def search(self, query: str) -> dict[str, Any]:
        if not self.configured:
            raise RuntimeError("Bright Data SERP is not configured.")

        target_url = f"https://www.google.com/search?q={quote_plus(query)}"
        return post_json(
            f"{self.base_url.rstrip('/')}/request",
            {
                "zone": self.serp_zone,
                "url": target_url,
                "format": "json",
            },
            headers={"Authorization": f"Bearer {self.api_token}"},
            timeout_seconds=45,
        )


@dataclass(frozen=True)
class BrightDataBrowserPlaywright:
    api_type: str
    ws_url: str | None
    web_unlocker_zone: str | None

    @classmethod
    def from_settings(cls, settings: Settings) -> "BrightDataBrowserPlaywright":
        return cls(
            api_type=setting_value(
                settings,
                "bright_data_browser_api_type",
                "BRIGHT_DATA_BROWSER_API_TYPE",
            )
            or "playwright",
            ws_url=setting_value(
                settings,
                "bright_data_browser_playwright_ws_url",
                "BRIGHT_DATA_BROWSER_PLAYWRIGHT_WS_URL",
            ),
            web_unlocker_zone=env_value("BRIGHT_DATA_WEB_UNLOCKER_ZONE"),
        )

    @property
    def configured(self) -> bool:
        return self.api_type == "playwright" and bool(self.ws_url)

    def playwright_connect_options(self) -> dict[str, str]:
        if not self.configured or not self.ws_url:
            raise RuntimeError("Bright Data Browser Playwright is not configured.")
        return {"ws_endpoint": self.ws_url}


class BrightDataCollector:
    def __init__(self, settings: Settings) -> None:
        self._serp = BrightDataSerpClient.from_settings(settings)
        self._browser = BrightDataBrowserPlaywright.from_settings(settings)

    def collect(self, place: Place) -> list[EvidenceItem]:
        query = _place_query(place)
        if not self._serp.configured:
            return [_stub_evidence("Bright Data SERP not configured", query, self._browser)]

        try:
            response = self._serp.search(query)
        except Exception as exc:
            return [
                EvidenceItem(
                    source_type="web",
                    source_timestamp=datetime.utcnow(),
                    title="Bright Data request failed",
                    claim="Buddy could not collect public web evidence from Bright Data, so it continued with local risk scoring.",
                    feature="unknown",
                    polarity="unknown",
                    confidence=0.0,
                    raw={
                        "mode": "bright_data_error",
                        "query": query,
                        "error": str(exc),
                        "hint": "Check BRIGHT_DATA_SERP_ZONE is the zone name, not an API id.",
                        "browser_playwright_configured": self._browser.configured,
                    },
                )
            ]
        evidence = _evidence_from_serp_response(response)
        if evidence:
            return evidence
        return [
            EvidenceItem(
                source_type="web",
                source_timestamp=datetime.utcnow(),
                title="Bright Data SERP returned no parsed evidence",
                claim="Bright Data responded, but Buddy could not extract accessibility evidence.",
                feature="unknown",
                polarity="unknown",
                confidence=0.1,
                raw={
                    "mode": "bright_data_serp",
                    "query": query,
                    "browser_playwright_configured": self._browser.configured,
                    "response_keys": sorted(response.keys()),
                },
            )
        ]


def _place_query(place: Place) -> str:
    parts = [part for part in (place.name, place.address, place.website) if part]
    return " ".join(parts) or "accessibility-friendly venue"


def _stub_evidence(
    title: str,
    query: str,
    browser: BrightDataBrowserPlaywright,
) -> EvidenceItem:
    return EvidenceItem(
        source_type="web",
        source_timestamp=datetime.utcnow(),
        title=title,
        claim="No public web evidence has been collected yet.",
        feature="unknown",
        polarity="unknown",
        confidence=0.0,
        raw={
            "mode": "stub",
            "query": query,
            "required_env": ["BRIGHT_DATA_API_TOKEN", "BRIGHT_DATA_SERP_ZONE"],
            "browser_playwright_configured": browser.configured,
            "browser_required_env": ["BRIGHT_DATA_BROWSER_PLAYWRIGHT_WS_URL"],
        },
    )


def _evidence_from_serp_response(response: dict[str, Any]) -> list[EvidenceItem]:
    results = _result_candidates(response)
    evidence: list[EvidenceItem] = []
    for result in results[:5]:
        claim = _first_text(result, "description", "snippet", "content", "text")
        title = _first_text(result, "title", "name")
        if not claim and title:
            claim = title
        if not claim:
            continue

        feature, polarity, confidence = _classify_accessibility_text(f"{title or ''} {claim}")
        evidence.append(
            EvidenceItem(
                source_type="web",
                source_url=_first_text(result, "url", "link"),
                source_timestamp=datetime.utcnow(),
                title=title,
                claim=claim,
                feature=feature,
                polarity=polarity,
                confidence=confidence,
                raw={"provider": "bright_data_serp", "result": result},
            )
        )
    return evidence


def _result_candidates(response: dict[str, Any]) -> list[dict[str, Any]]:
    for key in ("organic", "organic_results", "results"):
        value = response.get(key)
        if isinstance(value, list):
            return [item for item in value if isinstance(item, dict)]

    body = response.get("body")
    if isinstance(body, dict):
        return _result_candidates(body)
    if isinstance(body, str) and body.strip():
        try:
            parsed_body = json.loads(body)
        except json.JSONDecodeError:
            return []
        if isinstance(parsed_body, dict):
            return _result_candidates(parsed_body)
    return []


def _first_text(result: dict[str, Any], *keys: str) -> str | None:
    for key in keys:
        value = result.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def _classify_accessibility_text(text: str) -> tuple[str, str, float]:
    normalized = text.lower()
    if "restroom" in normalized or "bathroom" in normalized:
        feature = "restroom"
    elif "seat" in normalized or "aisle" in normalized or "path" in normalized:
        feature = "seating"
    elif "entrance" in normalized or "wheelchair" in normalized or "step-free" in normalized:
        feature = "entrance"
    else:
        feature = "unknown"

    barrier_terms = ("not wheelchair", "no wheelchair", "not accessible", "stairs only")
    support_terms = ("wheelchair accessible", "accessible", "step-free", "ada")
    if any(term in normalized for term in barrier_terms):
        return feature, "contradicts_access", 0.6
    if any(term in normalized for term in support_terms):
        return feature, "supports_access", 0.55
    return feature, "unknown", 0.25
