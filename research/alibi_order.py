"""Display order of two alibi companions over MAME games h_*: always ascending column."""
import glob, sys
sys.path.insert(0,'.')
from collections import Counter, defaultdict
from analyze import load, truth, alibi
def col(s): return 0 if s <= 10 and s % 2 == 0 else 1 if s <= 10 else 2 if s % 2 == 0 else 3
PL = {10: 'A', 6: 'B', 12: 'C', 13: 'D', 14: 'E', 15: 'F'}
c=Counter(); n=0; three=Counter()
for fn in sorted(glob.glob('data/h_*.tsv')):
    g = load(fn)
    if 'murderer' not in g or 'ram0' not in g: continue
    R = [g['ram0'][i * 16:(i + 1) * 16] for i in range(8)]
    loc, places = truth(g); V=g['victim']
    of = {loc[s]: s for s in loc if col(s)==3}      # odd female per place
    p3 = PL[R[4][5]]
    for s, lst in g['alibis'].items():
        if s == V: continue
        w = alibi(lst[0]).get('with', [])
        if len(w) != 2: continue
        n+=1
        key=(col(s), tuple(col(x) for x in w))
        if loc[s]==p3: three[(col(V),)+key]+=1
        else: c[(of[loc[s]],)+key]+=1
print(n,'alibis with two companions')
print('places of four: (odd female, speaker col, companion cols in display order)')
for k,v in sorted(c.items()): print('  ',k,v)
print('place of three: (victim col, speaker col, companion cols in display order)')
for k,v in sorted(three.items()): print('  ',k,v)
