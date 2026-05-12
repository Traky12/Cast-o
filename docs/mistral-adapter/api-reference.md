# Referencia de la API

## Clases y métodos

Resumen de las clases públicas y sus métodos:

| Clase / Método | Descripción | Parámetros |
|----------------|-------------|------------|
| **APIKeyManager** | Gestiona API Keys con cifrado y validación. | `region: str` (por defecto `"ES"`) |
| `get_valid_key()` | Devuelve la API Key válida (descifrada o en claro). | — |
| `_encrypt_key(api_key)` | Cifra la API key con Fernet. | `api_key: str` |
| `_decrypt_key(encrypted_key)` | Descifra la API key. | `encrypted_key: str` |
| **MistralDataManager** | Carga y valida datasets con cumplimiento por región. | `region: str` (por defecto `"ES"`) |
| `load_dataset(file_path, file_type)` | Carga un dataset (CSV, JSON o Parquet). | `file_path: str`, `file_type: Optional[str]` |
| `_validate_gdpr_compliance(df)` | Comprueba posibles datos personales (avisos). | `df: DataFrame` |
| **MistralAPIClient** | Cliente HTTP para Mistral API (chat/completions). | `api_key: str`, `region: str`, `rate_limit_per_minute: Optional[int]` |
| `query(model, prompt, ...)` | Envía una consulta y devuelve la respuesta JSON. | `model: str`, `prompt: str`, `temperature: float`, `max_tokens: int`, `stream: bool` |
| `_log_to_gaiachain(request, response)` | Registra la transacción (hash) para GaiaChain. | `request: Dict`, `response: Dict` |

## Configuración por región

| Región | Endpoint | Compliance |
|--------|----------|------------|
| `ES` | `https://api.mistral.ai/v1` | GDPR, AI_Act_2024 |
| `EU` | `https://api.mistral.ai/v1` | GDPR, AI_Act_2024, PAC_2040 |
| `GLOBAL` | `https://api.mistral.ai/v1` | GDPR |

## Variables de entorno

| Variable | Uso |
|----------|-----|
| `MISTRAL_API_KEY` | API key en claro (desarrollo). |
| `ENCRYPTED_MISTRAL_API_KEY` | API key cifrada con Fernet (producción). |
| `MISTRAL_ENCRYPTION_KEY_ES` / `_EU` / `_GLOBAL` | Clave Fernet (base64) para cifrar/descifrar la API key. |
