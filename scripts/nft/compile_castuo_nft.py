#!/usr/bin/env python3
"""
Genera CASTUO_NFT_ABI.json y CASTUO_NFT_BIN.json compilando contracts/nft/CASTUO_NFT.sol.
Requiere solc en PATH (solc-select o solc estándar). Si no está, imprime cómo compilar a mano.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONTRACT_DIR = ROOT / "contracts" / "nft"
SOL = CONTRACT_DIR / "CASTUO_NFT.sol"
ABI_OUT = CONTRACT_DIR / "CASTUO_NFT_ABI.json"
BIN_OUT = CONTRACT_DIR / "CASTUO_NFT_BIN.json"


def main() -> int:
    if not SOL.is_file():
        print(f"No encontrado: {SOL}", file=sys.stderr)
        return 1
    solc = shutil.which("solc")
    if not solc:
        print("solc no está en PATH. Instala con: pip install py-solc-x && solcx install 0.8.19", file=sys.stderr)
        print("O compila a mano: solc --abi --bin -o contracts/nft/ CASTUO_NFT.sol", file=sys.stderr)
        return 2
    out = subprocess.run(
        [
            solc,
            "--abi",
            "--bin",
            "--base-path", str(CONTRACT_DIR),
            "--include-path", str(CONTRACT_DIR),
            str(SOL),
            "-o", str(CONTRACT_DIR),
        ],
        capture_output=True,
        text=True,
        cwd=str(CONTRACT_DIR),
    )
    if out.returncode != 0:
        print(out.stderr or out.stdout, file=sys.stderr)
        return 3
    abi_files = list(CONTRACT_DIR.glob("CASTUO_NFT*.abi"))
    bin_files = list(CONTRACT_DIR.glob("CASTUO_NFT*.bin"))
    if not abi_files or not bin_files:
        print("solc no generó .abi/.bin; revisa la salida anterior", file=sys.stderr)
        return 4
    abi_file, bin_file = abi_files[0], bin_files[0]
    abi = json.loads(abi_file.read_text(encoding="utf-8"))
    raw_bin = bin_file.read_text(encoding="utf-8").strip()
    if not raw_bin.startswith("0x"):
        raw_bin = "0x" + raw_bin
    BIN_OUT.write_text(json.dumps({"bytecode": raw_bin}, indent=2), encoding="utf-8")
    ABI_OUT.write_text(json.dumps(abi, indent=2), encoding="utf-8")
    print(f"ABI → {ABI_OUT}")
    print(f"BIN → {BIN_OUT}")
    abi_file.unlink(missing_ok=True)
    bin_file.unlink(missing_ok=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
