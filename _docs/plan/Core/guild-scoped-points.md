---
title: Guild Scoped Points
status: proposed
draft_status: n/a
created_at: 2025-12-26
updated_at: 2025-12-26
references:
  - _docs/reference/database/points_repository.md
  - _docs/reference/app/container.md
  - _docs/reference/app/bot_client.md
  - _docs/guide/deployment/railway.md
related_issues: []
related_prs: []
---

## Overview
ポイントを guild 単位で分離し、同一ユーザーが複数サーバーに所属していてもポイントが干渉しないようにする。

## Scope
- `points` テーブルを guild 単位に拡張する（`guild_id` 追加、複合主キー化）。
- RPC 関数 (`ensure_points_schema` / `add_points` / `transfer_points`) を guild 対応に更新する。
- `PointsRepository` と `Database` の API を guild パラメータ付きに更新する。
- `/point` `/rank` `/send` `/remove` `/permit-remove` およびゲーム/VC/メッセージ付与を guild スコープで処理する。
- `point_remove_permissions` を guild 単位に分離する（guild ごとに剥奪権限を管理）。
- ドキュメント（reference/guide/plan）を更新する。

## Non-Goals
- 既存ポイントの移行方法の最終決定（別途決定し、実装時に確定する）。
- 既存のロール購入価格やクラン登録設定のスコープ変更（既に guild 単位のため対象外）。

## Requirements
- **Functional**
  - `/point` は実行された guild のポイントを表示する。
  - `/rank` は guild 内ランキングのみを表示する。
  - `/send` `/remove` は同一 guild 内でのみポイント移動を許可する。
  - メッセージ、VC、ゲームによるポイント付与は guild ごとに独立する。
  - `point_remove_permissions` は guild 単位で付与・解除できる。
- **Non-Functional**
  - 既存の Supabase RPC 呼び出しパターンを維持し、DB 操作の原子性を確保する。
  - 既存 API 呼び出し箇所はコンパイルエラーを防ぐために一括更新する。

## Tasks
- DB
  - `points` に `guild_id` を追加し、`(guild_id, user_id)` を主キーに変更。
  - `point_remove_permissions` に `guild_id` を追加し、複合主キー化。
  - `add_points` / `transfer_points` / `ensure_points_schema` を guild 引数対応に修正。
  - `top_rank` を guild 条件付きにする。
- App/Service
  - `Database` の `get_points/add_points/transfer/top_rank/ensure_user` を `guild_id` 引数対応。
  - `PointsRepository` を guild スコープ API に更新。
  - `bot/client.py` のポイント操作（メッセージ/VC/ゲーム）を guild ID 付きで呼び出す。
  - `app/container.py` のスラッシュコマンドを guild 依存の入力検証と DB 呼び出しに更新。
  - `permit-remove` の権限判定を guild 単位に変更。
- Docs
  - `_docs/reference/database/points_repository.md` を API 変更に合わせて更新。
  - `_docs/reference/app/container.md` / `_docs/reference/app/bot_client.md` の仕様を guild スコープに更新。
  - `_docs/guide/deployment/railway.md` の SQL セットアップ説明を更新。

## Test Plan
- サーバー A/B で同一ユーザーのポイントが独立していることを確認する。
- `/point` `/rank` `/send` `/remove` が guild 内でのみ作用することを確認する。
- VC/メッセージ/ゲームのポイント付与が guild ごとに記録されることを確認する。
- `permit-remove` が guild ごとに権限分離されることを確認する。

## Deployment / Rollout
- Supabase SQL を先に適用し、新スキーマ・RPC を反映する。
- アプリ側の更新後、既存データの移行を実施する（詳細は Open Questions の結論に従う）。
- ロールバック時は旧スキーマに戻すための SQL を準備する。

## Open Questions
- 既存ポイントの移行方針（guild 未分離データの割当ルール）を決める必要がある。
  - 決定: `746587719827980359` へ一括移行し、移行後は当該 guild のポイントとして固定する。
