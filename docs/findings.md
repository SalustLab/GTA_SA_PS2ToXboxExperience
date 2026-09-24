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

## 2026-09-24 — Test saves past the first missions (interiors)

- The xemu HDD had no GTA SA save, only `UDATA/545400a3/{TitleMeta,TitleImage,SaveImage}.xbx`. Title ID `545400A3` = Second Edition (v2). First-edition saves use `54540082` (NTSC) and `54540086` (PAL).
- Xbox save format [C]: `GTA_SA.xsv` = a 20-byte signature + the standard 0x31800-byte SA save (checksum = byte sum, as on PC). Signature = HMAC-SHA1(key, data[20:]), key = HMAC-SHA1(XboxCERTKey `5C0733AE…1FE0`, XBE cert SignatureKey at cert+0xC0)[:16] = `2914C3D3C61115BF5CD42C09655FED02`. The computed signature matches a genuine v2 save (roamable, not tied to the console).
- v1 → v2 conversion [C]:
  - Version ID: v1 = `4CDC1D64`, v2 = `F68D14FD` (block 0 +0).
  - MAIN is 196293 B in v1 and 196272 B in v2, and the 21-byte edit comes before every saved IP. Every relative thread IP and return-stack slot is shifted −21. All 28 threads then land after a `wait`, and the return slot lands after a `gosub`. A genuine v2 save has main at `0xEB36` = v1's `0xEB4B` − 21.
  - The scm-size field is set to 196272, then the checksum is recomputed and the save re-signed. Block sizes match v1/v2 exactly.
- Installed in `E:\Emuladores\xemu\xbox_hdd.qcow2` (original backed up as `xbox_hdd.qcow2.bak_20260924`):
  - slot 1 "Big Smoke": a genuine v2 save, unmodified (GameFAQs 9370), $999,999,999;
  - slot 2 "Ryder": EU v1, converted, clean (GameFAQs 12695);
  - slot 3 "Ryder": NA v1, converted, $999M, has-cheated flag set (GameFAQs 8099).
- Tools (read-only qcow2+FATX reader, installer that rewrites a fresh qcow2 and verifies every cluster, converter) and the downloads are in `work/saves/` (gitignored).
- Status: slot 1 is the zero-risk save. Slots 2–3 depend on the conversion **[S]**; untested in-game.

## 2026-09-24 — P1 in-game interior check (CJ's house)

- Setup: `gtasa_p1.xiso` with save slot 2 (the converted Ryder save, which loads fine → the v1→v2 conversion is **[C]**). CJ is inside interior 3 at (2495.6, −1700.9, 1014.7), clock about 06:30, `timescale 0`.
- Live checks [C]: RAM at 0x24F007 = P1 code, and `0x3CE7AD` = 0.
- Gamma ramp idx 0 is **not** the identity (`[0,32,64,128,192,255] → [6,63,101,160,210,255]`). Saved as `captures/cj_house_int/_gamma_ramp.bin`; captures are linearized through its inverse.
- ColourFilter args (`filterargs`) [C]: c1 = (64,64,64, a128), c2 = (64,64,64, a254). This is a neutral interior filter.
  - PS2 formula: gain ≈ 1.00.
  - Stock Xbox formula: 1.376 (before the blur mix).
- Hypothesis: P1 in an interior matches `predict_filter` (PS2) within ±2 and leaves the HUD untouched. Prediction: ≥ 90% of pixels within ±2, and HUD P1 == raw (raw = ColourFilter call NOP at 0x24CAF5).
- Result:
  - Whole frame (rows < 14 masked): 95.6% within ±2. The misses all fall in one box (x 268–396, y 173–428) where CJ's idle animation and the bobbing entry marker keep moving at `timescale 0`; two P1 captures differ from each other in the same box.
  - Outside that box: **100% within ±2**, MAE 0.51 / 0.51 / 0.48.
  - HUD (clock, money, health, weapon, radar): P1 vs raw max 2, MAE 0.30, so the MODULATE restore holds in interiors.
- **Verdict: Confirmed.** Caveat: the interior filter is close to the identity under the PS2 formula, so this scene tests state safety (HUD, restore, no artefacts) more than the colour transform. The night check is the stronger remaining test.

## 2026-09-24 — P1 in-game night check (Grove St, 00:00, SUNNY_LA)

- Setup: slot 2 save on `gtasa_p1.xiso`, player at (2488.2, −1665.5, 13.3). Clock frozen at 00:00, weather 0, then `timescale 0`. Gamma ramp idx 0 is the same non-identity ramp as in the interior check; captures are linearized.
- ColourFilter args [C]: c1 = (93,93,93, a254), c2 = (64,129,130, a254).
  - PS2 gain ≈ 1.23 / 1.74 / 1.75.
  - Stock Xbox gain ≈ 1.61 / 1.87 / 1.87 (formula only).
- Hypothesis: P1 at night matches the PS2 formula within ±2 on filtered pixels. Prediction: ≥ 95% within ±2 and near-zero bias; P1 vs the Xbox formula far off.
- Result (rows < 14 masked; pixels that move between two P1 captures masked, 6.1%):
  - All static pixels: 94.8% within ±2. Every outlier is a pixel where P1 == raw: the HUD, radar, help text and streetlight coronas. These are drawn after PostFX, so the prediction wrongly filters them.
  - Excluding pixels drawn after the filter (P1 == raw within ±2): **98.6% within ±2, 99.5% within ±4**, MAE 0.47 / 0.68 / 0.80, bias +0.2 / −0.0 / +0.1.
  - P1 vs the stock-Xbox formula: 5.3% within ±2 (bias −11.5 / −5.8 / −4.5).
  - HUD and coronas are unfiltered and intact (`_raw_vs_p1_bad.png`).
- **Verdict: Confirmed.** P1 applies the PS2 colour-filter formula at night, and the stage-state restore holds. PS2 fidelity at this spot/time (a PCSX2 reference) is not measured yet.

## 2026-09-24 — PS2 test save (PCSX2 memory card)

- Our PS2 disc is v3.00 (Greatest Hits): MAIN is 196586 B, globals 43792 [C], and the save version ID is `F68D14FD` (the same as Xbox v2). v3.00 MAIN differs from Xbox v2 MAIN (+314 B), so an Xbox→PS2 conversion would need an IP remap. Most PS2 saves online are v1 (`4CDC1D64`, globals 43768), which is incompatible.
- Used a native v2 save instead: GTASnP `Kn1lF4` "Tagging up Turf" (the mission after Ryder), downloaded with all site edits off. It has no cheats, $50,723, and was saved in CJ's house.
  - Checks [C]: ID `F68D14FD`, globals 43792, scm size 196586 = our MAIN, checksum OK, and all 28 thread IPs land after a `wait` in our v3.00 `MAIN.SCM`.
- Folder `BASLUS-20946GTA50000` (one folder holds every slot's `N  Mission.b`):
  - `icon.sys` and icons come from a PCSX2 `.psu` (GameFAQs 34735). Its `icon.sys` is identical to that of a v3.00 save.
  - The 1 KB `BASLUS-20946GTA50000` header comes from a genuine v3.00 save (GameFAQs 25084).
- Imported into `E:\Emuladores\PCSX2\memcards\Mcd001.ps2` with `mymcplus` (pip). Original backed up as `Mcd001.ps2.bak_20260924`. `mymcplus check`: no errors; the save read back from the card is byte-identical. Card free space is now 108 KB, so extra in-game save slots will not fit on this card. Untested in-game.

## 2026-09-24 — Interior fidelity vs PS2 (CJ's house)

- PS2 reference: `Tagging up Turf` save (it loads in PCSX2 → PS2 save **[C]**), software renderer 1×, clock 06:30, weather 0. CJ teleported to the Xbox capture spot (2495.6, −1700.9, 1014.7), then `timescale 0`.
  - Framing differs: the PS2 camera is lower and closer, so only global stats and hand-matched patches are used.
  - Variants are in `captures/cj_house_int/vs_ps2/`, rows < 14 cropped. The Xbox frames are linearized (= default brightness), because this Xbox save has a raised brightness ramp.
  - "Stock" is an **estimate**: raw × (1 + 0.585·(c1·a1 + c2·a2)) = 1.22×. It is not a capture.
- Global metrics (linear): see the table.

| Metric | PS2 | Xbox stock (est.) | Xbox + P1 |
|---|---|---|---|
| luminance mean | 0.140 | 0.199 | **0.165** |
| luminance p5 | 0.003 | 0.046 | 0.036 |
| HSV saturation mean | 0.472 | 0.322 | 0.329 |
| R/B | 1.342 | 1.275 | 1.280 |

- Patches (ΔE76 vs PS2, stock → P1): blue wall 20.7 → 13.4; wooden floor 7.5 → 4.6; door 17.3 → 8.9; ceiling 1.3 → 4.2.
- As displayed with this save's brightness ramp, Xbox luminance is 0.28 vs PS2 0.14, so the brightness option alone dominates. Fidelity captures need the Xbox brightness at its default (identity ramp).
- **Reading:**
  - The interior filter is neutral, so P1 only removes Xbox's 1.22× brightening. That closes about 57% of the luminance-mean gap and most of the wall/door ΔE.
  - What remains is **not** ColourFilter: the PS2 has much deeper shadows (p5 0.003 vs 0.036) and far more saturation (0.47 vs 0.33), for example the PS2 floor at 26/12/2. These are candidates for lighting/ambient (H5/P4), radiosity (P3) or the PS2 brightness setting (unknown for this save) [H].

## 2026-09-24 — Xbox brightness default + night fidelity vs PS2 (Grove St, 00:00, SUNNY_LA)

**Xbox brightness [C]:**
- `SetBrightness(float b)` is at 0x274662. `b` = menu int `[0x6E79AC]` (FrontEndMenuManager+0x3C) × 1/512.
- Exponent = 1 − 0.7·b + 0.2 (constants 0x390AAC / 0x39087C / 0x390A24). The ramp is `pow(i/256, exp)·255` → `SetGammaRamp(1, 0x5F20F0)`.
- Callers: menu slider 0x11C9E9, "restore defaults" 0x11DDCB (writes 256 and calls with 0.5), and settings load 0x11BFC7/0x11C11B/0x163FCE.
- **The default 256 is not the identity**: exponent 0.85 (`128→141`), which brightens. The identity seen in the first session was an untouched buffer. The Ryder save had 384 (exponent 0.675).
- Set live to 256 by injecting `SetBrightness(0.5)` through GDB (hijacked at the PostFX Render entry 0x24C537, registers restored). Resulting ramp idx 1 = `[2,44,79,142,200,255]`, the known 0.843 ramp.

**Night captures:**
- Both consoles were at (2488.2, −1665.5, 13.3), heading 1.43, 00:00, weather 0, `timescale 0`. Xbox stock was captured live by restoring the original 0x24F007 bytes + blur byte 1, then P1 was put back and verified.
- The PS2 frame has no HUD/CJ and a slightly different camera, so the stats are regional with CJ/HUD/menubar masked. Files: `captures/grove_night/{ps2,xbox_stock_display,xbox_p1_display}.png`, `_ps2_stock_p1.png`.

| Region | Metric | PS2 | Xbox stock | Xbox P1 |
|---|---|---|---|---|
| frame | R/B | 0.73 | 1.07 | **0.95** |
| road | R/B | 1.19 | 1.92 | **1.56** |
| road | saturation | 0.306 | 0.476 | **0.366** |
| frame | lum (displayed, ramp 256) | 0.133 | 0.175 | 0.192 |
| frame | lum (ramp removed) | 0.133 | 0.130 | 0.144 |

**Reading:**
- P1 moves the night hue toward PS2 (teal instead of brown).
- The displayed image is brighter than PS2 because of the **Xbox display gamma at default brightness (exp 0.85)**. With the ramp removed, luminance matches PS2 within ~0.01. So PS2 ≈ Xbox framebuffer without a display ramp **[S]** (the PS2 save's own brightness setting was not read).
- Candidate data patch [H]: `0x390A24` 0.2 → 0.35 makes brightness 256 give exponent 1.0 (identity), leaving the slider working. Test it against the PS2 in another scene before adopting it.

## 2026-09-24 — Gamma fix test: `0x390A24` 0.2 → 0.35 (brightness 256 = identity ramp)

- Hypothesis: the remaining displayed-brightness gap to PS2 is the Xbox default display gamma (exp 0.85). Prediction: with brightness 256 mapped to the identity ramp, P1's luminance and mean-colour ΔE vs PS2 drop in both a day and a night scene.
- Method:
  - Live RAM poke `0x390A24` = 0.35, then `SetBrightness(0.5)` injected. The ramp becomes **exactly the identity** on all 768 entries [C].
  - Grove St (2488.2, −1665.5, 13.3), heading 1.43, weather 0, at 12:00 and 00:00. Both consoles frozen. Captures:
    - PS2;
    - Xbox P1 and stock (live), both captured with the fix;
    - "default gamma" variants: the default ramp applied to those same frames, exact because the fixed display = framebuffer.
  - Masks: HUD, radar, CJ, menubar. Files: `captures/grove_{noon,night}_gammafix/`, `_grid.png`.
- Result (PS2 vs Xbox; ΔE76 of the region's mean colour; dlum = Xbox − PS2):

| Scene / region | stock, default gamma | P1, default gamma | **P1 + fix** |
|---|---|---|---|
| noon frame | ΔE 21.6, dlum +0.034 | ΔE 5.7, dlum +0.055 | **ΔE 1.0, dlum +0.002** |
| noon sky | 35.4 | 7.6 | 7.5 |
| noon road | 25.2 | 11.3 | **6.9** |
| night frame | ΔE 3.8, dlum +0.017 | ΔE 3.8, dlum +0.031 | **ΔE 2.1, dlum −0.015** |
| night sky | 6.8 | 9.3 | **3.2** |
| night road | 7.9 | 3.5 | 4.9 |

- **Verdict: Confirmed.** The fix improves whole-frame fidelity in both scenes. With it, PS2 ≈ the Xbox framebuffer with no display ramp [S→C for these two scenes].
  - Side effect: the brightness slider still works (exp = 1.35 − 0.7·b, so it brightens only above 256).
  - Remaining gaps: noon saturation (−0.10), noon sky (PS2 more teal), night road slightly darker (−0.03). These are candidates for P2/P3.
- Live state left in the xemu session: `0x390A24` = 0.35, brightness 256.

## 2026-09-24 — Diagnosis of the two residuals after P1 + gamma fix (noon sky, night asphalt)

- **Region boxes were framing-confounded.** The PS2 camera sits lower and closer and is pitched differently, so the same box samples a different height of the sky gradient. Re-measured by content (sky/asphalt pixel classes) at matched luminance. **Both residuals are real:**
  - Noon sky at equal luminance: PS2 81/187/178 vs P1+fix 104/178/173 (PS2 less red); the PS2 sky reaches higher luminance.
  - Night asphalt at equal luminance: PS2 40/47/31 vs 42/44/27 (PS2 greener/bluer); median lum 42 vs 36.
- **E2 (live `0x5F4B1C` = 1, noon) → H2 Confirmed.** The Xbox radiosity is called after ColourFilter at 0x24CD7D with args limit `[0x6C88DC]` (int; 180 at noon, 90 at midnight), filterPasses 2, renderPasses 1, intensity 35 (`0x3CE7C4..D0`). With it on, only edges change (a slight shift/blur) and bright pixels get marginally darker (−0.3). There is **no bloom**.
- **Offline PS2-radiosity model** (PLAN §9 P3: downsample ×4, `2D − limit`, add ×intensity/k):
  - Noon: the sky gets closer (ΔE 6.3 → **3.3** with /255; /128 overshoots, 10.2, so H4 favours **/255**), but the whole frame gets worse (ΔE 1.1 → 3.3) because the ground passes the limit too.
  - The PS2 sky's lower R cannot come from an additive bloom, so part of the sky gap is already in the pre-filter sky [H].
  - Night: the model does not touch asphalt (below limit 90) and the frame ΔE goes 2.2 → 2.0.
- **E1 (lighting mult) ruled out here [C].** 0x24C6B6–0x24C75F: `L` (smoothed light level at the player, `[0x75865C]`, rate `pe_lightchangerate`, cap `pe_lightingbasecap`) gives `mult = 1 + (1 − L/cap)·pe_lightingbasemult`, which scales the ColourFilter colour bytes. Live at Grove St, midnight: L = 0.30 of cap 0.35 → mult 1.071 (Xbox 0.5) vs 1.057 (PS2 0.4). That is about 1%, negligible.
- **Night asphalt → H5 (building ambient) is the remaining candidate [S].** The PS2 − P1 difference at matched luminance is ≈ +2/+8/+7, i.e. a teal additive term that looks like extra night ambient. Not gamma, not E1, not radiosity.
  - For P4: the building-pipe constant-upload functions around 0x166E26 (c6D–c70, c77, c80/81, c74–76) do not fire in this scene.
  - A 400-hit log of `SetVertexShaderConstant*` saw only RW Im2D's c96 (0x2AB925). So the 3D pipes write their constants **inline into the push buffer**; RE target 5 has to find those writers.

## 2026-09-24 — P5 built: neutral display gamma (operand repoint, not a constant edit)

- **Correction to "Gamma fix test".** `0x390A24` is the compiler's pooled float 0.2, with ~335 references game-wide (raw operand search). Editing it changes unrelated systems, and the live test did that while its captures were taken. Reverted in RAM.
  - The ramp and fidelity results stand: those frames were frozen, and the ramp depends only on SetBrightness.
  - "Candidate data patch `0x390A24` 0.2 → 0.35" is **withdrawn**.
- **P5 as built [C]:**
  - `addss xmm0, [0x390A24]` at 0x27468E (`F3 0F 58 05` imm32) now reads `[0x390C44]`, an existing float 0.35 in the same constant pool.
  - `.rdata` flags 0x6: not writable.
  - Only the 4-byte operand at 0x274692 changes (`240A3900` → `440C3900`, 2 bytes differ).
  - Live: operand poked, pooled 0.2 untouched, `SetBrightness(0.5)` → exact identity ramp on all channels.
- `patches/p5_display_gamma.py`: guards the instruction bytes and the 0.35 value. Its `--selftest` models the game's ramp loop and reproduces all three live ramps: stock 256, Ryder-save 384, and fixed = identity.
- `dist/default_p1p5.xbe` sha1 9c4db1ab…; `work/xbox/gtasa_p1p5.xiso` (embedded XBE replaced at sector 348678 after verifying the stock bytes). Boot test pending.
- **P5 boot test (2026-09-24) [C]:** `gtasa_p1p5.xiso` boots and slot 2 loads. Live: P1 code, blur byte 0, P5 operand `440C3900`, pooled 0.2 intact. The save restores its own brightness (384 → exp 0.825 under P5, ramp `128→144`; stock at 384 gives `128→160`), so brightness is per-save state. Setting 256 (slider or "restore defaults") gives the exact identity ramp.

## 2026-09-24 — P1 pause-menu check (Phase 2 closed)

- `gtasa_p1p5.xiso`, pause menu (Map tab). A breakpoint at 0x24F007 never hits within 3 s → **ColourFilter is not called while the menu is up [C]**.
- Capture with P1+P5 vs live stock ColourFilter + blur on: **0 pixels differ** (max diff 0). Repeat P1 capture also identical. The menu renders normally, with no leaked stage state (`captures/pause_menu/_p1p5_vs_stock.png`).
- **Verdict: Confirmed.** Phase 2 in-game checks (interior, night, menu) are all passed.

## 2026-09-24 — Phase 3 prep: RE target 3a (ColourFilter quad) + P2 design notes

- **ColourFilter quad at 0x5C7318 (live) [C]:**
  - Vertices (stride 28):
    - v0 = (0, 0) top-left, UV (0.00049, 0.00098);
    - v1 = (0, 512) bottom-left;
    - v2 = (1024, 512) bottom-right;
    - v3 = (1024, 0) top-right.
  - Index buffer 0x3CE82C = (0,1,2, 0,2,3). This **matches SkyGfx's corner mapping** directly: left → v0,v1; top → v0,v3; right → v2,v3; bottom → v1,v2.
  - UV at +0x14/+0x18; the half-texel bias is already present.
- **Blur offsets `0x3CE808/80C/810/814` (left/top/right/bottom) read 16/16/16/16 live**: Xbox `stream.ini` value; the PS2 ships 8.
  - SkyGfx: off_u = pe·(W/640)/16/rasW, off_v = pe·(H/448)/16/rasH, with the copy raster 1024×512.
  - pe 8 → +0.5 texel (u and v), which with LINEAR gives the PS2's soft 2×2 blur of the pass-2 term. pe 16 → a full-texel shift, with no blur.
  - [S] The PS2 value 8 is needed; for the RAM test poke the four globals. The shipped mod gives the ini lines (PLAN §15).
- **Code cave candidate:** the Xbox blur pass 0x24ECAA–0x24EEA1 (0x1F8 B; dead since P1 sets 0x3CE7AD = 0).
  - It starts `push ebp; mov ebp,esp; sub esp,0x28; cmp byte [0x3CE7AD],0; …; je 0x24EE9F`, and its only known call is at 0x24CC89. Not checked yet: whether other callers exist.
  - Alternative: 34 free bytes left in P1's 300-byte ColourFilter slot. That is too small for UV shift + restore.
- **P2 requirements:** pass 2 only, texture filter LINEAR (RwRenderStateSet 9 = 2), then back to NEAREST. The UVs must be restored after the draw (0x5C7318 persists across frames, so shifts would accumulate).

## 2026-09-24 — P2 filter blur: built, live RAM test and E5 (Grove St 12:00, SUNNY_LA)

- **Hypothesis:** the PS2 softness is pass 2 of the colour filter sampling fb′ with LINEAR filtering at +pe/16 texels (pe = 8 → +0.5 texel, a 2×2 box). **Prediction:** the patched frame matches `predict_filter.predict(raw, c1, c2, shift=(0.5, 0.5))` within ±2 levels, and its Laplacian variance moves from P1's value to the PS2's.
- **Cave [C]:** the Xbox blur pass 0x24ECAA–0x24EEA1 (504 B) has exactly one reference, `call` at 0x24CC89 (rel32 scan of every section; no absolute pointers). The caller pops the two args itself, so NOP-ing the call is equivalent to P1's blur byte = 0.
- **P2 as built (`patches/p2_filterblur.py` → `.json`):** P1 plus blur is 439 B, which does not fit P1's 300 B slot. P2 is therefore self-contained and **supersedes P1**. `xbe_patch.py` refuses P1 + P2 because both patch 0x24F007.
  - `0x24F007`: `jmp 0x24ECAA`. Every caller lands in the new body, with the stack and ABI unchanged.
  - `0x24CC89`: the blur-pass call becomes 5 × NOP.
  - `0x24ECAA`: P1's code (`p1_colourfilter.build(blur=True)`, which emits the same bytes as v0.1 when `blur=False`; the selftest asserts this) plus, for pass 2: filter LINEAR, a stack copy of the quad 0x5C7318, and UVs += `pe/(16·rasW|rasH)`. The raster size is read from the copy raster, where RwRaster width/height sit at +0xC/+0x10 = 1024/512 [C]. The persistent quad is never modified.
  - Unlike SkyGfx, no `W/640`, `H/448` scale is applied: the Xbox renders 640×480 natively, and the PS2 meaning of the value is pe/16 of a framebuffer pixel.
- **PS2 pe globals [C]:** `0x668D28..0x668D34` (`$gp` − 0x2B48): 8, 8, 8, 8, followed by 1.0, 1.0, 0.0008 (`pe_lightchangerate`) and 0.35 (`pe_lightingbasecap`). Found by a batched PINE scan of $gp ± 32 KB. Poking them to 0 visibly sharpens the PS2 image, so they are read every frame.
- **Live RAM test (xemu, P1+P5 session, brightness 256 = identity ramp, timescale 0):** c1 66,66,48,a254, c2 166,129,60,a254. The mask drops rows < 14, the last 2 rows/columns, moving pixels and the HUD (91.9 % of the frame kept). Files: `captures/grove_noon_p2/`.

| Capture vs model | MAE R/G/B | within ±2 | within ±4 |
|---|---|---|---|
| P1 vs predict (no shift) | 0.68 / 0.76 / 0.34 | 98.2 % | 99.5 % |
| **P2 pe 8 vs predict (+0.5)** | 0.83 / 0.86 / 0.45 | **97.1 %** | 98.3 % |
| P2 pe 8 vs predict (no shift) | 2.91 / 2.76 / 1.79 | 59.9 % | 78.6 % |
| P2 pe 16 vs predict (+1.0) | 1.12 / 1.19 / 0.60 | 97.1 % | 98.1 % |

- **E5 (sharpness):**
  - The PS2 blur toggle (pe 8 ↔ 0, three alternating pairs): Laplacian-variance ratio **0.626**, repeatable to 5 digits.
  - Xbox P2/P1: 0.497 as captured. Through a simulated PS2 display resample (448 → 480 bilinear, the PCSX2 present path) it is 0.557.
  - Absolute Laplacian variance: PS2 0.0064, P1 0.0115 (+79 %), **P2 0.0056 (−12 %)**, P2 with pe 16 0.0067.
  - Mean colour, R/B ratio, saturation and luminance percentiles are unchanged from P1, since the blur does not shift colour.
- **Verdict:** P2 mechanism **Confirmed** (97.1 % within ±2, and the unshifted model is clearly rejected). E5 **Confirmed [S]**: the sharpness gap to PS2 drops from +79 % to −12 %. The rest is inside the confounds (the PCSX2 present-path resample, different framing and content, and an offline sweep that is not reliable because the model also blurs the HUD). If visual sign-off wants less blur, the knob is data-only: ini pe 6 = +0.375 texel.
- **Harness note:** the PS2 camera keeps swinging for about 20 s after a teleport even at timescale 0. Wait until frame-to-frame diffs settle (mean |d| ≈ 1) before paired toggles.
- **Build:** `dist/default_p2p5.xbe` (P2 + P5) has sha1 ed5c41e3…. `work/xbox/gtasa_p2p5.xiso` = a stock copy with the embedded XBE replaced after checking the stock bytes, and with the embedded `stream.ini` (sector 1998977, 197 B, same size) set to pe 8 (`\t16` → `\t\t8`; a copy is at `work/xbox/stream_pe8.ini`). Boot test pending.
- **P2 boot test (2026-09-24) [C]:** `gtasa_p2p5.xiso` boots, and slot 2 loads. Live: all P2 and P5 bytes equal the JSONs; pe offsets are 8 ×4, read from the ISO's edited `stream.ini`; blur byte 0x3CE7AD = 1, as expected (P2 NOPs the call instead). Grove St 12:00, c1 66,66,48,a254, c2 166,129,60,a254: P2 vs `predict(raw, shift=0.5)` = **99.0 % within ±2** (MAE 0.63/0.62/0.35) with the overlays and animated characters masked (help box, Stats panel, HUD, CJ, one pedestrian; 69.7 % of the frame kept). The unshifted model gets 58.1 %. The unmasked frame gives 93.2 %, and all of the excess is the translucent HUD boxes (drawn after the filter) and CJ's idle animation. The HUD renders crisp and complete. Files: `captures/grove_noon_p2boot/`.
  - Brightness after "set 256" in the menu read **284** (`[0x6E79AC]`, ramp max +4, not the identity). The captures were linearized with the captured ramp. For exact-identity captures use `work/session_tools/xbright.py 256`.
- **Visual sign-off (2026-09-24):** the user accepted P2 with pe 8 against the PS2. Phase 3 is closed.

## 2026-09-24 — Phase 4: P3 radiosity (RE targets 3b/4, build, E6 live)

**RE [C]:**
- Stock `CPostEffects::Radiosity` is **0x24DF8E–0x24E512 (1413 B)**, not ~2.4 KB: 0x24E513 (darkness quad), 0x24E55E and 0x24E665 are separate functions with their own callers. References: only `call` at 0x24CD7D (main: limit = `[0x5F4B1E]` ? `[0x3CE7CC]` 220 : timecyc `[0x6C88DC]`; filterPasses `[0x3CE7C4]` 2, intensity `[0x3CE7D0]` 35, eax = renderPasses `[0x3CE7C8]` 1; skipped while the darkness filter `[0x5F4B14]` is on) and 0x24CB32 (darkness filter: `[0x3CE7A4]` 45, 0, 255, eax 2). UV corrections `[0x3CE7D4/D8]` = 2/2. The same defaults as PC `CPostEffects::m_Radiosity*`.
- Render order: 0x24BB7B (copy) → ColourFilter → darkness filter + radiosity → … → radiosity 0x24CD7D. No copy between the filter and the radiosity: the stock function samples the **pre-filter** copy. It builds a 2-vertex-per-rect sprite list at 0x5DB7C0 and draws it as a tristrip through 0x263B40, which degenerates on Xbox (the E2 result).
- `0x24BB7B` = RwCameraEndUpdate (0x2977F0, jmp [cam+0x1C]) on the scene camera `[0x5B8528]`, RwCameraBeginUpdate (0x297800, jmp [cam+0x18]) on the postfx camera `[0x5F4B30]` (raster = the copy 0x5F4B28, 1024×512, confirmed live), 0x263368 (2D default states), then the full-screen quad 0x5C72A8 textured with the screen raster, then back. So "render into C" is just a camera switch; no new raster or Initialise patch is needed (RE target 3b is not needed for P3).
- Screen W/H `[0x5B8530]/[0x5B8534]` = 640/480.
- `pe_bRadiosity` → `atoi != 0` → byte `0x5F4B1C` (handler 0x1580C7; tokens split on `" ,\t"`). `devkit_memory` sets the same memory global as `memory` (0x39F334 = v<<10) plus a "devkit" flag that makes later `memory` lines ignored; in the Xbox ini both are 38000.
- **PS2 `m_bRadiosity` = `$gp+0x1658` = 0x66CEC8** (INIT.NM stream.ini handler `sb $v0, 0x1658($gp)` at 0x895C20, next to `pe_bottomy` at `$gp−0x2B3C`). Live: 1, read every frame.

**P3 as built (`patches/p3_radiosity.py` → `.json`, 978 of 1413 B):** SkyGfx's fixed-function PS2 radiosity (`postfx.cpp CPostEffects::Radiosity` @926616a3), on the two Xbox surfaces:
1. `0x24BB7B`: C = F (the filtered frame).
2. Downsample ×filterPasses, SkyGfx geometry (src [UC+0.5, dw+0.5] → dst [0, dw/2+1], LINEAR), ping-pong C → backbuffer corner (scene camera) → C strip x ≥ 640 (postfx camera; that strip is never on screen).
3. Highlight `2D − L` = stage-0 `ADDSIGNED2X` (9) with vertex grey d = 128 − L·128/255, merged into the last hop when it lands in C, else a 1:1 hop (odd filterPasses; no stock caller).
4. Restore the backbuffer 1:1 from C, then add the (dw+1)-texel highlight stretched to full screen: LINEAR, SRCALPHA/ONE, A = intensity (/255), ×renderPasses. filterPasses 0 (darkness filter): highlight inside the 1:1 composite.
5. COLOROP back to 4, `0x24BB7B` again (C = final frame, SkyGfx UpdateFrontBuffer), stock tail states.
- Self-check (`--selftest`): code fits, disassembles fully, calls only 0x24BB7B / camera begin/end / its own draw helper, one Im2D draw site; `model()` = the same operator in numpy (analytic flat-frame and single-dot cases).

**PS2 reference (Grove St 12:00, weather 0, software renderer 1×, `m_bRadiosity` toggled live):**
- Hypothesis: SkyGfx's PS2 path with the timecyc limit and /255 reproduces the PS2 bloom (H4: /255 vs /128). Prediction: `model(ps2_off, L, 2, I)` ≈ `ps2_on` with best fit at the Xbox's live limit (180) and 35.
- Result: PS2 on − off mean +4.8/+5.5/+4.5 (repeatable, on/on MAE 0.8). Grid fit over L ∈ {140…220}, I ∈ {25, 35, 50, 70}: **best L = 180, I = 35: MAE 1.02, bias −0.02/0.00/−0.01** (no radiosity: MAE 6.01). /128 (I 70) is clearly worse. UC/VC 2 beats 0 and 1 (MAE 1.02 vs 1.58/1.27). The residual is unstructured scanline noise (PS2 448 → 480 display resample; modelling it gives 0.94).
- Night (00:00, limit 90): the PS2 bloom is tiny (+0.14/+0.32/+0.07); model(90, 35) bias ≈ 0, MAE 0.167 vs 0.222 with no radiosity (consistent, weak signal).
- **Verdict: H4 Confirmed = /255 [C for these scenes].** The PS2 radiosity operator is SkyGfx's, with the timecyc limit and the stock 35.
- Harness: the **idle camera** (CIdleCam) starts panning after CJ is left idle, on both consoles, even at timescale 0 (it made the first PS2 night set unusable). Nudge the player, then capture quickly.

**E6, Xbox live RAM test (`work/session_tools/p3live.py`; `gtasa_p2p5.xiso` session, brightness 256 = identity ramp, timescale 0):** P3 poked into 0x24DF8E, `0x5F4B1C` toggled. Deterministic check: capture vs `model(flag-off frame, …)`. The HUD boxes and moving pixels (dilated 16 px) are masked, because the HUD is drawn after PostFX and the model would bloom it.

| Path | Scene / args | kept | P3 − off mean | vs model MAE | within ±2 |
|---|---|---|---|---|---|
| filterPasses 2 (highlight merged) | noon, 180/2/35/1 | 75.6 % | +8.4/+7.4/+4.5 | 0.08/0.20/0.02 | **100 %** |
| (same, model without UC/VC) | | | | 1.28/1.47/0.72 | 79.4 % |
| filterPasses 2 | midnight, 90/2/35/1 | 72.7 % | +0.3/+0.4/+0.2 | 0.02/0.03/0.01 | **100 %** |
| filterPasses 0 (darkness filter forced via `0x5F4B14` = 1, darkness alpha 170) | 45/0/255/2 | 89.8 % | +0.5/+0.8/+0.3 | 0.04/0.06/0.02 | **100 %** |

- The HUD is intact, with no edge or strip artefacts; the game keeps running (GDB responsive, frames repeatable to MAE 0.15). `ADDSIGNED2X` = 9 and drawing at x ≥ 640 in the postfx camera are confirmed by the 100 % match.
- **Verdict: E6 Confirmed**: P3 draws exactly the PS2 (SkyGfx) radiosity on the Xbox.
- Fidelity vs PS2 at noon (content classes; framing differs): **sky ΔE 6.8 → 3.9** (the "noon sky" residual after P1 + gamma is mostly radiosity). Ground ΔE 8.1 → 10.6 and frame 3.8 → 6.6 get worse, because the Xbox ground is already brighter than the PS2's *before* radiosity (142/106/56 vs PS2 no-radiosity 121/86/42) and the bloom grows with it. Since the operator matches, that gap is upstream (building/ground lighting, H5/P4, or framing) [H].
- **Build:** `dist/default_p2p3p5.xbe` (P2 + P3 + P5; sha1 d7e1d28c…) → `work/xbox/gtasa_p2p3p5.xiso` (a copy of `gtasa_p2p5.xiso`, both regions verified before the write). The embedded `stream.ini` is pe 8 + `devkit_memory\t38000\r\n` → `pe_bRadiosity\t\t\t\t\t1\r\n` (same 21 B, file stays 197 B; a copy is at `work/xbox/stream_pe8_rad.ini`). Boot test pending.
- **P3 boot test (2026-09-24) [C]:** `gtasa_p2p3p5.xiso` boots and the save loads (slot 1, now a copy of slot 2 re-saved with brightness 256). Live (`work/session_tools/p3boot.py`):
  - All P2, P3 and P5 bytes equal the JSONs.
  - pe 8 ×4; `0x5F4B1C` = 1 read from the ISO's `stream.ini`; memory 38000 (the `devkit_memory` swap is harmless); brightness 256 → identity ramp.
  - Grove St 12:00, limit 180, c1 66,66,48,a254, c2 166,129,60,a254: P3 vs `model(flag-off frame, 180)` = **100 % within ±2** (MAE 0.08/0.22/0.02; 66.2 % kept after masking the HUD, radar and phone help box, dilated 16 px, plus CJ's phone animation, his shadow and a pedestrian). The first pass (95.9 %) left the help box and the later animation unmasked.
  - Overlays drawn after PostFX are unchanged. Side-by-side for sign-off: `captures/grove_noon_p3boot/_signoff_grid.png`.
- **P3 pause-menu check (2026-09-24) [C]:** with the pause menu up, breakpoints at 0x24DF8E (radiosity) and 0x24C537 (PostFX Render) never hit within 3 s. Captures with `0x5F4B1C` = 1 / 0 / 1: **0 pixels differ** (`captures/pause_menu_p3/`).
- **Visual sign-off (2026-09-24):** the user accepted P3 against the PS2 (`_signoff_grid.png`). **Phase 4 is closed**; v0.3 candidate = `gtasa_p2p3p5.xiso`.

## 2026-09-24 — P3 interior check (CJ's house, both consoles, 12:00)

- Setup: `gtasa_p2p3p5.xiso` (slot 1), the user walked CJ into his house on both consoles (Xbox (2495.5, −1702.3, 1014.7) area 3; PS2 (2495.8, −1701.6, 1014.7)), clocks 12:00, then `timescale 0`. ColourFilter args c1 64,64,64,a128, c2 64,64,64,a254 (neutral). Files: `captures/cj_house_p3/`.
- **Interior radiosity limit `[0x6C88DC]` = 0 [C]**: every pixel passes, so H = clip(2D) and the bloom is a relative gain (≈ +27 % of 2D·35/255).
- PS2 radiosity on/off (55 % static px): on − off +5.3/+4.4/+3.9. Grid fit: **best L = 0, I = 35** (MAE 1.43, bias −0.6), next L = 10. So the PS2 uses the same interior limit 0 [C].
- Xbox P3 vs `model(off, 0)`: **100 % within ±2** (MAE 0.11; 71 % kept); P3 − off = +10.8/+9.5/+8.5.
- Same relative bloom on both consoles: blue wall 108 → 133 (PS2, ×1.23) vs 122 → 155 (Xbox, ×1.27); window +33 on both.
- **The absolute gap is upstream of P3 [C for this frame]:** before radiosity, the Xbox interior is already brighter in the shadows (median luminance 18 vs 8; floor 18/11/7 vs 6/1/0; mean 33.4 vs 27.7), matching the earlier "PS2 has much deeper shadows" interior result. At L = 0 radiosity scales that gap by ~1.3× (mean 35.0 PS2 vs 42.6 Xbox P3).
- **Consequence for Phase 5 [H]:** in this interior the Xbox is brighter in the darks than the PS2. That is the *opposite* of H5 (PS2 building ambient ×2 → brighter PS2 shadows, from the night-asphalt residual). P4 must be tested in both directions: interiors may use a different pipe/prelight path (the 11:11:10 night/day prelight packing, or a missing PS2 darkening), rather than a plain ambient ×2.
