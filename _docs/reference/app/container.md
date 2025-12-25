---
title: App Container Reference
status: active
draft_status: n/a
created_at: 2025-12-24
updated_at: 2025-12-26
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

### Database
- `SUPABASE_URL` (必須): Supabase の Project URL。
- `SUPABASE_SERVICE_ROLE_KEY` (必須): Supabase の service role キー。

## Behavior
- Supabase への接続情報が不足している場合は起動時にエラーとなる。
- `/remove` はサーバー管理権限保持者、または `point_remove_permissions` に登録済みのユーザーのみ実行できる。
- `/permit-remove` はサーバー管理権限保持者のみ実行できる。

## API
- `load_discord_settings(raw_token: str | None = None)` -> `DiscordSettings`
  - 未指定の場合は環境変数から取得する。
- `load_db_settings(raw_supabase_url: str | None = None, raw_service_role_key: str | None = None)` -> `DBSettings`
  - 未指定の場合は環境変数から取得する。
- `load_config(env_file: str | Path | None = None)` -> `AppConfig`
  - `.env` を読み込んだ上でアプリ全体の設定を組み立てる。
- `register_commands(client: BotClient, points_repo: PointsRepository)` -> `None`
  - `/point` `/rank` `/send` `/remove` `/permit-remove` コマンドを登録する。
- `create_bot_client(config: AppConfig)` -> `BotClient`
  - DB初期化、ポイントスキーマ作成、コマンド登録まで行う。

## Usage
`main.py` から `load_config()` を呼び、`create_bot_client()` でBotを組み立てて `run()` する。
