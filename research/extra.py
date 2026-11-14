import glob, sys
from collections import Counter
sys.argv=['x','h']
import importlib.util
spec=importlib.util.spec_from_file_location('an','analyze.py')
src=open('analyze.py').read().replace('\nmain()\n','\n')
ns={}; exec(compile(src,'analyze.py','exec'),ns)
C=Counter()
for fn in glob.glob('data/h_*.tsv'):
    g=ns['load'](fn); loc,places=ns['truth'](g); M=g['murderer']; V=g['victim']
    A=lambda s,q: g['q'].get((s,q),[])
    L38=Counter(A(s,5)[0].upper() for s in range(1,21) if A(s,5) and s!=V).most_common(1)[0][0]
    L45=Counter(A(s,6)[0].upper() for s in range(1,21) if A(s,6) and s!=V).most_common(1)[0][0]
    mw='.38' if Counter(A(s,4)[0] for s in range(1,21) if A(s,4) and s!=V).most_common(1)[0][0]=='4E5' else '.45'
    for wn,q,L in (('.38',13,L38),('.45',14,L45)):
        occ=places[L]['occ']
        for sex in ('same','opp'):
            ws=[s for s in occ if (s<=10)==(M<=10)] if sex=='same' else [s for s in occ if (s<=10)!=(M<=10)]
            a=[A(s,q)[0] for s in ws]
            kind='murder' if wn==mw else 'other'
            C[(kind,sex,'two witnesses agree')]+= a[0]==a[1]
            C[(kind,sex,'pairs')]+=1
    # place-size category facts
    three=[p for p,v in places.items() if len(v['occ'])==3][0]
    C[('murderer category == victim category')]+= ns['cat'](M)==ns['cat'](V)
for k,v in sorted(C.items(), key=str): print(k,v)
