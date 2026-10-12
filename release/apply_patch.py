"""PS2 Atmosphere installer for GTA San Andreas (Xbox, USA Rev 1).

Patches default.xbe with default.xbe.xdelta and sets five stream.ini lines.

Usage:
    py apply_patch.py <game folder | image.iso>  [--xdelta path\\to\\xdelta3.exe]
    py apply_patch.py --selftest

A game folder must hold default.xbe and stream.ini; an .iso / .xiso is patched in place.
Either way the originals are kept as *.bak first (an existing .bak is never replaced).
Any input other than the USA Rev 1 files is refused and nothing is written.
"""
import glob
import hashlib
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(HERE))  # repo layout: xdvdfs_extract.py sits one level up
from xdvdfs_extract import SECTOR, image_files  # noqa: E402

XBE = ("10efb868f13d6944aa6684a52cac5156393f14c5", "2d1829b5647f05930290d6e56425a4b656b8937b")
INI = ("67732726ca17071fd28dee4e3f50469ac2a737d8", "dda7e8889cc64329b18bfde4ecdfa93effbf62de")
# Same-length swaps keep stream.ini at 197 B so an image can be patched in place.
# devkit_memory repeats memory 38000 on retail, so its line becomes pe_bRadiosity.
INI_EDITS = [
    (b"devkit_memory\t38000", b"pe_bRadiosity\t\t\t\t\t1"),
    (b"pe_leftx\t16", b"pe_leftx\t\t8"),
    (b"pe_topy\t\t16", b"pe_topy\t\t\t8"),
    (b"pe_rightx\t16", b"pe_rightx\t\t8"),
    (b"pe_bottomy\t16", b"pe_bottomy\t\t8"),
]


def sha1(data):
    return hashlib.sha1(data).hexdigest()


def find_xdelta(arg):
    found = [arg] if arg else glob.glob(os.path.join(HERE, "xdelta3*")) + [shutil.which("xdelta3")]
    exe = next((p for p in found if p and os.path.isfile(p)), None)
    if not exe:
        raise SystemExit("xdelta3 not found: put xdelta3.exe next to this script or pass --xdelta <path>")
    return exe


def xdelta_decode(exe, xbe):
    with tempfile.TemporaryDirectory() as tmp:
        src, out = os.path.join(tmp, "in.xbe"), os.path.join(tmp, "out.xbe")
        with open(src, "wb") as f:
            f.write(xbe)
        subprocess.run([exe, "-d", "-f", "-s", src, os.path.join(HERE, "default.xbe.xdelta"), out], check=True)
        with open(out, "rb") as f:
            return f.read()


def patch_ini(ini):
    for old, new in INI_EDITS:
        ini = ini.replace(old, new, 1)
    return ini


def backup(path):
    """Copy path to path.bak once; the copy goes through .part so a failed copy never looks like a backup."""
    if not os.path.exists(path + ".bak"):
        shutil.copyfile(path, path + ".bak.part")
        os.replace(path + ".bak.part", path + ".bak")


def patched(name, data, hashes, fn):
    """New bytes for one file, None if it is already patched; exits on any mismatch."""
    stock, mod = hashes
    have = sha1(data)
    if have == mod:
        print(f"{name}: already patched")
        return None
    if have != stock:
        raise SystemExit(f"{name}: SHA1 {have} is not GTA SA USA Rev 1 ({stock}); nothing written")
    new = fn(data)
    if sha1(new) != mod or len(new) != len(data):
        raise SystemExit(f"{name}: patch result has SHA1 {sha1(new)}, expected {mod}; nothing written")
    return new


def run(target, exe):
    names = ("default.xbe", "stream.ini")
    jobs = ((XBE, lambda d: xdelta_decode(exe, d)), (INI, patch_ini))
    if os.path.isdir(target):
        paths = [os.path.join(target, n) for n in names]
        olds = []
        for p in paths:
            with open(p, "rb") as f:
                olds.append(f.read())
        news = [patched(n, d, h, fn) for n, d, (h, fn) in zip(names, olds, jobs)]  # both checked before any write
        for p, new in zip(paths, news):
            if new is None:
                continue
            backup(p)
            with open(p, "wb") as f:
                f.write(new)
            print(f"patched {p}")
        return
    with open(target, "rb") as f:
        base, files = image_files(f)
        where = {path.lower(): (base + start * SECTOR, size) for path, start, size in files}
        olds = []
        for n in names:
            if n not in where:
                raise SystemExit(f"{n} not found at the image root; nothing written")
            off, size = where[n]
            f.seek(off)
            olds.append(f.read(size))
    news = [patched(n, d, h, fn) for n, d, (h, fn) in zip(names, olds, jobs)]
    if news == [None, None]:
        return
    print(f"backing up {target} -> {target}.bak (needs as much free space as the image)")
    backup(target)
    with open(target, "r+b") as f:
        for n, new in zip(names, news):
            if new is not None:
                f.seek(where[n][0])
                f.write(new)
                print(f"patched {n} inside {target}")


def selftest():
    for old, new in INI_EDITS:
        assert len(old) == len(new), old
    assert patch_ini(b"pe_leftx\t16\r\npe_leftx\t16") == b"pe_leftx\t\t8\r\npe_leftx\t16"
    h = (sha1(b"stock"), sha1(b"mod!!"))
    assert patched("t", b"stock", h, lambda d: b"mod!!") == b"mod!!"
    assert patched("t", b"mod!!", h, lambda d: 1 / 0) is None            # already patched: fn not called
    for data, fn in ((b"other", lambda d: b"mod!!"),                      # wrong input
                     (b"stock", lambda d: b"bad!!")):                     # wrong result
        try:
            patched("t", data, h, fn)
            raise AssertionError("not refused")
        except SystemExit:
            pass
    with tempfile.TemporaryDirectory() as tmp:
        p = os.path.join(tmp, "game.iso")
        for content in (b"stock", b"mod!!"):
            with open(p, "wb") as f:
                f.write(content)
            backup(p)
        with open(p + ".bak", "rb") as f:
            assert f.read() == b"stock"                                   # an existing backup is never replaced
        assert os.listdir(tmp) == ["game.iso", "game.iso.bak"]            # no .part left behind
    print("apply_patch selftest OK")


if __name__ == "__main__":
    args = sys.argv[1:]
    if args in ([], ["--selftest"]):
        selftest()
    else:
        exe = args[args.index("--xdelta") + 1] if "--xdelta" in args else None
        run(args[0], find_xdelta(exe))
