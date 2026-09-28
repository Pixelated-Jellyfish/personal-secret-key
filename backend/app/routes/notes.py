"""
API Routes untuk CRUD catatan + visualisasi AES.
"""

import base64
from fastapi import APIRouter, Header, HTTPException, status
from typing import Annotated

from ..crypto.aes import key_expansion, key_expansion_with_trace, encrypt_block, decrypt_block
from ..crypto.kdf import derive_key, DEFAULT_SALT
from ..schemas import (
    NoteCreate, NoteUpdate, NoteResponse, NoteListItem, NoteRaw,
    AesLogResponse, RoundKeysResponse, DeriveKeyRequest, DeriveKeyResponse, ErrorResponse
)
from ..storage import (
    list_notes, create_note, get_note, update_note, delete_note, get_note_raw
)

router = APIRouter()


def get_aes_key(x_aes_key: Annotated[str, Header(alias="X-AES-Key")]) -> bytes:
    """Extract dan validasi AES key dari header."""
    try:
        key = base64.b64decode(x_aes_key)
        if len(key) != 16:
            raise ValueError
        return key
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Header X-AES-Key harus base64 encoded 16-byte key"
        )


@router.post("/crypto/derive", response_model=DeriveKeyResponse)
def derive_key_endpoint(req: DeriveKeyRequest):
    """Derive AES key dari passphrase (PBKDF2)."""
    try:
        key = derive_key(req.passphrase, DEFAULT_SALT)
        return DeriveKeyResponse(key=base64.b64encode(key).decode("ascii"))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/notes", response_model=list[NoteListItem])
def get_notes(aes_key: bytes = Header(..., alias="X-AES-Key")):
    """Daftar semua catatan (judul didekripsi)."""
    key = get_aes_key(aes_key)
    return list_notes(key)


@router.post("/notes", response_model=dict, status_code=status.HTTP_201_CREATED)
def create_note_endpoint(note: NoteCreate, aes_key: bytes = Header(..., alias="X-AES-Key")):
    """Buat catatan baru."""
    key = get_aes_key(aes_key)
    note_id = create_note(note, key)
    return {"id": note_id}


@router.get("/notes/{note_id}", response_model=NoteResponse)
def get_note_endpoint(note_id: str, aes_key: bytes = Header(..., alias="X-AES-Key")):
    """Ambil catatan by ID (didekripsi)."""
    key = get_aes_key(aes_key)
    note = get_note(note_id, key)
    if note is None:
        raise HTTPException(status_code=404, detail="Catatan tidak ditemukan")
    return note


@router.put("/notes/{note_id}", status_code=status.HTTP_200_OK)
def update_note_endpoint(note_id: str, note: NoteUpdate, aes_key: bytes = Header(..., alias="X-AES-Key")):
    """Update catatan (re-encrypt dengan IV baru)."""
    key = get_aes_key(aes_key)
    success = update_note(note_id, note, key)
    if not success:
        raise HTTPException(status_code=404, detail="Catatan tidak ditemukan")
    return {"message": "Catatan diperbarui"}


@router.delete("/notes/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_note_endpoint(note_id: str, aes_key: bytes = Header(..., alias="X-AES-Key")):
    """Hapus catatan."""
    key = get_aes_key(aes_key)
    success = delete_note(note_id)
    if not success:
        raise HTTPException(status_code=404, detail="Catatan tidak ditemukan")
    return


@router.get("/notes/{note_id}/raw", response_model=NoteRaw)
def get_note_raw_endpoint(note_id: str, aes_key: bytes = Header(..., alias="X-AES-Key")):
    """Ambil catatan mentah (ciphertext + IV) untuk visualisasi AES client-side."""
    key = get_aes_key(aes_key)
    note = get_note_raw(note_id)
    if note is None:
        raise HTTPException(status_code=404, detail="Catatan tidak ditemukan")
    return note


@router.get("/notes/{note_id}/aes-log", response_model=AesLogResponse)
def get_aes_log(note_id: str, aes_key: bytes = Header(..., alias="X-AES-Key")):
    """
    Visualisasi proses AES untuk blok pertama catatan.
    Menampilkan matriks input + trace per ronde (SubBytes, ShiftRows, MixColumns, AddRoundKey).
    """
    key = get_aes_key(aes_key)
    
    note_raw = get_note_raw(note_id)
    if note_raw is None:
        raise HTTPException(status_code=404, detail="Catatan tidak ditemukan")
    
    # Ambil blok pertama dari body ciphertext (setelah dekripsi CBC)
    # Kita butuh plaintext blok pertama untuk trace enkripsi
    from ..crypto.modes import decrypt_cbc
    
    ct = base64.b64decode(note_raw["body_ciphertext"])
    iv = base64.b64decode(note_raw["body_iv"])
    
    # Dekripsi CBC untuk dapatkan plaintext
    round_keys = key_expansion(key)
    plaintext = decrypt_cbc(ct, key, iv)
    
    # Ambil 16 byte pertama
    first_block = plaintext[:16]
    if len(first_block) < 16:
        from ..crypto.aes import pkcs7_pad
        first_block = pkcs7_pad(first_block)[:16]
    
    # Enkripsi blok pertama dengan trace (ECB mode untuk visualisasi)
    _, trace = encrypt_block(first_block, round_keys, trace=True)
    
    # Input matrix (plaintext blok pertama sebagai 4x4 hex)
    from ..crypto.aes import bytes_to_state, state_to_hex
    input_state = bytes_to_state(first_block)
    input_matrix = state_to_hex(input_state)
    
    return AesLogResponse(
        input_matrix=input_matrix,
        trace=trace
    )


@router.get("/notes/{note_id}/round-keys", response_model=RoundKeysResponse)
def get_round_keys(note_id: str, aes_key: bytes = Header(..., alias="X-AES-Key")):
    """
    Visualisasi 11 round keys dari key expansion.
    Termasuk info word mana yang lewat RotWord, SubWord, Rcon.
    """
    key = get_aes_key(aes_key)
    
    round_keys, trace = key_expansion_with_trace(key)
    
    # Convert round keys ke hex matrix
    from ..crypto.aes import state_to_hex
    round_keys_hex = [state_to_hex(rk) for rk in round_keys]
    
    return RoundKeysResponse(
        round_keys=round_keys_hex,
        key_expansion_trace=trace
    )


@router.get("/notes/{note_id}/aes-log-decrypt", response_model=AesLogResponse)
def get_aes_log_decrypt(note_id: str, aes_key: bytes = Header(..., alias="X-AES-Key")):
    """
    Visualisasi proses DEKRIPSI AES untuk blok pertama catatan.
    Menampilkan ciphertext blok pertama → trace balik (InvAddRoundKey, InvShiftRows, InvSubBytes, InvMixColumns) → plaintext.
    """
    key = get_aes_key(aes_key)
    
    note_raw = get_note_raw(note_id)
    if note_raw is None:
        raise HTTPException(status_code=404, detail="Catatan tidak ditemukan")
    
    # Ambil blok pertama dari body ciphertext
    from ..crypto.modes import decrypt_cbc
    
    ct = base64.b64decode(note_raw["body_ciphertext"])
    iv = base64.b64decode(note_raw["body_iv"])
    
    # Dekripsi CBC untuk dapatkan plaintext
    round_keys = key_expansion(key)
    plaintext = decrypt_cbc(ct, key, iv)
    
    # Ambil 16 byte pertama plaintext (ini yang akan jadi output akhir dekripsi)
    first_block_plaintext = plaintext[:16]
    if len(first_block_plaintext) < 16:
        from ..crypto.aes import pkcs7_pad
        first_block_plaintext = pkcs7_pad(first_block_plaintext)[:16]
    
    # Enkripsi blok plaintext pertama untuk dapatkan ciphertext blok pertama (ECB mode)
    # Ini adalah ciphertext yang akan didekripsi dalam visualisasi
    first_block_ciphertext, _ = encrypt_block(first_block_plaintext, round_keys, trace=False)
    
    # Input matrix untuk visualisasi dekripsi = ciphertext blok pertama
    from ..crypto.aes import bytes_to_state, state_to_hex
    input_state = bytes_to_state(first_block_ciphertext)
    input_matrix = state_to_hex(input_state)
    
    # Dekripsi blok pertama dengan trace
    _, trace = decrypt_block(first_block_ciphertext, round_keys, trace=True)
    
    return AesLogResponse(
        input_matrix=input_matrix,
        trace=trace
    )