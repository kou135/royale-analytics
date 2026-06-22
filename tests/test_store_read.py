from __future__ import annotations

from royale_analytics.store import Store
from tests.factories import (
    GOLEM_DECK,
    HOG_DECK,
    make_battle_view,
    make_profile,
    make_raw_battle,
)


def _new_store() -> Store:
    store = Store(":memory:")
    store.init_schema()
    return store


def test_load_battles_returns_view_shaped_dicts():
    store = _new_store()
    store.upsert_battles(
        "#ME",
        [
            make_raw_battle(
                battle_time="20260502T021910.000Z",
                team_cards=HOG_DECK,
                opp_cards=GOLEM_DECK,
                team_crowns=2,
                opp_crowns=1,
            ),
            make_raw_battle(
                battle_time="20260502T031910.000Z",
                team_cards=HOG_DECK,
                opp_cards=GOLEM_DECK,
                team_crowns=0,
                opp_crowns=2,
                opponent_tag="#OPP2",
            ),
        ],
    )
    battles = store.load_battles("#ME")
    assert len(battles) == 2

    first = battles[0]
    # Top-level shape matches make_battle_view-style dict.
    reference = make_battle_view(
        team_cards=HOG_DECK,
        opp_cards=GOLEM_DECK,
        team_crowns=2,
        opp_crowns=1,
    )
    assert set(reference.keys()) <= set(first.keys())
    assert set(reference["team"].keys()) <= set(first["team"].keys())

    # snake_case card fields are reconstructed.
    assert first["team"]["cards"][0]["elixir_cost"] is not None
    assert "max_level" in first["team"]["cards"][0]
    # is_ladder_tournament is a real bool (not 0/1 int).
    assert isinstance(first["is_ladder_tournament"], bool)
    # result reflects crowns (first battle is a win for team).
    assert first["result"] == "win"
    # opponent deck_key is present.
    assert first["opponent"]["deck_key"]
    assert first["team"]["crowns"] == 2
    assert first["opponent"]["crowns"] == 1


def test_load_battles_ordered_by_battle_time():
    store = _new_store()
    store.upsert_battles(
        "#ME",
        [
            make_raw_battle(
                battle_time="20260502T031910.000Z",
                team_cards=HOG_DECK,
                opp_cards=GOLEM_DECK,
                team_crowns=0,
                opp_crowns=2,
                opponent_tag="#OPP2",
            ),
            make_raw_battle(
                battle_time="20260502T021910.000Z",
                team_cards=HOG_DECK,
                opp_cards=GOLEM_DECK,
                team_crowns=2,
                opp_crowns=1,
            ),
        ],
    )
    battles = store.load_battles("#ME")
    times = [b["battle_time"] for b in battles]
    assert times == sorted(times)


def test_get_latest_profile_returns_none_when_empty():
    store = _new_store()
    assert store.get_latest_profile("#ME") is None


def test_get_latest_profile_returns_most_recent():
    store = _new_store()
    first = make_profile({"Hog Rider": (10, 14)})
    first["trophies"] = 5900
    second = make_profile({"Hog Rider": (11, 14)})
    second["trophies"] = 6100
    store.save_profile_snapshot("#ME", first)
    store.save_profile_snapshot("#ME", second)
    latest = store.get_latest_profile("#ME")
    assert latest is not None
    # Most recently saved snapshot wins (highest id / fetched_at).
    assert latest["trophies"] == 6100
    assert latest["cards"][0]["level"] == 11
