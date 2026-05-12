#!/usr/bin/env python3
"""
Export ONNX para un causal LM grande + LoRA no es un único `torch.onnx.export` estable: embeddings,
máscaras causales y bucles de generación no cuadran con el ejemplo naive de tensores enteros.

Rutas realistas en producción:
  - Hugging Face Optimum (`optimum-cli export onnx` / ORTModelForCausalLM)
  - GGUF + llama.cpp / Ollama para edge
  - text-generation-inference, vLLM, etc.

Este script solo comprueba entorno y documenta el siguiente paso; no afirma un ONNX válido para Mistral 7B.
"""

from __future__ import annotations

import argparse
import sys


def main() -> None:
    p = argparse.ArgumentParser(description="Notas de export ONNX / edge (sin export mágico 7B).")
    p.add_argument("--model_dir", type=str, default="", help="Ignorado; reservado para futuro flujo Optimum")
    p.add_argument("--output", type=str, default="", help="Ignorado")
    args = p.parse_args()
    _ = (args.model_dir, args.output)
    print(
        "No se exporta ONNX desde este script.\n"
        "  - Optimum: https://huggingface.co/docs/optimum\n"
        "  - Edge: conversión GGUF / servicio de inferencia con GPU.\n"
        "Ver scripts/ai/mistral_lora/README.md",
        file=sys.stderr,
    )
    sys.exit(2)


if __name__ == "__main__":
    main()
