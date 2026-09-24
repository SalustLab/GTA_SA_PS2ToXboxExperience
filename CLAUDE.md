# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A reverse-engineering project, not an app. The goal is a binary patch for the original-Xbox GTA San Andreas (USA Rev 1) that reproduces the PS2 "atmosphere": the orange colour filter, radiosity glow and soft blur. The patch keeps the Xbox advantages (DXT textures, longer LODs, 480p, the Xbox car shader).

**`docs/PLAN.md` is the source of truth.** It holds the approved plan: the findings, the differential map, the hypotheses H1–H5, the patches P1–P4, the experiments E0–E8 and the phased roadmap. Read it before any work. Work starts at Phase 0 (§18).

Core finding: `timecyc.dat` and all assets are identical between the PS2 and Xbox versions. The visual difference is in **engine code** in `default.xbe`, plus a few `stream.ini` knobs. Xbox SA has no game pixel shaders, so every patch is to x86 code or fixed-function D3D state, applied in place in the XBE.

## Hard rules

- **Never modify the originals.** Both ISOs and the extracted folders are read-only: `Microsoft - Xbox/…(Rev 1)/` and `Sony - PlayStation 2/…(v3.00) (Rev 1)/`. Work only on copies under `work/`.
- The originals, `work/`, `captures/` and `dist/*.xbe` are gitignored (copyrighted and huge). Never commit Rockstar bytes. A distributed mod ships only an xdelta/BPS diff plus the ini lines to change (PLAN §15).
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

Any `.data` VA ≥ `0x3D2C04` is BSS: it is zero at boot and has no file bytes, so read it from a running emulator. The key anchors (ColourFilter `0x24F007`, Radiosity `0x24DF8E`, PostFX Render `0x24C537`, RW state ids, …) are listed in PLAN §9.

PS2 init code (the stream.ini and timecyc parsers) lives in the overlay `INIT.NM`, not in the main `SLUS_209.46` ELF.

## Layout and planned tooling

- `xdvdfs_extract.py` is the only existing tool. It extracts an original-Xbox XDVDFS ISO; 7-Zip misreads the format. Commands:
  - extract: `py xdvdfs_extract.py <image.iso> [outdir]`
  - list the contents: add `--list`

  It ends with an assert-based self-check.
- `tools/`, `patches/`, `work/`, `captures/` are empty scaffolds. Phase 0 adds the following to `tools/` (spec in PLAN §12):
  - `xbe_patch.py`: applies `patches/*.json`. Each entry holds a VA, the original bytes and the new bytes. The tool **refuses on an original-byte mismatch**.
  - `predict_filter.py`: carries an assert self-check using the LA 12:00 gains from PLAN §6.
  - `compare.py`: computes the capture metrics from PLAN §16.
- Captures go to `captures/<scene>/<variant>.png` alongside a `metrics.json`. After each experiment, add a note to `docs/findings.md`: hypothesis, prediction, result, and Confirmed or Refuted.
- There is no build system, linter or test suite. The checks are each script's `__main__` self-check. Python is run with `py`, and the available packages are capstone, pefile and PIL; numpy and keystone are still to be installed.

## Environment

- PCSX2: `E:\Emuladores\PCSX2`.
- Reference captures must use the software renderer, or Blending Accuracy = Maximum, at native 1×. Otherwise PS2 radiosity blending is emulated wrong.
- xemu (with the GDB stub `-s`) and Ghidra are needed but not yet installed.
- There is no database, web app or deploy target.
