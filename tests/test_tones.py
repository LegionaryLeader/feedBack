"""Tests for lib/tones.py — sloppak tone-change payload builder."""

from tones import sloppak_tone_changes


# ── sloppak_tone_changes (highway payload builder) ───────────────────────────

def test_sloppak_tone_changes_sorts_and_returns_base():
    base, changes = sloppak_tone_changes({
        "base": "Clean",
        "changes": [{"t": 12.5, "name": "Drive"}, {"t": 3.0, "name": "Clean"}],
    })
    assert base == "Clean"
    assert changes == [{"t": 3.0, "name": "Clean"}, {"t": 12.5, "name": "Drive"}]


def test_sloppak_tone_changes_skips_malformed_markers():
    _, changes = sloppak_tone_changes({
        "changes": [
            {"t": "nan", "name": "BadStr"},
            {"t": float("inf"), "name": "Inf"},
            {"t": 5.0, "name": 123},          # non-string name
            {"t": None, "name": "NoTime"},
            "not-a-dict",
            {"t": 7.0, "name": "Good"},
        ],
    })
    assert changes == [{"t": 7.0, "name": "Good"}]


def test_sloppak_tone_changes_handles_none_and_bad_base():
    assert sloppak_tone_changes(None) == ("", [])
    base, changes = sloppak_tone_changes({"base": 123, "changes": []})
    assert base == "" and changes == []


def test_sloppak_tone_changes_non_dict_input():
    """A truthy non-dict payload must not crash."""
    assert sloppak_tone_changes(["not", "a", "dict"]) == ("", [])
    assert sloppak_tone_changes("nope") == ("", [])


def test_sloppak_tone_changes_non_list_changes():
    """A truthy non-list `changes` value must not raise on iteration."""
    base, changes = sloppak_tone_changes({"base": "Clean", "changes": 1})
    assert base == "Clean" and changes == []
