#!/usr/bin/env python3
"""Cloud overlay validator for CASTUO-SYSTEM v4.x.

Checks:
- Required environment variables in an env file
- Presence of required local secret files
- docker compose config for docker-compose.cloud.yml
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

REQUIRED_VARS = {
    "ENV",
    "API_PORT",
    "POSTGRES_PASSWORD",
    "N8N_PASSWORD",
    "VAULT_ADDR",
    "VAULT_TOKEN_FILE",
}

REQUIRED_SECRET_FILES = {
    "vault_token",
    "iot_bearer",
    "mistral_key",
    "sabionda_key",
}

REQUIRED_VARS_IOT = {
    "TRACES_HYPERLEDGER_URL",
}

REQUIRED_SECRET_FILES_IOT = {
    "wireless_logic_token",
}


def parse_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw in path.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"')
    return values


def _normalize_profiles(raw: str) -> set[str]:
    parts = [p.strip() for p in raw.replace(",", " ").split() if p.strip()]
    return set(parts) if parts else {"core", "iot", "ai", "observability"}


def validate_env(values: dict[str, str], profiles: set[str]) -> list[str]:
    required = set(REQUIRED_VARS)
    if "iot" in profiles:
        required.update(REQUIRED_VARS_IOT)
    missing = [k for k in sorted(required) if not values.get(k)]
    return missing


def validate_secret_files(root: Path, profiles: set[str]) -> list[str]:
    required = set(REQUIRED_SECRET_FILES)
    if "iot" in profiles:
        required.update(REQUIRED_SECRET_FILES_IOT)

    missing = []
    for name in sorted(required):
        if not (root / "secrets" / name).exists():
            missing.append(f"secrets/{name}")
    return missing


def validate_compose(env_file: Path, root: Path) -> str | None:
    try:
        subprocess.run(
            [
                "docker",
                "compose",
                "-f",
                "docker-compose.cloud.yml",
                "--env-file",
                str(env_file),
                "config",
            ],
            cwd=root,
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
        )
        return None
    except FileNotFoundError:
        return "docker not available in PATH"
    except subprocess.CalledProcessError as exc:
        return exc.stderr.strip() or "docker compose config failed"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--env-file", default=".env.cloud")
    parser.add_argument(
        "--profiles",
        default="core,iot,ai,observability",
        help="Comma or space separated compose profiles",
    )
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[2]
    env_path = (root / args.env_file).resolve() if not os.path.isabs(args.env_file) else Path(args.env_file)

    if not env_path.exists():
        print(f"NO-GO: missing env file: {env_path}")
        return 1

    profiles = _normalize_profiles(args.profiles)
    values = parse_env_file(env_path)
    missing_env = validate_env(values, profiles)
    missing_secrets = validate_secret_files(root, profiles)
    compose_error = validate_compose(env_path, root)

    if missing_env:
        print("NO-GO: missing required env vars:")
        for key in missing_env:
            print(f"- {key}")
    if missing_secrets:
        print("NO-GO: missing required secret files:")
        for path in missing_secrets:
            print(f"- {path}")
    if compose_error:
        print(f"NO-GO: compose validation failed: {compose_error}")

    if missing_env or missing_secrets or compose_error:
        return 1

    print("GO: cloud environment is valid")
    return 0


if __name__ == "__main__":
    sys.exit(main())
