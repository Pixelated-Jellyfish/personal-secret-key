"""
Key Derivation Function menggunakan PBKDF2-HMAC-SHA256.
"""

import hashlib
import base64
import os

# Salt tetap untuk demo (dalam production harus unik per user)
DEFAULT_SALT = b"secretnotes-salt-123456789012"  # 32 bytes
ITERATIONS = 100_000
KEY_LENGTH = 16  # AES-128 = 16 bytes


def derive_key(passphrase: str, salt: bytes | None = None) -> bytes:
    """
    Derive AES-128 key dari passphrase menggunakan PBKDF2-HMAC-SHA256.
    
    Args:
        passphrase: Passphrase dari user (minimal 8 karakter)
        salt: Salt opsional, default pakai DEFAULT_SALT
        
    Returns:
        16-byte key untuk AES-128
    """
    if salt is None:
        salt = DEFAULT_SALT
    
    if len(passphrase) < 8:
        raise ValueError("Passphrase minimal 8 karakter")
    
    key = hashlib.pbkdf2_hmac(
        "sha256",
        passphrase.encode("utf-8"),
        salt,
        ITERATIONS,
        dklen=KEY_LENGTH
    )
    return key


def derive_key_base64(passphrase: str, salt: bytes | None = None) -> str:
    """Derive key dan return sebagai base64 string."""
    key = derive_key(passphrase, salt)
    return base64.b64encode(key).decode("ascii")


def generate_salt() -> bytes:
    """Generate salt acak 32 bytes."""
    return os.urandom(32)


def salt_to_base64(salt: bytes) -> str:
    return base64.b64encode(salt).decode("ascii")


def base64_to_salt(s: str) -> bytes:
    return base64.b64decode(s)