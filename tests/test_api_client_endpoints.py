from __future__ import annotations

import httpx

from royale_analytics.api_client import ApiClient

BASE_URL = "https://proxy.royaleapi.dev/v1"


def make_client_capturing(captured, response):
    """Build an ApiClient whose MockTransport records the request and returns `response`."""

    def handler(request: httpx.Request) -> httpx.Response:
        captured["path"] = request.url.raw_path.decode()
        return response

    transport = httpx.MockTransport(handler)
    http_client = httpx.Client(base_url=BASE_URL, transport=transport)
    return ApiClient("tok-123", BASE_URL, client=http_client)


def test_get_player_uses_encoded_path_and_returns_dict():
    captured = {}
    client = make_client_capturing(
        captured, httpx.Response(200, json={"tag": "#CGJ", "name": "Me"})
    )
    body = client.get_player("#CGJ")

    assert captured["path"] == "/v1/players/%23CGJ"
    assert body == {"tag": "#CGJ", "name": "Me"}


def test_get_battlelog_uses_encoded_path_and_returns_list():
    captured = {}
    client = make_client_capturing(
        captured, httpx.Response(200, json=[{"type": "PvP"}, {"type": "PvP"}])
    )
    body = client.get_battlelog("#CGJ")

    assert captured["path"] == "/v1/players/%23CGJ/battlelog"
    assert isinstance(body, list)
    assert body == [{"type": "PvP"}, {"type": "PvP"}]


def test_get_upcoming_chests_uses_encoded_path_and_returns_dict():
    captured = {}
    client = make_client_capturing(
        captured, httpx.Response(200, json={"items": [{"name": "Silver Chest"}]})
    )
    body = client.get_upcoming_chests("#CGJ")

    assert captured["path"] == "/v1/players/%23CGJ/upcomingchests"
    assert body == {"items": [{"name": "Silver Chest"}]}


def test_get_cards_uses_cards_path_and_returns_dict():
    captured = {}
    client = make_client_capturing(
        captured, httpx.Response(200, json={"items": [{"name": "Hog Rider"}]})
    )
    body = client.get_cards()

    assert captured["path"] == "/v1/cards"
    assert body == {"items": [{"name": "Hog Rider"}]}


def test_get_player_normalizes_o_to_zero_in_path():
    captured = {}
    client = make_client_capturing(
        captured, httpx.Response(200, json={"tag": "#0CG"})
    )
    # 'O' normalizes to '0' via encode_tag; '#' is stripped then re-added as %23.
    client.get_player("#OCG")

    assert captured["path"] == "/v1/players/%230CG"
