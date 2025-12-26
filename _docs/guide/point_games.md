---
title: Point Games Guide
status: active
draft_status: n/a
created_at: 2025-12-26
updated_at: 2025-12-26
references:
  - _docs/reference/app/point_games.md
related_issues: []
related_prs: []
---

## Overview
ポイントを掛けて遊べるゲームの使い方ガイド。

## Quick Start
```
m.slot
m.omikuji
m.hitblow
m.janken
m.coin
```
引数をまとめて指定したい場合は、従来通りまとめて入力しても問題ありません。
```
m.slot 200
m.omikuji 300
m.hitblow 500
m.janken 200 グー
m.coin 100 表
```

## Games
### Slot
```
m.slot [掛け金]
```
掛け金が未指定の場合は、Bot が掛け金の入力を促します。絵文字がスロット風に変化し、揃い方で倍率が決まります。

### Omikuji
```
m.omikuji [掛け金]
```
掛け金が未指定の場合は、Bot が掛け金の入力を促します。大吉・中吉などの結果で倍率が決まります。大凶は追加で失う点に注意してください。

### Hit & Blow
```
m.hitblow [掛け金]
```
3桁・重複なしの数字を当てるゲームです。掛け金が未指定の場合は、Bot が掛け金の入力を促します。開始後は次のメッセージが回答として扱われます。
- 例:
  1. `m.hitblow 300`
  2. `123`
  3. `907`

### Janken
```
m.janken [掛け金] [グー|チョキ|パー]
```
あいこの場合は勝敗がつくまで継続します。掛け金や手が未指定の場合は、Bot が入力を促します。

### Coin Toss
```
m.coin [掛け金] [表|裏]
```
表/裏を選ぶ2択ゲームです。掛け金や表/裏が未指定の場合は、Bot が入力を促します。

## Tips
- 掛け金は100以上の整数。
- 全角数字は半角に読み替えて解釈されます。
- クールタイムはユーザーごとに1秒。
- ゲーム進行中は新しいゲームを開始できません。
- キャンセルは `quit` で可能（入力待ち中は掛け金未消費）。
