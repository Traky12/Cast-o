# -*- coding: utf-8 -*-
"""Chatbot IA (Mistral) para alertas y recomendaciones CASTUO."""
import os
from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel
import httpx

router = APIRouter(prefix="/chatbot", tags=["chatbot"])


class AskBody(BaseModel):
    question: str
    contexto: str = "{}"


@router.post("/ask", response_model=dict)
async def ask(body: AskBody):
    """Genera respuesta con Mistral usando contexto (drones, riego, NDVI)."""
    api_url = os.getenv("MISTRAL_API_URL", "https://api.mistral.ai")
    api_key = os.getenv("MISTRAL_API_KEY", "")
    if not api_key:
        return {
            "respuesta": "Asistente no configurado. Añade MISTRAL_API_KEY para usar el chatbot."
        }
    prompt = f"""Eres un asistente experto en agricultura de precisión para CASTUO-SYSTEM™.
Responde en español de forma breve y práctica.
Contexto: {body.contexto}

Pregunta: {body.question}"""
    try:
        async with httpx.AsyncClient() as client:
            r = await client.post(
                f"{api_url}/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "mistral-small-latest",
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 256,
                },
                timeout=15.0,
            )
        if r.status_code != 200:
            return {"respuesta": f"Error del servicio: {r.status_code}"}
        data = r.json()
        content = (
            data.get("choices", [{}])[0].get("message", {}).get("content", "")
        )
        return {"respuesta": content.strip()}
    except Exception as e:
        return {"respuesta": f"Error: {str(e)}"}
