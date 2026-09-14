"""Tests for PostgreSQL URL normalization (psycopg v3 driver selection)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from database import normalize_database_url


def test_bare_postgresql_url_gets_the_psycopg_driver():
    assert (
        normalize_database_url("postgresql://user:pw@localhost:5432/db")
        == "postgresql+psycopg://user:pw@localhost:5432/db"
    )


def test_postgres_scheme_is_upgraded_and_gets_the_driver():
    # Several hosting providers hand out postgres:// URLs.
    assert (
        normalize_database_url("postgres://user:pw@localhost:5432/db")
        == "postgresql+psycopg://user:pw@localhost:5432/db"
    )


def test_explicit_driver_is_preserved():
    url = "postgresql+psycopg://user:pw@localhost:5432/db"
    assert normalize_database_url(url) == url


def test_explicit_psycopg2_driver_is_not_rewritten():
    url = "postgresql+psycopg2://user:pw@localhost:5432/db"
    assert normalize_database_url(url) == url


def test_non_postgres_url_is_untouched():
    assert normalize_database_url("sqlite:///test.db") == "sqlite:///test.db"
