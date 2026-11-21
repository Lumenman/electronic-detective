"""DRAFT, not part of the game: the rule 'everybody lies' (alibi = not here). (SPOILERS: playing logic.)

The rule tried here: every alibi is false in every field it shows, and everybody's, the murderer's too. The side
named is the other side (so the side is known all the same); the area is one of the two others; the place is another
place, never that of the body; each companion named is somebody of the same sex and parity as a true companion, who
was elsewhere. Which fields an alibi shows is as in the original (it follows the true position). Every answer to a
question is true; the prints are as always.

liar_suspects(obs) = every suspect who can still be the murderer, reading an alibi as: not this side (= the other),
not this area, not this place, not with these people. (That a named companion has the kind of a true one is used only
where it is sure to tell something: the place of three has nobody of the victim's kind.)

    python liar.py full [n]           how many deals can be solved when everything is asked? (no check)
    python liar.py play [n] [level]   turns of the methodical detective on deals that can be solved
    python liar.py cut [n]            par at levels 1-3 per case; what a cap on the level-2 par cuts and leaves
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'game'))
from itertools import permutations
from rules import col_of, deal, male, observe
from solver import ADDR, LETTERS, place_all


def liar_case(rng):
    """A dealt case with every alibi turned false: returns (obs, murderer)."""
    case = deal(rng)
    obs, murderer = observe(case)
    victim, scene = obs['victim'], obs['scene']
    people = sorted(obs['alibi'])
    cats = [[s for s in people if col_of(s) == c] for c in range(4)]
    for s in people:
        a, b = obs['alibi'][s], {}
        if 'side' in a: b['side'] = 3 - a['side']
        if 'area' in a: b['area'] = rng.choice([x for x in (3, 4, 5) if x != a['area']])
        if 'place' in a: b['place'] = rng.choice([l for l in LETTERS if l not in (a['place'], scene)])
        if 'with' in a:              # somebody of the same kind as each true companion, from another place
            b['with'] = sorted(rng.choice([o for o in cats[col_of(c)] if o != c]) for c in a['with'])
        obs['alibi'][s] = b
    return obs, murderer


def liar_suspects(obs, worlds=None, pause=None):
    """Possible murderers under the rule (see the module text); suspects() with the alibi read as 'not here'."""
    victim, scene, alibi, ans = obs['victim'], obs['scene'], obs['alibi'], obs['ans']
    people = [s for s in range(1, 21) if s != victim]
    places = [l for l in LETTERS if l != scene]

    def known(q):
        v = {a for (s, qq), a in ans.items() if qq == q}
        assert len(v) <= 1, (q, v)
        return v.pop() if v else None
    m_east, m_male, m_area, w38, l38, l45, three, m_abc = (known(q) for q in range(1, 9))

    def unary(s, l, side, area):
        a = alibi.get(s, {})
        if a.get('place') == l or a.get('side') == side or a.get('area') == area: return False
        g = lambda q: ans.get((s, q))
        if g(9) is not None and (g(9) == 'Y') != (side == 2): return False
        if g(10) is not None and int(g(10)) != area: return False
        if g(11) is not None and (g(11) == 'Y') != (l in 'ABC'): return False
        if g(12) is not None and l38 and l45 and (g(12) == 'Y') != (l in (l38, l45)): return False
        if g(13) is not None and l38 and (g(13) == '?') != (l != l38): return False
        if g(14) is not None and l45 and (g(14) == '?') != (l != l45): return False
        if three and l == three and (col_of(s) == col_of(victim)
                                     or any(col_of(x) == col_of(victim) for x in a.get('with', ()))): return False
        return True
    apart = [(s, x) for s, a in alibi.items() for x in a.get('with', ())]
    cats = [[s for s in people if col_of(s) == c] for c in range(4)]
    found = set()

    for perm in permutations(ADDR):
        amap = dict(zip(LETTERS, perm))
        dom = {s: {l for l in places if unary(s, l, *amap[l])} for s in people}
        if not all(dom.values()): continue
        if pause: pause()
        xs = [l for l in places if l not in (l38, l45)
              and (m_east is None or (m_east == 'Y') == (amap[l][0] == 2))
              and (m_area is None or int(m_area) == amap[l][1])
              and (m_abc is None or (m_abc == 'Y') == (l in 'ABC'))]
        for m in people:
            if m in found or m_male is not None and (m_male == 'Y') != male(m): continue
            for x, weapon38 in ((x, w) for x in xs if x in dom[m]
                                for w in ((w38 == 'Y',) if w38 is not None else (True, False))):
                d = {s: set(v) for s, v in dom.items()}; d[m] = {x}
                lw, qw = (l38, 13) if weapon38 else (l45, 14)
                if lw:
                    for s in people:
                        an = ans.get((s, qw))
                        if an in ('Y', 'N') and male(s) == male(m) and (an == 'Y') != (m % 2 == 1): d[s].discard(lw)
                loc = all(d.values()) and place_all(d, cats, [], places, three, apart)
                if loc:
                    found.add(m)
                    if worlds is not None: worlds[m] = (amap, loc)
                    break
    return found


def solvable_case(rng):
    """The first deal of rng that can be solved when everything is asked, and how many were skipped."""
    skip = 0
    while True:
        obs, murderer = liar_case(rng)
        if liar_suspects(obs) == {murderer}: return obs, murderer, skip
        skip += 1


def run(job):
    import random, par
    kind, seed, level = job
    if kind == 'full':
        obs, murderer = liar_case(random.Random(seed))
        cand = liar_suspects(obs)
        assert murderer in cand, seed
        return len(cand)
    obs, murderer, skip = solvable_case(random.Random(seed))
    if kind == 'cut': return [par.methodical(obs, lv, sus=liar_suspects, inverted=True) for lv in (1, 2, 3)]
    return par.methodical(obs, level, sus=liar_suspects, inverted=True), skip


if __name__ == '__main__':
    from collections import Counter
    from multiprocessing import Pool
    kind = sys.argv[1]; n = int(sys.argv[2]) if len(sys.argv) > 2 else 100
    level = int(sys.argv[3]) if len(sys.argv) > 3 else 3
    with Pool(2) as p:                                   # half of the cores stay free
        res = p.map(run, [(kind, i, level) for i in range(n)], chunksize=2)
    if kind == 'cut':
        stat = lambda v: 'median %2d  mean %4.1f  max %2d' % (v[len(v) // 2], sum(v) / len(v), v[-1]) if v else '-'
        for cap in (None, 30, 25, 20, 16, 14, 12):
            keep = [r for r in res if None not in r and (cap is None or r[1] <= cap)]
            print('level-2 par <= %-4s keeps %3d%%   ' % (cap or 'any', 100 * len(keep) // n) + '   '.join(
                'L%d: %s' % (lv, stat(sorted(r[lv - 1] for r in keep))) for lv in (1, 2, 3)))
    elif kind == 'full':
        c = Counter(res)
        print('everything asked, %d deals: names left %s; solvable %d%%' % (
            n, ' '.join('%d:%d' % kv for kv in sorted(c.items())), 100 * c[1] // n))
    else:
        v = sorted(r[0] for r in res if r[0] is not None); skips = [r[1] for r in res]
        print('level %d, %d solvable cases (deals skipped per case: mean %.1f): solved %d; turns min %d  median %d  '
              'mean %.1f  max %d   %s' % (level, n, sum(skips) / n, len(v), v[0], v[len(v) // 2], sum(v) / len(v), v[-1],
                                         ' '.join('%d:%d' % kv for kv in sorted(Counter(v).items()))))
