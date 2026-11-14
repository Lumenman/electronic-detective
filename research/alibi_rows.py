"""Joint alibi templates per place row (rows 0-3) across MAME games h_*."""
import glob
from collections import Counter, defaultdict
from analyze import load, truth, alibi

def col(s): return 0 if s <= 10 and s % 2 == 0 else 1 if s <= 10 else 2 if s % 2 == 0 else 3
SHORT = {'side': 's', 'town': 't', 'place': 'p'}
rows, games, bylet, byaddr = Counter(), Counter(), Counter(), Counter()
byf3 = Counter(); named3 = defaultdict(Counter); K = []; named = defaultdict(Counter)
from collections import defaultdict
PL = {10: 'A', 6: 'B', 12: 'C', 13: 'D', 14: 'E', 15: 'F'}
for fn in sorted(glob.glob('data/h_*.tsv')):
    g = load(fn)
    if 'murderer' not in g or 'ram0' not in g: continue
    R = [g['ram0'][i * 16:(i + 1) * 16] for i in range(8)]
    loc, places = truth(g); V = g['victim']
    tpl = {}
    for s, lst in g['alibis'].items():
        if s == V: continue
        a = alibi(lst[0])
        tpl[s] = ''.join(SHORT[k] for k in ('side', 'town', 'place') if k in a) + str(len(a.get('with', [])))
    per = []
    for r in range(4):
        occ = [s for s in range(1, 21) if s != V and loc.get(s) == {10: 'A', 6: 'B', 12: 'C', 13: 'D', 14: 'E', 15: 'F'}[R[r][5]]]
        t = ['?'] * 4
        for s in occ: t[col(s)] = tpl[s]
        TT = ' '.join(t) if '?' not in t else None
        for s in occ:
            w = alibi(g['alibis'][s][0]).get('with', [])
            if TT: named[(TT, col(s))][tuple(sorted(col(x) for x in w))] += 1
        f3 = [x for x in occ if col(x) == 3]
        if f3 and '?' not in t: byf3[(f3[0], ' '.join(t))] += 1
        rows[(r, tuple(t))] += 1; per.append(' '.join(t))
        NAME = {'s2 p0 t1 t0': 'A', 'p1 tp0 st0 s2': 'B', 'p1 2 s0 t0': 'C', 'st0 p0 2 2': 'D', 'sp0 t1 2 2': 'E'}
        bylet[(PL[R[r][5]], NAME[' '.join(t)])] += 1; byaddr[(R[r][4], NAME[' '.join(t)])] += 1
    occ4 = [x for x in range(1, 21) if x != V and loc.get(x) == PL[R[4][5]]]
    for x in occ4: named3[(col(x), R[4][12])][tuple(sorted(col(y) for y in alibi(g['alibis'][x][0]).get('with', [])))] += 1
    games[' | '.join(per)] += 1
    K.append(('ABCDE'.index(NAME[per[0]]), g['ram0']))
for k, n in sorted(rows.items()): print(k, n)
print(len(games), 'distinct games;', games.most_common(5))
print('place->tpl', sorted(bylet.items()))
print('addr->tpl', sorted(byaddr.items()))
from collections import defaultdict
for c in range(len(K[0][1])):
    m = defaultdict(set)
    for k, ram in K: m[ram[c]].add(k)
    if all(len(v) == 1 for v in m.values()):
        print('cell %X:%X determines k:' % (c >> 4, c & 15), {v: min(ks) for v, ks in sorted(m.items())})
print('k counts', Counter(k for k, _ in K))
for k in sorted(named): print('named', k, dict(named[k]))
for k in sorted(named3): print('3place (col, vcol)', k, dict(named3[k]))
print('odd female -> row template', sorted(byf3.items()))
