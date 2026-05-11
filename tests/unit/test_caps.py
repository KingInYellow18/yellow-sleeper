from __future__ import annotations

from yellow_sleeper.obs.caps import truncate_array, truncate_string


def test_truncate_string_strips_control_chars_and_limits_length() -> None:
    assert truncate_string("abc\x00def", 5) == "abcd\u2026"


def test_truncate_array_limits_items() -> None:
    assert truncate_array([1, 2, 3], 2) == [1, 2]
