"""Best-effort abuse protection for a single-instance deployment.

Every interview question and every answer evaluation costs an LLM call, so a
public URL with a real API key is an open tab against the owner's quota. Two
independent limits guard it:

* a **per-client** limit, so one caller cannot crowd everyone else out; and
* a **global** limit on the expensive endpoints, which is what actually caps
  spend - a per-client limit alone is defeated by anyone who can vary the
  address they appear to come from.

State is in process memory. That is the honest fit for the deployment this
targets (one container); run several replicas and each enforces its own share.
For a real security boundary, put the platform's rate limiting in front as
well - this is a cost guard, not an authentication control.
"""

from __future__ import annotations

import threading
import time
from collections import defaultdict, deque

from fastapi import Request
from fastapi.responses import JSONResponse

from config import settings

WINDOW_SECONDS = 60

# Paths that reach the LLM or the embedding model, plus the credential
# endpoints, where repeated attempts are the attack rather than the cost.
EXPENSIVE_PATHS = (
    "/start-interview",
    "/adaptive-interview",
    "/evaluate-answer",
    "/summarize-session",
    "/retry-evaluation",
    "/retry-generation",
    "/download-report",
    "/cv/upload",
    "/login",
    "/register",
)

# Never throttled: orchestrators poll these, and a throttled health check
# reads as an outage.
EXEMPT_PATHS = ("/health", "/docs", "/openapi.json", "/redoc")


class SlidingWindow:
    """Counts hits per key over a fixed window, pruning as it goes."""

    def __init__(self, window_seconds: int = WINDOW_SECONDS) -> None:
        self._window = window_seconds
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def hit(self, key: str, limit: int, now: float | None = None) -> float | None:
        """Record a request. Returns seconds to wait if over ``limit``.

        A rejected request is not recorded, so a caller that backs off is not
        punished for the attempt that told it to back off.
        """
        now = time.monotonic() if now is None else now
        cutoff = now - self._window

        with self._lock:
            hits = self._hits[key]
            while hits and hits[0] <= cutoff:
                hits.popleft()

            if len(hits) >= limit:
                return max(0.0, hits[0] - cutoff)

            hits.append(now)
            if not hits:
                self._hits.pop(key, None)
            return None

    def prune(self, now: float | None = None) -> None:
        """Drop keys with no recent hits so idle clients stop costing memory."""
        now = time.monotonic() if now is None else now
        cutoff = now - self._window

        with self._lock:
            for key in [k for k, v in self._hits.items() if not v or v[-1] <= cutoff]:
                self._hits.pop(key, None)


_per_client = SlidingWindow()
_global = SlidingWindow()
_last_prune = 0.0


def is_expensive(path: str) -> bool:
    return any(path.startswith(prefix) for prefix in EXPENSIVE_PATHS)


def is_exempt(path: str) -> bool:
    return any(path.startswith(prefix) for prefix in EXEMPT_PATHS)


def client_key(request: Request) -> str:
    """Identify the caller, preferring the real client behind a proxy.

    ``X-Forwarded-For`` is only read when TRUST_PROXY_HEADERS says the app is
    actually behind one: the header is caller-supplied, so trusting it without
    a proxy lets anyone pick their own bucket. Ignoring it when there *is* a
    proxy is just as wrong the other way - every request would share the proxy's
    address and one bucket would throttle the whole site.
    """
    if settings.trust_proxy_headers:
        forwarded = request.headers.get("x-forwarded-for", "")
        if forwarded:
            return forwarded.split(",")[0].strip()

    return request.client.host if request.client else "unknown"


def _retry_response(retry_after: float, detail: str) -> JSONResponse:
    seconds = max(1, int(retry_after + 0.999))
    return JSONResponse(
        status_code=429,
        content={"detail": detail},
        headers={"Retry-After": str(seconds)},
    )


async def rate_limit_middleware(request: Request, call_next):
    global _last_prune

    path = request.url.path
    if not settings.rate_limit_enabled or is_exempt(path):
        return await call_next(request)

    now = time.monotonic()
    if now - _last_prune > WINDOW_SECONDS:
        _last_prune = now
        _per_client.prune(now)
        _global.prune(now)

    expensive = is_expensive(path)
    key = client_key(request)

    limit = (
        settings.rate_limit_expensive_per_minute
        if expensive
        else settings.rate_limit_per_minute
    )
    retry_after = _per_client.hit(f"{'x' if expensive else 'd'}:{key}", limit, now)
    if retry_after is not None:
        return _retry_response(
            retry_after, "Too many requests. Please slow down and try again shortly."
        )

    # The global cap is what protects the API budget: unlike the per-client
    # limit it cannot be sidestepped by appearing to be somebody else.
    if expensive:
        retry_after = _global.hit(
            "global", settings.rate_limit_global_expensive_per_minute, now
        )
        if retry_after is not None:
            return _retry_response(
                retry_after,
                "The service is busy right now. Please try again in a moment.",
            )

    return await call_next(request)


def reset_for_tests() -> None:
    """Clear all counters. Tests only."""
    global _last_prune
    _per_client._hits.clear()
    _global._hits.clear()
    _last_prune = 0.0
