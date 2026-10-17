# Memory temperature: notes for Claude

One-screen phone prototype for the **memories** tab of the agent chat app in
the user's Figma file `phZYZx5gmbFyf7JNS5Geve` ("Designing-Shits", page
"1st Round"). The question it explores: how hot is a saved memory? Some are
still heating, others are frozen in ice. How should the whole space show it?

The user asked for a clickable prototype that lets them compare four layouts.
It should use the vocabulary already in the Figma file: Heat band, Horizon
glow, Thermal word, Molten Mic, the Lava icon set and "Any bothers?".
The node they linked (`96:2146`) no longer exists, so the starting point is
the memories tab on the "Switch Agent" board (`25:2434`, the "my fav 3"
frames) with the ember look of `iPhone 17 - 9` (`94:4083`).

Everything lives in `index.html` (no build step).

## Run and check

```sh
cd memories && python3 -m http.server 8000
```
Open `http://localhost:8000`. Visual checks were done with Playwright
screenshots of `.stage`; there are no console errors.

## The model

- **Temperature = time since anyone revisited it** (the user's choice). You or
  an agent bringing a memory up re-heats it. `heat(m)` = 2^(−age / halfLife)
  with halfLife = 10 × (1 + 0.6 ln(1 + visits)) days. With one visit a memory
  freezes in about 6 weeks; with seven visits, about 10 weeks.
- Five states (`STAGES`), each named and described with a Lava icon's own
  Figma description: Molten ≥ .8 (06 Lava Lamp), Simmering ≥ .55 (16 Rising
  Bubbles), Cooling ≥ .3 (13 Eroded Orb), Frosting over ≥ .12 (05 Cell Orb),
  Frozen (15 Droplet Vault). Revisit uses 19 Spark Emerging. Degrees shown are
  playful: −18° frozen … 98° molten.
- `thermalVars(t)` turns heat into every visual cue as CSS custom properties:
  colour ramp `RAMP` (ice → Thermal-word blue `#2f5bff` → dusk → wine →
  Heat-band ember `#d4220c` → orange `#ff5a1f` → cream), corner radius (round
  liquid → ice-cube corners), size, glow, frost overlay, wobble speed.
- The whole space: `--heat` / `--frost` (mean temperature) dim the Heat band
  and Horizon glow and spread the frost band at the top.

## Layout (402 × 874 design, sizes in `--u`)

- Header y 58: More button, "Memories" with a heating · cooling · frozen
  count, time-lapse ▶ button (a year in ten seconds).
- View switcher y 114, a pill with four segments named after Lava icons:
  - **Lava Lamp**: thermal map. New memories are born at the Heat band and
    rise into frost as they cool. Frozen ones pack into an ice shelf at the
    top with no labels. The rest are placed hottest-first in the free spot
    nearest their heat line (`renderLamp`).
  - **Foam**: gradient cards (after the meditation and Watch references),
    grouped by state. Card height grows with heat.
  - **Orbit**: radial core (after the AI OS menu). The hottest memory is
    the core and its title is a Thermal word; the others drift out past the
    simmer, cooling and frost lines, and their warm bonds to the core fade.
  - **Chain**: strata like an ice core. Newest layers are thick and molten
    at the bottom; old ones are pressed thin and frozen at the top.
- Time scrub y 706: moves "now" forward up to a year (`toDay`, eased).
- Composer y 780 (Figma `94:4094`): typing or the mic adds a molten memory.
- Tapping a memory opens a sheet: big Thermal-word degrees, state, Lava
  description and Revisit (re-heats it).

## Assets

The Lava icons are inlined as `<symbol>`s. They are the Bold variants
exported from the Figma components `Lava/NN` (nodes `92:2603` + 5k) as SVG,
with the paths unchanged and the fill set to currentColor. Figma's asset URLs
are blocked from the cloud container, so the Horizon glow and Liquid warp
SVGs were not downloaded; the Horizon glow is a CSS radial gradient with
the frame's colours.
