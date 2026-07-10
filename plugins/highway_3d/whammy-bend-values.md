# Whammy bend-animation values (for later)

Tuned bend **end poses** for the whammy-bridge model, to be applied when the real
per-note-type triggers exist. **Not wired into the game yet** — there is nowhere
to apply them (harmonics are only a temporary stand-in trigger, and a harmonic is
not a dive/pull). Kept here for safekeeping.

The bend rotates the model about its **anchored back edge** (`animG` in
`screen.js` — the back is always the pivot, never rotate in place). Values are a
rotation on the **Y axis**, in degrees, interpolated from a neutral 0° start over
the note's duration (longer note → slower bend):

| Note gesture | Bend end (Y) |
|---|---|
| Dive         | **+13°** |
| Pull         | **−13°** |
| Light dive   | **+5°**  |
| Light pull   | **−5°**  |
