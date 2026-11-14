"""Self-check of game/dealer.py ('Classic without patterns'): plays whole cases in the emulator and compares
every alibi, every card question, questions 13/14 and the accusation with the dealt table.
    python fair.py [games]      (about a minute per game, 2 processes)"""
import os, random, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'game'))
from dealer import Dealer
sys.path.pop(0)                           # keep this folder's tms0980/elecdet


# ---------------------------------------------------------------- self-check
CARDS = {1: (1, 2, 9), 2: (2, 3, 9), 3: (3, 4, 5), 4: (4, 5, 9), 5: (1, 4, 9), 6: (5, 6, 12), 7: (2, 5, 12),
         8: (3, 5, 12), 9: (1, 5, 12), 10: (7, 8, 12), 11: (6, 7, 11), 12: (2, 6, 11), 13: (3, 7, 11),
         14: (1, 6, 11), 15: (4, 7, 11), 16: (6, 8, 10), 17: (2, 7, 10), 18: (1, 8, 10), 19: (3, 8, 10), 20: (4, 8, 10)}
CH = {10: 'A', 6: 'b', 12: 'C', 13: 'd', 14: 'E', 15: 'F'}
# template -> column -> (fields, companion columns); RULES.md 5.1
TPL = {1: [('s', (1, 3)), ('p', ()), ('a', (0,)), ('a', ())], 2: [('p', (3,)), ('ap', ()), ('sa', ()), ('s', (1, 2))],
       3: [('p', (1,)), ('', (2, 3)), ('s', ()), ('a', ())], 4: [('sa', ()), ('p', ()), ('', (1, 3)), ('', (0, 2))],
       5: [('sp', ()), ('a', (0,)), ('', (0, 1)), ('', (1, 2))]}


def check(seed):
    import copy
    from elecdet import ElecDet, IPS
    from probe_reads import ROM
    rng = random.Random(seed); ed = ElecDet(ROM); cpu = ed.cpu; ram = cpu.ram; dealer = Dealer(rng)
    step = int(IPS / 60)
    def run(s):
        for _ in range(int(s * 60)):
            ed.run(step); dealer.tick(cpu)
    def keys(s):
        for k in s:
            row, bit = __import__('elecdet').KEYS[__import__('elecdet').ALIAS.get(k, k)]
            ed.inputs[row] |= bit; run(0.1); ed.inputs[row] &= ~bit; run(0.1)
    ed.power_on(); run(6.3 + rng.random()); keys('31E'); run(5.5)
    start = ed.display(); run(53)
    R = lambda r, c: ram[r * 16 + c]
    who = lambda r, c: [R(r, c) or 10, R(r, c), (R(r, c) or 10) + 10, R(r, c) + 10][c]
    vcol, mcol = R(4, 12), R(4, 13); victim, murderer = who(4, vcol), who(0, mcol); w38 = bool(R(1, 9) & 2)
    side = lambda r: '2' if R(r, 4) & 4 else '1'; area = lambda r: str(2 + (R(r, 4) & 3)); let = lambda r: CH[R(r, 5)]
    loc = {who(r, c): (r, c) for r in range(5) for c in range(4)}; del loc[victim]
    bad = []
    def expect(what, got, want):
        if got != want: bad.append('%s: got %r, want %r' % (what, got, want))
    expect('start', start.strip()[:-1].replace('b', '6') + start.strip()[-1:], '%d%s' % (victim, let(5)))
    yn = lambda b: '4E5' if b else 'N0'
    male = lambda n: n <= 10
    def answer(q, s):
        r, c = loc[s]
        if q == 13 or q == 14:
            if r != q - 12: return '0000000'
            same = male(s) == male(murderer)
            if q == 14: return yn(same and murderer % 2 == 1)
            if w38: return yn(murderer % 2 == 1 if same else True)
            return yn(s % 2 == 0)
        return {1: yn(side(0) == '2'), 2: yn(male(murderer)), 3: area(0), 4: yn(w38), 5: let(1), 6: let(2), 7: let(4),
                8: yn(let(0) in 'AbC'), 9: yn(side(r) == '2'), 10: area(r), 11: yn(let(r) in 'AbC'), 12: yn(r in (1, 2))}[q]
    for s in sorted(loc):
        r, c = loc[s]
        keys('S%dE' % s); run(1.0); d = ed.display()
        mates = [int(x.strip().replace('b', '6')) for x in (d[3:5], d[5:7]) if x.strip()]
        if R(r, 6) != 6:
            f, mc = TPL[R(r, 6)][c]
            want = (side(r) if 's' in f else ' ') + (area(r) if 'a' in f else ' ') + (let(r) if 'p' in f else ' ')
            expect('alibi %d fields' % s, d[:3], want); expect('alibi %d mates' % s, mates, [who(r, x) for x in mc])
        else:
            for ch, want in zip(d[:3], (side(r), area(r), let(r))):
                if ch != ' ': expect('alibi %d (three)' % s, ch, want)
            for m in mates: expect('alibi %d mate %d row' % (s, m), loc.get(m, (None,))[0], r)
        for q in CARDS[s]:
            keys('Q%dE' % q); run(0.8); expect('Q%d to %d' % (q, s), ed.display().strip(), answer(q, s))
        keys('T'); run(0.4)
    for s in sorted(loc):
        if loc[s][0] in (1, 2):
            keys('S%dE' % s); run(1.0)
            for q in (13, 14):
                keys('Q%dE' % q); run(0.8); expect('Q%d to %d' % (q, s), ed.display().strip(), answer(q, s))
            keys('T'); run(0.4)
    keys('A%dE' % murderer); seen = set()
    for _ in range(40):                   # the verdict blinks
        run(0.2); seen.add(ed.display().strip())
    if not any(d.endswith('4E5') for d in seen): bad.append('accusing %d -> %r' % (murderer, sorted(seen)))
    table = '/'.join(''.join('%x' % R(r, c) for c in range(7)) for r in range(6))
    return seed, victim, murderer, w38, table, bad


if __name__ == '__main__':
    import sys
    from multiprocessing import Pool
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 12
    fails = 0
    with Pool(2) as p:
        for seed, v, m, w38, table, bad in p.imap_unordered(check, range(100, 100 + n)):
            fails += bool(bad)
            print('game %d: victim %d murderer %d weapon %s table %s -> %s' % (
                seed, v, m, '.38' if w38 else '.45', table, 'OK' if not bad else 'FAIL'), flush=True)
            for b in bad[:12]: print('    ', b)
    print('%d games, %d failed' % (n, fails))
