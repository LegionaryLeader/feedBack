"""Tests for the pure song-stats helpers (lib/song_score.py)."""

import pytest

from song_score import accuracy, merge_stats, score


@pytest.mark.parametrize("hits,misses,acc", [
    (0, 0, 0.0),
    (1, 0, 1.0),
    (3, 1, 0.75),
    (0, 5, 0.0),
    (9, 1, 0.9),
])
def test_accuracy(hits, misses, acc):
    assert accuracy(hits, misses) == pytest.approx(acc)


@pytest.mark.parametrize("hits,misses,expected", [
    (0, 0, 0),
    (10, 0, 1000),     # round(10*100*1.0)
    (3, 1, 225),       # round(3*100*0.75)
    (9, 1, 810),       # round(9*100*0.9)
    # .5 boundary: 3*100*(3/8) = 112.5 → JS Math.round → 113 (half away from
    # zero), NOT Python banker's-rounding's 112. Guards against client drift.
    (3, 5, 113),
])
def test_score(hits, misses, expected):
    assert score(hits, misses) == expected


def test_score_monotonic_in_accuracy_for_fixed_hits():
    # More misses (lower accuracy) → lower score, for the same hit count.
    assert score(10, 0) > score(10, 5) > score(10, 20)


def test_merge_into_empty():
    m = merge_stats(None, {"score": 500, "accuracy": 0.8, "last_position": 12.5})
    assert m == {
        "plays": 1, "best_score": 500, "best_accuracy": 0.8,
        "last_score": 500, "last_accuracy": 0.8, "last_position": 12.5,
    }


def test_merge_takes_max_for_best_and_new_for_last():
    existing = {"plays": 2, "best_score": 900, "best_accuracy": 0.95,
                "last_score": 900, "last_accuracy": 0.95, "last_position": 30.0}
    # A worse session: plays increments, best preserved, last replaced.
    m = merge_stats(existing, {"score": 400, "accuracy": 0.6, "last_position": 5.0})
    assert m["plays"] == 3
    assert m["best_score"] == 900 and m["best_accuracy"] == 0.95
    assert m["last_score"] == 400 and m["last_accuracy"] == 0.6
    assert m["last_position"] == 5.0


def test_merge_raises_best_on_better_session():
    existing = {"plays": 1, "best_score": 400, "best_accuracy": 0.6,
                "last_score": 400, "last_accuracy": 0.6, "last_position": 5.0}
    m = merge_stats(existing, {"score": 800, "accuracy": 0.9, "last_position": 40.0})
    assert m["best_score"] == 800 and m["best_accuracy"] == 0.9
    assert m["plays"] == 2


def test_merge_keeps_existing_position_when_session_omits_it():
    existing = {"plays": 1, "best_score": 100, "best_accuracy": 0.5,
                "last_score": 100, "last_accuracy": 0.5, "last_position": 22.0}
    m = merge_stats(existing, {"score": 100, "accuracy": 0.5})  # no last_position
    assert m["last_position"] == 22.0
