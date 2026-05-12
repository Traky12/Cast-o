# Mistral-CASTÚO Adapter v1.0

Adapter oficial para integrar Mistral AI con CASTÚO-SYSTEM™ (datasets JSON/CSV/Parquet, API v1, cumplimiento GDPR / AI Act / PAC 2040, trazabilidad GaiaChain).

## Documentación pública

- **Estructura para web:** [docs/mistral-adapter/](../mistral-adapter/index.md) — Overview, Features, Installation, Usage, API Reference, Compliance, Examples.
- **URLs propuestas:** https://castuo-system.github.io/mistral-adapter/ | https://docs.castuo-system.com/mistral-adapter/

## Ubicación del código

- **Módulo:** `api/mistral_castuo_adapter.py`

## Uso rápido

```python
from api.mistral_castuo_adapter import MistralDataManager, MistralAPIClient, APIKeyManager

# Gestión de datos (CSV, JSON, Parquet)
manager = MistralDataManager(region="ES")
df = manager.load_dataset("data/cultivos.csv")

# API Key (cifrada en .env o MISTRAL_API_KEY en desarrollo)
key_manager = APIKeyManager(region="ES")
api_key = key_manager.get_valid_key()

# Consulta Mistral
client = MistralAPIClient(api_key=api_key, region="ES")
response = client.query(model="mistral-small", prompt="Explica agritech cuántica")
print(response["choices"][0]["message"]["content"])
```

## Variables de entorno

| Variable | Uso |
|----------|-----|
| `MISTRAL_API_KEY` | API key en claro (desarrollo). |
| `ENCRYPTED_MISTRAL_API_KEY` | API key cifrada con Fernet (producción). |
| `MISTRAL_ENCRYPTION_KEY_ES` / `_EU` / `_GLOBAL` | Clave Fernet para cifrar/descifrar la API key. |

## Regiones y cumplimiento

- **ES**: GDPR, AI_Act_2024  
- **EU**: GDPR, AI_Act_2024, PAC_2040  
- **GLOBAL**: GDPR  

## Ejemplo completo (Sabionda Educa)

Ejecutar desde la raíz del repo:

```bash
python api/mistral_castuo_adapter.py
```

O importar y llamar a `ejemplo_completo()`:

```python
from api.mistral_castuo_adapter import ejemplo_completo
ejemplo_completo()
```

## Requisitos

- `requests`
- `pandas` (para `load_dataset` con CSV/JSON/Parquet)
- `pyarrow` (opcional, para Parquet)
- `cryptography` (solo si se usa API key cifrada con Fernet)
