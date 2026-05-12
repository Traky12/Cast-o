#!/usr/bin/env python3
"""
Monitorea el crecimiento de una planta y actualiza el DynamicCropNFT en cada etapa.
En producción conectar con datos reales de sensores IoT (pH, EC, imagen).
Uso: python3 scripts/iot_growth_monitor.py <token_id> [interval_seconds] [steps]
Ejemplo: python3 scripts/iot_growth_monitor.py 1 86400 10  # 10% cada día, 10 pasos
Variables: GAIA_CHAIN_RPC, DYNAMIC_NFT_ADDRESS, PRIVATE_KEY
"""
import os
import subprocess
import sys
import time

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
UPDATE_SCRIPT = os.path.join(_SCRIPT_DIR, "update_dynamic_nft.py")


def monitor_growth(token_id: int, interval_seconds: int = 86400, steps: int = 10):
    growth_stage = 0
    step = max(1, 100 // steps)
    while growth_stage < 100:
        growth_stage = min(growth_stage + step, 100)
        image_path = f"images/lettuce_{growth_stage}percent.jpg"
        try:
            out = subprocess.run(
                [
                    sys.executable,
                    UPDATE_SCRIPT,
                    str(token_id),
                    str(growth_stage),
                    image_path,
                ],
                capture_output=True,
                text=True,
                timeout=120,
                cwd=os.path.dirname(_SCRIPT_DIR),
            )
            if out.returncode == 0:
                tx_hash = out.stdout.strip()
                print(f"Updated to {growth_stage}%: {tx_hash}")
            else:
                print(f"Error at {growth_stage}%: {out.stderr or out.stdout}", file=sys.stderr)
        except subprocess.TimeoutExpired:
            print(f"Timeout at {growth_stage}%", file=sys.stderr)
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)

        if growth_stage >= 100:
            break
        time.sleep(interval_seconds)


def main():
    if len(sys.argv) < 2:
        print(
            "Uso: iot_growth_monitor.py <token_id> [interval_seconds] [steps]",
            file=sys.stderr,
        )
        sys.exit(1)
    token_id = int(sys.argv[1])
    interval_seconds = int(sys.argv[2]) if len(sys.argv) > 2 else 86400
    steps = int(sys.argv[3]) if len(sys.argv) > 3 else 10
    monitor_growth(token_id, interval_seconds, steps)


if __name__ == "__main__":
    main()
