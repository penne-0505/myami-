from __future__ import annotations

import discord

from bot.constants import COMMAND_PREFIXES
from service.games.base import GameContext
from service.games.registry import GameRegistry
from service.games.support import is_cancel_message
from service.random.rng import Rng, SystemRng
from service.sessions.game_sessions import (
    GameInputSession,
    GameSession,
    GameSessionStore,
    HitBlowSession,
    JankenSession,
)
from service.time.clock import Clock, SystemClock

GAME_COOLDOWN_SECONDS = 1.0
GAME_INPUT_TIMEOUT_SECONDS = 120.0
HIT_BLOW_TIMEOUT_SECONDS = 120.0
JANKEN_TIMEOUT_SECONDS = 120.0


class PointGameHandler:
    def __init__(
        self,
        *,
        points_repo,
        registry: GameRegistry,
        clock: Clock | None = None,
        rng: Rng | None = None,
    ) -> None:
        self.points_repo = points_repo
        self.registry = registry
        self.clock = clock or SystemClock()
        self.rng = rng or SystemRng()
        self.sessions = GameSessionStore()
        self.cooldowns: dict[int, float] = {}

    async def handle_message(self, message: discord.Message) -> bool:
        if message.author.bot:
            return False
        if message.guild is None:
            return False

        user_id = message.author.id
        session = self.sessions.get(user_id)
        if session is not None:
            handled = await self._handle_session_message(message, session)
            if handled:
                return True

        prefix = self._match_command_prefix(message.content)
        if prefix is None:
            return False

        if await self._check_game_cooldown(message):
            return True

        content = message.content.strip()
        if not content.startswith(prefix):
            return False
        raw = content[len(prefix) :].strip()
        if raw == "":
            await message.channel.send("ゲームコマンドを指定してください。")
            return True
        parts = raw.split()
        command = parts[0].lower()
        args = parts[1:]

        if self.sessions.has(user_id):
            await message.channel.send(
                "進行中のゲームがあるため、新しいゲームは開始できません。"
            )
            return True

        game = self.registry.find(command)
        if game is None:
            await message.channel.send("不明なゲームコマンドです。")
            return True

        context = self._build_context(message)
        new_session = await game.start(context, args)
        if new_session is not None:
            self.sessions.set(user_id, new_session)
        return True

    async def _handle_session_message(
        self, message: discord.Message, session: GameSession
    ) -> bool:
        if message.channel.id != session.channel_id:
            await message.channel.send(
                "進行中のゲームがあります。開始したチャンネルで続けてください。"
            )
            return True

        now = self.clock.now()
        game = self.registry.find(session.game)
        if game is None:
            self.sessions.pop(message.author.id)
            return False

        if self._is_timed_out(session, now=now):
            self.sessions.pop(message.author.id)
            if isinstance(session, GameInputSession):
                await message.channel.send("入力待ちが時間切れで終了しました。")
                return False
            context = self._build_context(message, now=now)
            await game.timeout(context, session)
            return False

        if isinstance(session, GameInputSession) and is_cancel_message(message.content):
            self.sessions.pop(message.author.id)
            await message.channel.send("ゲームをキャンセルしました。")
            return True

        session.last_activity_ts = now
        context = self._build_context(message, now=now)
        next_session = await game.handle_input(context, message.content, session)
        if next_session is None:
            self.sessions.pop(message.author.id)
        else:
            self.sessions.set(message.author.id, next_session)
        return True

    async def _check_game_cooldown(self, message: discord.Message) -> bool:
        now = self.clock.now()
        user_id = message.author.id
        last_ts = self.cooldowns.get(user_id)
        if last_ts is not None and now - last_ts < GAME_COOLDOWN_SECONDS:
            await message.channel.send(
                "クールタイム中です。少し待ってから実行してください。"
            )
            return True
        self.cooldowns[user_id] = now
        return False

    @staticmethod
    def _is_timed_out(session: GameSession, *, now: float) -> bool:
        if isinstance(session, GameInputSession):
            return now - session.last_activity_ts >= GAME_INPUT_TIMEOUT_SECONDS
        if isinstance(session, HitBlowSession):
            return now - session.last_activity_ts >= HIT_BLOW_TIMEOUT_SECONDS
        if isinstance(session, JankenSession):
            return now - session.last_activity_ts >= JANKEN_TIMEOUT_SECONDS
        return False

    @staticmethod
    def _match_command_prefix(content: str) -> str | None:
        for prefix in COMMAND_PREFIXES:
            if content.startswith(prefix):
                return prefix
        return None

    def _build_context(self, message: discord.Message, *, now: float | None = None) -> GameContext:
        actual_now = now if now is not None else self.clock.now()
        return GameContext(
            guild_id=message.guild.id,
            channel_id=message.channel.id,
            user_id=message.author.id,
            message=message,
            points_repo=self.points_repo,
            now=actual_now,
            rng=self.rng,
            clock=self.clock,
        )


__all__ = ["PointGameHandler"]
