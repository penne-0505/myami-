---
title: Point Games Reference
status: active
draft_status: n/a
created_at: 2025-12-26
updated_at: 2025-12-26
references:
  - _docs/reference/app/bot_client.md
  - _docs/reference/database/points_repository.md
  - _docs/plan/Core/point-games.md
related_issues: []
related_prs: []
---

## Overview
テキストコマンド（`m.` プレフィックス）で遊べるポイント賭けゲームの仕様を定義する。

## Command Prefix
- プレフィックスは `m.` 固定。
- 例: `m.slot 200`

## Common Rules
- 掛け金は整数・最小100。
- 全角数字は半角として解釈する。
- 掛け金を先に差し引き、結果に応じて倍率分のポイントを付与する。
- ポイントは guild 単位で付与・消費される。
- クールダウン: ユーザー単位で1秒。
- ゲーム進行中は新規ゲームを開始できない。
- 掛け金・選択肢は対話的に取得する（引数が指定されている場合はスキップ）。
- キャンセル判定は `bot/constants.py` の `CANCEL_WORDS` を参照する。

## Games
### Slot
- コマンド: `m.slot [掛け金]`
- 3リールの絵文字がアニメーションで変化する。
- 倍率:
  - レア3揃い: `x4.5`
  - 通常3揃い: `x2.5`
  - 2揃い: `x1.3`
  - 揃いなし: `x0`

### Omikuji
- コマンド: `m.omikuji [掛け金]`
- 倍率:
  - 大吉 `x2.0`
  - 中吉 `x1.7`
  - 小吉 `x1.4`
  - 末吉 `x1.0`（返却）
  - 凶 `x0`
  - 大凶 `x-0.5`（掛け金の1.5倍を失う）
- 抽選ウェイト:
  - 大吉 5 / 中吉 10 / 小吉 20 / 末吉 25 / 凶 30 / 大凶 10

### Hit & Blow
- コマンド: `m.hitblow [掛け金]` (`m.hit` でも可)
- 3桁・重複なしの数字を当てる。
- 試行回数は10回まで。
- 開始ユーザーの次メッセージを回答として扱う。
- `CANCEL_WORDS` に一致する入力で終了できる。120秒のタイムアウトで終了する。
- クリア倍率: `x3.0`（未クリアは没収）

### Janken
- コマンド: `m.janken [掛け金] [グー|チョキ|パー]`
- あいこは勝敗がつくまで継続する。
- 120秒のタイムアウトで終了する。
- 勝利倍率: `x2.0`（敗北は没収）

### Coin Toss
- コマンド: `m.coin [掛け金] [表|裏]`
- 勝利倍率: `x1.7`（敗北は没収）
