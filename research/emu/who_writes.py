import sys, random
from elecdet import ElecDet
from probe_reads import ROM
from tracer import MN
cell = int(sys.argv[2].replace(':', ''), 16)
rnd = random.Random(int(sys.argv[1])); ed = ElecDet(ROM); cpu = ed.cpu
log = []; cur = [0]
ow, os_ = cpu._wr, cpu.step
def wr(a, v):
    if (a if a < 0x80 else 0x80 | (a & 15)) == cell and (not log or log[-1][2] != v):
        log.append((cpu.cycles, cur[0], v, cpu.a))
    ow(a, v)
def st():
    cur[0] = cpu.rom_address; os_()
cpu._wr, cpu.step = wr, st
ed.power_on(); ed.run_seconds(6.3 + rnd.random() * 4); ed.press('3'); ed.press('1')
log.append(('ENTER', 0, 0, 0))
ed.press('E', gap=0); ed.run_seconds(57)
log.append(('QUESTIONS', 0, 0, 0))
for s in (1, 2, 3):
    ed.keys('S%dE' % s); ed.run_seconds(1.5); ed.keys('Q13E'); ed.run_seconds(1); ed.press('T'); ed.run_seconds(0.5)
for c, pc, v, a in log[:40]:
    print(c, pc if isinstance(pc, int) and pc == 0 and c in ('ENTER', 'QUESTIONS') else '%X:%02X %s' % (pc >> 7, pc & 0x7f, MN.get(pc, '')), '->', v)
