"""Deals where every column is laid out by row = (a*k + b) mod 5 (the MK-61 idea), against rules.deal. Usage: affine.py n"""
import os, random, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..', '..', 'game'))
from rules import deal, observe
from solver import suspects
from par import methodical

BASE = [[2, 4, 6, 8, 10], [1, 3, 5, 7, 9], [12, 14, 16, 18, 20], [11, 13, 15, 17, 19]]


def affine_deal(rng):
    case = deal(rng)                      # addresses, letters, templates, victim, murderer, weapon stay as in the game
    for c, base in enumerate(BASE):
        a, b = rng.randrange(1, 5), rng.randrange(5)
        col = [0] * 5
        for k, s in enumerate(base): col[(a * k + b) % 5] = s
        for r in range(5): case['rows'][r]['people'][c] = col[r]
    return case


def run(job):
    kind, seed = job
    case = (affine_deal if kind == 'affine' else deal)(random.Random(seed))
    obs, m = observe(case)
    found = suspects(obs)
    return kind, m in found, len(found), [methodical(obs, lv) for lv in (3, 2, 1)]


if __name__ == '__main__':
    from multiprocessing import Pool
    from collections import Counter
    n = int(sys.argv[1])
    # self-check: an affine column is a permutation of its base
    r = random.Random(1)
    for _ in range(50):
        c = affine_deal(r)
        for col in range(4): assert sorted(c['rows'][i]['people'][col] for i in range(5)) == BASE[col]
    jobs = [(k, 10 ** 6 + i) for i in range(n) for k in ('affine', 'fair')]
    res = {'affine': [], 'fair': []}
    with Pool(2) as p:
        for kind, ok, k, pars in p.imap_unordered(run, jobs, chunksize=2): res[kind].append((ok, k, pars))
    for kind, v in res.items():
        print(kind, len(v), 'cases; murderer missing:', sum(not ok for ok, _, _ in v),
              '; possible murderers:', dict(sorted(Counter(k for _, k, _ in v).items())))
        for i, lv in enumerate((3, 2, 1)):
            t = sorted(p[i] for *_, p in v if p[i] is not None)
            print('  level %d: %d solved, turns median %d mean %.1f max %d' % (lv, len(t), t[len(t) // 2], sum(t) / len(t), t[-1]))
