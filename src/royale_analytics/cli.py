from __future__ import annotations

import json

import click

from royale_analytics.api_client import ApiClient
from royale_analytics.brief import render_json, render_markdown
from royale_analytics.config import load_config
from royale_analytics.features import build_features
from royale_analytics.reference import load_reference
from royale_analytics.store import Store

WHITELIST_IP = "45.79.218.79"
GAP_BATTLELOG_THRESHOLD = 25


@click.group()
def cli() -> None:
    """Royale Analytics — クラッシュロワイヤルのAI分析ツール（非公式）。"""


@cli.command()
def init() -> None:
    """設定を検証し、DB を初期化し、初回セットアップ手順を表示する。"""
    config = load_config()

    click.echo("Royale Analytics の初期化を行います。")
    click.echo(f"プレイヤータグ（正規化済み）: {config.player_tag}")
    click.echo(f"API base URL: {config.base_url}")
    click.echo(f"DB パス: {config.db_path}")

    store = Store(config.db_path)
    store.init_schema()
    click.echo("SQLite スキーマを初期化しました。")

    click.echo("")
    click.echo("セットアップ手順:")
    click.echo("  1. developer.clashroyale.com で API トークンを無料発行する。")
    click.echo(
        "  2. トークン作成時に固定 IP "
        f"{WHITELIST_IP} をホワイトリストへ登録する"
        "（RoyaleAPI proxy 用）。"
    )
    click.echo(
        f"  3. リクエスト先を proxy base URL {config.base_url} にする"
        "（同じ Bearer トークンをそのまま使用）。"
    )
    click.echo(
        "  4. .env に CLASH_ROYALE_API_TOKEN と CR_PLAYER_TAG を設定する。"
    )
    click.echo("")
    click.echo(
        "This material is unofficial and is not endorsed by Supercell. "
        "For more information see Supercell's Fan Content Policy: "
        "www.supercell.com/fan-content-policy."
    )


@cli.command()
def fetch() -> None:
    """プロフィール＋battlelog を取得し SQLite に追記する。"""
    config = load_config()

    client = ApiClient(config.token, config.base_url)
    store = Store(config.db_path)
    store.init_schema()

    profile = client.get_player(config.player_tag)
    battlelog = client.get_battlelog(config.player_tag)

    if not battlelog:
        click.echo(
            "まだ対戦がありません（battlelog が空です）。"
            "プレイしてから再実行してください。"
        )

    new_battles = store.upsert_battles(config.player_tag, battlelog)
    store.save_profile_snapshot(config.player_tag, profile)

    gap_suspected = len(battlelog) >= GAP_BATTLELOG_THRESHOLD
    store.record_fetch(
        config.player_tag, new_battles, gap_suspected=gap_suspected
    )

    click.echo(f"{new_battles} 件の新規対戦を取得")
    if gap_suspected:
        click.echo(
            "ギャップ警告: battlelog が満杯（25件）でした。"
            "前回取得からの取りこぼしの可能性があります。"
        )


@cli.command()
@click.option("--json-out", type=click.Path(), default=None)
def analyze(json_out: str | None) -> None:
    """蓄積から特徴量を算出し、分析ブリーフ（Markdown＋任意でJSON）を出力する。"""
    config = load_config()

    store = Store(config.db_path)
    store.init_schema()
    reference = load_reference()

    battles = store.load_battles(config.player_tag)
    profile = store.get_latest_profile(config.player_tag)
    gap = store.latest_gap_suspected(config.player_tag)

    features = build_features(battles, profile, reference, gap_suspected=gap)

    click.echo(render_markdown(features))

    if json_out is not None:
        with open(json_out, "w", encoding="utf-8") as fh:
            fh.write(json.dumps(render_json(features), ensure_ascii=False))
        click.echo(f"JSON ブリーフを書き出しました: {json_out}")
