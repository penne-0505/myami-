from __future__ import annotations

import discord

from bot.handlers.message_points_handler import MessagePointsHandler
from bot.handlers.point_game_handler import PointGameHandler
from bot.handlers.voice_points_handler import VoicePointsHandler
from service.games.registry import GameRegistry, create_default_registry
from service.random.rng import Rng, SystemRng
from service.time.clock import Clock, SystemClock


class BotClient(discord.Client):
    def __init__(
        self,
        *,
        points_repo,
        intents: discord.Intents = discord.Intents.default(),
        registry: GameRegistry | None = None,
        clock: Clock | None = None,
        rng: Rng | None = None,
    ):
        super().__init__(intents=intents)
        self.tree = discord.app_commands.CommandTree(self)
        self.points_repo = points_repo
        self.clock = clock or SystemClock()
        self.rng = rng or SystemRng()
        self.registry = registry or create_default_registry()

        self.message_points_handler = MessagePointsHandler(points_repo=points_repo)
        self.voice_handler = VoicePointsHandler(points_repo=points_repo, clock=self.clock)
        self.game_handler = PointGameHandler(
            points_repo=points_repo,
            registry=self.registry,
            clock=self.clock,
            rng=self.rng,
        )

    async def on_ready(self) -> None:
        await self.tree.sync()
        print(f"ログインしました: {self.user}")
        print("起動完了")
        self.voice_handler.ensure_background_loop(self)

    async def on_message(self, message: discord.Message) -> None:
        await self.message_points_handler.handle(message)
        await self.game_handler.handle_message(message)

    async def on_voice_state_update(
        self,
        member: discord.Member,
        before: discord.VoiceState,
        after: discord.VoiceState,
    ) -> None:
        await self.voice_handler.handle_state_update(
            member, before, after, now=self.clock.now()
        )


def create_client(*, points_repo) -> BotClient:
    intents = discord.Intents.default()
    intents.message_content = True
    intents.voice_states = True
    return BotClient(intents=intents, points_repo=points_repo)


__all__ = ["BotClient", "create_client"]
