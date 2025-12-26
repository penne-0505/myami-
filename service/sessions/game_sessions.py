from __future__ import annotations

from dataclasses import dataclass


@dataclass
class GameSession:
    game: str
    started_ts: float
    last_activity_ts: float
    channel_id: int


@dataclass
class GameInputSession(GameSession):
    bet: int | None
    choice: str | None


@dataclass
class HitBlowSession(GameSession):
    bet: int
    target: str
    attempts_left: int


@dataclass
class JankenSession(GameSession):
    bet: int


class GameSessionStore:
    def __init__(self) -> None:
        self._sessions: dict[int, GameSession] = {}

    def get(self, user_id: int) -> GameSession | None:
        return self._sessions.get(user_id)

    def set(self, user_id: int, session: GameSession) -> None:
        self._sessions[user_id] = session

    def pop(self, user_id: int) -> GameSession | None:
        return self._sessions.pop(user_id, None)

    def has(self, user_id: int) -> bool:
        return user_id in self._sessions


__all__ = [
    "GameSession",
    "GameInputSession",
    "HitBlowSession",
    "JankenSession",
    "GameSessionStore",
]
