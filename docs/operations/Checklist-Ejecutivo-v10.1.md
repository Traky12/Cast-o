# Checklist ejecutivo v10.1 (legal + técnica)

**CASTÚO-SYSTEM™** — SABIONDA v10.1 | Estándar global agrotech autónoma (legal + técnica).

---

## Resumen por área

| Área | Estado | Acción | Responsable | Plazo |
|------|--------|--------|-------------|-------|
| Registro RPI | ⏳ Pendiente | Ejecutar 15:00 CET (13,59 €). [sede.mcu.gob.es/rpi4](https://sede.mcu.gob.es/rpi4) | Legal Team | 15/03/2026 |
| Registro EUIPO | ⏳ Pendiente | Ejecutar 16:00 CET (850 €). [euipo.europa.eu](https://euipo.europa.eu) | Legal Team | 15/03/2026 |
| Sustitución placeholders | ⏳ Pendiente | Ejecutar `./scripts/replace-placeholders.sh` 17:00 CET | DevOps | 15/03/2026 |
| Verificación integridad | ✅ Listo | `verify-integrity.sh` (código) + `docs/legal/verify-integrity-legal.sh` (legal) | Seguridad | Hecho |
| Contratos inteligentes | ✅ Listo | EUCore, DynamicCompliance, GlobalGovernance, CASTUO_System en GaiaChain | Blockchain Team | Hecho |
| Cursor integration | ✅ Listo | Workflow legal-update.yml para placeholders; reglas TRL9 | DevOps | Hecho |
| Protocolo África | ✅ Listo | SAHPRA/DAFF en `backend/services/contingency_fallback.py` | Legal Team | Hecho |
| Protocolo Asia | ✅ Listo | MHLW/JAS/PMDA en `backend/services/contingency_fallback.py` | Legal Team | Hecho |
| ISO 27001 | ✅ Certificado | Documentado en TRL9-AntiTampering-Certification.md | Seguridad | Hecho |
| TRL9 | ✅ Certificado | TRL9-AntiTampering-Certification.md + TRL9-status.txt | I+D | Hecho |
| PCT internacional | ⏳ En proceso | Solicitud PCT/ESXXXX/2026 | Legal Team | Q2 2026 |
| DAO global | ✅ Desplegada | Contrato GlobalGovernance.sol + DynamicCompliance | Blockchain Team | Hecho |
| Cursor workflows | ✅ Operativos | legal-update.yml + certify / global-certify / aemps / deploy | DevOps | Hecho |
| Darktrace | ✅ Activado | Monitoreo 24/7 en producción | Seguridad | Hecho |
| Chainalysis | ✅ Activado | chainalysis_fraud.py + scripts/chainalysis_monitor.py | Blockchain Team | Hecho |

---

## Pasos finales para ejecución (15/03/2026)

1. **RPI (15:00 CET)**  
   Registro en sede.mcu.gob.es/rpi4 con certificado digital; subir código + memoria + ejecutable v1.0.0-trl9.

2. **EUIPO (16:00 CET)**  
   Registro CASTÚO-SYSTEM + SABIONDA Clase 9+42 (y opcional CASTÚO 360 9+42+35).

3. **Git (17:00 CET)**  
   ```bash
   RPI_NUMBER=RPI-XXXX/2026 EUIPO_NUMBER=EUIPO-YYYY/2026 ./scripts/replace-placeholders.sh
   git add docs/legal && git commit -m "LEGAL: Sustitución placeholders [TRL9]"
   git tag -a v1.0.0 -m "Versión legal certificada" && git push origin v1.0.0
   ```

4. **Verificar integridad**  
   ```bash
   ./docker/castuo-bookstack/verify-integrity.sh
   docs/legal/verify-integrity-legal.sh
   ```

5. **Despliegue producción**  
   ```bash
   # Cursor / CI: deploy con tag v1.0.0
   # cursor deploy --env production --tag v1.0.0
   ```

---

**Referencias**

- [SABIONDA-v10.0-Global-Standard.md](../ai/SABIONDA-v10.0-Global-Standard.md)
- [CASTUO-Legal-Framework.md](../legal/CASTUO-Legal-Framework.md)
- [TRL9-AntiTampering-Certification.md](../legal/TRL9-AntiTampering-Certification.md)
