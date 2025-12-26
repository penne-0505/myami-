---
title: Points Service Reference
status: active
draft_status: n/a
created_at: 2025-12-26
updated_at: 2025-12-26
references:
  - _docs/reference/database/points_repository.md
related_issues: []
related_prs: []
---

## Overview
`PointsService` は Discord コマンド層から呼び出されるユースケース層で、ポイント送信/剥奪/権限管理/購入チェックなどの業務ルールを集約する。実装は `service/points_service.py` にある。

## Behavior
- コマンド層の入力検証（Discord 権限チェックなど）を前提に、ユースケース単位の整合性チェックを行う。
- 失敗条件は例外で通知し、呼び出し側がレスポンス生成を担当する。

## Exceptions
- `InvalidPointsError`: 0 以下のポイント指定。
- `PermissionDeniedError`: ポイント剥奪の権限がない。
- `InsufficientPointsError`: 保有ポイントが不足している。
- `TargetHasNoPointsError`: 対象ユーザーがポイントを持っていない。
- `OperationFailedError`: DB 操作が失敗した。
- `MissingClanRegisterChannelError`: クラン登録通知チャンネルが未設定。
- `RoleNotForSaleError`: 購入対象ではないロール。
- `PermissionNotGrantedError`: 権限解除対象が権限を持っていない。

## API
- `get_user_points(guild_id: int, user_id: int)` -> `int | None`
- `get_top_rank(guild_id: int, limit: int = 10)` -> `list[dict]`
- `send_points(guild_id: int, sender_id: int, recipient_id: int, points: int)` -> `None`
- `remove_points(guild_id: int, admin_id: int, target_id: int, points: int, is_admin: bool)` -> `None`
- `grant_remove_permission(guild_id: int, user_id: int)` -> `None`
- `revoke_remove_permission(guild_id: int, user_id: int)` -> `None`
- `get_clan_register_channel(guild_id: int)` -> `int`
- `set_clan_register_channel(guild_id: int, channel_id: int)` -> `None`
- `set_role_buy_price(guild_id: int, role_id: int, price: int)` -> `None`
- `get_role_buy_price(guild_id: int, role_id: int)` -> `int | None`
- `validate_role_purchase(guild_id: int, role_id: int, user_id: int)` -> `RolePurchase`
- `charge_role_purchase(guild_id: int, user_id: int, price: int)` -> `None`
- `refund_role_purchase(guild_id: int, user_id: int, price: int)` -> `None`

## Usage
`app/command_registry.py` から `PointsService` を呼び出し、例外に応じて Discord レスポンスを生成する。
