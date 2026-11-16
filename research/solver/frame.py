"""DRAFT, not part of the game: the third game's rule 'the murderer and an accomplice keep to one false story'.
(SPOILERS: playing logic.)

The rule tried here: besides the true facts of the murder there is a false version - side, sex, area and half of
town (questions 1, 2, 3, 8; FRAMED) as they would be for one innocent suspect. The murderer and one accomplice
(any other suspect) always answer these questions by the false version; everybody else tells the truth; alibis
and all other answers are as in the original. The player knows the rule, not the names.

frame_suspects(obs) = every suspect who can still be the murderer: m is possible if for some accomplice c the
answers of the others agree with each other and solver.suspects() still allows m once the framed answers of m and
c are set aside. (That the false version must fit a real person is not used: the set may be a little too large.)

    python frame.py full [n]         is the case solvable when everything has been asked?
    python frame.py play [n] [level] turns of the methodical detective (par.py's routine taught the rule)
    python frame.py naive [n] [level]  where the usual routine ends when it trusts every answer
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'game'))
from itertools import combinations
from rules import CARDS, male, deal, observe
from solver import suspects

FRAMED = (1, 2, 3, 8)


def frame_case(rng):
    """A dealt case with the lies in: returns (obs, murderer, accomplice, framed suspect)."""
    case = deal(rng)
    obs, murderer = observe(case)
    rows = case['rows']
    row_of = {s: r for r, row in enumerate(rows) for s in row['people']}
    fact = lambda s: {1: 'Y' if rows[row_of[s]]['side'] == 2 else 'N', 2: 'Y' if male(s) else 'N',
                      3: str(rows[row_of[s]]['area']), 8: 'Y' if rows[row_of[s]]['letter'] in 'ABC' else 'N'}
    people = sorted(obs['alibi'])
    accomplice = rng.choice([s for s in people if s != murderer])
    # the framed one: innocent, not at a gun (the murderer never is), and different from the truth in something
    x = rng.choice([s for s in people if s not in (murderer, accomplice) and row_of[s] not in (1, 2)
                    and fact(s) != fact(murderer)])
    for s in (murderer, accomplice):
        for q in FRAMED:
            if (s, q) in obs['ans']: obs['ans'][(s, q)] = fact(x)[q]
    return obs, murderer, accomplice, x


def frame_suspects(obs, worlds=None, pairs=None):
    """Possible murderers under the rule. pairs: a set that receives the possible (murderer, accomplice) pairs."""
    people = sorted(s for s in range(1, 21) if s != obs['victim'])
    ans = obs['ans']
    told = {}                                            # informant -> {framed question: answer}
    for (s, q), a in ans.items():
        if q in FRAMED: told.setdefault(s, {})[q] = a
    cache, found = {}, set()

    def allowed(liars):
        """Murderers solver.suspects() allows when the framed answers of these informants are set aside."""
        mine = [told[s] for s in liars]
        if len(mine) == 2 and any(mine[0][q] != mine[1][q] for q in mine[0] if q in mine[1]):
            return ()                                    # the two tell one story
        rest = {}
        for s, d in told.items():
            if s in liars: continue
            for q, a in d.items():
                if rest.setdefault(q, a) != a: return ()  # the honest ones do not contradict each other
        key = tuple(sorted(rest.items()))
        if key not in cache:
            w = {}
            o = dict(obs, ans={k: a for k, a in ans.items() if k[1] not in FRAMED})
            o['ans'].update({(0, q): a for q, a in rest.items()})      # the facts that stand, from nobody in particular
            cache[key] = suspects(o, worlds=w), w
        cand, w = cache[key]
        if worlds is not None:
            for m in cand: worlds.setdefault(m, w[m])
        return cand

    silent = [s for s in people if s not in told]
    for liars in [()] + [(a,) for a in told] + list(combinations(told, 2)):
        cand = allowed(liars)
        for m in cand:
            if len(liars) == 2: cs = [c for c in liars if c != m] if m in liars else []
            elif len(liars) == 1: cs = [c for c in silent if c != m] if m in liars else list(liars) if m in silent else []
            else: cs = [c for c in silent if c != m] if m in silent else []
            if cs:
                found.add(m)
                if pairs is not None: pairs.update((m, c) for c in cs)
    return found


def partial(obs, asked, visited):
    return {'victim': obs['victim'], 'scene': obs['scene'], 'alibi': {s: obs['alibi'][s] for s in visited},
            'ans': {k: obs['ans'][k] for k in asked}}


def methodical(obs, level, cap=150):
    """par.methodical taught the rule: a framed fact counts as known once three agree on it.
    Returns (turns until one name is left, turns until two or fewer are left)."""
    people = sorted(obs['alibi'])
    visited, asked = set(), set()
    cand, worlds, two = set(people), {}, None
    for turn in range(1, cap + 1):
        def known(q):
            v = [obs['ans'][k] for k in asked if k[1] == q]
            if q not in FRAMED: return v[0] if v else None
            return next((a for a in set(v) if v.count(a) >= 3), None)
        fact = {q: known(q) for q in range(1, 9)}
        heard = {q: sum(1 for k in asked if k[1] == q) for q in FRAMED}
        sex = None if fact[2] is None else fact[2] == 'Y'
        weapon_q = None if fact[4] is None else 13 if fact[4] == 'Y' else 14
        told = lambda s, q: obs['ans'][(s, q)] if (s, q) in asked else None
        guns = (fact[5], fact[6])
        views = lambda s: {(loc[s], *amap[loc[s]], loc[s] in guns) for amap, loc in worlds.values()}
        spots = {(amap[loc[m]][0], amap[loc[m]][1], loc[m] in 'ABC') for m, (amap, loc) in worlds.items()}
        splits = lambda s, *i: len({tuple(v[k] for k in i) for v in views(s)}) > 1

        def worth(s, q, a):
            if q <= 8:
                if fact[q] is not None or q == 2 and len({male(c) for c in cand}) == 1: return 0
                if q in FRAMED and heard[q]: return 7                  # heard, not yet sure: a second and third voice
                k = {1: 0, 3: 1, 8: 2}.get(q)
                return 10 if k is None or len(spots) != 1 and len({v[k] for v in spots}) != 1 else 3
            place = a.get('place')
            if q in (13, 14):
                gun = fact[q - 8]
                if place and gun and place != gun or told(s, 12) == 'N': return 0
                if q == weapon_q and sex in (None, male(s)) and len({c % 2 for c in cand}) > 1:
                    return 8 if place and place == gun else 5
                return 2 if weapon_q is None else 1 if s in cand else 0
            if q == 12:
                if place and fact[5] and fact[6] or told(s, 13) or told(s, 14): return 0
                return 4 if splits(s, 3) else 3 if s in cand else 1 if sex in (None, male(s)) else 0
            if {9: 'side', 10: 'area', 11: 'place'}[q] in a: return 0
            return 4 if splits(s, {9: 1, 10: 2, 11: 0}[q]) else 3 if s in cand else 0

        def questions(s, a):
            left = [q for q in CARDS[s] + (13, 14) if (s, q) not in asked]
            return sorted(left, key=lambda q: (-worth(s, q, a), q))

        def value(s):
            a = obs['alibi'][s] if s in visited else {}
            v = sum(worth(s, q, a) for q in questions(s, a)[:level])
            if s not in visited: v += (6 if s in cand else 2) + 3 * splits(s, 0, 1, 2)
            return v, -s

        open_ = [s for s in people if s not in visited or questions(s, {})]
        if not open_:
            return None, two
        s = max(open_, key=value)
        visited.add(s)
        asked.update((s, q) for q in questions(s, obs['alibi'][s])[:level])
        worlds = {}
        cand = frame_suspects(partial(obs, asked, visited), worlds=worlds)
        if two is None and len(cand) <= 2: two = turn
        if len(cand) == 1:
            return turn, two
    return None, two


def run(job):
    import random
    kind, seed, level = job
    obs, murderer, accomplice, x = frame_case(random.Random(seed))
    if kind == 'full':
        pairs = set()
        cand = frame_suspects(obs, pairs=pairs)
        assert murderer in cand and (murderer, accomplice) in pairs, seed
        return len(cand), x in cand, len(pairs)
    if kind == 'naive':                                  # the usual routine, trusting every answer
        import par
        trace = []
        try:
            if par.methodical(obs, level, trace=trace) is None: return 'stuck'
        except AssertionError:
            return 'contradiction'
        visited = {t[0] for t in trace}; asked = {(t[0], q) for t in trace for q in t[1]}
        name = suspects(partial(obs, asked, visited)).pop()
        return 'murderer' if name == murderer else 'framed' if name == x else 'accomplice' if name == accomplice else 'other'
    return methodical(obs, level)


if __name__ == '__main__':
    from collections import Counter
    from multiprocessing import Pool
    kind = sys.argv[1]; n = int(sys.argv[2]) if len(sys.argv) > 2 else 100
    level = int(sys.argv[3]) if len(sys.argv) > 3 else 3
    with Pool(2) as p:                                   # half of the cores stay free
        res = p.map(run, [(kind, i, level) for i in range(n)], chunksize=2)
    if kind == 'full':
        c = Counter(r[0] for r in res)
        print('everything asked, %d cases: names left %s' % (n, ' '.join('%d:%d' % kv for kv in sorted(c.items()))))
        print('  the framed one still possible in %d; the pair of liars known exactly in %d' % (
            sum(r[1] for r in res), sum(r[2] == 1 for r in res)))
    elif kind == 'naive':
        print('level %d, %d cases, the detective who trusts every answer ends with: %s' % (
            level, n, '  '.join('%s %d' % kv for kv in Counter(res).most_common())))
    else:
        v = sorted(r[0] for r in res if r[0] is not None); t = sorted(r[1] for r in res if r[1] is not None)
        print('level %d, %d cases: solved %d; turns min %d  median %d  mean %.1f  max %d   %s' % (
            level, n, len(v), v[0], v[len(v) // 2], sum(v) / len(v), v[-1],
            ' '.join('%d:%d' % kv for kv in sorted(Counter(v).items()))))
        print('  two or fewer names left: median turn %d, mean %.1f' % (t[len(t) // 2], sum(t) / len(t)))
