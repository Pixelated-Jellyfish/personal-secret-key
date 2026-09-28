"""
Implementasi AES-128 manual (FIPS-197) dengan support trace untuk visualisasi.
Menggunakan representasi row-major standar (state[baris][kolom]) untuk kesederhanaan.
Hanya untuk keperluan edukasi, bukan untuk production security.
"""

# S-Box standar AES (Rijndael)
S_BOX = [
    0x63, 0x7c, 0x77, 0x7b, 0xf2, 0x6b, 0x6f, 0xc5, 0x30, 0x01, 0x67, 0x2b, 0xfe, 0xd7, 0xab, 0x76,
    0xca, 0x82, 0xc9, 0x7d, 0xfa, 0x59, 0x47, 0xf0, 0xad, 0xd4, 0xa2, 0xaf, 0x9c, 0xa4, 0x72, 0xc0,
    0xb7, 0xfd, 0x93, 0x26, 0x36, 0x3f, 0xf7, 0xcc, 0x34, 0xa5, 0xe5, 0xf1, 0x71, 0xd8, 0x31, 0x15,
    0x04, 0xc7, 0x23, 0xc3, 0x18, 0x96, 0x05, 0x9a, 0x07, 0x12, 0x80, 0xe2, 0xeb, 0x27, 0xb2, 0x75,
    0x09, 0x83, 0x2c, 0x1a, 0x1b, 0x6e, 0x5a, 0xa0, 0x52, 0x3b, 0xd6, 0xb3, 0x29, 0xe3, 0x2f, 0x84,
    0x53, 0xd1, 0x00, 0xed, 0x20, 0xfc, 0xb1, 0x5b, 0x6a, 0xcb, 0xbe, 0x39, 0x4a, 0x4c, 0x58, 0xcf,
    0xd0, 0xef, 0xaa, 0xfb, 0x43, 0x4d, 0x33, 0x85, 0x45, 0xf9, 0x02, 0x7f, 0x50, 0x3c, 0x9f, 0xa8,
    0x51, 0xa3, 0x40, 0x8f, 0x92, 0x9d, 0x38, 0xf5, 0xbc, 0xb6, 0xda, 0x21, 0x10, 0xff, 0xf3, 0xd2,
    0xcd, 0x0c, 0x13, 0xec, 0x5f, 0x97, 0x44, 0x17, 0xc4, 0xa7, 0x7e, 0x3d, 0x64, 0x5d, 0x19, 0x73,
    0x60, 0x81, 0x4f, 0xdc, 0x22, 0x2a, 0x90, 0x88, 0x46, 0xee, 0xb8, 0x14, 0xde, 0x5e, 0x0b, 0xdb,
    0xe0, 0x32, 0x3a, 0x0a, 0x49, 0x06, 0x24, 0x5c, 0xc2, 0xd3, 0xac, 0x62, 0x91, 0x95, 0xe4, 0x79,
    0xe7, 0xc8, 0x37, 0x6d, 0x8d, 0xd5, 0x4e, 0xa9, 0x6c, 0x56, 0xf4, 0xea, 0x65, 0x7a, 0xae, 0x08,
    0xba, 0x78, 0x25, 0x2e, 0x1c, 0xa6, 0xb4, 0xc6, 0xe8, 0xdd, 0x74, 0x1f, 0x4b, 0xbd, 0x8b, 0x8a,
    0x70, 0x3e, 0xb5, 0x66, 0x48, 0x03, 0xf6, 0x0e, 0x61, 0x35, 0x57, 0xb9, 0x86, 0xc1, 0x1d, 0x9e,
    0xe1, 0xf8, 0x98, 0x11, 0x69, 0xd9, 0x8e, 0x94, 0x9b, 0x1e, 0x87, 0xe9, 0xce, 0x55, 0x28, 0xdf,
    0x8c, 0xa1, 0x89, 0x0d, 0xbf, 0xe6, 0x42, 0x68, 0x41, 0x99, 0x2d, 0x0f, 0xb0, 0x54, 0xbb, 0x16,
]

# Inverse S-Box untuk dekripsi
INV_S_BOX = [0] * 256
for i, v in enumerate(S_BOX):
    INV_S_BOX[v] = i

# Rcon (Round Constant) untuk key expansion
RCON = [
    0x00, 0x01, 0x02, 0x04, 0x08, 0x10, 0x20, 0x40, 0x80, 0x1b, 0x36
]

# Matriks MixColumns (row-major)
MIX_COL_MATRIX = [
    [0x02, 0x03, 0x01, 0x01],
    [0x01, 0x02, 0x03, 0x01],
    [0x01, 0x01, 0x02, 0x03],
    [0x03, 0x01, 0x01, 0x02],
]

INV_MIX_COL_MATRIX = [
    [0x0e, 0x0b, 0x0d, 0x09],
    [0x09, 0x0e, 0x0b, 0x0d],
    [0x0d, 0x09, 0x0e, 0x0b],
    [0x0b, 0x0d, 0x09, 0x0e],
]


def bytes_to_state(data: bytes) -> list[list[int]]:
    """Konversi 16 bytes ke state 4x4 (row-major: state[baris][kolom])."""
    if len(data) != 16:
        raise ValueError("Input harus 16 bytes")
    # AES state: baris 0 = byte 0,4,8,12; baris 1 = byte 1,5,9,13; dst.
    return [
        [data[r + 4 * c] for c in range(4)]
        for r in range(4)
    ]


def state_to_bytes(state: list[list[int]]) -> bytes:
    """Konversi state 4x4 (row-major) ke 16 bytes."""
    return bytes(state[r][c] for c in range(4) for r in range(4))


def state_to_hex(state: list[list[int]]) -> list[list[str]]:
    """Konversi state ke representasi hex string 2 digit."""
    return [[f"{state[r][c]:02x}" for c in range(4)] for r in range(4)]


def sub_bytes(state: list[list[int]], inverse: bool = False) -> list[list[int]]:
    """SubBytes transformation."""
    box = INV_S_BOX if inverse else S_BOX
    return [[box[state[r][c]] for c in range(4)] for r in range(4)]


def shift_rows(state: list[list[int]], inverse: bool = False) -> list[list[int]]:
    """ShiftRows transformation (row-major)."""
    result = [[0] * 4 for _ in range(4)]
    for r in range(4):
        for c in range(4):
            if inverse:
                new_c = (c + r) % 4
            else:
                new_c = (c - r) % 4
            result[r][new_c] = state[r][c]
    return result


def galois_mul(a: int, b: int) -> int:
    """Perkalian di Galois Field GF(2^8) dengan polinomial x^8 + x^4 + x^3 + x + 1."""
    result = 0
    while b:
        if b & 1:
            result ^= a
        a <<= 1
        if a & 0x100:
            a ^= 0x11b
        b >>= 1
    return result & 0xff


def mix_columns(state: list[list[int]], inverse: bool = False) -> list[list[int]]:
    """MixColumns transformation (row-major)."""
    matrix = INV_MIX_COL_MATRIX if inverse else MIX_COL_MATRIX
    result = [[0] * 4 for _ in range(4)]
    for c in range(4):
        for r in range(4):
            val = 0
            for k in range(4):
                val ^= galois_mul(matrix[r][k], state[k][c])
            result[r][c] = val
    return result


def add_round_key(state: list[list[int]], round_key: list[list[int]]) -> list[list[int]]:
    """AddRoundKey transformation (XOR state dengan round key)."""
    return [[state[r][c] ^ round_key[r][c] for c in range(4)] for r in range(4)]


def rot_word(word: list[int]) -> list[int]:
    """RotWord: rotasi word 1 byte ke kiri."""
    return [word[1], word[2], word[3], word[0]]


def sub_word(word: list[int]) -> list[int]:
    """SubWord: substitusi setiap byte dengan S-Box."""
    return [S_BOX[b] for b in word]


def key_expansion(key: bytes) -> list[list[list[int]]]:
    """
    Key Expansion untuk AES-128.
    Input: 16 bytes key
    Output: 11 round keys (setiap round key = state 4x4 row-major)
    """
    if len(key) != 16:
        raise ValueError("Key harus 16 bytes (AES-128)")

    # Inisialisasi 44 words (4 words per round key * 11 round keys)
    words = [[0] * 4 for _ in range(44)]

    # 4 word pertama dari key asli (key dalam column-major untuk key expansion)
    for i in range(4):
        words[i] = [key[4*i], key[4*i+1], key[4*i+2], key[4*i+3]]

    # Generate remaining words
    for i in range(4, 44):
        temp = words[i-1].copy()
        if i % 4 == 0:
            temp = rot_word(temp)
            temp = sub_word(temp)
            temp[0] ^= RCON[i // 4]
        words[i] = [words[i-4][j] ^ temp[j] for j in range(4)]

    # Konversi ke 11 round keys (state 4x4 row-major)
    round_keys = []
    for i in range(11):
        # words 4*i sampai 4*i+3 adalah 4 kolom round key
        rk = [[words[4*i + c][r] for c in range(4)] for r in range(4)]
        round_keys.append(rk)

    return round_keys


def key_expansion_with_trace(key: bytes) -> tuple[list[list[list[int]]], list[dict]]:
    """
    Key expansion dengan informasi trace untuk visualisasi.
    Returns: (round_keys, trace_info)
    trace_info berisi info word mana yang lewat RotWord, SubWord, Rcon
    """
    if len(key) != 16:
        raise ValueError("Key harus 16 bytes (AES-128)")

    words = [[0] * 4 for _ in range(44)]
    trace_info = []

    for i in range(4):
        words[i] = [key[4*i], key[4*i+1], key[4*i+2], key[4*i+3]]

    for i in range(4, 44):
        temp = words[i-1].copy()
        info = {"word_index": i, "rotword": False, "subword": False, "rcon": None}

        if i % 4 == 0:
            temp = rot_word(temp)
            info["rotword"] = True
            temp = sub_word(temp)
            info["subword"] = True
            rcon_val = RCON[i // 4]
            temp[0] ^= rcon_val
            info["rcon"] = f"{rcon_val:02x}"

        words[i] = [words[i-4][j] ^ temp[j] for j in range(4)]
        trace_info.append(info)

    round_keys = []
    for i in range(11):
        rk = [[words[4*i + c][r] for c in range(4)] for r in range(4)]
        round_keys.append(rk)

    return round_keys, trace_info


def encrypt_block(block: bytes, round_keys: list[list[list[int]]], trace: bool = False) -> tuple[bytes, list[dict] | None]:
    """
    Enkripsi 1 blok (16 bytes) dengan AES-128.
    Returns: (ciphertext, trace_data)
    """
    if len(block) != 16:
        raise ValueError("Block harus 16 bytes")

    state = bytes_to_state(block)
    trace_data = []

    # Initial AddRoundKey (Round 0)
    state = add_round_key(state, round_keys[0])
    if trace:
        trace_data.append({
            "round": 0,
            "step": "add_round_key_initial",
            "state": state_to_hex(state)
        })

    # Rounds 1-9
    for round_num in range(1, 10):
        state = sub_bytes(state)
        if trace:
            trace_data.append({
                "round": round_num,
                "step": "sub_bytes",
                "state": state_to_hex(state)
            })

        state = shift_rows(state)
        if trace:
            trace_data.append({
                "round": round_num,
                "step": "shift_rows",
                "state": state_to_hex(state)
            })

        state = mix_columns(state)
        if trace:
            trace_data.append({
                "round": round_num,
                "step": "mix_columns",
                "state": state_to_hex(state)
            })

        state = add_round_key(state, round_keys[round_num])
        if trace:
            trace_data.append({
                "round": round_num,
                "step": "add_round_key",
                "state": state_to_hex(state)
            })

    # Round 10 (no MixColumns)
    state = sub_bytes(state)
    if trace:
        trace_data.append({
            "round": 10,
            "step": "sub_bytes",
            "state": state_to_hex(state)
        })

    state = shift_rows(state)
    if trace:
        trace_data.append({
            "round": 10,
            "step": "shift_rows",
            "state": state_to_hex(state)
        })

    state = add_round_key(state, round_keys[10])
    if trace:
        trace_data.append({
            "round": 10,
            "step": "add_round_key",
            "state": state_to_hex(state)
        })

    return state_to_bytes(state), trace_data


def decrypt_block(block: bytes, round_keys: list[list[list[int]]], trace: bool = False) -> tuple[bytes, list[dict] | None]:
    """Dekripsi 1 blok (16 bytes) dengan AES-128.
    Returns: (plaintext, trace_data) jika trace=True, else (plaintext, None)
    """
    if len(block) != 16:
        raise ValueError("Block harus 16 bytes")

    state = bytes_to_state(block)
    trace_data = []

    # Initial AddRoundKey (Round 10)
    state = add_round_key(state, round_keys[10])
    if trace:
        trace_data.append({
            "round": 10,
            "step": "add_round_key_initial",
            "state": state_to_hex(state)
        })

    # Rounds 9-1 (inverse order)
    for round_num in range(9, 0, -1):
        state = shift_rows(state, inverse=True)
        if trace:
            trace_data.append({
                "round": round_num,
                "step": "inv_shift_rows",
                "state": state_to_hex(state)
            })

        state = sub_bytes(state, inverse=True)
        if trace:
            trace_data.append({
                "round": round_num,
                "step": "inv_sub_bytes",
                "state": state_to_hex(state)
            })

        state = add_round_key(state, round_keys[round_num])
        if trace:
            trace_data.append({
                "round": round_num,
                "step": "add_round_key",
                "state": state_to_hex(state)
            })

        state = mix_columns(state, inverse=True)
        if trace:
            trace_data.append({
                "round": round_num,
                "step": "inv_mix_columns",
                "state": state_to_hex(state)
            })

    # Round 0
    state = shift_rows(state, inverse=True)
    if trace:
        trace_data.append({
            "round": 0,
            "step": "inv_shift_rows",
            "state": state_to_hex(state)
        })

    state = sub_bytes(state, inverse=True)
    if trace:
        trace_data.append({
            "round": 0,
            "step": "inv_sub_bytes",
            "state": state_to_hex(state)
        })

    state = add_round_key(state, round_keys[0])
    if trace:
        trace_data.append({
            "round": 0,
            "step": "add_round_key",
            "state": state_to_hex(state)
        })

    return state_to_bytes(state), trace_data


def pkcs7_pad(data: bytes, block_size: int = 16) -> bytes:
    """PKCS#7 padding."""
    pad_len = block_size - (len(data) % block_size)
    return data + bytes([pad_len] * pad_len)


def pkcs7_unpad(data: bytes) -> bytes:
    """Remove PKCS#7 padding."""
    if not data:
        raise ValueError("Data kosong")
    pad_len = data[-1]
    if pad_len > 16 or pad_len == 0:
        raise ValueError("Padding tidak valid")
    if data[-pad_len:] != bytes([pad_len] * pad_len):
        raise ValueError("Padding tidak valid")
    return data[:-pad_len]


# Test vector FIPS-197 Appendix C (dengan koreksi dari NIST AESAVS)
FIPS197_KEY = bytes.fromhex("2b7e151628aed2a6abf7158809cf4f3c")
FIPS197_PLAINTEXT = bytes.fromhex("6bc1bee22e409f96e93d7e117393172a")
FIPS197_CIPHERTEXT = bytes.fromhex("3ad77bb40d7a3660a89ecaf32466ef97")