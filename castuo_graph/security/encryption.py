"""Encryption module for sensitive data protection."""
import os
import logging
from cryptography.fernet import Fernet
from typing import Union

logger = logging.getLogger(__name__)


def generate_key() -> bytes:
    """
    Generate a new encryption key.

    Returns:
        A new Fernet encryption key as bytes
    """
    return Fernet.generate_key()


def encrypt_data(data: str, key: bytes) -> bytes:
    """
    Encrypt plaintext data using Fernet (AES-128).

    Args:
        data: Plaintext string to encrypt
        key: Encryption key (from generate_key())

    Returns:
        Encrypted ciphertext as bytes

    Raises:
        InvalidToken: If key is invalid
        TypeError: If data is not a string
    """
    if not isinstance(key, bytes):
        raise TypeError("Key must be bytes")
    
    cipher = Fernet(key)
    encrypted = cipher.encrypt(data.encode('utf-8'))
    
    logger.debug(f"Data encrypted successfully (plaintext length: {len(data)})")
    return encrypted


def decrypt_data(encrypted_data: bytes, key: bytes) -> str:
    """
    Decrypt Fernet-encrypted data.

    Args:
        encrypted_data: Ciphertext bytes to decrypt
        key: Encryption key used to encrypt

    Returns:
        Decrypted plaintext string

    Raises:
        InvalidToken: If key is wrong or data is corrupted
        TypeError: If inputs are wrong type
    """
    if not isinstance(encrypted_data, bytes):
        raise TypeError("Encrypted data must be bytes")
    
    if not isinstance(key, bytes):
        raise TypeError("Key must be bytes")
    
    cipher = Fernet(key)
    decrypted = cipher.decrypt(encrypted_data)
    
    logger.debug(f"Data decrypted successfully")
    return decrypted.decode('utf-8')


def load_key_from_env(env_var: str = "ENCRYPTION_KEY") -> bytes:
    """
    Load encryption key from environment variable.

    Args:
        env_var: Name of environment variable containing base64-encoded key

    Returns:
        Encryption key as bytes

    Raises:
        ValueError: If environment variable is not set
    """
    key_str = os.getenv(env_var)
    
    if not key_str:
        raise ValueError(
            f"Environment variable {env_var} not set. "
            f"Set it with: export {env_var}=$(python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())')"
        )
    
    try:
        key = key_str.encode()
        # Validate it's a proper Fernet key
        Fernet(key)
        return key
    except Exception as e:
        raise ValueError(f"Invalid encryption key in {env_var}: {e}")


def load_key_from_file(filepath: str) -> bytes:
    """
    Load encryption key from file.

    Args:
        filepath: Path to file containing base64-encoded key

    Returns:
        Encryption key as bytes

    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If file contents are invalid
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Key file not found: {filepath}")
    
    try:
        with open(filepath, 'rb') as f:
            key = f.read().strip()
        
        # Validate it's a proper Fernet key
        Fernet(key)
        return key
    except Exception as e:
        raise ValueError(f"Invalid key file {filepath}: {e}")


def save_key_to_file(key: bytes, filepath: str) -> None:
    """
    Save encryption key to file (be careful with file permissions!).

    Args:
        key: Encryption key to save
        filepath: Where to save the key

    Raises:
        IOError: If unable to write file
    """
    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(filepath) or '.', exist_ok=True)
        
        with open(filepath, 'wb') as f:
            f.write(key)
        
        # Restrict permissions to user only
        os.chmod(filepath, 0o600)
        logger.warning(f"Key saved to {filepath} - KEEP THIS FILE SECURE!")
    except IOError as e:
        raise IOError(f"Unable to save key to {filepath}: {e}")


class EncryptionManager:
    """Manager for encryption operations with key lifecycle."""

    def __init__(self, key: Union[bytes, str, None] = None):
        """
        Initialize encryption manager.

        Args:
            key: Encryption key (bytes) or env var name (str), or None to auto-detect
        """
        self.key = None
        
        if isinstance(key, bytes):
            self.key = key
        elif isinstance(key, str):
            # Try to load from environment
            try:
                self.key = load_key_from_env(key)
            except ValueError:
                # Try to load from file
                try:
                    self.key = load_key_from_file(key)
                except FileNotFoundError:
                    raise ValueError(f"Cannot load key from env var or file: {key}")
        elif key is None:
            # Try to load from default environment variable
            try:
                self.key = load_key_from_env("ENCRYPTION_KEY")
            except ValueError:
                logger.warning(
                    "No encryption key found. "
                    "Generate with: python -c 'from castuo_graph.security.encryption import generate_key; "
                    "print(generate_key().decode())'"
                )

    def encrypt(self, data: str) -> bytes:
        """Encrypt data using manager's key."""
        if self.key is None:
            raise RuntimeError("No encryption key configured")
        return encrypt_data(data, self.key)

    def decrypt(self, encrypted_data: bytes) -> str:
        """Decrypt data using manager's key."""
        if self.key is None:
            raise RuntimeError("No encryption key configured")
        return decrypt_data(encrypted_data, self.key)
