# Estrategia de Precios — Modelo Tiered

**Referencia**: Banco de España / auditoría externa (Deloitte).  
**Objetivo**: ROI > 20 % en 3 años. Validar con clientes piloto.

---

## Niveles (ejemplo)

| Nivel | Precio/mes | Incluye | Destinatarios |
|-------|------------|---------|---------------|
| **Basic** | €500 | Trazabilidad básica, 1 usuario, 100 lotes/mes | Pequeños productores |
| **Pro** | €1.000 | Certificaciones AEMPS/GlobalGAP, 5 usuarios, 500 lotes/mes, soporte | Cooperativas, CTAEX-type |
| **Enterprise** | €2.000 | Ilimitado, API, integración ERP, SLA 99,9 %, soporte prioritario | Grandes operadores, distribuidores |

---

## Costes operativos

- **Objetivo**: Reducir costes de certificación en un **30 %** (automatización RPA, ej. UiPath).
- **Negociación**: Descuentos con AEMPS/GlobalGAP cuando aplique.
- **Informe de costes**: Actualización trimestral (coste por certificación, por lote).

---

## Subvenciones

- **JEREMIE 605K€**, Next Generation EU.
- **Gestor de subvenciones** (ej. Grupo Cajamar): presentar proyectos en junio 2026.
- **Plan de subvenciones**: Documentar convocatorias y plazos.

---

## Escalabilidad

- **Soporte 1.000 usuarios concurrentes**: Migración a Kubernetes (Hetzner Cloud).
- **Pruebas de carga**: Locust (ya referenciado en proyecto).
- **Plan de escalabilidad**: Ver `docs/operations/KPI-Implementation-Timeline.md` y roadmap.
