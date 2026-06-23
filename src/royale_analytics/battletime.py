from __future__ import annotations

from datetime import datetime, timezone

from royale_analytics.errors import BattleTimeParseError

_BATTLE_TIME_FORMAT = "%Y%m%dT%H%M%S.%fZ"


def parse_battle_time(s: str) -> datetime:
    """Parse the API battleTime string (e.g. '20260502T021910.000Z').

    Returns a timezone-aware datetime in UTC. Raises BattleTimeParseError on
    any value that does not match the '%Y%m%dT%H%M%S.%fZ' format.
    """
    try:
        naive = datetime.strptime(s, _BATTLE_TIME_FORMAT)
    except (ValueError, TypeError) as exc:
        raise BattleTimeParseError(
            f"Could not parse battleTime {s!r} "
            f"(expected format {_BATTLE_TIME_FORMAT})"
        ) from exc
    return naive.replace(tzinfo=timezone.utc)


def to_utc_iso(s: str) -> str:
    """Parse a battleTime string and return its UTC ISO-8601 representation."""
    return parse_battle_time(s).isoformat()
