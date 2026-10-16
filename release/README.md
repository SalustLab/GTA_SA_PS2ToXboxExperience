# GTA San Andreas (Xbox) — PS2 Atmosphere v1.2

New in v1.2: support for USA **Rev 0** (the first release). The patch itself is unchanged from v1.1; Rev 1 users who already have v1.1 don't need to do anything.

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

- Your own copy of **GTA San Andreas, USA**, either revision:
  - **Rev 1**: the original `default.xbe` has SHA1 `10EFB868F13D6944AA6684A52CAC5156393F14C5`.
  - **Rev 0** (the first release): SHA1 `1CEAE5BE753B3675CE8C5C79D7F496DFC0AD597D`.

  Other regions or an already-modded file won't patch.
- A softmodded or modchipped Xbox, or the [xemu](https://xemu.app) emulator. The patched XBE is no longer retail-signed, so an unmodified console won't run it.

## Install with any xdelta GUI (easiest)

Pick the patch that matches the file you have:

The patches are in two folders, `GTA SA (USA) Rev 1` and `GTA SA (USA) Rev 0`, with the same three files in each:

| Your file | Patch (in `GTA SA (USA) Rev 1/` or `GTA SA (USA) Rev 0/`) |
|---|---|
| `default.xbe` from a game folder (for example on the Xbox hard drive) | `default.xbe.xdelta` |
| Full game ISO, 7,825,162,240 bytes: `Grand Theft Auto - San Andreas (USA) (En,Es) (Rev 1).iso`, or `Grand Theft Auto - San Andreas (USA) (En,Es).iso` for Rev 0 | `iso.xdelta` |
| XISO of the game partition (the full ISO minus its video partition), 7,419,363,328 bytes | `xiso.xdelta` |

The ISO patches are made for the Redump dumps of the game. The Rev 0 one was tested on the Rev 0 Redump image; the Rev 1 one on an image with the same layout.

A patch for the other revision is rejected with *"checksum mismatch"*, so trying the wrong folder does no harm.

1. Open your xdelta patcher (Delta Patcher, xdelta UI, or any other). For `default.xbe` a web patcher such as [Rom Patcher JS](https://www.marcrobledo.com/RomPatcher.js/) also works; the ISOs are too big for a browser.
2. **Original file:** your file. **Patch file:** the matching `.xdelta`.
3. Apply. Keep the original somewhere safe.

If you patched `default.xbe`, put the patched file back in the game folder. The patched XBE has SHA1 `84E14EEF41E0E83D7191A66973C99959815D7553` (Rev 1) or `6883102C897EAA58E8E01FB41A51B9C4B44B481D` (Rev 0).

A patched full ISO keeps its format. Convert it the way you usually do (Repackinator, extract-xiso, ...); xemu doesn't boot the full ISO directly, but it boots the patched XISO as is.

The wrong file is rejected with *"checksum mismatch"*. An ISO that was rebuilt or trimmed (for example by extract-xiso or Repackinator) has a different layout, so the ISO patches won't fit it. For those, use the script below, or extract the ISO and patch `default.xbe`.

Command line equivalent:

```
xdelta3 -d -s default.xbe "GTA SA (USA) Rev 1/default.xbe.xdelta" default_patched.xbe    # or "GTA SA (USA) Rev 0/..."
```

## Install with the script (folders and ISO images)

Needs Python 3 and [`xdelta3.exe`](https://github.com/jmacd/xdelta-gpl/releases) in this folder (or pass `--xdelta <path>`).

```
py apply_patch.py "D:\Games\GTA San Andreas"
py apply_patch.py "D:\xemu\GTA San Andreas.iso"
```

- **A folder:** `default.xbe` is patched and the original is kept as `default.xbe.bak`.
- **An `.iso` / `.xiso`:** a full copy is saved as `<name>.iso.bak` first, so you need as much free space as the image takes. Then `default.xbe` is patched inside the image.

The script tells Rev 1 and Rev 0 apart by the SHA1 of `default.xbe` and uses the matching patch. It checks the file before it writes anything and checks the result afterwards. An existing `.bak` is never overwritten. Running it again only reports `already patched`.

## Coming from v1.0 or v1.1

v1.1 → v1.2: nothing to do on Rev 1, the patched file is the same.

From v1.0: patch the **original** `default.xbe` again: restore it from `default.xbe.bak`, or from your original image. The `stream.ini` lines that v1.0 added can stay; they do no harm.

## Options

- **Turn the radiosity glow off:** add the line `pe_bRadiosity 0` to `stream.ini`.
- The blur is fixed at the PS2 value. The `pe_*` lines in `stream.ini` are ignored.

## Recommended setting

Keep **Brightness** at its default. Saves store their own brightness, so reset it with the Display menu's restore-defaults option. The patch's neutral gamma is calibrated for the default; higher values only brighten the image.

## Uninstall

Put the original `default.xbe` back: rename `default.xbe.bak` → `default.xbe`, or `<name>.iso.bak` → `<name>.iso`.

## Credits

The PS2 rendering behaviour follows aap's [SkyGfx](https://github.com/aap/skygfx) research and the [gta-reversed](https://github.com/gta-reversed/gta-reversed) project. The Xbox patches are original x86 code.
