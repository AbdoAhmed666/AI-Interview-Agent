from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from config import settings


def normalize_database_url(url: str) -> str:
    """Force the psycopg (v3) driver for driver-less PostgreSQL URLs.

    SQLAlchemy defaults ``postgresql://`` to psycopg2, which this project does
    not ship (we pin ``psycopg[binary]`` v3). Hosting providers and local
    setups commonly hand out ``postgres://`` or ``postgresql://``, so rewrite
    those to ``postgresql+psycopg://`` instead of failing with
    ``ModuleNotFoundError: No module named 'psycopg2'``. URLs that already name
    a driver are left untouched.
    """
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://") :]
    if url.startswith("postgresql://"):
        url = "postgresql+psycopg://" + url[len("postgresql://") :]
    return url


DATABASE_URL = normalize_database_url(settings.database_url)

if not DATABASE_URL:
    # create_engine("") raises a SQLAlchemy parse error that says nothing about
    # what is actually wrong, and it fires at import time - before the startup
    # config validation in main.py can report it.
    raise RuntimeError(
        "DATABASE_URL is not set. Set it in the environment (Docker) or in a "
        ".env file next to the backend (see .env.example)."
    )

engine = create_engine(
    DATABASE_URL,
    echo=False,
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()