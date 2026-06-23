from __future__ import annotations

from royale_analytics.errors import InvalidTagError

VALID_TAG_CHARS: str = "0289CGJLPQRUVY"


def normalize_tag(raw: str) -> str:
    """Normalize a player tag: strip '#', uppercase, map 'O'->'0', validate.

    Raises InvalidTagError if the tag is empty or contains a character that is
    not in VALID_TAG_CHARS (after O->0 substitution).
    """
    tag = raw.strip().lstrip("#").upper().replace("O", "0")
    if not tag:
        raise InvalidTagError(f"Empty tag after normalization: {raw!r}")
    for ch in tag:
        if ch not in VALID_TAG_CHARS:
            raise InvalidTagError(
                f"Invalid character {ch!r} in tag {raw!r}; "
                f"valid characters are {VALID_TAG_CHARS}"
            )
    return tag


def encode_tag(raw: str) -> str:
    """Return the URL-safe tag for an API path: '%23' + normalized tag."""
    return "%23" + normalize_tag(raw)
