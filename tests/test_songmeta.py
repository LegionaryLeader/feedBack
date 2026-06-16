"""Unit tests for lib/songmeta.py — metadata file-persistence helpers."""
from __future__ import annotations

# songmeta lives in lib/ which is on PYTHONPATH via conftest / pyproject
from songmeta import (
    _apply_to_sloppak_manifest,
    _coerce_year,
)


class TestCoerceYear:
    def test_int_passthrough(self):
        assert _coerce_year(2024) == 2024

    def test_string_digit(self):
        assert _coerce_year("2024") == 2024

    def test_empty_string_clears(self):
        # A user clearing the year field sends "" — must map to 0 so the
        # scanner reads it back as "" (str(0 or "") == "").
        assert _coerce_year("") == 0

    def test_none_clears(self):
        assert _coerce_year(None) == 0

    def test_non_numeric_string_clears(self):
        assert _coerce_year("unknown") == 0

    def test_zero_passthrough(self):
        assert _coerce_year(0) == 0


class TestApplyToSloppakManifest:
    def test_set_title(self):
        manifest = {"title": "Old Title", "artist": "A"}
        dirty = _apply_to_sloppak_manifest(manifest, {"title": "New Title"})
        assert dirty
        assert manifest["title"] == "New Title"
        assert manifest["artist"] == "A"  # untouched

    def test_set_year(self):
        manifest = {"year": 2000}
        dirty = _apply_to_sloppak_manifest(manifest, {"year": "2024"})
        assert dirty
        assert manifest["year"] == 2024

    def test_clear_year(self):
        """Clearing year (empty string) must write 0, not be silently skipped."""
        manifest = {"year": 2020}
        dirty = _apply_to_sloppak_manifest(manifest, {"year": ""})
        assert dirty, "clearing year should mark manifest dirty"
        assert manifest["year"] == 0

    def test_no_year_key_leaves_existing(self):
        """If 'year' is not in fields at all, the existing value is preserved."""
        manifest = {"year": 2020}
        dirty = _apply_to_sloppak_manifest(manifest, {"title": "T"})
        assert dirty
        assert manifest["year"] == 2020  # untouched

    def test_empty_fields(self):
        manifest = {"title": "T"}
        dirty = _apply_to_sloppak_manifest(manifest, {})
        assert not dirty
