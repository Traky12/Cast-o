# tests/stress_gaiachain.py — estrés de GaiaChain (compatible con cliente stub en memoria)
import random
import sys
import time
from pathlib import Path

# Raíz del proyecto para importar blockchain
_root = Path(__file__).resolve().parents[1]
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from blockchain.gaia_chain import GaiaChainClient


def stress_test_gaiachain():
    gaia = GaiaChainClient(rpc_url="http://localhost:8545")

    for i in range(1, 101):
        mission_id = f"STRESS-TEST-{i:03d}"
        try:
            tx_hash = gaia.log_iot_data(
                {
                    "tray_id": f"CASTUO-TRAY-{i % 20:03d}",
                    "timestamp": "2023-11-01T12:00:00",
                    "sensors": {
                        "temperature": 20 + random.uniform(0, 5),
                        "humidity": 50 + random.uniform(0, 20),
                        "co2": 300 + random.uniform(0, 100),
                    },
                    "metadata": {"location": f"Test Location {i}"},
                }
            )
            print(f"OK Transacción {i}: {tx_hash}")
        except Exception as e:
            print(f"Error en transacción {i}: {e}")
        time.sleep(0.2)


if __name__ == "__main__":
    stress_test_gaiachain()
