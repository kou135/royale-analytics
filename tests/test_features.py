from __future__ import annotations

from royale_analytics.features import (
    MatchupRow,
    current_deck,
    derive_matchups,
    mode_of,
    detect_loss_patterns,
    elixir_leaked_summary,
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


def test_detect_loss_patterns_counts_three_crown_and_close():
    battles = [
        # three-crown loss (0-3): also counts? abs diff == 3, so NOT close
        make_battle_view(
            team_cards=HOG_DECK, opp_cards=GOLEM_DECK,
            team_crowns=0, opp_crowns=3,
        ),
        # close loss (1-2): abs diff == 1
        make_battle_view(
            team_cards=HOG_DECK, opp_cards=GOLEM_DECK,
            team_crowns=1, opp_crowns=2,
        ),
        # a win (not a loss)
        make_battle_view(
            team_cards=HOG_DECK, opp_cards=GOLEM_DECK,
            team_crowns=3, opp_crowns=0,
        ),
    ]
    patterns = detect_loss_patterns(battles)
    assert patterns == {
        "total_losses": 2,
        "three_crown_losses": 1,
        "close_losses": 1,
    }


def test_elixir_leaked_summary_averages_only_complete_battles():
    battles = [
        make_battle_view(
            team_cards=HOG_DECK, opp_cards=GOLEM_DECK,
            team_crowns=1, opp_crowns=0,
            team_elixir_leaked=3.0, opp_elixir_leaked=2.0,
        ),
        make_battle_view(
            team_cards=HOG_DECK, opp_cards=GOLEM_DECK,
            team_crowns=0, opp_crowns=1,
            team_elixir_leaked=5.0, opp_elixir_leaked=4.0,
        ),
        # excluded: team leaked is None
        make_battle_view(
            team_cards=HOG_DECK, opp_cards=GOLEM_DECK,
            team_crowns=1, opp_crowns=1,
            team_elixir_leaked=None, opp_elixir_leaked=4.0,
        ),
        # excluded: opp leaked is None
        make_battle_view(
            team_cards=HOG_DECK, opp_cards=GOLEM_DECK,
            team_crowns=1, opp_crowns=1,
            team_elixir_leaked=4.0, opp_elixir_leaked=None,
        ),
    ]
    summary = elixir_leaked_summary(battles)
    assert summary == {
        "my_avg": 4.0,
        "opp_avg": 3.0,
        "delta": 1.0,
        "sample": 2,
    }


def test_elixir_leaked_summary_no_complete_battles():
    battles = [
        make_battle_view(
            team_cards=HOG_DECK, opp_cards=GOLEM_DECK,
            team_crowns=1, opp_crowns=0,
            team_elixir_leaked=None, opp_elixir_leaked=None,
        ),
    ]
    summary = elixir_leaked_summary(battles)
    assert summary == {
        "my_avg": None,
        "opp_avg": None,
        "delta": None,
        "sample": 0,
    }


from royale_analytics.features import (  # noqa: E402
    LevelDeficit,
    OpponentDeck,
    detect_level_deficits,
    frequent_opponent_decks,
)
from tests.factories import make_profile  # noqa: E402


def test_detect_level_deficits_for_under_leveled_card_in_deck():
    profile = make_profile({"Hog Rider": (11, 14), "Cannon": (14, 14)})
    deficits = detect_level_deficits(profile, HOG_DECK)
    assert isinstance(deficits, list)
    hog = next(d for d in deficits if d.card_name == "Hog Rider")
    assert hog == LevelDeficit(
        card_name="Hog Rider", level=11, max_level=14, deficit=3
    )
    # Cannon is maxed (14/14): no deficit row
    assert all(d.card_name != "Cannon" for d in deficits)


def test_detect_level_deficits_none_inputs_return_empty():
    assert detect_level_deficits(None, HOG_DECK) == []
    assert detect_level_deficits(make_profile({"Hog Rider": (11, 14)}), None) == []
    assert detect_level_deficits(None, None) == []


def test_frequent_opponent_decks_counts_and_classifies():
    ref = load_reference()
    battles = [
        # vs same Golem deck (loss)
        make_battle_view(
            team_cards=HOG_DECK, opp_cards=GOLEM_DECK,
            team_crowns=0, opp_crowns=3,
            battle_time="2026-05-01T00:00:00+00:00",
        ),
        # vs same Golem deck (win)
        make_battle_view(
            team_cards=HOG_DECK, opp_cards=GOLEM_DECK,
            team_crowns=2, opp_crowns=1,
            battle_time="2026-05-01T01:00:00+00:00",
        ),
        # vs a Hog deck (win)
        make_battle_view(
            team_cards=GOLEM_DECK, opp_cards=HOG_DECK,
            team_crowns=3, opp_crowns=0,
            battle_time="2026-05-01T02:00:00+00:00",
        ),
    ]
    decks = frequent_opponent_decks(battles, ref, top=5)
    assert isinstance(decks[0], OpponentDeck)
    first = decks[0]
    assert first.count == 2
    assert first.archetype == "beatdown"
    assert first.wins == 1
    assert first.losses == 1
    assert "Golem" in first.sample_names


from royale_analytics.features import Features, build_features  # noqa: E402


def test_build_features_empty_battles():
    ref = load_reference()
    features = build_features([], None, ref)
    assert isinstance(features, Features)
    assert features.my_deck is None
    assert features.my_deck_match is None
    assert features.matchups == []
    assert features.level_deficits == []
    assert features.frequent_opponent_decks == []
    assert features.sample_size == 0
    assert features.gap_warning is False
    assert features.modes_present == []
    assert features.loss_patterns == {
        "total_losses": 0,
        "three_crown_losses": 0,
        "close_losses": 0,
    }
    assert features.elixir_leaked == {
        "my_avg": None,
        "opp_avg": None,
        "delta": None,
        "sample": 0,
    }


def test_build_features_populated():
    ref = load_reference()
    profile = make_profile({"Hog Rider": (11, 14), "Cannon": (14, 14)})
    battles = [
        make_battle_view(
            team_cards=HOG_DECK, opp_cards=GOLEM_DECK,
            team_crowns=0, opp_crowns=3,
            battle_time="2026-05-01T00:00:00+00:00",
            mode_fields={"game_mode_name": "Ladder",
                         "is_ladder_tournament": False, "league_number": None},
        ),
        make_battle_view(
            team_cards=HOG_DECK, opp_cards=GOLEM_DECK,
            team_crowns=2, opp_crowns=1,
            battle_time="2026-05-02T00:00:00+00:00",
            mode_fields={"game_mode_name": "Ranked",
                         "is_ladder_tournament": False, "league_number": 5},
        ),
    ]
    features = build_features(battles, profile, ref)
    # current_deck is the most-recent battle's team (HOG_DECK) -> cycle
    assert features.my_deck is not None
    assert features.my_deck.archetype == "cycle"
    assert features.sample_size == 2
    assert features.modes_present == ["ladder", "ranked"]
    # level deficit from profile against the current (Hog) deck
    assert any(d.card_name == "Hog Rider" for d in features.level_deficits)
