import glob
from collections import Counter, defaultdict
src = open('analyze.py').read().replace('\nmain()\n', '\n'); ns = {}; exec(compile(src, 'analyze.py', 'exec'), ns)
INV = {v: k for k, v in ns['PLACE'].items()}
feats = defaultdict(list); rams = []
for fn in sorted(glob.glob('data/h_*.tsv')):
    g = ns['load'](fn); loc, places = ns['truth'](g); M = g['murderer']; V = g['victim']
    A = lambda s, q: g['q'].get((s, q), [])
    L38 = Counter(A(s, 5)[0].upper() for s in range(1, 21) if A(s, 5) and s != V).most_common(1)[0][0]
    L45 = Counter(A(s, 6)[0].upper() for s in range(1, 21) if A(s, 6) and s != V).most_common(1)[0][0]
    mw = Counter(A(s, 4)[0] for s in range(1, 21) if A(s, 4) and s != V).most_common(1)[0][0] == '4E5'
    r = g['ram0']; R = [r[i * 16:(i + 1) * 16] for i in range(8)]
    rowof = {ns['PLACE'][R[i][5]]: i for i in range(5)}
    cat = lambda s: [0 if s <= 10 and s % 2 == 0 else 1 if s <= 10 else 2 if s % 2 == 0 else 3][0]
    f = {'murderer_row': rowof[loc[M]], 'murderer_col': cat(M), 'victim_col': cat(V),
         'three_row': rowof[[p for p, v in places.items() if len(v['occ']) == 3][0]],
         'row38': rowof[L38], 'row45': rowof[L45], 'mw38': int(mw), 'code38': INV[L38], 'code45': INV[L45],
         'murderer_lowbits': M & 0xf, 'victim_lowbits': V & 0xf}
    for k, v in f.items(): feats[k].append(v)
    rams.append(r)
n = len(rams)
for k, vals in feats.items():
    hits = []
    for c in range(128):
        col = [rams[i][c] for i in range(n)]
        for name, fn in (('=', lambda x: x), ('+1', lambda x: x + 1), ('15-', lambda x: 15 - x)):
            if all(fn(vals[i]) == col[i] for i in range(n)): hits.append(f'{c // 16}:{c % 16:x}({name})')
    print(k, hits[:6])
print({k: Counter(v) for k, v in feats.items() if k in ('murderer_row','three_row','row38','row45','murderer_col','victim_col','mw38')})
mw = feats['mw38']
for c in range(128):
    m = defaultdict(set)
    for i in range(n): m[rams[i][c]].add(mw[i])
    if len(m) > 1 and all(len(s) == 1 for s in m.values()):
        print('mw cell %d:%x' % (c // 16, c % 16), {k: next(iter(s)) for k, s in m.items()})
for c in range(128):
    vals = Counter(rams[i][c] for i in range(n))
    if len(vals) == 1: continue
print('constant cells:', ''.join('%d:%x ' % (c // 16, c % 16) for c in range(128) if len({rams[i][c] for i in range(n)}) == 1))
mcol = feats['murderer_col']; vcol = feats['victim_col']
for name, fn in [('murderer odd', lambda i: mcol[i] in (1, 3)), ('murderer male', lambda i: mcol[i] in (0, 1)),
                 ('victim odd', lambda i: vcol[i] in (1, 3)), ('victim male', lambda i: vcol[i] in (0, 1)),
                 ('same parity', lambda i: (mcol[i] in (1, 3)) == (vcol[i] in (1, 3))),
                 ('same sex', lambda i: (mcol[i] < 2) == (vcol[i] < 2))]:
    t = Counter((fn(i), mw[i]) for i in range(n)); print(name, dict(t))
for cell in (0x19, 0x29, 0x09, 0x39, 0x49):
    print('cell %d:%x vs mw38' % (cell >> 4, cell & 15), dict(Counter((rams[i][cell], mw[i]) for i in range(n))))
