#!/usr/bin/env python3
# backend/scripts/optimize_code.py — Optimización de código con Mistral (pre-commit)

import os
import subprocess
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))


def optimize_code_with_mistral() -> None:
    try:
        from backend.ai.mistral_client import MistralAIClient
        from mistralai.models.chat_completion import ChatMessage
    except ImportError:
        print("Mistral no disponible. Saltando optimización.")
        return

    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"],
        capture_output=True,
        text=True,
        cwd=os.path.dirname(__file__) or ".",
    )
    changed = [f.strip() for f in (result.stdout or "").strip().split("\n") if f.strip() and f.strip().endswith(".py")]

    client = MistralAIClient()
    if not client.client:
        return

    for file_path in changed:
        if not os.path.isfile(file_path):
            continue
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            code = f.read()
        prompt = f"""
        CASTÚO-SYSTEM™ v2.0. Normativas: ISO 27001, EU AI Act, GDPR Art. 25.
        Objetivos: seguridad, rendimiento, cumplimiento, PEP 8.
        Devuelve SOLO el código Python optimizado, sin explicaciones.
        Código:
        ```python
        {code[:15000]}
        ```
        """
        try:
            r = client.chat_completion(
                messages=[
                    ChatMessage(role="system", content="Experto en optimización Python para sistemas críticos UE."),
                    ChatMessage(role="user", content=prompt),
                ],
                log_to_gaiachain=False,
            )
            msg = r["choices"][0]["message"]
            text = msg.get("content", getattr(msg, "content", ""))
            optimized = text.strip().strip("`").strip()
            if optimized.startswith("python"):
                optimized = optimized[6:].strip()
            if optimized != code and len(optimized) > 100:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(optimized)
                subprocess.run(["git", "add", file_path], check=False, cwd=os.path.dirname(__file__) or ".")
                print(f"Optimizado: {file_path}")
        except Exception as e:
            print(f"Error optimizando {file_path}: {e}")


if __name__ == "__main__":
    optimize_code_with_mistral()
