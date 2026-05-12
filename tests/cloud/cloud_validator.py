#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path


REQUIRED_ENV_KEYS = [
    "VAULT_ADDR",
    "S3_BUCKET_LOGS",
    "GAIA_X_RPC",
    "ALLOWED_ORIGINS",
]

IOT_PROFILE_ENV_KEYS = [
    "WIRELESS_LOGIC_MQTT_HOST",
    "IOT_TELEMETRY_URL",
    "IOT_DEVICE_CMD_URL",
    "WIRELESS_LOGIC_MQTT_USER",
    "WIRELESS_LOGIC_MQTT_PASS",
]

REQUIRED_SECRETS = [
    "vault_token",
    "iot_bearer",
    "mistral_key",
    "sabionda_key",
]

IOT_PROFILE_SECRETS = [
    "wireless_logic_token",
]

VALID_PROFILES = {"core", "observability", "iot", "ai"}


def load_env_file(env_path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw in env_path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def run_compose_config(compose_file: Path, env_file: Path) -> tuple[bool, str]:
    cmd = [
        "docker",
        "compose",
        "-f",
        str(compose_file),
        "--env-file",
        str(env_file),
        "config",
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        return False, proc.stderr.strip() or proc.stdout.strip()
    return True, proc.stdout


def main() -> int:
    parser = argparse.ArgumentParser(description="CASTUO cloud GO/NO-GO validator.")
    parser.add_argument("--env-file", default=".env.cloud")
    parser.add_argument("--compose-file", default="docker-compose.cloud.yml")
    parser.add_argument("--profiles", default="core,observability")
    args = parser.parse_args()

    env_file = Path(args.env_file)
    compose_file = Path(args.compose_file)
    secrets_dir = Path("secrets")

    errors: list[str] = []
    warnings: list[str] = []

    if not env_file.exists():
        errors.append(f"Env file not found: {env_file}")
    if not compose_file.exists():
        errors.append(f"Compose file not found: {compose_file}")
    if errors:
        for err in errors:
            print(f"NO-GO: {err}")
        return 1

    env_map = load_env_file(env_file)
    missing_env = [k for k in REQUIRED_ENV_KEYS if not env_map.get(k)]
    for key in missing_env:
        errors.append(f"Missing required env var: {key}")

    requested_profiles = {p.strip() for p in args.profiles.split(",") if p.strip()}
    invalid_profiles = sorted(requested_profiles - VALID_PROFILES)
    if invalid_profiles:
        errors.append(f"Invalid profiles requested: {', '.join(invalid_profiles)}")

    if "iot" in requested_profiles:
        missing_iot_env = [k for k in IOT_PROFILE_ENV_KEYS if not env_map.get(k)]
        for key in missing_iot_env:
            errors.append(f"Missing required iot env var: {key}")

    for secret_name in REQUIRED_SECRETS:
        secret_path = secrets_dir / secret_name
        if not secret_path.exists():
            errors.append(f"Missing secret file: {secret_path}")

    if "iot" in requested_profiles:
        for secret_name in IOT_PROFILE_SECRETS:
            secret_path = secrets_dir / secret_name
            if not secret_path.exists():
                errors.append(f"Missing required iot secret file: {secret_path}")

    ok_config, compose_output = run_compose_config(compose_file, env_file)
    if not ok_config:
        errors.append(f"docker compose config failed: {compose_output}")
    elif "services:" not in compose_output:
        warnings.append("Compose config output did not include expected service section.")

    if warnings:
        for warning in warnings:
            print(f"WARNING: {warning}")

    if errors:
        for err in errors:
            print(f"NO-GO: {err}")
        return 1

    print("GO: Cloud v4.1 validation passed.")
    print(f"GO: Profiles validated -> {', '.join(sorted(requested_profiles))}")
    print(f"GO: Compose file -> {compose_file}")
    print(f"GO: Env file -> {env_file}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
