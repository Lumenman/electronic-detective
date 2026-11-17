"""Cases dealt by rules.deal with x' = (84621 x + 3571 + x // 1000) mod 10^7 instead of random.Random,
three idle steps first (without the x // 1000 and the idle steps neighbouring numbers deal alike). Choice of n = x*n // 10^7.

    lcg.py similar          how alike are cases with neighbouring numbers (per warm-up)
    lcg.py classic n        solvable? turns of the methodical player, case numbers 1..n
    lcg.py lies n           Two False Alibis: share of unsolvable deals, LCG vs random.Random
"""
import os, random, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..', '..', 'game'))
from rules import deal, deal_lies, observe

M, A, C = 10 ** 7, 84621, 3571


class LCG:
    def __init__(self, number, warm=3):
        self.x = number % M
        for _ in range(warm): self.step()
    def step(self): self.x = (A * self.x + C + self.x // 1000) % M; return self.x
    def draw(self, n): return self.step() * n // M
    def randrange(self, a, b=None): return self.draw(a) if b is None else a + self.draw(b - a)
    def random(self): return self.step() / M
    def choice(self, seq): return seq[self.draw(len(seq))]
    def shuffle(self, x):                       # Fisher-Yates, as by hand: from the end
        for i in range(len(x) - 1, 0, -1):
            j = self.draw(i + 1); x[i], x[j] = x[j], x[i]


def rows_of(case):
    return {s: r for r, row in enumerate(case['rows']) for s in row['people']}


def classic(number):
    from solver import suspects
    from par import methodical
    obs, m = observe(deal(LCG(number)))
    return suspects(obs) == {m}, [methodical(obs, lv) for lv in (3, 2, 1)]


def lies(job):
    from solver import lie_suspects
    kind, number = job
    obs, m = observe(deal_lies(LCG(number) if kind == 'lcg' else random.Random(number)))
    return kind, lie_suspects(obs) == {m}


if __name__ == '__main__':
    from multiprocessing import Pool
    what = sys.argv[1]
    if what == 'similar':
        for warm in (0, 1, 2, 3):
            same = tot = 0
            for n in range(1, 2001):
                a, b = rows_of(deal(LCG(n, warm))), rows_of(deal(LCG(n + 1, warm)))
                same += sum(a[s] == b[s] for s in a); tot += len(a)
            print('warm-up %d: suspect in the same row in cases n and n+1: %.0f%% (unrelated cases: 20%%)' % (warm, 100 * same / tot))
    elif what == 'classic':
        n = int(sys.argv[2]); res = Pool(2).map(classic, range(1, n + 1), chunksize=2)
        print('classic, LCG, numbers 1..%d: solvable %d' % (n, sum(ok for ok, _ in res)))
        for i, lv in enumerate((3, 2, 1)):
            t = sorted(p[i] for _, p in res if p[i] is not None)
            print('  level %d: %d solved, turns median %d mean %.1f max %d' % (lv, len(t), t[len(t) // 2], sum(t) / len(t), t[-1]))
    elif what == 'lies':
        n = int(sys.argv[2]); res = Pool(2).map(lies, [(k, i) for i in range(1, n + 1) for k in ('lcg', 'random')], chunksize=2)
        for k in ('lcg', 'random'):
            v = [ok for kk, ok in res if kk == k]
            print('two false alibis, %s: %d deals, unsolvable %d (%.1f%%)' % (k, len(v), len(v) - sum(v), 100 * (len(v) - sum(v)) / len(v)))
