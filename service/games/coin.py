from __future__ import annotations

from service.games.base import BaseGame, GameContext
from service.games.support import (
    apply_payout,
    coin_label,
    ensure_balance,
    parse_bet_with_choice,
    parse_coin_choice,
    validate_bet,
)
from service.sessions.game_sessions import GameInputSession, GameSession


class CoinGame(BaseGame):
    command_names = {"coin", "cointoss"}
    game_key = "coin"

    async def start(self, context: GameContext, args: list[str]) -> GameSession | None:
        bet, choice = parse_bet_with_choice(args, parse_coin_choice)
        if bet is None or choice is None:
            if bet is not None:
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
            session = GameInputSession(
                game=self.game_key,
                bet=bet,
                choice=choice,
                started_ts=context.now,
                last_activity_ts=context.now,
                channel_id=context.channel_id,
            )
            await context.message.channel.send(
                "コイントス開始！賭けるポイントと表/裏を入力してください。"
            )
            return session

        bet_error = validate_bet(bet)
        if bet_error is not None:
            await context.message.channel.send(bet_error)
            return None

        return await self._resolve(context, bet, choice)

    async def handle_input(
        self, context: GameContext, raw: str, session: GameSession
    ) -> GameSession | None:
        if not isinstance(session, GameInputSession):
            return session

        bet, choice = parse_bet_with_choice(raw.split(), parse_coin_choice)
        if session.bet is None and bet is not None:
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
        if session.choice is None and choice is not None:
            session.choice = choice

        if session.bet is None:
            await context.message.channel.send("賭けるポイントを入力してください。")
            return session
        if session.choice is None:
            await context.message.channel.send("表/裏で入力してください。")
            return session

        return await self._resolve(context, session.bet, session.choice)

    async def timeout(self, context: GameContext, session: GameSession) -> None:
        await context.message.channel.send("入力待ちが時間切れで終了しました。")

    async def _resolve(self, context: GameContext, bet: int, choice: str) -> GameSession | None:
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
        result = context.rng.choice(["heads", "tails"])
        multiplier = 1.7 if result == choice else 0.0
        payout = apply_payout(
            context.points_repo, context.guild_id, context.user_id, bet, multiplier
        )
        net = payout - bet
        result_label = coin_label(result)
        choice_label = coin_label(choice)
        await context.message.channel.send(
            f"コイントス: {result_label}（選択: {choice_label}）\n"
            f"倍率: x{multiplier:.1f} / 差引: {net:+}ポイント"
        )
        return None


__all__ = ["CoinGame"]
