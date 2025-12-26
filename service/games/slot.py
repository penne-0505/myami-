from __future__ import annotations

import asyncio

from bot.constants import SLOT_RARE_SYMBOLS, SLOT_SYMBOLS
from service.games.base import BaseGame, GameContext
from service.games.support import apply_payout, ensure_balance, parse_bet, validate_bet
from service.sessions.game_sessions import GameInputSession, GameSession

SLOT_ANIMATION_STEPS = 3
SLOT_ANIMATION_INTERVAL_SECONDS = 0.6


class SlotGame(BaseGame):
    command_names = {"slot"}
    game_key = "slot"

    async def start(self, context: GameContext, args: list[str]) -> GameSession | None:
        bet = parse_bet(args)
        if bet is None:
            session = GameInputSession(
                game=self.game_key,
                bet=None,
                choice=None,
                started_ts=context.now,
                last_activity_ts=context.now,
                channel_id=context.channel_id,
            )
            await context.message.channel.send(
                "スロットを開始します。賭けるポイントを入力してください。"
            )
            return session
        return await self._resolve(context, bet)

    async def handle_input(
        self, context: GameContext, raw: str, session: GameSession
    ) -> GameSession | None:
        if not isinstance(session, GameInputSession):
            return session
        if session.bet is None:
            bet = parse_bet(raw.split())
            if bet is None:
                await context.message.channel.send("賭けるポイントを入力してください。")
                return session
            bet_error = validate_bet(bet)
            if bet_error is not None:
                await context.message.channel.send(bet_error)
                return session
            can_pay, required, points = ensure_balance(
                context.points_repo,
                context.guild_id,
                context.user_id,
                bet,
                max_loss_multiplier=1.0,
            )
            if not can_pay:
                await context.message.channel.send(
                    f"ポイントが足りません。（必要: {required} / 所持: {points}）"
                )
                return session
            session.bet = bet
        return await self._resolve(context, session.bet)

    async def timeout(self, context: GameContext, session: GameSession) -> None:
        await context.message.channel.send("入力待ちが時間切れで終了しました。")

    async def _resolve(self, context: GameContext, bet: int) -> GameSession | None:
        bet_error = validate_bet(bet)
        if bet_error is not None:
            await context.message.channel.send(bet_error)
            return None
        can_pay, required, points = ensure_balance(
            context.points_repo,
            context.guild_id,
            context.user_id,
            bet,
            max_loss_multiplier=1.0,
        )
        if not can_pay:
            await context.message.channel.send(
                f"ポイントが足りません。（必要: {required} / 所持: {points}）"
            )
            return None

        context.points_repo.add_points(context.guild_id, context.user_id, -bet)

        slot_message = await context.message.channel.send("🎰 | ??? | ??? | ???")
        reels = ["❓", "❓", "❓"]
        for _ in range(SLOT_ANIMATION_STEPS):
            reels = [context.rng.choice(SLOT_SYMBOLS) for _ in range(3)]
            await asyncio.sleep(SLOT_ANIMATION_INTERVAL_SECONDS)
            await slot_message.edit(
                content=f"🎰 | {reels[0]} | {reels[1]} | {reels[2]} |"
            )

        multiplier = self._slot_multiplier(reels)
        payout = apply_payout(
            context.points_repo, context.guild_id, context.user_id, bet, multiplier
        )
        net = payout - bet
        result_line = f"結果: {reels[0]} {reels[1]} {reels[2]}"
        await context.message.channel.send(
            f"{result_line}\n倍率: x{multiplier:.1f} / 差引: {net:+}ポイント"
        )
        return None

    @staticmethod
    def _slot_multiplier(reels: list[str]) -> float:
        if reels[0] == reels[1] == reels[2]:
            if reels[0] in SLOT_RARE_SYMBOLS:
                return 4.5
            return 2.5
        if reels[0] == reels[1] or reels[1] == reels[2] or reels[0] == reels[2]:
            return 1.3
        return 0.0


__all__ = ["SlotGame"]
