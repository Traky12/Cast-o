# Prontuario — matriz aceleradora TRL (orientativa) Castúo-System

**Versión:** 2026-03-22 · **Horizonte:** Q2-2026 → Q1-2027 (hipótesis de planificación).

**Límite:** este documento **no** fija presupuesto contractual, **no** promete TRL9 “bloqueado”, **no** sustituye MAPA/CNPD/AENOR ni ROI comercial auditado. Las cifras económicas son **órdenes de magnitud a validar** con compras, impuestos y contratos reales. **Prohibido** citar precios de hardware como verdad del git sin factura o catálogo vigente.

**Relación técnica:** [PLAN-EXCELENCIA-V2.5-REFUERZO.md](./PLAN-EXCELENCIA-V2.5-REFUERZO.md) · [PRONTUARIO-REFUERZO-SECRETS-VAULT-2026.md](./PRONTUARIO-REFUERZO-SECRETS-VAULT-2026.md) · [CHECKLIST-TRL6-HETZNER-STAGING.md](../deploy/CHECKLIST-TRL6-HETZNER-STAGING.md) · [PRONTUARIO-MAESTRO-EVOLUCION-SISTEMA-2026.md](../deploy/PRONTUARIO-MAESTRO-EVOLUCION-SISTEMA-2026.md) *(síntesis componentes, LLMNR/Multilinker, hoja 6 meses)* · [PRONTUARIO-AUDITORIA-TECNICA-ETICA-CASTUO-2026.md](../deploy/PRONTUARIO-AUDITORIA-TECNICA-ETICA-CASTUO-2026.md) *(auditoría técnica y ética)* · [PRONTUARIO-MAESTRO-AUDITORIA-EVOLUCION-RESILIENTE-2026.md](../deploy/PRONTUARIO-MAESTRO-AUDITORIA-EVOLUCION-RESILIENTE-2026.md) *(evidencia git + roadmap 3–6 m)* · [PRONTUARIO-MAESTRO-INFRAESTRUCTURA-SOBERANA-TRL6-TRL7-2026.md](../deploy/PRONTUARIO-MAESTRO-INFRAESTRUCTURA-SOBERANA-TRL6-TRL7-2026.md) *(infra UE TRL6→7)* · [DPIA-Robotics-DPO-SOLICITUD-FIRMA-PLANTILLA.md](./DPIA-Robotics-DPO-SOLICITUD-FIRMA-PLANTILLA.md) · [DPIA-Robotics-2026.md](./DPIA-Robotics-2026.md) §6 · [ROADMAP-INTEGRACIONES-SIGPAC-GAIACHAIN-AEMET.md](./ROADMAP-INTEGRACIONES-SIGPAC-GAIACHAIN-AEMET.md) · [ROADMAP-Scan3D-Print-2026.md](./ROADMAP-Scan3D-Print-2026.md) · [SISTEMA-COHERENCIA-ADMIN-GENERAL-2026.md](./SISTEMA-COHERENCIA-ADMIN-GENERAL-2026.md) · `docs/deploy/robotics-lab-hetzner.env.example` · `docker-compose.scan3d.yml`

---

## 1. Estado honesto del repositorio (línea base)

| Ámbito | TRL en clon | Evidencia |
|--------|-------------|-----------|
| Robotics lab HTTP | Simulación / stub | `lab_stub_app`, neuromórfico TRL-4 sim, scan3d sim |
| Cadena | Opt-in técnico | `lab_gaiachain_optional` + contrato desplegado |
| SIGPAC producción | No API MAPA en git | PEI-001 local, validación estructural |
| Certificaciones | Documentación generada / plantillas | `compliance_docs/generated/*` — **no** certificado AENOR en repo |

---

## 2. Matriz de fases (hipótesis — revisar trimestralmente)

| Fase | Objetivo TRL (campo) | Duración orientativa | Dependencias críticas | Entregables medibles |
|------|----------------------|----------------------|-------------------------|----------------------|
| **A — Piloto mínimo** | TRL6 *field trial* acotado | ~4–8 semanas | Firma DPO §6 DPIA robotics; hardware adquirido; edge desplegado | Informe piloto 1 parcela o lote acordado; KPIs agua/energía definidos con agrónomo |
| **B — Demo comercial** | TRL7 *demo* replicable | ~3 meses | Integración MAPA/FEGA si aplica; mainnet/HSM **solo** tras auditoría contrato | Contratos piloto por escrito; SLAs edge |
| **C — Escala calificada** | TRL8 *qualified* | ~3 meses | ISO 27001 **si** se persigue certificación; manual O&M | Auditoría interna + métricas 99.x% acordadas |
| **D — Operación sostenida** | TRL9 *production* (uso corriente) | ≥6 meses evidencia | Adopción usuario, soporte, retención datos RGPD | **Solo** tras cierre DPO + operación real documentada |

**TRL:** interpretación agro/IoT; no confundir con TRL de un único módulo de software en laboratorio.

---

## 3. Presupuesto — partidas (cotizar; no total fijo en git)

| Partida | Notas | Fase sugerida |
|---------|--------|---------------|
| Hardware escaneo / impresión FDM | Catálogo distribuidor; mantenimiento/resinas | A |
| Edge VPS (p. ej. Hetzner) | TLS, backups, coste recurrente | A–D |
| Auditoría smart contract | Presupuesto abogado/auditor blockchain | B |
| HSM / Vault enterprise | Si política de claves lo exige | B |
| MAPA / trazabilidad oficial | Según expediente y contrato | B |
| ISO 27001 / pre-auditoría | Si alcance certificable | C |
| Operación de campo | Personal técnico — coste local | A–D |

**Total “€150k / €500k ARR / ROI 3.3x”:** **no** figuran como datos del repositorio; van a **hoja financiera** externa aprobada por dirección.

---

## 4. KPIs piloto (ejemplo — a fijar con CTAEX / titular)

- **Agua / nutriente:** reducción orientativa vs línea base manual — medición **in situ**, no solo `riego_ml` del simulador neuromórfico.  
- **Prototipado:** tiempo diseño → pieza útil (scan3d real + slicer; el stub no mide esto).  
- **Cadena:** tasa de éxito de TX en red acordada (testnet/mainnet) con política de gas.  
- **Edge:** disponibilidad medida por monitorización (Prometheus/uptime externo).

---

## 5. Checklist 7 días (acciones inmediatas — sin órdenes de compra en git)

- [ ] **DPO:** revisión y decisión sobre [DPIA-Robotics-2026.md](./DPIA-Robotics-2026.md) §6 (`parcel_ref` off-chain por defecto).  
- [ ] **Compras:** RFQ hardware (escáner + impresora) con especificación técnica **sin** anclar marca en el markdown legal.  
- [ ] **Deploy:** preparar `.env` desde `docs/deploy/robotics-lab-hetzner.env.example` (**Opción A** `*_FILE` o **Opción B** `VAULT_ADDR`+`VAULT_TOKEN_FILE`; **no Opción C** en prod); matriz en [VAULT_KV_PATHS.md](../../backend/security/VAULT_KV_PATHS.md).  
- [ ] **Transporte:** `docker compose -f docker-compose.scan3d.yml` (o imagen lab 8011) en servidor; comprobar `/health` y `chain_status`.  
- [ ] **Datos piloto:** lista de parcelas **anonimizadas o código interno** (p. ej. EX-CTAEX-00x) sin geometría en tickets públicos.  
- [ ] **Baseline:** protocolo de medición manual vs asistido (firmado por técnico de campo).

---

## 6. Comandos de despliegue (referencia; rutas reales del clon)

```powershell
# En máquina de destino (ajustar host y rutas)
scp docker-compose.scan3d.yml user@servidor:/opt/castuo/
scp docs/deploy/robotics-lab-hetzner.env.example user@servidor:/opt/castuo/.env.hetzner
# Editar .env.hetzner en servidor; no subir secretos al git
```

```bash
# En servidor
docker compose -f docker-compose.scan3d.yml --env-file .env.hetzner up -d
```

Playbook admin (tras definir CASTUO_ADMIN_GENERAL_BEARER o *_FILE):

```powershell
curl.exe -sS -H "Authorization: Bearer $env:CASTUO_ADMIN_GENERAL_BEARER" http://127.0.0.1:8012/admin_general/playbook
```

(Puerto según mapeo `8012:80` del compose scan3d o `8011` si usas uvicorn local.)

---

## 7. Cierre

La **coherencia del sistema** en git = código + docs orientativas + tests. La **aceleración TRL** en campo = agua ahorrada, decisiones DPO y contratos fuera del markdown.

*Quien riega de verdad no necesita inflar el ROI en el prontuario.*
