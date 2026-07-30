"""
Shotto Songroho — Application Configuration
Uses pydantic-settings for type-safe environment variable management.
"""

from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # LLM
    GEMINI_API_KEY: str = ""

    # Vector Store
    CHROMA_PERSIST_PATH: str = "./chroma_data"
    EMBEDDING_MODEL: str = "paraphrase-multilingual-MiniLM-L12-v2"

    # CORS
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000"

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


# Singleton settings instance
settings = Settings()
