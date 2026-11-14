"""Column 0 after the tumbler stops, for different key sequences before ENTER."""
import sys, random, copy
sys.path.insert(0, r'D:\claude\GAMES\electronic_detective\research\emu')
from collections import Counter
from multiprocessing import Pool
from elecdet import ElecDet
from probe_reads import ROM
VAR = ['31E', '3E', '311E', '32E', 'T31E', '3T1E', '1E', '34E']
def run(var):
    base = ElecDet(ROM); base.power_on(); base.run_seconds(6.3)
    rnd = random.Random(var); res = Counter(); m = Counter()
    for i in range(60):
        ed = copy.deepcopy(base); ed.run_seconds(rnd.random() * 0.7)
        for k in var[:-1]: ed.press(k, hold=0.06 + rnd.random() * 0.2, gap=0.05 + rnd.random() * 0.3)
        ed.press('E', hold=0.08 + rnd.random() * 0.4, gap=0); ed.run_seconds(1.0)
        r = ed.cpu.ram
        res[''.join('%x' % r[x * 16] for x in range(5))] += 1; m['%x' % r[0x0c]] += 1
        started = r[0x3c]
    ed.run_seconds(5)
    return var, dict(res), dict(m), ed.display()
if __name__ == '__main__':
    with Pool(2) as p:
        for var, res, m, disp in p.imap(run, VAR):
            print(var, 'col0 rows0-4:', sorted(res.items()), ' M(0,12):', sorted(m.items()), ' last display', repr(disp))
