from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field


AUTH_TOKEN = REDACTED"RUNPOD_LLM_WORKER_AUTH_TOKEN") or REDACTED"RUNPOD_VOICE_WORKER_AUTH_TOKEN")
DEFAULT_MODEL = REDACTED"LLM_MODEL_NAME", "Qwen/Qwen2.5-1.5B-Instruct")


class WarmupRequest(BaseModel):
    model: str = DEFAULT_MODEL


class GenerateRequest(BaseModel):
    system: str = "You are Buddy, a careful accessibility evidence reasoning agent."
    prompt: str
    max_new_tokens: int = Field(default=512, ge=32, le=2048)
    temperature: float = Field(default=0.2, ge=0.0, le=2.0)


@dataclass
class Runtime:
    model_name: str = DEFAULT_MODEL
    loaded: bool = False
    tokenizer: Any = None
    model: Any = None

    def warmup(self, model_name: str = DEFAULT_MODEL) -> dict[str, Any]:
        if self.loaded and self.model_name == model_name:
            return self.status("already loaded")

        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer

        self.model_name = model_name
        self.tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
        self.model = AutoModelForCausalLM.from_pretrained(
            model_name,
            device_map="auto",
            torch_dtype="auto" if torch.cuda.is_available() else torch.float32,
            trust_remote_code=True,
        )
        self.loaded = True
        return self.status("loaded")

    def generate(self, request: GenerateRequest) -> dict[str, Any]:
        if not self.loaded:
            self.warmup(self.model_name)

        import torch

        messages = [
            {"role": "system", "content": request.system},
            {"role": "user", "content": request.prompt},
        ]
        text = self.tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        inputs = self.tokenizer([text], return_tensors="pt").to(self.model.device)
        with torch.inference_mode():
            output_ids = self.model.generate(
                **inputs,
                max_new_tokens=request.max_new_tokens,
                do_sample=request.temperature > 0,
                temperature=request.temperature if request.temperature > 0 else None,
                repetition_penalty=1.05,
                eos_token_id=self.tokenizer.eos_token_id,
                pad_token_id=self.tokenizer.eos_token_id,
            )
        generated = output_ids[0][inputs.input_ids.shape[-1] :]
        output = self.tokenizer.decode(generated, skip_special_tokens=True)
        return {"model": self.model_name, "output": output}

    def status(self, message: str = "ok") -> dict[str, Any]:
        return {
            "ready": self.loaded,
            "model": self.model_name,
            "auth_configured": bool(AUTH_TOKEN),
            "message": message,
        }


runtime = Runtime()
app = FastAPI(title="Buddy Runpod LLM Worker")


def require_auth(authorization: str | None) -> None:
    if not AUTH_TOKEN:
        return
    if authorization != f"Bearer {AUTH_TOKEN}":
        raise HTTPException(status_code=401, detail="Invalid worker token")


@app.get("/health")
def health() -> dict[str, Any]:
    return runtime.status()


@app.post("/warmup")
def warmup(request: WarmupRequest, authorization: str | None = Header(default=None)) -> dict[str, Any]:
    require_auth(authorization)
    return runtime.warmup(request.model)


@app.post("/generate")
def generate(request: GenerateRequest, authorization: str | None = Header(default=None)) -> dict[str, Any]:
    require_auth(authorization)
    return runtime.generate(request)
