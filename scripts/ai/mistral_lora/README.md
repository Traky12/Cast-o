# Mistral LoRA — FAQs (EducaNova / CASTÚO)

## Requisitos

- **Hardware**: GPU con VRAM adecuada para 7B en 4-bit (típ. ≥16–24 GB). Sin GPU, usar **modelo pequeño** (`TinyLlama`, etc.) y `--no_4bit`.
- **Software**: Python 3.10+, CUDA compatible si usas `bitsandbytes` (Linux/Windows con wheel; macOS suele ir sin 4-bit).
- **Hugging Face**: `huggingface-cli login` si el modelo base es *gated*.

## Instalación

```bash
cd scripts/ai/mistral_lora
pip install -r requirements.txt
```

## Uso

### 1. Entrenamiento

```bash
# GPU + 4-bit (por defecto si CUDA + bitsandbytes disponibles)
python finetune_lora.py --dataset data/educanova_faq.json --output_dir models/mistral_lora

# Forzar sin 4-bit / CPU o depuración
python finetune_lora.py --dataset data/educanova_faq.json --output_dir models/out --no_4bit --model_name TinyLlama/TinyLlama-1.1B-Chat-v1.0 --batch_size 1 --epochs 1
```

Si **CUDA OOM**, baja `--batch_size` (p. ej. 1) o `gradient_accumulation_steps` editando el script.

### 2. Inferencia

Misma `--model_name` que en entrenamiento:

```bash
python inference.py --model_dir models/mistral_lora --model_name mistralai/Mistral-7B-v0.1 --question "¿Cómo accedo a mis cursos?"
python inference.py --model_dir models/mistral_lora --no_4bit --question "hola"
```

### 3. Tests

Desde la raíz del repo:

```bash
pytest scripts/ai/mistral_lora/tests/test_faq_json.py -v
```
### 4. ONNX / edge

`export_onnx.py` **no** exporta un ONNX mágico para 7B; indica rutas realistas (Optimum, GGUF, servicios de inferencia).

## Notas

- El entrenamiento **tokeniza** el dataset; no es el ejemplo roto que pasa solo `text` al `Trainer`.
- **Producción**: DPIA, minimización de datos, anonimización (`scripts/compliance/GDPR/`).
- Ver también `FEDERATED_AND_DP.md` sobre límites FL+DP+LLM.

