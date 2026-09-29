"""
Penyimpanan catatan ke file JSON dengan file locking untuk thread safety.
"""

import json
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import HTTPException
from filelock import FileLock

from .schemas import NoteCreate, NoteUpdate


DATA_DIR = Path(__file__).parent.parent / "data"
NOTES_FILE = DATA_DIR / "notes.json"
LOCK_FILE = DATA_DIR / "notes.json.lock"


def ensure_data_dir():
    """Pastikan direktori data ada."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def read_notes() -> dict[str, Any]:
    """Baca file notes.json, return dict dengan key 'notes'."""
    ensure_data_dir()
    
    if not NOTES_FILE.exists():
        return {"notes": []}
    
    with FileLock(str(LOCK_FILE)):
        with open(NOTES_FILE, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
                if "notes" not in data:
                    data = {"notes": []}
                return data
            except json.JSONDecodeError:
                return {"notes": []}


def write_notes(data: dict[str, Any]) -> None:
    """Tulis data ke file notes.json."""
    ensure_data_dir()
    
    with FileLock(str(LOCK_FILE)):
        with open(NOTES_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)


def list_notes(aes_key: bytes) -> list[dict[str, Any]]:
    """
    Ambil daftar catatan, dekripsi judul untuk ditampilkan.
    Return: list of {id, title, updated_at}
    """
    from .crypto.modes import decrypt_cbc_base64
    
    data = read_notes()
    result = []
    
    for note in data["notes"]:
        try:
            title = decrypt_cbc_base64(note["title_ciphertext"], aes_key, note["title_iv"])
        except Exception:
            title = "[Gagal dekripsi]"
        
        result.append({
            "id": note["id"],
            "title": title,
            "updated_at": note["updated_at"]
        })
    
    # Urutkan dari yang terbaru
    result.sort(key=lambda x: x["updated_at"], reverse=True)
    return result


def create_note(note_in: NoteCreate, aes_key: bytes) -> str:
    """Buat catatan baru, return ID. Support client-side encryption."""
    from .crypto.modes import encrypt_cbc_base64
    
    now = datetime.utcnow().isoformat() + "Z"
    note_id = str(uuid.uuid4())
    
    # Check if client already encrypted the data
    if note_in.client_encrypted and note_in.title_iv and note_in.body_iv:
        # Client-side encrypted: use provided ciphertext and IV
        title_enc = {"ciphertext": note_in.title, "iv": note_in.title_iv}
        body_enc = {"ciphertext": note_in.body, "iv": note_in.body_iv}
    else:
        # Server-side encryption (backward compatibility)
        title_enc = encrypt_cbc_base64(note_in.title, aes_key)
        body_enc = encrypt_cbc_base64(note_in.body, aes_key)
    
    note = {
        "id": note_id,
        "title_ciphertext": title_enc["ciphertext"],
        "title_iv": title_enc["iv"],
        "body_ciphertext": body_enc["ciphertext"],
        "body_iv": body_enc["iv"],
        "created_at": now,
        "updated_at": now
    }
    
    data = read_notes()
    data["notes"].append(note)
    write_notes(data)
    
    return note_id


def get_note(note_id: str, aes_key: bytes) -> dict[str, Any] | None:
    """Ambil catatan by ID, dekripsi judul dan isi."""
    from .crypto.modes import decrypt_cbc_base64
    
    data = read_notes()
    
    for note in data["notes"]:
        if note["id"] == note_id:
            try:
                title = decrypt_cbc_base64(note["title_ciphertext"], aes_key, note["title_iv"])
                body = decrypt_cbc_base64(note["body_ciphertext"], aes_key, note["body_iv"])
            except Exception:
                title = "[Gagal dekripsi]"
                body = "[Gagal dekripsi]"
            
            return {
                "id": note["id"],
                "title": title,
                "body": body,
                "created_at": note["created_at"],
                "updated_at": note["updated_at"]
            }
    
    return None


def update_note(note_id: str, note_in: NoteUpdate, aes_key: bytes) -> bool:
    """Update catatan. Return True jika berhasil. Support client-side encryption."""
    from .crypto.modes import encrypt_cbc_base64
    
    data = read_notes()
    
    for i, note in enumerate(data["notes"]):
        if note["id"] == note_id:
            now = datetime.utcnow().isoformat() + "Z"
            
            # Check if client already encrypted the data
            if note_in.client_encrypted and note_in.title_iv and note_in.body_iv:
                # Client-side encrypted: use provided ciphertext and IV
                title_enc = {"ciphertext": note_in.title, "iv": note_in.title_iv}
                body_enc = {"ciphertext": note_in.body, "iv": note_in.body_iv}
            else:
                # Server-side encryption (backward compatibility)
                title_enc = encrypt_cbc_base64(note_in.title, aes_key)
                body_enc = encrypt_cbc_base64(note_in.body, aes_key)
            
            data["notes"][i] = {
                "id": note_id,
                "title_ciphertext": title_enc["ciphertext"],
                "title_iv": title_enc["iv"],
                "body_ciphertext": body_enc["ciphertext"],
                "body_iv": body_enc["iv"],
                "created_at": note["created_at"],
                "updated_at": now
            }
            
            write_notes(data)
            return True
    
    return False


def delete_note(note_id: str) -> bool:
    """Hapus catatan. Return True jika berhasil."""
    data = read_notes()
    
    for i, note in enumerate(data["notes"]):
        if note["id"] == note_id:
            data["notes"].pop(i)
            write_notes(data)
            return True
    
    return False


def get_note_raw(note_id: str) -> dict[str, Any] | None:
    """Ambil catatan mentah (ciphertext + IV) untuk visualisasi AES."""
    data = read_notes()
    
    for note in data["notes"]:
        if note["id"] == note_id:
            return note
    
    return None