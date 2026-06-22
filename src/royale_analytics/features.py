from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime

from .classify import DeckClassification, classify_deck
from .reference import Reference

_OTHER_MODE_TOKENS = ("Tournament", "Challenge", "Friendly")


@dataclass
class MatchupRow:
    opponent_archetype: str
    mode: str
    wins: int
    losses: int
    draws: int


def mode_of(battle: dict) -> str:
    game_mode_name = battle.get("game_mode_name") or ""
    if battle.get("is_ladder_tournament") or any(
        token in game_mode_name for token in _OTHER_MODE_TOKENS
    ):
        return "other"
    league_number = battle.get("league_number")
    if isinstance(league_number, int) and league_number >= 1:
        return "ranked"
    return "ladder"


def current_deck(battles: list[dict]) -> list[dict] | None:
    if not battles:
        return None
    latest = max(battles, key=lambda b: datetime.fromisoformat(b["battle_time"]))
    return latest["team"]["cards"]


def derive_matchups(battles: list[dict], reference: Reference) -> list[MatchupRow]:
    tallies: dict[tuple[str, str], dict[str, int]] = defaultdict(
        lambda: {"wins": 0, "losses": 0, "draws": 0}
    )
    for battle in battles:
        opp_classification: DeckClassification = classify_deck(
            battle["opponent"]["cards"], reference
        )
        key = (opp_classification.archetype, mode_of(battle))
        result = battle["result"]
        if result == "win":
            tallies[key]["wins"] += 1
        elif result == "loss":
            tallies[key]["losses"] += 1
        else:
            tallies[key]["draws"] += 1
    rows = [
        MatchupRow(
            opponent_archetype=archetype,
            mode=mode,
            wins=counts["wins"],
            losses=counts["losses"],
            draws=counts["draws"],
        )
        for (archetype, mode), counts in tallies.items()
    ]
    rows.sort(key=lambda r: (r.opponent_archetype, r.mode))
    return rows
