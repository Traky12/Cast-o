# FAQ — Preguntas frecuentes

## Configuración y tokens

### ¿Dónde pongo la API key de Mistral?

En desarrollo, define `MISTRAL_API_KEY` en tu archivo `.env` (en la raíz del proyecto). En producción, usa `ENCRYPTED_MISTRAL_API_KEY` y una clave de cifrado Fernet en `MISTRAL_ENCRYPTION_KEY_ES` (o `_EU` / `_GLOBAL`). El adapter descifra la key al vuelo y no la escribe en disco en claro.

### ¿Cómo genero una clave Fernet para cifrar la API key?

```python
from cryptography.fernet import Fernet
print(Fernet.generate_key().decode())
```

Copia el valor en `MISTRAL_ENCRYPTION_KEY_ES` y cifra tu API key con ese mismo Fernet para guardarla en `ENCRYPTED_MISTRAL_API_KEY`.

### Error "Falta ENCRYPTED_MISTRAL_API_KEY o MISTRAL_API_KEY"

Comprueba que el archivo `.env` esté en el directorio desde el que ejecutas el script (por ejemplo la raíz del repo) y que una de las dos variables esté definida. Si usas `ENCRYPTED_MISTRAL_API_KEY`, debe existir también `MISTRAL_ENCRYPTION_KEY_<REGION>`.

---

## Errores locales y dependencias

### "ModuleNotFoundError: No module named 'pandas'"

El adapter necesita `pandas` para `load_dataset` (CSV, JSON, Parquet). Instala con:

```bash
pip install pandas pyarrow
```

### "ModuleNotFoundError: No module named 'cryptography'"

Solo es necesario si usas API key cifrada. Instala con:

```bash
pip install cryptography
```

### La API devuelve 401 o 403

Verifica que `MISTRAL_API_KEY` sea correcta y tenga permisos en tu cuenta Mistral. Si usas key cifrada, asegúrate de que `MISTRAL_ENCRYPTION_KEY_<REGION>` sea la misma con la que se cifró.

---

## Rate limiting y uso

### ¿Hay límite de solicitudes?

Sí. Por defecto el cliente aplica un rate limit de 60 solicitudes por minuto. Puedes cambiarlo al crear el cliente:

```python
client = MistralAPIClient(api_key=api_key, region="ES", rate_limit_per_minute=120)
```

### ¿Cómo registro las llamadas en GaiaChain?

Cada llamada a `query()` genera un hash (SHA-256) de la petición y la respuesta y se registra vía el logger. En producción, ese hash (o el payload completo) debe enviarse a tu backend de GaiaChain 2.0; el adapter deja el punto de integración listo en `_log_to_gaiachain`.

---

## Cumplimiento y regiones

### ¿Qué región elijo para España?

Usa `region="ES"`. Para normativa UE amplia (incl. PAC 2040), usa `region="EU"`.

### ¿El adapter anonimiza datos personales?

No. Solo comprueba columnas que parecen datos personales (email, DNI, teléfono) y registra un aviso si no están anonimizadas. La anonimización debe aplicarse en tu pipeline antes de cargar el dataset.

---

Ver también: [Roadmap](roadmap.md) para próximos pasos y GaiaChain 2.0.
