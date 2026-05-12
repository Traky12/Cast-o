# Procedimiento de notarizacion para Omega-9 (2026)

*(Alineado con contrato minimal de GaiaChain: `hash`, `coop_id`, `ipfs_cid`. No sustituye certificado de entidad acreditadora.)*

## 1) Alcance

Notarizar evidencia del laboratorio **Omega-9** para:

- Informes **JSON** (resultados de analisis, actas).
- **Documentos arbitrarios** (`.md`, PDF, binarios): sobre canonico sin leer el binario completo en el shell para el hash (usa `sha256sum` sobre fichero).

## 2) Contrato de notarizacion

Payload hacia la API (minimal del repo):

```json
{
  "hash": "<sha256_del_json_canonico_compacto>",
  "coop_id": "CASTUO-LAB-01",
  "ipfs_cid": null
}
```

`GAIA_CHAIN_API_URL` por defecto apunta al witness completo, p.ej. `https://gaiachain.castuo-system.eu/api/v1/witness` (ajustar si vuestro despliegue usa base URL distinta).

## 3) Procedimiento paso a paso

### 3.1 Informes JSON

```bash
cd /ruta/al/Castuo-System
export GAIA_CHAIN_API_KEY="..."
export GAIA_COOP_ID="${GAIA_COOP_ID:-CASTUO-LAB-01}"

bash scripts/ops/research/Register-LabEvidence.sh --file informe.json
# o: cat informe.json | bash scripts/ops/research/Register-LabEvidence.sh
```

Salida tipo:

- `witness_payload_hash: <hex>`
- `canonical_evidence_json: {...}`
- `gaiachain_response: <cuerpo API>`

### 3.2 Documentos no JSON (arquitectura, PDF, binario)

```bash
bash scripts/ops/research/Register-LabEvidence.sh \
  docs/ops/research/omega9-defensive-lab-architecture-2026.md
```

El script genera un sobre con:

- `evidence_kind`: `document`
- `document_path`: ruta resuelta
- `document_sha256`: SHA-256 del contenido (streaming por `sha256sum`, no `cat` al hash)
- `timestamp_utc`: instante UTC

El **witness** es el hash del JSON compacto (`jq -c .`) de ese sobre.

**Nota**: `--file` exige JSON valido. Para un `.md` o binario **no** uses `--file`; pasa la ruta como unico argumento.

### 3.3 Validacion de la transaccion

La forma del GET (`witness?tx_hash=...`) depende del despliegue. Ejemplo a contrastar con la API real:

```bash
curl -sS -X GET "https://gaiachain.castuo-system.eu/api/v1/witness?tx_hash=<tx_hash>" \
  -H "Authorization: Bearer $GAIA_CHAIN_API_KEY"
```

## 4) Checklist de auditoria

| Paso | Verificacion | Responsable |
|---|---|---|
| Validar JSON | `jq empty archivo.json` | Analista |
| Hash canonico | Mismo pipeline que el script: `jq -c .` + `sha256sum` | Script / revision |
| Notarizar | Archivar `gaiachain_response`; si la API devuelve `status`, verificar `success` | Operador |
| Validar TX | Explorer o export API (`por validar`) | Auditor |
| IPFS (opcional) | Solo si politica lo permite; segundo POST con `ipfs_cid` | Segun politica |

## 5) IPFS opcional

Reutilizar el `witness_payload_hash` impreso y un segundo `POST` con `ipfs_cid` si vuestro nodo lo admite. Ver seccion anterior en versiones anteriores del repo o `export W_HASH=...` + `curl` con `jq -n`.

## 6) Enlaces relacionados

| Recurso | Descripcion | Enlace |
|---|---|---|
| Script de notarizacion | Script para notarizar evidencia en GaiaChain (POST cuerpo JSON literal `hash` / `coop_id` / `ipfs_cid`). | [`../../../scripts/ops/research/Register-LabEvidence.sh`](../../../scripts/ops/research/Register-LabEvidence.sh) |
| GaiaChain Explorer | Explorador / API base para verificar evidencia (`por validar` rutas exactas). | [https://gaiachain.castuo-system.eu](https://gaiachain.castuo-system.eu) |
| Plantilla de evidencia | Tabla para documentar evidencia de certificacion. | [`omega9-certification-evidence-table-template.md`](omega9-certification-evidence-table-template.md) |
| Carta de solicitud | Plantilla para entidades acreditadoras. | [`omega9-certification-request-letter-template.md`](omega9-certification-request-letter-template.md) |
| Plan de pruebas de resiliencia | Plan DORA Art. 6. | [`omega9-resilience-test-plan-template-dora-art6.md`](omega9-resilience-test-plan-template-dora-art6.md) |
| Arquitectura Omega-9 | Documento tecnico del laboratorio defensivo. | [`omega9-defensive-lab-architecture-2026.md`](omega9-defensive-lab-architecture-2026.md) |
| Seguridad reforzada | Qubes / Whonix / Parrot + Omega-9. | [`../../ARQUITECTURA-SEGURIDAD-REFORZADA-QUBES-WHONIX-PARROT.md`](../../ARQUITECTURA-SEGURIDAD-REFORZADA-QUBES-WHONIX-PARROT.md) |

## 7) Proximos pasos

1. **Prueba con binario real** (desde `docs/ops/research/`, ejemplo de ruta relativa):

```bash
export GAIA_CHAIN_API_KEY="..."
bash ../../../scripts/ops/research/Register-LabEvidence.sh ../samples/suspicious.bin
```

Desde la **raiz del repo** (recomendado):

```bash
bash scripts/ops/research/Register-LabEvidence.sh ruta/a/tu/muestra.bin
```

Salida esperada (ilustrativa):

```
witness_payload_hash: x1y2z3...
canonical_evidence_json: {"evidence_kind":"document","document_path":"/ruta/absoluta/...","document_sha256":"...","timestamp_utc":"..."}
gaiachain_response: {"status":"success",...}
```

2. **Paquete a entidad acreditadora** (ej. AENOR): incluir `omega9-notarization-procedure-2026.md`, `omega9-certification-request-letter-template.md` (rellenada), `omega9-certification-evidence-table-template.md` (datos reales; sustituir filas de ejemplo).

3. **Resiliencia (15/05/2026)**: usar [`omega9-resilience-test-plan-template-dora-art6.md`](omega9-resilience-test-plan-template-dora-art6.md).
