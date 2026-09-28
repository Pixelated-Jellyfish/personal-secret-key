"""
Unit test untuk AES manual - validasi dengan FIPS-197 test vector dan pycryptodome.
"""

import pytest
from app.crypto.aes import (
    key_expansion,
    key_expansion_with_trace,
    encrypt_block,
    decrypt_block,
    bytes_to_state,
    state_to_bytes,
    sub_bytes,
    shift_rows,
    mix_columns,
    add_round_key,
    pkcs7_pad,
    pkcs7_unpad,
    FIPS197_KEY,
    FIPS197_PLAINTEXT,
    FIPS197_CIPHERTEXT,
)
from app.crypto.modes import encrypt_cbc, decrypt_cbc
from app.crypto.kdf import derive_key


try:
    from Crypto.Cipher import AES
    HAS_PYCRYPTODOME = True
except ImportError:
    HAS_PYCRYPTODOME = False


class TestAESCore:
    """Test komponen inti AES."""

    def test_bytes_to_state_roundtrip(self):
        data = bytes(range(16))
        state = bytes_to_state(data)
        result = state_to_bytes(state)
        assert result == data

    def test_sub_bytes_inverse(self):
        state = [[i + j * 4 for i in range(4)] for j in range(4)]
        sub = sub_bytes(state)
        inv = sub_bytes(sub, inverse=True)
        assert inv == state

    def test_shift_rows_inverse(self):
        state = [[i + j * 4 for i in range(4)] for j in range(4)]
        shifted = shift_rows(state)
        inv = shift_rows(shifted, inverse=True)
        assert inv == state

    def test_mix_columns_inverse(self):
        state = [[i + j * 4 for i in range(4)] for j in range(4)]
        mixed = mix_columns(state)
        inv = mix_columns(mixed, inverse=True)
        assert inv == state

    def test_add_round_key(self):
        state = [[0] * 4 for _ in range(4)]
        key = [[i + j * 4 for i in range(4)] for j in range(4)]
        result = add_round_key(state, key)
        assert result == key
        # XOR lagi harus kembali ke 0
        result2 = add_round_key(result, key)
        assert result2 == state


class TestKeyExpansion:
    """Test Key Expansion."""

    def test_key_expansion_length(self):
        round_keys = key_expansion(FIPS197_KEY)
        assert len(round_keys) == 11  # 10 rounds + initial
        for rk in round_keys:
            assert len(rk) == 4
            for row in rk:
                assert len(row) == 4

    def test_first_round_key_equals_key(self):
        round_keys = key_expansion(FIPS197_KEY)
        # Round key 0 harus sama dengan key asli (row-major state)
        expected = bytes_to_state(FIPS197_KEY)
        assert round_keys[0] == expected

    def test_fips197_round_key_1(self):
        """Test vector FIPS-197: Round key 1 harus bernilai tertentu."""
        round_keys = key_expansion(FIPS197_KEY)
        # Round key 1 (index 1) dari FIPS-197 Appendix A
        expected_rk1 = bytes.fromhex("a0fafe1788542cb123a339392a6c7605")
        expected_matrix = bytes_to_state(expected_rk1)
        assert round_keys[1] == expected_matrix

    def test_key_expansion_trace(self):
        round_keys, trace = key_expansion_with_trace(FIPS197_KEY)
        assert len(round_keys) == 11
        assert len(trace) == 40  # 44 words - 4 initial = 40 generated
        # Word 4 (index 0 in trace) harus lewat RotWord, SubWord, Rcon
        assert trace[0]["rotword"] is True
        assert trace[0]["subword"] is True
        assert trace[0]["rcon"] == "01"


class TestAESEncryption:
    """Test enkripsi/dekripsi blok."""

    def test_encrypt_decrypt_block(self):
        round_keys = key_expansion(FIPS197_KEY)
        ct, _ = encrypt_block(FIPS197_PLAINTEXT, round_keys)
        pt, _ = decrypt_block(ct, round_keys)
        assert pt == FIPS197_PLAINTEXT

    def test_fips197_test_vector(self):
        """Test vector resmi FIPS-197 Appendix C."""
        round_keys = key_expansion(FIPS197_KEY)
        ct, _ = encrypt_block(FIPS197_PLAINTEXT, round_keys)
        assert ct == FIPS197_CIPHERTEXT

    def test_encrypt_block_with_trace(self):
        round_keys = key_expansion(FIPS197_KEY)
        ct, trace = encrypt_block(FIPS197_PLAINTEXT, round_keys, trace=True)
        
        # Harus ada trace untuk initial + 10 rounds * 4 steps + final round * 3 steps
        # Round 0: 1 step (add_round_key_initial)
        # Round 1-9: 4 steps each (sub_bytes, shift_rows, mix_columns, add_round_key)
        # Round 10: 3 steps (sub_bytes, shift_rows, add_round_key)
        expected_steps = 1 + 9 * 4 + 3
        assert len(trace) == expected_steps
        
        # Verifikasi struktur trace
        assert trace[0]["round"] == 0
        assert trace[0]["step"] == "add_round_key_initial"
        assert trace[-1]["round"] == 10
        assert trace[-1]["step"] == "add_round_key"
        
        # State akhir harus sama dengan ciphertext
        final_state = trace[-1]["state"]
        # Convert hex matrix back to bytes (row-major: state[r][c])
        final_bytes = bytes(int(final_state[r][c], 16) for c in range(4) for r in range(4))
        assert final_bytes == ct

    @pytest.mark.skipif(not HAS_PYCRYPTODOME, reason="pycryptodome not installed")
    def test_match_pycryptodome_ecb(self):
        """Hasil AES manual harus identik dengan pycryptodome ECB mode."""
        from Crypto.Cipher import AES
        
        key = FIPS197_KEY
        plaintext = FIPS197_PLAINTEXT
        
        # Manual
        round_keys = key_expansion(key)
        ct_manual, _ = encrypt_block(plaintext, round_keys)
        
        # pycryptodome
        cipher = AES.new(key, AES.MODE_ECB)
        ct_pycrypto = cipher.encrypt(plaintext)
        
        assert ct_manual == ct_pycrypto


class TestCBCMode:
    """Test mode CBC."""

    def test_encrypt_decrypt_cbc(self):
        key = FIPS197_KEY
        plaintext = b"Ini adalah pesan rahasia yang agak panjang untuk test CBC mode AES-128"
        
        ct, iv = encrypt_cbc(plaintext, key)
        pt = decrypt_cbc(ct, key, iv)
        
        assert pt == plaintext
        assert len(iv) == 16

    def test_cbc_different_iv_produces_different_ciphertext(self):
        key = FIPS197_KEY
        plaintext = b"Pesan test"
        
        ct1, iv1 = encrypt_cbc(plaintext, key)
        ct2, iv2 = encrypt_cbc(plaintext, key)
        
        # IV berbeda -> ciphertext berbeda
        assert iv1 != iv2
        assert ct1 != ct2
        
        # Tapi dekripsi keduanya harus sama
        assert decrypt_cbc(ct1, key, iv1) == plaintext
        assert decrypt_cbc(ct2, key, iv2) == plaintext

    @pytest.mark.skipif(not HAS_PYCRYPTODOME, reason="pycryptodome not installed")
    def test_match_pycryptodome_cbc(self):
        """CBC manual harus cocok dengan pycryptodome CBC."""
        from Crypto.Cipher import AES
        
        key = FIPS197_KEY
        iv = bytes.fromhex("000102030405060708090a0b0c0d0e0f")
        plaintext = b"Test CBC mode dengan pycryptodome untuk validasi"
        
        # Manual
        ct_manual, _ = encrypt_cbc(plaintext, key)
        # Manual dengan IV tetap untuk perbandingan
        from app.crypto.aes import key_expansion, pkcs7_pad
        round_keys = key_expansion(key)
        padded = pkcs7_pad(plaintext)
        blocks = [padded[i:i+16] for i in range(0, len(padded), 16)]
        ct_manual_fixed = bytearray()
        prev = iv
        for block in blocks:
            xor_block = bytes(a ^ b for a, b in zip(block, prev))
            enc_block, _ = encrypt_block(xor_block, round_keys)
            ct_manual_fixed.extend(enc_block)
            prev = enc_block
        
        # pycryptodome
        cipher = AES.new(key, AES.MODE_CBC, iv)
        ct_pycrypto = cipher.encrypt(padded)
        
        assert bytes(ct_manual_fixed) == ct_pycrypto


class TestKDF:
    """Test Key Derivation Function."""

    def test_derive_key_length(self):
        key = derive_key("passphrase123")
        assert len(key) == 16

    def test_derive_key_deterministic(self):
        key1 = derive_key("samasama", b"salt12345678901234567890123456789012")
        key2 = derive_key("samasama", b"salt12345678901234567890123456789012")
        assert key1 == key2

    def test_derive_key_different_passphrase(self):
        key1 = derive_key("passphrase1")
        key2 = derive_key("passphrase2")
        assert key1 != key2

    def test_derive_key_min_length(self):
        with pytest.raises(ValueError):
            derive_key("short")


class TestPadding:
    """Test PKCS#7 padding."""

    def test_pad_unpad_exact_block(self):
        data = b"x" * 16
        padded = pkcs7_pad(data)
        assert len(padded) == 32  # Full block padding
        assert pkcs7_unpad(padded) == data

    def test_pad_unpad_partial_block(self):
        data = b"hello"
        padded = pkcs7_pad(data)
        assert len(padded) == 16
        assert pkcs7_unpad(padded) == data

    def test_unpad_invalid(self):
        # Data harus multiple of block size (16)
        # Valid padding: 11 bytes data + 5 bytes padding = 16 bytes
        # Invalid: inconsistent padding (last byte says 5 but only 4 bytes of 0x05)
        with pytest.raises(ValueError):
            pkcs7_unpad(b"invaliddata" + bytes([0x05, 0x05, 0x05, 0x05, 0x04]))
        # Invalid: padding value == 0
        with pytest.raises(ValueError):
            pkcs7_unpad(b"invaliddata1234" + bytes([0x00] * 16))


if __name__ == "__main__":
    pytest.main([__file__, "-v"])