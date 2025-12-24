"""Utility to load typing texts from a JSON file."""

import json
from pathlib import Path
from typing import Iterable, List, Union


def load_bank_from_json(path: Path) -> List[str]:
    if not path.exists():
        return []

    content = path.read_text(encoding="utf-8-sig")
    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        return []

    if isinstance(data, list):
        cleaned: List[Union[str, List[str]]] = []
        for item in data:
            if isinstance(item, str) and item.strip():
                cleaned.append(item)
            elif isinstance(item, list) and any(isinstance(x, str) and x.strip() for x in item):
                cleaned.append([x for x in item if isinstance(x, str) and x.strip()])
        return cleaned
    return []


def normalize_bank(texts: Iterable[str]) -> List[str]:
    normalized = []
    for t in texts:
        if not t:
            continue
        normalized.append(_normalize_entry(t))
    return normalized


def _normalize_entry(entry: Union[str, List[str]]) -> str:
    """Normalize a single bank entry to a single string with LF newlines."""
    if isinstance(entry, list):
        parts = [_normalize_entry(e) for e in entry if isinstance(e, str) and e.strip()]
        text = "\n".join(parts)
    else:
        text = str(entry)

    # Normalize all line endings to LF to support multiparagraph texts.
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    # Trim trailing whitespace on each line but keep structure.
    lines = [line.rstrip(" \t") for line in text.split("\n")]
    # Remove leading/trailing empty lines introduced by formatting.
    while lines and lines[0] == "":
        lines.pop(0)
    while lines and lines[-1] == "":
        lines.pop()
    return "\n".join(lines)
