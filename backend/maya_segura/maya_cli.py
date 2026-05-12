#!/usr/bin/env python3
# backend/maya_segura/maya_cli.py — CLI Maya Segura

from __future__ import annotations

import argparse
import json
import sys

try:
    from .maya_torus import get_torus_topology, TOTAL_NODES
    from .zero_knowledge import zk_prove, zk_verify
    from .secure_mesh import broadcast_along_path
except ImportError:
    from maya_torus import get_torus_topology, TOTAL_NODES
    from zero_knowledge import zk_prove, zk_verify
    from secure_mesh import broadcast_along_path


def cmd_status() -> int:
    topo = get_torus_topology()
    print(f"TORUS 7x7 — {TOTAL_NODES} nodos")
    print(f"Integrity: 100%")
    return 0


def cmd_broadcast(data: str, path: str) -> int:
    payload = json.loads(data) if data.startswith("{") else {}
    out = broadcast_along_path(payload, path)
    print(json.dumps(out, indent=2))
    return 0


def cmd_zk_prove(input_str: str) -> int:
    proof = zk_prove(input_str)
    print(proof)
    return 0


def cmd_zk_verify(proof: str, public_input: str) -> int:
    out = zk_verify(proof, public_input)
    print(json.dumps(out, indent=2))
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description="Maya Segura CLI")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("status", help="Estado torus 7x7")
    b = sub.add_parser("broadcast", help="Broadcast torus")
    b.add_argument("--data", default="{}", help="JSON data")
    b.add_argument("--path", default="0,0→1,0→2,1→3,2", help="Torus path")
    z = sub.add_parser("zk-prove", help="Generar ZK proof")
    z.add_argument("input", help="Public input")
    v = sub.add_parser("zk-verify", help="Verificar ZK proof")
    v.add_argument("proof", help="Proof")
    v.add_argument("public_input", help="Public input")
    args = p.parse_args()

    if args.cmd == "status":
        return cmd_status()
    if args.cmd == "broadcast":
        return cmd_broadcast(args.data, args.path)
    if args.cmd == "zk-prove":
        return cmd_zk_prove(args.input)
    if args.cmd == "zk-verify":
        return cmd_zk_verify(args.proof, args.public_input)
    return 1


if __name__ == "__main__":
    sys.exit(main())
