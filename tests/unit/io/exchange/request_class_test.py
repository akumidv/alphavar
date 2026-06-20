import httpx
import pytest

from alphavar.io.exchange._abstract_exchange import RequestClass
from alphavar.io.exchange.exchange_exception import APIException, RequestException


def _client_with(handler) -> RequestClass:
    rc = RequestClass("https://example.com")
    rc.session = httpx.Client(transport=httpx.MockTransport(handler))
    return rc


@pytest.fixture(autouse=True)
def _no_sleep(monkeypatch):
    # Avoid real backoff delays in tests.
    monkeypatch.setattr("alphavar.io.exchange._abstract_exchange.time.sleep", lambda *_: None)


def test_signed_request_not_implemented():
    rc = RequestClass("https://example.com")
    with pytest.raises(NotImplementedError):
        rc.request_api("/x", signed=True)


def test_success_returns_json():
    rc = _client_with(lambda req: httpx.Response(200, json={"ok": 1}))
    assert rc.request_api("/x") == {"ok": 1}


def test_retries_then_succeeds_on_429():
    calls = {"n": 0}

    def handler(req):
        calls["n"] += 1
        if calls["n"] < 3:
            return httpx.Response(429, headers={"Retry-After": "0"})
        return httpx.Response(200, json={"ok": True})

    rc = _client_with(handler)
    assert rc.request_api("/x") == {"ok": True}
    assert calls["n"] == 3


def test_retries_exhausted_raises_apiexception_on_5xx():
    calls = {"n": 0}

    def handler(req):
        calls["n"] += 1
        return httpx.Response(503)

    rc = _client_with(handler)
    with pytest.raises(APIException):
        rc.request_api("/x")
    assert calls["n"] == rc.MAX_RETRIES + 1


def test_transport_error_retried_then_raises_requestexception():
    calls = {"n": 0}

    def handler(req):
        calls["n"] += 1
        raise httpx.ConnectError("boom")

    rc = _client_with(handler)
    with pytest.raises(RequestException):
        rc.request_api("/x")
    assert calls["n"] == rc.MAX_RETRIES + 1


def test_non_retryable_4xx_raises_immediately():
    calls = {"n": 0}

    def handler(req):
        calls["n"] += 1
        return httpx.Response(404, text="not found")

    rc = _client_with(handler)
    with pytest.raises(APIException):
        rc.request_api("/x")
    assert calls["n"] == 1  # 404 is not retried
