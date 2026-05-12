# backend/sabion_edu/app_edu.py
"""Protocolo educativo federado v5.0 — Puerto 9500. Enroll, progress, certificates, levelup, dashboard."""
from __future__ import annotations

import os

from fastapi import FastAPI, Query, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

try:
    from .edu_enroll import enroll
    from .edu_progress import report_progress
    from .edu_certificates import get_certificates, levelup
    from .edu_models import STUDENTS, CERTIFICATES, REVENUE_PER_CERT
except ImportError:
    from edu_enroll import enroll
    from edu_progress import report_progress
    from edu_certificates import get_certificates, levelup
    from edu_models import STUDENTS, CERTIFICATES, REVENUE_PER_CERT

app = FastAPI(
    title="SABION EDU v5.0 — Protocolo educativo federado",
    description="Microcredenciales blockchain TRL1-9, Sabionda orquestación, certificados IPFS.",
    version="5.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:9500").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class EnrollBody(BaseModel):
    student: str
    nivel: str = "TRL2"
    empresa: str = ""


class ProgressBody(BaseModel):
    student: str
    progress_pct: float
    skill: str = ""


class LevelUpBody(BaseModel):
    student: str
    target_nivel: str


@app.get("/")
def root():
    return {
        "service": "SABION_EDU_v5.0",
        "enroll": "POST /edu/enroll",
        "progress": "POST /edu/progress",
        "certificates": "GET /edu/certificates",
        "levelup": "POST /edu/levelup",
        "dashboard": "GET /edu/dashboard",
        "ws": "/ws/edu",
    }


@app.post("/edu/enroll")
def edu_enroll(body: EnrollBody):
    """Inscripción estudiante → certificado TRL inicial + Sabionda 3/3."""
    return enroll(body.student, body.nivel, body.empresa)


@app.post("/edu/progress")
def edu_progress(body: ProgressBody):
    """Reportar progreso → Agentes evalúan → Sabionda orchestrate."""
    return report_progress(body.student, body.progress_pct, body.skill)


@app.get("/edu/certificates")
def edu_certificates(student: str | None = Query(None)):
    """Mis certificados blockchain TRL (MerkleProof + IPFS)."""
    return {"certificates": get_certificates(student), "count": len(get_certificates(student))}


@app.post("/edu/levelup")
def edu_levelup(body: LevelUpBody):
    """Solicitar ascenso nivel → Consenso 2/3 Sabionda → Nuevo certificado."""
    return levelup(body.student, body.target_nivel)


@app.get("/edu/dashboard")
def edu_dashboard(student: str | None = Query(None)):
    """Progreso, Revenue predict, TRL status, certificados. Dashboard educativo LIVE."""
    certs = get_certificates(student)
    total_revenue = sum(c.get("revenue_eur", REVENUE_PER_CERT.get(c.get("nivel", 1), 0)) for c in certs)
    students_list = list(STUDENTS.values()) if not student else ([STUDENTS[student]] if student in STUDENTS else [])
    return {
        "protocol": "SABION_EDU_v5.0",
        "students_count": len(STUDENTS),
        "certificates_count": len(certs),
        "revenue_predicted_eur": total_revenue,
        "revenue_display": f"€{total_revenue // 1000}K",
        "students": students_list,
        "certificates": certs[:25],
        "revenue_2026_arr": "€705K",
    }


@app.websocket("/ws/edu")
async def ws_edu(websocket: WebSocket):
    """Real-time progreso + certificados LIVE."""
    await websocket.accept()
    try:
        import asyncio
        while True:
            data = await websocket.receive_json()
            cmd = data.get("command")
            if cmd == "dashboard":
                await websocket.send_json({
                    "certificates_count": len(CERTIFICATES),
                    "students_count": len(STUDENTS),
                    "revenue": f"€{sum(c.get('revenue_eur', 0) for c in CERTIFICATES)}",
                })
            elif cmd == "progress" and data.get("student"):
                r = report_progress(data["student"], data.get("progress_pct", 0))
                await websocket.send_json(r)
            else:
                await websocket.send_json({"certificates": get_certificates(), "count": len(CERTIFICATES)})
    except Exception:
        pass


@app.get("/health")
def health():
    return {"status": "healthy", "service": "SABION_EDU_v5.0"}
