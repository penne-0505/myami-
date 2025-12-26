---
title: Voice Pointing Plan
status: active
draft_status: n/a
created_at: 2025-12-26
updated_at: 2025-12-26
references:
  - _docs/reference/app/bot_client.md
  - _docs/reference/database/points_repository.md
related_issues: []
related_prs: []
---

## Overview
VC接続中のユーザーに対し、時間経過でポイントを付与する。

## Scope
- VC接続中のユーザーの滞在時間に応じてポイントを加算する。
- 付与レートは 1pt / 7分とする。
- スピーカーミュート時は付与対象外とする。
- 同一VCに2人以上（Bot含む）がいる場合のみ付与する。
- Bot再起動等での未付与は許容する（状態永続化は行わない）。

## Non-Goals
- 日次上限の実装。
- VC滞在ログの永続化。
- 付与履歴の可視化。

## Requirements
- **Functional**:
  - VC接続/切断/ミュート切替に追従し、条件を満たす時間のみポイントを加算する。
  - 連続滞在時も一定間隔でポイントを付与できる。
- **Non-Functional**:
  - Botの再起動で一時的にポイント計測がリセットされても許容される。

## Tasks
- `bot/client.py` にVCセッション管理と定期付与ループを実装する。
- VC条件（ミュート判定・2人以上判定）を実装する。
- 参照ドキュメントを更新する。

## Test Plan
- VC参加/退出でポイントが付与されるかを確認する。
- ミュート時はポイントが増えないことを確認する。
- 2人未満のVCではポイントが増えないことを確認する。
- Bot再起動後に付与がリセットされることを許容確認する。

## Deployment / Rollout
- Bot再起動時に新機能が有効になる。
- 既存DBの変更なし。
