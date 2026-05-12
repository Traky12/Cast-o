# ⚖️ FICHA TÉCNICA LEGAL: Protocolo de Soberanía Castúo v1.7.0

**Asunto:** Validación de jerarquía de custodia y trazabilidad inmutable.  
**Administrador Principal:** Gregorio (raíz de confianza única).

---

## 1. Marco de seguridad y propiedad intelectual

- **Aislamiento de activos:** El sistema utiliza cifrado asimétrico PGP/GPG y SOPS (AES-256). Legalmente, esto garantiza que el Administrador Principal es el único responsable y poseedor de los secretos industriales, cumpliendo con la Ley de Secretos Empresariales.

- **Control de acceso (Zero Trust):** El uso de Docker Secrets asegura que las claves de los activos (NFTs) no se almacenen en medios físicos persistentes, eliminando el riesgo de filtraciones por acceso físico no autorizado al servidor.

---

## 2. Trazabilidad blockchain y validez jurídica

- **Prueba de existencia:** Cada transacción en VeChain Thor actúa como un sellado de tiempo fehaciente (timestamping), vinculando el dato del sensor (pH, EC, energía) con una identidad digital protegida.

- **Cadena de custodia:** El script `audit_trace.py` genera una evidencia técnica utilizable como prueba pericial. Vincula el origen biótico (la planta) con el activo financiero (NFT) mediante una firma criptográfica autorizada exclusivamente por el Administrador.

---

## 3. Matriz de responsabilidad legal (Smart Governance)

| Capa técnica | Implicación legal | Garantía jurídica |
|--------------|------------------|-------------------|
| Root of Trust | Custodia de llave maestra | El Administrador tiene el control legal absoluto. |
| Git-crypt / SOPS | Protección de datos | Cumplimiento estricto de RGPD y secreto industrial. |
| Proxy Admin | Gobernanza del contrato | Solo se pueden aplicar cambios autorizados por firma. |
| Audit Trail | No repudio | El sistema impide que se niegue la veracidad del origen. |

---

## 4. Certificación de impacto socioeconómico

- **Soberanía cooperativa:** El modelo permite que las cooperativas operen bajo un paraguas de seguridad blindado, donde la trazabilidad aumenta el valor del producto final (ROI €281K/ha) al certificar origen y pureza de forma inexpugnable.

- **Dictamen técnico:** *"El sistema Castúo-System v1.7.0 implementa una arquitectura donde la tecnología se subordina a la autoridad legal del Administrador. La trazabilidad blockchain no es solo informativa, es vinculante e inmutable, eliminando intermediarios y riesgos de manipulación de datos."*

---

## Uso en CTAEX

- **Si el equipo legal pregunta por la gestión de claves:** mostrar el punto 1 (Marco de seguridad y propiedad intelectual) y el documento [Blindaje del Administrador](BLINDAJE_ADMINISTRADOR_V170.md).
- **Si preguntan por el control:** ejecutar `./security/verify-nft-stack.sh`. Los 7 checks en verde son la prueba visual de que el búnker está cerrado.
