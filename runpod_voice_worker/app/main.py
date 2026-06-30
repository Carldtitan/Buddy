from __future__ import annotations

import base64
import audioop
import asyncio
import io
import json
import logging
import os
import secrets
import wave
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect, status
from fastapi.responses import JSONResponse, Response
from dotenv import load_dotenv
from pydantic import BaseModel, Field

logger = logging.getLogger("buddy.voice_worker")


PROMPT_PATH = Path(__file__).with_name("system_prompt.md")
ROOT_ENV = Path(__file__).resolve().parents[3] / ".env"
if ROOT_ENV.exists():
    load_dotenv(ROOT_ENV)


class WarmupRequest(BaseModel):
    check_id: str | None = None
    system_prompt: str | None = None
    models: dict[str, str] = Field(default_factory=dict)


class TranscribeRequest(BaseModel):
    audio_base64: str | None = None
    audio_format: str = "mulaw"
    sample_rate: int = 8000
    text: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class SynthesizeRequest(BaseModel):
    text: str
    voice: str = "default"
    audio_format: str = "mulaw"
    sample_rate: int = 8000


class ReasonRequest(BaseModel):
    transcript: list[dict[str, Any]] = Field(default_factory=list)
    facts: dict[str, Any] = Field(default_factory=dict)
    questions: list[str] = Field(default_factory=list)
    asked_questions: list[str] = Field(default_factory=list)
    place: dict[str, Any] = Field(default_factory=dict)


@dataclass
class PlaceholderModel:
    kind: str
    name: str = "placeholder"
    loaded: bool = False
    backend: str = "placeholder"
    error: str | None = None

    async def load(self, model_name: str | None = None, backend: str | None = None) -> None:
        if model_name:
            self.name = model_name
        if backend:
            self.backend = backend
        self.loaded = True
        self.error = None

    async def fail(self, model_name: str, backend: str, error: Exception) -> None:
        self.name = model_name
        self.backend = backend
        self.loaded = False
        self.error = f"{type(error).__name__}: {error}"


@dataclass
class VoiceRuntime:
    stt: PlaceholderModel = field(default_factory=lambda: PlaceholderModel("stt"))
    llm: PlaceholderModel = field(default_factory=lambda: PlaceholderModel("llm"))
    tts: PlaceholderModel = field(default_factory=lambda: PlaceholderModel("tts"))
    system_prompt: str = ""
    active_streams: int = 0
    stt_model: Any = None
    tts_pipeline: Any = None

    @property
    def ready(self) -> bool:
        return self.stt.loaded and self.llm.loaded and self.tts.loaded

    async def warmup(self, request: WarmupRequest) -> dict[str, Any]:
        prompt = request.system_prompt
        if prompt is None:
            prompt = PROMPT_PATH.read_text(encoding="utf-8")
        self.system_prompt = prompt
        await self._load_stt_placeholder(request.models.get("stt") or request.models.get("faster_whisper"))
        await self._load_llm_placeholder(request.models.get("llm") or request.models.get("qwen"))
        await self._load_tts_placeholder(request.models.get("tts") or request.models.get("kokoro"))
        return self.status(message="voice models warmed")

    async def _load_stt_placeholder(self, model_name: str | None = None) -> None:
        name = model_name or REDACTED"STT_MODEL_NAME") or REDACTED"STT_MODEL") or "small.en"
        if name.startswith("Systran/faster-whisper-"):
            name = name.removeprefix("Systran/faster-whisper-")
        try:
            import whisper

            device = "cuda" if _cuda_available() else "cpu"
            self.stt_model = await asyncio.to_thread(whisper.load_model, name, device=device)
            await self.stt.load(name, backend=f"openai-whisper/{device}")
        except Exception as exc:
            logger.exception("Failed to load Whisper")
            await self.stt.fail(name, "openai-whisper", exc)

    async def _load_llm_placeholder(self, model_name: str | None = None) -> None:
        name = model_name or REDACTED"LLM_MODEL_NAME") or "Qwen/Qwen2.5-1.5B-Instruct"
        await self.llm.load(name, backend="qwen-on-llm-pod")

    async def _load_tts_placeholder(self, model_name: str | None = None) -> None:
        name = model_name or REDACTED"TTS_MODEL_NAME") or "hexgrad/Kokoro-82M"
        try:
            from kokoro import KPipeline

            lang_code = REDACTED"KOKORO_LANG_CODE", "a")
            self.tts_pipeline = await asyncio.to_thread(KPipeline, lang_code=lang_code)
            await self.tts.load(name, backend=f"kokoro/{lang_code}")
        except Exception as exc:
            logger.exception("Failed to load Kokoro")
            await self.tts.fail(name, "kokoro", exc)

    def status(self, message: str = "ok") -> dict[str, Any]:
        return {
            "ready": self.ready,
            "stt_loaded": self.stt.loaded,
            "llm_loaded": self.llm.loaded,
            "tts_loaded": self.tts.loaded,
            "models": {
                "stt": {"name": self.stt.name, "backend": self.stt.backend},
                "llm": {"name": self.llm.name, "backend": self.llm.backend},
                "tts": {"name": self.tts.name, "backend": self.tts.backend},
            },
            "errors": {
                "stt": self.stt.error,
                "llm": self.llm.error,
                "tts": self.tts.error,
            },
            "active_streams": self.active_streams,
            "auth_configured": bool(_configured_auth_token()),
            "message": message,
        }


runtime = VoiceRuntime()
app = FastAPI(title="Buddy Runpod Voice Worker")


def _configured_auth_token() -> str | None:
    for key in ("BUDDY_VOICE_WORKER_AUTH_TOKEN", "RUNPOD_VOICE_WORKER_AUTH_TOKEN", "VOICE_WORKER_AUTH_TOKEN"):
        token = REDACTEDkey)
        if token:
            return token
    return None


def _candidate_tokens(headers: Any, query_params: Any | None = None) -> list[str]:
    values: list[str] = []
    authorization = headers.get("authorization") if headers else None
    if authorization:
        scheme, _, token = authorization.partition(" ")
        values.append(token if scheme.lower() == "bearer" else authorization)
    for header in ("x-buddy-voice-token", "x-runpod-auth-token"):
        token = headers.get(header) if headers else None
        if token:
            values.append(token)
    if query_params is not None:
        for param in ("token", "auth_token"):
            token = query_params.get(param)
            if token:
                values.append(token)
    return [value for value in values if value]


def _is_authorized(headers: Any, query_params: Any | None = None) -> bool:
    configured = _configured_auth_token()
    if not configured:
        return True
    return any(secrets.compare_digest(configured, token) for token in _candidate_tokens(headers, query_params))


@app.middleware("http")
async def auth_token_middleware(request: Request, call_next: Any) -> Any:
    public_paths = {"/health", "/twilio/voice", "/twilio/status"}
    if request.url.path in public_paths or _is_authorized(request.headers, request.query_params):
        return await call_next(request)
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={"detail": "Missing or invalid voice worker auth token"},
        headers={"WWW-Authenticate": "Bearer"},
    )


@app.get("/health")
async def health() -> dict[str, Any]:
    return runtime.status()


@app.post("/twilio/voice")
async def twilio_voice() -> Response:
    public_base = REDACTED"RUNPOD_VOICE_WORKER_PUBLIC_URL", "").rstrip("/")
    if public_base.startswith("https://"):
        ws_url = "wss://" + public_base.removeprefix("https://") + "/twilio-media"
    else:
        ws_url = REDACTED"TWILIO_MEDIA_STREAM_WS_URL", "")
    token = _configured_auth_token()
    if token and "token=" not in ws_url:
        separator = "&" if "?" in ws_url else "?"
        ws_url = f"{ws_url}{separator}token={token}"
    twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Connect>
    <Stream url="{ws_url}" />
  </Connect>
</Response>"""
    return Response(content=twiml, media_type="application/xml")


@app.post("/twilio/status")
async def twilio_status() -> dict[str, Any]:
    return {"ok": True}


@app.post("/warmup")
async def warmup(request: WarmupRequest) -> dict[str, Any]:
    return await runtime.warmup(request)


def _require_warm() -> None:
    if not runtime.ready:
        logger.info("voice worker used before warmup; loading placeholders")


def _decode_audio_length(audio_base64: str | None) -> int:
    if not audio_base64:
        return 0


def _cuda_available() -> bool:
    try:
        import torch

        return bool(torch.cuda.is_available())
    except Exception:
        return False


def _mulaw_base64_to_float32(audio_base64: str) -> Any:
    import numpy as np

    mulaw = base64.b64decode(audio_base64, validate=False)
    pcm16 = audioop.ulaw2lin(mulaw, 2)
    return np.frombuffer(pcm16, dtype="<i2").astype("float32") / 32768.0


def _pcm_float32_to_mulaw_base64(audio: Any, source_rate: int, target_rate: int = 8000) -> str:
    import numpy as np

    clipped = np.clip(audio, -1.0, 1.0)
    pcm16 = (clipped * 32767.0).astype("<i2").tobytes()
    if source_rate != target_rate:
        pcm16, _ = audioop.ratecv(pcm16, 2, 1, source_rate, target_rate, None)
    mulaw = audioop.lin2ulaw(pcm16, 2)
    return base64.b64encode(mulaw).decode("ascii")


def _wav_base64_to_float32(audio_base64: str) -> tuple[Any, int]:
    import numpy as np

    payload = base64.b64decode(audio_base64, validate=False)
    with wave.open(io.BytesIO(payload), "rb") as wav:
        sample_rate = wav.getframerate()
        sample_width = wav.getsampwidth()
        channels = wav.getnchannels()
        frames = wav.readframes(wav.getnframes())
    if sample_width != 2:
        frames = audioop.lin2lin(frames, sample_width, 2)
    if channels > 1:
        frames = audioop.tomono(frames, 2, 0.5, 0.5)
    audio = np.frombuffer(frames, dtype="<i2").astype("float32") / 32768.0
    return audio, sample_rate
    try:
        return len(base64.b64decode(audio_base64, validate=False))
    except Exception:
        return 0


async def transcribe_audio(request: TranscribeRequest) -> dict[str, Any]:
    _require_warm()
    byte_count = _decode_audio_length(request.audio_base64)
    text = request.text.strip() if request.text else ""
    confidence = 1.0 if text else 0.0
    model = runtime.stt_model
    if not text and model is not None and request.audio_base64:
        try:
            if request.audio_format.lower() in {"mulaw", "ulaw"}:
                audio = _mulaw_base64_to_float32(request.audio_base64)
                sample_rate = 8000
            elif request.audio_format.lower() == "wav":
                audio, sample_rate = _wav_base64_to_float32(request.audio_base64)
            else:
                audio = _mulaw_base64_to_float32(request.audio_base64)
                sample_rate = request.sample_rate
            if sample_rate != 16000:
                pcm16 = (audio * 32767.0).astype("<i2").tobytes()
                pcm16, _ = audioop.ratecv(pcm16, 2, 1, sample_rate, 16000, None)
                import numpy as np

                audio = np.frombuffer(pcm16, dtype="<i2").astype("float32") / 32768.0
            output = await asyncio.to_thread(model.transcribe, audio, language="en", fp16=_cuda_available())
            text = str(output.get("text") or "").strip()
            confidence = 1.0 if text else 0.0
        except Exception as exc:
            logger.exception("STT transcription failed")
            return {
                "text": "",
                "confidence": 0.0,
                "is_final": True,
                "audio": {"format": request.audio_format, "sample_rate": request.sample_rate, "bytes": byte_count},
                "metadata": request.metadata,
                "error": f"{type(exc).__name__}: {exc}",
                "placeholder": False,
            }
    return {
        "text": text,
        "confidence": confidence,
        "is_final": True,
        "audio": {
            "format": request.audio_format,
            "sample_rate": request.sample_rate,
            "bytes": byte_count,
        },
        "metadata": request.metadata,
        "placeholder": False,
        "message": "ok",
    }


async def synthesize_text(request: SynthesizeRequest) -> dict[str, Any]:
    _require_warm()
    if runtime.tts_pipeline is not None:
        try:
            voice = request.voice if request.voice != "default" else REDACTED"VOICE_NAME", "af_heart")
            generator = runtime.tts_pipeline(request.text, voice=voice, speed=1.0)
            audio_chunks = []
            sample_rate = 24000
            for item in generator:
                if len(item) >= 3:
                    audio_chunks.append(item[2])
            if audio_chunks:
                import numpy as np

                audio = np.concatenate(audio_chunks)
                if request.audio_format.lower() in {"mulaw", "ulaw"}:
                    audio_base64 = _pcm_float32_to_mulaw_base64(audio, sample_rate, request.sample_rate)
                    return {
                        "audio_base64": audio_base64,
                        "audio_format": request.audio_format,
                        "sample_rate": request.sample_rate,
                        "voice": voice,
                        "placeholder": False,
                    }
                return {
                    "audio_base64": base64.b64encode(audio.astype("float32").tobytes()).decode("ascii"),
                    "audio_format": "f32le",
                    "sample_rate": sample_rate,
                    "voice": voice,
                    "placeholder": False,
                }
        except Exception as exc:
            logger.exception("TTS synthesis failed")
            return {
                "audio_base64": "",
                "audio_format": request.audio_format,
                "sample_rate": request.sample_rate,
                "voice": request.voice,
                "placeholder": False,
                "error": f"{type(exc).__name__}: {exc}",
            }
    text_bytes = request.text.encode("utf-8")
    return {
        "audio_base64": base64.b64encode(text_bytes).decode("ascii"),
        "audio_format": request.audio_format,
        "sample_rate": request.sample_rate,
        "voice": request.voice,
        "placeholder": True,
    }


def choose_next_question(request: ReasonRequest) -> dict[str, Any]:
    _require_warm()
    asked = {question.strip().lower() for question in request.asked_questions if question.strip()}
    for question in request.questions:
        if question.strip().lower() not in asked:
            return {"next_question": question, "done": False, "reason": "planned_question_remaining"}

    fact_questions = [
        ("step_free_entrance", "Is there an accessible entrance that works for the request today?"),
        ("accessible_restroom", "Is there an accessible customer restroom available today?"),
        ("wheelchair_seating_or_path", "Is there a usable interior path or seating arrangement for the request?"),
        ("temporary_blockers", "Are there any temporary accessibility blockers today?"),
    ]
    for key, question in fact_questions:
        if request.facts.get(key) in {None, "", "unknown", []} and question.lower() not in asked:
            return {"next_question": question, "done": False, "reason": f"missing_{key}"}

    return {"next_question": None, "done": True, "reason": "all_required_questions_addressed"}


@app.post("/transcribe")
async def transcribe(request: TranscribeRequest) -> dict[str, Any]:
    return await transcribe_audio(request)


@app.post("/synthesize")
async def synthesize(request: SynthesizeRequest) -> dict[str, Any]:
    return await synthesize_text(request)


@app.post("/reason-next-question")
async def reason_next_question(request: ReasonRequest) -> dict[str, Any]:
    return choose_next_question(request)


@app.websocket("/twilio-media")
async def twilio_media(websocket: WebSocket) -> None:
    if not _is_authorized(websocket.headers, websocket.query_params):
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Missing or invalid auth token")
        return
    await websocket.accept()
    runtime.active_streams += 1
    stream_sid: str | None = None
    transcript: list[dict[str, Any]] = []
    try:
        while True:
            raw_message = await websocket.receive_text()
            try:
                message = json.loads(raw_message)
            except json.JSONDecodeError:
                await websocket.send_json({"event": "error", "message": "invalid JSON"})
                continue

            event = message.get("event")
            if event == "connected":
                continue
            elif event == "start":
                stream_sid = (message.get("start") or {}).get("streamSid") or message.get("streamSid")
                greeting = REDACTED
                    "BUDDY_CALL_GREETING",
                    "Hi, this is Buddy calling to quickly confirm accessibility details today.",
                )
                speech = await synthesize_text(SynthesizeRequest(text=greeting, audio_format="mulaw", sample_rate=8000))
                if stream_sid and speech.get("audio_base64"):
                    await websocket.send_json(
                        {"event": "media", "streamSid": stream_sid, "media": {"payload": speech["audio_base64"]}}
                    )
                    await websocket.send_json({"event": "mark", "streamSid": stream_sid, "mark": {"name": "buddy_greeting"}})
            elif event == "media":
                media = message.get("media") or {}
                result = await transcribe_audio(
                    TranscribeRequest(
                        audio_base64=media.get("payload"),
                        audio_format="mulaw",
                        sample_rate=8000,
                        metadata={"streamSid": stream_sid, "track": media.get("track")},
                    )
                )
                if result["text"]:
                    transcript.append({"speaker": "venue", "text": result["text"]})
            elif event == "mark":
                continue
            elif event == "stop":
                break
            else:
                continue
    except WebSocketDisconnect:
        logger.info("Twilio media websocket disconnected")
    finally:
        runtime.active_streams = max(0, runtime.active_streams - 1)
