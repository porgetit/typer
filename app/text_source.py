"""Centralized text providers for the typing game."""

from pathlib import Path
from typing import Iterable, List, Optional

from .text_bank_loader import load_bank_from_json, normalize_bank

class TextSource:
    def __init__(
        self,
        bank_path: Optional[Path] = None,
        bank: Optional[Iterable[str]] = None,
    ) -> None:
        self.bank_path = bank_path or Path(__file__).parent / "data" / "texts.json"
        self._bank: List[str] = []
        self._load_initial(bank)

    def _load_initial(self, bank: Optional[Iterable[str]]) -> None:
        if bank is not None:
            self._bank = self._prepare_bank(bank)
            return

        file_bank = load_bank_from_json(self.bank_path)
        if file_bank:
            self._bank = self._prepare_bank(file_bank)
            return

        self._bank = []

    def _prepare_bank(self, raw: Iterable[str]) -> List[str]:
        normalized = normalize_bank(raw)
        return sorted(normalized, key=len)

    def reload_bank(self) -> None:
        file_bank = load_bank_from_json(self.bank_path)
        if file_bank:
            self._bank = self._prepare_bank(file_bank)
        elif not self._bank:
            # keep empty if nothing is available
            self._bank = []

    def demo(self) -> str:
        return self._bank[0] if self._bank else ""

    def bank(self) -> List[str]:
        return list(self._bank)

    def by_index(self, index: int) -> str:
        if not self._bank:
            return ""
        index = max(0, min(index, len(self._bank) - 1))
        return self._bank[index]

    def load_from_path(self, path: Path) -> str:
        text = Path(path).read_text(encoding="utf-8")
        return text.replace("\r\n", "\n").strip("\n")
