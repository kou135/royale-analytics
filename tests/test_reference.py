from __future__ import annotations

from royale_analytics.reference import Reference, load_reference


def test_load_reference_returns_reference():
    ref = load_reference()
    assert isinstance(ref, Reference)


def test_card_roles_hog_rider_is_wincon():
    ref = load_reference()
    assert ref.card_roles["cards"]["Hog Rider"]["role"] == "wincon"


def test_archetype_rules_siege_cards():
    ref = load_reference()
    assert ref.archetype_rules["siege_cards"] == ["X-Bow", "Mortar"]


def test_template_decks_has_at_least_three_with_hog_cycle():
    ref = load_reference()
    assert len(ref.template_decks) >= 3
    names = [d["name"] for d in ref.template_decks]
    assert "Hog 2.6 Cycle" in names
