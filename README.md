# GTA SA Xbox — PS2 Atmosphere

A binary patch for the original-Xbox *GTA: San Andreas* (USA, Rev 1). It brings back the PS2 look: the orange colour filter, the soft blur and, still to come, the radiosity glow. It keeps what the Xbox version does better: DXT textures, longer LOD distances, 480p and the Xbox car shader.

`timecyc.dat` and the game assets are identical on both consoles. The difference lives in engine code, so every change is an in-place x86 or fixed-function D3D patch to `default.xbe`, plus a few `stream.ini` lines.

## Status

| Patch | What it does | State |
|---|---|---|
| P1 | ColourFilter with the PS2 formula; turns off the Xbox blur pass that washes out the filter | done (v0.1) |
| P5 | Neutral display gamma at brightness 256 | done |
| P2 | PS2 colour-filter blur (pass 2 sampled with LINEAR at +pe/16 texels); supersedes P1 | done (v0.2) |
| P3 | Radiosity rewrite | next |
| P4 | Building ambient ×2 | only if still needed |

The plan and roadmap are in [`docs/PLAN.md`](docs/PLAN.md). The dated lab log (RE results, addresses, experiment verdicts) is in [`docs/findings.md`](docs/findings.md).

## Requirements

- Your own dump of `default.xbe`, USA Rev 1, SHA1 `10EFB868F13D6944AA6684A52CAC5156393F14C5`. The tools refuse any other input.
- Python 3.13 with `capstone`, `pefile`, `pillow`, `numpy` and `keystone-engine`.
- For testing: xemu, with the GDB stub for live pokes, and PCSX2 with PINE for the PS2 reference.

No game data is included in this repository. Patch files check the original bytes by SHA1 and never store them.

## Usage

```sh
py patches/p2_filterblur.py                    # regenerate the patch JSON from work/xbox/default.xbe
py tools/xbe_patch.py work/xbox/default.xbe dist/default_p2p5.xbe \
   patches/p2_filterblur.json patches/p5_display_gamma.json
```

Then set these lines in `stream.ini`:

```
pe_leftx	8
pe_topy	8
pe_rightx	8
pe_bottomy	8
```

Apply P2 + P5. P2 already contains P1, and `xbe_patch.py` refuses P1 + P2. Each script has a self-check: `py <script> --selftest`.

## Layout

- `tools/`: the XBE patcher, filter predictor, capture metrics, and xemu/PCSX2 live-memory helpers.
- `patches/`: one generator script per patch (keystone assembly) and its JSON.
- `docs/`: the plan and the findings log.
- `xdvdfs_extract.py`: extracts files from an Xbox XDVDFS image.

## Credits

The PS2 rendering behaviour is based on aap's [SkyGfx](https://github.com/aap/skygfx) research and on the [gta-reversed](https://github.com/gta-reversed/gta-reversed) project.
