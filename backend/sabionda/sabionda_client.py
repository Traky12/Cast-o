#!/usr/bin/env python3
# backend/sabionda/sabionda_client.py — CLI para nodos subordinados y pruebas SABIONDA v4.0
"""Uso: python -m backend.sabionda.sabionda_client status | orchestrate '{"type":"Certificación","progress":92}'"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
import os


BASE_URL = os.getenv("SABIONDA_URL", "http://localhost:9000")


async def cmd_status():
    import httpx
    async with httpx.AsyncClient(timeout=10.0) as client:
        r = await client.get(f"{BASE_URL}/sabionda/status")
        r.raise_for_status()
        print(json.dumps(r.json(), indent=2))


async def cmd_orchestrate(payload_str: str):
    import httpx
    try:
        payload = json.loads(payload_str)
    except json.JSONDecodeError:
        payload = {"type": payload_str}
    async with httpx.AsyncClient(timeout=15.0) as client:
        r = await client.post(f"{BASE_URL}/sabionda/orchestrate", json=payload)
        r.raise_for_status()
        print(json.dumps(r.json(), indent=2))


async def cmd_agent(agent_id: str, payload_str: str):
    import httpx
    payload = json.loads(payload_str) if payload_str else {}
    async with httpx.AsyncClient(timeout=10.0) as client:
        r = await client.post(f"{BASE_URL}/sabionda/agents/{agent_id}", json=payload)
        r.raise_for_status()
        print(json.dumps(r.json(), indent=2))


def main():
    p = argparse.ArgumentParser(description="SABIONDA v4.0 CLI")
    p.add_argument("command", choices=["status", "orchestrate", "agent"], help="status | orchestrate | agent")
    p.add_argument("payload", nargs="?", default="{}", help='JSON payload, e.g. {"type":"Certificación","progress":92}')
    p.add_argument("--agent-id", default="auditoria", help="For command=agent")
    args = p.parse_args()

    if args.command == "status":
        asyncio.run(cmd_status())
    elif args.command == "orchestrate":
        asyncio.run(cmd_orchestrate(args.payload))
    elif args.command == "agent":
        asyncio.run(cmd_agent(args.agent_id, args.payload))


if __name__ == "__main__":
    main()
