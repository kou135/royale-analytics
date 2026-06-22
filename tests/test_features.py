from __future__ import annotations

from royale_analytics.features import (
    MatchupRow,
    current_deck,
    derive_matchups,
    mode_of,
)
from royale_analytics.reference import load_reference
from tests.factories import GOLEM_DECK, HOG_DECK, make_battle_view


def test_mode_of_ladder():
    battle = make_battle_view(
        team_cards=HOG_DECK, opp_cards=GOLEM_DECK,
        team_crowns=1, opp_crowns=0,
        mode_fields={"game_mode_name": "Ladder",
                     "is_ladder_tournament": False, "league_number": None},
    )
    assert mode_of(battle) == "ladder"


def test_mode_of_ranked_by_league_number():
    battle = make_battle_view(
        team_cards=HOG_DECK, opp_cards=GOLEM_DECK,
        team_crowns=1, opp_crowns=0,
        mode_fields={"game_mode_name": "Ranked",
                     "is_ladder_tournament": False, "league_number": 5},
    )
    assert mode_of(battle) == "ranked"


def test_mode_of_other_when_ladder_tournament():
    battle = make_battle_view(
        team_cards=HOG_DECK, opp_cards=GOLEM_DECK,
        team_crowns=1, opp_crowns=0,
        mode_fields={"game_mode_name": "Some Challenge",
                     "is_ladder_tournament": True, "league_number": None},
    )
    assert mode_of(battle) == "other"


def test_current_deck_empty_returns_none():
    assert current_deck([]) is None


def test_current_deck_returns_most_recent_team_cards():
    older = make_battle_view(
        team_cards=GOLEM_DECK, opp_cards=HOG_DECK,
        team_crowns=0, opp_crowns=3,
        battle_time="2026-05-01T00:00:00+00:00",
    )
    newer = make_battle_view(
        team_cards=HOG_DECK, opp_cards=GOLEM_DECK,
        team_crowns=3, opp_crowns=0,
        battle_time="2026-05-02T00:00:00+00:00",
    )
    deck = current_deck([older, newer])
    assert deck == HOG_DECK


def test_derive_matchups_groups_by_opponent_archetype_and_mode():
    ref = load_reference()
    battles = [
        # loss vs Golem/beatdown opponent (ladder)
        make_battle_view(
            team_cards=HOG_DECK, opp_cards=GOLEM_DECK,
            team_crowns=0, opp_crowns=3,
            battle_time="2026-05-01T00:00:00+00:00",
        ),
        # loss vs Golem/beatdown opponent (ladder)
        make_battle_view(
            team_cards=HOG_DECK, opp_cards=GOLEM_DECK,
            team_crowns=1, opp_crowns=2,
            battle_time="2026-05-01T01:00:00+00:00",
        ),
        # win vs Hog/cycle opponent (ladder)
        make_battle_view(
            team_cards=GOLEM_DECK, opp_cards=HOG_DECK,
            team_crowns=3, opp_crowns=0,
            battle_time="2026-05-01T02:00:00+00:00",
        ),
    ]
    rows = derive_matchups(battles, ref)

    beatdown = next(
        r for r in rows
        if r.opponent_archetype == "beatdown" and r.mode == "ladder"
    )
    assert beatdown.losses == 2
    assert beatdown.wins == 0
    assert beatdown.draws == 0

    cycle = next(
        r for r in rows
        if r.opponent_archetype == "cycle" and r.mode == "ladder"
    )
    assert cycle.wins == 1
    assert cycle.losses == 0
    assert cycle.draws == 0
