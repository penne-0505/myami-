from __future__ import annotations

import random
from typing import Sequence, TypeVar

T = TypeVar("T")


class Rng:
    def choice(self, seq: Sequence[T]) -> T:
        raise NotImplementedError

    def choices(self, population: Sequence[T], *, weights: Sequence[float], k: int) -> list[T]:
        raise NotImplementedError

    def sample(self, population: Sequence[T], k: int) -> list[T]:
        raise NotImplementedError


class SystemRng(Rng):
    def choice(self, seq: Sequence[T]) -> T:
        return random.choice(seq)

    def choices(self, population: Sequence[T], *, weights: Sequence[float], k: int) -> list[T]:
        return random.choices(population, weights=weights, k=k)

    def sample(self, population: Sequence[T], k: int) -> list[T]:
        return random.sample(population, k)


__all__ = ["Rng", "SystemRng"]
