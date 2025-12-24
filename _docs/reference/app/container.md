---
title: App Container Reference
status: active
draft_status: n/a
created_at: 2025-12-24
updated_at: 2025-12-24
references:
  - _docs/reference/database/points_repository.md
  - _docs/reference/app/bot_client.md
related_issues: []
related_prs: []
---

## Overview
`container.py` は環境変数から設定を読み込み、`Database` と `PointsRepository`、Discord クライアントを組み立てるためのエントリポイント支援モジュール。

## Settings
### Discord
- `DS_SECRET_TOKEN` (必須): Discord Bot のトークン。
- `DS_ADMIN_IDS` (必須): 管理者 ID の配列形式文字列 (例: `[123, 456]`)。

### Database
- `DS_DB_PATH` (任意): SQLite のDBファイルパス。未指定時は `points.db`。
- `DS_DB_TIMEOUT` (任意): SQLite 接続タイムアウト秒。未指定時は `5.0`。

## Behavior
- `DS_DB_PATH` にディレクトリを含む場合、起動時に親ディレクトリを自動作成する。

## API
- `load_discord_settings(raw_token: str | None = None, raw_admin_ids: str | None = None)` -> `DiscordSettings`
  - 未指定の場合は環境変数から取得する。
- `load_db_settings(raw_db_path: str | None = None, raw_timeout: str | None = None)` -> `DBSettings`
  - 未指定の場合は環境変数から取得する。
- `load_config(env_file: str | Path | None = None)` -> `AppConfig`
  - `.env` を読み込んだ上でアプリ全体の設定を組み立てる。
- `register_commands(client: BotClient, points_repo: PointsRepository, admin_ids: set[int])` -> `None`
  - `/point` `/rank` `/send` `/remove` コマンドを登録する。
- `create_bot_client(config: AppConfig)` -> `BotClient`
  - DB初期化、ポイントスキーマ作成、コマンド登録まで行う。

## Usage
`main.py` から `load_config()` を呼び、`create_bot_client()` でBotを組み立てて `run()` する。
