# Blindaje CASTUO360 — ejecución en Ecosystem 6.X

La **cápsula del tiempo** digital (hash + expediente) hace que la ingeniería inversa sea **legalmente irrelevante**: la prueba de prioridad está on-chain.

## 1. Ancla de prioridad (GaiaChain)

- **Función:** notario digital → **fecha cierta** global.
- **Efecto:** en litigio de patentes, el registro en blockchain CASTUO prima sobre registro en papel (manipulable).
- **Timestamping:** certificado de existencia **cuántico-resistente**; no alterable por computación avanzada.

*Herramienta:* `scripts/hash_expediente_zip.py` → SHA-256 del ZIP → anclar en red.

## 2. Ciclo de vida PI por componente

| Componente | Acción técnica | Objetivo legal |
|------------|----------------|----------------|
| **Hardware (anillo)** | Planos CAD + escaneado 3D en ZIP | Modelo de utilidad |
| **Firmware (IA airbag)** | Código + logs de entrenamiento | Patente de invención (método predictivo) |
| **SimRing** | Binarios + GUI | Copyright |
| **V2X** | Handshake propietario | Secreto industrial |

## 3. Smart-NDA (firewall legal)

- Acceso al repo **airbags/firmware** condicionado a **firma electrónica** del Acuerdo (Sección 3/4 expediente).
- Sin firma vigente: archivos en **blob cifrado** (ciphertext) → secreto industrial protegido ante acceso no autorizado.
- Agent5 Pro puede interceptar petición de clonado y validar Smart-Contract NDA antes de desbloquear.

## 4. Checklist OEPM / PCT

| Punto | Verificación |
|-------|--------------|
| **Integridad** | ZIP incluye esquemas eléctricos sensores piezoeléctricos, no solo código. |
| **Repetibilidad** | Memoria descriptiva permite a un experto **replicar** el sistema (requisito patentabilidad). |
| **No divulgación** | Nada publicado en redes/ferias **antes** del registro del hash o solicitud oficial (margen según jurisdicción). |

## 5. Checklist lanzamiento seguro

- **Repetibilidad:** ¿Un ingeniero podría construir el anillo con el contenido del ZIP?
- **Integridad del hash:** ZIP **no modificado** ni un bit tras generar el hash que va al documento firmado.
- **Certificado de novedad:** confirmar ausencia de divulgación previa.

Ver [CASTUO360-EXPEDIENTE-SOBERANIA-DIGITAL.md](CASTUO360-EXPEDIENTE-SOBERANIA-DIGITAL.md).
