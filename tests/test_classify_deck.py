from __future__ import annotations

from royale_analytics.classify import DeckClassification, classify_deck
from royale_analytics.reference import load_reference
from tests.factories import GOLEM_DECK, HOG_DECK


def test_hog_deck_is_cycle():
    ref = load_reference()
    result = classify_deck(HOG_DECK, ref)
    assert isinstance(result, DeckClassification)
    assert result.archetype == "cycle"
    assert result.avg_elixir == 2.6


def test_hog_deck_role_counts_one_wincon():
    ref = load_reference()
    result = classify_deck(HOG_DECK, ref)
    assert result.role_counts["wincon"] == 1


def test_hog_deck_weakness_tags():
    ref = load_reference()
    result = classify_deck(HOG_DECK, ref)
    # Hog deck has 3 air-targeting cards (Ice Spirit, Musketeer, Fireball)
    assert "weak-to-air" not in result.weakness_tags
    assert "single-win-condition" in result.weakness_tags


def test_golem_deck_is_beatdown_no_building_defense():
    ref = load_reference()
    result = classify_deck(GOLEM_DECK, ref)
    assert result.archetype == "beatdown"
    assert "no-building-defense" in result.weakness_tags
