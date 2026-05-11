from __future__ import annotations

from typing import TypeVar

T = TypeVar("T")


def truncate_string(value: str, max_length: int) -> str:
    cleaned = "".join(ch for ch in value if ch.isprintable() or ch in ("\n", "\t"))
    if len(cleaned) <= max_length:
        return cleaned
    if max_length <= 1:
        return "\u2026"[:max_length]
    return cleaned[: max_length - 1] + "\u2026"


def truncate_array(items: list[T], max_length: int) -> list[T]:
    return items[:max_length]
