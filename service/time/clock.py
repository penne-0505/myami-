from __future__ import annotations

import time


class Clock:
    def now(self) -> float:
        raise NotImplementedError


class SystemClock(Clock):
    def now(self) -> float:
        return time.time()


__all__ = ["Clock", "SystemClock"]
