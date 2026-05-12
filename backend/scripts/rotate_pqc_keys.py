#!/usr/bin/env python3
# backend/scripts/rotate_pqc_keys.py — Rotación de claves PQC y notificación a agentes

from __future__ import annotations

import argparse
import base64
import json
import logging
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def rotate_keys(dry_run: bool = False) -> bool:
    """Genera nuevas claves Kyber/Dilithium, las guarda en Vault y notifica a los agentes."""
    from backend.security.pq_crypto import PostQuantumCrypto

    crypto = PostQuantumCrypto()
    if dry_run:
        pub_k, priv_k = crypto._generate_kyber_keypair_raw()
        pub_d, priv_d = crypto._generate_dilithium_keypair_raw()
        logger.info("Dry-run: generadas claves Kyber len=%s/%s Dilithium len=%s/%s", len(pub_k), len(priv_k), len(pub_d), len(priv_d))
        return True

    try:
        logger.info("Generando nuevas claves Kyber-1024 y Dilithium-5...")
        pub_k, priv_k = crypto._generate_kyber_keypair_raw()
        pub_d, priv_d = crypto._generate_dilithium_keypair_raw()

        pub_k_b64 = base64.b64encode(pub_k).decode("ascii")
        priv_k_b64 = base64.b64encode(priv_k).decode("ascii")
        pub_d_b64 = base64.b64encode(pub_d).decode("ascii")
        priv_d_b64 = base64.b64encode(priv_d).decode("ascii")
        ts = datetime.utcnow().isoformat()

        use_vault = bool(os.getenv("VAULT_TOKEN"))
        if use_vault:
            try:
                import hvac
                client = hvac.Client(url=os.getenv("VAULT_ADDR", "http://127.0.0.1:8200"), token=os.getenv("VAULT_TOKEN"))
                if not client.is_authenticated():
                    logger.error("Vault: no autenticado")
                    return False
                client.secrets.kv.v2.create_or_update_secret(
                    path="keys/kyber",
                    mount_point="castuo",
                    secret={"public_key": pub_k_b64, "private_key": priv_k_b64, "rotation_timestamp": ts},
                )
                client.secrets.kv.v2.create_or_update_secret(
                    path="keys/dilithium",
                    mount_point="castuo",
                    secret={"public_key": pub_d_b64, "private_key": priv_d_b64, "rotation_timestamp": ts},
                )
                logger.info("Claves guardadas en Vault.")
            except ImportError:
                logger.warning("hvac no instalado; no se actualiza Vault.")
            except Exception as e:
                logger.error("Error escribiendo en Vault: %s", e)
                return False
        else:
            crypto._path("kyber_public.pem").write_bytes(base64.b64encode(pub_k))
            crypto._path("kyber_private.pem").write_bytes(base64.b64encode(priv_k))
            crypto._path("dilithium_public.pem").write_bytes(base64.b64encode(pub_d))
            crypto._path("dilithium_private.pem").write_bytes(base64.b64encode(priv_d))
            for p in ("kyber_private.pem", "dilithium_private.pem"):
                crypto._path(p).chmod(0o600)
            logger.info("Claves guardadas en disco.")

        try:
            from backend.agents.message_bus import AgentMessageBus
            bus = AgentMessageBus("key_rotator")
            bus.broadcast({"type": "key_rotation", "timestamp": ts, "action": "reload_keys"}, encrypt=False)
            logger.info("Notificación key_rotation enviada a los agentes.")
        except Exception as e:
            logger.debug("Message bus no disponible: %s", e)

        return True
    except Exception as e:
        logger.error("Error en rotación de claves: %s", e)
        return False


def main() -> None:
    parser = argparse.ArgumentParser(description="Rotación de claves PQC y notificación a agentes")
    parser.add_argument("--dry-run", action="store_true", help="Solo simular generación")
    args = parser.parse_args()
    ok = rotate_keys(dry_run=args.dry_run)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
