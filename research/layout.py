from parse import load
from collections import defaultdict, Counter
def rows(g, key='ram0'): r=g[key]; return [r[i*16:(i+1)*16] for i in range(8)]
def occupants(g):
    R=rows(g); occ=[]
    for i in range(5):
        c=R[i]; occ.append([c[0] or 10, c[1], c[2]+10 if c[2] else 20, c[3]+10])
    return occ
def place_of_rows(g):
    occ=occupants(g); res=[]
    for i,o in enumerate(occ):
        letters=Counter(); side=Counter(); town=Counter()
        for s in o:
            a=g['alibi'].get(s,{})
            if 'place' in a: letters[a['place']]+=1
            if 'side' in a: side[a['side']]+=1
            if 'town' in a: town[a['town']]+=1
        res.append((letters, side, town))
    return res
if __name__=='__main__':
    gs=load('g')
    # verify alibi consistency: 'with' members in same row
    bad=0
    for g in gs:
        occ=occupants(g); where={s:i for i,o in enumerate(occ) for s in o}
        for s,a in g['alibi'].items():
            for t in a.get('with',[]):
                if where.get(s)!=where.get(t): bad+=1
    print('with-inconsistencies',bad)
    # column correlation with place letter / side / town
    for col in range(4,16):
        cl=defaultdict(Counter); cs=defaultdict(Counter); ct=defaultdict(Counter)
        for g in gs:
            R=rows(g)
            for i,(L,S,T) in enumerate(place_of_rows(g)):
                v=R[i][col]
                for k in L: cl[k][v]+=1
                for k in S: cs[k][v]+=1
                for k in T: ct[k][v]+=1
        print(col,'place',{k:dict(v) for k,v in sorted(cl.items())})
        print(col,'side ',{k:dict(v) for k,v in sorted(cs.items())})
        print(col,'town ',{k:dict(v) for k,v in sorted(ct.items())})
