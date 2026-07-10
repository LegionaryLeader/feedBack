# Whammy 3D model feature — handoff

Working doc for whoever (agent or human) continues this. **Delete before opening the PR.**
Last updated at plugin version **3.36.0**, branch **`feat/whammy-tremolo-model`** (uncommitted).

---

## 1. What this feature is

Render a Floyd Rose tremolo ("whammy") 3D model on the guitar neck in the `highway_3d`
plugin. It will eventually appear on a **specific note type that does not exist in the
game yet**. Until then it is **temporarily gated to harmonic notes** (`n.hm` natural /
`n.hp` pinch) so it can be seen and tuned. The user is a **non-developer** contributor;
run the git/deploy commands for them and explain plainly.

This is the **first time any plugin loads an external 3D model** — all other 3D in the
game is procedural geometry. So this introduces a new pattern (see §8 PR notes).

---

## 2. Locations & environment

- **Source repo (git):** `E:\Coding\feedBack-src`
  - Remotes: `upstream` = `github.com/got-feedback/feedBack`, `fork` = `github.com/LegionaryLeader/feedBack`
  - Branch: `feat/whammy-tremolo-model` (off `main`). **Nothing committed yet** — all work is uncommitted working-tree changes. User decides when to commit.
- **Two game installs** (runtime copies — must be synced to test in-game):
  - `E:\Coding\FeedBack Testing\feedback\current\resources\slopsmith\`
  - `E:\Coding\feedback\current\resources\slopsmith\`
  - Skip any `current.bak-*` backup dirs.
- **Launch to test:** `E:\Coding\FeedBack Testing\feedback\feedback.exe` — user must FULLY quit and relaunch (don't run `Update.exe`, it can overwrite synced plugin files).
- Static assets served at `/static/...`; plugin assets at `/api/plugins/highway_3d/assets/...`.
- THREE.js is vendored, pinned **r170**, loaded from `/static/vendor/three/three.module.min.js`.

## Git / PR rules (project-specific, non-negotiable)
- **Every commit must be signed off** (`git commit -s`).
- **PRs target `got-feedback/feedBack` `main`**, opened from the user's fork. Never push to upstream main.
- The plugin `version` in `plugin.json` is the **cache-bust key**: the game only re-fetches `screen.js` when the version changes. **Bump it on every change** or the game runs cached code.

---

## 3. Files changed / added

**Modified (tracked):**
- `plugins/highway_3d/screen.js` (+~326 lines) — all renderer + settings logic
- `plugins/highway_3d/settings.html` (+~170 lines) — the settings panel + hydration
- `plugins/highway_3d/plugin.json` — version only (now `3.36.0`)

**New (untracked — must `git add` before commit):**
- `plugins/highway_3d/assets/whammy_01.glb`, `whammy_02_streight.glb`, `whammy_03_simple.glb` — the 3 models (all valid glTF 2.0, single mesh, no textures/animations)
- `plugins/highway_3d/whammy-bend-values.md` — saved bend-animation values (see §6)
- `static/vendor/three/addons/loaders/GLTFLoader.js` — vendored from three r170; its `from 'three'` import was rewritten to `from '../../three.module.min.js'`
- `static/vendor/three/addons/utils/BufferGeometryUtils.js` — same (GLTFLoader dependency), same import rewrite
- `WHAMMY_HANDOFF.md` — this file (delete before PR)

**Pre-existing untracked (NOT ours — leave alone):** `.claude/skills/verify/`, `data/dlc/`

---

## 4. Deploy process (do this on EVERY change)

1. Edit source in `E:\Coding\feedBack-src`.
2. Bump `plugins/highway_3d/plugin.json` `version`.
3. Syntax-check: `node --check plugins/highway_3d/screen.js`, and validate each `<script>` in settings.html (extract with regex + `new Function(body)`).
4. Copy `screen.js`, `settings.html`, `plugin.json` (and any new `assets/*.glb` or vendored addon files) into **BOTH** install dirs (§2).
5. **md5-verify** every copied file matches across source + both installs (a stale install silently shows old behavior — this bit us before).
6. Tell the user to fully quit + relaunch.

`whammy-bend-values.md` and this handoff are docs — source only, not deployed.

---

## 5. Current behavior & where it lives in `screen.js`

All whammy code is grepping `whammy` / `Whammy` / `WHAMMY`. Key pieces:

- **Constants** (top of file, ~lines 30–60): `WHAMMY_MODELS` (id→URL map), `WHAMMY_MODEL_IDS`, baked transform `WHAMMY_ROT_X` (270°) + `WHAMMY_SCALE_MUL` (2.17), look consts (`WHAMMY_BODY_COLOR/OPACITY/EMISSIVE_I`, `WHAMMY_RIM_*`), fade consts (`WHAMMY_FADE_IN/OUT` = 0.6, `WHAMMY_MIN_DUR` = 0.25, `WHAMMY_LOOKBACK` = 8.0), `WHAMMY_BACK_SIGN` (anchor end), and **`_whammyIsTriggerNote = (n) => n.hm || n.hp`** — the ONE place to change the trigger.
- **`loadGLTFLoader()`** — memoized dynamic import of the vendored GLTFLoader (near `loadThree()`).
- **Settings plumbing** (follow the existing plugin pattern exactly):
  - `BG_DEFAULTS` — whammy keys: `whammyModel`, `whammyFollow`, `whammyPreviewAlways`, `whammyColor`, `whammyFretOffset` (10), `whammyDepthFollow` (0.05), `whammyHeight` (0.70), `whammyDepthFixed` (0.02), `whammyFixedPos` (0.5)
  - `_BG_BOOL_KEYS` (+`whammyFollow`, `whammyPreviewAlways`), `_BG_FLOAT_KEYS` (+the 0..1 sliders), `_bgCoerce` (`whammyModel` id-validate; `whammyColor` via the hex6 branch)
  - `window.h3dBgSetWhammy*` setters
  - `_bgLoadSettings()` reads them into per-instance `let`s (maps sliders → world units: depth `×250*K`, height `(v-0.5)×80*K`, fixed pos `(v-0.5)×600*K`)
  - the settings-change **listener** "just reload" branch lists the whammy keys
- **`_disposeWhammyModel()` / `_loadWhammyModel(id)` / `_updateWhammy(bundle)`** (near `teardown()`), and `_whammyEnvelope(elapsed, dur)`. `_updateWhammy(bundle)` is called from `draw()` right after `camUpdate(bundle)`.
- **teardown** disposes the model + resets refs.

**Transform hierarchy** built in `_loadWhammyModel`: `pivot` (world position + scale) → `animG` (bend rotation, **origin = back edge**) → `modelG` (baked 270°, body+rim recentred on bbox centre). The back edge is found from the model bbox (long horizontal axis, `WHAMMY_BACK_SIGN` picks the end). `animG` is the pivot the bend animation will use.

**Look:** translucent tinted body (`MeshLambertMaterial`, opacity 0.55, tiny emissive) + additive **inverted-hull rim** (a BackSide clone scaled ×1.04). Both feed the scene bloom — matches the note-gem / sustain-trail aesthetic, deliberately NOT realistic PBR (scene has no env map → real metal would render black; documented at `screen.js` ~line 880).

**Runtime behavior:**
- **Model dropdown**: Off / 01 / 02 (straight) / 03 (simple). Default 01. Switching disposes + reloads live.
- **Gated to harmonics** (temporary): fades in on the nearest harmonic note — envelope is fade-in 0.6s → hold across the note's `n.sus` duration → fade-out 0.6s.
- **"Always show (preview)"** checkbox overrides the gate; shows continuously at the play head for positioning.
- **"Follow the chart"** toggle:
  - ON → position at the note's fret + `whammyFretOffset`, `whammyHeight` Y offset, `whammyDepthFollow` Z.
  - OFF → parked past fret 24 by `whammyFixedPos`, centred Y, `whammyDepthFixed` Z.
  - The mode-specific sliders show/hide via `window.h3dWhammyFollowUI(on)` (defined in the settings.html hydration IIFE, called from the checkbox onchange + on load).
- **Colour** picker (`<input type="color">`, default `#4a60cf`), applied live to body + rim each frame.

---

## 6. Bend animation — PENDING (values saved, not wired)

The bend is intentionally **not driven yet**: harmonics are a stand-in trigger and are not a
dive/pull, so there's nowhere to apply it. The `animG` back-edge pivot is in place and ready.

Tuned values (in `plugins/highway_3d/whammy-bend-values.md`) — rotation on the **Y axis**,
about the anchored **back edge**, interpolated 0° → end over the note's duration:

| Gesture | Bend end (Y) |
|---|---|
| Dive | **+13°** | Pull | **−13°** | Light dive | **+5°** | Light pull | **−5°** |

**To wire it up (when a real dive/pull note type exists):** map the note gesture → Y end
angle, and in `_updateWhammy` set `animG.rotation.y` by interpolating `0 → endRad` over the
note progress `(now - note.t) / dur` (smoothstep). The anchor (back edge) is confirmed
correct; the axis is Y. Earlier attempts on other axes/auto-detection were wrong — use Y.

---

## 7. Reference facts (verified from the codebase)

- **Note wire keys** (`bundle.notes[i]`): `n.t` time, `n.s` string, `n.f` fret, `n.sus` sustain(s), `n.hm` natural harmonic, `n.hp` pinch harmonic (+ bend/slide/etc.). Source of truth: `lib/song.py` `Note` dataclass. `bundle.currentTime` is playback seconds.
- **Coordinate system** (`plugins/highway_3d/CLAUDE.md`): +X along neck, +Y up, +Z toward camera; notes spawn −Z, hit line at Z=0. `K = SCALE/300 ≈ 0.0075`; nearly every world dimension is `N*K`. Helpers in scope inside `createFactory`: `fretX(f)`/`fretMid(f)`, lefty-aware `xFret(f)`/`xFretMid(f)`, `sY(s)`, `curX` (play head X), `FRET_WIDTH_MID`, `NFRETS` (24), `_leftyCached`, `T` (the THREE namespace), `scene`.
- **Supported note types** (feedpak spec, implemented in `lib/song.py`): hammer-on, pull-off, slide (pitched + unpitched), bend (+shape/curve), harmonic + pinch harmonic, palm mute, fret-hand mute, dead/ghost, vibrato, tremolo picking, accent, tap, pluck, slap, link-next; teaching marks (finger, strum group, scale degree). Authoritative spec: https://github.com/got-feedback/feedpak-spec
- **GP import** (`lib/gp2rs.py`, PyGuitarPro): most GP effects map cleanly. **Whammy bar (`tremoloBar`) has no native representation** — approximated as an unpitched slide. That gap is exactly what this feature ultimately addresses. Tapping/slapping/popping/trill are dropped on import.
- **Shading limitation:** no scene env map → metallic PBR = black. This is why the model uses the matte-translucent-emissive look instead. A proper env map (PMREM + a procedural RoomEnvironment, CSP-safe) is a possible future enhancement but changes a core rendering assumption — needs maintainer sign-off; out of scope for the first PR.
- **File-size sensitivity:** repo enforces max-lines with a signed exemption register (`docs/size-exemptions.md`). `highway_3d/screen.js` is already a ~15.7k-line monolith on the planned-split list; adding renderer code there is consistent, but the vendored JS (~140 KB) + 3 models (~840 KB) are notable additions for review.

---

## 8. Open items / next steps

1. **Fixed-mode "Position along neck" default** was never finalized (user was mid-tuning when the mode got temporarily cut, now restored at 0.5). Have the user tune it in "Always show" + fixed mode and bake the reported number as `whammyFixedPos` default.
2. **Wire the bend animation** when the real note type lands (see §6).
3. **Repoint the trigger** (`_whammyIsTriggerNote`) from harmonics to the real note type, and decide final gating.
4. **Temporary scaffolding to remove/finalize before PR** (all marked `TEMPORARY` in code): `whammyPreviewAlways`, the harmonic stand-in trigger, `whammy-bend-values.md`, this handoff.
5. **PR strategy:** this establishes a new convention (external glTF loading + vendored GLTFLoader in a plugin + model binaries). Recommend floating a short design note/issue to maintainers first; consider Draco-compressing the models; decide whether GLTFLoader belongs in core vs the plugin's vendor dir.
6. **Commit** (signed off) only when the user says so; `git add` the new asset + vendored files; PR to `got-feedback/feedBack` main from the fork.

## Gotchas
- Bump `plugin.json` version + deploy to BOTH installs + md5-verify, every time (see §4). A stale install is the #1 source of "my change did nothing."
- Screenshots the agent takes are **not visible to the user** — rely on their description of what they see.
- `curly quotes / °` appear in some settings.html strings — match exactly when editing.
