from __future__ import annotations

from dataclasses import dataclass
import time

import discord
from discord.ext import tasks


VOICE_POINT_INTERVAL_SECONDS = 7 * 60
VOICE_TICK_SECONDS = 60


@dataclass
class VoiceSession:
    guild_id: int
    channel_id: int
    last_ts: float
    carry_seconds: float
    accruing: bool


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
        self.points_repo.award_point_for_message(user_id)

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
        self.points_repo.add_points(user_id, points)

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


def create_client(*, points_repo) -> BotClient:
    intents = discord.Intents.default()
    intents.message_content = True
    intents.voice_states = True
    return BotClient(intents=intents, points_repo=points_repo)


__all__ = ["BotClient", "create_client"]
