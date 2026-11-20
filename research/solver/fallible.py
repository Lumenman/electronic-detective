"""DRAFT, not part of the game: the rule 'a fallible witness'. (SPOILERS: playing logic.)

The rule tried here: one suspect, never the murderer, is wrong in exactly one field of his alibi - the side, the
area, the place, or one companion (named in place of a true one). Everything else he says is right, and every answer
to a question is true. The mistake never names the murderer as a companion nor leaves him out, and the alibi with the
mistake is never the whole alibi of somebody else (that would look like a lie). The player knows the rule, not who.

fallible_suspects(obs) = every suspect who can still be the murderer: m is possible if, for some heard witness w (not
m) and some field f of his alibi, everything fits once f is set aside; or if nobody heard need be wrong and somebody
other than m is still unheard. (That the field must be wrong is not used: the set may be a little too large.)

    python fallible.py full [n]           is the case solvable when everything has been asked?
    python fallible.py play [n] [level]   turns of the methodical detective taught the rule
    python fallible.py naive [n] [level]  where the usual routine ends when it trusts every alibi
    add 'kin' for a witness of the murderer's kind (sex and parity): their alibis decide who of the kind did it
    (the option 'bite' of 2026-11-20 - a mistake that misleads with everything asked - is gone: with everything
    asked a single mistake is always seen or harmless, never misleading; 1200 tried)
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'game'))
from itertools import permutations
from rules import col_of, deal, male, observe
from solver import ADDR, LETTERS, place_all, suspects

FIELDS = ('side', 'area', 'place', 'with')
KIN = False          # the variant 'kin': the witness is of the murderer's kind


def fallible_case(rng):
    """A dealt case with the mistake in: returns (obs, murderer, witness, field)."""
    case = deal(rng)
    obs, murderer = observe(case)
    alibi = obs['alibi']
    people = sorted(alibi)
    for tries in range(1000):
        w = rng.choice([s for s in people if s != murderer and (not KIN or col_of(s) == col_of(murderer))])
        f = rng.choice([f for f in FIELDS if f in alibi[w]] or ['none'])
        a = dict(alibi[w])
        if f == 'side':
            a['side'] = 3 - a['side']
        elif f == 'area':
            a['area'] = rng.choice([x for x in (3, 4, 5) if x != a['area']])
        elif f == 'place':
            a['place'] = rng.choice([l for l in LETTERS if l not in (a['place'], obs['scene'])])
        elif f == 'with':
            out = rng.choice(a['with'])
            new = [s for s in people if s not in a['with'] and s not in (w, murderer)]
            if out == murderer or not new: continue
            a['with'] = sorted(set(a['with']) - {out} | {rng.choice(new)})
        else:
            continue                                     # nothing to be wrong about
        if any(a == alibi[s] for s in people if s != w): continue
        alibi[w] = a
        return obs, murderer, w, f


def fallible_suspects(obs, worlds=None, pause=None):
    """Possible murderers under the rule (see the module text)."""
    victim, scene, alibi, ans = obs['victim'], obs['scene'], obs['alibi'], obs['ans']
    people = [s for s in range(1, 21) if s != victim]
    places = [l for l in LETTERS if l != scene]

    def known(q):
        v = {a for (s, qq), a in ans.items() if qq == q}
        assert len(v) <= 1, (q, v)
        return v.pop() if v else None
    m_east, m_male, m_area, w38, l38, l45, three, m_abc = (known(q) for q in range(1, 9))

    def unary(s, l, side, area, a):                      # as in suspects(), with the alibi a
        if a.get('place', l) != l or a.get('side', side) != side or a.get('area', area) != area: return False
        g = lambda q: ans.get((s, q))
        if g(9) is not None and (g(9) == 'Y') != (side == 2): return False
        if g(10) is not None and int(g(10)) != area: return False
        if g(11) is not None and (g(11) == 'Y') != (l in 'ABC'): return False
        if g(12) is not None and l38 and l45 and (g(12) == 'Y') != (l in (l38, l45)): return False
        if g(13) is not None and l38 and (g(13) == '?') != (l != l38): return False
        if g(14) is not None and l45 and (g(14) == '?') != (l != l45): return False
        return not (three and l == three and col_of(s) == col_of(victim))
    silent = [s for s in people if s not in alibi]
    hyps = [None] + [(w, f, o) for w in sorted(alibi) for f in FIELDS if f in alibi[w]
                     for o in (alibi[w]['with'] if f == 'with' else (None,))]
    every = [(s, o) for s, a in alibi.items() for o in a.get('with', ())]
    cats = [[s for s in people if col_of(s) == c] for c in range(4)]
    found = set()

    for perm in permutations(ADDR):
        amap = dict(zip(LETTERS, perm))
        dom = {s: {l for l in places if unary(s, l, *amap[l], alibi.get(s, {}))} for s in people}
        lost = {s for s in people if not dom[s]}
        if len(lost) > 1: continue
        if pause: pause()
        xs = [l for l in places if l not in (l38, l45)
              and (m_east is None or (m_east == 'Y') == (amap[l][0] == 2))
              and (m_area is None or int(m_area) == amap[l][1])
              and (m_abc is None or (m_abc == 'Y') == (l in 'ABC'))]
        for h in hyps:
            if h is None:                                # the wrong one is not heard yet
                if lost: continue
                base, mates = dom, every
                ms = [m for m in people if any(s != m for s in silent)]
            else:
                w, f, o = h
                if lost - {w}: continue
                a = dict(alibi[w])
                if f == 'with': a['with'] = [x for x in a['with'] if x != o]
                else: del a[f]
                base = dict(dom); base[w] = {l for l in places if unary(w, l, *amap[l], a)}
                mates = [(s, x) for s, x in every if (s, x) != (w, o)]
                ms = [m for m in people if m != w and m != o]       # the mistake never names the murderer
            for m in ms:
                if m in found or m_male is not None and (m_male == 'Y') != male(m): continue
                for x, weapon38 in ((x, wp) for x in xs if x in base[m]
                                    for wp in ((w38 == 'Y',) if w38 is not None else (True, False))):
                    d = {s: set(v) for s, v in base.items()}; d[m] = {x}
                    lw, qw = (l38, 13) if weapon38 else (l45, 14)
                    if lw:
                        for s in people:
                            an = ans.get((s, qw))
                            if an in ('Y', 'N') and male(s) == male(m) and (an == 'Y') != (m % 2 == 1): d[s].discard(lw)
                    loc = all(d.values()) and place_all(d, cats, mates, places, three)
                    if loc:
                        found.add(m)
                        if worlds is not None: worlds[m] = (amap, loc)
                        break
    return found


def partial(obs, asked, visited):
    return {'victim': obs['victim'], 'scene': obs['scene'], 'alibi': {s: obs['alibi'][s] for s in visited},
            'ans': {k: obs['ans'][k] for k in asked}}


def run(job):
    import random, par
    global KIN
    kind, seed, level, KIN = job
    obs, murderer, w, f = fallible_case(random.Random(seed))
    if kind == 'full':
        cand = fallible_suspects(obs)
        assert murderer in cand, seed
        return len(cand), f
    if kind == 'naive':                                  # the usual routine, trusting every alibi
        trace = []
        try:
            if par.methodical(obs, level, trace=trace) is None: return 'stuck'
        except AssertionError:
            return 'contradiction'
        visited = {t[0] for t in trace}; asked = {(t[0], q) for t in trace for q in t[1]}
        name = suspects(partial(obs, asked, visited)).pop()
        return 'murderer' if name == murderer else 'the witness' if name == w else 'other'
    return par.methodical(obs, level, lies=True, sus=fallible_suspects)   # lies: a place question tests an alibi


if __name__ == '__main__':
    from collections import Counter
    from multiprocessing import Pool
    kind = sys.argv[1]; n = int(sys.argv[2]) if len(sys.argv) > 2 else 100
    level = int(sys.argv[3]) if len(sys.argv) > 3 and sys.argv[3].isdigit() else 3
    print('variant: %s' % ('kin' if 'kin' in sys.argv else 'any mistake'))
    with Pool(2) as p:                                   # half of the cores stay free
        res = p.map(run, [(kind, i, level, 'kin' in sys.argv) for i in range(n)], chunksize=2)
    if kind == 'full':
        c = Counter(r[0] for r in res)
        print('everything asked, %d cases: names left %s' % (n, ' '.join('%d:%d' % kv for kv in sorted(c.items()))))
        for f in FIELDS:
            sub = [r[0] for r in res if r[1] == f]
            if sub: print('  mistake in %-5s: %d cases, solved %d' % (f, len(sub), sub.count(1)))
    elif kind == 'naive':
        print('level %d, %d cases, the detective who trusts every alibi ends with: %s' % (
            level, n, '  '.join('%s %d' % kv for kv in Counter(res).most_common())))
    else:
        v = sorted(r for r in res if r is not None)
        print('level %d, %d cases: solved %d; turns min %d  median %d  mean %.1f  max %d   %s' % (
            level, n, len(v), v[0], v[len(v) // 2], sum(v) / len(v), v[-1],
            ' '.join('%d:%d' % kv for kv in sorted(Counter(v).items()))))
