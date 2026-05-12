# Checklist — cifrado total (tránsito, reposo, secretos)

**Relación:** [PRONTUARIO-MAESTRO-INTEGRACION-CIFRADA-SOBERANA-2026.md](./PRONTUARIO-MAESTRO-INTEGRACION-CIFRADA-SOBERANA-2026.md)

Marca con **evidencia** (fecha, enlace a ticket o informe). Objetivo: **ningún secreto en git** y TLS donde haya datos sensibles.

## Tránsito

- [ ] HTTPS/TLS en todos los frontends y APIs expuestas
- [ ] TLS (o equivalente) entre app y PostgreSQL si la política lo exige
- [ ] TLS en Redis si el despliegue es multi-host o red compartida
- [ ] Versión de TLS y ciphers documentadas; certificados con cadena válida
- [ ] PQ/híbrido: solo si está **probado** en staging — ver [CASTUO-SECURITY-VSA-PQC-EXECUTIVE.md](../security/CASTUO-SECURITY-VSA-PQC-EXECUTIVE.md) y `pq_crypto.py`

## Reposo

- [ ] Volúmenes o discos cifrados *(LUKS / proveedor / BitLocker)* según plataforma
- [ ] Política de backup: cifrado + prueba de **restauración** documentada
- [ ] PostgreSQL: cifrado vía **proveedor/disco** o aplicación — sin confundir con “TDE nativo”

## Secretos y claves

- [ ] Producción: opción **A** `*_FILE` / Docker secrets o **B** Vault — [PRONTUARIO-REFUERZO-SECRETS-VAULT-2026.md](../legal/PRONTUARIO-REFUERZO-SECRETS-VAULT-2026.md)
- [ ] Rutas KV conocidas: [VAULT_KV_PATHS.md](../../backend/security/VAULT_KV_PATHS.md)
- [ ] Rotación: [POLITICA-ROTACION-CLAVES.md](./POLITICA-ROTACION-CLAVES.md)

## Identidad y acceso

- [ ] MFA en superficies críticas *(según IdP)*
- [ ] JWT firmados con algoritmo acordado *(no mezclar con PQC sin diseño explícito)*

## Cumplimiento

- [ ] DPIA actualizada si cambia ubicación o nuevos encargados ([DPIA-Robotics-2026.md](../legal/DPIA-Robotics-2026.md))
- [ ] Escaneo TLS/config autorizado archivado

---

*Checklist sin evidencia es cifrado en el cartel: se ve bien desde la carretera, no desde el laboratorio.*
