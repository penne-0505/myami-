---
title: Bot Client Usecase Separation Plan
status: proposed
draft_status: exploring
created_at: 2025-12-26
updated_at: 2025-12-26
references:
  - _docs/reference/app/bot_client.md
  - _docs/reference/app/point_games.md
  - _docs/reference/app/voice_points.md
  - _docs/plan/Core/point-games.md
  - _docs/plan/Core/voice-pointing.md
related_issues: []
related_prs: []
---

## Overview
`BotClient` に集約されている Discord イベント処理・ポイント付与・ゲーム進行などの責務を、ユースケース単位に分離して拡張性を高める。`BotClient` は I/O アダプタとして最小限の責務に寄せ、ユースケース層（ポイント付与、VCポイント、ポイントゲーム）へ委譲する構成へ移行する。

## Scope
- `BotClient` から以下のユースケース責務を分離する:
  - サーバー内メッセージのポイント付与
  - VCセッション管理とポイント付与
  - テキストゲームコマンドの解析・進行・セッション管理
- ユースケース層を拡張しやすい構造に整理し、ゲーム追加やVCルール変更が局所化する設計へ変更する。
- 既存機能のユーザー体験（コマンドや挙動、メッセージ文言、倍率仕様など）を保持する。

## Non-Goals
- 既存仕様のゲーム倍率・ルール変更。
- データ永続化や外部ストレージ導入（セッションのDB保存など）。
- スラッシュコマンド/ポイントAPIの仕様変更。

## Requirements
- **Functional**:
  - `BotClient` は Discord イベントを受け取り、ユースケース層へ委譲する。
  - VCポイント、メッセージポイント、ゲーム進行の責務を独立クラスに分ける。
  - ゲーム追加時は新規クラス追加 + レジストリ登録のみで完結できる。
  - 既存のクールダウン、入力タイムアウト、キャンセル動作は維持する。
- **Non-Functional**:
  - 既存の `points_repo` / `PointsService` との整合性を維持する。
  - 影響範囲を小さくするため、段階的移行を許容する（ユースケース単位で切替）。
  - テスト容易性向上のため、時間/乱数の注入可能性を確保する（拡張点の設計のみ）。

## Proposed Structure
```
bot/
  client.py
  handlers/
    message_points_handler.py
    voice_points_handler.py
    point_game_handler.py
service/
  games/
    base.py
    registry.py
    slot.py
    omikuji.py
    hitblow.py
    janken.py
    coin.py
  sessions/
    game_sessions.py
    voice_sessions.py
  time/
    clock.py
  random/
    rng.py
```

## Interfaces (Draft)
### BotClient (adapter)
- `on_ready()`:
  - `self.tree.sync()`
  - `voice_handler.ensure_background_loop(self)`
- `on_message(message)`:
  - `message_points_handler.handle(message)`
  - `game_handler.handle_message(message)`
- `on_voice_state_update(member, before, after)`:
  - `voice_handler.handle_state_update(member, before, after, now)`

### MessagePointsHandler
- `handle(message: discord.Message) -> None`
  - Bot/DM 判定
  - `points_repo.award_point_for_message(...)`

### VoicePointsHandler
- `handle_state_update(member, before, after, *, now: float) -> None`
- `tick(client: discord.Client, *, now: float) -> None`
- `ensure_background_loop(client: discord.Client) -> None`
  - 既存 `voice_award_loop` をラップして handler に委譲

### PointGameHandler
- `handle_message(message: discord.Message) -> None`
  - セッション継続判定（入力待ち/タイムアウト/キャンセル）
  - コマンド解析とゲーム開始

### GameSessionStore
- `get(user_id) -> Session | None`
- `set(user_id, session) -> None`
- `pop(user_id) -> Session | None`
- `has(user_id) -> bool`

### BaseGame
- `command_names: set[str]`
- `start(context: GameContext, args: list[str]) -> GameResult | None`
- `handle_input(context: GameContext, raw: str) -> GameResult | None`
- `timeout(context: GameContext) -> GameResult | None`

### GameRegistry
- `register(game: BaseGame) -> None`
- `find(command: str) -> BaseGame | None`

### GameContext (example)
- `guild_id`
- `channel_id`
- `user_id`
- `message`
- `points_repo`
- `now`
- `rng`

## Responsibilities Mapping
- `BotClient.on_message`:
  - `MessagePointsHandler.handle`
  - `PointGameHandler.handle_message`
- `BotClient.on_voice_state_update`:
  - `VoicePointsHandler.handle_state_update`
- `voice_award_loop`:
  - `VoicePointsHandler.tick`

## Migration Plan (Stepwise)
1. **VoicePoints 分離**
   - `voice_sessions` と `voice_award_loop` を `VoicePointsHandler` に移管。
   - `BotClient` からは handler 呼び出しのみ残す。
2. **PointGame 分離**
   - `game_sessions` / `game_cooldowns` を `GameSessionStore` に移管。
   - `PointGameHandler` を導入し、`BotClient` から呼び出す。
3. **Game Registry 導入**
   - 既存ゲームを 1つずつ `BaseGame` 実装に移行。
   - `PointGameHandler` は `GameRegistry` に委譲する形に整理。
4. **MessagePoints 分離**
   - `MessagePointsHandler` を導入し、`points_repo` の利用を集中管理。

## Compatibility Checklist
- コマンドプレフィックス `m.` 維持。
- クールダウン `1秒` 維持。
- タイムアウト値:
  - 入力待ち `120秒`
  - hit&blow `120秒`
  - じゃんけん `120秒`
- ゲーム倍率・抽選ウェイトを現行仕様で維持。
- メッセージ文言の主要テキストは現行を維持（破壊的変更禁止）。

## Tasks
- `BotClient` の責務を洗い出し、ユースケース単位に分類（Message/Voice/Game）。
- `VoicePointTracker` 相当のユースケースクラスを新設し、VC関連ロジックを移管。
- `PointGameController` と `GameSessionStore` を分離し、ゲーム進行・セッション管理を集約。
- ゲーム処理を `BaseGame` インタフェース + レジストリ方式で分離する。
- `MessagePointAwarder` を新設し、メッセージポイント付与を移管する。
- `BotClient` は各ユースケースへ処理を委譲するのみの構成に整理する。
- `bot_client.md` / `voice_points.md` / `point_games.md` を実装後に更新する。

## Test Plan
- 既存コマンドが全て同じ挙動で動作することを手動で確認する。
  - `m.slot 100`
  - `m.omikuji 100`
  - `m.hitblow 100`（3桁入力、キャンセル、タイムアウト）
  - `m.janken 100 グー`（あいこ継続）
  - `m.coin 100 表`
- VCポイント付与が従来通りに動作することを確認する。
  - 2人以上でVC参加、7分経過で付与される
  - mute/self_mute で付与停止する
- セッションタイムアウト/キャンセル/クールダウンが維持されていることを確認する。
  - 1秒以内の連続実行でクールダウンメッセージが出る
  - `CANCEL_WORDS` で中断できる
- 新しいゲーム追加時に既存ロジックへの影響が限定的であることを確認する。

## Deployment / Rollout
- 既存ユーザー向けの挙動差分がないことを確認後にリリースする。
- 段階的にユースケース単位で差し替える場合、差し替え単位ごとに確認を行う。
