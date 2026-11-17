"""Experiment (since moved into solver.lie_suspects; the patch below then changes nothing): lie_suspects taught one more thing the player rules say. (SPOILERS: playing logic.)

A liar tells the alibi of an honest suspect of the same kind (sex and parity) who was at another place. So a heard
alibi can be a lie only if another suspect of that kind, not the other liar, told exactly the same alibi.
twin_suspects() is lie_suspects() with the choices of liars cut down to such suspects (one not heard yet can still
be a liar). Nothing else changes.

    python lies_twin.py      the unsolvable deals of lies_unsolvable.jsonl: how many the twin rule solves
"""
import inspect, json, os, random, sys, textwrap
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..', '..', 'game'))
import solver
from rules import col_of, deal_lies, observe

OLD = "    choices = [()] * (len(silent) > 1) + [(a,) for a in spoke] + list(combinations(spoke, 2))\n"
NEW = OLD + ("    twin = lambda a, liars: any(o != a and o not in liars and col_of(o) == col_of(a)"
             " and (o not in alibi or alibi[o] == alibi[a]) for o in people)\n"          # the twin may be unheard yet
             "    choices = [c for c in choices if all(twin(a, c) for a in c)]\n")
src = inspect.getsource(solver.lie_suspects).replace('def lie_suspects(', 'def twin_suspects(')
assert OLD in src
ns = dict(vars(solver)); exec(src.replace(OLD, NEW), ns)
twin_suspects = ns['twin_suspects']


def run(seed):
    obs, m = observe(deal_lies(random.Random(seed)))
    found = twin_suspects(obs)
    assert m in found, seed                    # the rule is true, so the murderer must stay
    return seed, sorted(found)


if __name__ == '__main__':
    from multiprocessing import Pool
    recs = [json.loads(l) for l in open(os.path.join(HERE, 'lies_unsolvable.jsonl'))]
    bad = [r['seed'] for r in recs if len(r['found']) > 1]
    sample = [r['seed'] for r in recs if len(r['found']) == 1][:200]
    with Pool(2) as p:
        res = dict(p.map(run, bad + sample))
    still = [s for s in bad if len(res[s]) > 1]
    print('unsolvable before: %d; with the twin rule still unsolvable: %d' % (len(bad), len(still)))
    print('solvable before (200 checked) that stay solvable:', sum(len(res[s]) == 1 for s in sample))
    print('still unsolvable (seeds):', still)
