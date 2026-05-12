#!/usr/bin/env python3
"""
Inferencia FAQ:
  --engine lora   → Transformers + PEFT (GPU típico o CPU con modelo pequeño)
  --engine gguf   → llama-cpp-python sobre fichero .gguf (CPU/GPU según wheel)

Trazabilidad opcional: --trace_json y/o witness GaiaChain (ver trace_hash.py).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import torch
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

from trace_hash import log_inference_event


def build_prompt(question: str) -> str:
    q = question.strip()
    return (
        "### Instrucción:\n"
        "Responde la siguiente pregunta de un estudiante de EducaNova de manera clara y concisa.\n\n"
        f"### Pregunta:\n{q}\n\n"
        "### Respuesta:\n"
    )


def infer_gguf(
    gguf_path: Path,
    question: str,
    max_tokens: int,
    temperature: float,
) -> str:
    try:
        from llama_cpp import Llama
    except ImportError as e:
        raise SystemExit(
            "Instala: pip install llama-cpp-python (ver requirements-gguf.txt)"
        ) from e

    prompt = build_prompt(question)
    llm = Llama(model_path=str(gguf_path), n_ctx=4096, verbose=False)
    out = llm(
        prompt,
        max_tokens=max_tokens,
        temperature=temperature if temperature > 0 else 0.0,
        top_p=0.95,
        stop=["### Instrucción:", "### Pregunta:"],
    )
    chunk = out["choices"][0].get("text", "")
    return (chunk.split("### Respuesta:")[-1] if "### Respuesta:" in chunk else chunk).strip()


def infer_lora(
    model_dir: Path,
    model_name: str,
    question: str,
    max_new_tokens: int,
    temperature: float,
    use_4bit: bool,
) -> str:
    tok_path = model_dir if (model_dir / "tokenizer_config.json").is_file() else None
    tokenizer = AutoTokenizer.from_pretrained(
        str(tok_path) if tok_path else model_name,
        use_fast=True,
    )
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    model_kwargs: dict = {"trust_remote_code": False}
    if use_4bit and torch.cuda.is_available():
        try:
            import bitsandbytes  # noqa: F401

            model_kwargs["quantization_config"] = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_compute_dtype=torch.bfloat16,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_use_double_quant=False,
            )
            model_kwargs["device_map"] = "auto"
        except ImportError:
            use_4bit = False

    if not use_4bit or not torch.cuda.is_available():
        dtype = torch.float16 if torch.cuda.is_available() else torch.float32
        model_kwargs["torch_dtype"] = dtype
        model_kwargs["device_map"] = "auto" if torch.cuda.is_available() else None

    base = AutoModelForCausalLM.from_pretrained(model_name, **model_kwargs)
    if model_kwargs.get("device_map") is None:
        base = base.to("cpu")
    model = PeftModel.from_pretrained(base, str(model_dir))
    model.eval()

    prompt = build_prompt(question)
    inputs = tokenizer(prompt, return_tensors="pt")
    dev = next(model.parameters()).device
    inputs = {k: v.to(dev) for k, v in inputs.items()}
    with torch.no_grad():
        out = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            temperature=temperature if temperature > 0 else None,
            do_sample=temperature > 0,
            pad_token_id=tokenizer.pad_token_id,
            eos_token_id=tokenizer.eos_token_id,
            use_cache=True,
        )
    full = tokenizer.decode(out[0], skip_special_tokens=True)
    if "### Respuesta:" in full:
        return full.split("### Respuesta:")[-1].strip()
    return full[len(prompt) :].strip()


def main() -> None:
    p = argparse.ArgumentParser(description="Inferencia FAQ (LoRA HF o GGUF).")
    p.add_argument("--engine", type=str, choices=("lora", "gguf"), default="lora")
    p.add_argument("--model", type=Path, default=None, help="Ruta .gguf si engine=gguf")
    p.add_argument("--model_dir", "--model-dir", type=Path, default=None, dest="model_dir")
    p.add_argument(
        "--model_name",
        "--model-name",
        type=str,
        default="TinyLlama/TinyLlama-1.1B-Chat-v1.0",
        dest="model_name",
    )
    p.add_argument("--question", type=str, required=True)
    p.add_argument("--max_new_tokens", "--max-new-tokens", type=int, default=256, dest="max_new_tokens")
    p.add_argument("--temperature", type=float, default=0.7)
    p.add_argument("--use_4bit", "--use-4bit", action="store_true", dest="use_4bit")
    p.add_argument("--trace_json", type=Path, default=None, help="Append JSONL con hash de la interacción")
    args = p.parse_args()

    if args.engine == "gguf":
        if not args.model or not args.model.is_file():
            print("--engine gguf requiere --model ruta.gguf existente", file=sys.stderr)
            sys.exit(1)
        text = infer_gguf(args.model.resolve(), args.question, args.max_new_tokens, args.temperature)
        ref = str(args.model)
    else:
        if not args.model_dir or not args.model_dir.is_dir():
            print("--engine lora requiere --model_dir", file=sys.stderr)
            sys.exit(1)
        if not torch.cuda.is_available() and "7B" in args.model_name:
            print("AVISO: 7B en CPU puede fallar por RAM.", file=sys.stderr)
        text = infer_lora(
            args.model_dir.resolve(),
            args.model_name,
            args.question,
            args.max_new_tokens,
            args.temperature,
            use_4bit=args.use_4bit,
        )
        ref = f"{args.model_name}+{args.model_dir}"

    print(f"Respuesta: {text}")

    trace = log_inference_event(
        engine=args.engine,
        question=args.question,
        answer=text,
        model_ref=ref,
    )
    if args.trace_json:
        args.trace_json.parent.mkdir(parents=True, exist_ok=True)
        with args.trace_json.open("a", encoding="utf-8") as f:
            f.write(json.dumps(trace, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
