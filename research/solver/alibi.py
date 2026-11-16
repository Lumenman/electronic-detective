"""DRAFT, not part of the game: the third game's rule 'two false alibis'. (SPOILERS: playing logic.)

The rule tried here: the murderer and one other suspect (anybody, with something else to hide) each say they were
at a place where they were not: they give the alibi of the suspect of their own kind (sex and parity) who really
was there, and answer the questions about their own whereabouts (9-14) to match. Everybody else tells the truth,
and so do these two about the murder (questions 1-8). The player knows the rule, not the names.

lie_suspects(obs) = every suspect who can still be the murderer: m is possible if for some second liar c
solver.suspects() still allows m once what m and c say about themselves is set aside. (That their stories must
be false is not used: the set may be a little too large.)

    python alibi.py full [n]            is the case solvable when everything has been asked?
    python alibi.py play [n] [level]    turns of the methodical detective taught the rule
    python alibi.py naive [n] [level]   where the usual routine ends when it trusts everybody
    add 'check' for the variant where the two lie in the alibi only (a question to them can then test it)
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'game'))
from itertools import combinations, permutations
from rules import CARDS, OFF_CARD, col_of, deal, male, observe
from solver import ADDR, LETTERS, place_all, suspects
import frame

OWN = (9, 10, 11, 12, 13, 14)
CHECK = False        # the variant 'check': the liars lie in the alibi only and answer every question truthfully


def lie_case(rng):
    """A dealt case with the two false alibis in: returns (obs, murderer, second liar)."""
    case = deal(rng)
    obs, murderer = observe(case)
    rows = case['rows']
    row_of = {s: r for r, row in enumerate(rows) for s in row['people']}
    people = sorted(obs['alibi'])
    # the one of the same kind at another place without a gun (the murderer is never at a gun: nobody would say so)
    doubles = lambda s, second: [o for o in people if col_of(o) == col_of(s) and row_of[o] not in (row_of[s], 1, 2)
                                 and o not in (murderer, second)]
    second = rng.choice([s for s in people if s != murderer and doubles(s, s) and doubles(murderer, s)])
    for s in (murderer, second):
        o = rng.choice(doubles(s, second))
        row = rows[row_of[o]]
        obs['alibi'][s] = dict(obs['alibi'][o])
        own = {9: 'Y' if row['side'] == 2 else 'N', 10: str(row['area']), 11: 'Y' if row['letter'] in 'ABC' else 'N',
               12: 'N', 13: '?', 14: '?'}
        if CHECK: continue
        for q in OWN:
            if (s, q) in obs['ans']: obs['ans'][(s, q)] = own[q]
        if s in OFF_CARD: obs['hidden'][(s, 12)] = 'N'
    return obs, murderer, second


def lie_suspects(obs, worlds=None, pairs=None):
    """Possible murderers under the rule. pairs: a set that receives the possible (murderer, second liar) pairs.
    solver.suspects() with the liars inside: per arrangement of addresses, every choice of up to two suspects whose
    word about themselves is set aside (it must cover everybody whose word fits no place)."""
    victim, scene, alibi, ans = obs['victim'], obs['scene'], obs['alibi'], obs['ans']
    people = [s for s in range(1, 21) if s != victim]
    places = [l for l in LETTERS if l != scene]

    def known(q):
        v = {a for (s, qq), a in ans.items() if qq == q}
        assert len(v) <= 1, (q, v)
        return v.pop() if v else None
    m_east, m_male, m_area, w38, l38, l45, three, m_abc = (known(q) for q in range(1, 9))

    def unary(s, l, side, area, word=True):              # as in solver.suspects(); word: the alibi counts
        a = alibi.get(s, {}) if word else {}
        if a.get('place', l) != l or a.get('side', side) != side or a.get('area', area) != area: return False
        g = lambda q: ans.get((s, q))
        if g(9) is not None and (g(9) == 'Y') != (side == 2): return False
        if g(10) is not None and int(g(10)) != area: return False
        if g(11) is not None and (g(11) == 'Y') != (l in 'ABC'): return False
        if g(12) is not None and l38 and l45 and (g(12) == 'Y') != (l in (l38, l45)): return False
        if g(13) is not None and l38 and (g(13) == '?') != (l != l38): return False
        if g(14) is not None and l45 and (g(14) == '?') != (l != l45): return False
        return True
    spoke = sorted(alibi if CHECK else set(alibi) | {s for (s, q) in ans if q in OWN})   # said what may be a lie
    silent = [s for s in people if s not in spoke]
    choices = [()] * (len(silent) > 1) + [(a,) for a in spoke] + list(combinations(spoke, 2))
    cats = [[s for s in people if col_of(s) == c] for c in range(4)]
    free = {s: {l for l in places if not (three and l == three and col_of(s) == col_of(victim))} for s in people}
    found, done = set(), set()

    for perm in permutations(ADDR):
        amap = dict(zip(LETTERS, perm))
        dom = {s: {l for l in free[s] if unary(s, l, *amap[l])} for s in people}
        loose = {s: {l for l in free[s] if unary(s, l, *amap[l], False)} for s in spoke} if CHECK else free
        lost = {s for s in people if not dom[s]}
        if len(lost) > 2: continue
        xs = [l for l in places if l not in (l38, l45)
              and (m_east is None or (m_east == 'Y') == (amap[l][0] == 2))
              and (m_area is None or int(m_area) == amap[l][1])
              and (m_abc is None or (m_abc == 'Y') == (l in 'ABC'))]
        for liars in choices:
            if not lost <= set(liars): continue
            ms = liars if len(liars) == 2 else silent + list(liars)
            ms = [m for m in ms if (liars, m) not in done and (pairs is not None or m not in found)
                  and (m_male is None or (m_male == 'Y') == male(m))]
            if not ms: continue
            mates = [(s, o) for s, a in alibi.items() if s not in liars for o in a.get('with', ())]
            base = {s: loose[s] if s in liars else dom[s] for s in people}
            for m in ms:
                ok = False
                for x in xs:
                    if x not in base[m]: continue
                    for weapon38 in ((w38 == 'Y',) if w38 is not None else (True, False)):
                        d = {s: set(v) for s, v in base.items()}; d[m] = {x}
                        lw, qw = (l38, 13) if weapon38 else (l45, 14)
                        if lw:
                            for s in people:
                                a = ans.get((s, qw))
                                if (CHECK or s not in liars) and a in ('Y', 'N') and male(s) == male(m) and (a == 'Y') != (m % 2 == 1):
                                    d[s].discard(lw)
                        loc = all(d.values()) and place_all(d, cats, mates, places, three)
                        if loc:
                            ok = True
                            if worlds is not None: worlds.setdefault(m, (amap, loc))
                            break
                    if ok: break
                if ok:
                    found.add(m); done.add((liars, m))
                    if pairs is not None:
                        others = [c for c in liars if c != m] if m in liars and len(liars) == 2 else                             silent if m in liars else list(liars) if liars else silent
                        pairs.update((m, c) for c in others if c != m)
    return found


def run(job):
    import random
    global CHECK
    kind, seed, level, CHECK = job
    obs, murderer, second = lie_case(random.Random(seed))
    if kind == 'full':
        pairs = set()
        cand = lie_suspects(obs, pairs=pairs)
        assert murderer in cand and (murderer, second) in pairs, seed
        return len(cand), len(pairs)
    if kind == 'naive':
        import par
        trace = []
        if par.methodical(obs, level, trace=trace) is None:
            return 'contradiction' if any(t[2] == 0 for t in trace) else 'stuck'
        visited = {t[0] for t in trace}; asked = {(t[0], q) for t in trace for q in t[1]}
        name = suspects(frame.partial(obs, asked, visited)).pop()
        return 'murderer' if name == murderer else 'second liar' if name == second else 'other'
    return frame.methodical(obs, level, sus=lie_suspects, framed=(), check=CHECK)


if __name__ == '__main__':
    import time
    from collections import Counter
    from multiprocessing import Pool
    CHECK = 'check' in sys.argv
    if CHECK: sys.argv.remove('check'); print('variant: the liars answer every question truthfully')
    kind = sys.argv[1]; n = int(sys.argv[2]) if len(sys.argv) > 2 else 100
    level = int(sys.argv[3]) if len(sys.argv) > 3 else 3
    t0 = time.time()
    with Pool(2) as p:                                   # half of the cores stay free
        res = p.map(run, [(kind, i, level, CHECK) for i in range(n)], chunksize=1)
    if kind == 'full':
        c = Counter(r[0] for r in res)
        print('everything asked, %d cases: names left %s' % (n, ' '.join('%d:%d' % kv for kv in sorted(c.items()))))
        print('  the pair of liars known exactly in %d' % sum(r[1] == 1 for r in res))
    elif kind == 'naive':
        print('level %d, %d cases, the detective who trusts everybody ends with: %s' % (
            level, n, '  '.join('%s %d' % kv for kv in Counter(res).most_common())))
    else:
        v = sorted(r[0] for r in res if r[0] is not None); t = sorted(r[1] for r in res if r[1] is not None)
        print('level %d, %d cases: solved %d of %d' % (level, n, len(v), n))
        if v:
            print('  turns min %d  median %d  mean %.1f  max %d   %s' % (
                v[0], v[len(v) // 2], sum(v) / len(v), v[-1], ' '.join('%d:%d' % kv for kv in sorted(Counter(v).items()))))
        if t:
            print('  two or fewer names left: median turn %d, mean %.1f' % (t[len(t) // 2], sum(t) / len(t)))
    print('  (%.0f s)' % (time.time() - t0), flush=True)
