import glob
from collections import Counter, defaultdict
src=open('analyze.py').read().replace('\nmain()\n','\n'); ns={}; exec(compile(src,'analyze.py','exec'),ns)
H=defaultdict(Counter)
for fn in glob.glob('data/h_*.tsv'):
    g=ns['load'](fn); loc,places=ns['truth'](g); M=g['murderer']; V=g['victim']
    A=lambda s,q: g['q'].get((s,q),[])
    L={'.38':Counter(A(s,5)[0].upper() for s in range(1,21) if A(s,5) and s!=V).most_common(1)[0][0],
       '.45':Counter(A(s,6)[0].upper() for s in range(1,21) if A(s,6) and s!=V).most_common(1)[0][0]}
    mw='.38' if Counter(A(s,4)[0] for s in range(1,21) if A(s,4) and s!=V).most_common(1)[0][0]=='4E5' else '.45'
    ow='.45' if mw=='.38' else '.38'; q=13 if ow=='.38' else 14; qm=13 if mw=='.38' else 14
    for s in places[L[ow]]['occ']:
        a=A(s,q)[0]=='4E5'   # says odd
        sex='same' if (s<=10)==(M<=10) else 'opp'
        H[sex]['says odd == witness odd']+= a==(s%2==1)
        H[sex]['says odd == murderer odd']+= a==(M%2==1)
        H[sex]['n']+=1
    # opposite-sex lie at murder weapon: relation to anything?
    s=[x for x in places[L[mw]]['occ'] if (x<=10)!=(M<=10)][0]
    lie=(A(s,qm)[0]=='4E5')!=(M%2==1)
    H['murder_opp_lie']['lie']+=lie; H['murder_opp_lie']['lie & mw=.38']+=lie and mw=='.38'; H['murder_opp_lie']['mw=.38']+=mw=='.38'
for k,v in H.items(): print(k,dict(v))
