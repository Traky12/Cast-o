"""Tests for Encryption Module."""
import pytest
from cryptography.fernet import Fernet
from castuo_graph.security.encryption import encrypt_data, decrypt_data, generate_key


class TestEncryption:
    """Test suite for encryption functionality."""

    def test_generate_key(self):
        """Test that key generation produces valid Fernet key."""
        key = generate_key()
        assert isinstance(key, bytes)
        assert len(key) > 0
        # Verify it's a valid Fernet key
        cipher = Fernet(key)
        assert cipher is not None

    def test_encrypt_data_returns_bytes(self):
        """Test that encryption returns bytes."""
        key = generate_key()
        data = "datos_sensibles"
        encrypted = encrypt_data(data, key)
        
        assert isinstance(encrypted, bytes)
        assert len(encrypted) > 0

    def test_encrypt_data_produces_ciphertext(self):
        """Test that encrypted data is different from plaintext."""
        key = generate_key()
        plaintext = "información_agrícola"
        encrypted = encrypt_data(plaintext, key)
        
        assert encrypted != plaintext.encode()

    def test_decrypt_data_recovers_original(self):
        """Test that decryption recovers original plaintext."""
        key = generate_key()
        original = "datos_agrícolas_confidenciales"
        encrypted = encrypt_data(original, key)
        decrypted = decrypt_data(encrypted, key)
        
        assert decrypted == original

    def test_decrypt_with_wrong_key_fails(self):
        """Test that decryption with wrong key fails."""
        key1 = generate_key()
        key2 = generate_key()
        
        data = "secreto"
        encrypted = encrypt_data(data, key1)
        
        with pytest.raises(Exception):  # Fernet raises InvalidToken
            decrypt_data(encrypted, key2)

    def test_encrypt_empty_string(self):
        """Test encryption of empty string."""
        key = generate_key()
        encrypted = encrypt_data("", key)
        decrypted = decrypt_data(encrypted, key)
        
        assert decrypted == ""

    def test_encrypt_long_data(self):
        """Test encryption of large data."""
        key = generate_key()
        long_data = "x" * 10000  # 10KB of data
        encrypted = encrypt_data(long_data, key)
        decrypted = decrypt_data(encrypted, key)
        
        assert decrypted == long_data

    def test_encrypt_special_characters(self):
        """Test encryption of special characters."""
        key = generate_key()
        data = "温度: 25°C, 湿度: 70%, pH: 6.5 🌾"
        encrypted = encrypt_data(data, key)
        decrypted = decrypt_data(encrypted, key)
        
        assert decrypted == data

    def test_encrypt_json_data(self):
        """Test encryption of JSON structures."""
        import json
        key = generate_key()
        
        data_dict = {
            "temperature": 25,
            "humidity": 70,
            "soil_ph": 6.5,
            "crop": "tomate"
        }
        data_json = json.dumps(data_dict)
        
        encrypted = encrypt_data(data_json, key)
        decrypted = decrypt_data(encrypted, key)
        recovered_dict = json.loads(decrypted)
        
        assert recovered_dict == data_dict

    def test_encrypt_idempotence_produces_different_ciphertexts(self):
        """Test that encrypting same data twice produces different ciphertexts."""
        key = generate_key()
        data = "mismo_datos"
        
        # Fernet adds timestamp, so ciphertexts should differ
        encrypted1 = encrypt_data(data, key)
        encrypted2 = encrypt_data(data, key)
        
        # Ciphertexts are different (due to timestamp)
        assert encrypted1 != encrypted2
        # But both decrypt to same plaintext
        assert decrypt_data(encrypted1, key) == decrypt_data(encrypted2, key)

    def test_key_reusability(self):
        """Test that same key can encrypt/decrypt multiple datasets."""
        key = generate_key()
        
        datasets = [
            "sensor_temp_25C",
            "sensor_humidity_70",
            "sensor_ph_6.5",
            "crop_tomato"
        ]
        
        encrypted_data = [encrypt_data(data, key) for data in datasets]
        decrypted_data = [decrypt_data(enc, key) for enc in encrypted_data]
        
        assert decrypted_data == datasets

    def test_encrypt_binary_encoded_data(self):
        """Test encryption of already binary-encoded data."""
        key = generate_key()
        binary_data = b"binary_content"
        
        # Convert binary to string, encrypt, decrypt, convert back
        data_str = binary_data.decode('utf-8')
        encrypted = encrypt_data(data_str, key)
        decrypted = decrypt_data(encrypted, key)
        
        assert decrypted.encode('utf-8') == binary_data
