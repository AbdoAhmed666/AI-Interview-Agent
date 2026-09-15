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

    interview_recovery_stale_seconds: int = int(
        os.getenv("INTERVIEW_RECOVERY_STALE_SECONDS", "300")
    )

    # Abuse / cost protection. Every interview question and answer evaluation
    # is an LLM call, so a public deployment needs a ceiling on how fast those
    # can be triggered. See rate_limit.py.
    rate_limit_enabled: bool = os.getenv("RATE_LIMIT_ENABLED", "true").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    )

    rate_limit_per_minute: int = int(os.getenv("RATE_LIMIT_PER_MINUTE", "60"))

    rate_limit_expensive_per_minute: int = int(
        os.getenv("RATE_LIMIT_EXPENSIVE_PER_MINUTE", "10")
    )

    # Across every caller combined: the limit that actually caps the API bill.
    rate_limit_global_expensive_per_minute: int = int(
        os.getenv("RATE_LIMIT_GLOBAL_EXPENSIVE_PER_MINUTE", "60")
    )

    # Only set this where the app really sits behind a proxy (a hosted
    # deployment). X-Forwarded-For is caller-supplied: trusted without a proxy
    # it lets anyone choose their own rate-limit bucket, and ignored behind one
    # it collapses every visitor into the proxy's single bucket.
    trust_proxy_headers: bool = os.getenv(
        "TRUST_PROXY_HEADERS", "false"
    ).strip().lower() in ("1", "true", "yes", "on")

    # Database
    database_url: str = os.getenv("DATABASE_URL", "")

    # Deployment / runtime
    app_env: str = os.getenv("APP_ENV", "development").strip().lower()

    debug: bool = os.getenv("DEBUG", "false").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    )

    # Comma-separated list of allowed CORS origins for the frontend.
    cors_allow_origins: str = os.getenv(
        "CORS_ALLOW_ORIGINS",
        "http://localhost:3000,http://127.0.0.1:3000",
    )

    @property
    def is_production(self) -> bool:
        return self.app_env in ("production", "prod")

    @property
    def cors_origins(self) -> list[str]:
        """Parsed, de-duplicated list of allowed CORS origins."""
        return [
            origin.strip()
            for origin in self.cors_allow_origins.split(",")
            if origin.strip()
        ]

    def validate_runtime(self) -> None:
        """Fail fast on misconfiguration that would be unsafe at runtime.

        Called once at application startup so a misconfigured deployment
        refuses to boot instead of silently signing tokens with an empty
        secret or connecting to no database.
        """
        errors: list[str] = []
        if not self.secret_key:
            errors.append("SECRET_KEY is not set (JWTs would be unsigned/forgeable).")
        elif self.is_production and len(self.secret_key) < 32:
            errors.append("SECRET_KEY is too short for production (use >= 32 chars).")
        if not self.database_url:
            errors.append("DATABASE_URL is not set.")
        if self.is_production and self.debug:
            errors.append("DEBUG must be disabled in production.")
        if errors:
            raise RuntimeError(
                "Invalid configuration:\n  - " + "\n  - ".join(errors)
            )


settings = Settings()
