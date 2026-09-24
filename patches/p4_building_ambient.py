"""P4 - PS2 building ambient (PLAN §9 P4, H5; findings 2026-09-24 "Phase 5").

Every Xbox building vertex shader lights with (decoded, 8 blobs 0x3C9B18..0x3CA270)
  oD0.rgb = prelight*c20 + c15*c21        c20 = matCol*surfDiff, c21 = matCol*surfAmb, c15 = ambient light (<= 1)
The PS2 adds the ambient at ~2x (SkyGfx ps2BuildingVS: ambient*surfAmb, then colour x255/128 in the pixel stage;
live sweep: PS2/Xbox ambient response 1.7-1.8, texture-free ratio 0.47-0.54 vs 0.502 predicted).

c15 is built per frame in the pipe setup functions from the pAmbient light [0x5F4BFC]+0x18, clamped to 1 with an
86-byte comiss/ja block. P4 rewrites those blocks in place: c15 = min(pAmbient, 1), then xyz x2 (w unchanged):
  0x166D91  setup 0x166C70 (building pipe, VS [0x5F291C])                        -> always x2
  0x167700  setup 0x1675DF (building DN pipe 0x53F20096, VS [0x5F2928])        -> always x2
  0x16A30A  setup 0x16A1E5, shared with the vehicle/unlit pipes (VS [0x5F2960], [0x5F2984])
            -> x2 only when RW's current VS [0x3D4750] is a building one ([0x5F2934] / [0x5F2940])
A VS operand edit is not possible: each blob's `mov r, c[15]` shares its operand C with a paired ILU `mov oT0, ...`.
Not reproduced: PS2 overbright (the VS output still clamps at 1), SkyGfx's dropped matCol/surfDiff factors.

Usage: py patches/p4_building_ambient.py [--selftest]      -> writes patches/p4_building_ambient.json
"""
import hashlib
import json
import sys
from pathlib import Path

from capstone import CS_ARCH_X86, CS_MODE_32, Cs
from keystone import KS_ARCH_X86, KS_MODE_32, Ks

XBE = Path(__file__).resolve().parents[1] / "work" / "xbox" / "default.xbe"
P_AMBIENT, RW_CUR_VS = 0x5F4BFC, 0x3D4750
BUILDING_VS_SHARED = (0x5F2934, 0x5F2940)        # handles that reach the shared setup 0x16A1E5 from building pipes
BLOCKS = ((0x166D91, 0x166DE7, "ebp + 0x54", False),   # (start, end, c15 stack slot, shared -> check the VS)
          (0x167700, 0x167756, "ebp + 0x54", False),
          (0x16A30A, 0x16A360, "ebp - 0x20", True))


def text(xbe, va, n):
    return xbe[va - 0x10000:va - 0x10000 + n]


def stock_ok(xbe, start, end, slot):
    """The stock block: mov ecx,[pAmbient]; 4x (movss xmm0,[ecx+0x18+4k]; comiss xmm4,xmm0; movss [slot+4k],xmm0; ja; movss [slot+4k],xmm4)."""
    ins = list(Cs(CS_ARCH_X86, CS_MODE_32).disasm(text(xbe, start, end - start), start))
    assert sum(i.size for i in ins) == end - start and len(ins) == 21, hex(start)
    assert (ins[0].mnemonic, ins[0].op_str) == ("mov", f"ecx, dword ptr [{P_AMBIENT:#x}]"), ins[0].op_str
    base = int(slot.split()[-1], 16) * (-1 if "-" in slot else 1)
    for k in range(4):
        ld, cmp, st, ja, st1 = ins[1 + 5 * k:6 + 5 * k]
        disp = lambda d: f"ebp {'+' if d >= 0 else '-'} {abs(d):#x}"
        assert ld.op_str == f"xmm0, dword ptr [ecx + {0x18 + 4 * k:#x}]" and cmp.op_str == "xmm4, xmm0", hex(ld.address)
        assert st.op_str == f"dword ptr [{disp(base + 4 * k)}], xmm0" and ja.mnemonic == "ja", hex(st.address)
        assert st1.op_str == f"dword ptr [{disp(base + 4 * k)}], xmm4", hex(st1.address)
    nxt = next(Cs(CS_ARCH_X86, CS_MODE_32).disasm(text(xbe, end, 3), end))
    assert (nxt.mnemonic, nxt.op_str) == ("mov", "eax, dword ptr [eax + 4]"), nxt.op_str   # eax = pDirect, kept


def build(start, end, slot, shared):
    check = "".join(f"cmp edx, dword ptr [{h:#x}]; je dbl; " for h in BUILDING_VS_SHARED)
    asm = (f"mov ecx, dword ptr [{P_AMBIENT:#x}]; movups xmm0, [ecx + 0x18];"
           f"movaps xmm2, xmm4; shufps xmm2, xmm2, 0; minps xmm0, xmm2; movups [{slot}], xmm0;"   # xmm4 = (1,0,0,0)
           + (f"mov edx, dword ptr [{RW_CUR_VS:#x}]; {check}jmp done;" if shared else "")
           + f"dbl: addps xmm0, xmm0; movlps qword ptr [{slot}], xmm0; unpckhps xmm0, xmm0;"
           f"movss dword ptr [{slot} + 8], xmm0; done: jmp {end:#x}")
    code = bytes(Ks(KS_ARCH_X86, KS_MODE_32).asm(asm, start)[0])
    assert len(code) <= end - start, (hex(start), len(code))
    return code + b"\xcc" * (end - start - len(code))


def patches(xbe):
    out = []
    for start, end, slot, shared in BLOCKS:
        stock_ok(xbe, start, end, slot)
        new = build(start, end, slot, shared)
        out.append({"va": hex(start), "orig_sha1": hashlib.sha1(text(xbe, start, end - start)).hexdigest(),
                    "len": end - start, "new": new.hex(),
                    "note": f"c15 = min(pAmbient,1), xyz x2{' if RW VS is a building one' if shared else ''}"})
    return out


def selftest():
    xbe = XBE.read_bytes()
    md = Cs(CS_ARCH_X86, CS_MODE_32)
    for (start, end, slot, shared), e in zip(BLOCKS, patches(xbe)):
        new = bytes.fromhex(e["new"])
        ins = list(md.disasm(new.rstrip(b"\xcc"), start))
        assert sum(i.size for i in ins) == len(new.rstrip(b"\xcc")), hex(start)
        ops = [(i.mnemonic, i.op_str) for i in ins]
        assert ops[-1] == ("jmp", f"{end:#x}")
        assert ("minps", "xmm0, xmm2") in ops and ("addps", "xmm0, xmm0") in ops
        assert not any("eax" in o or "xmm4" in o.split(", ")[0] for _, o in ops), "eax (pDirect) and xmm4 (1.0) must survive"
        assert (("mov", f"edx, dword ptr [{RW_CUR_VS:#x}]") in ops) == shared
    print("p4_building_ambient selftest OK")


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        selftest()
        sys.exit()
    out = {"name": "P4 PS2 building ambient (c15 x2 in the building pipe setups)", "patches": patches(XBE.read_bytes())}
    Path(__file__).with_suffix(".json").write_text(json.dumps(out, indent=2))
    print(f"{len(out['patches'])} blocks; wrote {Path(__file__).with_suffix('.json').name}")
