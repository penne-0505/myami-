---
title: Supabase Database Migration Plan
status: proposed
draft_status: n/a
created_at: 2025-12-26
updated_at: 2025-12-26
references:
  - _docs/reference/database/points_repository.md
  - _docs/reference/app/facade.md
  - _docs/guide/deployment/railway.md
related_issues: []
related_prs: []
---

## Overview
SQLite から Supabase(PostgreSQL) へデータストアを移行し、Discord ポイント Bot の永続化を Supabase で運用する。既存データの移行はスコープ外とする。

## Scope
- Supabase(PostgreSQL) に `points` テーブルを作成する。
- SQLite 前提の `Database` 実装を Supabase(PostgreSQL) 対応に差し替える。
- 環境変数・設定ローダーを Supabase 接続情報に対応させる。
- デプロイガイドの環境変数を Supabase 前提へ更新する。
- 既存の `PointsRepository` API は維持する。

## Non-Goals
- 既存 SQLite データの移行/インポート。
- Supabase の Auth/Storage/Edge Functions の導入。
- 監視・分析などの周辺機能追加。

## Requirements
- **Functional**:
  - `ensure_schema()` で `points` テーブルが存在しない場合に作成できる。
  - `award_point_for_message` / `send_points` / `remove_points` が現在と同等の挙動を維持する。
  - ランキング取得 (`get_top_rank`) がポイント降順で取得できる。
- **Non-Functional**:
  - ポイント送受信はトランザクションで原子性を担保する。
  - Discord の `user_id` に対応する型は `BIGINT` を使用する。
  - Service Role キーはサーバーのみで使用し、ログやレスポンスに露出しない。

## Tasks
- Supabase 接続方式を決定（PostgreSQL 直結 or Supabase Python SDK）。
- `Database` 抽象/実装を Supabase(PostgreSQL) 向けに更新し、トランザクション対応を行う。
- `points` テーブル作成 SQL を追加し、起動時に `ensure_schema()` で実行する。
- `app/facade.py` の設定ローダーに Supabase 用環境変数を追加する。
- ドキュメント更新:
  - `_docs/reference/app/facade.md`
  - `_docs/reference/database/points_repository.md`
  - `_docs/guide/deployment/railway.md`

## Test Plan
- ローカル環境で Supabase(PostgreSQL) 接続し、以下を確認する:
  - `/point` で新規ユーザーのポイントが 0 から加算される。
  - `/send` でポイント送受信が原子性を保って実行される。
  - `/remove` で管理者のみが減算できる。
  - `/rank` でポイント降順の上位が取得される。

## Deployment / Rollout
- Supabase に `points` テーブルを作成（SQL Editor で実行）。
- Railway などの環境変数に Supabase 接続情報を追加。
- 旧 `DS_DB_PATH` / `DS_DB_TIMEOUT` は移行後に非推奨化し、必要なら削除。
- ロールバック時は SQLite 実装を復元し、Supabase 接続環境変数を無効化する。
