"""Q13 asked at the .38 place when the .38 is NOT the murder weapon: what decides YES/NO? (MAME data h_*)"""
import glob
from collections import Counter, defaultdict
from analyze import load, truth, male, odd

F = defaultdict(Counter)
for fn in sorted(glob.glob('data/h_*.tsv')):
    g = load(fn)
    if 'murderer' not in g or 'ram0' not in g: continue
    R = [g['ram0'][i * 16:(i + 1) * 16] for i in range(8)]
    if R[1][9] == 2: continue  # .38 is the murder weapon
    loc, places = truth(g); M, V = g['murderer'], g['victim']
    p38 = [p for p, v in places.items() if p == {10: 'A', 6: 'B', 12: 'C', 13: 'D', 14: 'E', 15: 'F'}[R[1][5]]][0]
    for s in places[p38]['occ']:
        a = g['q'].get((s, 13))
        if not a: continue
        yes = a[0] == '4E5'
        feats = {'witness odd': odd(s), 'witness male': male(s), 'same sex as M': male(s) == male(M),
                 'M odd': odd(M), 'M male': male(M), 'V odd': odd(V), 'V male': male(V),
                 'same parity as M': odd(s) == odd(M), 'asks agree': len(set(a)) == 1}
        for k, v in feats.items():
            F[k][(v, yes)] += 1
for k, c in F.items():
    print(f'{k:20s}', ' '.join(f'{"T" if v else "F"}->{"YES" if y else "NO "}:{n}' for (v, y), n in sorted(c.items())))
