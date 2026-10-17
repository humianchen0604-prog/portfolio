#!/usr/bin/env python3
"""Static SVGs of the Lava Voice icons (the 20 icons and the linked 04 variants).

voice.js holds the recipes; Node samples each field exactly on the same grid the
memory icons use, and the tracing and Bézier fitting come from ../icons/generate.py.
Every SVG is one filled path (fill-rule evenodd, fill currentColor). Each icon
is written in three frames:

    svg/            the still pose shown in the gallery (POSE)
    svg/idle/       resting, not listening
    svg/listening/  its loudest moment while listening

and each again at 32x32 under svg/32/.

    python3 lava/voice/export.py
"""
import importlib.util
import json
import pathlib
import re
import subprocess
import tempfile

import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("generate", HERE.parent / "icons" / "generate.py")
gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)
N = round(gen.SIZE / gen.STEP)  # 800 cells, 801 samples a side

NODE = """
const fs = require('fs');
const V = require(process.argv[1]);
const entries = [...V.ICONS.map((ic, i) => ({ ...ic, id: String(i + 1).padStart(2, '0') })), ...V.VARIANTS];
const [, , cmd, which, out] = process.argv;
const IDLE = { t: V.POSE.t, a: 0 };
// The listening frame where the icon fills the most area, within its first 8 seconds.
function loudest(e) {
  let best = -1, at = 1;
  for (let t = 0.5; t < 8; t += 0.05) {
    let n = 0;
    for (const v of V.sample(e.make(t, 1), 50, true)) if (v < 0) n++;
    if (n > best) { best = n; at = t; }
  }
  return { t: +at.toFixed(2), a: 1 };
}
if (cmd === 'list') {
  console.log(JSON.stringify(entries.map(e => ({ id: e.id, name: e.name, frames: { pose: V.POSE, idle: IDLE, listening: loudest(e) } }))));
} else {
  const e = entries.find(x => x.id === which), frames = JSON.parse(out);
  for (const [k, f] of Object.entries(frames)) {
    const F = new Float32Array(V.sample(e.make(f.t, f.a), %d, true));
    fs.writeFileSync(`${f.file}`, Buffer.from(F.buffer));
  }
}
"""

FOLDERS = {"pose": "", "idle": "idle/", "listening": "listening/"}


def write(path, title, d, size):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {size} {size}" width="{size}" height="{size}">\n'
        f'  <title>{title}</title>\n'
        f'  <path fill="currentColor" fill-rule="evenodd" d="{d}"/>\n'
        "</svg>\n")


def node(*args):
    return subprocess.run(["node", "-e", NODE % N, str(HERE / "voice.js"), *args],
                          check=True, capture_output=True, text=True).stdout


def main():
    entries = json.loads(node("list"))
    with tempfile.TemporaryDirectory() as tmp:
        for e in entries:
            frames = {k: {**f, "file": f"{tmp}/{k}.f32"} for k, f in e["frames"].items()}
            node("dump", e["id"], json.dumps(frames))
            slug = f"{e['id']}-" + re.sub(r"[^a-z0-9]+", "-", e["name"].lower()).strip("-")
            for k, f in frames.items():
                field = np.fromfile(f["file"], dtype=np.float32).astype(np.float64).reshape(N + 1, N + 1)
                loops = gen.trace(field)
                pts = np.vstack(loops)
                shift = 50 - (pts.min(axis=0) + pts.max(axis=0)) / 2  # centre in the viewBox
                beziers = [gen.fit_loop(p + shift) for p in loops]
                title = f"Lava Voice {e['id']} · {e['name']}" + ("" if k == "pose" else f" · {k}")
                write(HERE / "svg" / FOLDERS[k] / f"{slug}.svg", title, gen.to_path(beziers), 100)
                write(HERE / "svg" / "32" / FOLDERS[k] / f"{slug}.svg", title, gen.to_path(beziers, 0.32), 32)
            print(f"{slug}: listening at t={e['frames']['listening']['t']}")


if __name__ == "__main__":
    main()
