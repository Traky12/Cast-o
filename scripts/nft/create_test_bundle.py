#!/usr/bin/env python3
"""
Crea directorio castuo_test/ y CASTUO_GOLD_V1_TEST.zip para pruebas de NFT en testnet.
Ejecutar desde la raíz del repo. Luego: sha256 CASTUO_GOLD_V1_TEST.zip y poner hash en nft_metadata_test.example.json.
"""
from __future__ import annotations

import hashlib
import zipfile
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[2]
TEST_DIR = ROOT / "castuo_test"
ZIP_NAME = "CASTUO_GOLD_V1_TEST.zip"


def main() -> None:
    TEST_DIR.mkdir(exist_ok=True)
    (TEST_DIR / "docs" / "security").mkdir(parents=True, exist_ok=True)
    (TEST_DIR / "scripts").mkdir(exist_ok=True)

    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    (TEST_DIR / "README.md").write_text(
        f"# CASTUO_GOLD_V1 (TEST)\n\nPrueba para NFT en GaiaChain Testnet.\n- **Fecha**: {ts}\n- **Estado**: PRUEBA\n",
        encoding="utf-8",
    )
    (TEST_DIR / "SABIONDA_FINAL_RELEASE_TEST.log").write_text(
        "# KERNEL LOCK (simulado)\nSHA256 0x1234... TEST\n# BLACKOUT\nSHA256 0x5678... TEST\n",
        encoding="utf-8",
    )
    (TEST_DIR / "SABIONDA-AUTH-V1_TEST.cert").write_text(
        "ID: EXT-CAS-2026-001-TEST\nESTADO: LOCKDOWN (PRUEBA)\nMATRIZ EU: GDPR/eIDAS2/NIS2 (simulado)\n",
        encoding="utf-8",
    )
    (TEST_DIR / "docs" / "security" / "BLACKOUT-RECOVERY-SOP_TEST.md").write_text(
        "# BLACKOUT-RECOVERY-SOP (TEST)\nProcedimiento de recuperación simulado.\n",
        encoding="utf-8",
    )
    (TEST_DIR / "scripts" / "sabionda_test_seal.py").write_text(
        '#!/usr/bin/env python3\n# Script de prueba (testnet)\nprint("Log generado (PRUEBA)")\n',
        encoding="utf-8",
    )

    zip_path = ROOT / ZIP_NAME
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in TEST_DIR.rglob("*"):
            if f.is_file():
                zf.write(f, f.relative_to(TEST_DIR.parent))

    h = hashlib.sha256(zip_path.read_bytes()).hexdigest()
    print(f"Creado {zip_path}")
    print(f"SHA-256 del ZIP: {h}")
    print("Pon este hash en scripts/nft/nft_metadata_test.example.json → trait_type 'Zip Hash' y sube el JSON a IPFS.")


if __name__ == "__main__":
    main()
