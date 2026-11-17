"""How deep a deduction does a case need? (SPOILERS: playing logic.)

The solver places everybody by propagation (one of each category per place, companions together) and, where that
does not settle it, by trying cases: 'if #5 was at the Docks, then ...'. A weaker detective who never tries cases
- only follows what is forced - is solver.place_all without the branching: weak_place_all accepts any arrangement
of addresses whose propagation does not end in a contradiction.

For every case: par of the methodical player with the full solver and with the weak one. A case where the weak
detective needs more turns, or never gets there with everything asked, needs 'if-then' reasoning somewhere.

    python depth.py classic n       the ordinary game
    python depth.py lies n          Two False Alibis (deals as the game takes them)
"""
import inspect, os, random, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..', '..', 'game'))
import par, solver
from rules import deal, deal_lies, observe

FULL = solver.place_all
OLD = "        s = min(open_, key=lambda x: len(dom[x]))\n"
src = inspect.getsource(solver.place_all).replace('def place_all(', 'def weak_place_all(')
assert OLD in src
ns = dict(vars(solver))
exec(src.replace(OLD, "        return {s: min(v) for s, v in dom.items()}      # no 'if-then': forced steps only\n" + OLD), ns)
WEAK = ns['weak_place_all']
LEVELS = (3, 1)


def case_of(kind, seed):
    rng = random.Random(seed)
    if kind == 'classic': return observe(deal(rng))[0]
    while True:
        obs, m = observe(deal_lies(rng))
        if solver.lie_suspects(obs) == {m}: return obs


def run(job):
    kind, seed = job
    obs = case_of(kind, seed)
    lies = kind == 'lies'
    out = {}
    for name, fn in (('full', FULL), ('weak', WEAK)):
        solver.place_all = fn
        out[name] = [par.methodical(obs, lv, lies=lies) for lv in LEVELS]
    solver.place_all = WEAK                       # with everything asked, does the weak one get there at all?
    sus = solver.lie_suspects if lies else solver.suspects
    out['weak_all'] = len(sus(obs))
    solver.place_all = FULL
    return out


if __name__ == '__main__':
    from multiprocessing import Pool
    from collections import Counter
    kind, n = sys.argv[1], int(sys.argv[2])
    with Pool(2) as p:
        res = p.map(run, [(kind, s) for s in range(n)], chunksize=2)
    print('%s, %d cases. With everything asked the weak detective is left with: %s suspects' % (
        kind, n, dict(sorted(Counter(r['weak_all'] for r in res).items()))))
    for i, lv in enumerate(LEVELS):
        d = Counter()
        for r in res:
            f, w = r['full'][i], r['weak'][i]
            d['never' if w is None else min(w - f, 5)] += 1
        f = [r['full'][i] for r in res]; w = [r['weak'][i] for r in res if r['weak'][i] is not None]
        print('  level %d: full par mean %.1f; weak mean %.1f (where it gets there); weak minus full, turns: %s' % (
            lv, sum(f) / len(f), sum(w) / max(1, len(w)), dict(sorted(d.items(), key=lambda kv: str(kv[0])))))
