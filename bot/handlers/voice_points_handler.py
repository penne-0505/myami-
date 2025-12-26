from __future__ import annotations

import discord
from discord.ext import tasks

from service.sessions.voice_sessions import VoiceSession, VoiceSessionStore
from service.time.clock import Clock, SystemClock

VOICE_POINT_INTERVAL_SECONDS = 7 * 60
VOICE_TICK_SECONDS = 60


class VoicePointsHandler:
    def __init__(self, *, points_repo, clock: Clock | None = None) -> None:
        self.points_repo = points_repo
        self.clock = clock or SystemClock()
        self.sessions = VoiceSessionStore()
        self._client: discord.Client | None = None

    async def handle_state_update(
        self,
        member: discord.Member,
        before: discord.VoiceState,
        after: discord.VoiceState,
        *,
        now: float,
    ) -> None:
        if member.bot:
            return

        user_id = member.id
        session = self.sessions.get(user_id)

        if after.channel is None:
            if session is not None:
                self._update_session(session, now=now, accruing=False)
                self._award_from_session(user_id, session)
                self.sessions.pop(user_id)
        else:
            if session is None:
                self.sessions.set(
                    user_id,
                    VoiceSession(
                        guild_id=member.guild.id,
                        channel_id=after.channel.id,
                        last_ts=now,
                        carry_seconds=0.0,
                        accruing=self._is_voice_eligible(after),
                    ),
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

    async def tick(self, client: discord.Client, *, now: float) -> None:
        for user_id, session in self.sessions.items():
            guild = client.get_guild(session.guild_id)
            if guild is None:
                self.sessions.pop(user_id)
                continue
            member = guild.get_member(user_id)
            if member is None or member.voice is None:
                self._update_session(session, now=now, accruing=False)
                self._award_from_session(user_id, session)
                self.sessions.pop(user_id)
                continue
            state = member.voice
            if state.channel is None:
                self._update_session(session, now=now, accruing=False)
                self._award_from_session(user_id, session)
                self.sessions.pop(user_id)
                continue
            session.channel_id = state.channel.id
            self._update_session(session, now=now, accruing=self._is_voice_eligible(state))
            self._award_from_session(user_id, session)

    def ensure_background_loop(self, client: discord.Client) -> None:
        self._client = client
        if not self.voice_award_loop.is_running():
            self.voice_award_loop.start()

    @tasks.loop(seconds=VOICE_TICK_SECONDS)
    async def voice_award_loop(self) -> None:
        if self._client is None:
            return
        await self.tick(self._client, now=self.clock.now())

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
                    session = self.sessions.get(channel_member.id)
                    if session is None:
                        continue
                    self._update_session(session, now=now, accruing=False)
                    self._award_from_session(channel_member.id, session)
                    self.sessions.pop(channel_member.id)
                    continue
                session = self.sessions.get(channel_member.id)
                if session is None:
                    self.sessions.set(
                        channel_member.id,
                        VoiceSession(
                            guild_id=channel_member.guild.id,
                            channel_id=state.channel.id,
                            last_ts=now,
                            carry_seconds=0.0,
                            accruing=self._is_voice_eligible(state),
                        ),
                    )
                    continue
                session.channel_id = state.channel.id
                self._update_session(session, now=now, accruing=self._is_voice_eligible(state))
                self._award_from_session(channel_member.id, session)


__all__ = ["VoicePointsHandler"]
