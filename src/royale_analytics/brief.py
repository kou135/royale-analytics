from __future__ import annotations

import dataclasses

from .features import Features


def render_json(features: Features) -> dict:
    """Convert Features into a JSON-serializable dict.

    Uses dataclasses.asdict, which recursively converts nested dataclasses
    (DeckClassification, DeckMatch, MatchupRow, LevelDeficit, OpponentDeck)
    into plain dicts. None values (e.g. my_deck on an empty history) are
    preserved. The resulting structure contains only dicts, lists, str, int,
    float, bool, and None, so json.dumps(render_json(f)) never raises.
    """
    return dataclasses.asdict(features)
