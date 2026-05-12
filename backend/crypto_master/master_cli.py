#!/usr/bin/env python3
# backend/crypto_master/master_cli.py
# CLI Admin General — GREGORIO J JIMÉNEZ BODES

from __future__ import annotations

import argparse
import json
import os
import sys

try:
    from .master_key_manager import MasterKeyManager
    from .hierarchical_keys import get_admin_structure
    from .admin_structure import get_roles_table
except ImportError:
    from master_key_manager import MasterKeyManager
    from hierarchical_keys import get_admin_structure
    from admin_structure import get_roles_table


def cmd_status() -> int:
    m = MasterKeyManager()
    print("CLAVE_MAESTRA: loaded (Shamir 3/5)")
    print("Shares:", len(m.shamir_shares))
    print("Risk threshold:", m.risk_threshold)
    return 0


def cmd_roles() -> int:
    for r in get_roles_table():
        print(f"  Nivel {r['nivel']}: {r['rol']} — {r['clave']} — {r['acceso']} — {r['riesgo']}")
    return 0


def cmd_derive(system_id: str, level: int) -> int:
    m = MasterKeyManager()
    sub = m.derive_subkey(system_id, level)
    print(sub.hex())
    return 0


def cmd_broadcast(data_json: str, targets: list[str]) -> int:
    m = MasterKeyManager()
    if os.path.isfile(data_json):
        with open(data_json, encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = json.loads(data_json)
    out = m.encrypt_broadcast(data, targets)
    print(json.dumps(out, indent=2))
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description="Master CLI Admin General CASTÚO 360")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("status", help="Estado clave maestra y Shamir")
    sub.add_parser("roles", help="Tabla roles jerárquicos")
    d = sub.add_parser("derive", help="Derivar sub-clave")
    d.add_argument("system_id", help="OMEGA|SABIONDA|FEDERACION|EDU|AUDIT")
    d.add_argument("level", type=int, help="0-4")
    b = sub.add_parser("broadcast", help="Encriptar broadcast")
    b.add_argument("--data", required=True, help="JSON payload or path to .json file")
    b.add_argument("--targets", required=True, nargs="+", help="Targets")
    args = p.parse_args()

    if args.cmd == "status":
        return cmd_status()
    if args.cmd == "roles":
        return cmd_roles()
    if args.cmd == "derive":
        return cmd_derive(args.system_id, args.level)
    if args.cmd == "broadcast":
        return cmd_broadcast(args.data, args.targets)
    return 1


if __name__ == "__main__":
    sys.exit(main())
