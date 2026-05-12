# CASTUO-SYSTEM™ — Arquitectura integrada: CRM + ERP + LEGAL (Odoo + Nextcloud + GS1 EPCIS + BioCoin)

Objetivo: centralizar **clientes, granjas, licencias, facturas, trazabilidad** y **cumplimiento** en un único sistema operativo.

---

## 1. Arquitectura técnica (alto nivel)

```mermaid
graph TD
    A[Frontend: Nextcloud + React] -->|API| B[Backend: Odoo ERP/CRM]
    B -->|PostgreSQL| C[(DB Odoo)]
    B -->|REST| D[SII / Facturae]
    B -->|EPCIS| E[GS1 EPCIS (OpenEPCIS)]
    B -->|Smart Contracts| F[BioCoin Castúo (Ethereum/Polygon)]
    B -->|Webhooks| G[Notificaciones (Slack/Email/Telegram)]
    C -->|Backup| H[S3 cifrado con Age]
    E -->|Hash| I[IPFS + Filecoin]
```

---

## 2. Despliegue en Hetzner (Docker Compose)

Este repo incluye el compose **`docker-compose.odoo-erp-legal.yml`** con:

- **Odoo 17** (`:8069`) + **PostgreSQL**
- **Nextcloud** (`:8081`) + **MariaDB** + **Redis**
- **OpenEPCIS** (`:8082`) + **PostgreSQL** (usa `init/01-schema.sql`)

### Comandos

```bash
cd /castuo-system
cp .env.odoo.example .env.odoo
docker-compose -f docker-compose.odoo-erp-legal.yml --env-file .env.odoo up -d
```

Accesos:

- Odoo: `http://<IP>:8069`
- Nextcloud: `http://<IP>:8081`
- OpenEPCIS: `http://<IP>:8082`

---

## 3. Módulo Odoo “castu_system” (custom-addons)

Se añadió un esqueleto de módulo en:

`custom-addons/castu_system/`

Incluye:

- **Granjas** (`castu.granja`)
- **Licencias autoconsumo** (`castu.licencia`)
- **Eventos EPCIS** (`castu.epcis.event`)
- Extensión de factura (`account.move`) con `biocoin_tx` y `git_commit` (stub)

> Para activarlo: en Odoo → Apps → Update Apps List → buscar **CASTUO System** → Install.

---

## 4. Facturación España (SII / Facturae)

Ver:

- **`docs/LEGAL-SPAIN.md`** (BOE + SII Facturae)
- Plantilla: `templates/legal/facturae.xml`
- Script de ejemplo: `scripts/legal/enviar_facturae.py`

---

## 5. Trazabilidad UE (GS1 EPCIS + AI Act)

Ver:

- **`docs/LEGAL-EUROPE.md`** (GS1 EPCIS + AI Act)
- Evento ejemplo: `templates/legal/epcis_event.json`
- Script EPCIS: `scripts/legal/epcis_event.py`

---

## 6. BioCoin Castúo (smart contracts)

Contrato ejemplo con trazabilidad Git:

- `blockchain/contracts/BioCoinCastuo.sol`
- Hardhat: `blockchain/` (deploy + mint)

---

## 7. Operación y seguridad

- **Backups cifrados**: Age + S3 (ver `docs/COMPLIANCE-LEGAL.md`)
- **Alertas**: Slack/Email vía Alertmanager (`monitor/alertmanager.yml`)
- **Trazabilidad en Git**: hook TX obligatorio (ver `docs/CASTUO_GIT_BIOCOIN.md`)

