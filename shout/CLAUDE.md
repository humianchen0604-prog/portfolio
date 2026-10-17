# Reply, shouted: notes for Claude

Three versions of the Figma "F3 · Reply" phone screen (file `phZYZx5gmbFyf7JNS5Geve`,
nodes `91:4878` "F3 · 4 Reply" and `91:4862` "F3 · 3 Reply, word by word") where
Die Hard's reply **shouts**: each word's weight, size or stretch, and how much
it blurs, comes from how loud it was said. The user asked for the character's line to shout (not their
own speech), emphasis from live mic loudness, on one gallery page.

There were ten; the user kept Swell, Poster and Drawl and dropped Sideways,
Quake, Slam, Heat, Thrown, Echo and In your face (see git history for them).

Everything is in `index.html` (no build step). Serve the folder (`start.command`,
or `python3 -m http.server`) and open it in Chrome or Safari for the mic.

## How it works

- `LINES`: the two Figma lines plus two more; each word carries a demo loudness 0..1.
- One voice drives all three phones at once, so they can be compared side by side:
  - **Demo voice** (default): words land on a timer with their scripted loudness.
  - **My mic**: RMS in dBFS, scaled between -58 dBFS and your own recent peak
    (floor -28), so emphasis is relative to how you talk. A word lands 200ms after
    a voice onset with the loudest moment of that window; 1.4s of quiet after the
    last word moves to the next line.
- A word's loudness is shaped (`^1.3`) into `--e` on its span; each version is CSS
  keyed on `figure[data-v]`, plus a `BEHAVIOUR` entry for what CSS can't do.
  `--live` (the current level) is on every screen (heat floor, mic button ring).
- Only words already said are on screen (by request: no faint placeholder of the
  rest of the sentence, unlike Figma's word-by-word frame). The text stays centred,
  so it grows outward from the middle as words arrive.
- Sizes are `calc(N * var(--u))`, `--u = 100cqw / 402`; tapping a phone opens it full size.

## The three

Swell (weight and size), Poster (loud words get their own full-width line),
Drawl (loud words stretch their vowels). Captions in `VARIANTS`.

## Type and looks

The reply is set in **Unbounded** (Google Fonts, 200–900), asked for as "more
acidic"; base size 30u since it runs wide. The page chrome stays Geist.

A **Look** switcher (header and full-size view, remembered in localStorage) sets
`body[data-look]`, from the user's four reference images. In every look,
**shouting melts it**: the louder the word, the more it blurs, glows or warps;
quiet words stay crisp. Each look also sets the screen background (by request):

- **Neon**: hot-pink glowing caps on a red room with brighter red edges.
- **Ghost**: white type with a halo, a sideways smear and a blurred reflection
  below (`::after` from `data-t`), on black grain; the only look with the heat floor.
- **Liquid**: black ink warped by per-phone SVG filters (`.melt`, four levels from
  `data-m`; `sizeMelt()` rescales them so the melt is the same at any phone size),
  pink bleed, on pink-cream scanlines.
- **Focus**: out-of-focus print with magenta/blue fringes on a pale haze.

Film grain is an SVG-noise overlay (`.grain`), strength per look.

## Assets

Figma's asset host is blocked from the cloud container, so the three avatars in
`assets/` are 1x node renders (32/44px); the heat floor, mic/end icons and the
"Die Hard" label are drawn in code. Swap in real exports if they look soft.

The published claude.ai artifact can't use the microphone, so there it only plays
the demo voice.
