from __future__ import annotations

from service.games.base import BaseGame
from service.games.coin import CoinGame
from service.games.hitblow import HitBlowGame
from service.games.janken import JankenGame
from service.games.omikuji import OmikujiGame
from service.games.slot import SlotGame


class GameRegistry:
    def __init__(self) -> None:
        self._games: list[BaseGame] = []
        self._by_command: dict[str, BaseGame] = {}

    def register(self, game: BaseGame) -> None:
        self._games.append(game)
        for command in game.command_names:
            self._by_command[command] = game

    def find(self, command: str) -> BaseGame | None:
        return self._by_command.get(command)


def create_default_registry() -> GameRegistry:
    registry = GameRegistry()
    registry.register(SlotGame())
    registry.register(OmikujiGame())
    registry.register(HitBlowGame())
    registry.register(JankenGame())
    registry.register(CoinGame())
    return registry


__all__ = ["GameRegistry", "create_default_registry"]
