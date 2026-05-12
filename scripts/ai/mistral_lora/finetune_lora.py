#!/usr/bin/env python3
"""
Finetuning causal LM con LoRA (FAQs estilo EducaNova / CASTÚO).
Requisitos típicos: GPU con VRAM suficiente para 7B en 4-bit (≈16–24 GB) o modelo pequeño para pruebas.

Importante: el Trainer exige textos tokenizados; este script aplica map + DataCollatorForLanguageModeling (no solo el campo "text" crudo).

Uso:
  pip install -r scripts/ai/mistral_lora/requirements.txt
  huggingface-cli login   # si el modelo es gated (p. ej. Mistral)
  python finetune_lora.py --dataset data/educanova_faq.json --output_dir models/tiny
  python finetune_lora.py --dataset data/educanova_faq.json --output_dir models/m7b --model_name mistralai/Mistral-7B-v0.1 --use_4bit --batch_size 1
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List

import torch
from datasets import Dataset
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
    DataCollatorForLanguageModeling,
    Trainer,
    TrainingArguments,
)

LORA_TARGET_MODULES = ["q_proj", "k_proj", "v_proj", "o_proj"]


def format_prompt(example: Dict[str, str]) -> Dict[str, str]:
    q = example["question"].strip()
    a = example["answer"].strip()
    text = (
        "### Instrucción:\n"
        "Responde la siguiente pregunta de un estudiante de EducaNova de manera clara y concisa.\n\n"
        f"### Pregunta:\n{q}\n\n"
        f"### Respuesta:\n{a}"
    )
    return {"text": text}


def load_json_dataset(path: Path) -> Dataset:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, list) or not raw:
        raise ValueError("El JSON debe ser una lista no vacía")
    for i, row in enumerate(raw):
        if not isinstance(row, dict) or "question" not in row or "answer" not in row:
            raise ValueError(f"Ítem {i}: cada entrada debe tener 'question' y 'answer'")
    return Dataset.from_list(raw).map(format_prompt)


def _can_use_4bit() -> bool:
    if not torch.cuda.is_available():
        return False
    try:
        import bitsandbytes  # noqa: F401
    except ImportError:
        return False
    return True


def load_model_and_tokenizer(model_name: str, *, use_4bit: bool):
    tokenizer = AutoTokenizer.from_pretrained(model_name, use_fast=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "right"

    if use_4bit and _can_use_4bit():
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_compute_dtype=torch.bfloat16,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_use_double_quant=False,
        )
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            quantization_config=bnb_config,
            device_map="auto",
            trust_remote_code=False,
        )
        model = prepare_model_for_kbit_training(model)
    else:
        dtype = torch.float32
        if torch.cuda.is_available():
            dtype = torch.bfloat16 if torch.cuda.is_bf16_supported() else torch.float16
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype=dtype,
            device_map="auto" if torch.cuda.is_available() else None,
            trust_remote_code=False,
        )

    lora_config = LoraConfig(
        r=8,
        lora_alpha=32,
        target_modules=LORA_TARGET_MODULES,
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM",
    )
    model = get_peft_model(model, lora_config)
    if hasattr(model, "enable_input_require_grads"):
        model.enable_input_require_grads()
    model.config.use_cache = False
    model.gradient_checkpointing_enable()
    return model, tokenizer


def tokenize_dataset(ds: Dataset, tokenizer, max_length: int) -> Dataset:
    def _tok(batch: Dict[str, List[str]]) -> Dict[str, List]:
        return tokenizer(
            batch["text"],
            truncation=True,
            max_length=max_length,
            padding=False,
        )

    return ds.map(_tok, batched=True, remove_columns=ds.column_names)


def finetune(
    dataset_path: Path,
    output_dir: Path,
    model_name: str,
    batch_size: int,
    epochs: int,
    learning_rate: float,
    max_length: int,
    use_4bit: bool,
) -> None:
    dataset = load_json_dataset(dataset_path)
    model, tokenizer = load_model_and_tokenizer(model_name, use_4bit=use_4bit)
    tokenized = tokenize_dataset(dataset, tokenizer, max_length)

    collator = DataCollatorForLanguageModeling(tokenizer=tokenizer, mlm=False)

    use_bf16 = torch.cuda.is_available() and torch.cuda.is_bf16_supported()
    training_args = TrainingArguments(
        output_dir=str(output_dir),
        per_device_train_batch_size=batch_size,
        gradient_accumulation_steps=4,
        learning_rate=learning_rate,
        num_train_epochs=epochs,
        logging_steps=10,
        save_steps=100,
        save_total_limit=2,
        fp16=not use_bf16 and torch.cuda.is_available(),
        bf16=use_bf16,
        optim="paged_adamw_8bit" if (use_4bit and _can_use_4bit()) else "adamw_torch",
        lr_scheduler_type="cosine",
        warmup_ratio=0.05,
        report_to="none",
        gradient_checkpointing=True,
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=tokenized,
        data_collator=collator,
    )
    trainer.train()
    output_dir.mkdir(parents=True, exist_ok=True)
    model.save_pretrained(output_dir)
    tokenizer.save_pretrained(output_dir)


def main() -> None:
    p = argparse.ArgumentParser(description="LoRA finetune FAQ (JSON).")
    p.add_argument("--dataset", type=Path, required=True)
    p.add_argument("--output_dir", "--output-dir", type=Path, required=True, dest="output_dir")
    p.add_argument(
        "--model_name",
        "--model-name",
        type=str,
        default="TinyLlama/TinyLlama-1.1B-Chat-v1.0",
        dest="model_name",
    )
    p.add_argument("--batch_size", "--batch-size", type=int, default=2, dest="batch_size")
    p.add_argument("--epochs", type=int, default=3)
    p.add_argument("--learning_rate", "--learning-rate", type=float, default=5e-4, dest="learning_rate")
    p.add_argument("--max_length", "--max-length", type=int, default=512, dest="max_length")
    p.add_argument(
        "--use_4bit",
        "--use-4bit",
        action="store_true",
        dest="use_4bit",
        help="Cuantización 4-bit (CUDA + bitsandbytes; típ. modelos ≥7B)",
    )
    p.add_argument(
        "--no_4bit",
        "--no-4bit",
        action="store_true",
        dest="no_4bit",
        help="Forzar sin 4-bit aunque exista GPU",
    )
    args = p.parse_args()

    if not args.dataset.is_file():
        print(f"No existe dataset: {args.dataset}", file=sys.stderr)
        sys.exit(1)

    use_4bit = args.use_4bit and not args.no_4bit
    if use_4bit and not _can_use_4bit():
        print(
            "AVISO: --use_4bit pedido pero 4-bit no disponible (sin CUDA o sin bitsandbytes).",
            file=sys.stderr,
        )
        use_4bit = False

    if not torch.cuda.is_available() and "7B" in args.model_name:
        print(
            "AVISO: entrenar Mistral 7B sin GPU suele ser inviable por RAM. Usa --model_name pequeño o GPU.",
            file=sys.stderr,
        )

    finetune(
        dataset_path=args.dataset.resolve(),
        output_dir=args.output_dir.resolve(),
        model_name=args.model_name,
        batch_size=args.batch_size,
        epochs=args.epochs,
        learning_rate=args.learning_rate,
        max_length=args.max_length,
        use_4bit=use_4bit,
    )
    print(f"Adaptador guardado en {args.output_dir}")


if __name__ == "__main__":
    main()
