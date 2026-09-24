"""Extract original-Xbox ISOs (XDVDFS filesystem).

7-Zip cannot read XDVDFS -- it misdetects the leading UDF stub and extracts
only a 13 MB VIDEO_TS fragment. This walks the XDVDFS binary-tree directory
tables instead.

Usage:
    py xdvdfs_extract.py <image.iso> [outdir] [--list]
"""
import os
import struct
import sys

SECTOR = 2048
SIG = b"MICROSOFT*XBOX*MEDIA"
RESERVED_SECTORS = 32  # signature lives at sector 32 of the partition
ATTR_DIRECTORY = 0x10


def find_partition_base(f, size):
    """Locate the XDVDFS signature; the partition starts 32 sectors before it."""
    chunk_size = 1 << 22
    overlap = RESERVED_SECTORS * SECTOR + len(SIG)
    pos = 0
    tail = b""
    while pos < size:
        f.seek(pos)
        chunk = f.read(min(chunk_size, size - pos))
        if not chunk:
            break
        buf = tail + chunk
        start = 0
        while True:
            i = buf.find(SIG, start)
            if i < 0:
                break
            absolute = pos - len(tail) + i
            base = absolute - RESERVED_SECTORS * SECTOR
            if base >= 0 and base % SECTOR == 0:
                return base
            start = i + 1
        tail = buf[-overlap:]
        pos += len(chunk)
    raise SystemExit("XDVDFS signature not found -- not an original-Xbox image?")


def read_table(f, base, sector, size):
    f.seek(base + sector * SECTOR)
    return f.read(size)


def walk_table(table):
    """Directory table is a binary search tree rooted at offset 0.

    Child pointers hold byte_offsets / 4 (verified against this image: the
    root's left=5 -> byte 20, right=27 -> byte 108, both real entries).
    """
    stack = [0]
    seen = set()
    while stack:
        off = stack.pop()
        if off in seen or off + 14 > len(table):
            continue
        seen.add(off)
        left, right, start, size, attr, namelen = struct.unpack_from("<HHIIBB", table, off)
        name = table[off + 14:off + 14 + namelen]
        if len(name) == namelen and name and all(32 <= b < 127 for b in name):
            yield name.decode("latin-1"), start, size, attr
        for child in (left, right):
            if child:
                stack.append(child * 4)


def walk_files(f, base, sector, size, prefix="", visited=None):
    """Yield (relative_path, start_sector, file_size) for every file."""
    if visited is None:
        visited = set()
    if (sector, size) in visited:  # ponytail: cycle guard; loops shouldn't exist but cost nothing
        return
    visited.add((sector, size))
    for name, start, fsize, attr in walk_table(read_table(f, base, sector, size)):
        path = prefix + name
        if attr & ATTR_DIRECTORY:
            yield from walk_files(f, base, start, fsize, path + "\\", visited)
        else:
            yield path, start, fsize


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    iso = sys.argv[1]
    list_only = "--list" in sys.argv
    outdir = next((a for a in sys.argv[2:] if not a.startswith("--")),
                  os.path.splitext(iso)[0])

    with open(iso, "rb") as f:
        f.seek(0, 2)
        size = f.tell()
        base = find_partition_base(f, size)
        sig_off = base + RESERVED_SECTORS * SECTOR
        f.seek(sig_off + len(SIG))
        root_sector, root_size = struct.unpack("<II", f.read(8))
        print(f"partition base: {base} (sector {base // SECTOR})")
        print(f"root: sector {root_sector}, {root_size} bytes")

        files = list(walk_files(f, base, root_sector, root_size))
        total = sum(s for _, _, s in files)
        print(f"{len(files)} files, {total} bytes")

        if list_only:
            for path, start, fsize in files:
                print(f"  {start:>8} {fsize:>12}  {path}")
            return

        written = 0
        for path, start, fsize in files:
            dest = os.path.join(outdir, path)
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            f.seek(base + start * SECTOR)
            remaining = fsize
            with open(dest, "wb") as out:
                while remaining:
                    block = f.read(min(1 << 20, remaining))
                    if not block:
                        raise SystemExit(f"short read on {path}")
                    out.write(block)
                    remaining -= len(block)
            written += fsize
        print(f"extracted {len(files)} files, {written} bytes -> {outdir}")

    # self-check: the boot executable must exist at the root and be a real PE
    xbe = os.path.join(outdir, "default.xbe")
    assert os.path.exists(xbe), "default.xbe missing at image root"
    with open(xbe, "rb") as fh:
        assert fh.read(4) == b"XBEH", "default.xbe is not a valid XBE"
    assert written == total, "bytes written != bytes listed"
    print("self-check ok: default.xbe present and valid")


if __name__ == "__main__":
    main()
