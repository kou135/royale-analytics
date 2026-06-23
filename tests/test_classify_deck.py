from __future__ import annotations

from royale_analytics.classify import DeckClassification, classify_deck
from royale_analytics.reference import load_reference
from tests.factories import GOLEM_DECK, HOG_DECK, make_card


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


def test_spell_only_air_targeting_is_weak_to_air():
    # Deck with no non-spell air-targeting cards: only Fireball (spell).
    # All other cards have no air-targeting tag -> non-spell air-targeting count == 0.
    ref = load_reference()
    spell_only_air_deck = [
        make_card("Hog Rider",        1,  4, rarity="rare"),
        make_card("Ice Golem",        2,  2, rarity="rare"),
        make_card("Skeletons",        3,  1),
        make_card("Knight",           4,  3),
        make_card("Cannon",           5,  3),
        make_card("Fireball",         6,  4, rarity="rare"),
        make_card("The Log",          7,  2, rarity="legendary"),
        make_card("Barbarian Barrel", 8,  2, rarity="epic"),
    ]
    result = classify_deck(spell_only_air_deck, ref)
    assert "weak-to-air" in result.weakness_tags


def test_tornado_no_longer_has_air_targeting_tag():
    ref = load_reference()
    tornado_entry = ref.card_roles["cards"]["Tornado"]
    assert "air-targeting" not in tornado_entry["tags"]
