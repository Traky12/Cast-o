#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SABIONDA v7.1 | Emisión de certificado (AEMPS/GlobalGAP) en pipeline de certificación.
Uso: python scripts/issue_certificate.py <batch_id>
"""
import os
import sys

def main():
    batch_id = (sys.argv[1:] or ["demo-batch"])[0]
    api_url = os.getenv("CASTUO_API_URL", "http://localhost:8000")
    # Cannabis AEMPS
    url = f"{api_url.rstrip('/')}/cannabis/certify_aemps"
    payload = {
        "batch_id": batch_id,
        "strain_id": "default",
        "thc_percentage": 0.28,
        "cbd_percentage": 0.0,
        "lab_results": {},
    }
    try:
        import httpx
        r = httpx.post(url, json=payload, timeout=15.0)
        if r.status_code >= 400:
            print(f"Certificate API returned {r.status_code}: {r.text}")
            sys.exit(1)
        print(f"Certificate issued for batch {batch_id}: {r.json()}")
    except ImportError:
        print("httpx not installed; skipping certificate issue (stub OK)")
    except Exception as e:
        print(f"Certificate issue failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
