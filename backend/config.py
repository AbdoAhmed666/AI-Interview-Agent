import os
from dataclasses import dataclass
from pathlib import Path
from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BACKEND_DIR.parent
RUNTIME_DIR = PROJECT_ROOT / ".runtime"

# Support both documented startup locations: the repository root and backend/.
load_dotenv(PROJECT_ROOT / ".env")
load_dotenv(BACKEND_DIR / ".env", override=True)


@dataclass(frozen=True)
class Settings:

    openai_api_key: str | None = os.getenv("OPENAI_API_KEY")

    gemini_api_key: str | None = os.getenv("GEMINI_API_KEY")

    model_name: str | None = os.getenv("MODEL_NAME")

    groq_api_key: str | None = os.getenv("GROQ_API_KEY")

    groq_model: str | None = os.getenv("GROQ_MODEL")

    secret_key: str = os.getenv("SECRET_KEY", "")

    algorithm: str = os.getenv("ALGORITHM", "HS256")

    access_token_expire_minutes: int = int(
        os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60")
    )

    llm_provider: str = os.getenv(
        "LLM_PROVIDER",
        "mock"
    ).strip().lower()

    # Database
    database_url: str = os.getenv("DATABASE_URL", "")

settings = Settings()
