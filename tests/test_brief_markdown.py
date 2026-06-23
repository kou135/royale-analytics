from __future__ import annotations

from royale_analytics.brief import render_markdown
from royale_analytics.features import build_features
from royale_analytics.reference import load_reference
from tests.factories import HOG_DECK, GOLEM_DECK, make_battle_view


def _battles(n):
    out = []
    for i in range(n):
        team_crowns, opp_crowns = (2, 1) if i % 2 == 0 else (0, 3)
        out.append(make_battle_view(team_cards=HOG_DECK, opp_cards=GOLEM_DECK,
                                    team_crowns=team_crowns, opp_crowns=opp_crowns))
    return out


def test_render_markdown_contains_core_sections_and_archetype():
    ref = load_reference()
    features = build_features(_battles(12), None, ref)
    md = render_markdown(features)
    assert isinstance(md, str)
    assert "あなたのデッキ" in md
    assert "相性表" in md
    assert "負け方パターン" in md
    assert "レベル差" in md
    assert "elixirLeaked" in md
    assert "頻出相手デッキ" in md
    # my_deck archetype must appear (HOG_DECK classifies as "cycle").
    assert features.my_deck is not None
    assert features.my_deck.archetype in md


def test_render_markdown_marks_guess_not_measured():
    ref = load_reference()
    features = build_features(_battles(12), None, ref)
    md = render_markdown(features)
    assert "推測" in md
    # elixirLeaked / 立ち回り must NOT be presented as 実測.
    assert "elixirLeaked（実測）" not in md
    assert "立ち回り（実測）" not in md


def test_render_markdown_small_sample_warning():
    ref = load_reference()
    features = build_features(_battles(3), None, ref)  # sample_size < 10
    md = render_markdown(features)
    assert features.sample_size < 10
    assert "標本が少" in md


def test_render_markdown_empty_features_renders_with_no_data_note():
    ref = load_reference()
    features = build_features([], None, ref)
    md = render_markdown(features)  # must not raise
    assert isinstance(md, str)
    assert features.sample_size == 0
    assert features.my_deck is None
    # Core sections still present.
    assert "あなたのデッキ" in md
    # Notes that there is no data / no battles.
    assert ("データがない" in md) or ("試合がない" in md)


def test_render_markdown_emits_gap_warning():
    ref = load_reference()
    battles = [make_battle_view(team_cards=HOG_DECK, opp_cards=GOLEM_DECK,
                                team_crowns=0, opp_crowns=1,
                                battle_time=f"2026-05-02T02:19:{i:02d}+00:00")
               for i in range(25)]
    feats = build_features(battles, None, ref)
    assert feats.gap_warning is True
    md = render_markdown(feats)
    assert "取りこぼし（ギャップ）の疑いがあります。" in md
