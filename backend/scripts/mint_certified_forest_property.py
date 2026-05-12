#!/usr/bin/env python3
"""
Mint de propiedad forestal con certificaciones (PEFC/FSC/Red Natura 2000).
Flujo: validación opcional SIGPAC → metadatos → IPFS (si disponible) → GaiaChain.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime

try:
    from web3 import Web3
except ImportError:
    print("Instalar: pip install web3", file=sys.stderr)
    sys.exit(1)

GAIA_CHAIN_RPC = os.getenv("GAIA_CHAIN_RPC", "https://gaiachain.castuo-system.com")
FOREST_OWNERSHIP_TOKEN_ADDRESS = os.getenv("FOREST_OWNERSHIP_TOKEN_ADDRESS", "")
PRIVATE_KEY = os.getenv("PRIVATE_KEY") or os.getenv("JUNTA_PRIVATE_KEY")
SIGPAC_API_KEY = os.getenv("SIGPAC_API_KEY")

ABI = [
    {
        "inputs": [
            {"name": "to", "type": "address"},
            {"name": "parcelaId", "type": "string"},
            {"name": "coordinates", "type": "string"},
            {"name": "area", "type": "uint256"},
            {"name": "treeSpecies", "type": "string"},
            {"name": "carbonSequestered", "type": "uint256"},
            {"name": "isProtected", "type": "bool"},
            {"name": "ipfsHash", "type": "string"},
            {"name": "certifications", "type": "string[]"},
        ],
        "name": "mintProperty",
        "outputs": [{"name": "", "type": "uint256"}],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "inputs": [{"name": "tokenId", "type": "uint256"}],
        "name": "calculateSubsidies",
        "outputs": [{"name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    },
]


def validate_with_sigpac(parcela_id: str) -> dict:
    """Valida parcela con SIGPAC si API key está configurada. Si no, devuelve datos por defecto."""
    if not SIGPAC_API_KEY:
        return {
            "certifications": [],
            "protected": False,
            "area": 0,
        }
    try:
        import requests
        r = requests.get(
            f"https://sigpac.mapa.gob.es/sigpac/services/api/parcela/{parcela_id}",
            headers={"Authorization": f"Bearer {SIGPAC_API_KEY}"},
            timeout=10,
        )
        if r.status_code != 200:
            return {"certifications": [], "protected": False, "area": 0}
        data = r.json()
        return {
            "certifications": data.get("certifications", []),
            "protected": data.get("protected_area", False),
            "area": data.get("area", 0),
        }
    except Exception:
        return {"certifications": [], "protected": False, "area": 0}


def generate_metadata(
    parcela_id: str,
    owner_address: str,
    sigpac_data: dict,
    carbon_co2: int,
    species_str: str,
    coordinates: str,
) -> dict:
    """Genera metadatos en formato OpenSea + certificaciones."""
    certs = sigpac_data.get("certifications", [])
    metadata = {
        "name": f"Parcela Forestal {parcela_id}",
        "description": f"Propiedad forestal en Extremadura con certificaciones {', '.join(certs) or 'N/A'}.",
        "image": "ipfs://QmXoypizjW3WknFiJnKLwHCnL72vedxjQkDDP1mXWo6uco/parcela.jpg",
        "attributes": [
            {"trait_type": "Parcela ID", "value": parcela_id},
            {"trait_type": "Área", "value": f"{sigpac_data.get('area', 0)} m²"},
            {"trait_type": "Coordenadas GPS", "value": coordinates},
            {"trait_type": "Propietario", "value": owner_address},
            {"trait_type": "Certificaciones", "value": certs},
            {"trait_type": "Protegida", "value": sigpac_data.get("protected", False)},
            {"trait_type": "CO₂ Secuestrado", "value": f"{carbon_co2} kg/año"},
            {"trait_type": "Especies", "value": species_str},
            {"trait_type": "Fecha de Tokenización", "value": datetime.utcnow().isoformat() + "Z"},
        ],
        "certifications": [
            {
                "name": c,
                "id": f"ES-{c}-{parcela_id[-5:]}",
                "standard": "Gestión Forestal Sostenible" if c in ("PEFC", "FSC") else "Protección de Biodiversidad",
                "expiry": "2028-12-31",
                "verified_by": "SIGPAC",
            }
            for c in certs
        ],
    }
    return metadata


def upload_to_ipfs(data: dict) -> str | None:
    """Sube metadatos a IPFS si ipfshttpclient está disponible."""
    try:
        from ipfshttpclient import connect
        client = connect("/dns/ipfs.infura.io/tcp/5001/https")
        result = client.add_json(data)
        if isinstance(result, str):
            return result
        if isinstance(result, (list, tuple)) and result:
            return result[0].get("Hash") or result[0].get("hash") if isinstance(result[0], dict) else str(result[0])
        return None
    except Exception:
        return None


def calculate_subsidies_offchain(certifications: list, area_m2: int) -> float:
    """Calcula subvenciones estimadas (€/año) por certificaciones y área."""
    area_ha = area_m2 / 10000.0
    total = 200.0 * area_ha
    if any(c in ("PEFC", "FSC") for c in certifications):
        total += 150.0 * area_ha
    if "Red Natura 2000" in certifications:
        total += 300.0 * area_ha
    return total


def mint_certified_property(
    owner_address: str,
    parcela_id: str,
    coordinates: str = "39.4769°N, 6.3706°W",
    area_m2: int | None = None,
    tree_species: str = "Quercus ilex, Pinus pinea",
    carbon_sequestered: int | None = None,
    certifications: list[str] | None = None,
    use_sigpac: bool = True,
    upload_metadata_ipfs: bool = False,
) -> dict:
    """Proceso completo: opcional SIGPAC → metadatos → IPFS (opcional) → mint en GaiaChain."""
    if not PRIVATE_KEY or not FOREST_OWNERSHIP_TOKEN_ADDRESS:
        raise ValueError("FOREST_OWNERSHIP_TOKEN_ADDRESS y PRIVATE_KEY son obligatorios")

    sigpac_data = validate_with_sigpac(parcela_id) if use_sigpac else {"certifications": [], "protected": False, "area": 0}
    certs = certifications if certifications is not None else sigpac_data.get("certifications", [])
    area = area_m2 if area_m2 is not None and area_m2 > 0 else sigpac_data.get("area") or 10000
    carbon = carbon_sequestered if carbon_sequestered is not None else int(area * 0.5)
    is_protected = sigpac_data.get("protected", False)

    metadata = generate_metadata(parcela_id, owner_address, sigpac_data, carbon, tree_species, coordinates)
    ipfs_hash = upload_to_ipfs(metadata) if upload_metadata_ipfs else "QmXoypizjW3WknFiJnKLwHCnL72vedxjQkDDP1mXWo6uco"

    w3 = Web3(Web3.HTTPProvider(GAIA_CHAIN_RPC))
    account = w3.eth.account.from_key(PRIVATE_KEY.replace("0x", "").strip())
    contract = w3.eth.contract(
        address=Web3.to_checksum_address(FOREST_OWNERSHIP_TOKEN_ADDRESS),
        abi=ABI,
    )
    tx = contract.functions.mintProperty(
        Web3.to_checksum_address(owner_address),
        parcela_id,
        coordinates,
        area,
        tree_species,
        carbon,
        is_protected,
        ipfs_hash,
        certs,
    ).build_transaction({
        "from": account.address,
        "nonce": w3.eth.get_transaction_count(account.address),
        "gas": 600000,
        "gasPrice": w3.to_wei("50", "gwei"),
    })
    signed = w3.eth.account.sign_transaction(tx, PRIVATE_KEY)
    tx_hash_bytes = w3.eth.send_raw_transaction(signed.raw_transaction)
    tx_hash = tx_hash_bytes.hex()
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash_bytes)
    token_id = 0
    if receipt.get("logs"):
        topic = Web3.keccak(text="PropertyMinted(uint256,address,string)")
        for log in receipt["logs"]:
            if log.get("topics") and log["topics"][0] == topic:
                token_id = int(log["topics"][1].hex(), 16)
                break

    subsidies_eur = calculate_subsidies_offchain(certs, area)
    return {
        "tx_hash": tx_hash,
        "token_id": token_id,
        "ipfs_hash": ipfs_hash,
        "subsidies_eur_per_year": subsidies_eur,
    }


def main():
    parser = argparse.ArgumentParser(description="Mint de propiedad forestal certificada")
    parser.add_argument("owner_address", help="Dirección del propietario (0x...)")
    parser.add_argument("parcela_id", help="ID catastral (ej: XT-12345-001)")
    parser.add_argument("--coordinates", default="39.4769°N, 6.3706°W", help="Coordenadas GPS")
    parser.add_argument("--area", type=int, default=0, help="Área m² (0 = usar SIGPAC o 10000)")
    parser.add_argument("--species", default="Quercus ilex, Pinus pinea", help="Especies (coma)")
    parser.add_argument("--carbon", type=int, default=0, help="kg CO₂/año (0 = estimar)")
    parser.add_argument("--certifications", "-c", nargs="*", default=[], help="Ej: PEFC FSC 'Red Natura 2000'")
    parser.add_argument("--no-sigpac", action="store_true", help="No llamar a SIGPAC")
    parser.add_argument("--upload-ipfs", action="store_true", help="Subir metadatos a IPFS")
    args = parser.parse_args()

    try:
        result = mint_certified_property(
            args.owner_address,
            args.parcela_id,
            coordinates=args.coordinates,
            area_m2=args.area or None,
            tree_species=args.species,
            carbon_sequestered=args.carbon or None,
            certifications=args.certifications or None,
            use_sigpac=not args.no_sigpac,
            upload_metadata_ipfs=args.upload_ipfs,
        )
        print(json.dumps(result, indent=2))
        print(f"Explorer: https://explorer.gaiachain.castuo-system.com/tx/{result['tx_hash']}")
        print(f"Subvenciones estimadas: €{result['subsidies_eur_per_year']:.0f}/año")
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
