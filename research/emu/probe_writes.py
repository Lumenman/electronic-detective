"""Log which instructions write given RAM cells during crime setup (ENTER .. +5s)."""
import sys
from collections import Counter
from probe_reads import ROM
from elecdet import ElecDet
import random

cells = {int(c.replace(':', ''), 16) for c in sys.argv[2:]} if len(sys.argv) > 2 else {0x4c, 0x4d}
ed = ElecDet(ROM)
rnd = random.Random(int(sys.argv[1]) if len(sys.argv) > 1 else 1)
ed.power_on(); ed.run_seconds(6.3 + rnd.random() * 3)
ed.press('3'); ed.press('1')
cpu = ed.cpu
log = []
orig_wr = cpu._wr
def wr(addr, v):
    a = addr if addr < 0x80 else 0x80 | (addr & 0xf)
    if a in cells:
        pc = cpu.rom_address   # address of the *next* opcode; report the executing one below
        log.append((cpu.cycles, cur[0], a, v, cpu.a, cpu.x, cpu.y))
    orig_wr(addr, v)
cpu._wr = wr
cur = [0]
orig_step = cpu.step
def step():
    cur[0] = cpu.rom_address    # opcode being executed now was fetched from here
    orig_step()
cpu.step = step
ed.press('E', gap=0); ed.run_seconds(5)
seen = Counter()
for c, pc, a, v, A, X, Y in log:
    key = (pc, a)
    if seen[key] < 3:
        print(f'cyc {c:8d}  {pc >> 7:X}:{pc & 0x7f:02X}  RAM {a >> 4:X}:{a & 15:X} <- {v:X}   (A={A:X} X={X:X} Y={Y:X})')
    seen[key] += 1
print('writes per (pc,cell):', {f'{p >> 7:X}:{p & 0x7f:02X}@{a:02X}': n for (p, a), n in seen.items()})
print('final', ''.join('%x' % cpu.ram[a] for a in sorted(cells)), repr(ed.display()))
