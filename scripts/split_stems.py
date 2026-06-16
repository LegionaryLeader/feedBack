#!/usr/bin/env python3
"""Stub: the standalone sloppak stem-splitting tool has been removed.

This script previously split a sloppak's full-mix stem into per-instrument
stems via Demucs. Its implementation lived in the removed `sloppak_convert`
module. Use the in-app stem separation (Studio / stem-mixer) instead.
"""

from __future__ import annotations

import sys


def main() -> int:
    print(
        "split_stems.py: the stem-splitting tool is no longer available.\n"
        "Use the in-app stem separation (Studio / stem-mixer) instead.",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
