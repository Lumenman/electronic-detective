"""Is a case solvable? (SPOILERS: this is the winning logic.)

The solver knows only what the instruction tells the player (PLAYER_RULES.md, 'What the machine guarantees'):
everybody tells the truth except about fingerprints; four places hold one suspect of each category, the fifth
holds three, the scene is empty; the murderer is not at the scene nor where a gun lies; the parity of the
prints on the murder weapon is told reliably only by a suspect of the murderer's sex standing at that weapon.
It does NOT use the undocumented regularities from SPOILERS.md.

suspects(obs) returns every suspect who could be the murderer given the observations: if it is one name,
the case is solvable. obs is what rules.observe() returns, or any subset of it (fewer alibis and answers).

    python solver.py classic [n]     cases from the emulator sweep (the ROM's own deals)
    python solver.py fair [n]        random deals as made by game/dealer.py
"""
from itertools import permutations
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'game'))
from rules import CARDS, male, col_of

LETTERS = 'ABCDEF'
ADDR = [(s, a) for s in (1, 2) for a in (3, 4, 5)]


def suspects(obs, limit=None, worlds=None, only=None):
    """Set of possible murderers. limit: stop as soon as more than this many are found. only: look at these names only.
    worlds: a dict that receives one possible state of affairs per murderer: (place -> address, suspect -> place)."""
    victim, scene, alibi, ans = obs['victim'], obs['scene'], obs['alibi'], obs['ans']
    people = [s for s in range(1, 21) if s != victim]
    places = [l for l in LETTERS if l != scene]

    def known(q):                       # an answer everybody gives truthfully and identically
        v = {a for (s, qq), a in ans.items() if qq == q}
        assert len(v) <= 1, (q, v)
        return v.pop() if v else None
    m_east, m_male, m_area, w38, l38, l45, three, m_abc = (known(q) for q in range(1, 9))

    def unary(s, l, side, area):        # could suspect s be at place l, if l has this address?
        a = alibi.get(s, {})
        if a.get('place', l) != l or a.get('side', side) != side or a.get('area', area) != area: return False
        g = lambda q: ans.get((s, q))
        if g(9) is not None and (g(9) == 'Y') != (side == 2): return False
        if g(10) is not None and int(g(10)) != area: return False
        if g(11) is not None and (g(11) == 'Y') != (l in 'ABC'): return False
        if g(12) is not None and l38 and l45 and (g(12) == 'Y') != (l in (l38, l45)): return False
        if g(13) is not None and l38 and (g(13) == '?') != (l != l38): return False
        if g(14) is not None and l45 and (g(14) == '?') != (l != l45): return False
        if three and l == three and col_of(s) == col_of(victim): return False
        return True
    mates = [(s, m) for s, a in alibi.items() for m in a.get('with', ())]
    cats = [[s for s in people if col_of(s) == c] for c in range(4)]
    found = set()

    for perm in permutations(ADDR):
        amap = dict(zip(LETTERS, perm))
        dom = {s: {l for l in places if unary(s, l, *amap[l])} for s in people}
        if not all(dom.values()): continue
        # where the murderer went, as far as the answers say
        xs = [l for l in places if l not in (l38, l45)
              and (m_east is None or (m_east == 'Y') == (amap[l][0] == 2))
              and (m_area is None or int(m_area) == amap[l][1])
              and (m_abc is None or (m_abc == 'Y') == (l in 'ABC'))]
        for m in people:
            if m in found or only is not None and m not in only or (m_male is not None and (m_male == 'Y') != male(m)): continue
            for x in xs:
                if x not in dom[m]: continue
                for weapon38 in ((w38 == 'Y',) if w38 is not None else (True, False)):
                    d = {s: set(v) for s, v in dom.items()}; d[m] = {x}
                    lw, qw = (l38, 13) if weapon38 else (l45, 14)
                    if lw:                                   # a witness of the murderer's sex at the weapon is reliable
                        for s in people:
                            a = ans.get((s, qw))
                            if a in ('Y', 'N') and male(s) == male(m) and (a == 'Y') != (m % 2 == 1): d[s].discard(lw)
                    loc = all(d.values()) and place_all(d, cats, mates, places, three)
                    if loc:
                        found.add(m)
                        if worlds is not None: worlds[m] = (amap, loc)
                        break
                if m in found: break
            if limit is not None and len(found) > limit: return found
    return found


def lie_suspects(obs, worlds=None, pause=None):
    """suspects() for the game of two false alibis (rules.deal_lies): the murderer and one more suspect lie in the
    alibi, every answer to a question is true. m is possible if, for some second liar, everything fits once the
    alibis of the two are set aside. Per arrangement of addresses every choice of up to two heard alibis is tried
    (it must cover everybody whose word fits no place). A heard alibi is set aside only if it can be a lie: a liar
    repeats the alibi of an honest suspect of his kind, so another one of that kind, not the other liar, must have
    told the same or not be heard yet (research/solver/lies_twin_stats.txt). That the twin was at another place
    without a gun is not used.
    pause: called between arrangements; the game holds the counting there while a sound plays."""
    from itertools import combinations
    victim, scene, alibi, ans = obs['victim'], obs['scene'], obs['alibi'], obs['ans']
    people = [s for s in range(1, 21) if s != victim]
    places = [l for l in LETTERS if l != scene]

    def known(q):
        v = {a for (s, qq), a in ans.items() if qq == q}
        assert len(v) <= 1, (q, v)
        return v.pop() if v else None
    m_east, m_male, m_area, w38, l38, l45, three, m_abc = (known(q) for q in range(1, 9))

    def unary(s, l, side, area, word):                   # as in suspects(); word: the alibi counts
        a = alibi.get(s, {}) if word else {}
        if a.get('place', l) != l or a.get('side', side) != side or a.get('area', area) != area: return False
        g = lambda q: ans.get((s, q))
        if g(9) is not None and (g(9) == 'Y') != (side == 2): return False
        if g(10) is not None and int(g(10)) != area: return False
        if g(11) is not None and (g(11) == 'Y') != (l in 'ABC'): return False
        if g(12) is not None and l38 and l45 and (g(12) == 'Y') != (l in (l38, l45)): return False
        if g(13) is not None and l38 and (g(13) == '?') != (l != l38): return False
        if g(14) is not None and l45 and (g(14) == '?') != (l != l45): return False
        return not (three and l == three and col_of(s) == col_of(victim))
    spoke = sorted(alibi)
    silent = [s for s in people if s not in alibi]
    choices = [()] * (len(silent) > 1) + [(a,) for a in spoke] + list(combinations(spoke, 2))
    twin = lambda a, liars: any(o != a and o not in liars and col_of(o) == col_of(a)
                                and (o not in alibi or alibi[o] == alibi[a]) for o in people)
    choices = [c for c in choices if all(twin(a, c) for a in c)]
    cats = [[s for s in people if col_of(s) == c] for c in range(4)]
    found, done = set(), set()

    for perm in permutations(ADDR):
        amap = dict(zip(LETTERS, perm))
        dom = {s: {l for l in places if unary(s, l, *amap[l], True)} for s in people}
        lost = {s for s in people if not dom[s]}
        if len(lost) > 2: continue
        if pause: pause()
        loose = {s: {l for l in places if unary(s, l, *amap[l], False)} for s in spoke}
        xs = [l for l in places if l not in (l38, l45)
              and (m_east is None or (m_east == 'Y') == (amap[l][0] == 2))
              and (m_area is None or int(m_area) == amap[l][1])
              and (m_abc is None or (m_abc == 'Y') == (l in 'ABC'))]
        for liars in choices:
            if not lost <= set(liars): continue
            ms = [m for m in (liars if len(liars) == 2 else silent + list(liars))
                  if m not in found and (m_male is None or (m_male == 'Y') == male(m))]
            if not ms: continue
            mates = [(s, o) for s, a in alibi.items() if s not in liars for o in a.get('with', ())]
            base = {s: loose[s] if s in liars else dom[s] for s in people}
            for m in ms:
                for x, weapon38 in ((x, w) for x in xs if x in base[m]
                                    for w in ((w38 == 'Y',) if w38 is not None else (True, False))):
                    d = {s: set(v) for s, v in base.items()}; d[m] = {x}
                    lw, qw = (l38, 13) if weapon38 else (l45, 14)
                    if lw:
                        for s in people:
                            a = ans.get((s, qw))
                            if a in ('Y', 'N') and male(s) == male(m) and (a == 'Y') != (m % 2 == 1): d[s].discard(lw)
                    loc = all(d.values()) and place_all(d, cats, mates, places, three)
                    if loc:
                        found.add(m)
                        if worlds is not None: worlds[m] = (amap, loc)
                        break
    return found


def place_all(dom, cats, mates, places, three):
    """Can everybody be placed? One of each category per place of four; companions together.
    Returns one such placement (suspect -> place), or False."""
    dom = {s: set(v) for s, v in dom.items()}
    cat_of = {s: c for c, members in enumerate(cats) for s in members}
    pairs = {}
    for a, b in mates:
        pairs.setdefault(a, []).append(b); pairs.setdefault(b, []).append(a)

    def assign(s, l, trail):
        """Fix s at l and propagate; False on contradiction."""
        stack = [(s, l)]
        while stack:
            s, l = stack.pop()
            if l not in dom[s]: return False
            if len(dom[s]) > 1: trail.append((s, dom[s])); dom[s] = {l}
            for o in cats[cat_of[s]]:                      # same category: different places
                if o != s and l in dom[o]:
                    trail.append((o, dom[o])); dom[o] = dom[o] - {l}
                    if not dom[o]: return False
                    if len(dom[o]) == 1: stack.append((o, next(iter(dom[o]))))
            for o in pairs.get(s, ()):                     # companions: same place
                if dom[o] != {l}: stack.append((o, l))
        return True

    def ok_final():
        loc = {s: next(iter(v)) for s, v in dom.items()}
        if any(loc[a] != loc[b] for a, b in mates): return False
        for members in cats:
            if len({loc[s] for s in members}) != len(members): return False
        count = {l: sum(1 for s in loc if loc[s] == l) for l in places}
        return sorted(count.values()) == [3, 4, 4, 4, 4] and (three is None or count[three] == 3)

    def search():
        open_ = [s for s in dom if len(dom[s]) > 1]
        if not open_:
            return ok_final() and {s: next(iter(v)) for s, v in dom.items()}
        s = min(open_, key=lambda x: len(dom[x]))
        for l in sorted(dom[s]):
            trail = []
            r = assign(s, l, trail) and search()
            if r: return r
            for o, old in reversed(trail): dom[o] = old
        return False

    trail = []
    for s in list(dom):                                    # initial propagation of the already fixed ones
        if len(dom[s]) == 1 and not assign(s, next(iter(dom[s])), trail): return False
    return search()


# ---------------------------------------------------------------- experiments
from rules import deal as random_case


def run(job):
    import random
    from rules import observe, from_ram
    kind, arg = job
    case = random_case(random.Random(arg)) if kind == 'fair' else from_ram(arg)
    obs, murderer = observe(case)
    found = suspects(obs)
    return murderer in found, len(found), arg if kind == 'fair' else None


if __name__ == '__main__':
    import json, os, sys
    from collections import Counter
    from multiprocessing import Pool
    kind = sys.argv[1]; n = int(sys.argv[2]) if len(sys.argv) > 2 else 200
    here = os.path.dirname(os.path.abspath(__file__))
    if kind == 'fair':
        jobs = [('fair', i) for i in range(n)]
    else:
        rams = [[int(c, 16) for c in json.loads(l)['ram']] for l in open(os.path.join(here, '..', 'emu', 'sweep1.jsonl'))]
        jobs = [('classic', r) for r in rams[:n]]
    sizes = Counter(); wrong = 0; hard = []
    with Pool(2) as p:
        for ok, k, seed in p.imap_unordered(run, jobs, chunksize=4):
            sizes[k] += 1; wrong += not ok
            if k != 1 and seed is not None: hard.append(seed)
    print('%s: %d cases; possible murderers per case: %s; true murderer missing in %d' % (
        kind, len(jobs), dict(sorted(sizes.items())), wrong))
    if hard: print('deals with more than one possible murderer (seeds):', sorted(hard)[:40])
