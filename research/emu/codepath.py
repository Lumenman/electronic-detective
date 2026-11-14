"""Trace the answer code of the ROM: for every alibi template/column and every private question,
which table cells the handler reads and what it shows. Uses one saved game (seed 1) and RAM pokes.
    python codepath.py > codepath.txt      (about 5 minutes, 2 processes)"""
import copy, os, pickle, random, sys
from multiprocessing import Pool
from elecdet import ElecDet
from probe_reads import ROM
from tms0980 import M_MTP, M_MTN, M_DMTP, M_NDMTP

CARDS = {1: (1, 2, 9), 2: (2, 3, 9), 3: (3, 4, 5), 4: (4, 5, 9), 5: (1, 4, 9), 6: (5, 6, 12), 7: (2, 5, 12),
         8: (3, 5, 12), 9: (1, 5, 12), 10: (7, 8, 12), 11: (6, 7, 11), 12: (2, 6, 11), 13: (3, 7, 11),
         14: (1, 6, 11), 15: (4, 7, 11), 16: (6, 8, 10), 17: (2, 7, 10), 18: (1, 8, 10), 19: (3, 8, 10), 20: (4, 8, 10)}
BASE = None
SEED = 1


def base():
    global BASE
    if BASE is None:
        f = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'base%d.pkl' % SEED)
        if os.path.exists(f):
            BASE = pickle.load(open(f, 'rb'))
        else:
            rnd = random.Random(SEED); ed = ElecDet(ROM)
            ed.power_on(); ed.run_seconds(6.3 + rnd.random() * 4); ed.press('3'); ed.press('1')
            ed.press('E', hold=0.08 + rnd.random() * 0.4, gap=0); ed.run_seconds(58)
            pickle.dump(ed, open(f, 'wb')); BASE = ed
    return copy.deepcopy(BASE)


def who(ram, row, col):
    v = ram[row * 16 + col]
    return [v or 10, v, (v or 10) + 10, v + 10][col]


def col_of(n):
    return (0 if n % 2 == 0 else 1) + (2 if n > 10 else 0)


def watch(ed, keys, secs, pages):
    """Press keys; return (display, cells read by code on the given pages, first address on each page)."""
    cpu = ed.cpu; reads, entry = [], []; orig = cpu.step
    def step():
        pc = cpu.rom_address; pg = pc >> 7
        if pg in pages:
            if not entry or entry[-1][0] != pg: entry.append((pg, pc & 0x7f))
            m = cpu.micro
            if m & (M_MTP | M_MTN | M_DMTP | M_NDMTP):
                a = cpu.ram_address
                if a < 0x70 and a not in reads: reads.append(a)
        orig()
    cpu.step = step
    ed.keys(keys); ed.run_seconds(secs)
    cpu.step = orig
    return ed.display(), ' '.join('%X:%X' % (a >> 4, a & 15) for a in sorted(reads)), ' '.join('%X:%02X' % e for e in entry[:6])


def alibi_text(d, ram, row):
    f = ''.join(n for n, ch in zip(('side ', 'area ', 'place '), d[:3]) if ch != ' ')
    mates = []
    for s in (d[3:5], d[5:7]):
        s = s.strip().replace('b', '6')
        if s: mates.append(int(s))
    cols = [next((c for c in range(4) if who(ram, row, c) == m), '?') for m in mates]
    return (f + ('-> cols %s' % cols if mates else '')).strip()


def set_victim(ed, col):
    """Make the person in row 4, column col the victim (4:C and the number in 4:A/4:B)."""
    r = ed.cpu.ram; n = who(r, 4, col)
    r[0x4c] = col; r[0x4a] = n % 10; r[0x4b] = n // 10 if n >= 10 else 0xb


def job(j):
    kind = j[0]; ed = base(); r = ed.cpu.ram
    if kind == 'alibi4':                                   # place of four: template t, column c
        _, t, c = j; r[0x06] = t
        d, reads, entry = watch(ed, 'S%dE' % who(r, 0, c), 1.2, {11, 12})
        return 'template %d col %d: %-28s reads %-24s entry %s' % (t, c, alibi_text(d, r, 0), reads, entry)
    if kind == 'alibi3':                                   # place of three: victim column v, column c
        _, v, c = j; set_victim(ed, v)
        d, reads, entry = watch(ed, 'S%dE' % who(r, 4, c), 1.2, {9, 11, 12})
        return 'three, victim col %d, col %d: %-24s display %r entry %s' % (v, c, alibi_text(d, r, 4), d, entry)
    if kind == 'q':                                        # question q to suspect s
        _, q, s = j
        ed.keys('S%dE' % s); ed.run_seconds(1.2)
        row = next(x for x in range(5) if who(r, x, col_of(s)) == s)
        d, reads, entry = watch(ed, 'Q%dE' % q, 1.0, {6, 7, 8, 10})
        return 'Q%-2d suspect %-2d (row %d col %d): %-9r reads %-40s entry %s' % (q, s, row, col_of(s), d.strip(), reads, entry)
    if kind == 'victim':                                   # question q to the victim after questioning `prev`
        _, q, prev = j; v = who(r, 4, r[0x4c])
        if prev:
            ed.keys('S%dE' % prev); ed.run_seconds(1.2); ed.press('T'); ed.run_seconds(0.5)
        ed.keys('S%dE' % v); ed.run_seconds(1.2); row6 = ''.join('%x' % x for x in r[0x60:0x69])
        d, reads, entry = watch(ed, 'Q%dE' % q, 1.0, {6, 7, 8, 10})
        return 'victim, Q%-2d after suspect %-4s: %-9r row6 %s reads %s' % (q, prev, d.strip(), row6, reads)


def init(seed):
    global SEED; SEED = seed


if __name__ == '__main__':
    only_prints = len(sys.argv) > 1                        # codepath.py <seed>: questions 13/14 only, in another game
    if only_prints: SEED = int(sys.argv[1])
    b = base(); r = b.cpu.ram
    print('game: rows 0-5 (cols 0-15)')
    for x in range(8): print('  %d: ' % x + ' '.join('%x' % r[x * 16 + c] for c in range(16)))
    victim = who(r, 4, r[0x4c]); print('victim', victim, 'murderer', who(r, 0, r[0x4d]))
    jobs = []
    if not only_prints: jobs = [('alibi4', t, c) for t in range(1, 6) for c in range(4)]
    if not only_prints: jobs += [('alibi3', v, c) for v in range(4) for c in range(4)]
    if not only_prints: jobs += [('q', q, s) for q in range(1, 13) for s in range(1, 21) if q in CARDS[s] and s != victim]
    jobs += [('q', q, who(r, x, c)) for q in (13, 14) for x in range(5) for c in range(4) if who(r, x, c) != victim]
    if not only_prints: jobs += [('victim', q, p) for p in (None, 1, 17) for q in range(1, 15)]
    with Pool(2, init, (SEED,)) as p:
        for line in p.imap(job, jobs): print(line, flush=True)
