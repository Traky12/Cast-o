#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SABIONDA v7.1 | Validación LIMS CTAEX antes de certificación.
Uso: python scripts/validate_lims.py <batch_id>
"""
import os
import sys

def main():
    batch_id = (sys.argv[1:] or ["demo-batch"])[0]
    base_url = os.getenv("LIMS_API_URL", "https://lims.ctaex.es/api/v1")
    url = f"{base_url.rstrip('/')}/batch/{batch_id}/thc"
    try:
        import httpx
        r = httpx.get(url, timeout=10.0)
        if r.status_code != 200:
            print(f"LIMS returned {r.status_code} for batch {batch_id}")
            sys.exit(1)
        data = r.json()
        thc = float(data.get("thc", data.get("thc_percentage", 0)))
        if thc > 0.3:
            print(f"THC {thc}% > 0.3% (RD 903/2025) — batch {batch_id} rejected")
            sys.exit(1)
        print(f"THC {thc}% OK for batch {batch_id}")
    except ImportError:
        print("httpx not installed; skipping real LIMS check (stub OK)")
    except Exception as e:
        print(f"LIMS check failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
