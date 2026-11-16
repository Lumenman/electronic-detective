"""How many turns does a case take? (SPOILERS: the policy below is a playing method.)

Two numbers per case and level (1, 2, 3 = private questions per turn):

  methodical  a sensible routine that sees only what a player sees: each turn it goes to the suspect whose alibi
              and questions can still tell the most (unknown facts of the murder first, then those who can still
              be the murderer, and the fingerprints where they can matter), and never asks what is already known
              while anything else is left. Stops when solver.suspects() leaves one name.
  ideal       the fewest turns found when every choice is made knowing the answers in advance (greedy search,
              so an upper bound of the true minimum). Nobody plays like this; it is the floor.

The accusation itself is not counted.

    python par.py fair [n] [level]       random deals, as game/dealer.py makes them
    python par.py classic [n] [level]    deals of the ROM (emulator sweep)
    add 'ideal' to compute the floor too (slow)
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'game'))
from rules import CARDS, male
from solver import suspects


def partial(obs, asked, visited):
    return {'victim': obs['victim'], 'scene': obs['scene'], 'alibi': {s: obs['alibi'][s] for s in visited},
            'ans': {k: obs['ans'][k] for k in asked}}


def methodical(obs, level, cap=120, trace=None):
    people = sorted(obs['alibi'])
    visited, asked = set(), set()
    cand, worlds = set(people), {}
    for turn in range(1, cap + 1):
        fact = {q: next((obs['ans'][k] for k in asked if k[1] == q), None) for q in range(1, 9)}
        sex = None if fact[2] is None else fact[2] == 'Y'
        weapon_q = None if fact[4] is None else 13 if fact[4] == 'Y' else 14
        told = lambda s, q: obs['ans'][(s, q)] if (s, q) in asked else None
        guns = (fact[5], fact[6])
        # what the possible states of affairs (one per remaining name) say about s: (place, side, area, at a gun)
        views = lambda s: {(loc[s], *amap[loc[s]], loc[s] in guns) for amap, loc in worlds.values()}
        spots = {(amap[loc[m]][0], amap[loc[m]][1], loc[m] in 'ABC') for m, (amap, loc) in worlds.items()}
        splits = lambda s, *i: len({tuple(v[k] for k in i) for v in views(s)}) > 1      # they disagree about s

        def worth(s, q, a):
            """What an answer can be worth, judged from what is known (a = the alibi of s, {} before the visit)."""
            if q <= 8:                                                 # a fact of the murder
                if fact[q] is not None or q == 2 and len({male(c) for c in cand}) == 1: return 0
                k = {1: 0, 3: 1, 8: 2}.get(q)                          # about the murderer's place: do they disagree?
                return 10 if k is None or len(spots) != 1 and len({v[k] for v in spots}) != 1 else 3
            place = a.get('place')
            if q in (13, 14):
                gun = fact[q - 8]                                      # where that gun lies
                if place and gun and place != gun or told(s, 12) == 'N': return 0   # not there: no prints to tell
                if q == weapon_q and sex in (None, male(s)) and len({c % 2 for c in cand}) > 1:   # parity still open
                    return 8 if place and place == gun else 5
                return 2 if weapon_q is None else 1 if s in cand else 0
            if q == 12:                                                # at a gun or not
                if place and fact[5] and fact[6] or told(s, 13) or told(s, 14): return 0
                return 4 if splits(s, 3) else 3 if s in cand else 1 if sex in (None, male(s)) else 0
            if {9: 'side', 10: 'area', 11: 'place'}[q] in a: return 0  # the alibi said it already
            return 4 if splits(s, {9: 1, 10: 2, 11: 0}[q]) else 3 if s in cand else 0

        def questions(s, a):
            left = [q for q in CARDS[s] + (13, 14) if (s, q) not in asked]
            return sorted(left, key=lambda q: (-worth(s, q, a), q))

        def value(s):
            a = obs['alibi'][s] if s in visited else {}
            v = sum(worth(s, q, a) for q in questions(s, a)[:level])
            if s not in visited: v += (6 if s in cand else 2) + 3 * splits(s, 0, 1, 2)   # the alibi itself
            return v, -s

        open_ = [s for s in people if s not in visited or questions(s, {})]
        if not open_:
            return None
        s = max(open_, key=value)             # when nothing is worth anything, this still asks what is left
        visited.add(s)
        qs = questions(s, obs['alibi'][s])[:level]                 # chosen after hearing the alibi
        asked.update((s, q) for q in qs)
        worlds = {}
        cand = suspects(partial(obs, asked, visited), worlds=worlds)
        if trace is not None: trace.append((s, qs, len(cand)))
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
    from rules import observe, from_ram
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
