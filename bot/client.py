from __future__ import annotations

from dataclasses import dataclass
import asyncio
import math
import random
import time

import discord
from discord.ext import tasks

from bot.constants import SLOT_RARE_SYMBOLS, SLOT_SYMBOLS
from bot.constants import (
    CANCEL_WORDS,
    COIN_ALIASES,
    COIN_LABELS,
    COMMAND_PREFIXES,
    JANKEN_ALIASES,
    JANKEN_LABELS,
)

GAME_COOLDOWN_SECONDS = 1.0
MIN_BET = 100
GAME_INPUT_TIMEOUT_SECONDS = 120.0
HIT_BLOW_DIGITS = 3
HIT_BLOW_MAX_TRIES = 10
HIT_BLOW_TIMEOUT_SECONDS = 120.0
JANKEN_TIMEOUT_SECONDS = 120.0
SLOT_ANIMATION_STEPS = 3
SLOT_ANIMATION_INTERVAL_SECONDS = 0.6

VOICE_POINT_INTERVAL_SECONDS = 7 * 60
VOICE_TICK_SECONDS = 60


@dataclass
class VoiceSession:
    guild_id: int
    channel_id: int
    last_ts: float
    carry_seconds: float
    accruing: bool


@dataclass
class HitBlowSession:
    bet: int
    target: str
    attempts_left: int
    started_ts: float
    last_activity_ts: float
    channel_id: int


@dataclass
class JankenSession:
    bet: int
    started_ts: float
    last_activity_ts: float
    channel_id: int


@dataclass
class GameInputSession:
    game: str
    bet: int | None
    choice: str | None
    started_ts: float
    last_activity_ts: float
    channel_id: int


class BotClient(discord.Client):
    def __init__(
        self,
        *,
        points_repo,
        intents: discord.Intents = discord.Intents.default(),
    ):
        super().__init__(intents=intents)
        self.tree = discord.app_commands.CommandTree(self)
        self.points_repo = points_repo
        self.voice_sessions: dict[int, VoiceSession] = {}
        self.game_sessions: dict[
            int, HitBlowSession | JankenSession | GameInputSession
        ] = {}
        self.game_cooldowns: dict[int, float] = {}

    async def on_ready(self) -> None:
        await self.tree.sync()
        print(f"ログインしました: {self.user}")
        print("起動完了")
        if not self.voice_award_loop.is_running():
            self.voice_award_loop.start()

    async def on_message(self, message: discord.Message) -> None:
        if message.author.bot:
            return
        if message.guild is None:
            return

        user_id = message.author.id
        self.points_repo.award_point_for_message(message.guild.id, user_id)

        handled_session = await self._handle_game_session_message(message)
        if handled_session:
            return

        prefix = self._match_command_prefix(message.content)
        if prefix is None:
            return

        if await self._check_game_cooldown(message):
            return

        await self._handle_game_command(message, prefix)

    async def on_voice_state_update(
        self,
        member: discord.Member,
        before: discord.VoiceState,
        after: discord.VoiceState,
    ) -> None:
        if member.bot:
            return

        now = time.time()
        user_id = member.id
        session = self.voice_sessions.get(user_id)

        if after.channel is None:
            if session is not None:
                self._update_session(session, now=now, accruing=False)
                self._award_from_session(user_id, session)
                self.voice_sessions.pop(user_id, None)
        else:
            if session is None:
                self.voice_sessions[user_id] = VoiceSession(
                    guild_id=member.guild.id,
                    channel_id=after.channel.id,
                    last_ts=now,
                    carry_seconds=0.0,
                    accruing=self._is_voice_eligible(after),
                )
            else:
                session.channel_id = after.channel.id
                self._update_session(
                    session, now=now, accruing=self._is_voice_eligible(after)
                )
                self._award_from_session(user_id, session)

        affected_channels: set[discord.VoiceChannel] = set()
        if before.channel is not None:
            affected_channels.add(before.channel)
        if after.channel is not None:
            affected_channels.add(after.channel)
        if affected_channels:
            self._refresh_voice_channels(
                affected_channels, now=now, exclude_user_id=user_id
            )

    @staticmethod
    def _is_voice_eligible(state: discord.VoiceState | None) -> bool:
        if state is None or state.channel is None:
            return False
        if state.mute or state.self_mute:
            return False
        return len(state.channel.members) >= 2

    @staticmethod
    def _update_session(session: VoiceSession, *, now: float, accruing: bool) -> None:
        elapsed = max(0.0, now - session.last_ts)
        if session.accruing:
            session.carry_seconds += elapsed
        session.last_ts = now
        session.accruing = accruing

    def _award_from_session(self, user_id: int, session: VoiceSession) -> None:
        if session.carry_seconds < VOICE_POINT_INTERVAL_SECONDS:
            return
        points = int(session.carry_seconds // VOICE_POINT_INTERVAL_SECONDS)
        session.carry_seconds -= points * VOICE_POINT_INTERVAL_SECONDS
        self.points_repo.add_points(session.guild_id, user_id, points)

    def _refresh_voice_channels(
        self,
        channels: set[discord.abc.Connectable],
        *,
        now: float,
        exclude_user_id: int | None = None,
    ) -> None:
        for channel in channels:
            for channel_member in channel.members:
                if channel_member.bot:
                    continue
                if exclude_user_id is not None and channel_member.id == exclude_user_id:
                    continue
                state = channel_member.voice
                if state is None or state.channel is None:
                    session = self.voice_sessions.get(channel_member.id)
                    if session is None:
                        continue
                    self._update_session(session, now=now, accruing=False)
                    self._award_from_session(channel_member.id, session)
                    self.voice_sessions.pop(channel_member.id, None)
                    continue
                session = self.voice_sessions.get(channel_member.id)
                if session is None:
                    self.voice_sessions[channel_member.id] = VoiceSession(
                        guild_id=channel_member.guild.id,
                        channel_id=state.channel.id,
                        last_ts=now,
                        carry_seconds=0.0,
                        accruing=self._is_voice_eligible(state),
                    )
                    continue
                session.channel_id = state.channel.id
                self._update_session(
                    session, now=now, accruing=self._is_voice_eligible(state)
                )
                self._award_from_session(channel_member.id, session)

    @tasks.loop(seconds=VOICE_TICK_SECONDS)
    async def voice_award_loop(self) -> None:
        now = time.time()
        for user_id, session in list(self.voice_sessions.items()):
            guild = self.get_guild(session.guild_id)
            if guild is None:
                self.voice_sessions.pop(user_id, None)
                continue
            member = guild.get_member(user_id)
            if member is None or member.voice is None:
                self._update_session(session, now=now, accruing=False)
                self._award_from_session(user_id, session)
                self.voice_sessions.pop(user_id, None)
                continue
            state = member.voice
            if state.channel is None:
                self._update_session(session, now=now, accruing=False)
                self._award_from_session(user_id, session)
                self.voice_sessions.pop(user_id, None)
                continue
            session.channel_id = state.channel.id
            self._update_session(
                session, now=now, accruing=self._is_voice_eligible(state)
            )
            self._award_from_session(user_id, session)

    async def _check_game_cooldown(self, message: discord.Message) -> bool:
        now = time.time()
        user_id = message.author.id
        last_ts = self.game_cooldowns.get(user_id)
        if last_ts is not None and now - last_ts < GAME_COOLDOWN_SECONDS:
            await message.channel.send(
                "クールタイム中です。少し待ってから実行してください。"
            )
            return True
        self.game_cooldowns[user_id] = now
        return False

    async def _handle_game_session_message(self, message: discord.Message) -> bool:
        session = self.game_sessions.get(message.author.id)
        if session is None:
            return False
        if message.channel.id != session.channel_id:
            await message.channel.send(
                "進行中のゲームがあります。開始したチャンネルで続けてください。"
            )
            return True

        now = time.time()
        if isinstance(session, GameInputSession):
            if now - session.last_activity_ts >= GAME_INPUT_TIMEOUT_SECONDS:
                self.game_sessions.pop(message.author.id, None)
                await message.channel.send("入力待ちが時間切れで終了しました。")
                return False
            session.last_activity_ts = now
            if self._is_cancel_message(message.content):
                self.game_sessions.pop(message.author.id, None)
                await message.channel.send("ゲームをキャンセルしました。")
                return True
            await self._handle_game_input_message(message, session)
            return True
        if isinstance(session, HitBlowSession):
            if now - session.last_activity_ts >= HIT_BLOW_TIMEOUT_SECONDS:
                self.game_sessions.pop(message.author.id, None)
                await message.channel.send("hit&blow は時間切れで終了しました。")
                return False
            session.last_activity_ts = now
            await self._handle_hit_blow_answer(message, session)
            return True

        if isinstance(session, JankenSession):
            if now - session.last_activity_ts >= JANKEN_TIMEOUT_SECONDS:
                self.game_sessions.pop(message.author.id, None)
                await message.channel.send("じゃんけんは時間切れで終了しました。")
                return False
            session.last_activity_ts = now
            await self._handle_janken_answer(message, session)
            return True

        return False

    async def _handle_game_command(self, message: discord.Message, prefix: str) -> None:
        content = message.content.strip()
        if not content.startswith(prefix):
            return
        raw = content[len(prefix) :].strip()
        if raw == "":
            await message.channel.send("ゲームコマンドを指定してください。")
            return
        parts = raw.split()
        command = parts[0].lower()
        args = parts[1:]

        if message.author.id in self.game_sessions:
            await message.channel.send(
                "進行中のゲームがあるため、新しいゲームは開始できません。"
            )
            return

        if command in {"slot"}:
            await self._start_slot(message, args)
            return
        if command in {"omikuji"}:
            await self._start_omikuji(message, args)
            return
        if command in {"hitblow", "hit"}:
            await self._start_hit_blow(message, args)
            return
        if command in {"janken", "rps"}:
            await self._start_janken(message, args)
            return
        if command in {"coin", "cointoss"}:
            await self._start_coin_toss(message, args)
            return

        await message.channel.send("不明なゲームコマンドです。")

    async def _start_slot(self, message: discord.Message, args: list[str]) -> None:
        bet = self._parse_bet(args)
        if bet is None:
            self._start_game_input_session(message, game="slot", bet=None, choice=None)
            await message.channel.send(
                "スロットを開始します。賭けるポイントを入力してください。"
            )
            return
        await self._resolve_slot(message, bet)

    async def _start_omikuji(self, message: discord.Message, args: list[str]) -> None:
        bet = self._parse_bet(args)
        if bet is None:
            self._start_game_input_session(
                message, game="omikuji", bet=None, choice=None
            )
            await message.channel.send(
                "おみくじを開始します。賭けるポイントを入力してください。"
            )
            return
        await self._resolve_omikuji(message, bet)

    async def _start_hit_blow(self, message: discord.Message, args: list[str]) -> None:
        bet = self._parse_bet(args)
        if bet is None:
            self._start_game_input_session(
                message, game="hitblow", bet=None, choice=None
            )
            await message.channel.send(
                "hit&blow を開始します。賭けるポイントを入力してください。"
            )
            return
        await self._start_hit_blow_session(message, bet)

    async def _start_janken(self, message: discord.Message, args: list[str]) -> None:
        bet, choice = self._parse_bet_with_choice(args, self._parse_janken_choice)
        if bet is None:
            self._start_game_input_session(
                message, game="janken", bet=None, choice=choice
            )
            await message.channel.send(
                "じゃんけん開始！賭けるポイントを入力してください。"
            )
            return
        bet_error = self._validate_bet(bet)
        if bet_error is not None:
            await message.channel.send(bet_error)
            return

        if choice is None:
            self._start_game_input_session(message, game="janken", bet=bet, choice=None)
            await message.channel.send(
                "じゃんけん開始！グー/チョキ/パーで返答してください。"
            )
            return

        await self._start_janken_session(message, bet, choice)

    async def _start_coin_toss(self, message: discord.Message, args: list[str]) -> None:
        bet, choice = self._parse_bet_with_choice(args, self._parse_coin_choice)
        if bet is None or choice is None:
            if bet is not None:
                bet_error = self._validate_bet(bet)
                if bet_error is not None:
                    await message.channel.send(bet_error)
                    return
                can_pay, required, points = self._ensure_balance(
                    message.guild.id, message.author.id, bet, max_loss_multiplier=1.0
                )
                if not can_pay:
                    await message.channel.send(
                        f"ポイントが足りません。（必要: {required} / 所持: {points}）"
                    )
                    return
            self._start_game_input_session(message, game="coin", bet=bet, choice=choice)
            await message.channel.send(
                "コイントス開始！賭けるポイントと表/裏を入力してください。"
            )
            return
        bet_error = self._validate_bet(bet)
        if bet_error is not None:
            await message.channel.send(bet_error)
            return

        await self._resolve_coin_toss(message, bet, choice)

    async def _handle_hit_blow_answer(
        self, message: discord.Message, session: HitBlowSession
    ) -> None:
        content = message.content.strip()
        if self._is_cancel_message(content):
            self.game_sessions.pop(message.author.id, None)
            await message.channel.send(
                "hit&blow を終了しました。賭けるポイントは没収されます。"
            )
            return

        normalized = _normalize_digits(content)
        if not normalized.isdigit() or len(normalized) != HIT_BLOW_DIGITS:
            await message.channel.send("3桁の数字で入力してください。")
            return
        if len(set(normalized)) != HIT_BLOW_DIGITS:
            await message.channel.send("数字は重複なしで入力してください。")
            return

        session.attempts_left -= 1
        hits, blows = self._count_hits_blows(normalized, session.target)

        if hits == HIT_BLOW_DIGITS:
            self.game_sessions.pop(message.author.id, None)
            payout = self._apply_payout(
                message.guild.id, message.author.id, session.bet, 3.0
            )
            net = payout - session.bet
            await message.channel.send(
                f"🎉 正解！ {session.target}\n倍率: x3.0 / 差引: {net:+}ポイント"
            )
            return

        if session.attempts_left <= 0:
            self.game_sessions.pop(message.author.id, None)
            await message.channel.send(
                f"残念！正解は {session.target} でした。賭けるポイントは没収されます。"
            )
            return

        await message.channel.send(
            f"HIT: {hits} / BLOW: {blows} / 残り {session.attempts_left} 回"
        )

    async def _handle_janken_answer(
        self, message: discord.Message, session: JankenSession
    ) -> None:
        if self._is_cancel_message(message.content):
            self.game_sessions.pop(message.author.id, None)
            await message.channel.send(
                "じゃんけんをキャンセルしました。賭けるポイントは没収されます。"
            )
            return
        choice = self._parse_janken_choice(message.content.strip())
        if choice is None:
            await message.channel.send("グー/チョキ/パーで入力してください。")
            return
        await self._resolve_janken(message, session, choice)

    async def _resolve_janken(
        self, message: discord.Message, session: JankenSession, choice: str
    ) -> None:
        opponent = random.choice(["rock", "scissors", "paper"])
        result = self._janken_result(choice, opponent)
        if result == "draw":
            await message.channel.send("あいこ！もう一回（グー/チョキ/パー）")
            return
        self.game_sessions.pop(message.author.id, None)
        multiplier = 2.0 if result == "win" else 0.0
        payout = self._apply_payout(
            message.guild.id, message.author.id, session.bet, multiplier
        )
        net = payout - session.bet
        choice_label = self._janken_label(choice)
        opponent_label = self._janken_label(opponent)
        outcome_label = "勝ち" if result == "win" else "負け"
        await message.channel.send(
            f"じゃんけん {choice_label} vs {opponent_label}: {outcome_label}\n"
            f"倍率: x{multiplier:.1f} / 差引: {net:+}ポイント"
        )

    def _validate_bet(self, bet: int) -> str | None:
        if bet <= 0:
            return "賭けるポイントは1以上で指定してください。"
        if bet < MIN_BET:
            return f"賭けるポイントは {MIN_BET} 以上で指定してください。"
        return None

    def _ensure_balance(
        self, guild_id: int, user_id: int, bet: int, *, max_loss_multiplier: float
    ) -> tuple[bool, int, int]:
        points = self.points_repo.get_user_points(guild_id, user_id) or 0
        required = int(math.ceil(bet * max_loss_multiplier))
        return points >= required, required, points

    @staticmethod
    def _parse_bet(args: list[str]) -> int | None:
        if not args:
            return None
        if len(args) == 0:
            return None
        for arg in args:
            normalized = _normalize_digits(arg)
            if normalized.isdigit():
                return int(normalized)
        return None

    def _start_game_input_session(
        self,
        message: discord.Message,
        *,
        game: str,
        bet: int | None,
        choice: str | None,
    ) -> None:
        session = GameInputSession(
            game=game,
            bet=bet,
            choice=choice,
            started_ts=time.time(),
            last_activity_ts=time.time(),
            channel_id=message.channel.id,
        )
        self.game_sessions[message.author.id] = session

    async def _handle_game_input_message(
        self, message: discord.Message, session: GameInputSession
    ) -> None:
        raw_args = message.content.strip().split()
        if session.game in {"slot", "omikuji", "hitblow"}:
            if session.bet is None:
                bet = self._parse_bet(raw_args)
                if bet is None:
                    await message.channel.send("賭けるポイントを入力してください。")
                    return
                bet_error = self._validate_bet(bet)
                if bet_error is not None:
                    await message.channel.send(bet_error)
                    return
                max_loss_multiplier = 1.5 if session.game == "omikuji" else 1.0
                can_pay, required, points = self._ensure_balance(
                    message.guild.id,
                    message.author.id,
                    bet,
                    max_loss_multiplier=max_loss_multiplier,
                )
                if not can_pay:
                    await message.channel.send(
                        f"ポイントが足りません。（必要: {required} / 所持: {points}）"
                    )
                    return
                session.bet = bet

            if session.game == "slot":
                self.game_sessions.pop(message.author.id, None)
                await self._resolve_slot(message, session.bet)
                return
            if session.game == "omikuji":
                self.game_sessions.pop(message.author.id, None)
                await self._resolve_omikuji(message, session.bet)
                return
            if session.game == "hitblow":
                self.game_sessions.pop(message.author.id, None)
                await self._start_hit_blow_session(message, session.bet)
                return

        if session.game in {"janken", "coin"}:
            parser = (
                self._parse_janken_choice
                if session.game == "janken"
                else self._parse_coin_choice
            )
            bet, choice = self._parse_bet_with_choice(raw_args, parser)
            if session.bet is None and bet is not None:
                bet_error = self._validate_bet(bet)
                if bet_error is not None:
                    await message.channel.send(bet_error)
                    return
                can_pay, required, points = self._ensure_balance(
                    message.guild.id,
                    message.author.id,
                    bet,
                    max_loss_multiplier=1.0,
                )
                if not can_pay:
                    await message.channel.send(
                        f"ポイントが足りません。（必要: {required} / 所持: {points}）"
                    )
                    return
                session.bet = bet
            if session.choice is None and choice is not None:
                session.choice = choice

            if session.bet is None:
                await message.channel.send("賭けるポイントを入力してください。")
                return
            if session.choice is None:
                prompt = (
                    "グー/チョキ/パーで入力してください。"
                    if session.game == "janken"
                    else "表/裏で入力してください。"
                )
                await message.channel.send(prompt)
                return

            self.game_sessions.pop(message.author.id, None)
            if session.game == "janken":
                await self._start_janken_session(message, session.bet, session.choice)
                return
            await self._resolve_coin_toss(message, session.bet, session.choice)

    async def _resolve_slot(self, message: discord.Message, bet: int) -> None:
        bet_error = self._validate_bet(bet)
        if bet_error is not None:
            await message.channel.send(bet_error)
            return
        can_pay, required, points = self._ensure_balance(
            message.guild.id, message.author.id, bet, max_loss_multiplier=1.0
        )
        if not can_pay:
            await message.channel.send(
                f"ポイントが足りません。（必要: {required} / 所持: {points}）"
            )
            return

        self.points_repo.add_points(message.guild.id, message.author.id, -bet)

        slot_message = await message.channel.send("🎰 | ??? | ??? | ???")
        reels = ["❓", "❓", "❓"]
        for _ in range(SLOT_ANIMATION_STEPS):
            reels = [random.choice(SLOT_SYMBOLS) for _ in range(3)]
            await asyncio.sleep(SLOT_ANIMATION_INTERVAL_SECONDS)
            await slot_message.edit(
                content=f"🎰 | {reels[0]} | {reels[1]} | {reels[2]} |"
            )

        multiplier = self._slot_multiplier(reels)
        payout = self._apply_payout(
            message.guild.id, message.author.id, bet, multiplier
        )
        net = payout - bet
        result_line = f"結果: {reels[0]} {reels[1]} {reels[2]}"
        await message.channel.send(
            f"{result_line}\n倍率: x{multiplier:.1f} / 差引: {net:+}ポイント"
        )

    async def _resolve_omikuji(self, message: discord.Message, bet: int) -> None:
        bet_error = self._validate_bet(bet)
        if bet_error is not None:
            await message.channel.send(bet_error)
            return
        can_pay, required, points = self._ensure_balance(
            message.guild.id, message.author.id, bet, max_loss_multiplier=1.5
        )
        if not can_pay:
            await message.channel.send(
                f"ポイントが足りません。（必要: {required} / 所持: {points}）"
            )
            return

        self.points_repo.add_points(message.guild.id, message.author.id, -bet)
        outcome, multiplier = self._draw_omikuji()
        payout = self._apply_payout(
            message.guild.id, message.author.id, bet, multiplier
        )
        net = payout - bet
        await message.channel.send(
            f"おみくじ結果: {outcome}\n倍率: x{multiplier:.1f} / 差引: {net:+}ポイント"
        )

    async def _start_hit_blow_session(self, message: discord.Message, bet: int) -> None:
        bet_error = self._validate_bet(bet)
        if bet_error is not None:
            await message.channel.send(bet_error)
            return
        can_pay, required, points = self._ensure_balance(
            message.guild.id, message.author.id, bet, max_loss_multiplier=1.0
        )
        if not can_pay:
            await message.channel.send(
                f"ポイントが足りません。（必要: {required} / 所持: {points}）"
            )
            return

        self.points_repo.add_points(message.guild.id, message.author.id, -bet)
        target = "".join(random.sample("0123456789", HIT_BLOW_DIGITS))
        session = HitBlowSession(
            bet=bet,
            target=target,
            attempts_left=HIT_BLOW_MAX_TRIES,
            started_ts=time.time(),
            last_activity_ts=time.time(),
            channel_id=message.channel.id,
        )
        self.game_sessions[message.author.id] = session
        await message.channel.send(
            "hit&blow を開始します。3桁の数字を入力してください。"
            f"（試行 {HIT_BLOW_MAX_TRIES} 回 / {self._cancel_words_label()} で終了）"
        )

    async def _start_janken_session(
        self, message: discord.Message, bet: int, choice: str
    ) -> None:
        can_pay, required, points = self._ensure_balance(
            message.guild.id, message.author.id, bet, max_loss_multiplier=1.0
        )
        if not can_pay:
            await message.channel.send(
                f"ポイントが足りません。（必要: {required} / 所持: {points}）"
            )
            return

        self.points_repo.add_points(message.guild.id, message.author.id, -bet)
        session = JankenSession(
            bet=bet,
            started_ts=time.time(),
            last_activity_ts=time.time(),
            channel_id=message.channel.id,
        )
        self.game_sessions[message.author.id] = session
        await self._resolve_janken(message, session, choice)

    async def _resolve_coin_toss(
        self, message: discord.Message, bet: int, choice: str
    ) -> None:
        can_pay, required, points = self._ensure_balance(
            message.guild.id, message.author.id, bet, max_loss_multiplier=1.0
        )
        if not can_pay:
            await message.channel.send(
                f"ポイントが足りません。（必要: {required} / 所持: {points}）"
            )
            return

        self.points_repo.add_points(message.guild.id, message.author.id, -bet)
        result = random.choice(["heads", "tails"])
        multiplier = 1.7 if result == choice else 0.0
        payout = self._apply_payout(
            message.guild.id, message.author.id, bet, multiplier
        )
        net = payout - bet
        result_label = COIN_LABELS.get(result, result)
        choice_label = COIN_LABELS.get(choice, choice)
        await message.channel.send(
            f"コイントス: {result_label}（選択: {choice_label}）\n"
            f"倍率: x{multiplier:.1f} / 差引: {net:+}ポイント"
        )

    @staticmethod
    def _is_cancel_message(raw: str) -> bool:
        normalized = raw.strip().lower()
        return normalized in {word.lower() for word in CANCEL_WORDS}

    @staticmethod
    def _cancel_words_label() -> str:
        return "/".join(CANCEL_WORDS)

    @staticmethod
    def _match_command_prefix(content: str) -> str | None:
        for prefix in COMMAND_PREFIXES:
            if content.startswith(prefix):
                return prefix
        return None

    @staticmethod
    def _parse_bet_with_choice(
        args: list[str], parser
    ) -> tuple[int | None, str | None]:
        bet = None
        choice = None
        for arg in args:
            normalized = _normalize_digits(arg)
            if bet is None and normalized.isdigit():
                bet = int(normalized)
                continue
            if choice is None:
                parsed = parser(normalized)
                if parsed is not None:
                    choice = parsed
        return bet, choice

    @staticmethod
    def _parse_janken_choice(raw: str) -> str | None:
        normalized = raw.strip().lower()
        for key, aliases in JANKEN_ALIASES.items():
            if normalized in {alias.lower() for alias in aliases}:
                return key
        return None

    @staticmethod
    def _parse_coin_choice(raw: str) -> str | None:
        normalized = raw.strip().lower()
        for key, aliases in COIN_ALIASES.items():
            if normalized in {alias.lower() for alias in aliases}:
                return key
        return None

    @staticmethod
    def _janken_result(player: str, opponent: str) -> str:
        if player == opponent:
            return "draw"
        wins = {
            ("rock", "scissors"),
            ("scissors", "paper"),
            ("paper", "rock"),
        }
        return "win" if (player, opponent) in wins else "lose"

    @staticmethod
    def _janken_label(choice: str) -> str:
        return JANKEN_LABELS.get(choice, choice)

    @staticmethod
    def _count_hits_blows(guess: str, target: str) -> tuple[int, int]:
        hits = sum(1 for i, digit in enumerate(guess) if digit == target[i])
        blows = sum(
            1 for i, digit in enumerate(guess) if digit != target[i] and digit in target
        )
        return hits, blows

    @staticmethod
    def _slot_multiplier(reels: list[str]) -> float:
        if reels[0] == reels[1] == reels[2]:
            if reels[0] in SLOT_RARE_SYMBOLS:
                return 4.5
            return 2.5
        if reels[0] == reels[1] or reels[1] == reels[2] or reels[0] == reels[2]:
            return 1.3
        return 0.0

    @staticmethod
    def _draw_omikuji() -> tuple[str, float]:
        outcomes = [
            ("大吉", 2.0, 5),
            ("中吉", 1.7, 10),
            ("小吉", 1.4, 20),
            ("末吉", 1.0, 25),
            ("凶", 0.0, 30),
            ("大凶", -0.5, 10),
        ]
        weights = [item[2] for item in outcomes]
        selected = random.choices(outcomes, weights=weights, k=1)[0]
        return selected[0], selected[1]

    def _apply_payout(
        self, guild_id: int, user_id: int, bet: int, multiplier: float
    ) -> int:
        payout = int(round(bet * multiplier))
        if payout != 0:
            self.points_repo.add_points(guild_id, user_id, payout)
        return payout


def _normalize_digits(raw: str) -> str:
    return raw.translate(
        str.maketrans(
            "０１２３４５６７８９",
            "0123456789",
        )
    )


def create_client(*, points_repo) -> BotClient:
    intents = discord.Intents.default()
    intents.message_content = True
    intents.voice_states = True
    return BotClient(intents=intents, points_repo=points_repo)


__all__ = ["BotClient", "create_client"]
