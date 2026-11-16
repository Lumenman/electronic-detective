"""DRAFT, not part of the game: a harder game without lies. (SPOILERS: playing logic.)
  once    every suspect can be questioned one time only: how often is the case still solved, in how many turns?
  budget  how many private questions the usual methodical game takes in all (to choose a budget for the whole game)

    python hard.py [n]
"""
import sys
from collections import Counter
from multiprocessing import Pool
import par


def run(job):
    import random
    from rules import deal, observe
    seed, level = job
    obs = observe(deal(random.Random(seed)))[0]
    trace = []
    par.methodical(obs, level, trace=trace)
    return par.methodical(obs, level, once=True), sum(len(t[1]) for t in trace)


if __name__ == '__main__':
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 100
    for level in (3, 2, 1):
        with Pool(2) as p:                               # half of the cores stay free
            res = p.map(run, [(i, level) for i in range(n)], chunksize=2)
        v = sorted(r[0] for r in res if r[0] is not None); q = sorted(r[1] for r in res)
        print('level %d, %d cases. One visit each: solved %d; turns median %s  max %s' % (
            level, n, len(v), v[len(v) // 2] if v else '-', v[-1] if v else '-'))
        print('  questions in the usual game: min %d  median %d  9 of 10 within %d  max %d' % (
            q[0], q[n // 2], q[n * 9 // 10], q[-1]), flush=True)
