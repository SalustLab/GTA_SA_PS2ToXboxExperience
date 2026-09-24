"""P1 - CPostEffects::ColourFilter with the PS2 formula (PLAN §9, findings 2026-09-24).

  PS2: out = clip(fb*2c1) + clip(fb*2c2) * a2      (a2 = in-memory alpha, already x2 by the loader)

The stock "k ~= 0.585" dilution is not a draw property: it is the Xbox-only blur pass 0x24ECAA, which lerps the
pre-filter copy over the result twice at alpha 60 ((1 - 60/255)^2 = 0.585). P1 switches it off (data byte
0x3CE7AD 1 -> 0), so k defaults to 1. Both passes run stage-0 COLOROP = MODULATE2X with vertex colour c * S, S = 2/(mult*k) = 1 for k = 1,

  pass 1  ONE/ZERO      -> clip(4k*fb*c1*S) = clip(fb*2c1)
  pass 2  SRCALPHA/ONE  -> + clip(fb*2c2) * a2
The colour op is written only to the D3D deferred state (0x36BBF8 + dirty 0x800); RW's 2D setup 0x2AB710 leaves
it alone while its cache 0x75D5A0 stays 4. It is restored to MODULATE before returning (HUD).

Usage: py patches/p1_colourfilter.py [k]      -> writes patches/p1_colourfilter.json
"""
import hashlib
import json
import sys
from pathlib import Path

from keystone import KS_ARCH_X86, KS_MODE_32, Ks

START, END = 0x24F007, 0x24F133            # original function, 300 bytes (ret at 0x24F132)
XBE = Path(__file__).resolve().parents[1] / "work" / "xbox" / "default.xbe"


BLUR_ENABLE = 0x3CE7AD                     # .data byte, 1 in the stock XBE; gates the blur pass 0x24ECAA


def build(k=1.0):
    mult, op = (2, 5) if k >= 1 else (4, 6)   # MODULATE2X is exact for k = 1; 4X only to compensate k < 1
    s = round(256 * 2 / (mult * k))         # colour scale, fixed point /256 (256 = colour as-is)
    asm = f"""
        push ebp
        mov ebp, esp
        push ebx
        push esi
        push edi
        xor ebx, ebx
        inc ebx
        xor esi, esi
        mov edi, dword ptr [0x75de80]       # RwRenderStateSet, callee-saved register
        push ebx
        push 9
        call edi           # filter NEAREST
        push esi
        push 0xe
        call edi           # fog off
        push esi
        push 6
        call edi           # ztest off
        push esi
        push 8
        call edi           # zwrite off
        push dword ptr [0x5f4b28]
        push ebx
        call edi           # raster = fb copy
        push ebx
        push 0xc
        call edi           # vertex alpha on
        push 2
        push 0xa
        call edi           # src ONE
        push 1
        push 0xb
        call edi           # dst ZERO
        add esp, 0x40
        mov dword ptr [0x36bbf8], {op}      # stage0 COLOROP = MODULATE2X/4X (D3D only)
        or dword ptr [0x36e280], 0x800
        lea esi, [ebp + 8]
        mov dl, 0xff
        call pack_draw                      # pass 1: c1*S, A=FF
        push 5
        push 0xa
        call edi           # src SRCALPHA
        push 2
        push 0xb
        call edi           # dst ONE
        add esp, 0x10
        lea esi, [ebp + 0xc]
        mov dl, byte ptr [ebp + 0xf]
        call pack_draw                      # pass 2: c2*S, A=a2
        mov dword ptr [0x36bbf8], 4         # restore MODULATE
        or dword ptr [0x36e280], 0x800
        push 2
        push 9
        call edi           # original restore tail
        push ebx
        push 6
        call edi
        push ebx
        push 8
        call edi
        push 0
        push ebx
        call edi
        push 5
        push 0xa
        call edi
        push 6
        push 0xb
        call edi
        add esp, 0x30
        pop edi
        pop esi
        pop ebx
        pop ebp
        ret
    pack_draw:                              # esi -> R,G,B bytes, dl = alpha
        movzx edx, dl
        mov ecx, 3
    chan:
        shl edx, 8
        movzx eax, byte ptr [esi]
        imul eax, eax, {s}
        add eax, 0x80                       # round, don't truncate
        shr eax, 8
        or edx, eax
        inc esi
        loop chan
        mov dword ptr [0x5c7328], edx
        mov dword ptr [0x5c7344], edx
        mov dword ptr [0x5c7360], edx
        mov dword ptr [0x5c737c], edx
        push 6
        push 0x3ce82c
        push 4
        push 0x5c7318
        push 3
        call dword ptr [0x75de94]           # Im2DRenderIndexedPrimitive
        add esp, 0x14
        ret
    """
    code, _ = Ks(KS_ARCH_X86, KS_MODE_32).asm(asm, START)
    code = bytes(code)
    assert len(code) <= END - START, f"{len(code)} bytes > {END - START}"
    return code + b"\xcc" * (END - START - len(code)), s


if __name__ == "__main__":
    k = float(sys.argv[1]) if len(sys.argv) > 1 else 1.0
    new, s = build(k)
    xbe = XBE.read_bytes()
    orig = xbe[START - 0x10000:END - 0x10000]
    blur = xbe[BLUR_ENABLE - 0xFB60:BLUR_ENABLE - 0xFB60 + 1]
    out = {"name": f"P1 ColourFilter PS2 formula (k={k}, S={s}/256) + Xbox blur pass off",
           "patches": [{"va": hex(START), "orig_sha1": hashlib.sha1(orig).hexdigest(), "len": len(orig),
                        "new": new.hex(), "note": "full rewrite of CPostEffects::ColourFilter 0x24F007-0x24F132"},
                       {"va": hex(BLUR_ENABLE), "orig_sha1": hashlib.sha1(blur).hexdigest(), "len": 1,
                        "new": "00", "note": "disable the Xbox blur pass 0x24ECAA (re-adds the pre-filter frame)"}]}
    Path(__file__).with_suffix(".json").write_text(json.dumps(out, indent=2))
    print(f"{len(new.rstrip(bytes([0xcc])))} code bytes / {len(new)}; S={s}; wrote {Path(__file__).with_suffix('.json').name}")
