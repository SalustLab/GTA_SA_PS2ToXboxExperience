"""iso_xdelta.py - xdelta (VCDIFF) patches for whole Xbox images when the mod only rewrites bytes in place.

Usage:
  py tools/iso_xdelta.py <stock.xiso> <mod.xiso> <out.xdelta> [--redump] [--name <patched file name>]
  py tools/iso_xdelta.py --selftest

<stock.xiso>/<mod.xiso> are the game partition (work/xbox/gtasa_stock.xiso / gtasa_v1.1.xiso). Every window copies
the source at the same offset and ADDs only the changed bytes, so the patch is a few KB. Each window carries
xdelta3's adler32 of its target bytes, so applying to a wrong image fails with a checksum error instead of writing
garbage.

--redump: the patch is for the full Redump image instead, i.e. 0x18300000 bytes of XGD2 video partition followed by
the same game partition. We don't need the video partition's bytes: its windows are plain same-offset copies without
a checksum, and the game partition windows keep theirs.
"""
import os
import sys
import zlib

VIDEO = 0x18300000          # XGD2 Redump: game partition offset (findings, Phase 0: gtasa_stock.xiso = ISO[VIDEO:])
WIN = 1 << 23               # xdelta3's default window size


def varint(v):
    out = [v & 0x7F]
    while v > 0x7F:
        v >>= 7
        out.append(0x80 | (v & 0x7F))
    return bytes(reversed(out))


def window(a, b, edits, cksum):
    """Target window [a, b) = source [a, b) with `edits` (sorted (offset, bytes), inside [a, b)) written over it."""
    data, inst, addr, pos = bytearray(), bytearray(), bytearray(), a
    for off, new in edits + [(b, b"")]:
        if off > pos:                                    # COPY from the source segment (mode 0 = VCD_SELF)
            inst += b"\x13" + varint(off - pos)          # code table entry 19: COPY size 0 mode 0
            addr += varint(pos - a)
        if new:
            inst += b"\x01" + varint(len(new))           # code table entry 1: ADD size 0
            data += new
        pos = off + len(new)
    body = varint(b - a) + b"\x00" + varint(len(data)) + varint(len(inst)) + varint(len(addr))
    body += (cksum.to_bytes(4, "big") if cksum is not None else b"") + data + inst + addr
    return bytes([1 | (4 if cksum is not None else 0)]) + varint(b - a) + varint(a) + varint(len(body)) + body


def diff(stock, mod, chunk=1 << 24):
    """Changed byte runs between two same-size files, as sorted (offset, new bytes)."""
    runs = []
    with open(stock, "rb") as fs, open(mod, "rb") as fm:
        pos = 0
        while True:
            x, y = fs.read(chunk), fm.read(chunk)
            assert len(x) == len(y), "images differ in size"
            if not x:
                return runs
            if x != y:
                i = 0
                while i < len(x):
                    if x[i] != y[i]:
                        j = i
                        while j < len(x) and x[j] != y[j]:
                            j += 1
                        if runs and runs[-1][0] + len(runs[-1][1]) == pos + i:   # run continues across a chunk
                            runs[-1] = (runs[-1][0], runs[-1][1] + y[i:j])
                        else:
                            runs.append((pos + i, y[i:j]))
                        i = j
                    else:
                        i += 1
            pos += len(x)


def build(stock, mod, out, redump=False, name="patched.iso", src_name="original.iso"):
    edits = diff(stock, mod)
    shift = VIDEO if redump else 0
    size = os.path.getsize(mod) + shift
    cuts = sorted(set(range(0, size, WIN)) | ({VIDEO} if redump else set())) + [size]
    app = f"{name}//{src_name}/".encode()
    with open(mod, "rb") as fm, open(out, "wb") as fo:
        fo.write(b"\xd6\xc3\xc4\x00\x04" + varint(len(app)) + app)               # VCDIFF, VCD_APPHEADER
        k = 0
        for a, b in zip(cuts, cuts[1:]):
            mine = []
            while k < len(edits) and edits[k][0] + shift < b:
                off, new = edits[k]
                lo, hi = max(off + shift, a), min(off + shift + len(new), b)
                mine.append((lo, new[lo - off - shift:hi - off - shift]))
                if off + shift + len(new) > b:                                   # edit spans the cut: keep the rest
                    edits[k] = (b - shift, new[b - off - shift:])
                    break
                k += 1
            cksum = None
            if a >= shift:                                                       # game partition: target is known
                fm.seek(a - shift)
                cksum = zlib.adler32(fm.read(b - a))
            fo.write(window(a, b, mine, cksum))
    return len(edits), os.path.getsize(out)


def selftest():
    import random
    import shutil
    import subprocess
    import tempfile
    assert varint(0) == b"\x00" and varint(127) == b"\x7f" and varint(128) == b"\x81\x00" and varint(16384) == b"\x81\x80\x00"
    global WIN, VIDEO
    WIN, VIDEO = 1000, 700                                                       # tiny geometry for the test
    rnd = random.Random(1)
    game = bytes(rnd.getrandbits(8) for _ in range(5000))
    mod = bytearray(game)
    for off in (0, 999, 1000, 2500, 4995):                                       # cut edges + file ends
        mod[off:off + 5] = b"PATCH"[:len(mod[off:off + 5])]
    exe = shutil.which("xdelta3") or next(iter(__import__("glob").glob("F:/Tools/xdelta/xdelta3*.exe")), None)
    with tempfile.TemporaryDirectory() as t:
        p = lambda n: os.path.join(t, n)
        open(p("s"), "wb").write(game); open(p("m"), "wb").write(mod)
        for redump in (False, True):
            build(p("s"), p("m"), p("x"), redump)
            video = bytes(rnd.getrandbits(8) for _ in range(VIDEO)) if redump else b""
            open(p("src"), "wb").write(video + game)
            if not exe:
                print("xdelta3 not found: decode checks skipped")
                continue
            subprocess.run([exe, "-d", "-f", "-s", p("src"), p("x"), p("o")], check=True)
            assert open(p("o"), "rb").read() == video + bytes(mod), redump
            open(p("bad"), "wb").write(video + game[:3000] + b"X" + game[3001:])   # wrong game partition byte
            bad = subprocess.run([exe, "-d", "-f", "-s", p("bad"), p("x"), p("o")], capture_output=True)
            assert bad.returncode != 0, "wrong source not rejected"
    print("iso_xdelta selftest OK")


if __name__ == "__main__":
    args = sys.argv[1:]
    if args in ([], ["--selftest"]):
        selftest()
    else:
        name = args[args.index("--name") + 1] if "--name" in args else "patched.iso"
        n, size = build(args[0], args[1], args[2], "--redump" in args, name)
        print(f"wrote {args[2]}: {n} edit runs, {size} bytes")
