"""Tests for the abuse/cost guard in front of the LLM endpoints.

No database and no network: the limiter is pure in-process bookkeeping, so
these run anywhere.
"""
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

import rate_limit
from rate_limit import SlidingWindow, client_key, is_exempt, is_expensive


class FakeClient:
    def __init__(self, host):
        self.host = host


class FakeRequest:
    def __init__(self, host="1.2.3.4", headers=None):
        self.client = FakeClient(host) if host else None
        self.headers = headers or {}


@pytest.fixture(autouse=True)
def clean_counters():
    rate_limit.reset_for_tests()
    yield
    rate_limit.reset_for_tests()


class TestSlidingWindow:
    def test_allows_requests_up_to_the_limit(self):
        window = SlidingWindow(window_seconds=60)

        assert [window.hit("a", 3, now=100.0) for _ in range(3)] == [None, None, None]

    def test_rejects_the_one_past_the_limit(self):
        window = SlidingWindow(window_seconds=60)
        for _ in range(3):
            window.hit("a", 3, now=100.0)

        assert window.hit("a", 3, now=100.0) is not None

    def test_a_rejected_request_is_not_counted(self):
        """Otherwise a client that keeps retrying could never come back."""
        window = SlidingWindow(window_seconds=60)
        for _ in range(3):
            window.hit("a", 3, now=100.0)
        for _ in range(50):
            window.hit("a", 3, now=100.0)

        # The window still holds only the three that were accepted, so it frees
        # up exactly 60s after those - not after the last rejected attempt.
        assert window.hit("a", 3, now=160.1) is None

    def test_the_window_slides(self):
        window = SlidingWindow(window_seconds=60)
        for _ in range(3):
            window.hit("a", 3, now=100.0)

        assert window.hit("a", 3, now=130.0) is not None
        assert window.hit("a", 3, now=161.0) is None

    def test_keys_are_independent(self):
        window = SlidingWindow(window_seconds=60)
        for _ in range(3):
            window.hit("a", 3, now=100.0)

        assert window.hit("b", 3, now=100.0) is None

    def test_retry_after_is_when_the_oldest_hit_expires(self):
        window = SlidingWindow(window_seconds=60)
        window.hit("a", 1, now=100.0)

        assert window.hit("a", 1, now=110.0) == pytest.approx(50.0)

    def test_pruning_forgets_idle_keys(self):
        window = SlidingWindow(window_seconds=60)
        window.hit("a", 5, now=100.0)
        window.hit("b", 5, now=200.0)

        window.prune(now=230.0)

        assert "a" not in window._hits
        assert "b" in window._hits


class TestPathClassification:
    def test_llm_backed_paths_are_expensive(self):
        assert is_expensive("/adaptive-interview")
        assert is_expensive("/start-interview")
        assert is_expensive("/cv/upload")

    def test_credential_endpoints_are_expensive_too(self):
        # Not for cost - repeated attempts are the attack.
        assert is_expensive("/login")
        assert is_expensive("/register")

    def test_reads_are_not_expensive(self):
        assert not is_expensive("/my-sessions")
        assert not is_expensive("/session/23")

    def test_health_is_never_throttled(self):
        # A throttled health check reads as an outage to an orchestrator.
        assert is_exempt("/health")


def _with_proxy_trust(monkeypatch, trusted: bool):
    """Settings is a frozen dataclass, so swap the whole object."""
    monkeypatch.setattr(
        rate_limit, "settings", SimpleNamespace(trust_proxy_headers=trusted)
    )


class TestClientKey:
    def test_uses_the_socket_address_by_default(self, monkeypatch):
        _with_proxy_trust(monkeypatch, False)
        request = FakeRequest(host="1.2.3.4", headers={"x-forwarded-for": "9.9.9.9"})

        # Trusting the header without a proxy would let a caller pick its own
        # bucket and walk straight past the limit.
        assert client_key(request) == "1.2.3.4"

    def test_reads_the_forwarded_client_when_behind_a_proxy(self, monkeypatch):
        _with_proxy_trust(monkeypatch, True)
        request = FakeRequest(
            host="10.0.0.1", headers={"x-forwarded-for": "9.9.9.9, 10.0.0.1"}
        )

        assert client_key(request) == "9.9.9.9"

    def test_falls_back_when_there_is_no_client(self, monkeypatch):
        _with_proxy_trust(monkeypatch, False)

        assert client_key(FakeRequest(host=None)) == "unknown"


class TestGlobalCap:
    def test_the_global_window_is_shared_across_callers(self):
        """The per-client limit is best effort; this one caps the bill."""
        window = SlidingWindow(window_seconds=60)
        for _ in range(5):
            assert window.hit("global", 5, now=100.0) is None

        assert window.hit("global", 5, now=100.0) is not None
