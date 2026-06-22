from __future__ import annotations

import httpx
import pytest

from royale_analytics.api_client import ApiClient
from royale_analytics.errors import (
    AccessDeniedError,
    ApiServerError,
    MaintenanceError,
    NotFoundError,
    ThrottledError,
)

BASE_URL = "https://proxy.royaleapi.dev/v1"


def make_client(handler, *, max_retries=2, sleep=None):
    """Build an ApiClient backed by an httpx.MockTransport handler (no network)."""
    transport = httpx.MockTransport(handler)
    http_client = httpx.Client(base_url=BASE_URL, transport=transport)
    kwargs = {"client": http_client, "max_retries": max_retries}
    if sleep is not None:
        kwargs["sleep"] = sleep
    return ApiClient("tok-123", BASE_URL, **kwargs)


def test_get_returns_parsed_json_and_sends_bearer_header():
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["authorization"] = request.headers.get("Authorization")
        return httpx.Response(200, json={"tag": "#ME", "name": "Me"})

    client = make_client(handler)
    body = client._get("/players/%23ME")

    assert body == {"tag": "#ME", "name": "Me"}
    assert seen["authorization"] == "Bearer tok-123"


def test_403_raises_access_denied_with_status_and_guidance():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(403, json={"reason": "accessDenied"})

    client = make_client(handler)
    with pytest.raises(AccessDeniedError) as exc:
        client._get("/players/%23ME")

    assert exc.value.status == 403
    assert exc.value.guidance != ""
    assert "45.79.218.79" in exc.value.guidance


def test_404_raises_not_found_with_status_and_guidance():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, json={"reason": "notFound"})

    client = make_client(handler)
    with pytest.raises(NotFoundError) as exc:
        client._get("/players/%23ME")

    assert exc.value.status == 404
    assert exc.value.guidance != ""
    assert "tag" in exc.value.guidance.lower()


def test_503_raises_maintenance_with_status_and_guidance():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(503, json={"reason": "inMaintenance"})

    client = make_client(handler)
    with pytest.raises(MaintenanceError) as exc:
        client._get("/players/%23ME")

    assert exc.value.status == 503
    assert exc.value.guidance != ""
    assert "maintenance" in exc.value.guidance.lower()


def test_500_raises_api_server_error():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, json={"reason": "serverError"})

    client = make_client(handler)
    with pytest.raises(ApiServerError) as exc:
        client._get("/cards")

    assert exc.value.status == 500


def test_one_429_then_200_succeeds_and_sleep_called_with_converted_seconds():
    slept = []
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        if calls["n"] == 1:
            # 1_500_000 microseconds -> 1.5 seconds
            return httpx.Response(
                429,
                headers={"x-ratelimit-retry-after": "1500000"},
                json={"reason": "throttled"},
            )
        return httpx.Response(200, json={"ok": True})

    client = make_client(handler, max_retries=2, sleep=lambda s: slept.append(s))
    body = client._get("/cards")

    assert body == {"ok": True}
    assert slept == [1.5]
    assert calls["n"] == 2


def test_persistent_429_raises_throttled():
    slept = []

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            429,
            headers={"x-ratelimit-retry-after": "500000"},
            json={"reason": "throttled"},
        )

    client = make_client(handler, max_retries=2, sleep=lambda s: slept.append(s))
    with pytest.raises(ThrottledError) as exc:
        client._get("/cards")

    assert exc.value.status == 429
    assert exc.value.guidance != ""
    # 500_000 microseconds -> 0.5 seconds, slept once per retry (max_retries=2)
    assert slept == [0.5, 0.5]
