from __future__ import annotations

from dataclasses import dataclass

import discord

from service.random.rng import Rng
from service.time.clock import Clock
from service.sessions.game_sessions import GameSession


@dataclass
class GameContext:
    guild_id: int
    channel_id: int
    user_id: int
    message: discord.Message
    points_repo: object
    now: float
    rng: Rng
    clock: Clock


class BaseGame:
    command_names: set[str]

    async def start(self, context: GameContext, args: list[str]) -> GameSession | None:
        raise NotImplementedError

    async def handle_input(
        self, context: GameContext, raw: str, session: GameSession
    ) -> GameSession | None:
        raise NotImplementedError

    async def timeout(self, context: GameContext, session: GameSession) -> None:
        raise NotImplementedError


__all__ = ["BaseGame", "GameContext"]
