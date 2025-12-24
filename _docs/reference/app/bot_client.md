---
title: Bot Client Reference
status: active
draft_status: n/a
created_at: 2025-12-24
updated_at: 2025-12-24
references:
  - _docs/reference/database/points_repository.md
related_issues: []
related_prs: []
---

## Overview
`BotClient` は Discord のイベントを受け取り、ポイント付与やコマンド実行に必要な依存を保持する。

## Behavior
- Bot からのメッセージは無視する。
- **サーバー内メッセージのみ**ポイント付与対象とし、DM は対象外。

## API
- `on_ready()` -> None: スラッシュコマンドを同期し、起動ログを出力する。
- `on_message(message: discord.Message)` -> None: メッセージ受信時にポイントを加算する。

## Usage
`create_client(points_repo=...)` で生成し、`container.register_commands()` でコマンド登録を行う。
