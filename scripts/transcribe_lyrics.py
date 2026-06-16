#!/usr/bin/env python3
"""Add WhisperX-transcribed lyrics to an existing sloppak.

Usage:
    python scripts/transcribe_lyrics.py path/to/song.sloppak
    python scripts/transcribe_lyrics.py path/to/song.sloppak --force
    python scripts/transcribe_lyrics.py path/to/dir/        # batch over dir of sloppaks

Behaviour by input state:

  1. Sloppak already has stems/vocals.ogg → transcribe directly. Fast path.
  2. Sloppak only has stems/full.ogg     → run Demucs to extract vocals,
                                            then transcribe. Keeps other
                                            split stems as a side effect.
  3. Sloppak already has lyrics          → skip with a message; pass
     (any manifest-declared path,         --force to overwrite (the
     not just lyrics.json)                v1 fallback-only default is
                                          opt-out via this flag). On
                                          overwrite, the fresh transcript
                                          always lands at canonical
                                          <sloppak>/lyrics.json (sloppak
                                          root, not under stems/) and the
                                          manifest's `lyrics:` key gets
                                          repointed.

Requires whisperx for the local path, or a configured remote demucs server
(which hosts /align too) via $CONFIG_DIR/config.json:

    {
      "demucs_server_url": "http://...",       // reused for WhisperX /align
      "whisperx": {"enabled": true, "model_size": "medium"}
    }

The transcription step honours the `whisperx` config sub-section the same
way the converter does. `--force` only bypasses the existing-lyrics gate;
it does not enable WhisperX itself — the script unconditionally forces
the transcription on (overriding the config's `enabled: false` default),
since running the script at all is an explicit opt-in.
"""

from __future__ import annotations

import sys

# The batch lyric-transcription driver (`transcribe_existing_sloppak`) lived in
# the `sloppak_convert` module, which has been removed. The underlying WhisperX
# transcription primitives still exist in `lib/lyrics_transcribe.py`, but the
# orchestration that walked a sloppak, ran Demucs to get a vocals stem, and
# wrote `lyrics.json` was part of the removed converter. This script is retained
# only as a stub so its CLI entry point does not crash on a missing import.


def main() -> int:
    print(
        "transcribe_lyrics.py: the batch sloppak lyric-transcription tool is no "
        "longer available.\nUse the in-app lyric transcription instead.",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
