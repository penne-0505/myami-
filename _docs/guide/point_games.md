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
m.slot 200
m.omikuji 300
m.hitblow 500
m.janken 200
m.coin 100 表
```

## Games
### Slot
```
m.slot <掛け金>
```
絵文字がスロット風に変化し、揃い方で倍率が決まります。

### Omikuji
```
m.omikuji <掛け金>
```
大吉・中吉などの結果で倍率が決まります。大凶は追加で失う点に注意してください。

### Hit & Blow
```
m.hitblow <掛け金>
```
3桁・重複なしの数字を当てるゲームです。開始後は次のメッセージが回答として扱われます。
- 例:
  1. `m.hitblow 300`
  2. `123`
  3. `907`

### Janken
```
m.janken <掛け金> [グー|チョキ|パー]
```
あいこの場合は勝敗がつくまで継続します。コマンドで選択まで入れない場合は、次のメッセージで入力してください。

### Coin Toss
```
m.coin <掛け金> <表|裏>
```
表/裏を選ぶ2択ゲームです。

## Tips
- 掛け金は100以上の整数。
- クールタイムはユーザーごとに1秒。
- ゲーム進行中は新しいゲームを開始できません。
