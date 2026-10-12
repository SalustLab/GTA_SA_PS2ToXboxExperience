"""P7 - the PS2 stream.ini settings become the XBE defaults, so the stock stream.ini needs no edit (findings
2026-10-12, "P7").

The stream.ini parser (0x157F..) handles each key with atoi + a store. Two settings matter for the mod:
  pe_leftx/rightx/topy/bottomy -> mov [0x3CE808/0C/10/14], eax   (.data default is already 8 = PS2; the stock ini
                                                                   writes 16). P7 NOPs the four stores.
  pe_bRadiosity                -> setne al; mov [0x5F4B1C], al    (BSS byte, 0 at boot; the stock ini has no line).
                                  Its only reader is the guard `cmp byte [0x5F4B1C], 0; je skip` at 0x24CD43.
P7 inverts both ends (sete / jne): the byte now means "radiosity off". So radiosity is on with no line or with
`pe_bRadiosity 1` (the v1.0 ini), and `pe_bRadiosity 0` still turns it off.

Usage: py patches/p7_ini_defaults.py [--selftest]      -> writes patches/p7_ini_defaults.json
"""
import hashlib
import json
import sys
from pathlib import Path

from capstone import CS_ARCH_X86, CS_MODE_32, Cs

XBE = Path(__file__).resolve().parents[1] / "work" / "xbox" / "default.xbe"
TEXT = 0x10000                                   # .text file offset = VA - 0x10000
# (va, stock bytes, new bytes, note)
EDITS = [(va, bytes.fromhex(old), bytes.fromhex(new), note) for va, old, new, note in (
    (0x158063, "a308e83c00", "9090909090", "pe_leftx handler: drop mov [0x3CE808], eax (keep .data 8)"),
    (0x158084, "a30ce83c00", "9090909090", "pe_rightx handler: drop mov [0x3CE80C], eax (keep .data 8)"),
    (0x1580A2, "a310e83c00", "9090909090", "pe_topy handler: drop mov [0x3CE810], eax (keep .data 8)"),
    (0x1580C0, "a314e83c00", "9090909090", "pe_bottomy handler: drop mov [0x3CE814], eax (keep .data 8)"),
    (0x1580E1, "95", "94", "pe_bRadiosity handler: setne al -> sete al ([0x5F4B1C] = radiosity off)"),
    (0x24CD4A, "74", "75", "radiosity guard: je skip -> jne skip (runs while [0x5F4B1C] == 0)"),
)]


def radiosity_runs(ini_value):
    """Patched semantics: None = no pe_bRadiosity line (BSS 0)."""
    flag = 0 if ini_value is None else int(ini_value == 0)       # sete al after atoi
    return flag == 0                                             # jne skip


def selftest():
    assert radiosity_runs(None) and radiosity_runs(1) and not radiosity_runs(0)
    md = Cs(CS_ARCH_X86, CS_MODE_32)
    # the 1-byte edits land on the opcode bytes: decode the whole patched instructions
    assert next(md.disasm(bytes.fromhex("0f94c0"), 0x1580E0)).mnemonic == "sete"
    j = next(md.disasm(bytes.fromhex("7539"), 0x24CD4A))
    assert (j.mnemonic, j.op_str) == ("jne", "0x24cd85")         # same target as the stock je
    for va, old, new, _ in EDITS:
        assert len(old) == len(new), hex(va)
    print("p7_ini_defaults selftest OK")


if __name__ == "__main__":
    if sys.argv[1:] == ["--selftest"]:
        selftest()
        sys.exit()
    xbe = XBE.read_bytes()
    for va, old, _, _ in EDITS:
        assert xbe[va - TEXT:va - TEXT + len(old)] == old, hex(va)
    out = {"name": "P7 PS2 stream.ini settings as XBE defaults (pe stays 8, radiosity on unless pe_bRadiosity 0)",
           "requires": ["p2_filterblur", "p3_radiosity"],
           "patches": [{"va": hex(va), "orig_sha1": hashlib.sha1(old).hexdigest(), "len": len(old),
                        "new": new.hex(), "note": note} for va, old, new, note in EDITS]}
    Path(__file__).with_suffix(".json").write_text(json.dumps(out, indent=2))
    print(f"wrote {Path(__file__).with_suffix('.json').name}")
