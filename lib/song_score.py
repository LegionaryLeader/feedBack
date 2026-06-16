"""Pure helpers for fee[dB]ack v0.3.0 song-stats scoring + upsert logic.

The score/accuracy formulas mirror the frontend recorder (static/v3/
stats-recorder.js) so the value the badge shows and the value the server
stores agree. Kept pure + flat-importable (constitution Principle V); tested
in tests/test_song_score.py.

    accuracy(hits, misses) = hits / max(1, hits + misses)        # 0..1
    score(hits, misses)    = round(hits * 100 * accuracy)        # monotonic in accuracy
"""

from __future__ import annotations

import math

__all__ = ["accuracy", "score", "merge_stats"]


def accuracy(hits: int, misses: int) -> float:
    hits = max(0, int(hits or 0))
    misses = max(0, int(misses or 0))
    return hits / max(1, hits + misses)


def score(hits: int, misses: int) -> int:
    """Deterministic, monotonic-in-accuracy integer score.

    Rounds half-AWAY-from-zero to match the frontend recorder's JS
    Math.round() (e.g. hits=3, misses=5 → 112.5 → 113), not Python's
    banker's rounding which would give 112 and disagree with the client."""
    hits = max(0, int(hits or 0))
    return int(math.floor(hits * 100 * accuracy(hits, misses) + 0.5))


def merge_stats(existing: dict | None, session: dict) -> dict:
    """Upsert/max merge of a scored session into the existing row.

    `plays` increments; `best_*` take the max of old/new; `last_*` take the
    new session; `last_position` falls back to the existing value when the
    session doesn't carry one. Returns the merged field dict (no IO).
    """
    e = existing or {}

    def _i(v, d=0):
        try:
            return int(v)
        except (TypeError, ValueError, OverflowError):
            return d

    def _f(v, d=0.0):
        # Reject NaN/Inf as well as unparseable values: a stored non-finite
        # would later break JSON serialization of /api/stats reads.
        try:
            f = float(v)
            return f if math.isfinite(f) else d
        except (TypeError, ValueError, OverflowError):
            return d

    new_score = _i(session.get("score"))
    new_acc = _f(session.get("accuracy"))
    sess_pos = session.get("last_position")
    last_position = _f(sess_pos) if sess_pos is not None else _f(e.get("last_position"))
    return {
        "plays": _i(e.get("plays")) + 1,
        "best_score": max(_i(e.get("best_score")), new_score),
        "best_accuracy": max(_f(e.get("best_accuracy")), new_acc),
        "last_score": new_score,
        "last_accuracy": new_acc,
        "last_position": last_position,
    }
