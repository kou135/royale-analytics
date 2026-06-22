from __future__ import annotations

import json

from royale_analytics.brief import render_json
from royale_analytics.features import build_features
from royale_analytics.reference import load_reference
from tests.factories import HOG_DECK, GOLEM_DECK, make_battle_view


def _battles():
    return [
        make_battle_view(team_cards=HOG_DECK, opp_cards=GOLEM_DECK,
                         team_crowns=2, opp_crowns=1),
        make_battle_view(team_cards=HOG_DECK, opp_cards=GOLEM_DECK,
                         team_crowns=0, opp_crowns=3),
        make_battle_view(team_cards=HOG_DECK, opp_cards=GOLEM_DECK,
                         team_crowns=1, opp_crowns=2),
    ]


def test_render_json_returns_dict_with_top_level_keys():
    ref = load_reference()
    features = build_features(_battles(), None, ref)
    out = render_json(features)
    assert isinstance(out, dict)
    for key in ("my_deck", "matchups", "sample_size"):
        assert key in out


def test_render_json_my_deck_is_dict_with_archetype():
    ref = load_reference()
    features = build_features(_battles(), None, ref)
    out = render_json(features)
    assert isinstance(out["my_deck"], dict)
    assert "archetype" in out["my_deck"]


def test_render_json_matchups_is_list_of_dicts():
    ref = load_reference()
    features = build_features(_battles(), None, ref)
    out = render_json(features)
    assert isinstance(out["matchups"], list)
    for row in out["matchups"]:
        assert isinstance(row, dict)
        assert "opponent_archetype" in row


def test_render_json_is_json_serializable():
    ref = load_reference()
    features = build_features(_battles(), None, ref)
    out = render_json(features)
    # Must not raise.
    dumped = json.dumps(out)
    assert isinstance(dumped, str)


def test_render_json_my_deck_none_when_empty():
    ref = load_reference()
    result = render_json(build_features([], None, ref))
    assert result["my_deck"] is None
    assert result["my_deck_match"] is None
    assert result["sample_size"] == 0
    # Must not raise.
    dumped = json.dumps(result)
    assert isinstance(dumped, str)
