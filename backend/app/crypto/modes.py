"""
Mode operasi CBC (Cipher Block Chaining) dengan PKCS#7 padding.
"""

import os
import base64
from .aes import encrypt_block, decrypt_block, pkcs7_pad, pkcs7_unpad, key_expansion


def encrypt_cbc(plaintext: bytes, key: bytes) -> tuple[bytes, bytes]:
    """
    Enkripsi dengan AES-128-CBC.
    
    Args:
        plaintext: Data plaintext
        key: 16-byte AES key
        
    Returns:
        (ciphertext, iv) - keduanya bytes
    """
    if len(key) != 16:
        raise ValueError("Key harus 16 bytes")
    
    iv = os.urandom(16)
    round_keys = key_expansion(key)
    
    padded = pkcs7_pad(plaintext)
    blocks = [padded[i:i+16] for i in range(0, len(padded), 16)]
    
    ciphertext = bytearray()
    prev_block = iv
    
    for block in blocks:
        # XOR dengan IV atau ciphertext block sebelumnya
        xor_block = bytes(a ^ b for a, b in zip(block, prev_block))
        enc_block, _ = encrypt_block(xor_block, round_keys)
        ciphertext.extend(enc_block)
        prev_block = enc_block
    
    return bytes(ciphertext), iv


def decrypt_cbc(ciphertext: bytes, key: bytes, iv: bytes) -> bytes:
    """
    Dekripsi dengan AES-128-CBC.
    
    Args:
        ciphertext: Data ciphertext
        key: 16-byte AES key
        iv: 16-byte IV
        
    Returns:
        Plaintext bytes
    """
    if len(key) != 16:
        raise ValueError("Key harus 16 bytes")
    if len(iv) != 16:
        raise ValueError("IV harus 16 bytes")
    if len(ciphertext) % 16 != 0:
        raise ValueError("Ciphertext harus kelipatan 16 bytes")
    
    round_keys = key_expansion(key)
    blocks = [ciphertext[i:i+16] for i in range(0, len(ciphertext), 16)]
    
    plaintext = bytearray()
    prev_block = iv
    
    for block in blocks:
        dec_block, _ = decrypt_block(block, round_keys)
        # XOR dengan IV atau ciphertext block sebelumnya
        xor_block = bytes(a ^ b for a, b in zip(dec_block, prev_block))
        plaintext.extend(xor_block)
        prev_block = block
    
    return pkcs7_unpad(plaintext)


def encrypt_cbc_base64(plaintext: str, key: bytes) -> dict:
    """
    Enkripsi string dan return base64 encoded ciphertext + IV.
    """
    ct, iv = encrypt_cbc(plaintext.encode("utf-8"), key)
    return {
        "ciphertext": base64.b64encode(ct).decode("ascii"),
        "iv": base64.b64encode(iv).decode("ascii")
    }


def decrypt_cbc_base64(ciphertext_b64: str, key: bytes, iv_b64: str) -> str:
    """
    Dekripsi base64 encoded ciphertext + IV.
    """
    ct = base64.b64decode(ciphertext_b64)
    iv = base64.b64decode(iv_b64)
    pt = decrypt_cbc(ct, key, iv)
    return pt.decode("utf-8")