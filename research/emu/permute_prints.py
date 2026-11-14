"""Is the opposite-sex fingerprint lie a function of the layout? Shuffle occupants (cols 0-3, rows 0-4) from one
snapshot, ask the fingerprint question, compare with the truth of the shuffled layout. Writes permute_prints.jsonl."""
import copy, json, random, sys
from multiprocessing import Pool
from elecdet import ElecDet
from probe_reads import ROM
from sweep import decode

SNAP = None


def make_snap(seed=1):
    rnd = random.Random(seed); ed = ElecDet(ROM)
    ed.power_on(); ed.run_seconds(6.3 + rnd.random() * 4)
    ed.press('3'); ed.press('1'); ed.press('E', hold=0.08 + rnd.random() * 0.4, gap=0); ed.run_seconds(57)
    return ed


def ask(e, s, q):
    e.keys('S%dE' % s); e.run_seconds(1.5); e.keys('Q%dE' % q); e.run_seconds(1.0)
    a = e.display().strip(); e.press('T'); e.run_seconds(1)
    return a


def one(i):
    global SNAP
    if SNAP is None:
        SNAP = make_snap()
    e = copy.deepcopy(SNAP); rnd = random.Random(1000 + i)
    if i:  # i == 0 keeps the original layout
        for c in range(4):
            col = [e.cpu.ram[r << 4 | c] for r in range(5)]; rnd.shuffle(col)
            for r in range(5):
                e.cpu.ram[r << 4 | c] = col[r]
    ram = [e.cpu.ram[a] for a in range(0x90)]
    d = decode(ram); M = d['murderer']
    q = 13 if d['murder_weapon'] == '.38' else 14
    wp = d['p38'] if q == 13 else d['p45']
    truth = '4E5' if M % 2 else 'n0'
    occ = d['places'][wp]['occ']
    ans = {s: ask(e, s, q) for s in occ}
    return dict(i=i, murderer=M, q=q, truth=truth, layout=''.join('%x' % v for v in ram[:0x60]),
                answers={s: (a, 'same' if (s <= 10) == (M <= 10) else 'opp') for s, a in ans.items()})


if __name__ == '__main__':
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 200
    with Pool(2) as p, open('permute_prints.jsonl', 'w') as f:
        for r in p.imap_unordered(one, range(n)):
            f.write(json.dumps(r) + '\n'); f.flush()
