from __future__ import annotations

from service.games.base import BaseGame, GameContext
from service.games.support import apply_payout, ensure_balance, parse_bet, validate_bet
from service.sessions.game_sessions import GameInputSession, GameSession


class OmikujiGame(BaseGame):
    command_names = {"omikuji"}
    game_key = "omikuji"

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
                "おみくじを開始します。賭けるポイントを入力してください。"
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
                max_loss_multiplier=1.5,
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
            max_loss_multiplier=1.5,
        )
        if not can_pay:
            await context.message.channel.send(
                f"ポイントが足りません。（必要: {required} / 所持: {points}）"
            )
            return None

        context.points_repo.add_points(context.guild_id, context.user_id, -bet)
        outcome, multiplier = self._draw_omikuji(context)
        payout = apply_payout(
            context.points_repo, context.guild_id, context.user_id, bet, multiplier
        )
        net = payout - bet
        await context.message.channel.send(
            f"おみくじ結果: {outcome}\n倍率: x{multiplier:.1f} / 差引: {net:+}ポイント"
        )
        return None

    @staticmethod
    def _draw_omikuji(context: GameContext) -> tuple[str, float]:
        outcomes = [
            ("大吉", 2.0, 5),
            ("中吉", 1.7, 10),
            ("小吉", 1.4, 20),
            ("末吉", 1.0, 25),
            ("凶", 0.0, 30),
            ("大凶", -0.5, 10),
        ]
        weights = [item[2] for item in outcomes]
        selected = context.rng.choices(outcomes, weights=weights, k=1)[0]
        return selected[0], selected[1]


__all__ = ["OmikujiGame"]
