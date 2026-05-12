#!/usr/bin/env python3
# backend/scripts/propose_improvements.py — Propuestas de mejora con Mistral (post-merge)

import os
import subprocess
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))


def propose_improvements() -> int:
    try:
        from backend.ai.mistral_client import MistralAIClient
        from mistralai.models.chat_completion import ChatMessage
    except ImportError:
        print("Mistral no disponible.")
        return 0

    try:
        diff = subprocess.check_output(
            ["git", "diff", "HEAD~1", "HEAD", "--stat"],
            text=True,
            timeout=10,
            cwd=os.path.dirname(__file__) or ".",
        )
    except Exception:
        diff = "Sin diff disponible."

    client = MistralAIClient()
    if not client.client:
        return 0

    prompt = f"""
    CASTÚO-SYSTEM™ v2.0. Normativas: ISO 27001, EU AI Act, GDPR.
    Resumen de cambios: {diff[:2000]}
    Propón hasta 5 mejoras concretas (seguridad, cumplimiento, rendimiento). Lista numerada breve.
    """
    try:
        r = client.chat_completion(
            messages=[
                ChatMessage(role="system", content="Experto en mejoras de sistemas críticos UE."),
                ChatMessage(role="user", content=prompt),
            ],
            log_to_gaiachain=False,
        )
        text = r["choices"][0]["message"].content if isinstance(r["choices"][0]["message"], dict) else r["choices"][0].message.content
        print("Propuestas de mejora:\n", text[:2000])
    except Exception as e:
        print(f"Error: {e}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(propose_improvements())
