# Reply, shouted: notes for Claude

Ten versions of the Figma "F3 · Reply" phone screen (file `phZYZx5gmbFyf7JNS5Geve`,
nodes `91:4878` "F3 · 4 Reply" and `91:4862` "F3 · 3 Reply, word by word") where
Die Hard's reply **shouts**: each word's weight, size, angle, heat etc. comes from
how loud it was said. The user asked for the character's line to shout (not their
own speech), emphasis from live mic loudness, all ten on one gallery page.

Everything is in `index.html` (no build step). Serve the folder (`start.command`,
or `python3 -m http.server`) and open it in Chrome or Safari for the mic.

## How it works

- `LINES`: the two Figma lines plus two more; each word carries a demo loudness 0..1.
- One voice drives all ten phones at once, so they can be compared side by side:
  - **Demo voice** (default): words land on a timer with their scripted loudness.
  - **My mic**: RMS in dBFS, scaled between -58 dBFS and your own recent peak
    (floor -28), so emphasis is relative to how you talk. A word lands 200ms after
    a voice onset with the loudest moment of that window; 1.4s of quiet after the
    last word moves to the next line.
- A word's loudness is shaped (`^1.3`) into `--e` on its span; each version is CSS
  keyed on `figure[data-v]`, plus a `BEHAVIOUR` entry for what CSS can't do.
  `--live` (the current level) is on every screen for effects that follow the voice
  as it happens (heat floor, quake, echo, mic button ring).
- Words not yet said show at 18% like Figma's word-by-word frame.
- Sizes are `calc(N * var(--u))`, `--u = 100cqw / 402`; tapping a phone opens it full size.

## The ten

Swell, Sideways, Poster, Quake, Slam, Heat, Drawl, Thrown, Echo, In your face
(captions in `VARIANTS`).

## Assets

Figma's asset host is blocked from the cloud container, so the three avatars in
`assets/` are 1x node renders (32/44px); the heat floor, mic/end icons and the
"Die Hard" label are drawn in code. Swap in real exports if they look soft.

The published claude.ai artifact can't use the microphone, so there it only plays
the demo voice.
