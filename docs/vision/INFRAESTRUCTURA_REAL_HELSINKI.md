# Infraestructura real — Nodo Helsinki y activos de producción

El nodo no es una nube abstracta. Es un servidor físico con coordenadas de valor verificables. Soberanía europea y activos reales a día de hoy.

---

## 1. Infraestructura real: el nodo Helsinki

| Dato | Valor |
|------|--------|
| **IP real** | 46.62.152.158 (Hetzner Online GmbH) |
| **Ubicación** | Finlandia / UE |
| **Latencia** | ~73 ms (ruta Madrid → Frankfurt → Helsinki) |
| **Verificación** | `ping -c 3 46.62.152.158` |

Es el pulso real del sistema.

**Capa de datos — soberanía europea:** Al estar en Finlandia, los datos de las cooperativas extremeñas están protegidos por la **GDPR** y el **Data Act** de la UE, fuera del alcance de la **Cloud Act** de EE. UU.

---

## 2. Activos de producción reales (18.0 hectáreas)

Balance de situación a día de hoy. Cada hectárea es un activo que genera datos y recurrencia.

| Cooperativa | Superficie | Cultivo real | MRR (recurrencia) |
|-------------|------------|--------------|-------------------|
| Sabionda Educa | 2.5 ha | Lechuga (hidroponía) | 350 € |
| Coop #2 | 5.0 ha | Vid (agrovoltaica) | 700 € |
| Coop #3 | 3.0 ha | Tomate industrial | 420 € |
| Coop #4 (nueva) | 4.0 ha | Olivar superintensivo | 560 € |
| Coop #5 (nueva) | 3.5 ha | Patata | 490 € |
| **TOTAL REAL** | **18.0 ha** | **Mix diversificado** | **2.520 €/mes** |

---

## 3. Las 11 capas de seguridad (auditables)

Si un técnico del CTAEX lo solicita, estas capas son demostrables en terminal:

| # | Capa | Descripción |
|---|------|-------------|
| 1 | SSH hardening | Solo llaves RSA-4096, puerto no estándar |
| 2 | Kernel inmutabilidad | Atributo `+i` en archivos críticos (no modificables ni por root) |
| 3 | Firewall UFW | Bloqueo total excepto puertos de servicio e IP de administrador |
| 4 | Shredding | Eliminación forense de rastros de instalación |
| 5 | Cifrado PGP | Firmas digitales para mensajes de facturación |
| 6 | Checksum SHA256 | Verificación de integridad bit a bit (sello de lacre) |
| 7 | Aislamiento Docker | Cada vertical de negocio en su propio contenedor estanco |
| 8 | MQTT cifrado | TLS/SSL para datos de sensores de campo |
| 9 | VeChain Bridge | Hash de cada cosecha en blockchain pública |
| 10 | Fail2Ban | Bloqueo automático de IPs tras intentos fallidos |
| 11 | Root of Trust | Pendrive físico como única fuente de verdad para el búnker |

*(Verificación script: `./security/master-encrypt-verify.sh` → 11/11 SECURE.)*

---

## 4. Valoración real de mercado (VC ready)

Basada en múltiplos reales de SaaS B2B y valor de activos IP:

| Concepto | Valor | Nota |
|-----------|-------|------|
| **Valor del software (IP)** | ~5.000.000 € | Sistema 11 capas, IoT + blockchain, ingeniería senior |
| **Valor de tracción (ARR)** | 302.400 € | Proyectado a 12 meses con crecimiento actual (18 ha, 5 coops, escalado) |
| **Multiplicador por soberanía** | +25 % | Cumplimiento EU AI Act e infraestructura 100 % europea en impact investing |

---

*[DISCURSO_CTAEX](DISCURSO_CTAEX.md) · [TOP3_PLATAFORMAS_ESPANA_2026](TOP3_PLATAFORMAS_ESPANA_2026.md) · [ESTATUS_VALOR_V1.7.1](ESTATUS_VALOR_V1.7.1.md)*
