# CASTUO 5.PRO+ | Edición Ladanum — Integración final backend + HSM

Activo certificado: **ABI** + **scripts PKCS#11** + **CI release** + **Xtranet Edge**.

## Identidad del nodo

| Capa | Tecnología | Función |
|------|------------|---------|
| Física | **LadanumCast™** (biocompuesto jara) | Térmica, dieléctrica, antioxidante |
| Identidad | **TPM + PUF** | Raíz de confianza no clonable |
| Datos | **HSM + blockchain** | Firma legal, trazabilidad |
| Lógica | **MPC** | Residencia vs algas / skid térmico |

## Artefactos en repo

| Componente | Ruta |
|------------|------|
| Contrato registro | `contracts/CastuoRegistry.sol` |
| ABI Web3/Python/Node | `contracts/CastuoRegistryABI.json` |
| Token BIOC (placeholder) | `contracts/CastuoToken.sol` |
| Firma manifiesto | `scripts/sign_manifest_hsm.sh` |
| Firma EvidenceHash | `scripts/sign_evidencehash_hsm_generic.sh` |
| Release tarball | `scripts/make_release.sh` |
| CI | `.github/workflows/ci-release.yml` |
| Núcleo Edge | `backend/xtranet/core.py` |

## Variables HSM

`PKCS11_MODULE`, `HSM_PIN`, `HSM_KEY_LABEL`. Paquetes bajo `CASTUO_package/<GEMELO_ID>/`.

## Roadmap (resumen)

- **2025:** LadanumCast certificación, nodo piloto (p. ej. Membrío), Parcela 0.
- **2026:** Marketplace BioCoin, CIS auditados (UEx), fotobiorreactores Chlorella.
- **2027:** BioGrid mesh, Portugal/Alentejo, LATAM.

Ver [CASTUO-LIBRO-BLANCO-5PRO-INTEGRAL.md](CASTUO-LIBRO-BLANCO-5PRO-INTEGRAL.md), [PROYECTO-CHLORELLA-5PRO.md](PROYECTO-CHLORELLA-5PRO.md).
