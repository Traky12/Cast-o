from __future__ import annotations

import os

import pytest

from backend.digital_twin.holographic_encryption import HolographicEncryption
from backend.security.end_to_end_encryption import EndToEndEncryption


class TestHolographicEncryption:
    """Pruebas para el módulo de cifrado holográfico."""

    @pytest.fixture
    def encryption(self) -> HolographicEncryption:
        os.environ["DT_HOLOGRAPHIC_ENCRYPTION_ENABLED"] = "true"
        try:
            enc = HolographicEncryption()
            yield enc
        finally:
            os.environ.pop("DT_HOLOGRAPHIC_ENCRYPTION_ENABLED", None)

    def test_encryption_disabled_by_default(self) -> None:
        os.environ.pop("DT_HOLOGRAPHIC_ENCRYPTION_ENABLED", None)
        enc = HolographicEncryption()
        assert not enc.is_enabled()
        with pytest.raises(RuntimeError):
            enc.encrypt_with_holography(b"test")

    def test_encryption_enabled_flag(self, encryption: HolographicEncryption) -> None:
        assert encryption.is_enabled()

    def test_encrypt_decrypt_cycle(self, encryption: HolographicEncryption) -> None:
        data = b"Prueba de cifrado holografico resistente a ataques cuanticos"
        context = {"source": "unit_test", "purpose": "security_validation"}

        pkg = encryption.encrypt_with_holography(data, context)
        assert isinstance(pkg, dict)
        assert "encrypted_data" in pkg
        assert "holographic_key" in pkg
        assert "integrity_proof" in pkg
        assert pkg["metadata"]["encryption_scheme"] == "Holographic-PQC-Hybrid-EU"
        assert pkg.get("_stub") is False

        assert encryption.zk_prover.verify_proof(pkg["integrity_proof"])

        decrypted = encryption.decrypt_with_holography(pkg)
        assert decrypted == data

    def test_integrity_proof_failure(self, encryption: HolographicEncryption) -> None:
        data = b"test data"
        pkg = encryption.encrypt_with_holography(data)

        corrupted = dict(pkg["integrity_proof"])
        corrupted_proof = dict(corrupted["proof"])
        corrupted_proof["pi_a"] = "corrupted"
        corrupted["proof"] = corrupted_proof
        pkg["integrity_proof"] = corrupted

        with pytest.raises(ValueError, match="Prueba de integridad ZK invalida|inválida"):
            encryption.decrypt_with_holography(pkg)

    def test_integration_with_end_to_end_encryption(self) -> None:
        os.environ["DT_HOLOGRAPHIC_ENCRYPTION_ENABLED"] = "true"
        try:
            e2e = EndToEndEncryption()
            assert e2e.holographic is not None
            assert e2e.holographic.is_enabled()

            data = b"test integration"
            pkg = e2e.encrypt(data, use_holography=True)
            assert isinstance(pkg, dict)
            decrypted = e2e.decrypt(pkg, use_holography=True)
            assert decrypted == data

            normal_encrypted = e2e.encrypt(data, use_holography=False)
            assert isinstance(normal_encrypted, (bytes, bytearray))
            normal_decrypted = e2e.decrypt(normal_encrypted, use_holography=False)
            assert normal_decrypted == data
        finally:
            os.environ.pop("DT_HOLOGRAPHIC_ENCRYPTION_ENABLED", None)

    def test_holographic_transformation(self, encryption: HolographicEncryption) -> None:
        test_key = os.urandom(64)
        transformed = encryption._apply_holographic_transform(test_key)
        assert isinstance(transformed, (bytes, bytearray))
        assert len(transformed) == len(test_key)

        original = encryption._reverse_holographic_transform(transformed)
        assert isinstance(original, (bytes, bytearray))

    def test_zk_proof_generation(self, encryption: HolographicEncryption) -> None:
        data = b"test"
        enc = b"encrypted_test"
        hk = b"holographic_key_test"
        ctx = {"test": "context"}

        proof = encryption.zk_prover.generate_proof(data, enc, hk, ctx)
        assert proof["proof_type"] == "Groth16-BLAKE3"
        inner = proof["proof"]
        assert "pi_a" in inner and "pi_b" in inner and "pi_c" in inner
        assert encryption.zk_prover.verify_proof(proof)

    def test_hadamard_matrix_shape(self, encryption: HolographicEncryption) -> None:
        assert encryption.hadamard_matrix.shape == (256, 256)

    def test_quantum_noise_variation(self, encryption: HolographicEncryption) -> None:
        key = os.urandom(64)
        t1 = encryption._apply_holographic_transform(key)
        t2 = encryption._apply_holographic_transform(key)
        assert t1 != t2

    def test_metadata_contains_zk_scheme(self, encryption: HolographicEncryption) -> None:
        pkg = encryption.encrypt_with_holography(b"hola", {"source": "test"})
        assert pkg["metadata"]["zk_scheme"] == "Groth16-BLAKE3"

    def test_end_to_end_encrypt_holography_requires_flag(self) -> None:
        os.environ.pop("DT_HOLOGRAPHIC_ENCRYPTION_ENABLED", None)
        e2e = EndToEndEncryption()
        with pytest.raises(RuntimeError):
            e2e.encrypt(b"x", use_holography=True)

    def test_encrypt_for_moltbook_and_verify_compliance(
        self, encryption: HolographicEncryption
    ) -> None:
        """Ciclo cifrado Moltbook con metadatos legales UE y verificación de cumplimiento."""
        data = b"datos_agronomicos_finca_EXT_001"
        moltbook_context = {"finca_id": "EXT-001", "cultivo": "cannabis_medicinal"}

        pkg = encryption.encrypt_for_moltbook(data, moltbook_context)
        assert "encrypted_data" in pkg and "integrity_proof" in pkg
        meta = pkg["metadata"]
        assert meta.get("rgpd_compliance") == "GDPR_Art32_2026"
        assert meta.get("ai_act_compliance") == "EU_AI_Act_2024_Annex_III"
        assert meta.get("data_provenance") == "Extremadura_ES"

        result = encryption.verify_moltbook_compliance(pkg)
        assert result["compliant"] is True
        assert "EU" in result.get("jurisdiction", "")
        assert "GDPR_Art32_2026" in result.get("standards", [])

        decrypted = encryption.decrypt_with_holography(pkg)
        assert decrypted == data

    def test_verify_moltbook_compliance_fails_on_invalid_metadata(
        self, encryption: HolographicEncryption
    ) -> None:
        """verify_moltbook_compliance devuelve compliant=False si faltan metadatos legales."""
        pkg = encryption.encrypt_with_holography(b"x", {"source": "test"})
        # Eliminar metadatos legales para simular paquete no conforme
        del pkg["metadata"]["rgpd_compliance"]
        result = encryption.verify_moltbook_compliance(pkg)
        assert result["compliant"] is False
        assert "reason" in result

