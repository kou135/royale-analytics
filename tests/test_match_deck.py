from __future__ import annotations

from royale_analytics.classify import DeckMatch, match_deck
from royale_analytics.reference import load_reference
from tests.factories import HOG_DECK, make_card


def test_exact_match_hog():
    ref = load_reference()
    result = match_deck(HOG_DECK, ref)
    assert isinstance(result, DeckMatch)
    assert result.confidence == "exact"
    assert result.name == "Hog 2.6 Cycle"
    assert result.overlap == 8
    assert result.archetype == "cycle"


def test_variant_match_hog_six_of_eight():
    ref = load_reference()
    # Replace two HOG_DECK cards (Cannon, Skeletons) with off-deck cards.
    variant = [
        c for c in HOG_DECK if c["name"] not in ("Cannon", "Skeletons")
    ] + [
        make_card("Archers", 8, 3, rarity="common"),
        make_card("Knight", 4, 3, rarity="common"),
    ]
    result = match_deck(variant, ref)
    assert result.confidence == "variant"
    assert result.name == "Hog 2.6 Cycle"
    assert result.overlap == 6
    assert result.archetype == "cycle"


def test_unknown_match_unrelated_cards():
    ref = load_reference()
    unrelated = [
        make_card("Goblin Barrel", 101, 3),
        make_card("Princess", 102, 3),
        make_card("Goblin Gang", 103, 3),
        make_card("Inferno Tower", 104, 5),
        make_card("Rocket", 105, 6),
        make_card("Bats", 106, 2),
        make_card("Tesla Trooper", 107, 4),
        make_card("Dart Goblin", 108, 3),
    ]
    result = match_deck(unrelated, ref)
    assert result.confidence == "unknown"
    assert result.name is None
    assert result.archetype is None
