"""Unit tests for lib/notation.py — vocabulary constants and wire helpers."""

from __future__ import annotations

import notation


# ── Constants ─────────────────────────────────────────────────────────────────

def test_clefs_exact_set():
    assert notation.CLEFS == {"G2", "F4", "C3", "C4", "neutral"}


def test_durations_exact_set():
    assert notation.DURATIONS == {1, 2, 4, 8, 16, 32}


def test_schema_version_is_one():
    assert notation.SCHEMA_VERSION == 1


# ── validate_notation — happy path ────────────────────────────────────────────

def test_validate_notation_accepts_minimal_payload():
    ok, reason = notation.validate_notation({"staves": [], "measures": []})
    assert ok, reason


def test_validate_notation_accepts_version_1():
    ok, reason = notation.validate_notation({"version": 1, "staves": [], "measures": []})
    assert ok, reason


def test_validate_notation_accepts_missing_version():
    """Missing version key is treated as SCHEMA_VERSION — not an error."""
    ok, reason = notation.validate_notation({"staves": [], "measures": []})
    assert ok, reason


def test_validate_notation_accepts_unknown_version():
    """An unknown version is logged at DEBUG but the payload is still accepted
    for forward-compat (a newer sloppak on an older client should still load)."""
    ok, reason = notation.validate_notation({"version": 99, "staves": [], "measures": []})
    assert ok, reason


def test_validate_notation_accepts_unknown_top_level_fields():
    """Unknown fields must pass through — additive schema evolution."""
    ok, reason = notation.validate_notation({
        "staves": [],
        "measures": [],
        "future_field": "some value",
        "another_new_key": 42,
    })
    assert ok, reason


def test_validate_notation_accepts_populated_payload():
    """A realistic non-empty payload with staves and measures passes."""
    ok, reason = notation.validate_notation({
        "version": 1,
        "instrument": "piano",
        "staves": [
            {"id": "rh", "clef": "G2", "label": "Right Hand"},
            {"id": "lh", "clef": "F4", "label": "Left Hand"},
        ],
        "measures": [
            {
                "idx": 1,
                "t": 0.0,
                "ts": [4, 4],
                "ks": 0,
                "tempo": 120.0,
                "staves": {
                    "rh": {"voices": [{"v": 1, "beats": [{"t": 0.0, "dur": 4, "notes": [{"midi": 64}]}]}]},
                    "lh": {"voices": [{"v": 1, "beats": [{"t": 0.0, "dur": 1, "rest": True}]}]},
                },
            }
        ],
    })
    assert ok, reason


# ── validate_notation — rejection cases ──────────────────────────────────────

def test_validate_notation_rejects_list():
    ok, _ = notation.validate_notation([])
    assert not ok


def test_validate_notation_rejects_none():
    ok, _ = notation.validate_notation(None)
    assert not ok


def test_validate_notation_rejects_string():
    ok, _ = notation.validate_notation("not a dict")
    assert not ok


def test_validate_notation_rejects_missing_staves():
    ok, reason = notation.validate_notation({"measures": []})
    assert not ok
    assert "staves" in reason


def test_validate_notation_rejects_missing_measures():
    ok, reason = notation.validate_notation({"staves": []})
    assert not ok
    assert "measures" in reason


def test_validate_notation_rejects_non_list_staves():
    ok, reason = notation.validate_notation({"staves": {}, "measures": []})
    assert not ok
    assert "staves" in reason


def test_validate_notation_rejects_non_list_measures():
    ok, reason = notation.validate_notation({"staves": [], "measures": {}})
    assert not ok
    assert "measures" in reason


def test_validate_notation_rejects_string_version():
    ok, _ = notation.validate_notation({"version": "1", "staves": [], "measures": []})
    assert not ok


def test_validate_notation_rejects_float_version():
    ok, _ = notation.validate_notation({"version": 1.0, "staves": [], "measures": []})
    assert not ok


def test_validate_notation_rejects_bool_version_true():
    """bool is a subclass of int in Python — must be explicitly rejected."""
    ok, _ = notation.validate_notation({"version": True, "staves": [], "measures": []})
    assert not ok


def test_validate_notation_rejects_bool_version_false():
    ok, _ = notation.validate_notation({"version": False, "staves": [], "measures": []})
    assert not ok


# ── measure_to_wire ───────────────────────────────────────────────────────────

def _make_measure(beat_t: float) -> dict:
    """Build a minimal measure with one beat at the given time."""
    return {
        "idx": 1,
        "t": 0.0,
        "staves": {
            "rh": {
                "voices": [
                    {"v": 1, "beats": [{"t": beat_t, "dur": 4, "notes": [{"midi": 64}]}]}
                ]
            }
        },
    }


def test_measure_to_wire_rounds_beat_times():
    measure = _make_measure(0.5001)
    out = notation.measure_to_wire(measure)
    beat_t = out["staves"]["rh"]["voices"][0]["beats"][0]["t"]
    assert beat_t == 0.5


def test_measure_to_wire_rounds_to_3dp():
    measure = _make_measure(0.123456789)
    out = notation.measure_to_wire(measure)
    beat_t = out["staves"]["rh"]["voices"][0]["beats"][0]["t"]
    assert beat_t == 0.123


def test_measure_to_wire_returns_copy():
    """Mutating the returned dict must not affect the original."""
    measure = _make_measure(0.5)
    out = notation.measure_to_wire(measure)
    out["idx"] = 999
    assert measure["idx"] == 1  # original unchanged


def test_measure_to_wire_does_not_mutate_nested_beats():
    """Mutating beats in the returned dict must not affect the original."""
    measure = _make_measure(0.5001)
    out = notation.measure_to_wire(measure)
    out["staves"]["rh"]["voices"][0]["beats"][0]["t"] = 99.0
    # original beat time must be unmodified
    orig_t = measure["staves"]["rh"]["voices"][0]["beats"][0]["t"]
    assert orig_t == 0.5001


def test_measure_to_wire_malformed_returns_empty_dict():
    assert notation.measure_to_wire("not a dict") == {}
    assert notation.measure_to_wire(None) == {}
    assert notation.measure_to_wire([]) == {}
    assert notation.measure_to_wire(42) == {}


def test_measure_to_wire_guards_nan_t_and_tempo():
    """NaN/Infinity in measure-level t or tempo must be replaced with 0.0.

    Starlette serialises non-finite floats as the bare token ``NaN`` which is
    not valid JSON, so browser JSON.parse fails on the notation_measures frame.
    """
    import math
    measure = {"idx": 1, "t": float("nan"), "tempo": float("inf"), "staves": {}}
    out = notation.measure_to_wire(measure)
    assert out["t"] == 0.0
    assert out["tempo"] == 0.0
    assert math.isfinite(out["t"])
    assert math.isfinite(out["tempo"])


def test_measure_to_wire_passes_through_non_staves_fields():
    """Top-level fields other than staves are preserved as-is."""
    measure = {"idx": 3, "t": 4.0, "ts": [3, 4], "ks": 2, "tempo": 96.0, "staves": {}}
    out = notation.measure_to_wire(measure)
    assert out["idx"] == 3
    assert out["ts"] == [3, 4]
    assert out["ks"] == 2
    assert out["tempo"] == 96.0


def test_measure_to_wire_clamps_nan_t_to_zero():
    """NaN in measure-level 't' must be replaced with 0.0 (invalid JSON token)."""
    import math
    measure = {"idx": 1, "t": float("nan"), "staves": {}}
    out = notation.measure_to_wire(measure)
    assert out["t"] == 0.0
    assert math.isfinite(out["t"])


def test_measure_to_wire_clamps_inf_tempo_to_zero():
    """Infinity in measure-level 'tempo' must be replaced with 0.0."""
    import math
    measure = {"idx": 1, "t": 0.0, "tempo": float("inf"), "staves": {}}
    out = notation.measure_to_wire(measure)
    assert out["tempo"] == 0.0
    assert math.isfinite(out["tempo"])


def test_measure_to_wire_handles_measure_without_staves():
    """A measure dict with no staves key is returned as-is (no crash)."""
    measure = {"idx": 1, "t": 0.0}
    out = notation.measure_to_wire(measure)
    assert out["idx"] == 1


def test_measure_to_wire_handles_non_dict_staves_value():
    """A staff entry whose value is not a dict passes through without error."""
    measure = {"idx": 1, "t": 0.0, "staves": {"rh": "bad"}}
    out = notation.measure_to_wire(measure)
    assert out["staves"]["rh"] == "bad"


# ── measures_to_wire ──────────────────────────────────────────────────────────

def test_measures_to_wire_processes_two_measures():
    measures = [_make_measure(0.0), _make_measure(2.0)]
    out = notation.measures_to_wire(measures)
    assert len(out) == 2


def test_measures_to_wire_drops_malformed():
    measures = [_make_measure(0.0), "bad", None, 42, _make_measure(2.0)]
    out = notation.measures_to_wire(measures)
    assert len(out) == 2


def test_measures_to_wire_preserves_order():
    """Output order must match input order — no sorting by time."""
    m1 = {"idx": 2, "t": 2.0, "staves": {}}
    m2 = {"idx": 1, "t": 0.0, "staves": {}}
    out = notation.measures_to_wire([m1, m2])
    assert out[0]["idx"] == 2
    assert out[1]["idx"] == 1


def test_measures_to_wire_empty_input():
    assert notation.measures_to_wire([]) == []


def test_measures_to_wire_all_malformed():
    assert notation.measures_to_wire(["a", None, 1]) == []


# ── beat_pos and beat_groups pass-through ─────────────────────────────────────

def test_measure_to_wire_passes_through_beat_pos():
    """beat_pos round-trips through measure_to_wire unchanged."""
    measure = {
        "idx": 1,
        "t": 0.0,
        "staves": {
            "rh": {
                "voices": [
                    {"v": 1, "beats": [{"t": 0.0, "dur": 8, "beat_pos": [3, 8], "notes": [{"midi": 64}]}]}
                ]
            }
        },
    }
    out = notation.measure_to_wire(measure)
    beat_pos = out["staves"]["rh"]["voices"][0]["beats"][0]["beat_pos"]
    assert beat_pos == [3, 8]


def test_measure_to_wire_beat_pos_not_rounded():
    """beat_pos is not rounded or modified; only t is rounded."""
    measure = {
        "idx": 1,
        "t": 0.0,
        "staves": {
            "rh": {
                "voices": [
                    {"v": 1, "beats": [{"t": 0.5001, "dur": 4, "beat_pos": [1, 4], "notes": [{"midi": 60}]}]}
                ]
            }
        },
    }
    out = notation.measure_to_wire(measure)
    beat = out["staves"]["rh"]["voices"][0]["beats"][0]
    assert beat["beat_pos"] == [1, 4]
    assert beat["t"] == 0.5


def test_measure_to_wire_passes_through_beat_groups():
    """beat_groups round-trips through measure_to_wire unchanged."""
    measure = {"idx": 1, "t": 0.0, "beat_groups": [3, 3], "staves": {}}
    out = notation.measure_to_wire(measure)
    assert out["beat_groups"] == [3, 3]


def test_measures_to_wire_passes_through_beat_groups():
    """beat_groups is preserved through measures_to_wire for each measure."""
    m1 = {"idx": 1, "t": 0.0, "beat_groups": [3, 3], "staves": {}}
    m2 = {"idx": 2, "t": 2.0, "beat_groups": [2, 3], "staves": {}}
    out = notation.measures_to_wire([m1, m2])
    assert out[0]["beat_groups"] == [3, 3]
    assert out[1]["beat_groups"] == [2, 3]


# ── Schema-completeness batch (epic #828 / #822 spec freeze) ─────────────────


def test_grace_types_exact_set():
    assert notation.GRACE_TYPES == {"a", "p"}


def test_stem_directions_exact_set():
    assert notation.STEM_DIRECTIONS == {"up", "down"}


def test_dynamics_exact_set():
    assert notation.DYNAMICS == {"ppp", "pp", "p", "mp", "mf", "f", "ff", "fff"}


def test_validate_accepts_credit_fields():
    """rights / lyricist / arranger are optional top-level passthrough fields."""
    ok, reason = notation.validate_notation({
        "version": 1,
        "rights": "© 2026 Tester",
        "lyricist": "L. Writer",
        "arranger": "A. Ranger",
        "staves": [],
        "measures": [],
    })
    assert ok, reason


def test_measure_to_wire_passes_through_pickup():
    out = notation.measure_to_wire({"idx": 1, "t": 0.0, "pickup": True, "staves": {}})
    assert out["pickup"] is True


def test_measure_to_wire_passes_through_new_beat_and_note_fields():
    """Typed grace, arp, ferm, pedal trio, and forced stem survive the wire."""
    measure = {
        "idx": 1,
        "t": 0.0,
        "staves": {
            "rh": {
                "voices": [
                    {
                        "v": 1,
                        "beats": [
                            {
                                "t": 0.0,
                                "dur": 8,
                                "grace": "a",
                                "arp": True,
                                "ferm": True,
                                "spd": True,
                                "notes": [{"midi": 64, "stem": "down"}],
                            },
                            {"t": 0.5, "dur": 4, "sph": True, "notes": [{"midi": 64}]},
                            {"t": 1.0, "dur": 4, "spu": True, "rest": True},
                        ],
                    }
                ]
            }
        },
    }
    out = notation.measure_to_wire(measure)
    beats = out["staves"]["rh"]["voices"][0]["beats"]
    assert beats[0]["grace"] == "a"
    assert beats[0]["arp"] is True
    assert beats[0]["ferm"] is True
    assert beats[0]["spd"] is True
    assert beats[0]["notes"][0]["stem"] == "down"
    assert beats[1]["sph"] is True
    assert beats[2]["spu"] is True
