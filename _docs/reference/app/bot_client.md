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
- VC接続中のユーザーに対し、時間経過でポイントを付与する。
- `m.` プレフィックスのゲームコマンドを処理する。

## API
- `on_ready()` -> None: スラッシュコマンドを同期し、起動ログを出力する。
- `on_message(message: discord.Message)` -> None: メッセージ受信時にポイントを加算し、ゲームコマンド/セッション入力を処理する。
- `on_voice_state_update(...)` -> None: VC接続状態の更新を受け取り、影響するチャンネル内メンバーのセッションを更新して経過時間を加算する。

## Usage
`create_client(points_repo=...)` で生成し、`container.register_commands()` でコマンド登録を行う。
