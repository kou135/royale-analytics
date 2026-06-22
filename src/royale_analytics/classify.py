from __future__ import annotations

from dataclasses import dataclass

from royale_analytics.decks import average_elixir
from royale_analytics.reference import Reference

_ROLE_KEYS = ("wincon", "support", "defense", "cycle", "spell")


@dataclass
class DeckClassification:
    archetype: str
    avg_elixir: float
    role_counts: dict
    weakness_tags: list[str]
    card_names: list[str]


@dataclass
class DeckMatch:
    name: str | None
    confidence: str
    overlap: int
    archetype: str | None


def _card_roles(cards: list[dict], reference: Reference) -> list[str]:
    roles_table = reference.card_roles["cards"]
    out = []
    for c in cards:
        entry = roles_table.get(c["name"])
        out.append(entry["role"] if entry else "")
    return out


def _card_tags(cards: list[dict], reference: Reference) -> list[list[str]]:
    roles_table = reference.card_roles["cards"]
    out = []
    for c in cards:
        entry = roles_table.get(c["name"])
        out.append(list(entry["tags"]) if entry else [])
    return out


def _archetype(cards: list[dict], avg: float, reference: Reference) -> str:
    rules = reference.archetype_rules
    names = {c["name"] for c in cards}

    if names & set(rules["siege_cards"]):
        return "siege"
    if (names & set(rules["tank_cards"])) and avg >= rules["beatdown_min_avg_elixir"]:
        return "beatdown"
    if len(names & set(rules["bridge_spam_cards"])) >= 2:
        return "bridge_spam"
    if avg <= rules["cycle_max_avg_elixir"]:
        return "cycle"
    return "control"


def _role_counts(roles: list[str]) -> dict:
    counts = {key: 0 for key in _ROLE_KEYS}
    for role in roles:
        if role in counts:
            counts[role] += 1
    return counts


def _weakness_tags(roles: list[str], tags: list[list[str]]) -> list[str]:
    flat_tags = [t for card_tags in tags for t in card_tags]
    air_targeting = sum(
        1
        for role, card_tags in zip(roles, tags)
        if "air-targeting" in card_tags and role != "spell"
    )
    splash = sum(1 for t in flat_tags if t == "splash")
    building = sum(1 for t in flat_tags if t == "building")
    spell_count = sum(1 for role in roles if role == "spell")
    wincon_count = sum(1 for role in roles if role == "wincon")

    out: list[str] = []
    if air_targeting <= 1:
        out.append("weak-to-air")
    if splash == 0:
        out.append("weak-to-swarm")
    if spell_count == 0:
        out.append("spell-light")
    if wincon_count == 0:
        out.append("no-win-condition")
    elif wincon_count == 1:
        out.append("single-win-condition")
    if building == 0:
        out.append("no-building-defense")
    return out


def classify_deck(cards: list[dict], reference: Reference) -> DeckClassification:
    avg = average_elixir(cards)
    roles = _card_roles(cards, reference)
    tags = _card_tags(cards, reference)
    return DeckClassification(
        archetype=_archetype(cards, avg, reference),
        avg_elixir=avg,
        role_counts=_role_counts(roles),
        weakness_tags=_weakness_tags(roles, tags),
        card_names=[c["name"] for c in cards],
    )


def match_deck(
    cards: list[dict], reference: Reference, *, variant_threshold: int = 6
) -> DeckMatch:
    """
    Match a deck against template decks by card-name set overlap.

    Ties (e.g., two templates with equal overlap) resolve to the first-iterated
    template via strict '>' comparison in the loop.
    """
    observed = {c["name"] for c in cards}

    best_template: dict | None = None
    best_overlap = -1
    for template in reference.template_decks:
        overlap = len(observed & set(template["cards"]))
        if overlap > best_overlap:
            best_overlap = overlap
            best_template = template

    if best_template is None:
        return DeckMatch(name=None, confidence="unknown", overlap=0, archetype=None)

    if best_overlap == 8:
        confidence = "exact"
    elif best_overlap >= variant_threshold:
        confidence = "variant"
    else:
        confidence = "unknown"

    if confidence == "unknown":
        return DeckMatch(
            name=None, confidence="unknown", overlap=best_overlap, archetype=None
        )

    return DeckMatch(
        name=best_template["name"],
        confidence=confidence,
        overlap=best_overlap,
        archetype=best_template["archetype"],
    )
