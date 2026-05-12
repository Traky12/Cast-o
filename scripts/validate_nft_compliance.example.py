"""Validar que metadatos NFT mencionan marcos EU declarados (referencial)."""


def validate_compliance(nft_metadata: dict) -> bool:
    for item in nft_metadata.get("attributes", []):
        if item.get("trait_type") == "Compliance (declarado)":
            s = str(item.get("value", ""))
            return all(x in s for x in ("GDPR", "eIDAS2", "NIS2", "EU AI Act"))
    return False


if __name__ == "__main__":
    import json
    from pathlib import Path

    p = Path(__file__).parent / "castuo_nft_metadata.example.json"
    meta = json.loads(p.read_text(encoding="utf-8"))
    print("COMPLIANCE OK" if validate_compliance(meta) else "COMPLIANCE FAIL")
