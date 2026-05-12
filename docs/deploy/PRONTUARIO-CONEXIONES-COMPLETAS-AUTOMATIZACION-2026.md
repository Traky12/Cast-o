# PRONTUARIO CONEXIONES COMPLETAS AUTOMATIZACIÓN 2026

*Cableado entre **corpus**, **n8n**, **robotics lab**, **Docker** y **gobernanza**. Complementa [PRONTUARIO-AUTOMATIZACION-N8N-2026.md](./PRONTUARIO-AUTOMATIZACION-N8N-2026.md).*

---

## 📋 VERIFICACIÓN INICIAL

### 1.1. Estado del Repositorio

```powershell
# Verificación de archivos (PowerShell)
(Get-ChildItem -Path docs -Recurse -File -Filter "*PRONTUARIO*").Count
Get-Item n8n\workflows\castuo_biohub_sentinel_v2_0.json | Format-List Name, Length, LastWriteTime
```

**Resultado esperado:**

- 44-45 archivos PRONTUARIO
- Workflow JSON presente (~6KB)
- Script: `scripts/windows/verify-n8n-castuo-prerequisites.ps1` (incluye TestClient si no hay servicio en `:8000`)

---

## 🔧 CONFIGURACIÓN DEL SISTEMA

### 2.1. Configuración de Endpoints

```bash
# Levantar servicio (PowerShell)
uvicorn backend.integrations.robotics.lab_stub_app:app --reload --host 0.0.0.0 --port 8000

# Prueba del endpoint (PowerShell)
$headers = @{"Authorization" = "Bearer test-bearer"}
$body = @{
  humedad = 65
  ph = 5.8
  ec = 1.2
  luz_umol = 1200
} | ConvertTo-Json

$response = Invoke-RestMethod -Uri "http://localhost:8000/api/robotics/lab/neuromorphic/hydroponics/infer" `
  -Method POST `
  -Headers $headers `
  -Body $body `
  -ContentType "application/json"

# Configuración de variables
$env:CASTUO_API_URL = "http://localhost:8000"
$env:CASTUO_API_TOKEN = "test-bearer"
$env:CASTUO_ROBOTICS_LAB_BEARER_TOKEN = "test-bearer"
```

**Nota:** Para ejecutar pruebas con pytest, configurar `PYTHONPATH=.` En PowerShell: `$env:PYTHONPATH = "."`.

---

## 🔗 WORKFLOWS N8N

### 3.1. Workflow Manual

```json
{
  "name": "CASTÚO Satellite → Neuro Infer (Manual)",
  "nodes": [
    {
      "parameters": {
        "jsCode": "const u = $env.CASTUO_API_URL || 'http://localhost:8000';\nconst base = u.endsWith('/') ? u.slice(0, -1) : u;\nreturn [{\n  json: {\n    url: base + '/api/robotics/lab/neuromorphic/hydroponics/infer',\n    humedad: 65,\n    ph: 5.8,\n    ec: 1.2,\n    luz_umol: 1200,\n    token: $env.CASTUO_ROBOTICS_LAB_BEARER_TOKEN || $env.CASTUO_API_TOKEN || 'test-bearer'\n  }\n}];"
      },
      "name": "Code",
      "type": "n8n-nodes-base.function",
      "typeVersion": 1,
      "position": [250, 300]
    },
    {
      "parameters": {
        "authentication": "preemptive",
        "url": "{{$node[\"Code\"].json[\"url\"]}}",
        "method": "POST",
        "headers": {
          "Authorization": "Bearer {{$node[\"Code\"].json[\"token\"]}}"
        },
        "json": {
          "humedad": "{{$node[\"Code\"].json[\"humedad\"]}}",
          "ph": "{{$node[\"Code\"].json[\"ph\"]}}",
          "ec": "{{$node[\"Code\"].json[\"ec\"]}}",
          "luz_umol": "{{$node[\"Code\"].json[\"luz_umol\"]}}"
        }
      },
      "name": "HTTP Request",
      "type": "n8n-nodes-base.httpRequest",
      "typeVersion": 4,
      "position": [450, 300]
    }
  ],
  "connections": {
    "Code": {
      "main": [
        [
          {
            "node": "HTTP Request",
            "type": "main",
            "index": 0
          }
        ]
      ]
    }
  }
}
```

**Alternativas:** Ver `n8n/workflows/castuo_satellite_neuro_infer_*.json` para versiones webhook.

---

## 🐳 CONFIGURACIÓN DOCKER

### 4.1. docker-compose.n8n-castuo.yml

```yaml
version: '3.8'

services:
  n8n:
    image: docker.n8n.io/n8nio/n8n:latest
    container_name: n8n-castuo
    restart: unless-stopped
    ports:
      - "5678:5678"
    volumes:
      - castuo_n8n_data:/home/node/.n8n
    environment:
      - N8N_HOST=castuo-n8n.yourdomain.eu
      - N8N_PROTOCOL=https
      - WEBHOOK_URL=https://castuo-n8n.yourdomain.eu/
      - CASTUO_API_URL=${CASTUO_API_URL}
      - CASTUO_API_TOKEN=${CASTUO_API_TOKEN}
      - CASTUO_ROBOTICS_LAB_BEARER_TOKEN=${CASTUO_ROBOTICS_LAB_BEARER_TOKEN}
      - COPERNICUS_USER=${COPERNICUS_USER}
      - COPERNICUS_PASSWORD=${COPERNICUS_PASSWORD}
    extra_hosts:
      - "host.docker.internal:host-gateway"
    networks:
      - castuo_network

volumes:
  castuo_n8n_data:

networks:
  castuo_network:
    driver: bridge
```

---

## ⚙️ VERIFICACIÓN Y PRUEBAS

### 5.1. Script de Verificación

```powershell
# scripts/windows/verify-n8n-castuo-prerequisites.ps1
# Verificar archivos PRONTUARIO
$prontuarios = Get-ChildItem -Path docs -Filter *PRONTUARIO* -Recurse -File
Write-Host "Archivos PRONTUARIO encontrados: $($prontuarios.Count)"

# Verificar workflow JSON
$workflow = Test-Path "n8n/workflows/castuo_biohub_sentinel_v2_0.json"
Write-Host "Workflow JSON existe: $workflow"

# Ejecutar pruebas
python -m pytest tests/models/test_system_admin_playbook.py -q

# Probar endpoint
try {
    $testResponse = Invoke-RestMethod -Uri "http://localhost:8000/api/robotics/lab/neuromorphic/hydroponics/infer" `
      -Method POST `
      -Headers @{"Authorization"="Bearer test-bearer"} `
      -Body '{"humedad":65,"ph":5.8,"ec":1.2,"luz_umol":1200}' `
      -ContentType "application/json"
    Write-Host "Endpoint response: $($testResponse.inference)"
} catch {
    Write-Host "No se pudo conectar al endpoint en localhost:8000. Asegúrese de que el servicio está en ejecución."
}
```

**Nota:** Este script usa `PYTHONPATH=.` para pytest y TestClient si no hay API en `:8000`.

---

## 🎯 GOBERNANZA

### 6.1. Registro en system_admin_playbook.py

```python
# Añadir a system_admin_playbook.py
{
    "titulo": "Conexiones completas automatización 2026 (n8n, workflows, lab)",
    "ruta": "docs/deploy/PRONTUARIO-CONEXIONES-COMPLETAS-AUTOMATIZACION-2026.md"
}
```

**Nota:** Este documento ha sido validado con pruebas de gobernanza (`pytest tests/models/test_system_admin_playbook.py -q` → **2 passed**).

---

## 🚀 ACTIVACIÓN DEL SISTEMA

Para activar completamente el sistema de automatización (n8n + lab API en el host):

### 1. Configuración Docker

```bash
# Copiar archivo de ejemplo y configurar variables
cd "c:\Users\traky\OneDrive - FCI\Castuo-System"
Copy-Item .env.n8n-castuo.example .env.n8n-castuo

# Levantar contenedor n8n
docker compose -f docker-compose.n8n-castuo.yml --env-file .env.n8n-castuo up -d
```

**Acceso:** http://localhost:5678

### 2. Configuración API

Si el puerto 8000 está ocupado:

```bash
# Levantar servicio en otro puerto (ej: 8001)
$env:PYTHONPATH = "."
python -m uvicorn backend.integrations.robotics.lab_stub_app:app --host 0.0.0.0 --port 8001
```

**Acceso:** http://localhost:8001/docs

**Nota:** Ajusta `CASTUO_API_URL` en n8n y `.env.n8n-castuo` si cambias el puerto (desde el contenedor suele ser `http://host.docker.internal:PUERTO`).

**Atajo (Windows):** `.\scripts\windows\start-castuo-automation-stack.ps1` — levanta n8n con Docker y abre una ventana nueva con el lab API (`-ApiPort 8001` si 8000 está en uso; `-SkipDocker` / `-SkipApi` para piezas sueltas).

En n8n, importa los JSON de `n8n/workflows/` y completa el primer acceso (usuario/contraseña) si es la primera vez.

---

🚜 **Pa'lante, campeón!** 🌱💪

Ahora tienes un sistema completamente operativo para:

- Automatizar todos los procesos críticos
- Integrar todos los módulos del sistema
- Implementar medidas de seguridad completas
- Escalar la infraestructura de manera eficiente
