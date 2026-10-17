#!/usr/bin/env python3
"""Static SVGs of the Lava Voice icons, one per icon at its still pose.

voice.js holds the recipes; Node samples each field exactly on the same grid the
memory icons use, and the tracing and Bézier fitting come from ../icons/generate.py.
Every SVG is one filled path (fill-rule evenodd, fill currentColor).

    python3 lava/voice/export.py     # writes svg/NN-name.svg and svg/32/NN-name.svg
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

DUMP = """
const fs = require('fs');
const V = require(process.argv[1]);
const out = process.argv[2];
V.ICONS.forEach((ic, i) => {
  const F = V.sample(ic.make(V.POSE.t, V.POSE.a), %d, true);
  fs.writeFileSync(`${out}/${i}.f64`, Buffer.from(F.buffer));
});
console.log(JSON.stringify(V.ICONS.map(ic => ({ name: ic.name, note: ic.note }))));
"""


def write(path, n, name, d, size):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {size} {size}" width="{size}" height="{size}">\n'
        f'  <title>Lava Voice {n:02d} · {name}</title>\n'
        f'  <path fill="currentColor" fill-rule="evenodd" d="{d}"/>\n'
        "</svg>\n")


def main():
    with tempfile.TemporaryDirectory() as tmp:
        meta = json.loads(subprocess.run(["node", "-e", DUMP % N, str(HERE / "voice.js"), tmp],
                                         check=True, capture_output=True, text=True).stdout)
        for i, m in enumerate(meta):
            field = np.fromfile(f"{tmp}/{i}.f64", dtype=np.float64).reshape(N + 1, N + 1)
            loops = gen.trace(field)
            pts = np.vstack(loops)
            shift = 50 - (pts.min(axis=0) + pts.max(axis=0)) / 2  # centre in the viewBox
            beziers = [gen.fit_loop(p + shift) for p in loops]
            n = i + 1
            slug = f"{n:02d}-" + re.sub(r"[^a-z0-9]+", "-", m["name"].lower()).strip("-")
            d = gen.to_path(beziers)
            write(HERE / "svg" / f"{slug}.svg", n, m["name"], d, 100)
            write(HERE / "svg" / "32" / f"{slug}.svg", n, m["name"], gen.to_path(beziers, 0.32), 32)
            print(f"{slug}: {d.count('C')} curves")


if __name__ == "__main__":
    main()
