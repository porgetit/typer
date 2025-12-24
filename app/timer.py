"""Simple high-resolution timer for the typing session."""

import time
from typing import Optional


class GameTimer:
    def __init__(self) -> None:
        self.started_at: Optional[float] = None
        self.finished_at: Optional[float] = None

    @property
    def started(self) -> bool:
        return self.started_at is not None

    @property
    def finished(self) -> bool:
        return self.finished_at is not None

    def start(self) -> None:
        if self.started_at is None:
            self.started_at = time.perf_counter()

    def stop(self) -> None:
        if self.started_at is not None and self.finished_at is None:
            self.finished_at = time.perf_counter()

    def reset(self) -> None:
        self.started_at = None
        self.finished_at = None

    def elapsed(self) -> float:
        if self.started_at is None:
            return 0.0
        end = self.finished_at or time.perf_counter()
        return max(0.0, end - self.started_at)
