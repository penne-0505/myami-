---
title: Points Repository Reference
status: active
draft_status: n/a
created_at: 2025-12-24
updated_at: 2025-12-24
references: []
related_issues: []
related_prs: []
---

## Overview
`PointsRepository` はポイント管理のユースケースを集約するデータアクセス層。`Database` のCRUDに依存し、Discord側のコマンド実装からSQL直書きを排除する。

## API
- `ensure_schema()` -> None: points テーブルを作成する。
- `award_point_for_message(user_id: int)` -> int: メッセージ受信時に1ポイント加算する。
- `get_user_points(user_id: int)` -> int | None: ユーザーのポイントを返す。
- `get_top_rank(limit: int = 10)` -> list[sqlite3.Row]: ランキング上位を返す。
- `send_points(sender_id: int, recipient_id: int, points: int)` -> bool: 送信者から受信者へポイントを移動する。
- `remove_points(admin_id: int, target_id: int, points: int)` -> bool: 対象ユーザーから管理者へポイントを移動する。

## Usage
アプリ起動時に `ensure_schema()` を実行し、各コマンドでは `PointsRepository` のユースケースメソッドを呼び出す。
