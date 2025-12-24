from __future__ import annotations

import discord


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

    async def on_ready(self) -> None:
        await self.tree.sync()
        print(f"ログインしました: {self.user}")
        print("起動完了")

    async def on_message(self, message: discord.Message) -> None:
        if message.author.bot:
            return
        if message.guild is None:
            return

        user_id = message.author.id
        self.points_repo.award_point_for_message(user_id)


def create_client(*, points_repo) -> BotClient:
    intents = discord.Intents.default()
    intents.message_content = True
    return BotClient(intents=intents, points_repo=points_repo)


__all__ = ["BotClient", "create_client"]
