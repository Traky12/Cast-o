#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SABIONDA v7.1 | Registro de lote en GaiaChain (workflow AEMPS / Cursor).
Uso: python scripts/register_batch.py <batch_id>
"""
import os
import sys

def main():
    batch_id = (sys.argv[1:] or ["demo-batch"])[0]
    api_url = os.getenv("CASTUO_API_URL", "http://localhost:8000")
    url = f"{api_url.rstrip('/')}/blockchain/register_batch"
    payload = {
        "batch_id": batch_id,
        "strain_id": "default",
        "thc_percentage": 0.28,
        "cbd_percentage": 0.0,
        "weight_kg": 0,
        "lab_results": {},
        "account_id": "pipeline",
    }
    try:
        import httpx
        r = httpx.post(url, json=payload, timeout=15.0)
        if r.status_code >= 400:
            print(f"GaiaChain register returned {r.status_code}: {r.text}")
            sys.exit(1)
        print(f"GaiaChain registration OK for batch {batch_id}: {r.json()}")
    except ImportError:
        print("httpx not installed; skipping GaiaChain register (stub OK)")
    except Exception as e:
        print(f"GaiaChain register failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
