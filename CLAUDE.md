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

## Working here

- Prototypes are self-contained static pages (no build step). Serve the folder
  with `python3 -m http.server` to try it in a browser.
- Commit and push work as you go, so it's never only on one machine.
