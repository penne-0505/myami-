from __future__ import annotations

from dataclasses import dataclass


@dataclass
class VoiceSession:
    guild_id: int
    channel_id: int
    last_ts: float
    carry_seconds: float
    accruing: bool


class VoiceSessionStore:
    def __init__(self) -> None:
        self._sessions: dict[int, VoiceSession] = {}

    def get(self, user_id: int) -> VoiceSession | None:
        return self._sessions.get(user_id)

    def set(self, user_id: int, session: VoiceSession) -> None:
        self._sessions[user_id] = session

    def pop(self, user_id: int) -> VoiceSession | None:
        return self._sessions.pop(user_id, None)

    def items(self) -> list[tuple[int, VoiceSession]]:
        return list(self._sessions.items())


__all__ = ["VoiceSession", "VoiceSessionStore"]
