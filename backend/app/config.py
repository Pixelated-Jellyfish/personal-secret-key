"""
Konfigurasi aplikasi dari environment variables.
"""

from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Salt untuk PBKDF2 (base64 encoded 32 bytes)
    SALT_BASE64: str = "c2VjcmV0bm90ZXMtc2FsdC0xMjM0NTY3ODkwMTI="
    
    # CORS origins
    CORS_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    return Settings()