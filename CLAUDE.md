# Portfolio

## Projects

- `papa/`: **Papá o la papa**, a voice-to-watercolor phone prototype (say "Dad"
  in Spanish; "el papa", "la papa" and "papá" paint the Pope, a potato or Dad).
  Read `papa/CLAUDE.md` before changing it: it records the design decisions the
  user asked for and the directions they rejected.
  **Work on it now continues in its own repo, `humianchen0604-prog/languagelearning`**
  (the prototype at its root, with this folder's history). `papa/` here is a
  snapshot from when it moved; make new changes there, not here.
- `lava/icons/`: 20 liquid, acid-feeling memory icons for **Lava** (an app that
  stores memories). Monochrome, mixed filled/outline, each keeping a circle or
  star as "the memory". `generate.py` holds the recipes (signed distance fields
  joined with smooth unions/cuts) and writes `svg/*.svg` (one editable path each,
  `currentColor`) plus the gallery in `index.html`. Edit a recipe and rerun
  `python3 lava/icons/generate.py`; don't hand-edit the generated block.
  Two weights: Regular (`svg/`) and Bold (`svg/bold/`, heavier lines and no
  dot/hole too small for 32px); `svg/32/{regular,bold}/` are the same icons
  drawn natively at 32×32, which is what goes into Figma as components.
  Figma: https://www.figma.com/design/FZc3qGmrdKMPBMPINqeYmw ("Lava Memory
  Icons", Side Project drafts): 20 component sets `Lava/NN Name` with
  `Weight=Regular|Bold`, glyph fills bound to the `icon/ink` variable (Lava
  collection, Light/Dark modes).

- `lava/voice/`: 20 filled, liquid **voice-input (listening) icons** for Lava.
  `voice.js` holds the recipes as animated distance fields `make(t, a)` (t =
  time, a = 0 idle → 1 listening) plus the tracer the gallery uses each frame.
  `index.html` is the animated gallery (idle icons breathe in CSS; listening
  ones are retraced live), published at
  https://claude.ai/artifact/VT7rzoHvRgHDwN6sTTSnNG. `python3 lava/voice/export.py`
  writes the static `svg/` (100 units) and `svg/32/` at the shared `POSE`,
  reusing `lava/icons/generate.py`'s tracing and fitting, in three frames:
  `svg/` (still pose), `svg/idle/`, `svg/listening/` (each icon's loudest
  moment), each also under `svg/32/`. `VARIANTS` holds six linked takes on 04
  (ids 04a–04f), shown in the gallery's "04, linked" section.
  In Figma (same file, "Voice" page): the user's picks 04, 06, 14, 15, 20 as
  component sets `Voice/NN Name` with `State=Idle|Listening`, glyphs bound to
  `icon/ink`.

## Working here

- Prototypes are self-contained static pages (no build step). Serve the folder
  with `python3 -m http.server` to try it in a browser.
- Commit and push work as you go, so it's never only on one machine.
