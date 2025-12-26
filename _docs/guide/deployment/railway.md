---
title: Railway Deployment Guide
status: active
draft_status: n/a
created_at: 2025-12-24
updated_at: 2025-12-26
references:
  - _docs/reference/app/container.md
  - _docs/reference/app/bot_client.md
related_issues: []
related_prs: []
---

## Overview

このドキュメントは、Discord ポイント Bot を Railway にデプロイする手順をまとめたガイド。

## Prerequisites

- GitHub リポジトリに本プロジェクトが push 済み
- Railway アカウントを作成済み

## Deploy Steps (GitHub 連携)

1. Railway で新規プロジェクトを作成し、`Deploy from GitHub repo` から対象リポジトリを選んでデプロイを開始する。
2. サービスの Variables タブで環境変数を追加する。
   - 必須
     - `DS_SECRET_TOKEN`: Discord Bot トークン
     - `SUPABASE_URL`: Supabase Project URL
     - `SUPABASE_SERVICE_ROLE_KEY`: Supabase service role キー
3. Start Command を `python -m app` に設定する。
4. Deploy を実行し、View logs で起動状況を確認する。

## Supabase SQL Setup

Supabase の SQL Editor で `supabase/supabase_init.sql` を実行し、
`points` テーブルと RPC 関数を作成する。

### Guild Scoping Migration

既存データがある場合は、`supabase/supabase_init.sql` 末尾の migration セクションを実行して
`points` と `point_remove_permissions` を guild 単位に移行する。

- 既存ポイントは `746587719827980359` に一括で割り当てる。

## Notes

- Variables 画面では Raw Editor で `.env` を貼り付けられるため、まとめて設定する場合に活用する。
- リポジトリ内の `.env` を検出して変数候補を提示できるため、必要に応じて取り込む。
- Start Command を手動設定することで、自動検出に依存せず起動できる。
- 起動ログに `[startup] DB connection check` が出るため、環境変数や Supabase の到達性確認に利用できる。
- DB スキーマ未作成の場合は起動時に自動初期化を試みる。失敗する場合は SQL セットアップを再確認する。
