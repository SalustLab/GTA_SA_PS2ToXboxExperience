# GTA San Andreas (Xbox) — PS2 Atmosphere v1.0

A patch for the original-Xbox *GTA: San Andreas* that brings back the look of the PS2 version. The Xbox advantages stay: DXT textures, longer draw distance, 480p and the Xbox car shader.

What changes:

- The PS2 colour filter: the warm orange or green grade from `timecyc.dat`, which the Xbox washes out.
- The soft PS2 blur on that filter.
- The PS2 radiosity glow on bright areas.
- PS2-style building lighting: stronger ambient light, softer baked light.
- PS2 alpha test on foliage, so palms, trees and power lines look full and continuous.
- A neutral display gamma at the default brightness.

Only the game's code (`default.xbe`) and five lines of `stream.ini` change. No game files are included.

## Requirements

- Your own copy of **GTA San Andreas, USA, Rev 1**. The script checks `default.xbe` against SHA1 `10EFB868F13D6944AA6684A52CAC5156393F14C5` and refuses anything else (other regions, Rev 0, or an already-modded file).
- A softmodded or modchipped Xbox, or the [xemu](https://xemu.app) emulator. The patched XBE is no longer retail-signed, so an unmodified console won't run it.
- [xdelta3](https://github.com/jmacd/xdelta-gpl/releases), or any xdelta GUI.
- For the automatic install: Python 3.

## Install (automatic)

1. Put `xdelta3.exe` in this folder, or pass its path with `--xdelta`.
2. Run the script on **either** of these:
   - A game folder, for example one copied from the Xbox hard drive over FTP. It must contain `default.xbe` and `stream.ini`. The originals are kept as `default.xbe.bak` and `stream.ini.bak`.

     ```
     py apply_patch.py "D:\Games\GTA San Andreas"
     ```

   - An Xbox image (`.iso` / `.xiso`), for example the one you load in xemu. It is patched in place after a full copy is saved as `<name>.iso.bak`, so you need as much free disk space as the image takes.

     ```
     py apply_patch.py "D:\xemu\GTA San Andreas (PS2 Atmosphere).iso"
     ```

The script checks both files before it writes anything, and checks the result after patching. An existing `.bak` is never overwritten. Running it again on a patched copy only reports `already patched`.

## Install (manual)

1. Apply `default.xbe.xdelta` to your original `default.xbe` with xdelta3 or an xdelta GUI:

   ```
   xdelta3 -d -s default.xbe default.xbe.xdelta default_patched.xbe
   ```

   Then replace `default.xbe` with `default_patched.xbe`. The result must have SHA1 `2D1829B5647F05930290D6E56425A4B656B8937B`.
2. Edit `stream.ini` in the game folder so that it contains these lines (separate each key from its value with tabs or spaces):

   ```
   pe_bRadiosity	1
   pe_leftx	8
   pe_topy	8
   pe_rightx	8
   pe_bottomy	8
   ```

   `pe_bRadiosity 1` turns the glow on. The four `pe_*` values (stock: `16`) set the blur strength.

## Recommended setting

Keep **Brightness** at its default. Saves store their own brightness, so reset it with the Display menu's restore-defaults option. The patch's neutral gamma is calibrated for the default; higher values only brighten the image.

## Uninstall

Delete the patched files and rename the `.bak` files back: `default.xbe.bak` → `default.xbe`, `stream.ini.bak` → `stream.ini`, or `<name>.iso.bak` → `<name>.iso`.

## Credits

The PS2 rendering behaviour follows aap's [SkyGfx](https://github.com/aap/skygfx) research and the [gta-reversed](https://github.com/gta-reversed/gta-reversed) project. The Xbox patches are original x86 code.
