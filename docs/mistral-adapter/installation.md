# Instalación

## Cómo instalar el adapter en pocos minutos

Sigue estos pasos para tener el adapter operativo en tu entorno.

### 1. Clonar el repositorio

```bash
git clone https://github.com/CASTUO-SYSTEM/Castuo-System.git
cd Castuo-System
```

*(Si el adapter se publica en un repo propio: `git clone https://github.com/CASTUO-SYSTEM/mistral-adapter.git`.)*

### 2. Instalar dependencias

```bash
pip install -r requirements.txt
```

O solo las necesarias para el adapter:

```bash
pip install requests pandas pyarrow cryptography
```

### 3. Configurar variables de entorno

Crear o editar `.env` en la raíz del proyecto:

```bash
# API Key de Mistral (desarrollo: en claro)
echo "MISTRAL_API_KEY=tu_api_key_aqui" >> .env

# Producción: clave para cifrar/descifrar la API key (Fernet)
echo "MISTRAL_ENCRYPTION_KEY_ES=tu_clave_fernet_base64" >> .env
# Opcional: key cifrada
# echo "ENCRYPTED_MISTRAL_API_KEY=..." >> .env
```

### 4. Ejecutar el ejemplo

Desde la raíz del repo:

```bash
python api/mistral_castuo_adapter.py
```

O desde código:

```python
from api.mistral_castuo_adapter import ejemplo_completo
ejemplo_completo()
```

### 5. Documentación (MkDocs)

Desde la **raíz del repo**:

```bash
# Test local
pip install -r requirements-docs.txt
mkdocs serve

# Producción (1 línea)
mkdocs gh-deploy --clean --message "Deploy v1.0.0 docs $(git rev-parse --short HEAD)"
```

Ver [README de la doc](README.md) para verificación de despliegue, DNS por proveedor y dominio `docs.castuo-system.com`.

---

### 6. Docker (producción)

Construir y ejecutar la API con Mistral Adapter incluido (desde la **raíz del repo**):

```bash
docker build -t castuo/mistral-api -f api/Dockerfile .
docker run -p 8000:8000 -e MISTRAL_API_KEY=tu_key castuo/mistral-api
```

Variables de entorno recomendadas en producción: `MISTRAL_API_KEY` o `ENCRYPTED_MISTRAL_API_KEY` + `MISTRAL_ENCRYPTION_KEY_ES`, y opcionalmente `MISTRAL_REGION` (ES, EU, GLOBAL).

---

### 7. API Endpoints (FastAPI)

Con la API en marcha (`uvicorn api.main:app` o el contenedor anterior):

**Health del adapter:**

```bash
curl http://localhost:8000/mistral/health
```

**Consulta con contexto de dataset (Sabionda):**

```bash
curl -X POST http://localhost:8000/mistral/query \
  -H "Content-Type: application/json" \
  -d '{"dataset_path": "data/sabionda.parquet", "query": "análisis rendimiento", "temperature": 0.7, "max_tokens": 2000}'
```

**Solo pregunta (sin dataset):**

```bash
curl -X POST http://localhost:8000/mistral/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Sugiere 3 estrategias de riego para agrovoltaica"}'
```
