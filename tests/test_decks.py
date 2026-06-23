from __future__ import annotations

import random

from royale_analytics.decks import average_elixir, compute_deck_key
from tests.factories import GOLEM_DECK, HOG_DECK, make_card


def test_compute_deck_key_hog_deck():
    assert compute_deck_key(HOG_DECK) == "1,2,3,4,5,6,7,8"


def test_compute_deck_key_is_order_independent():
    shuffled = list(HOG_DECK)
    random.Random(1234).shuffle(shuffled)
    assert compute_deck_key(shuffled) == compute_deck_key(HOG_DECK)


def test_compute_deck_key_deduplicates_ids():
    cards = [make_card("A", 5, 3), make_card("B", 5, 2), make_card("C", 1, 4)]
    assert compute_deck_key(cards) == "1,5"


def test_average_elixir_hog_deck():
    assert average_elixir(HOG_DECK) == 2.6


def test_average_elixir_golem_deck():
    assert average_elixir(GOLEM_DECK) == 4.3
