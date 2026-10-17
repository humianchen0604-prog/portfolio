# Memory temperature: notes for Claude

One-screen phone prototype for the **memories** tab of the agent chat app in
the user's Figma file `phZYZx5gmbFyf7JNS5Geve` ("Designing-Shits", page
"1st Round"). The question it explores: how hot is a saved memory? Some are
still heating, others are frozen in ice.

Everything lives in `index.html` (no build step).

## History

1. First version: four layouts (Lava Lamp thermal map, Foam cards, Orbit,
   Chain strata) with a time scrub. It's in git history (commit `174c52a`).
2. **Current version**, at the user's request: the layout of a meditation-app
   reference (Marii Kataeva) with the user's own visuals. That reference has
   a "Talk to me…" pill with an avatar, a menu button, tabs with superscript
   counts ("For You ⁶ Sleep ⁴ …") and a 2-column grid of soft gradient cards
   with a 3D glass object in each. The user asked to:
   - make the six cards Molten, Simmering, Cooling, Frosting over, Frozen
     and **Core memory** (one card per state, not one per memory);
   - make the tabs go from all memories to kinds of event: Interview,
     Family, Friends, Relationship, Money;
   - keep the memory ball icon at the top left;
   - fill the cards with the Lava icons, large;
   - keep the extras: the time bar, revisit (re-heat) and "Any bothers?".

## Run and check

```sh
cd memories && python3 -m http.server 8000
```
Open `http://localhost:8000`. Visual checks were done with Playwright
screenshots of `.stage`; there are no console errors.

## The model

- **Temperature = time since anyone revisited it** (the user's choice).
  `heat(m)` = 2^(−age / halfLife), halfLife = 10 × (1 + 0.6 ln(1 + visits))
  days. With one visit a memory freezes in about 6 weeks.
- States (`STAGES`): Molten ≥ .8 (06 Lava Lamp), Simmering ≥ .55 (16 Rising
  Bubbles), Cooling ≥ .3 (13 Eroded Orb), Frosting over ≥ .12 (05 Cell Orb),
  Frozen (15 Droplet Vault). Each one's description is the Lava icon's own
  Figma description. **Core memory** (`CORE`, 01 Kept Spark) is the memory
  with the most visits in the current tab (ties go to the warmer one); its
  card takes its colours from that memory's temperature.
- Degrees are playful: −18° frozen … 98° molten. The ramp `RAMP` runs ice →
  Thermal-word blue `#2f5bff` → dusk → wine → Heat-band ember `#d4220c` →
  orange `#ff5a1f` → cream.

## Layout (402 × 874 design, sizes in `--u`)

- Background pure black like the reference; a faint frost band at the top and
  Heat band at the bottom follow the mean temperature (`--heat`, `--frost`).
- y 66: pill (290 × 54) with the **memory ball** (red glossy sphere with
  the Lava/02 Bubble Foam glyph, after the Figma top-left ball in
  `iPhone 17 - 9`) and the "Any bothers?" input. Return adds a molten memory
  to the current tab. Tapping the ball goes back to All memories. Menu button
  54 at the right (no action).
- y 146: tabs, which scroll sideways and fade out at the right like the
  reference: All memories, Interview, Family, Friends, Relationship, Money,
  each with a superscript count. They filter the grid.
- y 198: 2 × 3 grid of 172u cards. Each card shows the name and
  "N memories · note", a 96u **glass Lava glyph** (Regular weight, filled
  with the `#glass` gradient, plus drop shadows), and dots for the count.
  Motion by state: molten melts quickly and beads rise off it, simmering
  melts more slowly, cooling drifts, frost and frozen stay still with a
  crystal hatch and sparkles, core floats. Empty states dim to 38%.
- Tapping a card opens a sheet: the state in Thermal-word glow, the Lava
  description, and the memories inside (temperature dot, kind · agent · when,
  degrees) each with a **re-heat** button (19 Spark Emerging). Re-heating
  sends the memory to Molten (its row slides out) and shows a toast.
- y 754: time bar: ▶ plays a year in ten seconds; the slider moves "now" up
  to a year (`toDay`, eased).

## Assets

The Lava icons are inlined as `<symbol>`s with their paths unchanged and the
fill set to currentColor. Bold (`lava-NN`, nodes `92:2603` + 5k) is used at
32px and below; Regular (`lava-NN-r`, nodes `92:2601` + 5k) is used for the
big card glyphs, following the Figma note "Regular from 48px up". Figma's
asset URLs are blocked from the cloud container, so the icons were exported
as SVG strings through `use_figma`, and the memory ball is drawn in CSS.
