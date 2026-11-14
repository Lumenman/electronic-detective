"""Columns 4 (address) and 5 (place letter): rotation + swap at generation, see RULES.md 4.2. Prints matches for letters, addresses, games."""
import json
G=[json.loads(l) for l in open('emu/sweep1.jsonl')]
CYC='ADBCEF'; ACYC=[5,2,7,1,6,3]
ok=ok2=0
for g in G:
    row={v['row']:k for k,v in g['places'].items()}; addr={v['row']:v['addr'] for v in g['places'].values()}
    i=CYC.index(g['scene']); nx=lambda k: CYC[(i+k)%6]
    # unswapped rows u0..u5 are consecutive in the cycle
    if g['mcol']<2:   # rows 0 and 5 swapped: u0=scene
        u=[nx(k) for k in range(6)]; act=[u[5],u[1],u[2],u[3],u[4],u[0]]
    else:             # rows 0 and 4 swapped: u5=scene
        u=[nx(k+1) for k in range(6)]; act=[u[4],u[1],u[2],u[3],u[0],u[5]]
    ok+= act==[row[r] for r in range(6)]
    # addresses: rotation fixed by the address of row 5 for male (no swap); female: swap 0-4 (even victim col) or 0-2
    j=ACYC.index(addr[5]); a=[ACYC[(j+1+k)%6] for k in range(6)]
    if g['mcol']>=2:
        t=4 if g['vcol']%2==0 else 2; a[0],a[t]=a[t],a[0]
    ok2+= a==[addr[r] for r in range(6)]
print(ok,ok2,len(G))
