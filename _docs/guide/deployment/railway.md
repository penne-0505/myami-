---
title: Railway Deployment Guide
status: active
draft_status: n/a
created_at: 2025-12-24
updated_at: 2025-12-24
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
     - `DS_ADMIN_IDS`: 管理者 ID の配列形式文字列（例: `[123, 456]`）
   - 任意
     - `DS_DB_PATH`: SQLite DB パス（未設定なら `points.db`）
     - `DS_DB_TIMEOUT`: SQLite 接続タイムアウト秒（未設定なら `5.0`）
3. Start Command を `python main.py` に設定する。
4. Deploy を実行し、View logs で起動状況を確認する。

## Notes

- Variables 画面では Raw Editor で `.env` を貼り付けられるため、まとめて設定する場合に活用する。
- リポジトリ内の `.env` を検出して変数候補を提示できるため、必要に応じて取り込む。
- Start Command を手動設定することで、自動検出に依存せず起動できる。
