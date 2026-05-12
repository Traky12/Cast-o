#!/usr/bin/env python3
# backend/scripts/analyze_with_mistral.py — Análisis de código con Mistral AI (pre-commit)

import json
import os
import sys

# Repo root en path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

def analyze_file(file_path: str) -> int:
    if not os.path.isfile(file_path):
        print(f"Archivo no encontrado: {file_path}")
        return 1
    try:
        from backend.ai.mistral_client import MistralAIClient
        from mistralai.models.chat_completion import ChatMessage
    except ImportError:
        print("Mistral no configurado (mistralai, backend.ai). Saltando análisis.")
        return 0

    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
        code = f.read()

    client = MistralAIClient()
    if not client.client:
        return 0

    prompt = f"""
    CASTÚO-SYSTEM™ v2.0. Normativas: ISO 27001:2022 (A.14.2), EU AI Act (2024/1689), GDPR Art. 25.
    Código:
    ```python
    {code[:12000]}
    ```
    Responde JSON: issues_found (type, description, line, severity, suggested_fix), compliance_status (ok|warning|critical), overall_score (0-100).
    """
    try:
        r = client.chat_completion(
            messages=[
                ChatMessage(role="system", content="Experto en revisión de código Python para sistemas críticos UE."),
                ChatMessage(role="user", content=prompt),
            ],
            log_to_gaiachain=False,
        )
        msg = r["choices"][0]["message"]
        text = msg.get("content", getattr(msg, "content", ""))
        analysis = json.loads(text)
    except json.JSONDecodeError:
        print("Respuesta Mistral no es JSON válido. Continuando.")
        return 0
    except Exception as e:
        print(f"Error Mistral: {e}")
        return 0

    if analysis.get("compliance_status") == "critical":
        print("Estado de cumplimiento crítico. Revisar código.")
        return 1
    print(f"Análisis: score {analysis.get('overall_score', 0)}/100, compliance: {analysis.get('compliance_status', 'ok')}")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Uso: analyze_with_mistral.py <archivo>")
        sys.exit(1)
    sys.exit(analyze_file(sys.argv[1]))
