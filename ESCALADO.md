# CASTUO-SYSTEM — Estrategias de escalado post-producción

Objetivo: escalar tracción, ARR y valoración hasta un exit estratégico en horizonte 2028, apoyado en múltiplo SaaS, valor IP (algoritmo LER patentado), funding y demostración de tracción.

---

## Justificación post-deploy (valor técnico)

- **Production LIVE**: paso de “funciona en local” a “accesible 24/7” → incremento de valor y confianza.
- **HTTPS + Nginx enterprise**: DevOps profesional → mejora de valoración técnica.
- **CTAEX-ready demo**: probabilidad de funding y contratos muy alta.
- **Múltiples endpoints + Landing v5.0 públicos**: tracción demostrable y escalable.

La valoración objetivo se construye con: **VALOR = (ARR × múltiplo) + (IP × factor) + (Funding × factor) + (Tracción × factor)**. Las cifras concretas se gestionan en planificación interna; aquí solo se describen fases y palancas.

---

## Fases de escalado

### Fase 1: Piloto (primeros meses)

- **Objetivo**: 1 cliente piloto (ej. 10 ha) y validación comercial.
- **Acciones**:
  - Finca piloto (ej. Extremadura): sorgo + paneles.
  - Contrato recurrente por hectárea/mes.
  - KPIs: LER, eficiencia, rendimiento (t/ha).
  - Case study público como lead magnet.
- **Infra**: CAX21 → CAX31 (más RAM).
- **Resultado**: Validación y primer ARR; subida de valoración.

### Fase 2: SaaS regional

- **Objetivo**: Decenas de parcelas en región (Extremadura/Andalucía).
- **Pricing**: planes Basic (dashboard + sensores), Pro (IA + blockchain/QR), Enterprise (drones + optimización).
- **Marketing**:
  - Case study CTAEX + apoyo JEREMIE.
  - Webinars (ej. eficiencia agrovoltaica).
  - Demo farm tour → generación de leads/mes.
- **Infra**: CAX31 + Redis (cache/sesiones) + CDN si aplica.
- **Resultado**: ARR regional; valoración en rango SaaS.

### Fase 3: Nacional / UE

- **Objetivo**: Centenares de parcelas en España y Portugal.
- **Expansión**:
  - Certificación GS1 EPCIS y cumplimiento Reg 178/2002.
  - Integración ayudas PAC y subvenciones.
  - API Marketplace para integradores IoT.
- **Equipo**: Ventas, Soporte, DevOps (FTE).
- **Infra**: Kubernetes (EKS o equivalente) y multi-región si aplica.
- **Resultado**: ARR nacional/UE; valoración alineada con múltiplo SaaS y preparación para exit.

---

## Infra escalable (Hetzner → cloud)

| Escala   | Infra aproximada | Capacidad orientativa |
|----------|------------------|------------------------|
| Piloto   | CAX31 16 GB      | Decenas de parcelas   |
| Regional | CAX41 32 GB      | Centenares            |
| Nacional | K8s / EKS        | Miles                 |
| Multi    | Multi-región     | Escala mayor          |

---

## Automatización del escalado

1. **Terraform**: módulos para auto-scaling y entornos (piloto, prod).
2. **CI/CD (GitHub Actions)**: blue-green o canary para despliegues sin caídas.
3. **Onboarding cliente**: registro self-service, facturación (ej. Stripe), aprovisionamiento de parcelas y dashboard (con opción white-label).
4. **Monitorización**: Prometheus + Grafana (o Grafana Cloud); alertas Slack/Email automáticas.

---

## Canales de adquisición prioritarios

1. Ecosistema CTAEX (porcentaje alto de primeros clientes).
2. Google Ads (ej. “agrovoltaica IA”).
3. LinkedIn Sales.
4. Referrals.

**Embudo**: Leads → Demo → Trial → Pago. Objetivo: CAC bajo y LTV alto (retención 2 años).

---

## Checklist escalado (primeros 90 días)

- [ ] CTAEX / JEREMIE cerrado y desplegado.
- [ ] Contrato piloto Finca (primer ARR).
- [ ] Terraform CAX31 + Redis (o equivalente).
- [ ] Self-service signup + Stripe (o pasarela).
- [ ] Primeros clientes de pago (MRR inicial).
- [ ] Case study + webinars (leads/mes).
- [ ] Decenas de clientes → ARR regional → valoración en rango objetivo.

---

## Comandos útiles (escalado)

```bash
# Monitoring (Grafana Agent / Helm, cuando se use)
helm repo add grafana https://grafana.github.io/helm-charts
helm install castuo-monitoring grafana/grafana-agent

# Infra as code (cuando exista)
terraform -chdir=infra/terraform init
terraform -chdir=infra/terraform apply -auto-approve

# Deploy multi-entorno (cuando exista playbook)
ansible-playbook -i inventory/prod.yml deploy.yml
```

---

Este documento describe **estrategia y fases**; las cifras concretas de ARR, valoración y exit se mantienen en la planificación interna y no se referencian en el código ni en scripts de despliegue.
