"""Loader coverage for the sloppak `centOffset` field — both the arrangement
JSON wire value and the manifest-level override (which mirrors how `tuning` /
`capo` overrides work, per docs/sloppak-spec.md §2.1)."""

from __future__ import annotations

import json
from pathlib import Path

import yaml

import sloppak as sloppak_mod


def _build(root: Path, arr_extras: dict, manifest_arr_extras: dict) -> Path:
    """Build a directory-form sloppak with one Lead arrangement, letting the
    caller inject keys into both the arrangement JSON and its manifest entry."""
    pak = root / f"{root.name}.sloppak"
    pak.mkdir()
    arr_dir = pak / "arrangements"
    arr_dir.mkdir()

    arr = {
        "name": "Lead",
        "tuning": [0, 0, 0, 0, 0, 0],
        "capo": 0,
        "notes": [],
        "chords": [],
        "anchors": [],
        "handshapes": [],
        "templates": [],
        "beats": [],
        "sections": [],
    }
    arr.update(arr_extras)
    (arr_dir / "lead.json").write_text(json.dumps(arr))

    arr_entry = {"id": "lead", "name": "Lead", "file": "arrangements/lead.json"}
    arr_entry.update(manifest_arr_extras)
    manifest = {
        "title": "Test",
        "artist": "Tester",
        "album": "",
        "year": 2026,
        "duration": 10.0,
        "arrangements": [arr_entry],
        "stems": [{"id": "full", "file": "stems/full.ogg", "default": True}],
    }
    (pak / "manifest.yaml").write_text(yaml.safe_dump(manifest, sort_keys=False))
    return pak


def _load(pak: Path, tmp_path: Path):
    cache = tmp_path / "cache"
    cache.mkdir()
    return sloppak_mod.load_song(pak.name, pak.parent, cache)


def test_cent_offset_from_arrangement_json(tmp_path: Path):
    pak = _build(tmp_path, {"centOffset": -1200.0}, {})
    loaded = _load(pak, tmp_path)
    assert loaded.song.arrangements[0].cent_offset == -1200.0


def test_manifest_cent_offset_overrides_arrangement_json(tmp_path: Path):
    # Arrangement JSON says +5.0, manifest says -1200.0 — manifest wins, like
    # tuning/capo.
    pak = _build(tmp_path, {"centOffset": 5.0}, {"centOffset": -1200.0})
    loaded = _load(pak, tmp_path)
    assert loaded.song.arrangements[0].cent_offset == -1200.0


def test_cent_offset_defaults_zero_when_absent_everywhere(tmp_path: Path):
    pak = _build(tmp_path, {}, {})
    loaded = _load(pak, tmp_path)
    assert loaded.song.arrangements[0].cent_offset == 0.0


def test_manifest_cent_offset_non_finite_sanitized(tmp_path: Path):
    # A corrupt manifest carrying NaN must not poison the song_info JSON.
    pak = _build(tmp_path, {}, {"centOffset": float("nan")})
    loaded = _load(pak, tmp_path)
    assert loaded.song.arrangements[0].cent_offset == 0.0
