"""Par of Two False Alibis with the old solver and the new one (the twin rule in solver.lie_suspects).
The old one is not kept in the repository: git show 7250ada:research/solver/solver.py > _solver_old.py

Deals are taken as the game takes them: rules.deal_lies until the solver solves it (old solver, so both see the
same cases). Par = turns of par.methodical. For comparison, the ordinary game on deals of the same seeds.

    python lies_par.py n
"""
import os, random, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..', '..', 'game'))
from rules import deal, deal_lies, observe
import par, solver, _solver_old


def run(seed):
    rng = random.Random(seed)
    while True:
        obs, m = observe(deal_lies(rng))
        if _solver_old.lie_suspects(obs) == {m}: break
    out = {}
    for name, fn in (('old', _solver_old.lie_suspects), ('new', solver.lie_suspects)):
        par.lie_suspects = fn
        out[name] = [par.methodical(obs, lv, lies=True) for lv in (3, 2, 1)]
    out['classic'] = [par.methodical(observe(deal(random.Random(seed)))[0], lv) for lv in (3, 2, 1)]
    return out


if __name__ == '__main__':
    from multiprocessing import Pool
    n = int(sys.argv[1])
    with Pool(2) as p:
        res = p.map(run, range(n), chunksize=2)
    for name in ('classic', 'old', 'new'):
        for i, lv in enumerate((3, 2, 1)):
            t = sorted(r[name][i] for r in res if r[name][i] is not None)
            print('%-7s level %d: %d of %d reached, turns median %d mean %.1f min %d max %d' % (
                name, lv, len(t), n, t[len(t) // 2], sum(t) / len(t), t[0], t[-1]), flush=True)
    d = [r['old'][i] - r['new'][i] for r in res for i in range(3) if None not in (r['old'][i], r['new'][i])]
    print('old - new per case and level: faster %d, same %d, slower %d' % (sum(x > 0 for x in d), sum(x == 0 for x in d), sum(x < 0 for x in d)))
