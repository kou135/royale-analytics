from __future__ import annotations

import pytest

from royale_analytics.errors import InvalidTagError
from royale_analytics.tags import VALID_TAG_CHARS, encode_tag, normalize_tag


def test_valid_tag_chars_constant():
    assert VALID_TAG_CHARS == "0289CGJLPQRUVY"


def test_normalize_strips_hash():
    assert normalize_tag("#C0G20PR2") == "C0G20PR2"


def test_normalize_uppercases_input():
    assert normalize_tag("#c0g20pr2") == "C0G20PR2"


def test_normalize_maps_o_to_zero():
    assert normalize_tag("#OPR") == "0PR"


def test_normalize_maps_lowercase_o_to_zero():
    assert normalize_tag("#opr") == "0PR"


def test_normalize_rejects_invalid_char_b():
    with pytest.raises(InvalidTagError):
        normalize_tag("#B0G")


def test_normalize_rejects_invalid_char_i():
    with pytest.raises(InvalidTagError):
        normalize_tag("#I0G")


def test_normalize_rejects_empty():
    with pytest.raises(InvalidTagError):
        normalize_tag("")


def test_normalize_rejects_hash_only():
    with pytest.raises(InvalidTagError):
        normalize_tag("#")


def test_encode_tag_adds_percent_23_and_normalizes():
    assert encode_tag("#c0g") == "%23C0G"
