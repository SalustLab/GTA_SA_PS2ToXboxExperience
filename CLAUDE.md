# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A reverse-engineering project, not an app. The goal is a binary patch for the original-Xbox GTA San Andreas (USA Rev 1) that reproduces the PS2 "atmosphere": the orange colour filter, radiosity glow and soft blur. The patch keeps the Xbox advantages (DXT textures, longer LODs, 480p, the Xbox car shader).

**`docs/PLAN.md` is the source of truth.** It holds the approved plan: the findings, the differential map, the hypotheses H1–H5, the patches P1–P4, the experiments E0–E8 and the phased roadmap (§18, which tracks progress). **`docs/findings.md`** is the dated lab log: every RE result, live address and experiment verdict so far. Read both before any work.

Core finding: `timecyc.dat` and all assets are identical between the PS2 and Xbox versions. The visual difference is in **engine code** in `default.xbe`, plus a few `stream.ini` knobs. Xbox SA has no game pixel shaders, so every patch is to x86 code or fixed-function D3D state, applied in place in the XBE.

## Hard rules

- **Never modify the originals.** Both ISOs and the extracted folders are read-only: `Microsoft - Xbox/…(Rev 1)/` and `Sony - PlayStation 2/…(v3.00) (Rev 1)/`. Work only on copies under `work/`.
- The originals, `work/`, `captures/` and `dist/*.xbe` are gitignored (copyrighted and huge). Never commit Rockstar bytes. Committed patch JSONs guard original bytes with `orig_sha1` instead of `orig` for this reason. A distributed mod ships only an xdelta/BPS diff plus the ini lines to change (PLAN §15).
- The only supported target is `default.xbe` USA Rev 1, SHA1 `10EFB868F13D6944AA6684A52CAC5156393F14C5`. Tools must verify this hash and refuse any other input.
- Label claims with the evidence legend from PLAN.md:
  - **[C]** confirmed from bytes or source;
  - **[S]** strongly inferred;
  - **[H]** hypothesis that needs testing.

  Don't promote a claim to [C] without reading the bytes.

## Address conventions (Xbox)

Addresses are VAs in `default.xbe`. To get the file offset:
- `.text`: file offset = VA − `0x10000`
- `.data`: file offset = VA − `0xFB60`
- `.rdata`: file offset = VA − `0x10280`

`xbe_patch.py` maps VAs through the XBE section headers, so these deltas matter only for hand-reading bytes. Any `.data` VA ≥ `0x3D2C04` is BSS, and the `D3D` section's deferred-state area near `0x36BBF8` is partly BSS too. BSS is zero at boot and has no file bytes, so read it from a running emulator. The key anchors (ColourFilter `0x24F007`, Radiosity `0x24DF8E`, PostFX Render `0x24C537`, RW state ids, …) are listed in PLAN §9. Live RAM addresses (clock, weather, player, PostFX colours `0x6C88B8`, blur pass `0x24ECAA`, gamma ramp) are in findings.md, "RE target 6" and later entries.

PS2 init code (the stream.ini and timecyc parsers) lives in the overlay `INIT.NM`, not in the main `SLUS_209.46` ELF. PS2 live addresses are relative to `$gp` = `0x66B870`.

## Tools and commands

There is no build system, linter or test suite. Each script has an assert-based self-check, and `py <script> --selftest` must print `… selftest OK`. Run it after editing that script. Python is run with `py` (3.13). The available packages are capstone, pefile, PIL, numpy and keystone-engine.

| Script | Purpose |
|---|---|
| `xdvdfs_extract.py <iso> [outdir] [--list]` | Extracts an Xbox XDVDFS ISO; 7-Zip misreads the format. |
| `tools/xbe_patch.py <in.xbe> <out.xbe> <patch.json…>` | Applies patch JSONs. Refuses a wrong input SHA1, BSS targets, overlaps, and any original-byte mismatch. Also refuses to overwrite its input or to write into the originals. |
| `tools/predict_filter.py` | Expected PS2 or Xbox colour-filter output for a postfx-off frame plus c1/c2. |
| `tools/compare.py captures/<scene>` | PLAN §16 metrics. The reference is `ps2.png` and every other `*.png` is a variant. Writes `metrics.json` and `_diff_*.png`. Files starting with `_` are ignored as inputs. |
| `tools/xemu_gdb.py <cmd>` | Live Xbox pokes and captures through the xemu GDB stub (port 1234): `clock`, `weather`, `postfx`, `filter`, `teleport`, `timescale`, `capture`. Add `--cxbx` to target Cxbx-Reloaded. |
| `tools/pcsx2_pine.py <cmd>` | The same for PS2 through PCSX2 PINE (port 28011). |
| `tools/ps2_cheats.pnach` | Alternative PS2 clock and weather freeze. Install instructions are in its header. |

### Patch pipeline

1. Each patch is authored as a generator script, `patches/pN_*.py`. It holds keystone assembly, reads `work/xbox/default.xbe`, and writes `patches/pN_*.json` with `orig_sha1` guards. Example: `py patches/p1_colourfilter.py`.
2. Apply it: `py tools/xbe_patch.py work/xbox/default.xbe dist/default_pN.xbe patches/pN_*.json`.
3. Boot test: copy `work/xbox/gtasa_stock.xiso` and replace the embedded `default.xbe` in place. It sits at sector 348678, is 4018176 bytes, and keeps the same size. The Redump ISO doesn't boot in xemu. `gtasa_stock.xiso` is its game partition, from offset `0x18300000` to the end.
4. Before editing a patch, test it as a live RAM poke in xemu (E4 style).

## Captures and experiments

- Captures go to `captures/<scene>/<variant>.png`, with `ps2.png` as the reference. After each experiment, add a dated entry to `docs/findings.md`: hypothesis, prediction, result, and Confirmed or Refuted. Update the PLAN §18 status when a phase moves.
- **Gamma:** xemu applies the game's brightness gamma ramp at display, which can make captures `fb^0.843`. Read the active ramp (findings.md, "Residual k2 = display gamma") and linearize before any per-pixel comparison.
- The xemu menubar covers the top ~12 rows of captures, so mask rows < 14.
- Freeze the scene first: clock, weather, teleport and `timescale 0`.
- PS2 reference captures must use the software renderer, or Blending Accuracy = Maximum, at native 1×. Otherwise PS2 radiosity blending is emulated wrong.

## Environment

This is a local RE workstation. There is no database, web app or deploy target.
- PCSX2: `E:\Emuladores\PCSX2`, with PINE enabled.
- xemu 0.8.136: `E:\Emuladores\xemu`. Launch it with `xemu-gdb.bat` for the GDB stub. QEMU halts the guest while GDB is attached; `xemu_gdb.py` detaches after every command, which resumes it.
- Cxbx-Reloaded: `E:\Emuladores\Cxbx-Reloaded`.
- Ghidra 12.1.4: `F:\Tools\ghidra`.
- xdelta: `F:\Tools\xdelta`.
