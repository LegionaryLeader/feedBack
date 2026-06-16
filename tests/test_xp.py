"""Tests for the unified XP/level math (lib/xp.py).

Values are pinned to the curve the minigames plugin shipped so the unified
core store cannot silently change anyone's level.
"""

import math

import pytest

from xp import (
    level_for_xp,
    level_threshold,
    progress,
    xp_for_run,
    xp_in_level,
    xp_to_next,
)


@pytest.mark.parametrize("score,expected", [
    (0, 0),
    (-5, 0),
    (1, 10),       # floor(sqrt(1)*10)
    (100, 100),    # floor(sqrt(100)*10) = 100
    (250, 158),    # floor(sqrt(250)*10) = floor(158.11) = 158
])
def test_xp_for_run(score, expected):
    assert xp_for_run(score) == expected


def test_xp_for_run_matches_formula():
    for s in (0, 1, 7, 42, 999, 10000):
        assert xp_for_run(s) == (0 if s <= 0 else int(math.floor(math.sqrt(s) * 10)))


@pytest.mark.parametrize("xp,level", [
    (0, 1),
    (-10, 1),
    (99, 1),
    (100, 2),      # threshold L2 = 100
    (399, 2),
    (400, 3),      # threshold L3 = 400
    (900, 4),      # threshold L4 = 900
    (1600, 5),
])
def test_level_for_xp(xp, level):
    assert level_for_xp(xp) == level


def test_level_threshold():
    assert level_threshold(1) == 0
    assert level_threshold(2) == 100
    assert level_threshold(3) == 400
    assert level_threshold(4) == 900


def test_thresholds_are_self_consistent():
    # Reaching a threshold should put you exactly at that level.
    for lvl in range(1, 12):
        assert level_for_xp(level_threshold(lvl)) == lvl


def test_xp_in_level_and_to_next_partition_the_level():
    # in_level + to_next must equal the width of the current level band.
    for xp in (0, 50, 100, 250, 401, 1234, 5000):
        lvl = level_for_xp(xp)
        band = level_threshold(lvl + 1) - level_threshold(lvl)
        assert xp_in_level(xp) + xp_to_next(xp) == band
        assert xp_in_level(xp) >= 0
        assert xp_to_next(xp) >= 0


def test_progress_payload():
    p = progress(450)
    assert p == {
        "xp": 450,
        "level": 3,                 # 400 <= 450 < 900
        "xp_in_level": 50,          # 450 - 400
        "xp_to_next": 450,          # 900 - 450
    }


def test_progress_clamps_negative():
    assert progress(-100) == {"xp": 0, "level": 1, "xp_in_level": 0, "xp_to_next": 100}
