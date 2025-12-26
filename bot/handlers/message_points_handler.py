from __future__ import annotations

import discord


class MessagePointsHandler:
    def __init__(self, *, points_repo) -> None:
        self.points_repo = points_repo

    async def handle(self, message: discord.Message) -> None:
        if message.author.bot:
            return
        if message.guild is None:
            return
        self.points_repo.award_point_for_message(message.guild.id, message.author.id)


__all__ = ["MessagePointsHandler"]
