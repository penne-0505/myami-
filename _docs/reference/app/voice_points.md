---
title: Voice Points Reference
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
VC接続中の滞在時間に応じてポイントを付与するための仕様をまとめる。

## Behavior
- 付与レートは **1pt / 7分**。
- ポイントは guild 単位で付与される。
- スピーカーミュート（`mute` / `self_mute`）時は付与対象外。
- 同一VCに2人以上（Bot含む）がいる場合のみ付与対象。
- 状態はメモリ上で保持し、Bot再起動でリセットされる。

## Implementation Notes
- `bot/handlers/voice_points_handler.py` の `VoicePointsHandler` がVCセッションを管理する。
- `handle_state_update` で接続・切断・状態変化を検出し、対象チャンネル内の全メンバーのセッションを更新して加点判定を揃える。
- `voice_award_loop` が一定間隔でポイント付与を実行する。
