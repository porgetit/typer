"""Utility to load typing texts from a JSON file."""

import json
from pathlib import Path
from typing import Iterable, List


def load_bank_from_json(path: Path) -> List[str]:
    if not path.exists():
        return []

    content = path.read_text(encoding="utf-8-sig")
    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        return []

    if isinstance(data, list):
        return [str(item) for item in data if isinstance(item, str) and item.strip()]
    return []


def normalize_bank(texts: Iterable[str]) -> List[str]:
    normalized = []
    for t in texts:
        if not t:
            continue
        normalized.append(str(t).replace("\r\n", "\n").strip("\n"))
    return normalized
