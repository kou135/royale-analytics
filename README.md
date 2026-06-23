# Royale Deep Analytics

OSS の Clash Royale 対戦履歴 AI 分析ツール（Claude Code skill）。決定論的な Python コアが公式 API（RoyaleAPI proxy 経由）からデータを取得・蓄積・集計し、構造化した「分析ブリーフ（Markdown ＋ JSON）」を出力します。Claude Code のセッションがそのブリーフを読み、局所解に陥らない多様な次アクションを提案します。

- パッケージ: `royale_analytics`
- CLI: `ra`
- skill: `royale-analyzer`

## セットアップ

1. **API トークンを発行**: <https://developer.clashroyale.com> で無料のトークンを作成します。
2. **IP をホワイトリスト登録**: 動的 IP 環境では、トークン作成時に固定 IP `45.79.218.79`（RoyaleAPI proxy）を許可 IP として登録します。
3. **proxy 経由でリクエスト**: ベース URL を `https://proxy.royaleapi.dev/v1` にします（同じ Bearer トークンをそのまま使用）。これが既定値です。
4. **環境変数を設定**: `.env.example` を `.env` にコピーし、`CLASH_ROYALE_API_TOKEN` と `CR_PLAYER_TAG` を埋めます。

   ```sh
   cp .env.example .env
   ```

5. **インストール**:

   ```sh
   pip install -e .
   ```

## 使い方

```sh
ra init       # 設定検証・タグ正規化表示・DB 初期化・セットアップガイド
ra fetch      # プロフィール＋battlelog 取得 → 重複排除 → SQLite 追記
ra analyze    # 蓄積から特徴量算出 → 分析ブリーフ（Markdown ＋ JSON）を出力
```

## 免責

This material is unofficial and is not endorsed by Supercell. For more information see Supercell's Fan Content Policy: www.supercell.com/fan-content-policy.

## ライセンス

MIT License.
