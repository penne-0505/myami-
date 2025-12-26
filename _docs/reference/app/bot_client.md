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
`BotClient` は Discord のイベントを受け取り、ポイント付与やコマンド実行に必要な依存を保持する。実装は `bot/client.py` にある。

## Behavior
- Bot からのメッセージは無視する。
- **サーバー内メッセージのみ**ポイント付与対象とし、DM は対象外。
- ポイントは guild 単位で付与・消費される。
- VC接続中のユーザーに対し、時間経過でポイントを付与する（guild 単位）。
- `m.` プレフィックスのゲームコマンドを処理する。
- 起動時の DB 接続確認とスキーマ初期化は `app/bot_factory.py` 側で行われ、ログが出力される（`app/container.py` はファサードとして呼び出す）。

## API
- `on_ready()` -> None: スラッシュコマンドを同期し、起動ログを出力する。
- `on_message(message: discord.Message)` -> None: メッセージ受信時にポイントを加算し、ゲームコマンド/セッション入力を処理する。
- `on_voice_state_update(...)` -> None: VC接続状態の更新を受け取り、影響するチャンネル内メンバーのセッションを更新して経過時間を加算する。

## Usage
`create_client(points_repo=...)` で生成し、`command_registry.register_commands()` または `container.register_commands()` でコマンド登録を行う。
