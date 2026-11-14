import sys
from elecdet import ElecDet
from tracer import Tracer
from probe_reads import ROM
from sweep import decode
import random
seed = int(sys.argv[1]) if len(sys.argv) > 1 else 1
rnd = random.Random(seed); ed = ElecDet(ROM)
ed.power_on(); ed.run_seconds(6.3 + rnd.random() * 4)
ed.press('3'); ed.press('1'); ed.press('E', hold=0.08 + rnd.random() * 0.4, gap=0); ed.run_seconds(5)
d = decode([ed.cpu.ram[a] for a in range(0x90)])
M = d['murderer']; wp = d['p38'] if d['murder_weapon'] == '.38' else d['p45']
q = 13 if d['murder_weapon'] == '.38' else 14
opp = [s for s in d['places'][wp]['occ'] if (s <= 10) != (M <= 10)]
same = [s for s in d['places'][wp]['occ'] if (s <= 10) == (M <= 10)]
ed.run_seconds(52)
for tag, s in (('opp', opp[0]), ('same', same[0])):
    ed.keys('S%dE' % s); ed.run_seconds(1.5)
    with Tracer(ed, 'prints_%s.txt' % tag, pages={2, 3, 4, 6, 7, 8, 9, 10, 11, 12}):
        ed.keys('Q%dE' % q); ed.run_seconds(1.0)
    print(tag, s, 'answer', repr(ed.display()), 'truth odd' if M % 2 else 'truth even')
    ed.press('T'); ed.run_seconds(1)
print('dam', ''.join('%x' % ed.cpu.ram[a] for a in range(0x80, 0x90)))
