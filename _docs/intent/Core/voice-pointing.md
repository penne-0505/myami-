---
title: Voice Pointing Intent
status: active
draft_status: n/a
created_at: 2025-12-26
updated_at: 2025-12-26
references:
  - _docs/plan/Core/voice-pointing.md
  - _docs/reference/app/voice_points.md
related_issues: []
related_prs: []
---

## Background
VC参加者の継続参加を促すため、チャット以外の貢献にもポイントを付与したい。

## Decision
- 付与レートは 1pt / 7分とする。
- スピーカーミュート時は付与対象外とする。
- 同一VCに2人以上（Bot含む）がいる場合のみ付与対象とする。
- Bot再起動での未付与は許容し、永続化は行わない。

## Rationale
- メッセージ付与と比べて緩やかに増えるレートにすることでポイントのインフレを抑える。
- ミュート中の付与を外すことで、実際の参加に紐づける。
- 2人以上条件により、単独接続の放置を抑止する。
- 実装コストを抑えるため、状態はメモリ保持とする。

## Consequences
- Bot再起動やクラッシュ時に、直前の滞在時間は失われる。
- 2人未満のVCやミュート状態ではポイントが増えない。
