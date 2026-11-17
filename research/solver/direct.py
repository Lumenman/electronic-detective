"""A detective who reasons the way a person can: no trying of the 720 arrangements of addresses. (SPOILERS: playing logic.)

direct_suspects(obs) keeps, per place, the addresses still possible and, per suspect, the places still possible,
and narrows them by forced steps only:
  - a suspect's alibi and own answers (9-12) against the place and its possible addresses;
  - a suspect known to be at a place fixes what that place's address can be;
  - every place has its own address (a value left in one place only goes there);
  - one suspect of each category per place (the victim's category misses the place of three); companions together.
A suspect stays a possible murderer unless the single supposition 'he did it' (his place then matches questions
1, 3, 8 and holds no gun; the prints rule as in solver.suspects) runs into a contradiction by these steps alone.
Sound like solver.suspects (it only removes what cannot be), weaker: it never tries 'if ... then ...' twice.

Depth of a case: replay the questioning of par.methodical (with the full solver) and see on which turn the direct
detective is left with one name: the same turn, later (needs more than was asked), or never (not even with
everything asked: the case needs trying of arrangements somewhere).

    python direct.py n      n cases of the ordinary game, levels 3 and 1
"""
import os, random, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..', '..', 'game'))
from rules import col_of, male, deal, observe

LETTERS = 'ABCDEF'
ADDR = [(s, a) for s in (1, 2) for a in (3, 4, 5)]


def direct_suspects(obs):
    victim, scene, alibi, ans = obs['victim'], obs['scene'], obs['alibi'], obs['ans']
    people = [s for s in range(1, 21) if s != victim]
    places = [l for l in LETTERS if l != scene]

    def known(q):
        v = {a for (s, qq), a in ans.items() if qq == q}
        return v.pop() if v else None
    m_east, m_male, m_area, w38, l38, l45, three, m_abc = (known(q) for q in range(1, 9))
    vcat = col_of(victim)
    cats = [[s for s in people if col_of(s) == c] for c in range(4)]
    pairs = [(s, o) for s, a in alibi.items() for o in a.get('with', ()) if o != victim]

    def addr_ok(s, a):                                  # what s said about his own side and area
        side, area = a; al = alibi.get(s, {}); g = lambda q: ans.get((s, q))
        if al.get('side', side) != side or al.get('area', area) != area: return False
        if g(9) is not None and (g(9) == 'Y') != (side == 2): return False
        return g(10) is None or int(g(10)) == area

    def letter_ok(s, l):                                # ... and about the place itself
        al = alibi.get(s, {}); g = lambda q: ans.get((s, q))
        if al.get('place', l) != l: return False
        if g(11) is not None and (g(11) == 'Y') != (l in 'ABC'): return False
        if g(12) is not None and l38 and l45 and (g(12) == 'Y') != (l in (l38, l45)): return False
        if g(13) is not None and l38 and (g(13) == '?') != (l != l38): return False
        if g(14) is not None and l45 and (g(14) == '?') != (l != l45): return False
        return not (three and l == three and col_of(s) == vcat)

    A0 = {l: set(ADDR) for l in LETTERS}
    P0 = {s: {l for l in places if letter_ok(s, l)} for s in people}

    def propagate(A, P, m, mfit):
        ok_a = lambda s, a: addr_ok(s, a) and (s != m or mfit(a))
        changed = True
        while changed:
            changed = False
            def setp(s, new):
                nonlocal changed
                if new != P[s]: P[s] = new; changed = True
                return bool(new)
            def seta(l, new):
                nonlocal changed
                if new != A[l]: A[l] = new; changed = True
                return bool(new)
            for s in people:                             # a place fits s only if one of its addresses does
                if not setp(s, {l for l in P[s] if any(ok_a(s, a) for a in A[l])}): return False
                if len(P[s]) == 1:                       # s is surely there: the place's address fits s
                    l = next(iter(P[s]))
                    if not seta(l, {a for a in A[l] if ok_a(s, a)}): return False
            for l in LETTERS:                            # every place its own address
                if len(A[l]) == 1:
                    a = next(iter(A[l]))
                    for o in LETTERS:
                        if o != l and a in A[o] and not seta(o, A[o] - {a}): return False
            for a in ADDR:
                holders = [l for l in LETTERS if a in A[l]]
                if not holders: return False
                if len(holders) == 1 and len(A[holders[0]]) > 1: seta(holders[0], {a})
            for c, members in enumerate(cats):           # one of each category per place
                for s in members:
                    if len(P[s]) == 1:
                        l = next(iter(P[s]))
                        for o in members:
                            if o != s and l in P[o] and not setp(o, P[o] - {l}): return False
                need = places if c != vcat else ([l for l in places if l != three] if three else [])
                for l in need:
                    holders = [s for s in members if l in P[s]]
                    if not holders: return False
                    if len(holders) == 1 and len(P[holders[0]]) > 1: setp(holders[0], {l})
            for a, b in pairs:                           # companions together
                both = P[a] & P[b]
                if not setp(a, both) or not setp(b, set(both)): return False
        return True

    found = set()
    for m in people:
        if m_male is not None and (m_male == 'Y') != male(m): continue
        mfit = lambda a: (m_east is None or (m_east == 'Y') == (a[0] == 2)) and (m_area is None or int(m_area) == a[1])
        for weapon38 in ((w38 == 'Y',) if w38 is not None else (True, False)):
            A = {l: set(v) for l, v in A0.items()}; P = {s: set(v) for s, v in P0.items()}
            P[m] = {l for l in P[m] if l not in (l38, l45) and (m_abc is None or (m_abc == 'Y') == (l in 'ABC'))}
            lw, qw = (l38, 13) if weapon38 else (l45, 14)
            if lw:
                for s in people:
                    a = ans.get((s, qw))
                    if a in ('Y', 'N') and male(s) == male(m) and (a == 'Y') != (m % 2 == 1): P[s].discard(lw)
            if all(P.values()) and propagate(A, P, m, mfit):
                found.add(m); break
    return found


def run(job):
    import par
    seed, levels = job
    obs, m = observe(deal(random.Random(seed)))
    assert m in direct_suspects(obs), seed
    full_alone = len(direct_suspects(obs)) == 1
    out = []
    for lv in levels:
        trace = []
        n_full = par.methodical(obs, lv, trace=trace)
        visited, asked, n_direct, left = set(), set(), None, None
        for t, (s, qs, _) in enumerate(trace, 1):
            visited.add(s); asked.update((s, q) for q in qs)
            sus = direct_suspects(par.partial(obs, asked, visited))
            assert m in sus, (seed, lv, t)
            left = len(sus)                      # at the turn the full solver is done: names still open
            if len(sus) == 1: n_direct = t; break
        out.append((n_full, n_direct, full_alone, left))
    return out


if __name__ == '__main__':
    from multiprocessing import Pool
    from collections import Counter
    n = int(sys.argv[1]); levels = (3, 1)
    with Pool(2) as p:
        res = p.map(run, [(s, levels) for s in range(n)], chunksize=2)
    print('ordinary game, %d cases. With everything asked the direct detective names the murderer in %d' % (
        n, sum(r[0][2] for r in res)))
    import json
    with open(os.path.join(HERE, 'direct_cases.json'), 'w') as f:          # seeds by depth, for a look later
        json.dump({lv: {'same': [s for s, r in enumerate(res) if r[i][1] is not None],
                        'deep': [s for s, r in enumerate(res) if r[i][1] is None]} for i, lv in enumerate(levels)}, f)
    for i, lv in enumerate(levels):
        c = Counter('same turn' if d == f else 'later' if d is None and al else 'never' if d is None else 'earlier?'
                    for f, d, al, _ in (r[i] for r in res))
        left = Counter(r[i][3] for r in res if r[i][1] is None)
        print('  level %d: the direct detective is done %s; names still open when the full one is done: %s' % (
            lv, dict(c), dict(sorted(left.items()))))
