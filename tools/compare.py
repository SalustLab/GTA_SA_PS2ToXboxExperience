"""Per-scene capture metrics (PLAN §16).

Usage:
  py tools/compare.py captures/<scene>      reference = ps2.png, every other *.png is a variant
  py tools/compare.py --selftest

Writes captures/<scene>/metrics.json (per-image stats + variant-minus-reference deltas +
per-channel histogram EMD) and _diff_<variant>.png (reference | variant | abs diff x4).
Files starting with "_" are ignored as inputs.
"""
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageChops

REFERENCE = "ps2.png"


def load(path):
    return np.asarray(Image.open(path).convert("RGB"), dtype=np.float64) / 255


def stats(img):
    r, g, b = img[..., 0], img[..., 1], img[..., 2]
    lum = 0.2126 * r + 0.7152 * g + 0.0722 * b
    mx, mn = img.max(-1), img.min(-1)
    sat = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1e-9), 0)
    lap = lum[:-2, 1:-1] + lum[2:, 1:-1] + lum[1:-1, :-2] + lum[1:-1, 2:] - 4 * lum[1:-1, 1:-1]
    p5, p50, p95 = np.percentile(lum, [5, 50, 95])
    return {
        "mean_rgb": [float(r.mean()), float(g.mean()), float(b.mean())],
        "rb_ratio": float(r.mean() / max(b.mean(), 1e-9)),
        "lum_mean": float(lum.mean()), "lum_p5": float(p5), "lum_p50": float(p50), "lum_p95": float(p95),
        "sat_mean": float(sat.mean()),
        "bloom_pct": float((lum > 0.9).mean() * 100),
        "laplacian_var": float(lap.var()),
    }


def hist_emd(a, b):
    """1-D EMD per channel over 256 bins, in units of levels/255."""
    out = []
    for ch in range(3):
        ha = np.histogram(a[..., ch], 256, (0, 1))[0] / a[..., ch].size
        hb = np.histogram(b[..., ch], 256, (0, 1))[0] / b[..., ch].size
        out.append(float(np.abs(np.cumsum(ha - hb)).sum() / 255))
    return out


def delta(v, ref):
    if isinstance(v, list):
        return [x - y for x, y in zip(v, ref)]
    return v - ref


def compare_scene(scene):
    scene = Path(scene)
    ref_img = load(scene / REFERENCE)
    ref = stats(ref_img)
    result = {REFERENCE: ref}
    for p in sorted(scene.glob("*.png")):
        if p.name == REFERENCE or p.name.startswith("_"):
            continue
        img = load(p)
        s = stats(img)
        s["delta_vs_ref"] = {k: delta(v, ref[k]) for k, v in s.items()}
        s["hist_emd_vs_ref"] = hist_emd(img, ref_img)
        result[p.name] = s
        a, b = Image.open(scene / REFERENCE).convert("RGB"), Image.open(p).convert("RGB")
        if a.size == b.size:
            diff = ImageChops.difference(a, b).point(lambda v: min(255, v * 4))
            sbs = Image.new("RGB", (a.width * 3, a.height))
            for i, im in enumerate((a, b, diff)):
                sbs.paste(im, (i * a.width, 0))
            sbs.save(scene / f"_diff_{p.stem}.png")
    (scene / "metrics.json").write_text(json.dumps(result, indent=2))
    return result


def selftest():
    import tempfile
    rng = np.random.default_rng(0)
    base = rng.uniform(0.1, 0.8, (64, 64, 3))
    with tempfile.TemporaryDirectory() as d:
        save = lambda name, a: Image.fromarray((np.clip(a, 0, 1) * 255).round().astype(np.uint8)).save(Path(d) / name)
        save(REFERENCE, base)
        save("same.png", base)
        save("warm.png", base * [1.3, 1.0, 0.7])
        blurred = (base + np.roll(base, 1, 0) + np.roll(base, 1, 1) + np.roll(base, (1, 1), (0, 1))) / 4
        save("blur.png", blurred)
        m = compare_scene(d)
        assert all(abs(x) < 1e-9 for x in m["same.png"]["hist_emd_vs_ref"])
        assert m["same.png"]["delta_vs_ref"]["rb_ratio"] == 0
        assert m["warm.png"]["delta_vs_ref"]["rb_ratio"] > 0.5
        assert m["warm.png"]["hist_emd_vs_ref"][2] > 0.05
        assert m["blur.png"]["laplacian_var"] < m[REFERENCE]["laplacian_var"] / 2
        assert (Path(d) / "_diff_warm.png").exists() and (Path(d) / "metrics.json").exists()
        assert "_diff_warm.png" not in m                   # outputs are not re-read as inputs
        m2 = compare_scene(d)
        assert set(m2) == set(m)
    print("compare selftest OK")


if __name__ == "__main__":
    args = sys.argv[1:]
    if args in ([], ["--selftest"]):
        selftest()
    elif len(args) == 1:
        print(json.dumps(compare_scene(args[0]), indent=2))
    else:
        raise SystemExit(__doc__)
