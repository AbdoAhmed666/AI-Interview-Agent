"""Application configuration for the AI Interview Agent backend.

This module centralizes environment-variable loading and keeps secrets out of
business logic. Future LLM integrations can reuse these settings.
"""

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    """Runtime settings loaded from environment variables."""

    openai_api_key: str | None = os.getenv("OPENAI_API_KEY") or None
    gemini_api_key: str | None = os.getenv("GEMINI_API_KEY") or None
    model_name: str | None = os.getenv("MODEL_NAME") or None
    llm_provider: str = os.getenv("LLM_PROVIDER", "mock").strip().lower()


settings = Settings()
