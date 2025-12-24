from pathlib import Path
from typing import Dict, Optional

from .metrics import MetricsCalculator
from .models import GameMetrics, GameStatus
from .text_source import TextSource
from .timer import GameTimer


class GameService:
    """Core business logic for the typing game."""

    def __init__(self, text_source: Optional[TextSource] = None) -> None:
        self.text_source = text_source or TextSource()
        self.timer = GameTimer()
        self.text_source.reload_bank()
        self.text_bank = self.text_source.bank()
        self.current_index: int = 0
        self.target_text: str = self.text_bank[0] if self.text_bank else ""
        self.typed_text: str = ""
        self.mistakes: int = 0
        self.history: Dict[int, GameMetrics] = {}
        self.session_recorded: bool = False
        self.is_custom: bool = False
        self.status: GameStatus = GameStatus.NO_TEXT if not self.target_text else GameStatus.READY

    def load_demo_text(self) -> Dict[str, object]:
        # Align demo with first item in the bank for consistency.
        self._sync_bank()
        self.current_index = 0
        self.target_text = self.text_bank[0] if self.text_bank else ""
        self.is_custom = False
        return self._initialize_session(include_text=True)

    def load_text_file(self, path: str) -> Dict[str, object]:
        self.target_text = self.text_source.load_from_path(Path(path))
        # Custom text does not alter the bank index.
        self.is_custom = True
        return self._initialize_session(include_text=True)

    def set_text(self, text: str) -> Dict[str, object]:
        self.target_text = (text or "").replace("\r\n", "\n").strip("\n")
        self.is_custom = True
        return self._initialize_session(include_text=True)

    def current(self) -> Dict[str, object]:
        self._sync_bank()
        return self._initialize_session(include_text=True)

    def reset(self) -> Dict[str, object]:
        return self._initialize_session(include_text=True)

    def repeat_current(self) -> Dict[str, object]:
        return self._initialize_session(include_text=True)

    def restart_progress(self) -> Dict[str, object]:
        self.text_source.reload_bank()
        self._sync_bank()
        self.history = {}
        self.current_index = 0
        self.target_text = self.text_bank[0] if self.text_bank else ""
        self.is_custom = False
        return self._initialize_session(include_text=True)

    def next_text(self) -> Dict[str, object]:
        if not self.text_bank:
            self.target_text = ""
            return self._initialize_session(include_text=True)

        if self.current_index < len(self.text_bank) - 1:
            self.current_index += 1
        self.target_text = self.text_bank[self.current_index]
        self.is_custom = False
        return self._initialize_session(include_text=True)

    def submit_input(self, typed: str) -> Dict[str, object]:
        if not self.target_text:
            self.status = GameStatus.NO_TEXT
            self.timer.reset()
            return self._snapshot()

        # Keep inputs aligned to the target length to avoid runaway typing.
        normalized = (typed or "").replace("\r\n", "\n")
        if self.target_text:
            normalized = normalized[: len(self.target_text)]

        prev_len = len(self.typed_text)
        incoming_len = len(normalized)

        # Backspace branch: allow shrinking the accepted text.
        if incoming_len < prev_len:
            # Rewind while keeping only the longest correct prefix of the provided text.
            limit = min(incoming_len, len(self.target_text))
            new_text = ""
            for i in range(limit):
                if normalized[i] == self.target_text[i]:
                    new_text += normalized[i]
                else:
                    break
            self.typed_text = new_text
        else:
            # Process character by character to enforce correctness gating.
            limit = min(incoming_len, len(self.target_text))
            new_text = self.typed_text
            i = len(self.typed_text)
            while i < limit:
                ch = normalized[i]
                expected = self.target_text[i]
                if ch == expected:
                    new_text += ch
                    i += 1
                else:
                    self.mistakes += 1
                    break  # stop progress until corrected
            self.typed_text = new_text

        if self.typed_text and not self.timer.started:
            self.timer.start()

        finished = (
            len(self.typed_text) == len(self.target_text) and bool(self.target_text)
        )
        if finished:
            self.status = GameStatus.COMPLETED
            self.timer.stop()
        elif self.timer.started:
            self.status = GameStatus.RUNNING
        else:
            self.status = GameStatus.READY

        return self._snapshot()

    def tick(self) -> Dict[str, object]:
        if self.status == GameStatus.COMPLETED and not self.timer.finished:
            self.timer.stop()
        return self._snapshot()

    def _initialize_session(self, include_text: bool) -> Dict[str, object]:
        self.typed_text = ""
        self.mistakes = 0
        self.session_recorded = False
        self.timer.reset()
        self.status = GameStatus.NO_TEXT if not self.target_text else GameStatus.READY
        return self._snapshot(include_text=include_text)

    def _snapshot(self, include_text: bool = False) -> Dict[str, object]:
        metrics = self._build_metrics()
        payload: Dict[str, object] = {"metrics": metrics.to_dict()}
        if include_text:
            payload["target_text"] = self.target_text
        payload["typed_text"] = self.typed_text
        payload["bank_progress"] = {
            "position": self.current_index + 1 if self.text_bank else 0,
            "total": len(self.text_bank),
            "has_next": self.current_index < len(self.text_bank) - 1,
        }

        if (
            self.status == GameStatus.COMPLETED
            and not self.session_recorded
            and not self.is_custom
        ):
            self._record_history(metrics)
            self.session_recorded = True

        return payload

    def _build_metrics(self) -> GameMetrics:
        errors = self.mistakes

        elapsed = self.timer.elapsed() if self.timer.started else 0.0
        wpm = (
            MetricsCalculator.words_per_minute(len(self.typed_text), elapsed)
            if self.timer.started
            else 0
        )
        accuracy = MetricsCalculator.accuracy(len(self.typed_text), errors)

        if self.status == GameStatus.COMPLETED and not self.timer.finished:
            self.timer.stop()
            elapsed = self.timer.elapsed()

        return GameMetrics(
            status=self.status,
            target_length=len(self.target_text),
            typed_length=len(self.typed_text),
            errors=errors,
            accuracy=accuracy,
            wpm=wpm,
            elapsed_seconds=elapsed,
            started=self.timer.started,
            finished=self.status == GameStatus.COMPLETED,
        )

    def _record_history(self, metrics: GameMetrics) -> None:
        self.history[self.current_index] = metrics

    def summary(self) -> Dict[str, object]:
        results = []
        for idx in sorted(self.history.keys()):
            m = self.history[idx]
            results.append(
                {
                    "index": idx + 1,
                    "wpm": m.wpm,
                    "accuracy": m.accuracy,
                    "errors": m.errors,
                    "time": m.elapsed_seconds,
                }
            )
        count = len(results) or 1
        avg_wpm = sum(r["wpm"] for r in results) / count if results else 0.0
        avg_acc = sum(r["accuracy"] for r in results) / count if results else 0.0
        avg_err = sum(r["errors"] for r in results) / count if results else 0.0
        avg_time = sum(r["time"] for r in results) / count if results else 0.0
        return {
            "total": len(self.text_bank),
            "completed": len(results),
            "averages": {
                "wpm": avg_wpm,
                "accuracy": avg_acc,
                "errors": avg_err,
            },
            "results": results,
        }

    def _sync_bank(self) -> None:
        # Ensure we have the latest bank and indices are in range.
        self.text_bank = self.text_source.bank()
        if not self.text_bank:
            self.current_index = 0
            self.target_text = ""
            return
        if self.current_index >= len(self.text_bank):
            self.current_index = len(self.text_bank) - 1
        self.target_text = self.text_bank[self.current_index]
