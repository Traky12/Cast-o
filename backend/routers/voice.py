# -*- coding: utf-8 -*-
"""API de voz: STT + Chatbot + TTS (Slack/Telegram)."""
import base64
import os
from typing import Optional

from fastapi import APIRouter, UploadFile, File, Form
from pydantic import BaseModel
import httpx

router = APIRouter(prefix="/voice", tags=["voice"])


class VoiceChatBody(BaseModel):
    audio: str  # base64
    session_id: Optional[str] = None


@router.post("/chat")
async def voice_chat(audio: str = Form(...), session_id: str = Form("")):
    """Recibe audio base64, transcribe (STT), responde con Mistral, devuelve audio (TTS)."""
    # STT: placeholder (en prod: Google STT o VOSK)
    # Por ahora devolvemos texto sin audio real
    try:
        audio_bytes = base64.b64decode(audio)
    except Exception:
        return {"error": "Audio base64 inválido", "text": "", "audio": ""}
    text = "(STT no configurado; configurar Google/VOSK)"
    # Chatbot
    api_key = os.getenv("MISTRAL_API_KEY", "")
    if api_key:
        try:
            async with httpx.AsyncClient() as client:
                r = await client.post(
                    f"{os.getenv('MISTRAL_API_URL', 'https://api.mistral.ai')}/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": "mistral-small-latest",
                        "messages": [
                            {"role": "user", "content": f"Responde breve en español: {text}"}
                        ],
                        "max_tokens": 150,
                    },
                    timeout=10.0,
                )
            if r.status_code == 200:
                text = (
                    r.json()
                    .get("choices", [{}])[0]
                    .get("message", {})
                    .get("content", text)
                )
        except Exception:
            pass
    # TTS: placeholder (en prod: Google TTS o eSpeak)
    audio_out_b64 = base64.b64encode(b"").decode("utf-8")
    return {"text": text, "audio": audio_out_b64, "action_result": None}
