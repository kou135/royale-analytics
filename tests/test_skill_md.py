from __future__ import annotations

from pathlib import Path

SKILL_PATH = (
    Path(__file__).resolve().parent.parent
    / ".claude" / "skills" / "royale-analyzer" / "SKILL.md"
)


def test_skill_md_exists():
    assert SKILL_PATH.is_file(), f"SKILL.md not found at {SKILL_PATH}"


def test_skill_md_contains_required_substrings():
    text = SKILL_PATH.read_text(encoding="utf-8")
    for needle in [
        "royale-analyzer",
        "ra fetch",
        "ra analyze",
        "局所解",
        "推測",
        "not endorsed by Supercell",
    ]:
        assert needle in text, f"missing substring: {needle!r}"
