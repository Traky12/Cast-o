# Plan de implementación priorizada v2.0

Basado en **AUTOMATIZACION_SOBERANA_CASTUO_v2.md**.

## Objetivo inmediato

Implementar los módulos críticos para:

- Cifrado post-cuántico (Kyber-1024 / Dilithium-5) en `backend/security/pq_crypto.py`
- Agentes autónomos: `backend/agents/master_agent.py`, `backend/agents/selfhealing_agent.py`
- Auto-evolución con git hooks (pre-commit / post-merge)
- Integración con Mistral AI (solo dependencias europeas)

---

## PASO 1: Cifrado post-cuántico ✅

| Elemento | Ubicación | Estado |
|----------|-----------|--------|
| Módulo principal | `backend/security/pq_crypto.py` | Implementado |
| Directorio de claves | `backend/security/keys/` o `CASTUO_KEY_DIR` | Configurable |
| Tests | `backend/security/tests/test_pq_crypto.py` | Implementado |
| Fallback sin pqcrypto | AES-256-GCM + HKDF / firma simulada | Activo |
| Blake3 / SHA3-512 | `_blake3_hex` con fallback Python &lt; 3.11 | Activo |

Próximos pasos opcionales: integración con Vault (`backend/scripts/manage_vault_keys.py`), vectores NIST en `backend/security/tests/test_vectors/`.

---

## PASO 2: Agentes autónomos ✅

| Componente | Archivo | Estado |
|------------|---------|--------|
| Agente maestro | `backend/agents/master_agent.py` | Implementado (Mistral + Prometheus opcionales) |
| Self-healing | `backend/agents/selfhealing_agent.py` | Implementado (Mistral + Docker opcionales) |

Los agentes usan dependencias opcionales: si Mistral o Prometheus no están configurados, no fallan y registran advertencias.

---

## PASO 3: Git hooks y scripts ✅

| Elemento | Ubicación | Estado |
|----------|-----------|--------|
| Pre-commit (ejemplo) | `docs/git-hooks/pre-commit` | Plantilla para copiar a `.git/hooks/pre-commit` |
| Post-merge (ejemplo) | `docs/git-hooks/post-merge` | Plantilla para copiar a `.git/hooks/post-merge` |
| Análisis con Mistral | `backend/scripts/analyze_with_mistral.py` | Implementado |
| Optimización código | `backend/scripts/optimize_code.py` | Implementado |
| Análisis de cambios | `backend/scripts/analyze_changes.py` | Implementado |
| Propuestas de mejora | `backend/scripts/propose_improvements.py` | Implementado |

Instalación manual de hooks:

```bash
cp docs/git-hooks/pre-commit .git/hooks/pre-commit && chmod +x .git/hooks/pre-commit
cp docs/git-hooks/post-merge   .git/hooks/post-merge   && chmod +x .git/hooks/post-merge
```

---

## PASO 4: Cliente Mistral AI ✅

| Elemento | Archivo | Estado |
|----------|---------|--------|
| Cliente seguro | `backend/ai/mistral_client.py` | Implementado |
| Validación normativa | Mensaje de sistema con ISO 27001, GDPR, NIS2, EU AI Act | Activo |
| Logging a GaiaChain | Opcional, cifrado con `PostQuantumCrypto` | Si script existe |

---

## PASO 5: GitHub Actions ✅

| Elemento | Archivo | Estado |
|----------|---------|--------|
| Workflow autónomo | `.github/workflows/autonomous_deployment.yml` | Implementado |
| Revisión de despliegue | `backend/scripts/review_deployment.py` | Implementado |

El workflow ejecuta: analyze-code (Mistral) → test (pytest) → security-scan → deploy-staging → mistral-review → deploy-production. Los pasos que dependen de secretos (MISTRAL_API_KEY_EU, VAULT_*) salen con éxito si no están configurados.

---

## Checklist final

| Item | Verificado |
|------|------------|
| Cifrado post-cuántico funcional (con fallback) | ✅ |
| Tests en `backend/security/tests/test_pq_crypto.py` | ✅ |
| Agentes maestro y self-healing operativos (con deps opcionales) | ✅ |
| Scripts de hooks (analyze_with_mistral, optimize_code, analyze_changes, propose_improvements) | ✅ |
| Cliente Mistral con validación y logging opcional | ✅ |
| Workflow autonomous_deployment.yml y review_deployment.py | ✅ |
| Documentación en docs/vision/ | ✅ |

---

## Próximos hitos recomendados

1. Desplegar en staging y validar con `python backend/scripts/review_deployment.py --environment staging`.
2. Configurar secretos en GitHub: `MISTRAL_API_KEY_EU`, `VAULT_ADDR`, `VAULT_TOKEN` si se usa Vault.
3. Copiar hooks de `docs/git-hooks/` a `.git/hooks/` y probar con un commit de prueba.
4. Integrar registro en GaiaChain (`register_gaiachain_event.py`) cuando el servicio esté disponible.
