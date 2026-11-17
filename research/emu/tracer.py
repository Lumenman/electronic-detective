"""Annotated instruction trace from the emulator: address, mnemonic, A/X/Y/status and RAM writes.
Usage in code:  with Tracer(ed, 'out.txt', pages={3,5}): ed.run(...)"""
import os, re

# made by ../dasm/tms0980_dasm.py from your ROM (not published: it is the ROM's program)
LISTING = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'dasm', 'listing.txt')
MN = {}
for line in open(LISTING):
    m = re.match(r'  ([0-9A-F]):([0-9A-F]{2})  [0-9A-F]{3}  (.*)', line)
    if m:
        MN[int(m.group(1), 16) << 7 | int(m.group(2), 16)] = m.group(3).split(';')[0].rstrip()


class Tracer:
    def __init__(self, ed, path, pages=None, limit=200000):
        self.ed, self.path, self.pages, self.limit = ed, path, pages, limit

    def __enter__(self):
        cpu = self.ed.cpu
        self.f = open(self.path, 'w')
        self.n = 0
        self.orig_step, self.orig_wr = cpu.step, cpu._wr
        writes = []

        def wr(addr, v):
            a = addr if addr < 0x80 else 0x80 | (addr & 0xf)
            writes.append('%X:%X<-%X' % (a >> 4, a & 15, v))
            self.orig_wr(addr, v)

        def step():
            pc = cpu.rom_address
            writes.clear()
            self.orig_step()
            if (self.pages is None or pc >> 7 in self.pages) and self.n < self.limit:
                self.n += 1
                self.f.write('%7d %X:%02X  %-14s A=%X X=%X Y=%X S=%d %s\n' % (
                    cpu.cycles, pc >> 7, pc & 0x7f, MN.get(pc, '?'), cpu.a, cpu.x, cpu.y, cpu.status,
                    ' '.join(writes)))
        cpu.step, cpu._wr = step, wr
        return self

    def __exit__(self, *exc):
        cpu = self.ed.cpu
        cpu.step, cpu._wr = self.orig_step, self.orig_wr
        self.f.close()
