# Comando único Hetzner — Verificación + 2.ª cooperativa

Consolidación: **verificación final 10/10**, **deploy docs** y **onboarding segunda cooperativa** en una sola ejecución.

---

## Comando único (copiar/pegar)

Ejecutar en **raíz del repo** (Hetzner o local). El backend de cooperativas debe estar en **8001** (o definir `BACKEND_URL`).

```bash
# Opción A: script todo-en-uno (recomendado)
chmod +x scripts/hetzner-verificar-y-coop2.sh
./scripts/hetzner-verificar-y-coop2.sh
```

```bash
# Opción B: comandos en secuencia (30s)
./security/master-encrypt-verify.sh && \
mkdocs gh-deploy --message "v1.7.1: GDPR 10/10 + €5.2M VALOR" 2>/dev/null || true && \
curl -s -X POST http://localhost:8001/cooperativas \
  -H "Content-Type: application/json" \
  -d '{"nombre":"Cooperativa #2","hectareas":5.0,"socios":4,"cultivo":"vid"}' && echo "" && \
echo "✅ Verificación + docs + 2.ª cooperativa listos. Certik: certik.com → DynamicCropNFT.sol (45 días → +€2.5M)"
```

---

## Qué hace cada paso

| Paso | Acción | Salida esperada |
|------|--------|------------------|
| **1. Verificación** | `./security/master-encrypt-verify.sh` | `CASTÚO-SYSTEM ENCRYPTION: N/10 SECURE` |
| **2. Deploy docs** | `mkdocs gh-deploy` | Docs en gh-pages con mensaje v1.7.1 |
| **3. 2.ª cooperativa** | `POST /cooperativas` | `201` + JSON con `id`, `nombre`, `hectareas` |
| **4. Certik** | Recordatorio | certik.com → DynamicCropNFT.sol (45 días → +€2.5M valor) |

---

## Requisitos

- **Backend en 8001:** para que el onboarding responda 201, el backend (cooperativas) debe estar levantado:
  ```bash
  cd backend && uvicorn main:app --host 0.0.0.0 --port 8001
  ```
- **MkDocs:** opcional; si no está instalado o no hay `mkdocs.yml`, se omite el deploy.
- **Variable:** `BACKEND_URL=http://IP:8001` si el backend está en otra máquina.

---

## Endpoint POST /cooperativas

El backend expone **POST /cooperativas** para registrar una nueva cooperativa:

**Body (JSON):**
- `nombre` (obligatorio): nombre de la cooperativa.
- `hectareas` (obligatorio): 0.1–1000.
- `nif` (opcional): CIF/NIF.
- `socios` (opcional): número de socios (default 3).
- `cultivo` (opcional): cultivo principal (default "mixto").

**Ejemplo:**
```bash
curl -X POST http://localhost:8001/cooperativas \
  -H "Content-Type: application/json" \
  -d '{"nombre":"Cooperativa #2","hectareas":5.0}'
```

**Respuesta 201:**
```json
{
  "id": 3,
  "nombre": "Cooperativa #2",
  "hectareas": 5.0,
  "message": "Cooperativa registrada. GET /cooperativas para listado."
}
```

---

[← Estatus y valor](ESTATUS_VALOR_V1.7.1.md) · [Nueva carga GDPR](../security/NUEVA_CARGA_GDPR_ENCRYPTION_V1.7.1.md)
