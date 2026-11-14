"""Which RAM cells does the program read while answering a given private question?"""
import random, sys
from collections import Counter
from elecdet import ElecDet
from tms0980 import M_MTP, M_MTN, M_DMTP, M_NDMTP

ROM = 'D:/claude/GAMES/electronic_detective/mame/roms/elecdet'


def new_game(seed):
    ed = ElecDet(ROM)
    rnd = random.Random(seed)
    ed.power_on(); ed.run_seconds(6.3 + rnd.random() * 3)
    ed.press('3'); ed.press('1'); ed.press('E', gap=0); ed.run_seconds(5)
    return ed


def reads_during(ed, keys, secs=1.0):
    cpu = ed.cpu
    cnt = Counter()
    orig = cpu.step
    def step():
        m = cpu.micro
        if m & (M_MTP | M_MTN):
            cnt[cpu.ram_address] += 1
        if m & (M_DMTP | M_NDMTP):
            cnt[cpu.ram_address | 0x80] += 1
        orig()
    cpu.step = step
    ed.keys(keys); ed.run_seconds(secs)
    cpu.step = orig
    return cnt, ed.display()


if __name__ == '__main__':
    ed = new_game(int(sys.argv[1]) if len(sys.argv) > 1 else 1)
    print('crime', repr(ed.display()))
    base, _ = reads_during(ed, 'S3E', 1.5)
    q2, a2 = reads_during(ed, 'Q4E')
    ed.press('T'); ed.run_seconds(1)
    reads_during(ed, 'S1E', 1.5)
    q1, a1 = reads_during(ed, 'Q2E')
    fmt = lambda c: ' '.join('%X:%X' % (a >> 4, a & 15) for a in sorted(c))
    print('Q4 answer', repr(a2), 'cells read in Q4 but not in Q2:', fmt(set(q2) - set(q1)))
    print('Q2 answer', repr(a1), 'cells read in Q2 but not in Q4:', fmt(set(q1) - set(q2)))
