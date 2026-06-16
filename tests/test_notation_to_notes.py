"""Tests for lib/notation.notation_to_notes — the notation → flat-notes inverse.

Covers onset-gap sustain (tuplet/tempo-robust), tempo carry, tie folding, grace
and rest handling, plus a round-trip through notation_lift.build_notation.
"""

from __future__ import annotations

import pytest

import notation
import notation_lift


def _beat(t, midi, dur=4, dot=0, tied=False, rest=False, grace=None):
    b = {"t": t, "dur": dur}
    if dot:
        b["dot"] = dot
    if grace:
        b["grace"] = grace
    if rest:
        b["rest"] = True
    else:
        b["notes"] = [{"midi": midi, **({"tied": True} if tied else {})}]
    return b


def _nt(measures):
    return {"version": 1, "instrument": "piano",
            "staves": [{"id": "rh", "clef": "G2"}, {"id": "lh", "clef": "F4"}],
            "measures": measures}


def test_returns_empty_for_non_dict_or_empty():
    assert notation.notation_to_notes(None) == []
    assert notation.notation_to_notes({}) == []
    assert notation.notation_to_notes({"measures": []}) == []


def test_flat_notes_sorted_with_absolute_midi():
    nt = _nt([{
        "idx": 1, "t": 0.0, "tempo": 120.0,
        "staves": {
            "rh": {"voices": [{"v": 1, "beats": [_beat(0.5, 64), _beat(0.0, 67)]}]},
            "lh": {"voices": [{"v": 1, "beats": [_beat(0.0, 48)]}]},
        },
    }])
    notes = notation.notation_to_notes(nt)
    assert [(n["t"], n["midi"]) for n in notes] == [(0.0, 48), (0.0, 67), (0.5, 64)]
    # Sustain is the written quarter (0.5 s at 120 BPM).
    assert notes[1]["sus"] == pytest.approx(0.5)


def test_short_note_before_gap_keeps_written_length():
    # note@0.0 (32nd, sus 0.1) then next onset far away at 2.0 with no rest beat
    # (lifter-style) must keep its written 32nd length, not stretch to the gap.
    nt = _nt([{
        "idx": 1, "t": 0.0, "tempo": 120.0,
        "staves": {"rh": {"voices": [{"v": 1, "beats": [
            _beat(0.0, 60, dur=32), _beat(2.0, 62),
        ]}]}},
    }])
    by = {n["midi"]: n for n in notation.notation_to_notes(nt)}
    assert by[60]["sus"] == pytest.approx(0.0625)  # 32nd at 120 BPM


def test_tie_folds_into_sustain():
    nt = _nt([{
        "idx": 1, "t": 0.0, "tempo": 120.0,
        "staves": {"rh": {"voices": [{"v": 1, "beats": [
            _beat(0.0, 60), _beat(0.5, 60, tied=True), _beat(1.0, 60, tied=True),
        ]}]}},
    }])
    notes = notation.notation_to_notes(nt)
    assert len(notes) == 1
    assert notes[0]["sus"] == pytest.approx(1.5)


def test_grace_and_rest_skipped():
    nt = _nt([{
        "idx": 1, "t": 0.0, "tempo": 120.0,
        "staves": {"rh": {"voices": [{"v": 1, "beats": [
            _beat(0.0, 62, grace="a"), _beat(0.0, 60), _beat(0.5, 0, rest=True),
        ]}]}},
    }])
    notes = notation.notation_to_notes(nt)
    assert [n["midi"] for n in notes] == [60]


def test_tuplet_sustain_uses_tu_ratio():
    # An eighth triplet carrying `tu: [3, 2]` sounds ⅔ of a straight eighth.
    nt = _nt([{
        "idx": 1, "t": 0.0, "tempo": 120.0,
        "staves": {"rh": {"voices": [{"v": 1, "beats": [
            {"t": 0.0, "dur": 8, "tu": [3, 2], "notes": [{"midi": 60}]},
        ]}]}},
    }])
    by = {n["midi"]: n["sus"] for n in notation.notation_to_notes(nt)}
    assert by[60] == pytest.approx(0.25 * 2 / 3, abs=1e-3)  # eighth 0.25 × 2/3


def test_terminal_tuplet_fallback_honors_ratio():
    # A lone triplet eighth (dur=8, tu=[3,2]) at 120 BPM with no later onset
    # must fall back to ~0.1667 s (⅔ of a straight eighth), not 0.25 s.
    nt = _nt([{
        "idx": 1, "t": 0.0, "tempo": 120.0,
        "staves": {"rh": {"voices": [{"v": 1, "beats": [
            {"t": 0.0, "dur": 8, "tu": [3, 2], "notes": [{"midi": 60}]},
        ]}]}},
    }])
    notes = notation.notation_to_notes(nt)
    assert notes[0]["sus"] == pytest.approx(0.5 / 3, abs=1e-3)


def test_malformed_measure_staves_skipped():
    # A truthy non-dict `staves` (the validator only checks the top-level shape)
    # must be skipped, not crash the flattener.
    nt = _nt([
        {"idx": 1, "t": 0.0, "tempo": 120.0, "staves": "oops"},
        {"idx": 2, "t": 2.0, "staves": {
            "rh": {"voices": [{"v": 1, "beats": [_beat(2.0, 60)]}]}}},
    ])
    notes = notation.notation_to_notes(nt)
    assert [n["midi"] for n in notes] == [60]


def test_grace_beat_does_not_truncate_previous_sustain():
    # note@0.0, grace@0.45, next note@0.5 — the 0.0 note must sustain to 0.5
    # (the next sounded onset), not to the grace at 0.45.
    nt = _nt([{
        "idx": 1, "t": 0.0, "tempo": 120.0,
        "staves": {"rh": {"voices": [{"v": 1, "beats": [
            _beat(0.0, 60), _beat(0.45, 62, grace="a"), _beat(0.5, 64),
        ]}]}},
    }])
    by = {n["midi"]: n for n in notation.notation_to_notes(nt)}
    assert 62 not in by  # grace excluded from output
    assert by[60]["sus"] == pytest.approx(0.5)


def test_malformed_voices_and_notes_skipped():
    # Truthy-but-non-list `voices` / beat `notes` (only the top-level shape is
    # validated) must be skipped, not crash the flattener.
    nt = _nt([
        {"idx": 1, "t": 0.0, "tempo": 120.0, "staves": {"rh": {"voices": 1}}},
        {"idx": 2, "t": 2.0, "staves": {"rh": {"voices": [
            {"v": 1, "beats": [{"t": 2.0, "dur": 4, "notes": 1}, _beat(2.5, 60)]}]}}},
    ])
    notes = notation.notation_to_notes(nt)
    assert [n["midi"] for n in notes] == [60]


def test_out_of_order_beats_still_correct():
    # Beats listed out of chronological order must still yield correct onset-gap
    # sustains (the voice timeline is sorted before deriving durations).
    nt = _nt([{
        "idx": 1, "t": 0.0, "tempo": 120.0,
        "staves": {"rh": {"voices": [{"v": 1, "beats": [
            _beat(0.5, 64), _beat(0.0, 60),  # reversed
        ]}]}},
    }])
    notes = notation.notation_to_notes(nt)
    by = {n["midi"]: n for n in notes}
    assert by[60]["t"] == 0.0 and by[60]["sus"] == pytest.approx(0.5)  # gap to 64


def test_round_trips_build_notation():
    # wire notes → notation (lifter) → flat notes; pitches + onsets survive.
    wire = [{"t": 0.0, "midi": 60, "sus": 0.5}, {"t": 0.0, "midi": 48, "sus": 0.5},
            {"t": 0.5, "midi": 64, "sus": 0.5}, {"t": 1.0, "midi": 55, "sus": 0.5}]
    beats = [{"time": round(i * 2.0, 3), "measure": i} for i in range(3)]
    payload = notation_lift.build_notation(wire, beats, ts=(4, 4))
    notes = notation.notation_to_notes(payload)
    assert {(round(n["t"], 3), n["midi"]) for n in notes} == {
        (0.0, 60), (0.0, 48), (0.5, 64), (1.0, 55)}
