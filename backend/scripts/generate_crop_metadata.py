#!/usr/bin/env python3
"""
Genera metadatos ERC-721 para un NFT de cultivo y los sube a IPFS.
Uso: python3 scripts/generate_crop_metadata.py <crop_type> <farm_id> <location> <co2_saved> [image_path]
Ejemplo: python3 scripts/generate_crop_metadata.py lettuce extremadura-farm-001 "39.4769°N, 6.3706°W" 12 images/lettuce.jpg
Variables: IPFS_GATEWAY (opcional, ej. /dns/ipfs.infura.io/tcp/5001/https)
"""
import json
import os
import sys
from datetime import datetime


def connect_ipfs():
    try:
        import ipfshttpclient
    except ImportError:
        return None
    api = os.getenv("IPFS_GATEWAY", "/dns/ipfs.infura.io/tcp/5001/https")
    try:
        return ipfshttpclient.connect(api)
    except Exception:
        return None


def upload_to_ipfs_str(client, data: str) -> str:
    if client is None:
        return "QmPlaceholderNoIPFS"
    return client.add_str(data)


def upload_file_to_ipfs(client, path: str) -> str:
    if client is None or not os.path.isfile(path):
        return "QmPlaceholderImage"
    with open(path, "rb") as f:
        data = f.read()
    result = client.add_bytes(data)
    if isinstance(result, list) and result:
        return result[0].get("Hash", result[0]) if isinstance(result[0], dict) else str(result[0])
    return str(result)


def generate_metadata(
    crop_type: str,
    farm_id: str,
    location: str,
    co2_saved: int,
    image_path: str | None = None,
) -> str:
    client = connect_ipfs()
    image_hash = upload_file_to_ipfs(client, image_path) if image_path else "QmPlaceholderImage"
    image_uri = f"ipfs://{image_hash}"

    metadata = {
        "name": f"{crop_type.capitalize()} from {farm_id}",
        "description": f"A {crop_type} cultivated with zero waste in {location}. CO₂ saved: {co2_saved} kg.",
        "image": image_uri,
        "attributes": [
            {"trait_type": "Crop Type", "value": crop_type},
            {"trait_type": "Farm ID", "value": farm_id},
            {"trait_type": "Location", "value": location},
            {"trait_type": "CO₂ Saved (kg)", "value": co2_saved},
            {"trait_type": "Harvest Date", "value": datetime.utcnow().isoformat() + "Z"},
        ],
    }

    metadata_json = json.dumps(metadata, ensure_ascii=False)
    metadata_hash = upload_to_ipfs_str(client, metadata_json)
    return metadata_hash


def main():
    if len(sys.argv) < 5:
        print(
            "Uso: generate_crop_metadata.py <crop_type> <farm_id> <location> <co2_saved> [image_path]",
            file=sys.stderr,
        )
        sys.exit(1)
    crop_type = sys.argv[1]
    farm_id = sys.argv[2]
    location = sys.argv[3]
    co2_saved = int(sys.argv[4])
    image_path = sys.argv[5] if len(sys.argv) > 5 else None

    metadata_hash = generate_metadata(crop_type, farm_id, location, co2_saved, image_path)
    print(metadata_hash)
    return metadata_hash


if __name__ == "__main__":
    main()
