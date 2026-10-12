# GTA San Andreas (Xbox) — PS2 Atmosphere v1.1

A patch for the original-Xbox *GTA: San Andreas* that brings back the look of the PS2 version. The Xbox advantages stay: DXT textures, longer draw distance, 480p and the Xbox car shader.

What changes:

- The PS2 colour filter: the warm orange or green grade from `timecyc.dat`, which the Xbox washes out.
- The soft PS2 blur on that filter.
- The PS2 radiosity glow on bright areas.
- PS2-style building lighting: stronger ambient light, softer baked light.
- PS2 alpha test on foliage, so palms, trees and power lines look full and continuous.
- A neutral display gamma at the default brightness.

**One file changes: `default.xbe`.** Everything else, `stream.ini` included, stays as it is. No game files are included.

## Requirements

- Your own copy of **GTA San Andreas, USA, Rev 1**. The original `default.xbe` has SHA1 `10EFB868F13D6944AA6684A52CAC5156393F14C5`. Other regions, Rev 0 or an already-modded file won't patch.
- A softmodded or modchipped Xbox, or the [xemu](https://xemu.app) emulator. The patched XBE is no longer retail-signed, so an unmodified console won't run it.

## Install with any xdelta GUI (easiest)

1. Open your xdelta patcher (Delta Patcher, xdelta UI, or any other).
2. **Original file:** the game's `default.xbe`.
3. **Patch file:** `default.xbe.xdelta`.
4. Apply, then replace the game's `default.xbe` with the patched one. Keep the original somewhere safe.

Done. The patched file has SHA1 `84E14EEF41E0E83D7191A66973C99959815D7553`.

If your game is a folder (for example on the Xbox hard drive), copy `default.xbe` to your PC, patch it, and copy it back. If it's an ISO, use the script below, or extract the ISO to a folder first.

Command line equivalent:

```
xdelta3 -d -s default.xbe default.xbe.xdelta default_patched.xbe
```

## Install with the script (folders and ISO images)

Needs Python 3 and [`xdelta3.exe`](https://github.com/jmacd/xdelta-gpl/releases) in this folder (or pass `--xdelta <path>`).

```
py apply_patch.py "D:\Games\GTA San Andreas"
py apply_patch.py "D:\xemu\GTA San Andreas.iso"
```

- **A folder:** `default.xbe` is patched and the original is kept as `default.xbe.bak`.
- **An `.iso` / `.xiso`:** a full copy is saved as `<name>.iso.bak` first, so you need as much free space as the image takes. Then `default.xbe` is patched inside the image.

The script checks the file before it writes anything and checks the result afterwards. An existing `.bak` is never overwritten. Running it again only reports `already patched`.

## Coming from v1.0

Patch the **original** `default.xbe` again: restore it from `default.xbe.bak`, or from your original image. The `stream.ini` lines that v1.0 added can stay; they do no harm.

## Options

- **Turn the radiosity glow off:** add the line `pe_bRadiosity 0` to `stream.ini`.
- The blur is fixed at the PS2 value. The `pe_*` lines in `stream.ini` are ignored.

## Recommended setting

Keep **Brightness** at its default. Saves store their own brightness, so reset it with the Display menu's restore-defaults option. The patch's neutral gamma is calibrated for the default; higher values only brighten the image.

## Uninstall

Put the original `default.xbe` back: rename `default.xbe.bak` → `default.xbe`, or `<name>.iso.bak` → `<name>.iso`.

## Credits

The PS2 rendering behaviour follows aap's [SkyGfx](https://github.com/aap/skygfx) research and the [gta-reversed](https://github.com/gta-reversed/gta-reversed) project. The Xbox patches are original x86 code.
