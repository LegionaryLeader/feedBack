# Real-Instrument WAV Fixtures

Drop WAV recordings from your actual instruments here and they will be picked up automatically by the real-instrument test suite (`tests/js/yin.realinstrument.test.js`).

## Naming Convention

```text
<NoteClass><Octave>_<FreqHz>Hz[_label].wav
```

An optional label suffix (e.g. `_8string`, `_guitar`, `_take2`) can be added between `Hz` and `.wav` — it is ignored by the test runner.

Examples:

| File | Note | Expected frequency |
|------|------|--------------------|
| `E2_82.41Hz.wav` | E2 | 82.41 Hz |
| `E2_82.41Hz_8string.wav` | E2 | 82.41 Hz |
| `A2_110Hz_bass.wav` | A2 | 110.00 Hz |
| `A#3_233.08Hz.wav` | A#3 | 233.08 Hz |
| `D3_146.83Hz.wav` | D3 | 146.83 Hz |

The test asserts that YIN detects a frequency within **±20 cents** of the value in the filename.

## Recording Guidelines

1. **Capture the sustain portion** — not the attack or release. A 1–2 second clip of a note ringing cleanly is ideal. The test extracts a 4096-sample window from the middle of the file to skip transients.
2. **Length** — aim for ≤ 2 seconds to keep repository size small.
3. **Format** — **16-bit PCM WAV** (mono or stereo). Export at 44100 Hz or 48000 Hz from your DAW or audio interface.
   - 32-bit float WAV is not supported by the parser — convert to 16-bit PCM first.
4. **Channels** — mono or stereo both work. Stereo files are averaged to mono before detection.
5. **Tune first** — play the note in tune against a reference tuner before recording. The file name encodes the expected frequency; a note recorded sharp or flat will fail the test.

## Frequency Reference (standard MIDI A4 = 440 Hz)

| Note | Hz |
|------|----|
| E2 | 82.41 |
| A2 | 110.00 |
| D3 | 146.83 |
| G3 | 196.00 |
| B3 | 246.94 |
| E4 | 329.63 |
| A4 | 440.00 |
| A#3 / Bb3 | 233.08 |

For any other note: `f = 440 * 2^((midi - 69) / 12)`.

## Committing Recordings

These WAV files **are committed to the repository** as regression fixtures. If a code change causes the detected pitch to drift outside ±20 cents, CI will flag it.

> **Repository size note:** Keep clips short (≤ 2 s). If the fixture corpus grows large, Git LFS is a future option — configure it with `git lfs track "tests/fixtures/audio/real/*.wav"`.
