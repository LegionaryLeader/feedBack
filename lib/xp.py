"""Unified XP / level math for the fee[dB]ack player profile.

This is the single source of truth for the XP curve. It is intentionally the
SAME math the minigames plugin shipped (so promoting XP to a unified core
store does not change anyone's level):

    xp_for_run(score) = floor(sqrt(score) * 10)
    level_for_xp(xp)  = floor(sqrt(xp / 100)) + 1   # L1@0, L2@100, L3@400, L4@900…
    threshold(level)  = (level - 1)^2 * 100          # xp needed to reach `level`

Pure functions, no IO, flat-importable (`from xp import ...`) per constitution
Principle V. Covered by tests/test_xp.py.
"""

from __future__ import annotations

import math

__all__ = [
    "xp_for_run",
    "level_for_xp",
    "level_threshold",
    "xp_in_level",
    "xp_to_next",
    "progress",
]


def xp_for_run(score: int) -> int:
    """XP awarded for a run/play with the given score. ``floor(sqrt(score)*10)``."""
    if score is None or score <= 0:
        return 0
    return int(math.floor(math.sqrt(score) * 10))


def level_for_xp(xp: int) -> int:
    """Level for a total XP. ``floor(sqrt(xp/100)) + 1`` (minimum 1)."""
    if xp is None or xp <= 0:
        return 1
    return int(math.floor(math.sqrt(xp / 100))) + 1


def level_threshold(level: int) -> int:
    """Total XP required to *reach* ``level``. ``(level-1)^2 * 100``."""
    if level <= 1:
        return 0
    return (level - 1) ** 2 * 100


def xp_in_level(xp: int) -> int:
    """XP accumulated within the current level (xp above the current level's floor)."""
    xp = max(0, int(xp or 0))
    return xp - level_threshold(level_for_xp(xp))


def xp_to_next(xp: int) -> int:
    """XP remaining to reach the next level (0 only at exact-threshold edge cases)."""
    xp = max(0, int(xp or 0))
    return max(0, level_threshold(level_for_xp(xp) + 1) - xp)


def progress(xp: int) -> dict:
    """The full badge payload for a total XP: ``{xp, level, xp_in_level, xp_to_next}``."""
    xp = max(0, int(xp or 0))
    return {
        "xp": xp,
        "level": level_for_xp(xp),
        "xp_in_level": xp_in_level(xp),
        "xp_to_next": xp_to_next(xp),
    }
