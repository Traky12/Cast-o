# backend/sabion_omega_2040/app_omega.py
"""SABION_OMEGA_2040 — FastAPI puerto 10000 EXCLUSIVO ADMIN."""
from __future__ import annotations

import os

from fastapi import FastAPI, HTTPException, Header, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

try:
    from .admin_biometric import verify_admin
    from .omega_master import SabionOmega2040, AccessDenied
    from .god_mode_commands import execute_god_command, OMEGA_COMMANDS
except ImportError:
    from admin_biometric import verify_admin
    from omega_master import SabionOmega2040, AccessDenied
    from god_mode_commands import execute_god_command, OMEGA_COMMANDS

app = FastAPI(
    title="SABION_OMEGA_2040 — Admin Exclusivo",
    description="SOLO GREGORIO J JIMÉNEZ BODES. Kyber2048 + God Mode.",
    version="2040.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:3000").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_session_admin: str | None = None


class AuthBody(BaseModel):
    token: str
    biometric: str | None = None


class GodModeBody(BaseModel):
    command: str


def require_admin(authorization: str | None = Header(None), x_admin_token: str | None = Header(None)) -> str:
    """Exige token ADMIN. Header: Authorization: Bearer <token> o X-Admin-Token."""
    token = (authorization or "").replace("Bearer ", "").strip() or (x_admin_token or "").strip()
    ok, identity = verify_admin(token)
    if not ok:
        raise HTTPException(status_code=403, detail="AccessDenied: SOLO GREGORIO J JIMÉNEZ BODES")
    return identity


@app.get("/")
def root():
    return {
        "service": "SABION_OMEGA_2040",
        "auth": "POST /omega/auth",
        "dashboard": "GET /omega/admin_dashboard",
        "god_mode": "POST /omega/god_mode",
        "ws": "/ws/omega_admin",
    }


@app.post("/omega/auth")
def omega_auth(body: AuthBody):
    """Autenticación ADMIN EXCLUSIVO. Token obligatorio."""
    ok, identity = verify_admin(body.token, body.biometric)
    if not ok:
        raise HTTPException(status_code=403, detail="AccessDenied: SOLO GREGORIO J JIMÉNEZ BODES")
    global _session_admin
    _session_admin = identity
    return {"ok": True, "admin": identity, "message": f"{identity} verified ✓"}


@app.get("/omega/admin_dashboard")
def omega_admin_dashboard(authorization: str | None = Header(None), x_admin_token: str | None = Header(None)):
    """Dashboard 2040 — SOLO CON ADMIN_TOKEN."""
    token = (authorization or "").replace("Bearer ", "").strip() or (x_admin_token or "").strip()
    ok, identity = verify_admin(token)
    if not ok:
        raise HTTPException(status_code=403, detail="AccessDenied: SOLO GREGORIO J JIMÉNEZ BODES")
    omega = SabionOmega2040(admin_token=token)
    return omega.get_admin_dashboard(identity)


@app.post("/omega/god_mode")
def omega_god_mode(body: GodModeBody, authorization: str | None = Header(None), x_admin_token: str | None = Header(None)):
    """Comando GOD MODE — OMEGA_KILL_ALL, OMEGA_RESTART_NODES, etc."""
    identity = require_admin(authorization, x_admin_token)
    return execute_god_command(body.command, identity)


@app.websocket("/ws/omega_admin")
async def ws_omega_admin(websocket: WebSocket):
    """Control real-time EXCLUSIVO (requiere auth en primera msg)."""
    await websocket.accept()
    try:
        data = await websocket.receive_json()
        token = (data.get("token") or data.get("authorization") or "").replace("Bearer ", "").strip()
        ok, identity = verify_admin(token)
        if not ok:
            await websocket.send_json({"error": "AccessDenied"})
            return
        omega = SabionOmega2040(admin_token=token)
        await websocket.send_json(omega.get_admin_dashboard(identity))
        while True:
            msg = await websocket.receive_json()
            cmd = msg.get("command")
            if cmd:
                result = execute_god_command(cmd, identity)
                await websocket.send_json(result)
    except Exception:
        pass


@app.get("/omega/commands")
def omega_commands_list(authorization: str | None = Header(None), x_admin_token: str | None = Header(None)):
    """Lista comandos GOD MODE (requiere admin)."""
    require_admin(authorization, x_admin_token)
    return {"commands": list(OMEGA_COMMANDS.keys()), "god_mode": "ENABLED"}


@app.get("/health")
def health():
    return {"status": "healthy", "service": "SABION_OMEGA_2040"}
