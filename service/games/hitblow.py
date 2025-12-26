from __future__ import annotations

from service.games.base import BaseGame, GameContext
from service.games.support import (
    apply_payout,
    cancel_words_label,
    ensure_balance,
    is_cancel_message,
    normalize_digits,
    parse_bet,
    validate_bet,
)
from service.sessions.game_sessions import GameInputSession, GameSession, HitBlowSession

HIT_BLOW_DIGITS = 3
HIT_BLOW_MAX_TRIES = 10


class HitBlowGame(BaseGame):
    command_names = {"hitblow", "hit"}
    game_key = "hitblow"

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
                "hit&blow を開始します。賭けるポイントを入力してください。"
            )
            return session
        return await self._start_session(context, bet)

    async def handle_input(
        self, context: GameContext, raw: str, session: GameSession
    ) -> GameSession | None:
        if isinstance(session, GameInputSession):
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
            return await self._start_session(context, session.bet)

        if not isinstance(session, HitBlowSession):
            return session

        content = raw.strip()
        if is_cancel_message(content):
            await context.message.channel.send(
                "hit&blow を終了しました。賭けるポイントは没収されます。"
            )
            return None

        normalized = normalize_digits(content)
        if not normalized.isdigit() or len(normalized) != HIT_BLOW_DIGITS:
            await context.message.channel.send("3桁の数字で入力してください。")
            return session
        if len(set(normalized)) != HIT_BLOW_DIGITS:
            await context.message.channel.send("数字は重複なしで入力してください。")
            return session

        session.attempts_left -= 1
        hits, blows = self._count_hits_blows(normalized, session.target)

        if hits == HIT_BLOW_DIGITS:
            payout = apply_payout(
                context.points_repo, context.guild_id, context.user_id, session.bet, 3.0
            )
            net = payout - session.bet
            await context.message.channel.send(
                f"🎉 正解！ {session.target}\n倍率: x3.0 / 差引: {net:+}ポイント"
            )
            return None

        if session.attempts_left <= 0:
            await context.message.channel.send(
                f"残念！正解は {session.target} でした。賭けるポイントは没収されます。"
            )
            return None

        await context.message.channel.send(
            f"HIT: {hits} / BLOW: {blows} / 残り {session.attempts_left} 回"
        )
        return session

    async def timeout(self, context: GameContext, session: GameSession) -> None:
        await context.message.channel.send("hit&blow は時間切れで終了しました。")

    async def _start_session(self, context: GameContext, bet: int) -> GameSession | None:
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
        target = "".join(context.rng.sample("0123456789", HIT_BLOW_DIGITS))
        session = HitBlowSession(
            game=self.game_key,
            bet=bet,
            target=target,
            attempts_left=HIT_BLOW_MAX_TRIES,
            started_ts=context.now,
            last_activity_ts=context.now,
            channel_id=context.channel_id,
        )
        await context.message.channel.send(
            "hit&blow を開始します。3桁の数字を入力してください。"
            f"（試行 {HIT_BLOW_MAX_TRIES} 回 / {cancel_words_label()} で終了）"
        )
        return session

    @staticmethod
    def _count_hits_blows(guess: str, target: str) -> tuple[int, int]:
        hits = sum(1 for i, digit in enumerate(guess) if digit == target[i])
        blows = sum(
            1 for i, digit in enumerate(guess) if digit != target[i] and digit in target
        )
        return hits, blows


__all__ = ["HitBlowGame"]
