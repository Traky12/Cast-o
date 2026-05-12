from __future__ import annotations

import os
from typing import Any, Dict, Optional

import httpx


MISTRAL_API_URL = os.getenv("MISTRAL_API_URL", "https://api.mistral.ai")
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")


async def analyze_with_mistral(
    prompt: str,
    model: str = "mistral-small",
    temperature: float = 0.3,
) -> Dict[str, Any]:
    """
    Llamada mínima a Mistral Chat Completions.
    Devuelve un dict normalizado: {"summary": str, "quality": float}

    Si no hay API key, responde en modo demo (offline).
    """
    if not MISTRAL_API_KEY:
        return {
            "summary": "Modo demo (sin MISTRAL_API_KEY): recomendaciones generadas localmente.",
            "quality": 1.0,
        }

    url = f"{MISTRAL_API_URL.rstrip('/')}/v1/chat/completions"
    headers = {"Authorization": f"Bearer {MISTRAL_API_KEY}"}
    body = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": temperature,
    }

    async with httpx.AsyncClient(timeout=20.0) as client:
        r = await client.post(url, headers=headers, json=body)
        r.raise_for_status()
        data = r.json()

    # Normalización robusta
    content: Optional[str] = None
    try:
        content = data["choices"][0]["message"]["content"]
    except Exception:
        content = str(data)

    return {"summary": content, "quality": 1.0}

