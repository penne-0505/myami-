---
title: Bot Client Reference
status: active
draft_status: n/a
created_at: 2025-12-24
updated_at: 2025-12-26
references:
  - _docs/reference/database/points_repository.md
  - _docs/reference/app/voice_points.md
  - _docs/reference/app/point_games.md
related_issues: []
related_prs: []
---

## Overview
`BotClient` は Discord のイベントを受け取り、ユースケース層（メッセージポイント、VCポイント、ポイントゲーム）へ委譲する I/O アダプタである。実装は `bot/client.py` と `bot/handlers/` にある。

## Behavior
- Bot からのメッセージは無視する。
- **サーバー内メッセージのみ**ポイント付与対象とし、DM は対象外。
- ポイントは guild 単位で付与・消費される。
- VC接続中のユーザーに対し、時間経過でポイントを付与する（guild 単位）。
- `m.` プレフィックスのゲームコマンドを処理する。
- 起動時の DB 接続確認と、スキーマ未作成時の初期化は `app/bot_factory.py` 側で行われ、ログが出力される（`app/facade.py` はファサードとして呼び出す）。

## API
- `on_ready()` -> None: スラッシュコマンドを同期し、起動ログを出力する。
- `on_message(message: discord.Message)` -> None: メッセージ受信時にポイントを加算し、ゲームコマンド/セッション入力をユースケースへ委譲する。
- `on_voice_state_update(...)` -> None: VC接続状態の更新を受け取り、VCポイントのユースケースへ委譲する。

## Usage
`create_client(points_repo=...)` で生成し、`command_registry.register_commands(points_service=...)` または `facade.register_commands()` でコマンド登録を行う。
