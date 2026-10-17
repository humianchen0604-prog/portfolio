# Portfolio

## Projects

- `papa/`: **Papá o la papa**, a voice-to-watercolor phone prototype (say "Dad"
  in Spanish; "el papa", "la papa" and "papá" paint the Pope, a potato or Dad).
  Read `papa/CLAUDE.md` before changing it: it records the design decisions the
  user asked for and the directions they rejected.
  **Work on it now continues in its own repo, `humianchen0604-prog/languagelearning`**
  (the prototype at its root, with this folder's history). `papa/` here is a
  snapshot from when it moved; make new changes there, not here.
- `memories/`: **Memory temperature**, a phone prototype for the memories tab
  of the agent chat app. Saved memories cool from molten to frozen with time
  since they were last revisited, shown in four layouts with a time scrub.
  Read `memories/CLAUDE.md` before changing it.

## Working here

- Prototypes are self-contained static pages (no build step). Serve the folder
  with `python3 -m http.server` to try it in a browser.
- Commit and push work as you go, so it's never only on one machine.
