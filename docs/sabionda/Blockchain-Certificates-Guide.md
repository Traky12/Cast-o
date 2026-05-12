# Guía de Certificados Blockchain — Sabionda

**Objetivo**: Emitir certificados de formación verificables en GaiaChain (Smart Contract Solidity).

---

## Flujo

1. **Moodle** (o plataforma Sabionda): El alumno completa el curso.
2. **Backend**: Llama al contrato `SabiondaCertificates.issueCertificate(courseName, studentId, studentName, completionDate)`.
3. **GaiaChain**: Transacción registrada; evento `CertificateIssued`.
4. **Verificación**: Cualquier parte puede llamar `verifyCertificate(studentId)` y comprobar validez.

---

## Contrato

- Ubicación: `contracts/SabiondaCertificates.sol` (o `blockchain/contracts/`).
- Compilación: Hardhat. Despliegue en GaiaChain (testnet primero).
- Integración Moodle: Módulo o webhook que invoque la API del backend; el backend firma y envía la tx al contrato.

---

## Datos del certificado

- `courseName`: Nombre del curso (ej: "Experto en Trazabilidad Blockchain").
- `studentId`: Identificador único del alumno.
- `studentName`: Nombre (opcional, según privacidad).
- `completionDate`: Fecha de finalización (timestamp Unix).
- `isValid`: El propietario puede revocar con `revokeCertificate(studentId)`.

---

## Retención y privacidad

- Cumplir RGPD: minimizar datos personales en blockchain; usar hashes o identificadores opacos cuando proceda.
- Registro de actividades de tratamiento (AEPD) si se tratan datos personales en blockchain.
