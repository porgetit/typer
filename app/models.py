from dataclasses import asdict, dataclass
from enum import Enum
from typing import Dict


class GameStatus(str, Enum):
    """Possible lifecycle states for a typing session."""

    NO_TEXT = "no_text"
    READY = "ready"
    RUNNING = "running"
    COMPLETED = "completed"


@dataclass
class GameMetrics:
    """Business metrics shared with the UI."""

    status: GameStatus
    target_length: int
    typed_length: int
    errors: int
    accuracy: float
    wpm: int
    elapsed_seconds: float
    started: bool
    finished: bool

    def to_dict(self) -> Dict[str, object]:
        payload = asdict(self)
        payload["status"] = self.status.value
        return payload
