"""Two False Alibis dealt so that it can be solved, instead of dealing at random and asking the solver.
(SPOILERS: playing logic.)

rules.deal_lies picks the second liar and the two borrowed alibis at random. deal_lies_built() picks among the
choices that avoid what lies_twin_stats.txt found behind every unsolvable deal:
  - the two liars do not tell the alibi of the same suspect;
  - the murderer can be told from his double: a question 9-11 on his card tells their places apart, or an honest
    suspect names one of them as a companion (not the one whose alibi the second liar tells: he may be the liar).
If a deal leaves no such choice, the next deal is taken.

    python lies_built.py check n     solver.lie_suspects on n built deals: how many cannot be solved
    python lies_built.py par n       turns of the methodical player: built deals against the game's deals
    add 'strict': the double only where a question on the murderer's card tells them apart
"""
import os, random, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..', '..', 'game'))
from rules import CARDS, col_of, deal, deal_lies, observe

STRICT = 'strict' in sys.argv[3:] or os.environ.get('LIES_STRICT') == '1'   # only a question 9-11 on the
                                     # murderer's card may tell him from his double (the variable reaches the workers)
ATTR = {9: lambda row: row['side'], 10: lambda row: row['area'], 11: lambda row: row['letter'] in 'ABC'}


def deal_lies_built(rng):
    while True:
        case = deal(rng)
        rows = case['rows']
        victim, m = rows[4]['people'][case['vcol']], rows[0]['people'][case['mcol']]
        row_of = {s: r for r, row in enumerate(rows) for s in row['people'] if s != victim}
        alibi = observe(case)[0]['alibi']                       # the true ones: no lies yet
        doubles = lambda s, second: [o for o in sorted(row_of) if col_of(o) == col_of(s) and o not in (m, second)
                                     and row_of[o] not in (row_of[s], 1, 2)]
        told_apart = lambda md: any(ATTR[q](rows[row_of[m]]) != ATTR[q](rows[row_of[md]]) for q in CARDS[m] if q in ATTR)
        named = lambda md, sec, sd: any(set(a.get('with', ())) & {m, md} for s, a in alibi.items() if s not in (m, sec, sd))
        good = [(sec, md, sd) for sec in sorted(row_of) if sec != m
                for md in doubles(m, sec) for sd in doubles(sec, sec)
                if md != sd and (told_apart(md) or not STRICT and named(md, sec, sd))]
        if good:
            sec, md, sd = rng.choice(good)
            case['lies'] = [[m, md], [sec, sd]]
            return case


def check(seed):
    from solver import lie_suspects
    obs, m = observe(deal_lies_built(random.Random(seed)))
    found = lie_suspects(obs)
    assert m in found, seed
    return seed, len(found)


def par_of(seed):
    import par, solver
    rng = random.Random(seed)
    while True:                                                 # the game's way: deal, ask the solver
        obs, m = observe(deal_lies(rng))
        if solver.lie_suspects(obs) == {m}: break
    built = observe(deal_lies_built(random.Random(seed)))[0]
    return [[par.methodical(o, lv, lies=True) for lv in (3, 2, 1)] for o in (obs, built)]


if __name__ == '__main__':
    from multiprocessing import Pool
    what, n = sys.argv[1], int(sys.argv[2])
    os.environ['LIES_STRICT'] = '1' if STRICT else '0'
    with Pool(2) as p:
        if what == 'check':
            res = p.map(check, range(n), chunksize=8)
            bad = [s for s, k in res if k > 1]
            print('%d built deals: unsolvable %d (%.2f%%) %s' % (n, len(bad), 100 * len(bad) / n, bad[:30]))
        else:
            res = p.map(par_of, range(n), chunksize=2)
            for i, name in enumerate(('game', 'built')):
                for j, lv in enumerate((3, 2, 1)):
                    t = sorted(r[i][j] for r in res if r[i][j] is not None)
                    print('%-5s level %d: %d of %d reached, turns median %d mean %.1f min %d max %d' % (
                        name, lv, len(t), n, t[len(t) // 2], sum(t) / len(t), t[0], t[-1]), flush=True)
