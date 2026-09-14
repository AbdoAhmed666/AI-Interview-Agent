"""Guards on the container build that are cheap to check and expensive to miss.

These assert on the Dockerfile and compose text rather than building an image,
so they run in the normal suite. Each one covers a failure that is silent at
build time and only shows up in a deployed container.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

BACKEND_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BACKEND_DIR.parent

DOCKERFILE = BACKEND_DIR / "Dockerfile"
DOCKERIGNORE = PROJECT_ROOT / ".dockerignore"
COMPOSE_FILE = PROJECT_ROOT / "docker-compose.yml"
GITATTRIBUTES = PROJECT_ROOT / ".gitattributes"
ENTRYPOINT = BACKEND_DIR / "docker-entrypoint.sh"


def _dockerfile_arg(name: str) -> str:
    prefix = f"ARG {name}="
    for line in DOCKERFILE.read_text().splitlines():
        stripped = line.strip()
        if stripped.startswith(prefix):
            return stripped[len(prefix) :].strip()
    raise AssertionError(f"{DOCKERFILE} declares no ARG {name}")


def test_the_baked_embedding_model_matches_the_application():
    """The image pre-downloads whatever rag/config.py will ask for at runtime.

    If these drift, the image still builds and still starts, but the first
    request that touches RAG tries to fetch a model over the network - which
    fails outright, because the runtime stage sets HF_HUB_OFFLINE=1.
    """
    from rag import config as rag_config

    assert _dockerfile_arg("EMBEDDING_MODEL") == rag_config.EMBEDDING_MODEL


def test_the_image_never_reaches_for_the_model_at_runtime():
    dockerfile = DOCKERFILE.read_text()

    assert "HF_HUB_OFFLINE=1" in dockerfile
    assert "TRANSFORMERS_OFFLINE=1" in dockerfile


def test_env_files_are_excluded_from_the_build_context():
    """A bare ".env" pattern only matches the context root.

    The build context is the repository root, so without the "**/" prefix
    backend/.env - which holds real credentials - is copied into the image.
    """
    patterns = {
        line.strip()
        for line in DOCKERIGNORE.read_text().splitlines()
        if line.strip() and not line.strip().startswith("#")
    }

    assert "**/.env" in patterns
    assert "**/.env.*" in patterns


def test_compose_hands_the_backend_a_psycopg_v3_url():
    """A driver-less postgresql:// URL makes SQLAlchemy reach for psycopg2."""
    compose = COMPOSE_FILE.read_text()

    assert "postgresql+psycopg://" in compose


def test_shell_scripts_are_pinned_to_lf_line_endings():
    """Git for Windows checks files out as CRLF unless told otherwise.

    A CRLF shebang makes the kernel look for an interpreter named "/bin/sh\r",
    so the container dies with "no such file or directory" naming a file that is
    plainly there. Only .gitattributes stops that at the checkout.
    """
    rules = {
        line.strip()
        for line in GITATTRIBUTES.read_text().splitlines()
        if line.strip() and not line.strip().startswith("#")
    }

    assert "*.sh text eol=lf" in rules


def test_the_entrypoint_has_no_carriage_returns():
    assert b"\r" not in ENTRYPOINT.read_bytes()


def test_the_image_strips_carriage_returns_from_the_entrypoint():
    """Belt and braces: a checkout predating .gitattributes still has to boot."""
    dockerfile = DOCKERFILE.read_text()

    assert "sed -i 's/\\r$//' /app/backend/docker-entrypoint.sh" in dockerfile
