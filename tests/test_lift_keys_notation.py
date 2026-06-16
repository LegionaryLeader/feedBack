"""Tests for scripts/lift_keys_notation.py — the legacy keys → notation lifter.

Builds directory-form sloppak fixtures with guitar-wire keys notes
(``midi = s*24 + f``, the style of tests/test_sloppak_notation_load.py's
fixture builder) and asserts the lifted ``notation_<id>.json`` contents:
hand split, durations, tempo derivation, idempotency, and dry-run no-op.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from scripts.lift_keys_notation import (
    _load_song_beats,
    build_notation,
    decode_wire_notes,
    downbeat_times,
    lift_sloppak,
    main,
    measure_tempos,
    notation_mod,
    quantize_duration,
    split_hands,
)


# ── Fixture builder ──────────────────────────────────────────────────────────

def _wire_note(t: float, midi: int, sus: float = 0.0) -> dict:
    """Guitar-wire keys note: midi packed as s*24 + f."""
    return {"t": t, "s": midi // 24, "f": midi % 24, "sus": sus}


def _write_keys_sloppak(
    root: Path,
    *,
    notes: list[dict],
    beats: list[dict],
    arr_id: str = "keys",
    arr_name: str = "Keys",
    chords: list[dict] | None = None,
    extra_arrangements: list[dict] | None = None,
    extra_manifest: dict | None = None,
    notation_key: str | None = None,
) -> Path:
    pak = root / "song.sloppak"
    pak.mkdir()
    arr_dir = pak / "arrangements"
    arr_dir.mkdir()

    entry: dict = {"id": arr_id, "name": arr_name,
                   "file": f"arrangements/{arr_id}.json"}
    if notation_key is not None:
        entry["notation"] = notation_key
    arrangements = [entry] + (extra_arrangements or [])

    arr_content = {
        "name": arr_name,
        "notes": notes,
        "chords": chords or [],
        "anchors": [], "handshapes": [], "templates": [],
        "beats": beats,
        "sections": [],
    }
    (arr_dir / f"{arr_id}.json").write_text(json.dumps(arr_content))

    manifest: dict = {
        "title": "Test", "artist": "Tester", "duration": 10.0,
        "arrangements": arrangements,
        "stems": [{"id": "full", "file": "stems/full.ogg"}],
    }
    if extra_manifest:
        manifest.update(extra_manifest)
    (pak / "manifest.yaml").write_text(yaml.safe_dump(manifest, sort_keys=False))
    return pak


def _beats_4_4(n_measures: int, spb: float = 0.5) -> list[dict]:
    """4/4 beats at `spb` seconds per beat (0.5 = 120 BPM)."""
    out = []
    for m in range(n_measures):
        for b in range(4):
            out.append({"time": round((m * 4 + b) * spb, 3),
                        "measure": m + 1 if b == 0 else -1})
    return out


# ── Pure helpers ─────────────────────────────────────────────────────────────

def test_decode_wire_notes_includes_chord_notes_and_l_alias():
    arr = {
        "notes": [{"t": 0.0, "s": 2, "f": 12, "sus": 0.4}],   # midi 60
        "chords": [{"t": 1.0, "id": 0, "notes": [
            {"s": 1, "f": 12, "l": 0.25},                      # midi 36, l alias
            {"s": 2, "f": 16},                                 # midi 64
        ]}],
    }
    notes = decode_wire_notes(arr)
    assert [(n["t"], n["midi"], n["sus"]) for n in notes] == [
        (0.0, 60, 0.4), (1.0, 36, 0.25), (1.0, 64, 0.0),
    ]


def test_decode_wire_notes_skips_malformed():
    arr = {"notes": [{"t": "x", "s": 1, "f": 2}, {"t": 0.0, "s": 9, "f": 23}]}
    # 9*24+23 = 239 > 127 → dropped; malformed t → dropped.
    assert decode_wire_notes(arr) == []


def test_downbeat_times_measure_ge_zero():
    beats = [
        {"time": 0.0, "measure": 1}, {"time": 0.5, "measure": -1},
        {"time": 1.0, "measure": 0},   # measure >= 0 counts as a downbeat
        {"time": 2.0, "measure": 2},
    ]
    assert downbeat_times(beats) == [0.0, 1.0, 2.0]


def test_measure_tempos_from_downbeat_spacing():
    # 4/4, downbeats 2 s apart → 120 BPM; last measure inherits.
    assert measure_tempos([0.0, 2.0, 4.0], (4, 4)) == [120.0, 120.0, 120.0]
    # 6/8 measure of 1.5 s → 3 quarter notes / 1.5 s → 120 BPM.
    assert measure_tempos([0.0, 1.5], (6, 8)) == [120.0, 120.0]


@pytest.mark.parametrize("secs, bpm, expected", [
    (0.5, 120.0, (4, 0)),       # exact quarter
    (0.75, 120.0, (4, 1)),      # dotted quarter
    (0.25, 120.0, (8, 0)),      # eighth
    (1.0, 120.0, (2, 0)),       # half
    (0.005, 120.0, (32, 0)),    # below the 32nd floor
    (10.0, 120.0, (1, 1)),      # clamps to the largest candidate (dotted whole)
])
def test_quantize_duration(secs, bpm, expected):
    assert quantize_duration(secs, bpm) == expected


def test_split_hands_wide_group_splits_at_largest_gap():
    # C2+E2 cluster vs C5 melody — span 36 > 12, largest gap E2→C5.
    notes = [
        {"t": 0.0, "midi": 36, "sus": 0.0},
        {"t": 0.0, "midi": 40, "sus": 0.0},
        {"t": 0.0, "midi": 72, "sus": 0.0},
    ]
    hands = split_hands(notes)
    assert sorted(n["midi"] for n in hands["lh"]) == [36, 40]
    assert [n["midi"] for n in hands["rh"]] == [72]


def test_split_hands_narrow_group_by_mean_pitch():
    high = [{"t": 0.0, "midi": 64, "sus": 0.0}, {"t": 0.0, "midi": 67, "sus": 0.0}]
    low = [{"t": 1.0, "midi": 45, "sus": 0.0}, {"t": 1.0, "midi": 50, "sus": 0.0}]
    hands = split_hands(high + low)
    assert sorted(n["midi"] for n in hands["rh"]) == [64, 67]
    assert sorted(n["midi"] for n in hands["lh"]) == [45, 50]


def test_split_hands_simultaneity_window():
    # 8 ms apart → same group; 20 ms apart → separate groups.
    same = split_hands([
        {"t": 0.0, "midi": 40, "sus": 0.0},
        {"t": 0.008, "midi": 72, "sus": 0.0},
    ])
    assert "lh" in same and "rh" in same  # split as one wide group
    apart = split_hands([
        {"t": 0.0, "midi": 40, "sus": 0.0},
        {"t": 0.020, "midi": 72, "sus": 0.0},
    ])
    # Two separate groups, each assigned by mean pitch.
    assert [n["midi"] for n in apart["lh"]] == [40]
    assert [n["midi"] for n in apart["rh"]] == [72]


# ── build_notation ───────────────────────────────────────────────────────────

def test_build_notation_measures_tempo_and_durations():
    # 120 BPM 4/4: sustained half note (1.0 s) then sus=0 quarter gap pair.
    notes = decode_wire_notes({"notes": [
        _wire_note(0.0, 72, sus=1.0),
        _wire_note(2.0, 74),
        _wire_note(2.5, 76),
    ]})
    payload = build_notation(notes, _beats_4_4(2))
    assert payload["version"] == 1
    assert payload["instrument"] == "piano"
    assert [s["id"] for s in payload["staves"]] == ["rh"]  # single-staff output

    m1, m2 = payload["measures"]
    assert m1["idx"] == 1 and m1["t"] == 0.0 and m1["ts"] == [4, 4]
    assert m1["tempo"] == 120.0
    assert "tempo" not in m2  # unchanged within 1 BPM

    rh1 = m1["staves"]["rh"]["voices"][0]["beats"]
    assert rh1 == [{"t": 0.0, "dur": 2, "notes": [{"midi": 72}]}]   # 1.0s → half
    # Measure 2 (downbeat 2.0): gap 0.5s to next onset → quarter, then the
    # last note (no sustain, no next onset) → quarter fallback at local tempo.
    rh2 = m2["staves"]["rh"]["voices"][0]["beats"]
    assert rh2 == [
        {"t": 2.0, "dur": 4, "notes": [{"midi": 74}]},
        {"t": 2.5, "dur": 4, "notes": [{"midi": 76}]},
    ]


def test_build_notation_tempo_emitted_on_real_change():
    # Measure 1 at 120 BPM (2.0 s), measure 2 at 60 BPM (4.0 s), measure 3 inherits.
    beats = [
        {"time": 0.0, "measure": 1},
        {"time": 2.0, "measure": 2},
        {"time": 6.0, "measure": 3},
    ]
    notes = [{"t": 0.0, "midi": 72, "sus": 0.5},
             {"t": 2.0, "midi": 74, "sus": 0.5},
             {"t": 6.0, "midi": 76, "sus": 0.5}]
    payload = build_notation(notes, beats)
    m1, m2, m3 = payload["measures"]
    assert m1["tempo"] == 120.0
    assert m2["tempo"] == 60.0
    assert "tempo" not in m3  # inherited, no >1 BPM change


def test_build_notation_two_hands_and_chord_grouping():
    # Wide simultaneous group → lh cluster + rh melody as separate staves,
    # each one beat with (deduplicated, sorted) chord notes.
    notes = [
        {"t": 0.0, "midi": 36, "sus": 0.5},
        {"t": 0.0, "midi": 40, "sus": 0.5},
        {"t": 0.0, "midi": 72, "sus": 0.5},
        {"t": 0.0, "midi": 72, "sus": 0.5},  # duplicate pitch collapses
    ]
    payload = build_notation(notes, _beats_4_4(1))
    assert [s["id"] for s in payload["staves"]] == ["rh", "lh"]
    m = payload["measures"][0]
    assert m["staves"]["lh"]["voices"][0]["beats"][0]["notes"] == [
        {"midi": 36}, {"midi": 40}]
    assert m["staves"]["rh"]["voices"][0]["beats"][0]["notes"] == [{"midi": 72}]


def test_build_notation_returns_none_without_notes_or_downbeats():
    assert build_notation([], _beats_4_4(1)) is None
    assert build_notation([{"t": 0.0, "midi": 60, "sus": 0.0}], []) is None


# ── lift_sloppak end-to-end ──────────────────────────────────────────────────

def test_lift_writes_notation_and_manifest_key(tmp_path: Path):
    pak = _write_keys_sloppak(
        tmp_path,
        notes=[_wire_note(0.0, 36, sus=0.5), _wire_note(0.0, 40, sus=0.5),
               _wire_note(0.0, 72, sus=0.5), _wire_note(1.0, 74, sus=0.5)],
        beats=_beats_4_4(2),
    )
    changes = lift_sloppak(pak)
    assert len(changes) == 1

    nt = pak / "notation_keys.json"
    assert nt.exists()
    payload = json.loads(nt.read_text())
    ok, reason = notation_mod.validate_notation(payload)
    assert ok, reason
    assert [s["id"] for s in payload["staves"]] == ["rh", "lh"]
    assert len(payload["measures"]) == 2

    manifest = yaml.safe_load((pak / "manifest.yaml").read_text())
    entry = manifest["arrangements"][0]
    assert entry["notation"] == "notation_keys.json"
    # Key order preserved by the sort_keys=False round-trip.
    assert list(manifest.keys()) == ["title", "artist", "duration",
                                     "arrangements", "stems"]


def test_lift_is_idempotent(tmp_path: Path):
    pak = _write_keys_sloppak(
        tmp_path,
        notes=[_wire_note(0.0, 72, sus=0.5)],
        beats=_beats_4_4(1),
    )
    assert len(lift_sloppak(pak)) == 1
    first_payload = (pak / "notation_keys.json").read_text()
    first_manifest = (pak / "manifest.yaml").read_text()

    # Second run: the manifest now carries the notation key → no-op.
    assert lift_sloppak(pak) == []
    assert (pak / "notation_keys.json").read_text() == first_payload
    assert (pak / "manifest.yaml").read_text() == first_manifest


def test_lift_dry_run_writes_nothing(tmp_path: Path):
    pak = _write_keys_sloppak(
        tmp_path,
        notes=[_wire_note(0.0, 72, sus=0.5)],
        beats=_beats_4_4(1),
    )
    before = (pak / "manifest.yaml").read_text()
    changes = lift_sloppak(pak, dry_run=True)
    assert len(changes) == 1
    assert not (pak / "notation_keys.json").exists()
    assert (pak / "manifest.yaml").read_text() == before


def test_lift_skips_non_keys_arrangements(tmp_path: Path):
    pak = _write_keys_sloppak(
        tmp_path,
        notes=[_wire_note(0.0, 72, sus=0.5)],
        beats=_beats_4_4(1),
        arr_id="lead", arr_name="Lead Guitar",
    )
    assert lift_sloppak(pak) == []
    assert not any(pak.glob("notation_*.json"))


@pytest.mark.parametrize("name", ["Keys", "piano", "My Keyboard Part", "Synth 2"])
def test_keys_name_variants_match(tmp_path: Path, name: str):
    pak = _write_keys_sloppak(
        tmp_path,
        notes=[_wire_note(0.0, 72, sus=0.5)],
        beats=_beats_4_4(1),
        arr_name=name,
    )
    assert len(lift_sloppak(pak)) == 1


def test_lift_refuses_to_overwrite_orphan_notation_file(tmp_path: Path):
    pak = _write_keys_sloppak(
        tmp_path,
        notes=[_wire_note(0.0, 72, sus=0.5)],
        beats=_beats_4_4(1),
    )
    orphan = pak / "notation_keys.json"
    orphan.write_text("{}")
    assert lift_sloppak(pak) == []
    assert orphan.read_text() == "{}"


def test_lift_uses_song_timeline_when_present(tmp_path: Path):
    pak = _write_keys_sloppak(
        tmp_path,
        notes=[_wire_note(0.0, 72, sus=0.5), _wire_note(2.0, 74, sus=0.5)],
        beats=[],  # arrangement carries no beats
        extra_manifest={"song_timeline": "song_timeline.json"},
    )
    (pak / "song_timeline.json").write_text(json.dumps({
        "version": 1, "beats": _beats_4_4(2), "sections": [],
    }))
    changes = lift_sloppak(pak)
    assert len(changes) == 1
    payload = json.loads((pak / "notation_keys.json").read_text())
    assert len(payload["measures"]) == 2


def test_main_end_to_end_and_dry_run(tmp_path: Path, capsys):
    dlc = tmp_path / "dlc"
    dlc.mkdir()
    _write_keys_sloppak(
        dlc,
        notes=[_wire_note(0.0, 72, sus=0.5)],
        beats=_beats_4_4(1),
    )
    assert main([str(dlc), "--dry-run"]) == 0
    assert not (dlc / "song.sloppak" / "notation_keys.json").exists()
    assert main([str(dlc)]) == 0
    assert (dlc / "song.sloppak" / "notation_keys.json").exists()


def test_main_rejects_missing_dir(tmp_path: Path):
    assert main([str(tmp_path / "nope")]) == 2


def test_build_notation_pickup_measure_for_anacrusis():
    """Onsets before the first downbeat land in a pickup: true measure."""
    # First downbeat at t=2.0; one pickup note at t=1.0.
    beats = [{"time": 2.0, "measure": 1}, {"time": 4.0, "measure": 2}]
    notes = [
        {"t": 1.0, "midi": 60, "sus": 0.5},
        {"t": 2.0, "midi": 64, "sus": 0.5},
    ]
    payload = build_notation(notes, beats)
    m0, m1 = payload["measures"][0], payload["measures"][1]
    assert m0["pickup"] is True
    assert m0["t"] == 1.0
    assert m0["idx"] == 1 and m1["idx"] == 2
    # The pickup note sits inside the pickup measure, not measure 2.
    pickup_beats = m0["staves"]["rh"]["voices"][0]["beats"]
    assert [b["t"] for b in pickup_beats] == [1.0]
    m1_beats = m1["staves"]["rh"]["voices"][0]["beats"]
    assert [b["t"] for b in m1_beats] == [2.0]
    # No beat ever precedes its measure's own start.
    for m in payload["measures"]:
        for staff in m["staves"].values():
            for beat in staff["voices"][0]["beats"]:
                assert beat["t"] >= m["t"]


def test_build_notation_no_pickup_flag_when_first_onset_on_downbeat():
    beats = [{"time": 0.0, "measure": 1}, {"time": 2.0, "measure": 2}]
    payload = build_notation([{"t": 0.0, "midi": 60, "sus": 0.5}], beats)
    assert "pickup" not in payload["measures"][0]


def test_build_notation_splits_note_across_barline_with_tie():
    """A sustain crossing the next downbeat becomes note + tied continuation."""
    # 4/4 at 120 BPM (2s measures). Note starts on beat 4 (t=1.5) and rings
    # 1.0s — half a beat into measure 2.
    beats = [
        {"time": 0.0, "measure": 1},
        {"time": 2.0, "measure": 2},
        {"time": 4.0, "measure": 3},
    ]
    payload = build_notation([{"t": 1.5, "midi": 60, "sus": 1.0}], beats)
    m1, m2 = payload["measures"][0], payload["measures"][1]
    b1 = m1["staves"]["rh"]["voices"][0]["beats"]
    b2 = m2["staves"]["rh"]["voices"][0]["beats"]
    # Measure 1 holds the truncated head (0.5s = quarter at 120), untied.
    assert [b["t"] for b in b1] == [1.5]
    assert b1[0]["dur"] == 4
    assert "tied" not in b1[0]["notes"][0]
    # Measure 2 holds the tied continuation (0.5s quarter at its start).
    assert [b["t"] for b in b2] == [2.0]
    assert b2[0]["dur"] == 4
    assert b2[0]["notes"][0]["tied"] is True


def test_build_notation_clean_durations_not_split_by_jitter():
    """A note ending exactly on the barline is NOT split."""
    beats = [{"time": 0.0, "measure": 1}, {"time": 2.0, "measure": 2}]
    payload = build_notation([{"t": 1.0, "midi": 60, "sus": 1.0}], beats)
    m1 = payload["measures"][0]
    b1 = m1["staves"]["rh"]["voices"][0]["beats"]
    assert len(b1) == 1 and b1[0]["dur"] == 2  # half note at 120 BPM
    m2_staves = payload["measures"][1]["staves"]
    assert not m2_staves or "rh" not in m2_staves


def test_empty_song_timeline_beats_falls_back_to_arrangement(tmp_path: Path):
    """song_timeline with beats: [] is not authoritative — the arrangement
    JSON's beats still drive the lift."""
    pak = _write_keys_sloppak(
        tmp_path,
        notes=[_wire_note(0.0, 72, sus=0.5)],
        beats=_beats_4_4(1),  # beats live in the arrangement JSON
        extra_manifest={"song_timeline": "song_timeline.json"},
    )
    (pak / "song_timeline.json").write_text(json.dumps({
        "version": 1, "beats": [], "sections": [],
    }))
    assert len(lift_sloppak(pak)) == 1
    assert (pak / "notation_keys.json").is_file()


def test_manifest_write_failure_rolls_back_notation_files(tmp_path: Path, monkeypatch):
    """A failed manifest rewrite removes this run's notation sidecars so no
    orphan files remain."""
    pak = _write_keys_sloppak(
        tmp_path,
        notes=[_wire_note(0.0, 72, sus=0.5)],
        beats=_beats_4_4(1),
    )
    real_replace = Path.replace

    def boom(self, target):
        if str(target).endswith("manifest.yaml"):
            raise OSError("disk full")
        return real_replace(self, target)

    monkeypatch.setattr(Path, "replace", boom)
    with pytest.raises(OSError):
        lift_sloppak(pak)
    assert not any(pak.glob("notation_*.json"))
    # The manifest itself is untouched (no notation: key was persisted).
    assert "notation" not in (pak / "manifest.yaml").read_text()


def test_load_song_beats_skips_malformed_first_arrangement(tmp_path: Path):
    """A non-list `beats` (dict/string) in the first arrangement must not
    short-circuit the fallback — _load_song_beats consults later arrangements
    and returns the first VALID non-empty list."""
    pak = tmp_path / "song.sloppak"
    (pak / "arrangements").mkdir(parents=True)
    # First arrangement: malformed beats (a dict).
    (pak / "arrangements" / "a.json").write_text(json.dumps({
        "notes": [], "beats": {"bogus": 1}, "sections": [],
    }))
    # Second arrangement: valid beats.
    good = _beats_4_4(1)
    (pak / "arrangements" / "b.json").write_text(json.dumps({
        "notes": [], "beats": good, "sections": [],
    }))
    manifest = {
        "title": "T", "artist": "A", "duration": 4.0,
        "arrangements": [
            {"id": "a", "name": "Keys A", "file": "arrangements/a.json"},
            {"id": "b", "name": "Keys B", "file": "arrangements/b.json"},
        ],
        "stems": [],
    }
    (pak / "manifest.yaml").write_text(yaml.safe_dump(manifest, sort_keys=False))
    assert _load_song_beats(pak, manifest) == good
