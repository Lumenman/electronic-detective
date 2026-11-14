"""Which RAM bits decide the opposite-sex witness's fingerprint answer? Flip one bit at a time from a snapshot."""
import copy, random, sys
from elecdet import ElecDet
from probe_reads import ROM
from sweep import decode

seed = int(sys.argv[1]) if len(sys.argv) > 1 else 1
rnd = random.Random(seed); ed = ElecDet(ROM)
ed.power_on(); ed.run_seconds(6.3 + rnd.random() * 4)
ed.press('3'); ed.press('1'); ed.press('E', hold=0.08 + rnd.random() * 0.4, gap=0); ed.run_seconds(57)
d = decode([ed.cpu.ram[a] for a in range(0x90)])
M = d['murderer']; mw = d['murder_weapon']
wp = d['p38'] if mw == '.38' else d['p45']
q = 13 if mw == '.38' else 14
opp = [s for s in d['places'][wp]['occ'] if (s <= 10) != (M <= 10)]
print('murderer parity', 'odd' if M % 2 else 'even', 'opp witnesses', opp, 'q', q)


def ask(e, s):
    e.keys('S%dE' % s); e.run_seconds(1.5); e.keys('Q%dE' % q); e.run_seconds(1.0)
    return e.display().strip()


snap = copy.deepcopy(ed)
base = ask(copy.deepcopy(snap), opp[0])
print('baseline answer', base, '| other opp witness:', ask(copy.deepcopy(snap), opp[1]))
cells = [r << 4 | c for r in range(5) for c in range(6, 16)] if len(sys.argv) > 2 else list(range(0x50, 0x80)) + list(range(0x80, 0x90))
for c in cells:
    for b in range(4):
        e = copy.deepcopy(snap)
        e.cpu.ram[c] ^= 1 << b
        a = ask(e, opp[0])
        if a != base:
            print('flip %X:%X bit %d -> %s' % (c >> 4, c & 15, b, a))
