"""Poke/read GTA SA PS2 (SLUS-20946 v3.00) state in PCSX2 through PINE (Settings > Advanced > Enable PINE, port 28011).

Usage:
  py tools/pcsx2_pine.py clock <hour> <minute>                  set + freeze (ms-per-minute = 0x7FFFFFFF)
  py tools/pcsx2_pine.py weather <id>                           Old=New=Forced=id
  py tools/pcsx2_pine.py teleport <x> <y> <z> [heading_rad]     player ped (or its vehicle) matrix position
  py tools/pcsx2_pine.py timescale <f>                          CTimer::ms_fTimeScale; 0 freezes the world
  py tools/pcsx2_pine.py idlecam off|on                         CIdleCam kick-in time 1e30 / stock 90000 ms
  py tools/pcsx2_pine.py where                                 player position + ped floats (heading search)
  py tools/pcsx2_pine.py capture <out.png> [title]              PrintWindow of the PCSX2 game window
  py tools/pcsx2_pine.py --selftest

Addresses: docs/findings.md "RE target 6" ($gp = 0x66B870).
"""
import socket
import struct
import sys

CLOCK_HOURS, CLOCK_MINUTES, CLOCK_SECONDS = 0x66BF2C, 0x66BF30, 0x66BF34
MS_PER_GAME_MINUTE = 0x66BF1C
WEATHER_OLD, WEATHER_NEW, WEATHER_FORCED = 0x66C4A4, 0x66C4A8, 0x66C4AC
PLAYERS = 0x70A160                      # CWorld::Players[0].m_pPed (stride 0x1BC)
TIME_SCALE = 0x66C1A8                   # CTimer::ms_fTimeScale (0x938($gp)); 0 stops the clock, tested live
IDLECAM_KICKIN = 0x6FFE48               # gIdleCam 0x6FFE20 +0x28 (same layout as Xbox 0x6C5248) [C], tested live
PED_HEADING = (0x598, 0x59C)          # current, aiming [S]: Xbox +0x558/+0x55C shifted by 0x40 like m_pVehicle

READ8, READ32, WRITE8, WRITE16, WRITE32 = 0, 2, 4, 5, 6


class Pine:
    def __init__(self, port=28011):
        self.s = socket.create_connection(("127.0.0.1", port), timeout=5)

    def _call(self, op, payload, reply_len):
        msg = bytes([op]) + payload
        self.s.sendall(struct.pack("<I", len(msg) + 4) + msg)
        want, data = 5 + reply_len, b""
        while len(data) < want:
            chunk = self.s.recv(want - len(data))
            if not chunk:
                raise IOError("PINE closed")
            data += chunk
        if data[4] != 0:
            raise IOError(f"PINE op {op} failed")
        return data[5:]

    def read(self, addr, n):                                      # n = 1 or 4
        return self._call(READ8 if n == 1 else READ32, struct.pack("<I", addr), n)

    def u32(self, addr):
        return struct.unpack("<I", self.read(addr, 4))[0]

    def f32(self, addr):
        return struct.unpack("<f", self.read(addr, 4))[0]

    def write(self, addr, data):
        op = {1: WRITE8, 2: WRITE16, 4: WRITE32}[len(data)]
        self._call(op, struct.pack("<I", addr) + data, 0)


def player_entity(p):
    ped = p.u32(PLAYERS)
    if p.read(ped + 0x4A5, 1)[0] & 1 and p.u32(ped + 0x5CC):
        return ped, p.u32(ped + 0x5CC)
    return ped, ped


def run(p, args):
    op = args[0]
    if op == "clock":
        p.write(MS_PER_GAME_MINUTE, struct.pack("<i", 0x7FFFFFFF))
        p.write(CLOCK_HOURS, bytes([int(args[1])]))
        p.write(CLOCK_MINUTES, bytes([int(args[2])]))
        p.write(CLOCK_SECONDS, struct.pack("<H", 0))
    elif op == "weather":
        for a in (WEATHER_FORCED, WEATHER_NEW, WEATHER_OLD):
            p.write(a, struct.pack("<h", int(args[1])))
    elif op == "teleport":
        ped, ent = player_entity(p)
        mat = p.u32(ent + 0x14)
        base = mat + 0x30 if mat else ent + 4
        for i, v in enumerate(args[1:4]):
            p.write(base + 4 * i, struct.pack("<f", float(v)))
        if len(args) > 4 and ent == ped:
            for o in PED_HEADING:
                p.write(ped + o, struct.pack("<f", float(args[4])))
    elif op == "timescale":
        p.write(TIME_SCALE, struct.pack("<f", float(args[1])))
    elif op == "idlecam":
        p.write(IDLECAM_KICKIN, struct.pack("<f", 90000.0 if args[1] == "on" else 1e30))
    elif op == "where":
        ped, ent = player_entity(p)
        mat = p.u32(ent + 0x14)
        pos = [p.f32((mat + 0x30 if mat else ent + 4) + 4 * i) for i in range(3)]
        floats = {o: p.f32(ped + o) for o in range(0x500, 0x640, 4)}
        angles = " ".join(f"+{o:#x}={v:.3f}" for o, v in floats.items() if 0.001 < abs(v) < 6.3)
        return f"ped={ped:#x} pos=({pos[0]:.2f}, {pos[1]:.2f}, {pos[2]:.2f})\nangle-like ped floats: {angles}"
    else:
        raise SystemExit(__doc__)
    return "ok"


def selftest():
    import threading
    mem = bytearray(0x800000)
    srv = socket.socket()
    srv.bind(("127.0.0.1", 0))
    srv.listen(1)

    def stub():
        c, _ = srv.accept()
        while True:
            head = c.recv(4)
            if len(head) < 4:
                return
            body = c.recv(struct.unpack("<I", head)[0] - 4)
            op, addr = body[0], struct.unpack_from("<I", body, 1)[0]
            if op in (READ8, READ32):
                n = 1 if op == READ8 else 4
                out = bytes([0]) + bytes(mem[addr:addr + n])
            else:
                data = body[5:]
                mem[addr:addr + len(data)] = data
                out = bytes([0])
            c.sendall(struct.pack("<I", len(out) + 4) + out)

    threading.Thread(target=stub, daemon=True).start()
    ped, mat = 0x700000, 0x710000
    struct.pack_into("<I", mem, PLAYERS, ped)
    struct.pack_into("<I", mem, ped + 0x14, mat)
    p = Pine(srv.getsockname()[1])
    run(p, ["clock", "12", "0"])
    assert mem[CLOCK_HOURS] == 12 and struct.unpack_from("<i", mem, MS_PER_GAME_MINUTE)[0] == 0x7FFFFFFF
    run(p, ["weather", "1"])
    assert all(struct.unpack_from("<h", mem, a)[0] == 1 for a in (WEATHER_OLD, WEATHER_NEW, WEATHER_FORCED))
    run(p, ["teleport", "2489.25", "-1667", "13.25", "-1.5"])
    assert struct.unpack_from("<3f", mem, mat + 0x30) == (2489.25, -1667.0, 13.25)
    assert struct.unpack_from("<2f", mem, ped + PED_HEADING[0]) == (-1.5, -1.5)
    assert "pos=(2489.25, -1667.00, 13.25)" in run(p, ["where"])
    run(p, ["idlecam", "off"])
    assert struct.unpack_from("<f", mem, IDLECAM_KICKIN)[0] > 1e29
    print("pcsx2_pine selftest OK")


if __name__ == "__main__":
    args = sys.argv[1:]
    if args in ([], ["--selftest"]):
        selftest()
    elif args[0] == "capture" and len(args) in (2, 3):
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).parent))
        from xemu_gdb import capture
        print(capture(args[1], args[2] if len(args) == 3 else "Grand Theft Auto"))
    else:
        print(run(Pine(), args))
