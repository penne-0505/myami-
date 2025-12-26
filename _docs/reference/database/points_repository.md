---
title: Points Repository Reference
status: active
draft_status: n/a
created_at: 2025-12-24
updated_at: 2025-12-26
references: []
related_issues: []
related_prs: []
---

## Overview
`PointsRepository` はポイント管理のユースケースを集約するデータアクセス層。Supabase(PostgreSQL) を前提とした `Database` に依存し、Discord側のコマンド実装からDB操作を抽象化する。ポイントは guild 単位で分離される。

## Notes
- Supabase では RPC 関数 `ensure_points_schema` / `add_points` / `transfer_points` を利用する。
- これらの関数は `_docs/guide/deployment/railway.md` の SQL セクションで作成する。
- `point_remove_permissions` テーブルでポイント剥奪権限を管理する（guild 単位）。
- `clan_register_settings` テーブルでクラン登録通知チャンネルを管理する。
- `role_buy_settings` テーブルでロール購入の価格設定を管理する。

## API
- `ensure_schema()` -> None: points テーブルを作成する。
- `award_point_for_message(guild_id: int, user_id: int)` -> int: メッセージ受信時に1ポイント加算する。
- `get_user_points(guild_id: int, user_id: int)` -> int | None: ユーザーのポイントを返す。
- `get_top_rank(guild_id: int, limit: int = 10)` -> list[dict]: ランキング上位を返す。
- `send_points(guild_id: int, sender_id: int, recipient_id: int, points: int)` -> bool: 送信者から受信者へポイントを移動する。
- `remove_points(guild_id: int, admin_id: int, target_id: int, points: int)` -> bool: 対象ユーザーから管理者へポイントを移動する。
- `has_remove_permission(guild_id: int, user_id: int)` -> bool: ポイント剥奪権限を持つか判定する。
- `grant_remove_permission(guild_id: int, user_id: int)` -> None: ポイント剥奪権限を付与する。
- `revoke_remove_permission(guild_id: int, user_id: int)` -> bool: ポイント剥奪権限を解除する。
- `set_clan_register_channel(guild_id: int, channel_id: int)` -> None: クラン登録通知チャンネルを設定する。
- `get_clan_register_channel(guild_id: int)` -> int | None: クラン登録通知チャンネルを取得する。
- `set_role_buy_price(guild_id: int, role_id: int, price: int)` -> None: ロール購入の価格を設定する。
- `get_role_buy_price(guild_id: int, role_id: int)` -> int | None: ロール購入の価格を取得する。

## Usage
アプリ起動時に `ensure_schema()` を実行し、各コマンドでは `PointsRepository` のユースケースメソッドを呼び出す。
