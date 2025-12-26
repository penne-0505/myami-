from __future__ import annotations

from service.games.base import BaseGame, GameContext
from service.games.support import (
    apply_payout,
    ensure_balance,
    is_cancel_message,
    janken_label,
    janken_result,
    parse_bet_with_choice,
    parse_janken_choice,
    validate_bet,
)
from service.sessions.game_sessions import GameInputSession, GameSession, JankenSession


class JankenGame(BaseGame):
    command_names = {"janken", "rps"}
    game_key = "janken"

    async def start(self, context: GameContext, args: list[str]) -> GameSession | None:
        bet, choice = parse_bet_with_choice(args, parse_janken_choice)
        if bet is None:
            session = GameInputSession(
                game=self.game_key,
                bet=None,
                choice=choice,
                started_ts=context.now,
                last_activity_ts=context.now,
                channel_id=context.channel_id,
            )
            await context.message.channel.send(
                "じゃんけん開始！賭けるポイントを入力してください。"
            )
            return session

        bet_error = validate_bet(bet)
        if bet_error is not None:
            await context.message.channel.send(bet_error)
            return None

        if choice is None:
            session = GameInputSession(
                game=self.game_key,
                bet=bet,
                choice=None,
                started_ts=context.now,
                last_activity_ts=context.now,
                channel_id=context.channel_id,
            )
            await context.message.channel.send(
                "じゃんけん開始！グー/チョキ/パーで返答してください。"
            )
            return session

        return await self._start_session(context, bet, choice)

    async def handle_input(
        self, context: GameContext, raw: str, session: GameSession
    ) -> GameSession | None:
        if isinstance(session, GameInputSession):
            bet, choice = parse_bet_with_choice(raw.split(), parse_janken_choice)
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
                await context.message.channel.send("グー/チョキ/パーで入力してください。")
                return session

            return await self._start_session(context, session.bet, session.choice)

        if not isinstance(session, JankenSession):
            return session

        if is_cancel_message(raw):
            await context.message.channel.send(
                "じゃんけんをキャンセルしました。賭けるポイントは没収されます。"
            )
            return None
        choice = parse_janken_choice(raw.strip())
        if choice is None:
            await context.message.channel.send("グー/チョキ/パーで入力してください。")
            return session
        return await self._resolve(context, session, choice)

    async def timeout(self, context: GameContext, session: GameSession) -> None:
        await context.message.channel.send("じゃんけんは時間切れで終了しました。")

    async def _start_session(
        self, context: GameContext, bet: int, choice: str
    ) -> GameSession | None:
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
        session = JankenSession(
            game=self.game_key,
            bet=bet,
            started_ts=context.now,
            last_activity_ts=context.now,
            channel_id=context.channel_id,
        )
        return await self._resolve(context, session, choice)

    async def _resolve(
        self, context: GameContext, session: JankenSession, choice: str
    ) -> GameSession | None:
        opponent = context.rng.choice(["rock", "scissors", "paper"])
        result = janken_result(choice, opponent)
        if result == "draw":
            await context.message.channel.send("あいこ！もう一回（グー/チョキ/パー）")
            return session
        multiplier = 2.0 if result == "win" else 0.0
        payout = apply_payout(
            context.points_repo,
            context.guild_id,
            context.user_id,
            session.bet,
            multiplier,
        )
        net = payout - session.bet
        choice_label = janken_label(choice)
        opponent_label = janken_label(opponent)
        outcome_label = "勝ち" if result == "win" else "負け"
        await context.message.channel.send(
            f"じゃんけん {choice_label} vs {opponent_label}: {outcome_label}\n"
            f"倍率: x{multiplier:.1f} / 差引: {net:+}ポイント"
        )
        return None


__all__ = ["JankenGame"]
