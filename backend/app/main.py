from __future__ import annotations

from uuid import UUID
from urllib.parse import parse_qs
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from starlette.middleware.base import BaseHTTPMiddleware

from buddy.contracts.buddy_contracts import (
    AccessCheck,
    AccessCheckCreate,
    CallSession,
    CommunityReport,
    EvidenceAnalysis,
)

from .config import load_settings
from .env_utils import setting_value
from .env_validation import router as env_validation_router
from .orchestrator import BuddyOrchestrator
from .storage import store


app = FastAPI(title="Buddy Backend Orchestrator", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


class NoStoreHtmlMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        if request.url.path == "/" or response.headers.get("content-type", "").startswith("text/html"):
            response.headers["Cache-Control"] = "no-store, max-age=0"
        return response


app.add_middleware(NoStoreHtmlMiddleware)
app.include_router(env_validation_router)
FRONTEND_DIST = Path(__file__).resolve().parents[2] / "mobile" / "dist"


def _frontend_index() -> str:
    index = FRONTEND_DIST / "index.html"
    if not index.exists():
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Frontend build not found.")
    return index.read_text(encoding="utf-8")


@app.get("/front")
@app.get("/check")
@app.get("/community")
def recovery_frontend() -> HTMLResponse:
    return HTMLResponse(content=_frontend_index())


def get_orchestrator() -> BuddyOrchestrator:
    return BuddyOrchestrator(load_settings(), store)


def require_check(check_id: UUID) -> AccessCheck:
    check = store.get_check(check_id)
    if check is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Check not found.")
    return check


@app.get("/health")
def health() -> dict:
    settings = load_settings()
    return {
        "status": "ok",
        "storage": "memory",
        "bright_data_configured": bool(
            settings.bright_data_api_key
            and settings.bright_data_serp_zone
            and settings.bright_data_browser_playwright_ws_url
        ),
        "runpod_configured": bool(settings.runpod_api_key),
        "voice_worker_configured": bool(
            settings.runpod_voice_worker_warmup_url and settings.runpod_voice_worker_ws_url
        ),
        "twilio_media_configured": bool(settings.twilio_media_stream_ws_url),
        "twilio_configured": bool(
            settings.twilio_account_sid
            and settings.twilio_auth_token
            and settings.twilio_from_phone_number
        ),
        "supabase_configured": bool(
            settings.supabase_url
            and settings.supabase_publishable_key
            and settings.supabase_secret_key
            and settings.database_url
        ),
        "allow_real_venue_calls": settings.allow_real_venue_calls,
        "ui_renderer": settings.ui_renderer,
    }


@app.post("/checks", response_model=AccessCheck, status_code=status.HTTP_201_CREATED)
def create_check(payload: AccessCheckCreate) -> AccessCheck:
    return get_orchestrator().run_default_flow(payload)


@app.post("/checks/draft", response_model=AccessCheck, status_code=status.HTTP_201_CREATED)
def create_check_draft(payload: AccessCheckCreate) -> AccessCheck:
    return get_orchestrator().create_check(payload)


@app.get("/checks", response_model=list[AccessCheck])
def list_checks() -> list[AccessCheck]:
    return store.list_checks()


@app.get("/checks/{check_id}", response_model=AccessCheck)
def get_check(check_id: UUID) -> AccessCheck:
    return require_check(check_id)


@app.post("/checks/{check_id}/collect", response_model=AccessCheck)
def collect_public_web(check_id: UUID) -> AccessCheck:
    return get_orchestrator().collect_public_web(require_check(check_id))


@app.post("/checks/{check_id}/analyze", response_model=EvidenceAnalysis)
def analyze_evidence(check_id: UUID) -> EvidenceAnalysis:
    return get_orchestrator().analyze_evidence(require_check(check_id))


@app.post("/checks/{check_id}/calls", response_model=CallSession)
def start_call(check_id: UUID) -> CallSession:
    try:
        return get_orchestrator().start_call(require_check(check_id))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@app.post("/checks/{check_id}/finalize", response_model=AccessCheck)
def finalize_check(check_id: UUID) -> AccessCheck:
    return get_orchestrator().finalize(require_check(check_id))


@app.get("/community-reports", response_model=list[CommunityReport])
def list_community_reports() -> list[CommunityReport]:
    return store.list_community_reports()


@app.get("/community-reports/{report_id}", response_model=CommunityReport)
def get_community_report(report_id: UUID) -> CommunityReport:
    report = store.get_community_report(report_id)
    if report is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Community report not found.")
    return report


@app.post("/api/twilio/voice")
@app.post("/webhooks/twilio/voice")
async def twilio_voice() -> Response:
    settings = load_settings()
    media_stream_ws_url = setting_value(
        settings,
        "twilio_media_stream_ws_url",
        "TWILIO_MEDIA_STREAM_WS_URL",
        "RUNPOD_VOICE_WORKER_WS_URL",
    )
    if not media_stream_ws_url:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="TWILIO_MEDIA_STREAM_WS_URL is not configured.",
        )
    twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Connect>
    <Stream url="{media_stream_ws_url}" />
  </Connect>
</Response>"""
    return Response(content=twiml, media_type="application/xml")


@app.post("/api/twilio/status")
@app.post("/webhooks/twilio/status")
async def twilio_status(request: Request) -> dict:
    body = (await request.body()).decode("utf-8", errors="replace")
    form = {key: values[0] for key, values in parse_qs(body).items()}
    return {
        "ok": True,
        "call_sid": form.get("CallSid"),
        "call_status": form.get("CallStatus"),
    }


if FRONTEND_DIST.exists():
    app.mount("/", StaticFiles(directory=FRONTEND_DIST, html=True), name="frontend")
