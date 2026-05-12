#!/usr/bin/env python3
# backend/scripts/analyze_changes.py — Análisis de cambios recientes con Mistral (post-merge)

import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))


def analyze_changes() -> int:
    try:
        from backend.ai.mistral_client import MistralAIClient
        from mistralai.models.chat_completion import ChatMessage
    except ImportError:
        print("Mistral no disponible. Saltando análisis de cambios.")
        return 0

    try:
        diff = subprocess.check_output(
            ["git", "diff", "HEAD~1", "HEAD"],
            text=True,
            timeout=30,
            cwd=os.path.dirname(__file__) or ".",
        )
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
        diff = "Sin cambios o error al obtener diff."

    client = MistralAIClient()
    if not client.client:
        return 0

    prompt = f"""
    CASTÚO-SYSTEM™ v2.0. Normativas: ISO 27001:2022, EU AI Act (2024/1689), GDPR Art. 25.
    Cambios:
    {diff[:8000]}
    Responde JSON: security_impact (issues, severity), compliance_status (issues, affected_normatives), regression_risk (low|medium|high), overall_assessment (safe|warning|critical).
    """
    try:
        r = client.chat_completion(
            messages=[
                ChatMessage(role="system", content="Experto en revisión de cambios en sistemas críticos UE."),
                ChatMessage(role="user", content=prompt),
            ],
            log_to_gaiachain=False,
        )
        msg = r["choices"][0]["message"]
        text = msg.get("content", getattr(msg, "content", ""))
        analysis = text
        out_path = os.path.join(os.path.dirname(__file__), "..", "..", "tmp", "last_changes_analysis.json")
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        try:
            data = json.loads(analysis)
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except json.JSONDecodeError:
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(analysis)
        print(f"Análisis guardado en {out_path}")

        data = json.loads(analysis) if isinstance(analysis, str) else analysis
        if isinstance(data, dict) and data.get("overall_assessment") == "critical":
            print("Análisis crítico. Revisar cambios.")
            return 1
    except Exception as e:
        print(f"Error: {e}")
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(analyze_changes())
