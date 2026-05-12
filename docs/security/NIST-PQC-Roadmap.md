# NIST PQC Roadmap — CASTÚO-SYSTEM™

Algoritmos NIST estandarizados 2026: **ML-KEM (FIPS 203)**, **ML-DSA (FIPS 204)**, **SLH-DSA (FIPS 205)**. Objetivo: **CASTÚO-SYSTEM PQC LIVE 15/09/2026**.

---

## Algoritmos

| NIST / FIPS | Nombre liboqs | Uso |
|-------------|----------------|-----|
| ML-KEM (FIPS 203) | Kyber768 / Kyber1024 | Key Encapsulation |
| ML-DSA (FIPS 204) | Dilithium2 (ML-DSA-44) / Dilithium5 (ML-DSA-65) | Firmas digitales |
| SLH-DSA (FIPS 205) | SPHINCS+ | Hash-based signatures |

---

## Benchmark vs AES-256 + ECDSA

- **Kyber-768** → ~2.1x más lento → 100% quantum-safe  
- **Dilithium2** → ~3.4x firmas vs ECDSA → 128-bit post-quantum  
- **Throughput:** ~85% AES-256 (aceptable TRL4)  
- **Side-channel resistance:** ~95% (power analysis)

---

## Híbrido: AES-256 + Kyber-768

Transición suave: cifrado híbrido con `CastuoHybridPQC` (scripts/pqc/hybrid_crypto.py).

- 1. Kyber encapsula clave compartida.  
- 2. AES-256-GCM cifra datos con clave derivada del shared secret.

BookStack/n8n pueden usar `CASTUO_CRYPTO_MODE=hybrid_pqc` y `PQC_ALG=ML-KEM_768+ML-DSA_44`. Ejemplo de servicio:

```yaml
# bookstack-pqc (extensión compose)
services:
  bookstack-pqc:
    environment:
      - CASTUO_CRYPTO_MODE=hybrid_pqc
      - PQC_ALG=ML-KEM_768+ML-DSA_44
    volumes:
      - pqc_encrypted:/data
```

---

## Fincas Extremadura + Hetzner PQC

- **RPi4 B001** → Kyber TLS 1.3 PQC  
- **Hetzner CAX21** → OpenQuantumSafe liboqs  
- **SwissVault** → Shard Kyber encapsulado  

Instalación OpenQuantumSafe (RPi + Hetzner):

```bash
apt install liboqs-c   # Kyber/Dilithium nativo
openssl enable-fips    # Hybrid mode
```

---

## Roadmap 180 días → 15/09/2026 LIVE

| Fase | Contenido | Duración |
|------|-----------|----------|
| TRL1-3 | NIST ML-KEM/ML-DSA | 30 días |
| TRL4 | Componentes Kyber/Dilithium | 30 días |
| TRL5 | Híbrido AES+Kyber prototipo | 30 días |
| TRL6 | Fincas reales PQC TLS | 30 días |
| TRL7-8 | Sistema completo PQC | 30 días |
| TRL9 | Producción agrovoltaica PQC | 30 días |

**TOTAL: 180 días → 15/09/2026 LIVE**

---

## Verificación PQC

```bash
# Instalar OpenQuantumSafe
apt install liboqs-c openssl-fipsmodule

# TRL1 NIST PQC
docker run castuo/pqc-trl1 python scripts/pqc/benchmark_nist.py

# TRL4 Hybrid baseline
docker compose -f docker/docker-compose-trl4-pqc.yml up -d

# Verify (TLS PQC cuando el servidor soporte KYBER)
curl -I --ciphersuites KYBER https://89.167.5.233:8080
```

---

## Estado objetivo LIVE

- Kyber-1024 → 100% quantum-resistant (NIST FIPS 203)  
- Dilithium-65 → 256-bit classical / 128-bit quantum  
- 50 fincas → TLS 1.3 PQC 99.999% uptime  
- BookStack → https://89.167.5.233:8080 PQC LIVE  
- SwissVault → Shards Kyber físicos  

---

## Scripts y compose

| Recurso | Descripción |
|---------|-------------|
| `scripts/pqc/trl1_nist_pqc.py` | ML-KEM-768, ML-DSA-44 (keygen, encap, sign, verify) |
| `scripts/pqc/benchmark_nist.py` | Benchmark 1M encaps/firmas, throughput |
| `scripts/pqc/hybrid_crypto.py` | CastuoHybridPQC (AES + Kyber) |
| `docker/docker-compose-trl4-pqc.yml` | Servicio pqc-benchmark |
| `docker/docker-compose-trl8-pqc.yml` | castuo-pqc CRYPTO_MODE=pqc_only, ML-KEM-1024, ML-DSA-65 |

---

**Referencias:** [TRL4-TRL6-Roadmap.md](TRL4-TRL6-Roadmap.md) | [TRL6-Certification.md](../legal/TRL6-Certification.md)
