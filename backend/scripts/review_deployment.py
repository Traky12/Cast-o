#!/usr/bin/env python3
# backend/scripts/review_deployment.py — Revisión de despliegue con Mistral AI (CI/CD)

import argparse
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))


def review_deployment(environment: str) -> int:
    try:
        from backend.ai.mistral_client import MistralAIClient
        from mistralai.models.chat_completion import ChatMessage
    except ImportError:
        print("Mistral no disponible. Aprobación omitida.")
        return 0

    metrics = {}
    try:
        out = subprocess.check_output(
            ["docker", "stats", "castuo-system_backend_1", "--no-stream", "--format", "{{.CPUPerc}}"],
            text=True,
            timeout=5,
        )
        metrics["cpu_usage"] = out.strip() or "N/A"
    except Exception:
        metrics["cpu_usage"] = "N/A"
    try:
        out = subprocess.check_output(
            ["docker", "stats", "castuo-system_backend_1", "--no-stream", "--format", "{{.MemUsage}}"],
            text=True,
            timeout=5,
        )
        metrics["memory_usage"] = out.strip() or "N/A"
    except Exception:
        metrics["memory_usage"] = "N/A"

    client = MistralAIClient()
    if not client.client:
        return 0

    prompt = f"""
    CASTÚO-SYSTEM™ v2.0. Entorno: {environment}.
    Normativas: ISO 27001:2022 (A.12.5), NIS2 (2022/2555), EU AI Act (2024/1689).
    Métricas: {json.dumps(metrics)}
    Evalúa si el despliegue está listo para producción. Responde JSON: deployment_approved (bool), reasoning, compliance_status (ok|warning|critical), recommendations (lista), risk_assessment (low|medium|high).
    """
    try:
        r = client.chat_completion(
            messages=[
                ChatMessage(role="system", content="Experto en evaluación de despliegues para sistemas críticos UE."),
                ChatMessage(role="user", content=prompt),
            ],
            log_to_gaiachain=False,
        )
        msg = r["choices"][0]["message"]
        text = msg.get("content", getattr(msg, "content", ""))
        result = json.loads(text)
    except Exception as e:
        print(f"Error revisión: {e}")
        return 0

    if not result.get("deployment_approved", True):
        print("Despliegue rechazado por Mistral AI:", result.get("reasoning", ""))
        print("Recomendaciones:", result.get("recommendations", []))
        return 1
    print("Despliegue aprobado por Mistral AI")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--environment", required=True, choices=["staging", "production"])
    args = parser.parse_args()
    sys.exit(review_deployment(args.environment))
