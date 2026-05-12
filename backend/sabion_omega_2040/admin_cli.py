#!/usr/bin/env python3
# backend/sabion_omega_2040/admin_cli.py — CLI GOD MODE EXCLUSIVO
"""Uso: python -m backend.sabion_omega_2040.admin_cli auth | dashboard | god <command>"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys

BASE_URL = os.getenv("OMEGA_URL", "http://localhost:10000")
TOKEN = os.getenv("ADMIN_TOKEN", "CASTUO_360_GREGORIO_2040_KYBER2048_TRL9")


async def _post(path: str, data: dict):
    import httpx
    async with httpx.AsyncClient(timeout=15.0) as client:
        r = await client.post(f"{BASE_URL}{path}", json=data)
        r.raise_for_status()
        return r.json()


async def _get(path: str, token: str):
    import httpx
    async with httpx.AsyncClient(timeout=10.0) as client:
        r = await client.get(f"{BASE_URL}{path}", headers={"X-Admin-Token": token})
        r.raise_for_status()
        return r.json()


async def cmd_auth(token: str | None = None):
    data = await _post("/omega/auth", {"token": token or TOKEN})
    print(json.dumps(data, indent=2))


async def cmd_dashboard(token: str | None = None):
    data = await _get("/omega/admin_dashboard", token or TOKEN)
    print(json.dumps(data, indent=2))


async def cmd_god(command: str, token: str | None = None):
    import httpx
    async with httpx.AsyncClient(timeout=10.0) as client:
        r = await client.post(
            f"{BASE_URL}/omega/god_mode",
            json={"command": command},
            headers={"X-Admin-Token": token or TOKEN},
        )
        r.raise_for_status()
        print(json.dumps(r.json(), indent=2))


def main():
    p = argparse.ArgumentParser(description="SABION_OMEGA_2040 Admin CLI")
    p.add_argument("command", choices=["auth", "dashboard", "god"], help="auth | dashboard | god")
    p.add_argument("extra", nargs="?", help="Para god: OMEGA_KILL_ALL | OMEGA_RESTART_NODES | ...")
    p.add_argument("--token", default=TOKEN, help="ADMIN_TOKEN")
    args = p.parse_args()

    if args.command == "auth":
        asyncio.run(cmd_auth(args.token))
    elif args.command == "dashboard":
        asyncio.run(cmd_dashboard(args.token))
    elif args.command == "god":
        cmd = args.extra or "OMEGA_RESTART_NODES"
        asyncio.run(cmd_god(cmd, args.token))


if __name__ == "__main__":
    main()
