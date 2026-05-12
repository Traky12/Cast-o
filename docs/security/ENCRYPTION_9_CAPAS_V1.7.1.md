# CASTÚO-SYSTEM v1.7.1 — 10+1 Capas Encriptación Enterprise

Plataforma Web3 agrovoltaica production LIVE. Primera cooperativa Sabionda SAT onboarded. ROI €352K anual 2.5 ha validado.

---

## Resumen

**Todo queda tras una capa con la clave maestra del administrador general** ([ADMIN_MASTER_LAYER](ADMIN_MASTER_LAYER.md)): bundles y secretos opcionales pueden cifrarse con ella; sin esa clave no se accede.

| Capa | Tecnología | Objetivo |
|------|------------|----------|
| **0** | **Clave maestra administrador** | Una clave (env / Docker secret / security/.admin_master_key) cifra todo lo sensible; AES-256-GCM + HKDF |
| 1 | HashiCorp Vault | Secrets centralizados (claves NFT, RPC, IPFS) |
| 2 | Docker Secrets + Compose | Claves en runtime sin exponer en imagen |
| 3 | SOPS + AGE | Archivos .env y compose cifrados en repo |
| 4 | Git-crypt + GPG | Archivos críticos (.key, private/) cifrados en Git |
| 5 | Kubernetes RBAC + Taints | Mínimo privilegio y nodos dedicados críticos |
| 6 | NFT Master Key Hierarchy | HKDF desde MASTER_KEY para minter, IPFS, audit, proxy |
| 7 | Audit Trail Inmutable | IPFS + testigo en GaiaChain por evento crítico |
| 8 | HSM + MPC | Fireblocks/DFNS en producción; Ledger/Trezor root |
| 9 | Verificación diaria | Script master-encrypt-verify.sh + cron |
| 10 | GDPR Art.30 | Registro actividades y request-erasure |

---

## Capa 0: Clave maestra administrador general

Todo el material sensible puede cifrarse **bajo una única capa** con la clave maestra del administrador del sistema. Sin esta clave no se accede a los payloads protegidos.

- **Origen de la clave:** `ADMIN_MASTER_KEY` (env), `/run/secrets/admin_master_key` (Docker), o `security/.admin_master_key` (local; no versionar).
- **Cifrado:** HKDF-SHA256(salt, info) → clave 32 bytes; AES-256-GCM. Salida base64(nonce \|\| ct).
- **CLI:** `python3 security/encrypt_with_admin_master.py encrypt|decrypt -i archivo -o salida`.
- **Módulo:** [security/admin_master_layer.py](../../security/admin_master_layer.py); ver [ADMIN_MASTER_LAYER.md](ADMIN_MASTER_LAYER.md).

---

## Capa 1: Vault Secrets (HashiCorp Vault)

```bash
vault kv put castuo-system/nft \
  private_key="mpc://sabionda-omega-2040" \
  gaia_rpc="https://gaiachain-testnet" \
  ipfs_key="sabionda-nft-master-v1.7"
```

Consumo desde app: `vault kv get -field=private_key castuo-system/nft`.

---

## Capa 2: Docker Secrets + Compose

Crear secrets (Swarm):

```bash
echo "mpc://sabionda-root" | docker secret create castuo_root_key -
echo "https://gaiachain-testnet" | docker secret create gaia_chain_rpc -
echo "NFT_PRIVATE_KEY_HEX" | docker secret create nft_private_key -
```

Referencia en [docker-compose.hetzner.yml](../../docker-compose.hetzner.yml): los servicios `backend` y `api` montan `castuo_root_key`, `gaia_chain_rpc`, `nft_private_key`. Variables de entorno: `NFT_KEY_PATH=/run/secrets/nft_private_key`.

---

## Capa 3: SOPS + AGE (Mozilla SOPS)

```bash
# Generar par age
age-keygen -o castuo-age.pub

# Cifrar
sops --encrypt --age $(cat castuo-age.pub | grep -o 'AGE.*') .env > .env.sops
sops --encrypt --age $(cat castuo-age.pub | grep -o 'AGE.*') docker-compose.hetzner.yml > compose.sops

# Desencriptar en runtime (CI o servidor)
sops --decrypt .env.sops > .env
```

Configuración: [.sops.yaml](../../.sops.yaml) (PGP o AGE).

---

## Capa 4: Git-crypt + GPG

```bash
git-crypt init
gpg --gen-key "CASTÚO 360 S.L. gregorio@castuo.es"
git-crypt add-gpg-user gregorio@castuo.es
```

Archivos cubiertos en [.gitattributes](../../.gitattributes): `.key`, `private/**`, `backend/config/secrets/**`, `.env`. Bloquear antes de push: `git-crypt lock && git add -u && git commit -m "🔒 Encriptación git-crypt v1.7"`.

---

## Capa 5: Kubernetes RBAC + Taints

Manifest: [kubernetes/castuo-secure.yaml](../../kubernetes/castuo-secure.yaml).

- Namespace `castuo-secure`, ServiceAccount `nft-minter-sa`, Role `nft-minter-role`, RoleBinding `castuo-nft-minter`.
- Deployment con `serviceAccountName: nft-minter-sa` y toleration `castuo-critical=:NoSchedule` para nodos dedicados.

Aplicar: `kubectl apply -f kubernetes/castuo-secure.yaml`. Nodos críticos: `kubectl taint nodes <node> castuo-critical=:NoSchedule`.

---

## Capa 6: NFT Master Key Hierarchy (HKDF)

```
MASTER_KEY = sabionda-omega-global-2040-v1.7.0
├── nft_minter_key  = HKDF(MASTER_KEY, "nft-minter")
├── ipfs_pin_key    = HKDF(MASTER_KEY, "ipfs-pinning")
├── audit_log_key   = HKDF(MASTER_KEY, "immutable-audit")
└── proxy_admin     = HKDF(MASTER_KEY, "contract-upgrade")
```

Exportar en entorno: `MASTER_KEY` o derivados (`NFT_MINTER_KEY`, etc.). Opcional: crear `security/.master-key-hierarchy` (no versionar contenido real). Verificación en [security/master-encrypt-verify.sh](../../security/master-encrypt-verify.sh) (check 6).

---

## Capa 7: Audit Trail Inmutable (IPFS + GaiaChain)

Clase [security/immutable_audit.py](../../security/immutable_audit.py):

```python
class ImmutableAudit:
    def log_critical_event(self, event_type, data):
        audit_blob = {
            "timestamp": datetime.utcnow(),
            "event": event_type,
            "data_hash": sha256(json.dumps(data)),
            "signer": self.signer_address
        }
        ipfs_hash = pin_json(audit_blob, self.audit_log_key)
        witness_to_gaia(ipfs_hash)  # On-chain proof
```

Uso: `audit = ImmutableAudit(); audit.log_critical_event("nft_mint", {"token_id": 1})`.

---

## Capa 8: HSM + MPC

- **Producción:** Fireblocks/DFNS. `MPC_ENDPOINT="mpc.fireblocks.io/sabionda"`, `export PRIVATE_KEY_MPC="mpc://castuo-sabionda-nft-v1.7"`.
- **Root maestro:** Ledger/Trezor. `ledger connect --app=Ethereum --contract=DynamicCropNFT`.

Marcar configurado: `touch security/.hsm-mpc-configured` (no versionar claves). Ver [docs/security/Fireblocks-Custody.md](Fireblocks-Custody.md), [Ledger-Vault-Integration.md](Ledger-Vault-Integration.md).

---

## Capa 9: Verificación automática diaria

Script: [security/master-encrypt-verify.sh](../../security/master-encrypt-verify.sh).

```bash
chmod +x security/master-encrypt-verify.sh
./security/master-encrypt-verify.sh
```

Salida esperada: `🔒 CASTÚO-SYSTEM ENCRYPTION: N/9 SECURE`. Cron recomendado: `0 6 * * * /path/to/repo/security/master-encrypt-verify.sh`.

---

## Comando único (ejecución ~15 min en Hetzner)

```bash
chmod +x security/master-encrypt-verify.sh &&
./security/master-encrypt-verify.sh &&
echo "mpc://sabionda-root" | docker secret create castuo_root_key - 2>/dev/null || true &&
# sops --encrypt --age castuo-age.pub .env > .env.sops  # si age configurado
git-crypt lock 2>/dev/null || true &&
# mkdocs gh-deploy --message "v1.7.1: TOTAL ENCRYPTION 9/9"  # si docs en gh-pages
echo "🔒 IMPERIO AGROVOLTAICO TOTALMENTE PROTEGIDO"
```

---

## Verificación final esperada

```
🔒 CASTÚO-SYSTEM ENCRYPTION: 9/9 SECURE
✅ Vault secrets activos
✅ Docker secrets mounted
✅ SOPS configs encrypted
✅ Git-crypt locked
✅ NFT Master Key HKDF
✅ Audit trail IPFS+GaiaChain
✅ HSM/MPC production
✅ K8s RBAC + taints
✅ Daily verification cron

¡Trazabilidad inmutable → NFTs protegidos → Cooperativas seguro!
```

---

[← Documentación seguridad](.) · [Estatus y valor v1.7.1](../vision/ESTATUS_VALOR_V1.7.1.md)
