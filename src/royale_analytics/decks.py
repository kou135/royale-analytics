from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal


def compute_deck_key(cards: list[dict]) -> str:
    """Return a stable group key for a deck: card ids ascending, unique, comma-joined.

    Order-independent (sorted) and de-duplicated so the same 8 cards always
    yield the same key regardless of the order they appear in the battlelog.
    """
    ids = sorted({card["id"] for card in cards})
    return ",".join(str(i) for i in ids)


def average_elixir(cards: list[dict]) -> float:
    """Return the mean elixir cost of the cards, rounded to one decimal place.

    Uses half-up rounding (not banker's rounding) so 4.25 -> 4.3, matching the
    template_decks reference values.
    """
    if not cards:
        return 0.0
    mean = Decimal(sum(card["elixir_cost"] for card in cards)) / Decimal(len(cards))
    return float(mean.quantize(Decimal("0.1"), rounding=ROUND_HALF_UP))
