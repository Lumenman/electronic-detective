"""How much faster does a player solve the MK-61 cases if they know row = (a*k + b) mod 5?

A player who knows the program knows the rows too: row 0 is the murderer's place, 1 the .38, 2 the .45, 3 the other
place of four, 4 the place of three (the victim's row), the scene holds nobody. struct_suspects() enumerates worlds
(addresses of the places, row -> place, one layout per column from PERMS) and returns the possible murderers.
With PERMS = all 120 layouts it is the same reasoning without the formula: the control.

    affine_known.py n [levels]     n affine cases; prints turns of the methodical player for three solvers
"""
import os, random, sys, time
from itertools import permutations
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..', '..', 'game'))
from rules import observe, male, col_of
import solver, par
from affine import affine_deal, BASE

LETTERS, ADDR = solver.LETTERS, solver.ADDR
AFFINE = sorted({tuple((a * k + b) % 5 for k in range(5)) for a in range(1, 5) for b in range(5)})
ALL = sorted(permutations(range(5)))
KIDX = {s: (c, k) for c, col in enumerate(BASE) for k, s in enumerate(col)}


def struct_suspects(obs, perms, worlds=None, limit=None, only=None):
    victim, scene, alibi, ans = obs['victim'], obs['scene'], obs['alibi'], obs['ans']
    people = [s for s in range(1, 21) if s != victim]
    places = [l for l in LETTERS if l != scene]
    vc, vk = KIDX[victim]

    def known(q):
        v = {a for (s, qq), a in ans.items() if qq == q}
        return v.pop() if v else None
    m_east, m_male, m_area, w38, l38, l45, three, m_abc = (known(q) for q in range(1, 9))

    rows_ok = {}                       # rows allowed by the answers about guns (12, 13, 14), whatever the addresses
    for s in people:
        g = lambda q: ans.get((s, q))
        rows_ok[s] = {r for r in range(5) if (g(12) is None or (g(12) == 'Y') == (r in (1, 2)))
                      and (g(13) is None or (g(13) == '?') == (r != 1)) and (g(14) is None or (g(14) == '?') == (r != 2))}

    def letter_ok(s, l, side, area):
        a = alibi.get(s, {})
        if a.get('place', l) != l or a.get('side', side) != side or a.get('area', area) != area: return False
        g = lambda q: ans.get((s, q))
        if g(9) is not None and (g(9) == 'Y') != (side == 2): return False
        if g(10) is not None and int(g(10)) != area: return False
        if g(11) is not None and (g(11) == 'Y') != (l in 'ABC'): return False
        return True
    pairs = [(s, m) for s, a in alibi.items() for m in a.get('with', ())]
    found = set()
    okmask = {s: sum(1 << r for r in rows_ok[s]) for s in people}
    memo = {}
    xp = {}                            # companions in two columns: (column, column) -> [(index, index)], both ways
    for a, b in pairs:
        (ca, ka), (cb, kb) = KIDX[a], KIDX[b]
        if ca == cb: return set()      # one category, so two places: no world fits (never happens with true alibis)
        xp.setdefault((ca, cb), []).append((ka, kb)); xp.setdefault((cb, ca), []).append((kb, ka))
    cats = [[s for s in people if col_of(s) == c] for c in range(4)]
    could = {s for s in people if (m_male is None or (m_male == 'Y') == male(s)) and (only is None or s in only)}

    for aperm in permutations(ADDR):
        amap = dict(zip(LETTERS, aperm))
        dom = {s: [l for l in places if letter_ok(s, l, *amap[l])] for s in people}
        if not all(dom.values()): continue
        for rl in permutations(places):            # rl[r] = the place of row r
            if l38 and rl[1] != l38 or l45 and rl[2] != l45 or three and rl[4] != three: continue
            x = rl[0]; sx, ax = amap[x]
            if m_east and (m_east == 'Y') != (sx == 2) or m_area and int(m_area) != ax or m_abc and (m_abc == 'Y') != (x in 'ABC'):
                continue
            bit = {l: 1 << r for r, l in enumerate(rl)}
            mask = {s: sum(bit[l] for l in dom[s]) & okmask[s] for s in people}
            mask[victim] = 16
            if not all(mask.values()): continue
            if perms is ALL:                   # control: any layout, so a placement search does the same job faster
                for s in BASE[vc]: mask[s] &= 15                    # the victim's category is not at the place of three
                d0 = {s: {rl[r] for r in range(5) if mask[s] >> r & 1} for s in people}
                if not all(d0.values()): continue
                for m in sorted(could - found):
                    if x not in d0[m]: continue
                    for weapon38 in ((w38 == 'Y',) if w38 is not None else (True, False)):
                        wr, qw = (1, 13) if weapon38 else (2, 14)
                        d = {s: set(v) for s, v in d0.items()}; d[m] = {x}
                        for s in people:
                            if ans.get((s, qw)) in ('Y', 'N') and male(s) == male(m) and (ans[(s, qw)] == 'Y') != (m % 2 == 1):
                                d[s].discard(rl[wr])
                        loc = all(d.values()) and solver.place_all(d, cats, pairs, places, rl[4])
                        if loc:
                            found.add(m)
                            if worlds is not None: worlds[m] = (amap, loc)
                            break
                if found >= could: return found
                continue
            cols = []
            for c, col in enumerate(BASE):
                key = (c, tuple(mask[s] for s in col))
                v = memo.get(key)
                if v is None:
                    v = memo[key] = [p for p in perms if all(key[1][k] >> p[k] & 1 for k in range(5))]
                if not v: break
                cols.append(v)
            else:
                for mc in range(4):
                    for p0 in cols[mc]:
                        m = BASE[mc][p0.index(0)]
                        if m in found or m == victim or only is not None and m not in only: continue
                        if m_male is not None and (m_male == 'Y') != male(m): continue
                        for weapon38 in ((w38 == 'Y',) if w38 is not None else (True, False)):
                            wr, qw = (1, 13) if weapon38 else (2, 14)
                            bad = {s for s in people if ans.get((s, qw)) in ('Y', 'N') and male(s) == male(m)
                                   and (ans[(s, qw)] == 'Y') != (m % 2 == 1)}       # these are not at the weapon
                            cc = [[p for p in (cols[c] if c != mc else [p0])
                                   if all(p[k] != wr for k, s in enumerate(BASE[c]) if s in bad)] for c in range(4)]
                            def dfs(lists, chosen):   # forward checking: a choice prunes the other columns at once
                                if len(chosen) == 4: return chosen
                                c = min((c for c in range(4) if c not in chosen), key=lambda c: len(lists[c]))
                                for p in lists[c]:
                                    nl = dict(lists)
                                    for c2 in range(4):
                                        if c2 in chosen or c2 == c: continue
                                        kk = xp.get((c, c2))
                                        if kk: nl[c2] = [q for q in lists[c2] if all(p[k1] == q[k2] for k1, k2 in kk)]
                                        if not nl[c2]: break
                                    else:
                                        r = dfs(nl, {**chosen, c: p})
                                        if r: return r
                                return None
                            got = all(cc) and dfs(dict(enumerate(cc)), {})
                            if got:
                                found.add(m)
                                if worlds is not None:
                                    worlds[m] = (amap, {s: rl[got[c][k]] for c in range(4) for k, s in enumerate(BASE[c]) if s != victim})
                                break
                if limit is not None and len(found) > limit or found >= could: return found
    return found


def run(job):
    seed, levels = job
    obs, m = observe(affine_deal(random.Random(seed)))
    out = {}
    for name, fn in (('base', solver.suspects), ('affine', lambda o, **kw: struct_suspects(o, AFFINE, **kw)),
                     ('control', lambda o, **kw: struct_suspects(o, ALL, **kw))):
        par.suspects = fn
        assert fn(obs) == {m}, (seed, name)
        t = time.time(); out[name] = [par.methodical(obs, lv) for lv in levels]; out['t_' + name] = round(time.time() - t)
    return seed, out


if __name__ == '__main__':
    from multiprocessing import Pool
    n = int(sys.argv[1]); levels = [int(c) for c in sys.argv[2]] if len(sys.argv) > 2 else [3, 2, 1]
    res = {k: [] for k in ('base', 'affine', 'control')}
    with Pool(2) as p:
        for i, (seed, out) in enumerate(p.imap_unordered(run, [(10 ** 6 + i, levels) for i in range(n)])):
            for k in res: res[k].append(out[k])
            print('done', i + 1, seed, {k: v for k, v in out.items() if k.startswith('t_')}, flush=True)
    for k, v in res.items():
        for i, lv in enumerate(levels):
            t = sorted(x[i] for x in v if x[i] is not None)
            print('%-8s level %d: %d solved, turns median %d mean %.1f min %d max %d' % (k, lv, len(t), t[len(t) // 2], sum(t) / len(t), t[0], t[-1]), flush=True)
