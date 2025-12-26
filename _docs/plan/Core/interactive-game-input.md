---
title: Interactive Game Input Plan
status: active
draft_status: n/a
created_at: 2025-12-26
updated_at: 2025-12-26
references:
  - _docs/reference/app/point_games.md
  - _docs/guide/point_games.md
related_issues: []
related_prs: []
---

## Overview
ポイント賭けゲームの入力を、引数一括指定ではなく対話的に取得できるようにする。

## Scope
- スロット/おみくじ/hit&blow/じゃんけん/コイントスの入力フローを対話式に変更
- 既存の引数指定は省略可能とし、指定されている場合は対話をスキップ
- キャンセル用文字列は `bot/constants.py` で定義する

## Non-Goals
- スラッシュコマンド化
- ゲーム倍率やポイント計算ロジックの変更

## Requirements
- **Functional**:
  - すべてのゲームで掛け金や選択肢を対話的に取得できる
  - 引数が指定されている場合は、その入力を採用して対話をスキップする
  - キャンセルは定義済みの文字列リストで判定する
  - 既存のタイムアウト（120秒）とクールダウン（1秒）を維持する
- **Non-Functional**:
  - 既存のポイント増減ロジックの挙動を維持する
  - ドキュメント（guide/reference）を更新する

## Tasks
- `bot/client.py` の入力セッションとゲーム進行を分離し、状態遷移を実装する
- `bot/constants.py` にキャンセル文字列リストを追加する
- `_docs/guide/point_games.md` と `_docs/reference/app/point_games.md` を更新する

## Test Plan
- 各ゲームで引数なし開始 → 対話入力 → 完了ができる
- 引数指定で対話がスキップされる
- キャンセルワード入力で適切に終了する（進行中のゲームは掛け金没収）
- 入力待ちとゲーム進行が120秒でタイムアウトする

## Deployment / Rollout
- 既存のコマンド互換を維持してリリースする
