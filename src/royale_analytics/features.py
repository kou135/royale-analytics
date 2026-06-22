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


def detect_loss_patterns(battles: list[dict]) -> dict:
    total_losses = 0
    three_crown_losses = 0
    close_losses = 0
    for battle in battles:
        if battle["result"] != "loss":
            continue
        total_losses += 1
        team_crowns = battle["team"]["crowns"]
        opp_crowns = battle["opponent"]["crowns"]
        if team_crowns == 0 and opp_crowns == 3:
            three_crown_losses += 1
        if abs(team_crowns - opp_crowns) == 1:
            close_losses += 1
    return {
        "total_losses": total_losses,
        "three_crown_losses": three_crown_losses,
        "close_losses": close_losses,
    }


def elixir_leaked_summary(battles: list[dict]) -> dict:
    my_values: list[float] = []
    opp_values: list[float] = []
    for battle in battles:
        team_leaked = battle["team"]["elixir_leaked"]
        opp_leaked = battle["opponent"]["elixir_leaked"]
        if team_leaked is None or opp_leaked is None:
            continue
        my_values.append(team_leaked)
        opp_values.append(opp_leaked)
    sample = len(my_values)
    if sample == 0:
        return {"my_avg": None, "opp_avg": None, "delta": None, "sample": 0}
    my_avg = round(sum(my_values) / sample, 2)
    opp_avg = round(sum(opp_values) / sample, 2)
    delta = round(my_avg - opp_avg, 2)
    return {
        "my_avg": my_avg,
        "opp_avg": opp_avg,
        "delta": delta,
        "sample": sample,
    }
