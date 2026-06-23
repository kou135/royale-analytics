from __future__ import annotations

import json

from royale_analytics.store import Store
from tests.factories import GOLEM_DECK, HOG_DECK, make_profile, make_raw_battle


def _new_store() -> Store:
    store = Store(":memory:")
    store.init_schema()
    return store


def test_upsert_two_distinct_battles_returns_two():
    store = _new_store()
    battlelog = [
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
    ]
    assert store.upsert_battles("#ME", battlelog) == 2


def test_upsert_is_idempotent():
    store = _new_store()
    battlelog = [
        make_raw_battle(
            team_cards=HOG_DECK,
            opp_cards=GOLEM_DECK,
            team_crowns=2,
            opp_crowns=1,
        ),
    ]
    assert store.upsert_battles("#ME", battlelog) == 1
    # Re-inserting the same list adds nothing.
    assert store.upsert_battles("#ME", battlelog) == 0


def test_loss_result_for_zero_vs_two_crowns():
    store = _new_store()
    store.upsert_battles(
        "#ME",
        [
            make_raw_battle(
                team_cards=HOG_DECK,
                opp_cards=GOLEM_DECK,
                team_crowns=0,
                opp_crowns=2,
            )
        ],
    )
    row = store.conn.execute("SELECT result FROM battles").fetchone()
    assert row[0] == "loss"


def test_battle_cards_has_sixteen_snake_case_rows():
    store = _new_store()
    store.upsert_battles(
        "#ME",
        [
            make_raw_battle(
                team_cards=HOG_DECK,
                opp_cards=GOLEM_DECK,
                team_crowns=2,
                opp_crowns=1,
            )
        ],
    )
    rows = store.conn.execute(
        "SELECT card_name, max_level, elixir_cost, evolution_level "
        "FROM battle_cards"
    ).fetchall()
    assert len(rows) == 16  # 8 cards x 2 sides
    # snake_case fields are populated (elixir_cost present, not null).
    for card_name, max_level, elixir_cost, _evo in rows:
        assert isinstance(card_name, str) and card_name
        assert max_level is not None
        assert elixir_cost is not None
    # Hog Rider costs 4 elixir per the HOG_DECK factory.
    hog = store.conn.execute(
        "SELECT elixir_cost FROM battle_cards WHERE card_name='Hog Rider'"
    ).fetchone()
    assert hog[0] == 4


def test_save_profile_snapshot_writes_row():
    store = _new_store()
    profile = make_profile({"Hog Rider": (11, 14)})
    store.save_profile_snapshot("#ME", profile)
    count = store.conn.execute(
        "SELECT COUNT(*) FROM profile_snapshots WHERE player_tag='#ME'"
    ).fetchone()[0]
    assert count == 1


def test_record_fetch_stores_gap_as_int():
    store = _new_store()
    store.record_fetch("#ME", new_battles=3, gap_suspected=True)
    store.record_fetch("#ME", new_battles=0, gap_suspected=False)
    rows = store.conn.execute(
        "SELECT new_battles, gap_suspected FROM fetch_log ORDER BY id"
    ).fetchall()
    assert rows[0] == (3, 1)
    assert rows[1] == (0, 0)


def test_upsert_skips_unparseable_battletime(tmp_path):
    from royale_analytics.store import Store
    from tests.factories import make_raw_battle, HOG_DECK, GOLEM_DECK
    s = Store(str(tmp_path / "db.sqlite"))
    s.init_schema()
    good = make_raw_battle(team_cards=HOG_DECK, opp_cards=GOLEM_DECK,
                           team_crowns=1, opp_crowns=0, opponent_tag="#A")
    bad = make_raw_battle(team_cards=HOG_DECK, opp_cards=GOLEM_DECK,
                          team_crowns=0, opp_crowns=1, opponent_tag="#B")
    bad["battleTime"] = "not-a-time"
    assert s.upsert_battles("#ME", [good, bad]) == 1


def test_upsert_skips_malformed_battle(tmp_path):
    """A battle with a card dict missing 'elixirCost' is skipped; the good one is stored."""
    from royale_analytics.store import Store
    from tests.factories import make_raw_battle, HOG_DECK, GOLEM_DECK
    import copy
    s = Store(str(tmp_path / "db.sqlite"))
    s.init_schema()
    good = make_raw_battle(team_cards=HOG_DECK, opp_cards=GOLEM_DECK,
                           team_crowns=2, opp_crowns=0, opponent_tag="#GOOD")
    malformed = copy.deepcopy(
        make_raw_battle(team_cards=HOG_DECK, opp_cards=GOLEM_DECK,
                        team_crowns=1, opp_crowns=0, opponent_tag="#BAD",
                        battle_time="20260502T041910.000Z")
    )
    # Remove elixirCost from one card to trigger KeyError in _to_card_dict.
    del malformed["team"][0]["cards"][0]["elixirCost"]
    result = s.upsert_battles("#ME", [good, malformed])
    assert result == 1
    count = s.conn.execute("SELECT COUNT(*) FROM battles").fetchone()[0]
    assert count == 1


def test_upsert_skips_2v2_battles(tmp_path):
    """A 2v2 battle (team/opponent arrays of length 2) is skipped; only the 1v1 is stored."""
    from royale_analytics.store import Store
    from tests.factories import make_raw_battle, HOG_DECK, GOLEM_DECK
    import copy
    s = Store(str(tmp_path / "db.sqlite"))
    s.init_schema()
    good = make_raw_battle(team_cards=HOG_DECK, opp_cards=GOLEM_DECK,
                           team_crowns=1, opp_crowns=0, opponent_tag="#GOOD1V1")
    twov2 = copy.deepcopy(
        make_raw_battle(team_cards=HOG_DECK, opp_cards=GOLEM_DECK,
                        team_crowns=2, opp_crowns=1, opponent_tag="#2V2A",
                        battle_time="20260502T051910.000Z")
    )
    # Make it a 2v2 by duplicating both sides.
    twov2["team"] = twov2["team"] + copy.deepcopy(twov2["team"])
    twov2["opponent"] = twov2["opponent"] + copy.deepcopy(twov2["opponent"])
    result = s.upsert_battles("#ME", [good, twov2])
    assert result == 1
    count = s.conn.execute("SELECT COUNT(*) FROM battles").fetchone()[0]
    assert count == 1
