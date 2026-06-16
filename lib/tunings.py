"""Tuning data and helpers.

Kept separate from server.py so tests can import it without triggering
FastAPI / SQLite module-level side effects.
"""

DEFAULT_REFERENCE_PITCH = 440.0

# Canonical tuning frequencies at 440 Hz reference, keyed by instrument then
# tuning name. This is the authoritative source; tuner/routes.py previously
# held a copy — it was removed in favour of this one.
DEFAULT_TUNINGS: dict[str, dict[str, list[float]]] = {
    "guitar-6": {
        "Standard":    [82.41, 110.00, 146.83, 196.00, 246.94, 329.63],
        "Eb Standard": [77.78, 103.83, 138.59, 185.00, 233.08, 311.13],
        "Drop D":      [73.42, 110.00, 146.83, 196.00, 246.94, 329.63],
        "D Standard":  [73.42,  98.00, 130.81, 174.61, 220.00, 293.66],
        "Drop C":      [65.41,  98.00, 130.81, 174.61, 220.00, 293.66],
        "Open G":      [73.42,  98.00, 146.83, 196.00, 246.94, 293.66],
        "Open D":      [73.42, 110.00, 146.83, 185.00, 220.00, 293.66],
        "DADGAD":      [73.42, 110.00, 146.83, 196.00, 220.00, 293.66],
        "Open E":      [82.41, 123.47, 164.81, 207.65, 246.94, 329.63],
    },
    "guitar-7": {
        "Standard":    [61.74, 82.41, 110.00, 146.83, 196.00, 246.94, 329.63],
        "Drop A":      [55.00, 82.41, 110.00, 146.83, 196.00, 246.94, 329.63],
        "A Standard":  [55.00, 73.42,  98.00, 130.81, 174.61, 220.00, 293.66],
        "Drop G":      [49.00, 73.42, 110.00, 146.83, 196.00, 246.94, 329.63],
        "Bb Standard": [58.27, 77.78, 103.83, 138.59, 185.00, 233.08, 311.13],
    },
    "guitar-8": {
        "Standard":    [46.25, 61.74, 82.41, 110.00, 146.83, 196.00, 246.94, 329.63],
        "Drop E":      [41.20, 61.74, 82.41, 110.00, 146.83, 196.00, 246.94, 329.63],
        "E Standard":  [41.20, 55.00, 73.42,  98.00, 130.81, 174.61, 220.00, 293.66],
        "Drop D":      [36.71, 55.00, 73.42,  98.00, 130.81, 174.61, 220.00, 293.66],
        "Eb Standard": [38.89, 51.91, 69.30,  92.50, 123.47, 164.81, 207.65, 277.18],
    },
    "bass-4": {
        "Standard":    [41.20, 55.00, 73.42,  98.00],
        "Eb Standard": [38.89, 51.91, 69.30,  92.50],
        "Drop D":      [36.71, 55.00, 73.42,  98.00],
        "D Standard":  [36.71, 48.99, 65.41,  87.31],
        "Drop C":      [32.70, 48.99, 65.41,  87.31],
    },
    "bass-5": {
        "Standard":    [30.87, 41.20, 55.00, 73.42,  98.00],
        "Eb Standard": [29.14, 38.89, 51.91, 69.30,  92.50],
        "Drop D":      [30.87, 36.71, 55.00, 73.42,  98.00],
        "D Standard":  [27.50, 36.71, 48.99, 65.41,  87.31],
        "Drop C":      [27.50, 32.70, 48.99, 65.41,  87.31],
    },
}


def apply_reference_pitch(
    tunings: dict[str, dict[str, list[float]]],
    reference_pitch: float,
) -> dict[str, dict[str, list[float]]]:
    """Return a copy of tunings with all frequencies scaled to reference_pitch."""
    scale = reference_pitch / DEFAULT_REFERENCE_PITCH
    return {
        instrument: {
            name: [round(f * scale, 4) for f in freqs]
            for name, freqs in names.items()
        }
        for instrument, names in tunings.items()
    }


def tuning_name(offsets: list[int]) -> str:
    # All three pattern checks below are gated on `len(offsets) == 6`. The
    # naming conventions here are 6-string-specific — e.g. a 7-string all-zeros
    # tuning has a low B, not an E, so labeling it "E Standard" would be wrong.
    # 7+-string community content falls through to the numeric fallback. See #43.

    # Standard tunings (all six strings same offset)
    standard = {
        0: "E Standard", -1: "Eb Standard", -2: "D Standard",
        -3: "C# Standard", -4: "C Standard", -5: "B Standard",
        -6: "Bb Standard", -7: "A Standard",
        1: "F Standard", 2: "F# Standard",
    }
    if len(offsets) == 6 and all(o == offsets[0] for o in offsets):
        name = standard.get(offsets[0])
        if name:
            return name

    # Drop tunings (low string 2 semitones below the rest)
    # Named after the low string's note: e.g. offsets[-2,0,0,0,0,0] = Drop D (low E dropped to D)
    if len(offsets) == 6 and offsets[0] == offsets[1] - 2 and all(o == offsets[1] for o in offsets[1:]):
        note_names = ["E", "F", "F#", "G", "Ab", "A", "Bb", "B", "C", "C#", "D", "Eb"]
        low_note = note_names[offsets[0] % 12]
        return f"Drop {low_note}"

    # Common named tunings
    named = {
        (-2, 0, 0, 0, 0, 0): "Drop D",
        (-4, -2, -2, -2, -2, -2): "Drop C",
        (-2, -2, 0, 0, 0, 0): "Double Drop D",
        (0, 0, 0, -1, 0, 0): "Open G",
        (-2, -2, 0, 0, -2, -2): "Open D",
        (-2, 0, 0, 0, -2, 0): "DADGAD",
        (0, 2, 2, 1, 0, 0): "Open E",
        (-2, 0, 0, 2, 3, 2): "Open D (alt)",
    }
    if len(offsets) == 6 and tuple(offsets) in named:
        return named[tuple(offsets)]

    if not offsets:
        return "Unknown"
    return "Custom Tuning"
