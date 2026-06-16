"""End-to-end tests for per-arrangement notation file loading in the sloppak loader.

Tests Option B architecture: notation key lives on each arrangement entry in the
manifest, not at the top level.
"""

from __future__ import annotations

import json
from pathlib import Path

import yaml

import sloppak as sloppak_mod


def _write_dir_sloppak_with_notation(root, notation_entries, extra_manifest=None):
    """
    notation_entries is a list of dicts:
      {
        "id": str,               # arrangement id
        "name": str,             # arrangement name (optional, defaults to id)
        "include_file": bool,    # whether to write arrangements/<id>.json
        "notation_filename": str | None,  # e.g. "notation_keys.json"; None = no notation key
        "notation_payload": dict | None,  # written to notation_filename if not None
      }
    extra_manifest: additional top-level manifest keys (dict | None)
    """
    pak = root / f"{root.name}.sloppak"
    pak.mkdir()
    arr_dir = pak / "arrangements"
    arr_dir.mkdir()

    arrangements = []
    for e in notation_entries:
        arr_id = e["id"]
        name = e.get("name", arr_id)
        entry: dict = {"id": arr_id, "name": name}

        if e.get("include_file"):
            arr_file = f"arrangements/{arr_id}.json"
            entry["file"] = arr_file
            arr_content = {
                "notes": [], "chords": [], "anchors": [],
                "handshapes": [], "templates": [],
            }
            (arr_dir / f"{arr_id}.json").write_text(json.dumps(arr_content))

        if e.get("notation_filename") is not None:
            entry["notation"] = e["notation_filename"]

        if e.get("notation_payload") is not None:
            (pak / e["notation_filename"]).write_text(json.dumps(e["notation_payload"]))

        arrangements.append(entry)

    manifest: dict = {
        "title": "Test",
        "artist": "Tester",
        "album": "",
        "year": 2026,
        "duration": 10.0,
        "arrangements": arrangements,
        "stems": [{"id": "full", "file": "stems/full.ogg", "default": True}],
    }
    if extra_manifest:
        manifest.update(extra_manifest)
    (pak / "manifest.yaml").write_text(yaml.safe_dump(manifest, sort_keys=False))
    return pak


def _load(pak_path: Path, tmp_path: Path):
    dlc_root = pak_path.parent
    cache = tmp_path / "cache"
    cache.mkdir()
    return sloppak_mod.load_song(pak_path.name, dlc_root, cache)


VALID_NOTATION = {"version": 1, "staves": [], "measures": []}


# ── Happy path ───────────────────────────────────────────────────────────────

def test_single_arrangement_with_notation(tmp_path: Path):
    pak = _write_dir_sloppak_with_notation(tmp_path, [
        {
            "id": "keys",
            "name": "Keys",
            "include_file": True,
            "notation_filename": "notation_keys.json",
            "notation_payload": VALID_NOTATION,
        },
    ])
    loaded = _load(pak, tmp_path)
    assert loaded.notation_by_id is not None
    assert "keys" in loaded.notation_by_id
    assert loaded.notation_by_id["keys"] == VALID_NOTATION
    assert len(loaded.song.arrangements) == 1


def test_two_arrangements_both_with_notation(tmp_path: Path):
    notation_a = {"version": 1, "staves": [{"id": "a"}], "measures": []}
    notation_b = {"version": 1, "staves": [{"id": "b"}], "measures": []}
    pak = _write_dir_sloppak_with_notation(tmp_path, [
        {
            "id": "lead",
            "include_file": True,
            "notation_filename": "notation_lead.json",
            "notation_payload": notation_a,
        },
        {
            "id": "bass",
            "include_file": True,
            "notation_filename": "notation_bass.json",
            "notation_payload": notation_b,
        },
    ])
    loaded = _load(pak, tmp_path)
    assert loaded.notation_by_id is not None
    assert loaded.notation_by_id["lead"] == notation_a
    assert loaded.notation_by_id["bass"] == notation_b
    assert len(loaded.song.arrangements) == 2


def test_arrangement_notation_key_no_file(tmp_path: Path):
    """Arrangement with notation: but no file: key still loads into song.arrangements."""
    pak = _write_dir_sloppak_with_notation(tmp_path, [
        {
            "id": "keys",
            "name": "Keys",
            "include_file": False,
            "notation_filename": "notation_keys.json",
            "notation_payload": VALID_NOTATION,
        },
    ])
    loaded = _load(pak, tmp_path)
    assert len(loaded.song.arrangements) == 1
    assert loaded.notation_by_id is not None
    assert loaded.notation_by_id["keys"] == VALID_NOTATION


def test_no_arrangement_has_notation_key(tmp_path: Path):
    """When no arrangement carries a notation key, notation_by_id is None."""
    pak = _write_dir_sloppak_with_notation(tmp_path, [
        {
            "id": "lead",
            "include_file": True,
            "notation_filename": None,
            "notation_payload": None,
        },
    ])
    loaded = _load(pak, tmp_path)
    assert loaded.notation_by_id is None
    assert len(loaded.song.arrangements) == 1


def test_mixed_one_notation_one_without(tmp_path: Path):
    """One arrangement has notation, one does not — both load; only one in notation_by_id."""
    pak = _write_dir_sloppak_with_notation(tmp_path, [
        {
            "id": "lead",
            "include_file": True,
            "notation_filename": "notation_lead.json",
            "notation_payload": VALID_NOTATION,
        },
        {
            "id": "bass",
            "include_file": True,
            "notation_filename": None,
            "notation_payload": None,
        },
    ])
    loaded = _load(pak, tmp_path)
    assert len(loaded.song.arrangements) == 2
    assert loaded.notation_by_id is not None
    assert "lead" in loaded.notation_by_id
    assert "bass" not in loaded.notation_by_id


# ── Isolation / error cases ──────────────────────────────────────────────────

def test_notation_file_missing_arrangement_still_loads(tmp_path: Path):
    """notation_filename set but file not written — arr loads, notation_by_id is None."""
    pak = _write_dir_sloppak_with_notation(tmp_path, [
        {
            "id": "keys",
            "include_file": True,
            "notation_filename": "notation_keys.json",
            "notation_payload": None,  # file not written
        },
    ])
    loaded = _load(pak, tmp_path)
    assert len(loaded.song.arrangements) == 1
    assert loaded.notation_by_id is None


def test_notation_file_invalid_json_arrangement_still_loads(tmp_path: Path):
    """Notation file present but unparseable JSON — arr loads, key absent."""
    pak = _write_dir_sloppak_with_notation(tmp_path, [
        {
            "id": "keys",
            "include_file": True,
            "notation_filename": "notation_keys.json",
            "notation_payload": None,
        },
    ])
    (pak / "notation_keys.json").write_text("not json {{{")
    loaded = _load(pak, tmp_path)
    assert len(loaded.song.arrangements) == 1
    assert loaded.notation_by_id is None


def test_notation_file_fails_validation_arrangement_still_loads(tmp_path: Path):
    """Notation file present but measures is not a list — arr loads, key absent."""
    invalid_notation = {"version": 1, "staves": [], "measures": "not a list"}
    pak = _write_dir_sloppak_with_notation(tmp_path, [
        {
            "id": "keys",
            "include_file": True,
            "notation_filename": "notation_keys.json",
            "notation_payload": invalid_notation,
        },
    ])
    loaded = _load(pak, tmp_path)
    assert len(loaded.song.arrangements) == 1
    assert loaded.notation_by_id is None


def test_notation_path_traversal_arrangement_still_loads(tmp_path: Path):
    """notation: "../outside.json" is a path traversal — arr loads, key absent."""
    pak = _write_dir_sloppak_with_notation(tmp_path, [
        {
            "id": "keys",
            "include_file": True,
            "notation_filename": "../outside.json",
            "notation_payload": None,  # don't attempt write outside pak
        },
    ])
    loaded = _load(pak, tmp_path)
    assert len(loaded.song.arrangements) == 1
    assert loaded.notation_by_id is None


def test_notation_absolute_path_arrangement_still_loads(tmp_path: Path):
    """notation: "/etc/passwd" absolute path — arr loads, key absent."""
    pak = _write_dir_sloppak_with_notation(tmp_path, [
        {
            "id": "keys",
            "include_file": True,
            "notation_filename": "/etc/passwd",
            "notation_payload": None,
        },
    ])
    loaded = _load(pak, tmp_path)
    assert len(loaded.song.arrangements) == 1
    assert loaded.notation_by_id is None


# ── id edge cases ────────────────────────────────────────────────────────────

def test_arrangement_without_id_skips_notation(tmp_path: Path):
    """Arrangement entry missing 'id' field — notation skipped, arr still loads."""
    pak = _write_dir_sloppak_with_notation(tmp_path, [
        {
            "id": "keys",
            "include_file": True,
            "notation_filename": "notation_keys.json",
            "notation_payload": VALID_NOTATION,
        },
    ])
    manifest = yaml.safe_load((pak / "manifest.yaml").read_text())
    del manifest["arrangements"][0]["id"]
    (pak / "manifest.yaml").write_text(yaml.safe_dump(manifest, sort_keys=False))
    loaded = _load(pak, tmp_path)
    assert len(loaded.song.arrangements) == 1
    assert loaded.notation_by_id is None


def test_arrangement_empty_id_skips_notation(tmp_path: Path):
    """Arrangement entry with id: '' — notation skipped, arr still loads."""
    pak = _write_dir_sloppak_with_notation(tmp_path, [
        {
            "id": "keys",
            "include_file": True,
            "notation_filename": "notation_keys.json",
            "notation_payload": VALID_NOTATION,
        },
    ])
    manifest = yaml.safe_load((pak / "manifest.yaml").read_text())
    manifest["arrangements"][0]["id"] = ""
    (pak / "manifest.yaml").write_text(yaml.safe_dump(manifest, sort_keys=False))
    loaded = _load(pak, tmp_path)
    assert len(loaded.song.arrangements) == 1
    assert loaded.notation_by_id is None


# ── arrangement_ids parallel-index alignment ─────────────────────────────────

def test_malformed_notation_key_dict_does_not_create_phantom_arrangement(tmp_path: Path):
    """A notation key whose value is a dict (not a string) with no file must not
    create a phantom placeholder arrangement."""
    pak = _write_dir_sloppak_with_notation(tmp_path, [
        {
            # No file, notation value is a dict — truthy but not a valid path.
            "id": "bad",
            "include_file": False,
            "notation_filename": None,
            "notation_payload": None,
            "_raw_notation": {"nested": "dict"},
        },
    ])
    # Patch the manifest to inject the malformed notation key directly.
    import yaml  # noqa: PLC0415
    manifest_path = pak / "manifest.yaml"
    manifest = yaml.safe_load(manifest_path.read_text())
    manifest["arrangements"][0]["notation"] = {"nested": "dict"}
    manifest_path.write_text(yaml.safe_dump(manifest, sort_keys=False))

    loaded = _load(pak, tmp_path)
    assert len(loaded.song.arrangements) == 0, (
        "malformed notation key (dict) with no file must not create a phantom arrangement"
    )


def test_malformed_notation_key_list_does_not_create_phantom_arrangement(tmp_path: Path):
    """A notation key whose value is a list with no file must not create a
    phantom placeholder arrangement."""
    pak = _write_dir_sloppak_with_notation(tmp_path, [
        {
            "id": "bad",
            "include_file": False,
            "notation_filename": None,
            "notation_payload": None,
        },
    ])
    import yaml  # noqa: PLC0415
    manifest_path = pak / "manifest.yaml"
    manifest = yaml.safe_load(manifest_path.read_text())
    manifest["arrangements"][0]["notation"] = ["not", "a", "path"]
    manifest_path.write_text(yaml.safe_dump(manifest, sort_keys=False))

    loaded = _load(pak, tmp_path)
    assert len(loaded.song.arrangements) == 0, (
        "malformed notation key (list) with no file must not create a phantom arrangement"
    )


def test_arrangement_ids_aligned_with_song_arrangements(tmp_path: Path):
    """arrangement_ids is parallel to song.arrangements (not manifest list).

    When a manifest entry is skipped (no file, no notation), the entries that
    *do* load must still be reachable by their compacted index, not the raw
    manifest index.
    """
    # Build a sloppak with three manifest entries: the first has neither file
    # nor notation so it is skipped by load_song.  The second and third load
    # normally.
    pak = _write_dir_sloppak_with_notation(tmp_path, [
        {
            # Skipped: no file, no notation key.
            "id": "ghost",
            "include_file": False,
            "notation_filename": None,
            "notation_payload": None,
        },
        {
            "id": "lead",
            "include_file": True,
            "notation_filename": "notation_lead.json",
            "notation_payload": VALID_NOTATION,
        },
        {
            "id": "keys",
            "include_file": True,
            "notation_filename": "notation_keys.json",
            "notation_payload": VALID_NOTATION,
        },
    ])
    loaded = _load(pak, tmp_path)

    # Only two arrangements should have loaded (ghost was skipped).
    assert len(loaded.song.arrangements) == 2
    # arrangement_ids must be parallel: index 0 → lead, index 1 → keys.
    assert loaded.arrangement_ids == ["lead", "keys"]
    # Notation lookup via compacted index must be correct.
    assert loaded.notation_by_id is not None
    assert "lead" in loaded.notation_by_id
    assert "keys" in loaded.notation_by_id
