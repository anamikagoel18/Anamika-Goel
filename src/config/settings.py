from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Central configuration for the project.

    This will be useful in later phases when we actually call the Groq LLM.
    For now it just knows how to load the Groq API key from the environment or .env file.
    """

    groq_api_key: str | None = Field(
        default=None,
        alias="GROQ_API_KEY",
        description="API key for Groq LLM (do not commit this to git).",
    )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()

