# CERTIFICACIÓN TRL6 — CASTÚO-SYSTEM™

## Fincas reales + Hetzner + SwissVault LIVE

**OBJETIVO:** Fincas reales Extremadura, MQTT encriptado a Hetzner, shard 2/5 en SwissVault Zúrich, GaiaChain witness, Behavioral Auth.

---

## EVOLUCIÓN TRL4 → TRL5 → TRL6

| TRL  | Contenido | Verificación |
|------|-----------|--------------|
| **TRL4** | AES-256-GCM + Shamir 3/5 + HSM/PEM (componentes) | `python tests/trl4/crypto_validation.py` |
| **TRL5** | BookStack + SABIONDA encriptados, finca simulada 99.9% | `./test-finca-simulada.sh` |
| **TRL6** | 2 fincas reales, SwissVault shard-2, GaiaChain, Behavioral AI | `./verify-trl6.sh` |

---

## CRITERIOS TRL6

- ✅ 2 fincas reales → 10 parcelas → 100% encriptadas  
- ✅ SwissVault shard-2 → Recuperación 3/5 OK  
- ✅ GaiaChain → transacciones firmadas  
- ✅ Behavioral AI → detección intrusos  
- ✅ BookStack → https://89.167.5.233:8080 TRL6 LIVE  

---

## VERIFICACIÓN

```bash
# Todas las capas TRL6
./scripts/deploy/verify-trl6.sh
```

Variables opcionales: `CASTUO_BOOKSTACK_URL`, `SWISS_VAULT_SHARD`, `GAIA_CHAIN_ADMIN_KEY`, `BEHAVIORAL_AUTH_ENABLED`.

---

## DEPLOY TRL6

```bash
# Día 90: TRL6 LIVE
docker compose -f docker/docker-compose-trl6.yml up -d
curl -f https://89.167.5.233:8080
./scripts/deploy/verify-trl6.sh
```

---

## ROADMAP (Día 1 / 45 / 90)

Véase [TRL4-TRL6-Roadmap.md](../security/TRL4-TRL6-Roadmap.md) para checklist y comandos por fase.

## REFERENCIAS

- [TRL9-AntiTampering-Certification.md](TRL9-AntiTampering-Certification.md) — Base TRL9  
- [TRL11-Secure-SDLC.md](../security/TRL11-Secure-SDLC.md) — Pipeline CI/CD  
- [Swiss-Vault-Integration.md](../security/Swiss-Vault-Integration.md) — Custodia shard 2/5  
