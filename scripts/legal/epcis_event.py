#!/usr/bin/env python3
"""
CASTUO-SYSTEM™ | Registro de eventos GS1 EPCIS (trazabilidad europea).
Envía evento a la API EPCIS con txHash, gitCommit, farmId.
Uso: python scripts/legal/epcis_event.py --tx a1b2c3... --git abc123 --farm castu-finca1
"""
import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TEMPLATES = ROOT / "templates" / "legal"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tx", default="a1b2c3d4e5f67890123456789abcdef0", help="TX hash BioCoin")
    ap.add_argument("--git", default="abc123def456", help="Git commit short hash")
    ap.add_argument("--ipfs", default="", help="IPFS hash del documento")
    ap.add_argument("--farm", default="castu-finca1", help="farmId")
    args = ap.parse_args()

    with open(TEMPLATES / "epcis_event.json", encoding="utf-8") as f:
        doc = json.load(f)

    ext = doc["event"]["extension"]
    ext["txHash"] = args.tx
    ext["gitCommit"] = args.git
    ext["farmId"] = args.farm
    if args.ipfs:
        ext["ipfsHash"] = args.ipfs

    url = os.environ.get("EPCIS_API_URL", "https://epcis.castu-system.com/api/events")
    auth = os.environ.get("EPCIS_API_KEY")
    if not auth:
        print("✅ Payload EPCIS preparado (no enviado; definir EPCIS_API_URL y EPCIS_API_KEY):")
        print(json.dumps(doc, indent=2))
        return 0

    try:
        import requests
        r = requests.post(url, json=doc, headers={"Authorization": f"Bearer {auth}"}, timeout=10)
        r.raise_for_status()
        print(f"✅ Evento EPCIS registrado: {r.json().get('eventID', r.text)}")
    except Exception as e:
        print(f"⚠️ Envío EPCIS: {e}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
