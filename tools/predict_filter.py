"""Predict the colour-filter output (PLAN §6, §16) for a postfx-off frame.

Usage:
  py tools/predict_filter.py <raw.png> <out.png> r1 g1 b1 a1 r2 g2 b2 a2 [--xbox]
  py tools/predict_filter.py --selftest

c1/c2 are the in-memory PostFX values at 0x6C88B8 (0..255 scale, alpha already doubled
by the timecyc loader; timecyc.dat alpha 127 -> 254 here).

  PS2 : out = clip(fb*2c1) + clip(fb'*2c2) * a2      (a2/255 = PS2's 2*a2/255)
  Xbox: out = fb + fb*c1*a1 + fb*c2*a2               (stock Xbox formula)

Each colour is /255. fb' is taken equal to fb (no blur; P2 not modelled yet). The
per-pass clamp points are [H] (the H3 test).
"""
import sys

from PIL import Image


def _clip(v):
    return min(max(v, 0.0), 1.0)


def channel_out(fb, k1, k2, a1, a2, ps2=True):
    """fb, k1, k2, a1, a2 in 0..1; returns the output in 0..1."""
    if ps2:
        return _clip(_clip(fb * 2 * k1) + _clip(fb * 2 * k2) * a2)
    return _clip(fb + fb * k1 * a1 + fb * k2 * a2)


def predict(img, c1, c2, ps2=True):
    """Per-channel LUT; fb' == fb, so each output channel depends only on its own input."""
    a1, a2 = c1[3] / 255, c2[3] / 255
    lut = []
    for ch in range(3):
        k1, k2 = c1[ch] / 255, c2[ch] / 255
        lut += [round(255 * channel_out(v / 255, k1, k2, a1, a2, ps2)) for v in range(256)]
    return img.convert("RGB").point(lut)


def selftest():
    # LA 12:00 (PLAN §6): c1 66,66,48  c2 166,129,60  timecyc a 127 -> 254 in memory.
    c1, c2 = (66, 66, 48, 254), (166, 129, 60, 254)
    grey = Image.new("RGB", (4, 4), (100, 100, 100))
    for ps2, want in ((True, (1.81, 1.53, 0.85)), (False, (1.91, 1.76, 1.42))):
        got = predict(grey, c1, c2, ps2).getpixel((0, 0))
        for g, w in zip(got, want):
            assert abs(g / 100 - w) <= 0.015, (ps2, got, want)
    assert predict(Image.new("RGB", (1, 1), (200, 200, 200)), c1, c2).getpixel((0, 0))[0] == 255  # clamps
    assert predict(Image.new("RGB", (1, 1), (0, 0, 0)), c1, c2).getpixel((0, 0)) == (0, 0, 0)
    print("predict_filter selftest OK")


if __name__ == "__main__":
    args = sys.argv[1:]
    if args in ([], ["--selftest"]):
        selftest()
    else:
        ps2 = "--xbox" not in args
        args = [a for a in args if a != "--xbox"]
        if len(args) != 10:
            raise SystemExit(__doc__)
        c = [float(v) for v in args[2:]]
        predict(Image.open(args[0]), c[:4], c[4:], ps2).save(args[1])
