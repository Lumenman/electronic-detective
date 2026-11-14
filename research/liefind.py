import glob
from collections import Counter, defaultdict
src = open('analyze.py').read().replace('\nmain()\n', '\n'); ns = {}; exec(compile(src, 'analyze.py', 'exec'), ns)
rows = []
for fn in sorted(glob.glob('data/h_*.tsv')):
    g = ns['load'](fn); loc, places = ns['truth'](g); M = g['murderer']; V = g['victim']
    r = g['ram0']; R = [r[i * 16:(i + 1) * 16] for i in range(8)]
    mw38 = R[1][9] == 2
    wrow = 1 if mw38 else 2; orow = 2 if mw38 else 1
    wplace = ns['PLACE'][R[wrow][5]]; oplace = ns['PLACE'][R[orow][5]]
    q = 13 if mw38 else 14; qo = 14 if mw38 else 13
    opp = [s for s in places[wplace]['occ'] if (s <= 10) != (M <= 10)][0]
    lie = (g['q'][(opp, q)][0] == '4E5') != (M % 2 == 1)
    # non-murder weapon answers: same-sex and opposite-sex witnesses at other weapon place
    other = {s: g['q'][(s, qo)][0] == '4E5' for s in places[oplace]['occ']}
    rows.append((r, lie, other, M, R))
n = len(rows)
print('lie rate', sum(x[1] for x in rows) / n)
for c in range(128):
    for b in range(4):
        t = Counter(((rows[i][0][c] >> b) & 1, rows[i][1]) for i in range(n))
        if len(t) == 2 and all(k[0] != k[1] for k in t) or len(t) == 2 and all(k[0] == k[1] for k in t):
            print('lie == bit %d of %d:%x' % (b, c // 16, c % 16), dict(t))
