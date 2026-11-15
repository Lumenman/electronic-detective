"""How many turns does a case take? (SPOILERS: the policy below is a playing method.)

Two numbers per case and level (1, 2, 3 = private questions per turn):

  methodical  a fixed, sensible routine that sees only what a player sees: first collect the facts of the murder
              from the cards that carry them, then question suspects of the murderer's sex, asking about the
              fingerprints where it can matter. Stops when solver.suspects() leaves one name.
  ideal       the fewest turns found when every choice is made knowing the answers in advance (greedy search,
              so an upper bound of the true minimum). Nobody plays like this; it is the floor.

The accusation itself is not counted.

    python par.py fair [n] [level]       random deals, as game/dealer.py makes them
    python par.py classic [n] [level]    deals of the ROM (emulator sweep)
    add 'ideal' to compute the floor too (slow)
"""
from engine import CARDS, male
from solver import suspects


def partial(obs, asked, visited):
    return {'victim': obs['victim'], 'scene': obs['scene'], 'alibi': {s: obs['alibi'][s] for s in visited},
            'ans': {k: obs['ans'][k] for k in asked}}


def methodical(obs, level, cap=120):
    people = sorted(obs['alibi'])
    visited, asked = set(), set()
    cand = set(people)
    for turn in range(1, cap + 1):
        fact = {q: next((obs['ans'][k] for k in asked if k[1] == q), None) for q in range(1, 9)}
        sex = None if fact[2] is None else fact[2] == 'Y'
        weapon_q = None if fact[4] is None else 13 if fact[4] == 'Y' else 14

        def questions(s):
            left = [q for q in CARDS[s] + (13, 14) if (s, q) not in asked]
            def rank(q):
                if q <= 8: return 0 if fact[q] is None else 9          # a fact of the murder not known yet
                if q in (13, 14):
                    if weapon_q is None: return 5
                    return 1 if q == weapon_q and sex in (None, male(s)) else 8
                return 3                                               # about the suspect's own place
            return sorted(left, key=lambda q: (rank(q), q)), rank

        def value(s):
            qs, rank = questions(s)
            new_facts = sum(1 for q in qs[:level] if rank(q) == 0)
            fresh = s not in visited
            fits = sex is None or male(s) == sex
            return (new_facts, fresh and fits, fresh, s in cand, bool(qs), -s)

        open_ = [s for s in people if s not in visited or questions(s)[0]]   # somebody who can still tell something
        if not open_:
            return None
        s = max(open_, key=value)
        qs, _ = questions(s)
        visited.add(s); asked.update((s, q) for q in qs[:level])
        cand = suspects(partial(obs, asked, visited))
        if len(cand) == 1:
            return turn
    return None


def ideal(obs, level, cap=40):
    """Greedy with foresight: each turn take the suspect and questions that leave the fewest candidates."""
    from itertools import combinations
    people = sorted(obs['alibi'])
    visited, asked = set(), set()
    for turn in range(1, cap + 1):
        best = None
        for s in people:
            left = [q for q in CARDS[s] + (13, 14) if (s, q) not in asked]
            if not left and s in visited: continue
            for qs in combinations(left, min(level, len(left))):
                n = len(suspects(partial(obs, asked | {(s, q) for q in qs}, visited | {s}),
                                 limit=None if best is None else best[0]))
                if best is None or n < best[0]: best = (n, s, qs)
                if n == 1: break
            if best and best[0] == 1: break
        n, s, qs = best
        visited.add(s); asked.update((s, q) for q in qs)
        if n == 1:
            return turn
    return None


def run(job):
    import random
    from engine import observe, from_ram
    from solver import random_case
    kind, arg, level, want_ideal = job
    case = random_case(random.Random(arg)) if kind == 'fair' else from_ram(arg)
    obs, _ = observe(case)
    return methodical(obs, level), ideal(obs, level) if want_ideal else None


if __name__ == '__main__':
    import json, os, sys
    from collections import Counter
    from multiprocessing import Pool
    args = [a for a in sys.argv[1:] if a != 'ideal']; want_ideal = 'ideal' in sys.argv
    kind = args[0]; n = int(args[1]) if len(args) > 1 else 100; levels = [int(args[2])] if len(args) > 2 else [3, 2, 1]
    here = os.path.dirname(os.path.abspath(__file__))
    if kind == 'classic':
        rams = [[int(c, 16) for c in json.loads(l)['ram']] for l in open(os.path.join(here, '..', 'emu', 'sweep1.jsonl'))]
    for level in levels:
        jobs = [(kind, i if kind == 'fair' else rams[i], level, want_ideal) for i in range(n)]
        with Pool(2) as p:
            res = p.map(run, jobs, chunksize=2)
        for name, k in (('methodical', 0), ('ideal', 1)):
            v = sorted(r[k] for r in res if r[k] is not None)
            if not v: continue
            c = Counter(v)
            print('%s level %d %-10s: %d cases, turns min %d  median %d  mean %.1f  max %d   %s' % (
                kind, level, name, len(v), v[0], v[len(v) // 2], sum(v) / len(v), v[-1],
                ' '.join('%d:%d' % kv for kv in sorted(c.items()))), flush=True)
