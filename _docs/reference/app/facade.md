---
title: App Facade Reference
status: active
draft_status: n/a
created_at: 2025-12-24
updated_at: 2025-12-26
references:
  - _docs/reference/database/points_repository.md
  - _docs/reference/app/bot_client.md
  - _docs/reference/service/points_service.md
related_issues: []
related_prs: []
---

## Overview
`app/facade.py` はエントリポイント用のファサードであり、設定ロード (`app/settings.py`)・コマンド登録 (`app/command_registry.py`)・Bot 組み立て (`app/bot_factory.py`) をまとめて公開する。

## Settings
### Discord
- `DS_SECRET_TOKEN` (必須): Discord Bot のトークン。

### Database
- `SUPABASE_URL` (必須): Supabase の Project URL。
- `SUPABASE_SERVICE_ROLE_KEY` (必須): Supabase の service role キー。

## Behavior
- Supabase への接続情報が不足している場合は起動時にエラーとなる。
- 起動時に DB 接続確認を行い、失敗時はログ出力して起動を中止する。
- 起動時に `points` スキーマが未作成の場合のみ初期化を行い、結果をログ出力する。
- `/point` `/rank` `/send` `/remove` はサーバー内でのみ実行できる。
- `/remove` はサーバー管理権限保持者、または `point_remove_permissions`（guild 単位）に登録済みのユーザーのみ実行できる。
- `/permit-remove` はサーバー管理権限保持者のみ実行できる。
- `/clan-register` は設定済みの通知チャンネルへ申請内容を送信する。
- `/clan-register-channel` はサーバー管理権限保持者のみ実行できる。
- `/role-buy-register` はサーバー管理権限保持者のみ実行できる。
- `/role-buy` は登録済みの購入対象ロールをポイント消費して即時付与する。

## API
- `load_discord_settings(raw_token: str | None = None)` -> `DiscordSettings`
  - 実装は `app/settings.py`。未指定の場合は環境変数から取得する。
- `load_db_settings(raw_supabase_url: str | None = None, raw_service_role_key: str | None = None)` -> `DBSettings`
  - 実装は `app/settings.py`。未指定の場合は環境変数から取得する。
- `load_config(env_file: str | Path | None = None)` -> `AppConfig`
  - 実装は `app/settings.py`。`.env` を読み込んだ上でアプリ全体の設定を組み立てる。
- `register_commands(client: BotClient, points_service: PointsService)` -> `None`
  - 実装は `app/command_registry.py`。`/point` `/rank` `/send` `/remove` `/permit-remove` `/clan-register` `/clan-register-channel` `/role-buy-register` `/role-buy` コマンドを登録する。
- `create_bot_client(config: AppConfig)` -> `BotClient`
  - 実装は `app/bot_factory.py`。DB初期化、ポイントスキーマ作成、コマンド登録まで行う。

## Usage
`app/main.py` から `load_config()` を呼び、`create_bot_client()` でBotを組み立てて `run()` する。
