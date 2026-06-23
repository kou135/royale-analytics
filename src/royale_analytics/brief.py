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


def _fmt_opt(value: object) -> str:
    """Render an optional number/None for display."""
    if value is None:
        return "不明"
    return str(value)


def _render_my_deck(features: Features) -> list[str]:
    lines: list[str] = ["## あなたのデッキ", ""]
    deck = features.my_deck
    if deck is None:
        lines.append("デッキを判定できる試合がないため、デッキ情報はありません。")
        lines.append("")
        return lines
    lines.append(f"- アーキタイプ: {deck.archetype}")
    lines.append(f"- 平均エリクサー: {deck.avg_elixir}")
    match = features.my_deck_match
    if match is not None and match.name is not None:
        lines.append(f"- テンプレ照合: {match.name}（{match.confidence}）")
    else:
        confidence = match.confidence if match is not None else "unknown"
        lines.append(f"- テンプレ照合: 該当なし（{confidence}）")
    if deck.weakness_tags:
        lines.append(f"- 弱点タグ: {', '.join(deck.weakness_tags)}")
    else:
        lines.append("- 弱点タグ: なし")
    lines.append("")
    return lines


def _render_matchups(features: Features) -> list[str]:
    lines: list[str] = ["## 相性表", ""]
    if not features.matchups:
        lines.append("相性を集計できる試合がありません。")
        lines.append("")
        return lines
    lines.append("| 相手アーキタイプ | モード | 勝 | 負 | 分 |")
    lines.append("| --- | --- | --- | --- | --- |")
    for row in features.matchups:
        lines.append(
            f"| {row.opponent_archetype} | {row.mode} | "
            f"{row.wins} | {row.losses} | {row.draws} |"
        )
    lines.append("")
    return lines


def _render_loss_patterns(features: Features) -> list[str]:
    lines: list[str] = ["## 負け方パターン", ""]
    lp = features.loss_patterns
    total = lp.get("total_losses", 0)
    three = lp.get("three_crown_losses", 0)
    close = lp.get("close_losses", 0)
    lines.append(f"- 総負け数: {total}")
    lines.append(f"- 3クラウン負け: {three}")
    lines.append(f"- 接戦負け（1クラウン差）: {close}")
    lines.append("")
    return lines


def _render_level_deficits(features: Features) -> list[str]:
    lines: list[str] = ["## レベル差", ""]
    if not features.level_deficits:
        lines.append("レベル差のあるカードはありません（または所持データなし）。")
        lines.append("")
        return lines
    lines.append("| カード | レベル | 最大 | 差 |")
    lines.append("| --- | --- | --- | --- |")
    for d in features.level_deficits:
        lines.append(f"| {d.card_name} | {d.level} | {d.max_level} | {d.deficit} |")
    lines.append("")
    return lines


def _render_elixir_leaked(features: Features) -> list[str]:
    lines: list[str] = ["## elixirLeaked（推測・参考）", ""]
    el = features.elixir_leaked
    my_avg = el.get("my_avg")
    opp_avg = el.get("opp_avg")
    delta = el.get("delta")
    sample = el.get("sample", 0)
    lines.append("※ elixirLeaked は唯一の機械的指標ですが、立ち回りの良し悪しを直接")
    lines.append("測ったものではなく、あくまで推測・参考値です（実測ではありません）。")
    lines.append(f"- 自分の平均: {_fmt_opt(my_avg)}")
    lines.append(f"- 相手の平均: {_fmt_opt(opp_avg)}")
    lines.append(f"- 差（自分 - 相手）: {_fmt_opt(delta)}")
    lines.append(f"- 対象試合数: {sample}")
    lines.append("")
    return lines


def _render_frequent_opponents(features: Features) -> list[str]:
    lines: list[str] = ["## 頻出相手デッキ", ""]
    if not features.frequent_opponent_decks:
        lines.append("頻出相手デッキを集計できる試合がありません。")
        lines.append("")
        return lines
    for od in features.frequent_opponent_decks:
        names = "、".join(od.sample_names) if od.sample_names else od.deck_key
        lines.append(
            f"- [{od.archetype}] {od.count}回 "
            f"(勝 {od.wins} / 負 {od.losses}): {names}"
        )
    lines.append("")
    return lines


def _render_footer(features: Features) -> list[str]:
    lines: list[str] = ["## メモ・注記", ""]
    lines.append(f"- 標本サイズ: {features.sample_size} 試合")
    if features.modes_present:
        lines.append(f"- 含まれるモード: {', '.join(features.modes_present)}")
    if features.sample_size == 0:
        lines.append("- まだ試合がないため、分析できるデータがありません。"
                     "`ra fetch` で対戦履歴を蓄積してください。")
    elif features.sample_size < 10:
        lines.append("- 標本が少ないため、結果は断定ではなく仮説として扱ってください。")
    if features.gap_warning:
        lines.append("- 取りこぼし（ギャップ）の疑いがあります。"
                     "battlelog は直近約25戦しか返さないため、"
                     "こまめな `ra fetch` を推奨します。")
    lines.append("- 立ち回り・elixirLeaked 由来の示唆はすべて「推測」であり、"
                 "試合中の実測ではありません。")
    lines.append("")
    return lines


def render_markdown(features: Features) -> str:
    """Render a Japanese human-readable analysis brief.

    Always includes the sections あなたのデッキ / 相性表 / 負け方パターン /
    レベル差 / elixirLeaked / 頻出相手デッキ plus a footer. elixirLeaked and
    立ち回り are explicitly labelled 推測 (NOT 実測). Emits a small-sample
    warning ("標本が少") when sample_size < 10, an empty-data note ("試合がない"
    / "データがない") when there are no battles, and a gap warning when
    gap_warning is set.
    """
    lines: list[str] = ["# 分析ブリーフ", ""]
    lines += _render_my_deck(features)
    lines += _render_matchups(features)
    lines += _render_loss_patterns(features)
    lines += _render_level_deficits(features)
    lines += _render_elixir_leaked(features)
    lines += _render_frequent_opponents(features)
    lines += _render_footer(features)
    return "\n".join(lines)
