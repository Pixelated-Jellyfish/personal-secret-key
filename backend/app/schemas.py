"""
Model Pydantic untuk validasi request/response.
"""

from pydantic import BaseModel, Field
from typing import Optional


class NoteCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    body: str = Field(..., min_length=0, max_length=10000)
    title_iv: Optional[str] = None
    body_iv: Optional[str] = None
    client_encrypted: bool = False


class NoteUpdate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    body: str = Field(..., min_length=0, max_length=10000)
    title_iv: Optional[str] = None
    body_iv: Optional[str] = None
    client_encrypted: bool = False


class NoteResponse(BaseModel):
    id: str
    title: str
    body: str
    created_at: str
    updated_at: str


class NoteListItem(BaseModel):
    id: str
    title: str
    updated_at: str


class NoteRaw(BaseModel):
    id: str
    title_ciphertext: str
    title_iv: str
    body_ciphertext: str
    body_iv: str
    created_at: str
    updated_at: str


class AesLogResponse(BaseModel):
    """Response untuk /notes/{id}/aes-log"""
    input_matrix: list[list[str]]  # 4x4 hex matrix
    trace: list[dict]  # List of {round, step, state: 4x4 hex matrix}


class RoundKeysResponse(BaseModel):
    """Response untuk /notes/{id}/round-keys"""
    round_keys: list[list[list[str]]]  # 11 x 4x4 hex matrix
    key_expansion_trace: list[dict]  # Info RotWord, SubWord, Rcon per word


class DeriveKeyRequest(BaseModel):
    passphrase: str = Field(..., min_length=8)


class DeriveKeyResponse(BaseModel):
    key: str  # base64 encoded 16-byte key


class ErrorResponse(BaseModel):
    detail: str