#!/usr/bin/env python3
"""
Generate WAV fixture files for YIN pitch detection tests.

Naming convention: <Note><Octave>_<FreqHz>Hz.wav
  e.g.  A4_440.0Hz.wav   →  440.0 Hz sine wave
        E2_82.41Hz.wav   →  82.41 Hz sine wave

To add more fixtures, just call generate() with the desired note/frequency
and re-run this script, or drop in your own WAV files following the naming
convention (16-bit PCM mono, any sample rate ≥ 8000 Hz).
"""

import math
import struct
import wave
from pathlib import Path

FIXTURES_DIR = Path(__file__).parent / "audio"  # tests/plugins/tuner/fixtures/audio/
SAMPLE_RATE = 44100
DURATION_SEC = 0.5
AMPLITUDE = 0.8

FIXTURES = [
    ("E2",  82.41),
    ("A2", 110.00),
    ("D3", 146.83),
    ("G3", 196.00),
    ("B3", 246.94),
    ("E4", 329.63),
    ("A4", 440.00),
]


def _freq_to_str(hz: float) -> str:
    return f"{hz:.2f}".rstrip("0").rstrip(".")


def generate(note: str, freq_hz: float, sample_rate: int = SAMPLE_RATE,
             duration_sec: float = DURATION_SEC, amplitude: float = AMPLITUDE) -> Path:
    filename = f"{note}_{_freq_to_str(freq_hz)}Hz.wav"
    path = FIXTURES_DIR / filename
    n = int(sample_rate * duration_sec)
    frames = b"".join(
        struct.pack("<h", int(amplitude * math.sin(2 * math.pi * freq_hz * i / sample_rate) * 32767))
        for i in range(n)
    )
    with wave.open(str(path), "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(frames)
    print(f"  wrote {path.name}  ({freq_hz} Hz, {n} samples)")
    return path


if __name__ == "__main__":
    FIXTURES_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Generating {len(FIXTURES)} WAV fixtures in {FIXTURES_DIR}/")
    for note, freq in FIXTURES:
        generate(note, freq)
    print("Done.")
