"""
Integration tests untuk API notes.
"""

import base64
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.crypto.kdf import derive_key, DEFAULT_SALT
from app.crypto.aes import pkcs7_pad


client = TestClient(app)


def get_test_key() -> str:
    """Get base64 encoded AES key untuk testing."""
    key = derive_key("testpassphrase123", DEFAULT_SALT)
    return base64.b64encode(key).decode("ascii")


def auth_header() -> dict:
    return {"X-AES-Key": get_test_key()}


def hex_matrix(block: bytes) -> list[list[str]]:
    from app.crypto.aes import bytes_to_state, state_to_hex

    return state_to_hex(bytes_to_state(block))


class TestNotesAPI:
    """Test CRUD notes API."""

    @pytest.fixture(autouse=True)
    def isolate_notes_storage(self, tmp_path, monkeypatch):
        from app import storage

        monkeypatch.setattr(storage, "DATA_DIR", tmp_path)
        monkeypatch.setattr(storage, "NOTES_FILE", tmp_path / "notes.json")
        monkeypatch.setattr(storage, "LOCK_FILE", tmp_path / "notes.json.lock")

    def test_derive_key(self):
        response = client.post("/api/crypto/derive", json={"passphrase": "testpassphrase123"})
        assert response.status_code == 200
        data = response.json()
        assert "key" in data
        assert len(data["key"]) > 0

    def test_derive_key_too_short(self):
        response = client.post("/api/crypto/derive", json={"passphrase": "short"})
        assert response.status_code == 422  # FastAPI validation error

    def test_create_and_list_notes(self):
        # Create note
        response = client.post("/api/notes", 
            json={"title": "Catatan Pertama", "body": "Isi catatan rahasia"},
            headers=auth_header())
        assert response.status_code == 201
        note_id = response.json()["id"]

        # List notes
        response = client.get("/api/notes", headers=auth_header())
        assert response.status_code == 200
        notes = response.json()
        assert len(notes) == 1
        assert notes[0]["id"] == note_id
        assert notes[0]["title"] == "Catatan Pertama"

    def test_get_note(self):
        # Create
        response = client.post("/api/notes",
            json={"title": "Test Title", "body": "Test Body"},
            headers=auth_header())
        note_id = response.json()["id"]

        # Get
        response = client.get(f"/api/notes/{note_id}", headers=auth_header())
        assert response.status_code == 200
        note = response.json()
        assert note["id"] == note_id
        assert note["title"] == "Test Title"
        assert note["body"] == "Test Body"

    def test_update_note(self):
        # Create
        response = client.post("/api/notes",
            json={"title": "Original", "body": "Original body"},
            headers=auth_header())
        note_id = response.json()["id"]

        # Update
        response = client.put(f"/api/notes/{note_id}",
            json={"title": "Updated", "body": "Updated body"},
            headers=auth_header())
        assert response.status_code == 200

        # Verify
        response = client.get(f"/api/notes/{note_id}", headers=auth_header())
        assert response.status_code == 200
        note = response.json()
        assert note["title"] == "Updated"
        assert note["body"] == "Updated body"

    def test_delete_note(self):
        # Create
        response = client.post("/api/notes",
            json={"title": "To Delete", "body": "Delete me"},
            headers=auth_header())
        note_id = response.json()["id"]

        # Delete
        response = client.delete(f"/api/notes/{note_id}", headers=auth_header())
        assert response.status_code == 204

        # Verify deleted
        response = client.get(f"/api/notes/{note_id}", headers=auth_header())
        assert response.status_code == 404

        # List should be empty
        response = client.get("/api/notes", headers=auth_header())
        assert response.status_code == 200
        assert len(response.json()) == 0

    def test_wrong_key_cannot_read(self):
        # Create with key1
        key1 = base64.b64encode(derive_key("passphrase111", DEFAULT_SALT)).decode()
        response = client.post("/api/notes",
            json={"title": "Secret", "body": "Hidden"},
            headers={"X-AES-Key": key1})
        note_id = response.json()["id"]

        # Try to read with key2
        key2 = base64.b64encode(derive_key("passphrase222", DEFAULT_SALT)).decode()
        response = client.get(f"/api/notes/{note_id}", headers={"X-AES-Key": key2})
        # Should fail to decrypt (title will be garbled or error)
        # Actually it returns 200 but title is "[Gagal dekripsi]"
        # Better: list notes with wrong key should show garbled title
        response = client.get("/api/notes", headers={"X-AES-Key": key2})
        assert response.status_code == 200
        notes = response.json()
        assert notes[0]["title"] == "[Gagal dekripsi]"

    @pytest.mark.parametrize("body", [
        "short",
        "Ini adalah plaintext untuk test AES visualisasi blok pertama",
    ])
    def test_aes_log_endpoint(self, body):
        response = client.post("/api/notes",
            json={"title": "AES Test", "body": body},
            headers=auth_header())
        note_id = response.json()["id"]

        raw = client.get(f"/api/notes/{note_id}/raw", headers=auth_header()).json()
        response = client.get(f"/api/notes/{note_id}/aes-log", headers=auth_header())
        assert response.status_code == 200
        data = response.json()
        assert "input_matrix" in data
        assert "trace" in data
        assert len(data["input_matrix"]) == 4
        assert len(data["trace"]) > 0
        ciphertext = base64.b64decode(raw["body_ciphertext"])
        iv = base64.b64decode(raw["body_iv"])
        first_plaintext_block = pkcs7_pad(body.encode("utf-8"))[:16]
        cbc_input = bytes(
            plaintext_byte ^ iv_byte
            for plaintext_byte, iv_byte in zip(first_plaintext_block, iv)
        )
        assert data["input_matrix"] == hex_matrix(first_plaintext_block)
        assert data["trace"][0]["step"] == "cbc_xor_iv"
        assert data["trace"][0]["state"] == hex_matrix(cbc_input)
        assert data["trace"][-1]["state"] == hex_matrix(ciphertext[:16])

    def test_round_keys_endpoint(self):
        response = client.post("/api/notes",
            json={"title": "RK Test", "body": "Test round keys"},
            headers=auth_header())
        note_id = response.json()["id"]

        response = client.get(f"/api/notes/{note_id}/round-keys", headers=auth_header())
        assert response.status_code == 200
        data = response.json()
        assert "round_keys" in data
        assert "key_expansion_trace" in data
        assert len(data["round_keys"]) == 11
        for rk in data["round_keys"]:
            assert len(rk) == 4
            for row in rk:
                assert len(row) == 4

    @pytest.mark.parametrize("body", [
        "short",
        "Ini adalah plaintext untuk test dekripsi AES visualisasi",
    ])
    def test_aes_log_decrypt_endpoint(self, body):
        response = client.post("/api/notes",
            json={"title": "AES Decrypt Test", "body": body},
            headers=auth_header())
        note_id = response.json()["id"]

        raw = client.get(f"/api/notes/{note_id}/raw", headers=auth_header()).json()
        response = client.get(f"/api/notes/{note_id}/aes-log-decrypt", headers=auth_header())
        assert response.status_code == 200
        data = response.json()
        assert "input_matrix" in data
        assert "trace" in data
        assert len(data["input_matrix"]) == 4
        assert len(data["trace"]) > 0
        
        # Verify trace contains decryption steps
        step_names = [step["step"] for step in data["trace"]]
        assert "add_round_key_initial" in step_names
        assert "inv_shift_rows" in step_names
        assert "inv_sub_bytes" in step_names
        assert "inv_mix_columns" in step_names
        assert "add_round_key" in step_names
        ciphertext = base64.b64decode(raw["body_ciphertext"])
        first_plaintext_block = pkcs7_pad(body.encode("utf-8"))[:16]
        assert data["input_matrix"] == hex_matrix(ciphertext[:16])
        assert data["trace"][-1]["step"] == "cbc_xor_iv"
        assert data["trace"][-1]["state"] == hex_matrix(first_plaintext_block)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])