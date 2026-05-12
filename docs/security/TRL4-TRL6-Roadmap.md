# Roadmap TRL4 → TRL5 → TRL6 — CASTÚO-SYSTEM™

Verificación por fases: componentes criptográficos → finca simulada → fincas reales + SwissVault + GaiaChain.

---

## Checklist

- [ ] **TRL4:** `crypto_validation.py` → 100% componentes (AES-256-GCM, Shamir 3/5, HSM/PEM)
- [ ] **TRL5:** `docker-compose-trl5.yml` → Finca simulada (BookStack + SABIONDA encriptados)
- [ ] **TRL6:** 2 fincas reales + SwissVault shard-2
- [ ] **VERIFICACIÓN:** `./verify-trl6.sh` → Todas capas
- [ ] **CERTIFICACIÓN:** [docs/legal/TRL6-Certification.md](../legal/TRL6-Certification.md)

---

## Ejecución por fases

### Día 1: TRL4

```bash
docker compose -f docker/docker-compose-trl4.yml up --build
python tests/trl4/crypto_validation.py
```

### Día 45: TRL5

```bash
docker compose -f docker/docker-compose-trl5.yml up -d
./scripts/deploy/test-finca-simulada.sh
```

### Día 90: TRL6 LIVE

```bash
docker compose -f docker/docker-compose-trl6.yml up -d
curl -f https://89.167.5.233:8080
./scripts/deploy/verify-trl6.sh
```

---

## Resumen

| Fase  | Contenido                         | Test / Verify              |
|-------|-----------------------------------|----------------------------|
| TRL4  | AES-256-GCM + Shamir 3/5 (componentes) | `crypto_validation.py`     |
| TRL5  | HSM YubiKey + n8n/BookStack encriptados, finca simulada 99.9% | `test-finca-simulada.sh`   |
| TRL6  | SwissVault físico + GaiaChain + finca real, 99.999% uptime    | `verify-trl6.sh`           |

---

**Referencias:** [TRL6-Certification.md](../legal/TRL6-Certification.md) | [TRL11-Secure-SDLC.md](TRL11-Secure-SDLC.md)
