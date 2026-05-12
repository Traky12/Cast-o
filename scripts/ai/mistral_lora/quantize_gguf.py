#!/usr/bin/env python3
"""
Fusiona adaptador LoRA en el modelo base (HF) y delega la conversión a GGUF en **llama.cpp**.

Requisitos para el paso GGUF:
  - Clonar https://github.com/ggerganov/llama.cpp y definir:
      set CASTUO_LLAMA_CPP_ROOT=C:\\ruta\\llama.cpp
  - Python con `gguf` / dependencias que exija `convert_hf_to_gguf.py` (ver doc de llama.cpp).

Sin CASTUO_LLAMA_CPP_ROOT: solo fusiona a un directorio HF (`--merged_hf_dir`) y muestra instrucciones.

No existe un `pip install ggml` mágico que sustituya a llama.cpp para conversión seria.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import tempfile
from pathlib import Path


def merge_lora_to_hf(adapter_dir: Path, base_model: str, merged_dir: Path) -> None:
    import torch
    from peft import PeftModel
    from transformers import AutoModelForCausalLM, AutoTokenizer

    tok = AutoTokenizer.from_pretrained(str(adapter_dir), use_fast=True)
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token
    base = AutoModelForCausalLM.from_pretrained(
        base_model,
        torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
        device_map="auto" if torch.cuda.is_available() else None,
        trust_remote_code=False,
    )
    m = PeftModel.from_pretrained(base, str(adapter_dir))
    merged = m.merge_and_unload()
    merged_dir.mkdir(parents=True, exist_ok=True)
    merged.save_pretrained(merged_dir)
    tok.save_pretrained(merged_dir)


def run_llama_cpp_convert(llama_cpp: Path, hf_dir: Path, outfile: Path, outtype: str) -> None:
    script = llama_cpp / "convert_hf_to_gguf.py"
    if not script.is_file():
        raise FileNotFoundError(f"No se encuentra {script} (¿llama.cpp actualizado?)")
    outfile.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        sys.executable,
        str(script),
        str(hf_dir),
        "--outfile",
        str(outfile),
        "--outtype",
        outtype,
    ]
    subprocess.run(cmd, check=True)


def main() -> None:
    p = argparse.ArgumentParser(description="LoRA → HF fusionado → GGUF (vía llama.cpp).")
    p.add_argument("--model_dir", "--model-dir", type=Path, required=True, dest="model_dir")
    p.add_argument("--output", type=Path, required=True, help="Fichero .gguf de salida")
    p.add_argument(
        "--outtype",
        type=str,
        default="q4_k_m",
        help="Tipo GGUF (ej. f16, q8_0, q4_k_m; ver convert_hf_to_gguf.py)",
    )
    p.add_argument("--model_base", "--model-base", type=str, required=True, dest="model_base")
    p.add_argument(
        "--merged_hf_dir",
        type=Path,
        default=None,
        help="Si se omite, se usa un directorio temporal",
    )
    args = p.parse_args()

    merged = args.merged_hf_dir or Path(tempfile.mkdtemp(prefix="castuo_merged_"))
    print(f"Fusionando LoRA + {args.model_base} → {merged} …")
    merge_lora_to_hf(args.model_dir.resolve(), args.model_base, merged.resolve())

    root = os.environ.get("CASTUO_LLAMA_CPP_ROOT", "").strip()
    if not root:
        print(
            "Listo el modelo fusionado en HF.\n"
            "Define CASTUO_LLAMA_CPP_ROOT apuntando al clon de llama.cpp y vuelve a ejecutar\n"
            "con el mismo --merged_hf_dir para generar el .gguf, o ejecuta manualmente:\n"
            f'  python convert_hf_to_gguf.py "{merged}" --outfile "{args.output}" --outtype {args.outtype}',
            file=sys.stderr,
        )
        sys.exit(2)

    llama = Path(root)
    print(f"Convirtiendo con llama.cpp en {llama} …")
    run_llama_cpp_convert(llama, merged.resolve(), args.output.resolve(), args.outtype)
    print(f"GGUF escrito en {args.output}")


if __name__ == "__main__":
    main()
