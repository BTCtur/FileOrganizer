from __future__ import annotations

from datetime import datetime
from pathlib import Path


def safe_rename(target_path: Path) -> Path:
    """Return a non-conflicting path like `name (1).ext` if needed."""
    if not target_path.exists():
        return target_path

    stem = target_path.stem
    suffix = target_path.suffix
    parent = target_path.parent

    index = 1
    while True:
        candidate = parent / f"{stem} ({index}){suffix}"
        if not candidate.exists():
            return candidate
        index += 1


def format_date(value: datetime, format_style: str) -> str:
    if format_style == "YYYY-MM-DD":
        return value.strftime("%Y-%m-%d")
    if format_style == "YYYY/MM/DD":
        return value.strftime("%Y/%m/%d")
    msg = f"Unsupported folder format: {format_style}"
    raise ValueError(msg)


def is_subdirectory(parent: Path, child: Path) -> bool:
    """Return True if child is parent itself or nested under parent."""
    parent_resolved = parent.resolve()
    child_resolved = child.resolve()
    return child_resolved == parent_resolved or parent_resolved in child_resolved.parents
