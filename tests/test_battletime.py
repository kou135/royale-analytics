from __future__ import annotations

from datetime import datetime, timezone

import pytest

from royale_analytics.battletime import parse_battle_time, to_utc_iso
from royale_analytics.errors import BattleTimeParseError


def test_parse_battle_time_returns_tz_aware_utc_datetime():
    result = parse_battle_time("20260502T021910.000Z")
    assert result == datetime(2026, 5, 2, 2, 19, 10, tzinfo=timezone.utc)


def test_parse_battle_time_is_tz_aware():
    result = parse_battle_time("20260502T021910.000Z")
    assert result.tzinfo is not None
    assert result.utcoffset() == timezone.utc.utcoffset(None)


def test_to_utc_iso_roundtrip():
    assert to_utc_iso("20260502T021910.000Z") == "2026-05-02T02:19:10+00:00"


def test_parse_battle_time_bad_input_raises():
    with pytest.raises(BattleTimeParseError):
        parse_battle_time("not-a-time")


def test_to_utc_iso_bad_input_raises():
    with pytest.raises(BattleTimeParseError):
        to_utc_iso("not-a-time")
