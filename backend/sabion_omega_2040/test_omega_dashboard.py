#!/usr/bin/env python3
# test_omega_dashboard.py - SABION_OMEGA_2040 GOD MODE TESTER
# Uso: python backend/sabion_omega_2040/test_omega_dashboard.py

import json
import os
import sys

try:
    import requests
except ImportError:
    print("Instala: pip install requests")
    sys.exit(1)

ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", "CASTUO_360_GREGORIO_2040_KYBER2048_TRL9")
BASE_URL = os.getenv("OMEGA_URL", "http://localhost:10000")

def main():
    print("🔐 SABION_OMEGA_2040 - GREGORIO GOD MODE TEST")
    print("=" * 60)

    # 1. AUTH
    print("1. AUTH →", end=" ")
    try:
        auth_resp = requests.post(
            f"{BASE_URL}/omega/auth",
            json={"token": ADMIN_TOKEN},
            headers={"Content-Type": "application/json"},
            timeout=5,
        )
        auth_resp.raise_for_status()
        msg = auth_resp.json().get("message", "OK")
        print(msg)
    except requests.RequestException as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

    # 2. DASHBOARD
    print("2. DASHBOARD →", end=" ")
    try:
        dash_resp = requests.get(
            f"{BASE_URL}/omega/admin_dashboard",
            headers={"X-Admin-Token": ADMIN_TOKEN},
            timeout=5,
        )
        dash_resp.raise_for_status()
        dashboard = dash_resp.json()
    except requests.RequestException as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

    print(f"✅ GREGORIO OK | €{dashboard.get('total_revenue_2040', '?')} | {dashboard.get('nodes_global', '?')}")
    subs = dashboard.get("subsidiaries", {})
    print("   Subsidiaries:", list(subs.values()) if isinstance(subs, dict) else subs)
    print(f"   GOD MODE: {dashboard.get('god_mode', '?')}")

    # 3. GOD MODE TEST
    print("3. GOD MODE →", end=" ")
    try:
        god_resp = requests.post(
            f"{BASE_URL}/omega/god_mode",
            json={"command": "OMEGA_RESTART_NODES"},
            headers={
                "Content-Type": "application/json",
                "X-Admin-Token": ADMIN_TOKEN,
            },
            timeout=5,
        )
        god_resp.raise_for_status()
        god_data = god_resp.json()
        block = god_data.get("block_hash", "")[:20] + "..." if god_data.get("block_hash") else "N/A"
        print(f"{god_data.get('message', 'OK')} | Block: {block}")
    except requests.RequestException as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

    print("\n🎉 SABION_OMEGA_2040 = 100% CONTROL GREGORIO ✓")


if __name__ == "__main__":
    main()
