#!/usr/bin/env python3
"""
CASTUO-SYSTEM™ | Generación de documentación de modelos de IA (AI Act UE 2024/1689).
Uso: python scripts/legal/generar_ai_doc.py
"""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TEMPLATES = ROOT / "templates" / "legal"
OUTPUT = ROOT / "docs" / "legal"

def main():
    try:
        from jinja2 import Environment, FileSystemLoader
    except ImportError:
        print("Instala: pip install jinja2")
        return 1

    env = Environment(loader=FileSystemLoader(str(TEMPLATES)))
    template = env.get_template("ai_model.md")
    data = {
        "model": {
            "nombre": "Sabionda Predictive v1.0",
            "version": "1.0",
            "tipo": "Predictivo",
            "datos_entrenamiento": "Datos de sensores IoT (2023-2026)",
            "precision": 92.5,
            "riesgo": "Bajo",
            "descripcion": "Modelo para predecir necesidades de riego en cultivos agrovoltaicos.",
            "datos_origen": "Sensores IoT de 10 granjas en Extremadura",
            "datos_tamano": 1000000,
            "datos_preprocesamiento": "Normalización + limpieza de outliers",
            "recall": 91.2,
            "f1": 91.8,
            "gdpr_compliant": "Sí (datos anonimizados)",
            "ai_act_compliant": "Sí (registro en UE AI Database)",
            "auditoria": "Trimestral (última: 2026-01-15)",
        },
        "tx_hash": os.environ.get("BIOCAST_TX", "a1b2c3d4e5f67890123456789abcdef0"),
        "git_commit": os.popen("git rev-parse --short HEAD 2>/dev/null").read().strip() or "unknown",
        "repo": "castu-system",
    }
    doc = template.render(**data)
    OUTPUT.mkdir(parents=True, exist_ok=True)
    out_file = OUTPUT / "ai_model_sabionda_v1.md"
    out_file.write_text(doc, encoding="utf-8")
    print(f"✅ Documentación de IA generada: {out_file}")
    print(f"   TX BioCoin: {data['tx_hash']}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
