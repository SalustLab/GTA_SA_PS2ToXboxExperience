# Findings log

One entry per experiment / RE target: hypothesis, prediction, result, Confirmed/Refuted. Evidence legend as in PLAN.md.

## 2026-09-23 — Phase 0: workspace and tools

- `work/xbox/default.xbe` and `work/xbox/stream.ini` are copies of the originals; SHA1 match (`10efb868…` / `67732726…`) [C].
- XBE section table [C]: `.text` VA 0x11000 raw 0x1000 (Δ0x10000); `.rdata` Δ0x10280; `.data` Δ0xFB60, raw ends at VA 0x3D2C04 (BSS above); `D3D` VA 0x35AD80 Δ0xDD80 (raw 0x10B44 < vsize 0x14418, so the deferred-state area near 0x36BBF8 is partly BSS). `xbe_patch.py` maps VAs through this table.
- `0x24F007` begins `55 8B EC 53 56 33 DB 57 43 53 6A 09 FF 15 80 DE 75 00` = prologue + `RwRenderStateSet(9 filter, 1 nearest)` — consistent with PLAN §9 ColourFilter [C].
- Installed: xemu 0.8.136 (`E:\Emuladores\xemu`), Ghidra 12.1.4 (`F:\Tools\ghidra`, JDK 21), numpy, keystone-engine, capstone (was missing on py 3.13). xdelta already at `F:\Tools\xdelta`.
- Tools: `tools/xbe_patch.py`, `tools/predict_filter.py`, `tools/compare.py`, `tools/xemu_gdb.py`, each with an assert self-check (`--selftest`, all pass; `xemu_gdb` against a fake RSP stub, not yet a live xemu). `predict_filter` reproduces the PLAN §6 LA 12:00 gains for both formulas using in-memory alpha 254 (timecyc 127 ×2) [C].

## 2026-09-23 — RE target 6: clock / weather / player (static)

### Xbox (`default.xbe` Rev 1)

| Item | Address | Evidence |
|---|---|---|
| CClock::Initialise(eax = ms/minute) | 0xEBBA6 (sets 12:00, day 1, month 1, weekday 4) | [C] |
| CClock::SetGameClock(h, m, day) | 0xEBBE4 | [C] |
| CClock::Update | 0xEBD11 | [C] |
| ms_nGameClockHours (byte) | 0x55F3DF | [C] |
| ms_nGameClockMinutes (byte) | 0x55F3DE | [C] |
| ms_nGameClockSeconds (word) | 0x55F3DC | [C] |
| day / month / weekday (bytes) | 0x55F3E0 / 0x55F3E1 / 0x55F3DA | [C] |
| ms_nLastClockTick / ms_nMillisecondsPerGameMinute | 0x55F3E4 / 0x55F3E8 (signed compare; also written at 0x163D4C) | [C] |
| CTimer::m_snTimeInMilliseconds | 0x56B9CC | [C] |
| CCheat active flags read by Update | 0x45660B (faster clock), 0x456637, 0x456638 (clock-stop cheats) | [S] names |
| CWeather::Update | 0x26025D | [C] |
| OldWeatherType / NewWeatherType / ForcedWeatherType (short) | 0x5E62FC / 0x5E62F8 / 0x5E62F4 | [C] (Update: Old=New; New = Forced≥0 ? Forced : list[(idx+1)%64]) |
| WeatherTypeInList / InterpolationValue | 0x5E62EC / 0x5E62E8 | [C] |
| Weather cheat handlers (Old=New=Forced=k) | 0x39D9D… | [C] |
| CWorld::Players (stride 0x190) / PlayerInFocus (byte) | 0x6C8F18 / 0x56BC54 | [C] (FindPlayerPed 0x102F07) |
| FindPlayerEntity / FindPlayerCoors | 0x102EA0 / 0x102F37 | [C] |
| CPed: bInVehicle bit / m_pVehicle / heading | +0x46D bit0 / +0x58C / +0x558, +0x55C (current, aiming) | [C] (heading live: −1.71 / 4.57 = same angle mod 2π) |
| Entity position | `[ent+0x14]` matrix → +0x30 (x,y,z floats); else `ent+4` | [C] |
| TheCamera placement / m_matrix | 0x6C44D4 / 0x6C44E4 | [S] |

### PS2 (`SLUS_209.46` v3.00; `$gp` = 0x66B870, set in crt0 at 0x100198)

| Item | Address | Evidence |
|---|---|---|
| CClock::SetGameClock | 0x22CD60 | [C] |
| CClock::Update | 0x22CF30 | [C] |
| hours / minutes (bytes), seconds (short) | 0x66BF2C / 0x66BF30 / 0x66BF34 | [C] |
| day / month / weekday | 0x66BF28 / 0x66BF24 / 0x66BF38 | [C] |
| LastClockTick / ms per minute | 0x66BF20 / 0x66BF1C | [C] |
| CTimer::m_snTimeInMilliseconds | 0x66C194 | [C] |
| CCheat flags read by Update | 0x88E28B, 0x88E2B7, 0x88E2B8 (same 0x2C spacing as Xbox) | [S] names |
| CWeather::ForceWeather / ForceWeatherNow / ReleaseWeather | 0x2BDF50 / 0x2BDF60 / 0x2BDFC0 | [C] |
| Old / New / Forced weather (short) | 0x66C4A4 / 0x66C4A8 / 0x66C4AC | [C] (Update shift at 0x2BC6CC) |
| WeatherTypeInList / InterpolationValue | 0x66C4B4 / 0x66C4B8 | [C] / [S] |
| CWorld::Players (stride 0x1BC) / PlayerInFocus | 0x70A160 / 0x66C1F4 | [C] |
| CPed: bInVehicle bit / m_pVehicle | +0x4A5 bit0 / +0x5CC | [C] |
| CPed heading | unknown — PS2 CPed offsets are not a constant shift of Xbox (0x38 vs 0x40) | [H] |
| Entity position | `[ent+0x14]` matrix → +0x30, same as Xbox | [C] |
| TheCamera placement / m_matrix | 0x6FF094 / 0x6FF0A4 | [S] |

### Consequences for the harness (E0)

- Clock freeze: continuously write hours/minutes/seconds (pnach place 1), or set ms-per-minute to 0x7FFFFFFF (signed compare → never ticks). On Xbox re-poke 0x55F3E8, since 0x163D4C also writes it.
- Weather freeze: write the same id to Old/New/Forced; with Forced ≥ 0 Update keeps New = Forced.
- `tools/ps2_cheats.pnach` implements clock + weather groups for the §16 scenes; installed as `PCSX2\cheats\SLUS-20946_2C6BE434.pnach`. CRC = XOR of all ELF words [C] (method reproduces PCSX2's logged `2F56CBC9` for Klonoa 2 SLUS_201.51).
- xemu: portable `E:\Emuladores\xemu\xemu.toml` points at the BIOS files, the official copyright-free `xbox_hdd.qcow2` (xemu-project/xemu-hdd-image) and the original Xbox ISO (read-only DVD). Teleport (pointer chase to the ped matrix) and PS2 heading are still open.
- Weather ids are taken from gta-reversed `eWeatherType` [S]; the code's special-cases (0x10, 0x13, and the 0/0xB/0x11/0x12 group) are consistent with it.

## 2026-09-24 — E0: xemu live validation

- The Redump ISO (video partition first) shows "insert an Xbox disc" in xemu. Fix: `work/xbox/gtasa_stock.xiso` = original ISO bytes from 0x18300000 to the end (game partition). The embedded `default.xbe` (sector 348678, 4018176 B) hashes to Rev 1 [C]. Patched builds = copy of this XISO with the XBE bytes replaced in place.
- xemu 0.8.136 `-s` boots it; `tools/xemu_gdb.py` works live [C]:
  - clock 0x55F3DF/0x55F3DE ticks (8:00 → 8:02); `clock 12 0` holds 12:00:00 after 10 s (ms-per-minute 0x7FFFFFFF freeze works);
  - `weather 1` holds Old/New/Forced = 1 (was 14/14/14 at boot);
  - Players[0].m_pPed = 0xEB71A0, matrix pos (2489.3, −1667.0, 13.3) = Grove Street;
  - PostFX floats at 0x6C88B8 have alpha 254 = timecyc 127 ×2 (loader doubling confirmed live); radiosity flag 0x5F4B1C = 0, postfx disable 0x5F4B1F = 0.

## 2026-09-24 — E0/E4 prep: deterministic check of the stock Xbox ColourFilter (Grove St, 12:00, SUNNY_LA)

- **Hypothesis (PLAN §5/§9):** stock Xbox output = `fb·(1 + c1·a1 + c2·a2)`, with a = vertex alpha and framebuffer-copy alpha = 1.0 (H3).
- **Setup:** world frozen via `CTimer::ms_fTimeScale` 0x56B9AC = 0 (4.0% → 0.86% changing px). Real ColourFilter args read by breakpoint at 0x24CAF5: c1 = (70,121,120, a240), c2 = (160,88,21, a254) = the 0x6C88B8 floats (lighting mult ≈ 1 at noon) [C]. Live RAM-only code patches (XBE on disk untouched): NOP `call ColourFilter` (raw frame); alpha of pass 1 or pass 2 forced to 0 (`movzx eax,[ebp+0xb|0xf]` → `xor eax,eax`).
- **Code [C]:** ColourFilter sets filter NEAREST, fog/ztest/zwrite off, raster = fb copy 0x5F4B28, vtxalpha on, SRC = SRCALPHA, DST = ONE, then draws two Im2D quads with vertex colour c1, then c2 (ARGB packed from the arg bytes, R at byte 0).
- **Result:** gain vs raw is spatially constant (road/wall/ground agree; IQR ≤ 0.03 on R/G). Per pass:
  - pass 2 alone: α2 = 0.585 / 0.587 / 0.592 (R/G/B), vertex a2 = 0.996;
  - pass 1 alone: α1 = 0.552 / 0.552 / 0.531, vertex a1 = 0.941;
  - both: gain 1.517 / 1.462 / 1.296 (PLAN's formula predicted 1.883 / 1.790 / 1.525).
  - The model `fb·(1 + Σ c·α)` holds (α is consistent across channels), but **α ≈ 0.58–0.59 × vertex alpha**, i.e. the effective framebuffer-copy alpha is a constant ≈ 0.585 (≈149/255), not 1.0.
- **Verdict:** H3 **Refuted** as stated (fb alpha ≠ 1). Stock Xbox formula corrected to `fb + fb·c1·(a1·k) + fb·c2·(a2·k)`, k ≈ 0.585 [C for this scene]. The origin of k (backbuffer alpha content vs. xemu NV2A behaviour) is open [H]; it matters for P1, since `ALPHAOP=MODULATE` would inherit it.
- **Also:** the PostFX disable-all byte 0x5F4B1F changes 19% of pixels vs NOP-ing only the ColourFilter call, so it is **not** a clean "raw" frame. E3/E4 must use the call-NOP raw frame.

## 2026-09-24 — E3: offline filter transplant (LS street by the tracks, (2277.4, −1254.4, 24.0), 12:00, SUNNY_LA)

- **Hypothesis H1:** the colour-filter formula explains most of the PS2/Xbox colour gap. *Prediction:* the PS2 formula applied to a raw Xbox frame lands near the PS2 capture; stock Xbox stays far.
- **Setup:** both emulators frozen (timeScale 0; PS2 timeScale = 0x66C1A8 = 0x938($gp) [C, live]). Same clock/weather/position via `xemu_gdb.py` / `pcsx2_pine.py` (PS2 heading +0x598/+0x59C written; PS2 CJ drifted 3.6 m before capture). PCSX2 software renderer 1× (per-game ini). Xbox raw = ColourFilter call NOP'd in RAM. PS2 formula applied with the real call-site args c1 (70,121,120,a240), c2 (160,88,21,a254) → `xbox_raw_ps2formula.png`. Files in `captures/ls_2277_noon/`.
- **Result (matched regions, CIE76 ΔE vs PS2):**

| Region | PS2 RGB | Xbox stock | Xbox raw + PS2 formula | ΔE stock | ΔE PS2-formula |
|---|---|---|---|---|---|
| ground left of CJ | 141 118 61 | 121 108 74 | 143 121 63 | 14.5 | **1.1** |
| railway | 108 92 45 | 103 96 73 | 122 107 62 | 14.9 | **6.4** |
| sky (hue-classified) | 64 229 238 | 67 190 229 | 80 218 233 | — | G gap 39 → 11 |

  Global stats are skewed by framing (a parked car on PS2, xemu menubar in the top 12 rows, no Xbox HUD): saturation PS2 0.615 / stock 0.460 / PS2-formula 0.549; R/B 0.82 / 0.75 / 0.97.
- **Verdict:** H1 **Confirmed** (visually and on the matched ground/rail patches). Residual: the PS2-formula frame is a little too red in the sky (R 80 vs 64) and the PS2 has darker shadows (lum p5 0.087 vs 0.154). Candidates: radiosity (not modelled), the per-pass clamp points, or c1 on PS2 differing from the Xbox call-site value [H].
- **Harness notes:** set `display.ui.show_menubar = false` in xemu.toml (the menubar appears in captures on mouse-over); give the PS2 camera time to settle before freezing.

## 2026-09-24 — RE targets 1–2 + diagnosis of the k ≈ 0.585 filter factor

**RE target 1 — fb copy `0x24BB7B` [C]:** not CopyRects. It ends the scene camera `[0x5B8528]`, begins the postfx camera `[0x5F4B30]` (its raster is the copy `[0x5F4B28]`), draws the Im2D quad at 0x5C72A8 (0..640 × 0..480, vertex colour FFFFFFFF, texel-space UVs 0.5..640.5 = linear texture) textured with the screen raster `[0x5F4B2C]` (vtxalpha 0, ztest/zwrite/fog off, address CLAMP, cull none), then restores the scene camera.
- Copy raster: RwRaster 1024×512×32; D3D texture at plugin +0x34 → `D3DPixelContainer` {Common 0x000C0001, Data phys, Format 0x09A10729 = fmt 0x07 **X8R8G8B8 swizzled**}. Screen raster: 640×480×32, surface 0x36D7F4 in the D3D section, fmt 0x1E LIN_X8R8G8B8, pitch 2560. Guest VA = 0x80000000 | Data.
- ColourFilter quad at 0x5C7318: 0..1024 × 0..512, UV 0..1 plus a half texel, rhw 1.111 → samples the 1024×512 copy 1:1.

**RE target 2 — Xbox D3D texture-stage state [C]:** `D3D__TextureState` base **0x36BBC8**, 0x80 bytes per stage, XDK 5849 order (ADDRESSU 0, ADDRESSV 1, MAGFILTER 3, MINFILTER 4, MIPFILTER 5, COLOROP 12, COLORARG0/1/2 13/14/15, ALPHAOP 16, ALPHAARG0/1/2 17/18/19, RESULTARG 20, TEXCOORDINDEX 28). Values: D3DTOP DISABLE 1, SELECTARG1 2, SELECTARG2 3, MODULATE 4, MODULATE2X 5; D3DTA DIFFUSE 0, CURRENT 1, TEXTURE 2. During ColourFilter: stage0 COLOROP = ALPHAOP = MODULATE(DIFFUSE, TEXTURE), CLAMP, POINT; stage1 DISABLE. Dirty flags 0x36E280 = 0x20 at that point.

**Diagnosis of k (live pass-2 probes, pass 1 alpha = 0, c2 forced via `push imm8; pop reg` RAM patches):**
- gain − 1 = k·c·a with k = 0.585 ± 0.005, constant over channel, colour value (64/127) and vertex alpha (64/128/255) [C].
- rhw 1.111 / 20 / 1.0 → same k; c2 = 0 → gain exactly 1 (no additive term) → **fog/depth refuted**.
- Blend ONE/ONE with a = 128 → gain − 1 = 0.585·c (alpha unused) → **k is in the colour path** (combiner output = 0.585·texel·diffuse), not in the blend factor.
- Copy texels in guest RAM equal the backbuffer exactly (Morton-swizzle check at 7 points) → the data in RAM is not darkened. (xemu keeps render targets on the GPU, so RAM may not be what gets sampled.)
- RW alpha test kills a = 0 source pixels (a0 + ONE/ONE adds nothing).
- By the book (MODULATE, X8 texture, SRCALPHA/ONE) real hardware gives k = 1. The HUD (also Im2D + MODULATE) does not look darkened, so k is specific to sampling this render-target texture.

**Status:** H-a (fb alpha) refuted, H-b refuted, fog refuted. Leading hypothesis **H-c: xemu artefact when sampling a render-target texture** [H] — needs a hardware or second-emulator reference. Consequences:
- The E3 transplant stays valid (the raw frame has no filter).
- On real hardware the stock Xbox gain should be the PLAN's 1.88/1.79/1.53 (brighter, more washed out than xemu's 1.52/1.46/1.30).
- P1 must be designed to hardware semantics; xemu validation then needs k in the prediction, until k is explained.

## 2026-09-24 — k cross-check on Cxbx-Reloaded (HLE)

- Cxbx-Reloaded CI-585c49a runs `work/xbox/game/default.xbe` (a copy of the extracted folder). CJ is invisible, but the scene renders. The XBE lives at its own VAs inside `cxbxr-ldr.exe`, so `xemu_gdb.py --cxbx` pokes memory via Read/WriteProcessMemory (the same addresses work: clock, ped, code). Capture needs PrintWindow flag 2 on the D3D9 child window (automatic fallback in `capture`).
- Same scene/state, same RAM patches: pass 2 alone k = 0.581 / 0.583 / 0.577 (a255); ONE/ONE a128 identical to SRCALPHA a255 → colour path; stock full-filter gain **1.519 / 1.462 / 1.304** (xemu 1.517 / 1.462 / 1.296).
- **Verdict:** H-c (xemu artefact) **Refuted**. Two independent GPU implementations (LLE NV2A vs HLE D3D8→D3D9) agree, so k ≈ 0.58 comes from the game's D3D state/data. The PLAN's "Xbox gain 1.91 / 1.76 / 1.42" (k = 1) is wrong for the real game. Stock Xbox = `fb·(1 + 0.585·(c1·a1 + c2·a2))` [C for this scene; both emulators].
- Remaining candidates (matter for P1, because stage-state MODULATE2X only works if the fixed-function stages are what is really active) [H]:
  1. a pixel shader still bound during PostFX (stage states ignored; the PS computes tex·diffuse·const);
  2. the copy pass `0x24BB7B` stores fb·0.585 on the GPU (guest RAM compare in xemu could be stale);
  3. RW's Xbox Im2D draws through a vertex shader that scales diffuse;
  4. a D3D state not yet read (e.g., a stage-0 texture-transform or colour-sign side effect).

## 2026-09-24 — Where k lives (continued)

Symbols come from the Cxbx-Reloaded symbol cache (`E:\Emuladores\Cxbx-Reloaded\SymbolCache\GTA San Andreas-80a6f8dd6db3ccc6.ini`, 354 XDK 5849 functions and D3DRS addresses, e.g. SetPixelShader 0x368270, SetVertexShader 0x35CF30, DrawIndexedVertices 0x360610, D3DRS_FogEnable 0x36E3F8).

- Device global `[0x36E278]`; current pixel shader `[dev+0x784]`; current vertex shader `[dev+0x794]` [C].
- During ColourFilter: **pixel shader = 0** (fixed function) [C]. RW `Im2DRenderIndexedPrimitive` 0x2ABA40 copies the vertices verbatim (movntq), calls the 2D setup 0x2AB710 (SetPixelShader(0); with a texture: COLOROP = ALPHAOP = MODULATE, ARG1 DIFFUSE, ARG2 TEXTURE; VS 0x3D4D18), then DrawIndexedVertices [C].
- Im2D vertex shaders (created at 0x2AB5A2; decl/func in .rdata): 0x3D4D18 = {oPos = v0·c96 + c97, oPos.w = 1/v0.w, **oD0 = v1**, oT0 = v2}; 0x3D4D1C = no texcoord; 0x3D4D20 = no colour. No oFog write, no colour scaling [C]. RW uploads only c96/c97 (viewport).
- Render state at the draw: FOGENABLE 0, ZFUNC ALWAYS, ALPHATEST on (GREATER, ref 2), SRCBLEND SRCALPHA, DESTBLEND ONE, BLENDOP ADD, BLENDCOLOR 0, COLORWRITE all, DITHER 1 [C].
- **Texture-less probe** (raster push → 0, ONE/ONE, c2 = (64,32,16,a255)): the result is an addition of +37/+19/+10 = 0.58·c → k is on the **diffuse** side, not in the texture/copy [C].
- The HUD (Im2D) is not visibly scaled (clock digits 225,225,225) → k is draw-specific; cause still unknown [H]. A float 0.585 at 0x36A4D4 (D3D section) is part of a log2 table {0, 0.585, 1, 1.322, 1.585} with no code reference, so it's a coincidence.
- **Decision for P1:** treat k as an empirical property of this draw (present in LLE xemu and HLE Cxbx). The P1 colour constants get a single tunable k (default 0.585), so the patched output matches the PS2 formula in the emulators. Hardware validation remains open (if k = 1 on hardware, re-tune one constant).

## 2026-09-24 — k solved: the Xbox blur pass; P1 built and E4 (live, RAM-only)

**k = the Xbox-only blur pass `0x24ECAA` [C].** It runs after ColourFilter (called at 0x24CC89 with count `[0x3CE7B4]` = 2, alpha `[0x3CE7B8]` = 60, UV-offset scale `[0x3CE7B0]` = 1, enable byte `[0x3CE7AD]` = 1; static .data defaults, no direct writers). Each iteration draws the **pre-filter copy** `[0x5F4B28]` full-screen (colour 255,255,255, a = 60, default SRCALPHA/INVSRCALPHA) with slightly larger UV offsets. Two lerps at 60/255 → `out = 0.585·F + 0.415·raw`, and **(1 − 60/255)² = 0.5854** = the measured k.
- Evidence: in replace mode the output is `0.415·raw + 0.585·F` (pass-1-only probes with MODULATE/2X/4X fit this); with `0x3CE7AD` = 0 the additive-probe k goes from 0.489 to 0.83 (ratio 0.589).
- H-a (fb alpha), H-b, H-c (xemu), fog, VS scaling and pixel shader are all refuted. The HUD is unaffected because it is drawn later.
- This pass is part of the Xbox "washed-out" look: it re-adds 41.5% of the unfiltered frame (plus a slight blur).

**Residual k2 ≈ 0.80–0.83 [H].** It appeared only after the controller was disconnected/reconnected (before that, total k was exactly 0.585). It sits in the colour path (ONE/ONE and SRCALPHA give the same result; alpha is exact) and fits a further ~17% raw mix. Not the 0x24E90C/0x24B93E SpeedFX block, heat haze, underwater, 0x24E55E, 0x24E513, 0x110594, or 0x24EF1A (night vision only). Not a fade (black level normal). The trace of `0x263B40` callers after the filter: blur ×2 (0x24C42F), 0x24FA3A (render-to-texture, shadows), 0x250410 ×4, 0x25CCA8, 0x25BBAC ×9. Next check: a fresh boot, to see whether it disappears.

**P1 (`patches/p1_colourfilter.py` → `.json`) [built]:** a full rewrite of 0x24F007–0x24F132 (261 of 300 B): NEAREST, fog/z off, raster = copy, vtxalpha on; D3D-only stage0 COLOROP = MODULATE4X (RW cache 0x75D5A0 stays 4, so 0x2AB710 does not overwrite it), vertex colour = c·S (S = 128/256 for k = 1); pass 1 ONE/ZERO A = FF, pass 2 SRCALPHA/ONE A = a2; restores MODULATE and the original tail. Plus a data patch `0x3CE7AD` 01 → 00 (blur off). The JSON uses `orig_sha1` (no Rockstar bytes); `xbe_patch.py` now supports it. `dist/default_p1.xbe` sha1 96956a41…, 292 bytes changed.

**E4 (live RAM patch, blur off, frozen scene):**
- pass 1 alone: gain/c1 = 2.20 / 2.00 / 2.02 → `clip(fb·2c1)` reproduced [C] (R slightly high at a low c value).
- pass 2 alone: (gain − 1)/c2 = 1.59 / 1.63 / 1.56 vs 2·a2 = 1.99 → the residual k2 ≈ 0.8.
- Verdict: the P1 mechanism is **Confirmed** (MODULATE4X survives RW's 2D setup; the pass-1 term is exact). The ±2 E4 criterion is **not met yet** while the k2 residual is present; to be re-run after a fresh boot.
- Bug fixed on the way: `capture` letterbox auto-crop cut into dark 4:3 frames; it now crops only non-4:3 windows (PCSX2).

## 2026-09-24 — Residual k2 = display gamma; E4 passes

- **Residual k2 ≈ 0.83 = display gamma [C].** `D3DDevice_SetGammaRamp` (0x35E4E0) keeps a double-buffered ramp in the device at `dev + 0x1C28 + 0x1DC + idx·0x300` (R, G, B × 256; current idx `[dev+0x240C]`). The game builds it from the brightness setting with pow() into 0x5F20F0 and calls it from 0x2746EE. Active ramp after loading the save: R = G = B, `[0,32,64,128,192,255] → [2,44,79,142,200,255]`, fitted exponent **0.843**; the other buffer is the identity (the first session, a new game → k was exactly 0.585). xemu applies the ramp at display, so the captures are `fb^0.843`. This explains every "k2" probe, e.g. pass-1 R 0.549 → 0.608 (measured 0.604), 0.275 → 0.343 (0.338), 0.137 → 0.192 (0.191). A fresh boot + the same save keeps it; it is not a render pass (a trace of 1,372 RwRenderStateSet calls after the filter found no rebind of the copy raster).
- **Rule for all future captures:** read the active ramp and linearize with its inverse before any per-pixel comparison (the E3 captures were taken while the ramp was still the identity).
- **P1 final form:** MODULATE2X with the colours as-is (S = 256, exact for k = 1; the builder falls back to 4X + scale only if k < 1), rounding in the scale, plus blur off. 266 of 300 B. `dist/default_p1.xbe` regenerated via `xbe_patch.py`.
- **E4 (live RAM patch, frozen scene, framebuffer space):** P1 vs `predict_filter` PS2 formula on the raw frame: MAE 2.49 / 2.29 / 0.97, **86.9% of pixels within ±2**, 93% within ±4, mean bias ≈ −1 level. Residual spread is consistent with gamma-inversion quantization of 8-bit captures + dithering. **Verdict: E4 Confirmed** (P1 implements the PS2 colour-filter formula on the Xbox). (MODULATE4X variants: truncated S = 1/2 → 83.8% within ±2; rounded → 77.5%.)

## 2026-09-24 — P1 boot test (v0.1 candidate)

- `work/xbox/gtasa_p1.xiso` = a copy of `gtasa_stock.xiso` with the embedded default.xbe (sector 348678) replaced by `dist/default_p1.xbe` (sha1 c54604a8…; same size; the XDVDFS listing is still valid). Booted in xemu via Machine → Load Disc + Reset; the save loads.
- Live check [C]: RAM at 0x24F007 = P1 code, blur byte 0x3CE7AD = 0. The gamma ramp is the identity in this session (captures are linear).
- HUD, radar, clock and money render normally at dawn (06:51) and noon, so the MODULATE restore works. The dawn sky is strongly orange (PS2-like).
- Fidelity vs PS2 (same spot/time/weather; camera framing differs a little; `captures/ls_2277_noon/_p1_vs_ps2.png`):

| Metric | PS2 | Xbox stock | Xbox + P1 |
|---|---|---|---|
| ground patch RGB / ΔE vs PS2 | 141 118 61 | 121 108 74 / 14.5 | 131 113 66 / **6.3** |
| rail patch ΔE (framing-sensitive) | — | 14.9 | 10.5 |
| sky RGB (hue-classified) | 64 229 238 | 67 190 229 | **80 221 236** |
| HSV saturation mean | 0.615 | 0.460 | 0.533 |
| luminance p5 | 0.087 | 0.136 | 0.102 |

- **Verdict:** P1 closes most of the colour gap (Phase 2 goal). Remaining gap (saturation, deep shadows, glow) is expected from P2 blur / P3 radiosity / P4 building ambient, which are not applied yet.
- Note: `display.ui.show_menubar = false` in xemu.toml did not hide the menubar (it still appears in the top ~12 rows of captures); the analysis masks rows < 14.
