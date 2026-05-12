"""
Firma EIP-191 alineada con Solidity:
keccak256("\\x19Ethereum Signed Message:\\n32" || keccak256(abi.encodePacked(evidence, manifest, tokenId, to, vault, chainId))).
Distinto de firmar texto plano evidence: aquí evidence y manifest son bytes32 on-chain.
"""
from __future__ import annotations

from eth_utils import keccak


def _addr20(addr: str) -> bytes:
    h = addr[2:] if addr.startswith("0x") else addr
    return bytes.fromhex(h.lower())[-20:]


def mint_message_hash(
    evidence_hash_32: bytes,
    manifest_hash_32: bytes,
    token_id: int,
    to_address: str,
    vault_contract_address: str,
    chain_id: int,
) -> bytes:
    """Igual que keccak256(abi.encodePacked(...)) en Solidity."""
    packed = (
        evidence_hash_32
        + manifest_hash_32
        + token_id.to_bytes(32, "big")
        + _addr20(to_address)
        + _addr20(vault_contract_address)
        + chain_id.to_bytes(32, "big")
    )
    inner = keccak(packed)
    eth_msg = b"\x19Ethereum Signed Message:\n32" + inner
    return keccak(eth_msg)


def sign_mint_oracle(
    evidence_hash_hex: str,
    manifest_hash_hex: str,
    token_id: int,
    to_address: str,
    vault_address: str,
    chain_id: int,
    oracle_key_hex: str,
) -> tuple[int, str, str]:
    from eth_account import Account

    ev = bytes.fromhex(evidence_hash_hex.replace("0x", ""))
    mv = bytes.fromhex(manifest_hash_hex.replace("0x", ""))
    if len(ev) != 32 or len(mv) != 32:
        raise ValueError("hashes must be 32 bytes")
    msg_hash = mint_message_hash(ev, mv, token_id, to_address, vault_address, chain_id)
    pk = oracle_key_hex.strip()
    if pk.startswith("0x"):
        pk = pk[2:]
    acct = Account.from_key(pk)
    sig = Account.unsafe_sign_hash(msg_hash, private_key=acct.key)
    return sig.v, hex(sig.r), hex(sig.s)
