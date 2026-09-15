# Backend image for the AI Interview Agent API.
#
# Build context is the REPOSITORY ROOT, not backend/, because requirements.txt
# lives there:
#     docker build -f backend/Dockerfile -t ai-interview-backend .

# --------------------------------------------------------------------------
# Build stage: install dependencies and pre-fetch the embedding model.
# Neither the compiler toolchain nor pip's caches reach the final image.
# --------------------------------------------------------------------------
FROM python:3.11-slim AS builder

ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    HF_HOME=/opt/hf-cache

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /tmp/requirements.txt

RUN python -m venv /opt/venv \
    && /opt/venv/bin/pip install --upgrade pip \
    && /opt/venv/bin/pip install -r /tmp/requirements.txt

# Bake the sentence-transformers model into the image. Downloading it on first
# use meant the API could not start at all without internet access, and the
# first candidate to hit RAG paid a ~130MB download. Keep this value in step
# with EMBEDDING_MODEL in backend/rag/config.py - test_docker_image.py fails if
# the two drift apart.
ARG EMBEDDING_MODEL=BAAI/bge-small-en-v1.5
RUN /opt/venv/bin/python -c \
    "from sentence_transformers import SentenceTransformer; SentenceTransformer('${EMBEDDING_MODEL}')"

# --------------------------------------------------------------------------
# Runtime stage.
# --------------------------------------------------------------------------
FROM python:3.11-slim AS runtime

# HF_HUB_OFFLINE/TRANSFORMERS_OFFLINE: the model is already in the image, so
# never reach for the network. Override them if you deliberately want a
# different model pulled at runtime.
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/opt/venv/bin:${PATH}" \
    HF_HOME=/opt/hf-cache \
    HF_HUB_OFFLINE=1 \
    TRANSFORMERS_OFFLINE=1

RUN useradd --create-home --uid 10001 app

COPY --from=builder /opt/venv /opt/venv
COPY --from=builder /opt/hf-cache /opt/hf-cache

WORKDIR /app
COPY backend/ /app/backend/

# Uploaded CVs and generated FAISS indexes are written under .runtime; compose
# mounts a volume here so they outlive the container. Everything else stays
# read-only to the unprivileged user that runs the app.
#
# The sed strips CRLF from the entrypoint. .gitattributes already pins it to LF,
# but a checkout made before that landed - or an edit in a Windows editor - puts
# "\r" back, and the kernel then looks for an interpreter literally named
# "/bin/sh\r" and reports "no such file or directory" about a file that exists.
# One line here makes the image immune to however it was checked out.
RUN mkdir -p /app/.runtime \
    && chown -R app:app /app/.runtime \
    && sed -i 's/\r$//' /app/backend/docker-entrypoint.sh \
    && chmod +x /app/backend/docker-entrypoint.sh

USER app
WORKDIR /app/backend

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=45s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=4)"

ENTRYPOINT ["/app/backend/docker-entrypoint.sh"]
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
