#!/usr/bin/env python3
# backend/scripts/manage_vault_keys.py — Gestión de claves post-cuánticas en HashiCorp Vault
# Uso: python backend/scripts/manage_vault_keys.py --init | --load

from __future__ import annotations

import argparse
import os
import sys

# Raíz del repo para imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))


def _key_dir():
    d = os.getenv("CASTUO_KEY_DIR")
    if d:
        return os.path.abspath(d)
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "security", "keys"))


def init_vault() -> None:
    """Genera claves Kyber y Dilithium (local) y las sube a Vault."""
    try:
        import hvac
    except ImportError:
        print("Instalar hvac: pip install hvac")
        sys.exit(1)

    from backend.security.pq_crypto import PostQuantumCrypto

    key_dir = _key_dir()
    os.makedirs(key_dir, exist_ok=True)
    try:
        os.chmod(key_dir, 0o700)
    except OSError:
        pass

    # Generar claves locales (PostQuantumCrypto escribe en CASTUO_KEY_DIR o backend/security/keys)
    env_before = os.environ.get("CASTUO_KEY_DIR")
    os.environ["CASTUO_KEY_DIR"] = key_dir
    try:
        crypto = PostQuantumCrypto()
    finally:
        if env_before is not None:
            os.environ["CASTUO_KEY_DIR"] = env_before
        else:
            os.environ.pop("CASTUO_KEY_DIR", None)

    # Leer claves generadas
    def read_b64(path: str) -> str:
        with open(os.path.join(key_dir, path), "rb") as f:
            return f.read().decode("ascii").strip()

    kyber_pub = read_b64("kyber_public.pem")
    kyber_priv = read_b64("kyber_private.pem")
    dilithium_pub = read_b64("dilithium_public.pem")
    dilithium_priv = read_b64("dilithium_private.pem")

    # Conectar a Vault
    url = os.getenv("VAULT_ADDR", "http://127.0.0.1:8200")
    token = os.getenv("VAULT_TOKEN", "")
    if not token:
        print("Definir VAULT_TOKEN (y VAULT_ADDR si no es localhost:8200)")
        sys.exit(1)

    client = hvac.Client(url=url, token=token)
    if not client.is_authenticated():
        print("Vault: autenticación fallida")
        sys.exit(1)

    # Habilitar kv-v2 en castuo si no existe
    try:
        client.sys.enable_secrets_engine("kv", path="castuo", options={"version": "2"})
    except Exception:
        pass

    # Escribir secretos (path en kv-v2: castuo/data/keys/kyber)
    client.secrets.kv.v2.create_or_update_secret(
        path="keys/kyber",
        mount_point="castuo",
        secret={"public_key": kyber_pub, "private_key": kyber_priv},
    )
    client.secrets.kv.v2.create_or_update_secret(
        path="keys/dilithium",
        mount_point="castuo",
        secret={"public_key": dilithium_pub, "private_key": dilithium_priv},
    )
    print("Claves Kyber y Dilithium guardadas en Vault (castuo/keys/kyber, castuo/keys/dilithium)")
    print("Directorio local:", key_dir)


def load_from_vault() -> None:
    """Descarga claves desde Vault y las escribe en CASTUO_KEY_DIR (o backend/security/keys)."""
    try:
        import hvac
    except ImportError:
        print("Instalar hvac: pip install hvac")
        sys.exit(1)

    key_dir = _key_dir()
    os.makedirs(key_dir, exist_ok=True)
    try:
        os.chmod(key_dir, 0o700)
    except OSError:
        pass

    url = os.getenv("VAULT_ADDR", "http://127.0.0.1:8200")
    token = os.getenv("VAULT_TOKEN", "")
    if not token:
        print("Definir VAULT_TOKEN")
        sys.exit(1)

    client = hvac.Client(url=url, token=token)
    if not client.is_authenticated():
        print("Vault: autenticación fallida")
        sys.exit(1)

    def write_pem(name: str, content: str, private: bool = False) -> None:
        path = os.path.join(key_dir, name)
        with open(path, "wb") as f:
            f.write(content.strip().encode("ascii"))
        if private:
            try:
                os.chmod(path, 0o600)
            except OSError:
                pass

    try:
        kyber = client.secrets.kv.v2.read_secret(path="keys/kyber", mount_point="castuo")
        data = kyber["data"]["data"]
        write_pem("kyber_public.pem", data["public_key"])
        write_pem("kyber_private.pem", data["private_key"], private=True)
    except Exception as e:
        print("Error leyendo castuo/keys/kyber:", e)
        sys.exit(1)

    try:
        dilithium = client.secrets.kv.v2.read_secret(path="keys/dilithium", mount_point="castuo")
        data = dilithium["data"]["data"]
        write_pem("dilithium_public.pem", data["public_key"])
        write_pem("dilithium_private.pem", data["private_key"], private=True)
    except Exception as e:
        print("Error leyendo castuo/keys/dilithium:", e)
        sys.exit(1)

    print("Claves cargadas desde Vault en:", key_dir)


def main() -> None:
    parser = argparse.ArgumentParser(description="Gestión de claves post-cuánticas en Vault")
    parser.add_argument("--init", action="store_true", help="Generar claves locales y subirlas a Vault")
    parser.add_argument("--load", action="store_true", help="Cargar claves desde Vault al directorio local")
    args = parser.parse_args()

    if args.init:
        init_vault()
    elif args.load:
        load_from_vault()
    else:
        parser.print_help()
        sys.exit(0)


if __name__ == "__main__":
    main()
