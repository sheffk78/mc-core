#!/usr/bin/env python3
"""
Leland Mills Hermes Bridge API
Runs alongside Hermes on the Hostinger VPS.
Exposes REST endpoints the Leland Mills web app (Railway) calls.

Architecture:
  Railway (Next.js) -> HTTPS -> Hostinger VPS (this bridge :8080) -> Hermes CLI (local)

Role-based routing:
  ADMIN   -> default profile (full knowledge), CWD: /home/cleaningbot/bridge
  MANAGER -> leland-manager profile (operations, drivers, maintenance, fleet), CWD: bridge-manager
  STAFF   -> leland-staff profile (operations only), CWD: bridge-staff
  DRIVER  -> leland-driver profile (driver only), CWD: bridge-driver

Endpoints:
  GET  /api/health       - health check
  POST /api/chat          - send message, get Hermes response
"""

import os
import asyncio
import uuid
from datetime import datetime, timezone

from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List

# --- Config ---
API_KEY = os.environ.get("BRIDGE_API_KEY", "lm-bridge-key-2026")
HERMES_BIN = "/home/cleaningbot/.hermes/hermes-agent/venv/bin/hermes"
HERMES_USER = "cleaningbot"
HERMES_HOME = f"/home/{HERMES_USER}"
HERMES_TIMEOUT = 200  # seconds

# --- Role -> Profile + Working Directory Mapping ---
# The working directory determines which AGENTS.md Hermes loads.
# Each role-specific dir has its own AGENTS.md with scoped knowledge.
ROLE_CONFIG = {
    "ADMIN": {
        "profile": None,  # default profile (no --profile flag)
        "workdir": f"/home/{HERMES_USER}/bridge",
    },
    "MANAGER": {
        "profile": "leland-manager",
        "workdir": f"/home/{HERMES_USER}/bridge-manager",
    },
    "STAFF": {
        "profile": "leland-staff",
        "workdir": f"/home/{HERMES_USER}/bridge-staff",
    },
    "DRIVER": {
        "profile": "leland-driver",
        "workdir": f"/home/{HERMES_USER}/bridge-driver",
    },
}
DEFAULT_ROLE = "STAFF"

# --- App ---
app = FastAPI(title="Leland Mills Hermes Bridge", version="2.0.0")

PRODUCTION_DOMAIN = "https://archie.lelandmills.com"

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        PRODUCTION_DOMAIN,
        "http://localhost:3000",  # local dev
    ],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# --- Models ---
class ChatRequest(BaseModel):
    message: str
    conversationId: Optional[str] = None
    history: Optional[List[dict]] = None
    role: Optional[str] = None  # "ADMIN" | "MANAGER" | "STAFF" | "DRIVER"

class ChatResponse(BaseModel):
    response: str
    conversationId: str
    createdAt: str

# --- Auth ---
def verify_key(x_api_key: Optional[str] = Header(None)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")

# --- Hermes subprocess ---
async def call_hermes(prompt: str, role: str = DEFAULT_ROLE) -> str:
    role_config = ROLE_CONFIG.get(role, ROLE_CONFIG[DEFAULT_ROLE])
    profile = role_config["profile"]
    workdir = role_config["workdir"]

    env = {
        "HOME": HERMES_HOME,
        "PATH": os.environ.get("PATH", "/usr/local/bin:/usr/bin:/bin"),
    }

    # Build command with optional --profile flag
    cmd = [HERMES_BIN]
    if profile:
        cmd.extend(["--profile", profile])
    cmd.extend(["-z", prompt])

    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        env=env,
        cwd=workdir,
    )

    try:
        stdout, stderr = await asyncio.wait_for(
            proc.communicate(), timeout=HERMES_TIMEOUT
        )
    except asyncio.TimeoutError:
        proc.kill()
        raise HTTPException(status_code=504, detail="Hermes timed out")

    if proc.returncode != 0:
        err = stderr.decode().strip()[:500] if stderr else "Unknown error"
        raise HTTPException(status_code=502, detail=f"Hermes error: {err}")

    return stdout.decode().strip()

# --- Prompt builder ---
def build_prompt(message: str, history: Optional[List[dict]] = None) -> str:
    """Format conversation history + new message into a single prompt for one-shot mode."""
    if not history:
        return message

    parts = []
    # Use last 10 messages for context (keeps prompt manageable)
    for msg in history[-10:]:
        role = msg.get("role", "").upper()
        content = msg.get("content", "")
        if role in ("USER", "ASSISTANT"):
            label = "User" if role == "USER" else "Assistant"
            parts.append(f"{label}: {content}")

    parts.append(f"User: {message}")
    return "\n\n".join(parts)

# --- Routes ---
@app.get("/api/health")
async def health():
    return {"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat()}

@app.post("/api/chat", response_model=ChatResponse)
async def chat(req: ChatRequest, x_api_key: Optional[str] = Header(None)):
    verify_key(x_api_key)

    role = (req.role or DEFAULT_ROLE).upper()
    prompt = build_prompt(req.message, req.history)
    conv_id = req.conversationId or str(uuid.uuid4())

    response_text = await call_hermes(prompt, role=role)

    return ChatResponse(
        response=response_text,
        conversationId=conv_id,
        createdAt=datetime.now(timezone.utc).isoformat(),
    )