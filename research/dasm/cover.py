import re, sys
from collections import Counter
def addrs(fn):
    c=Counter()
    for line in open(fn):
        m=re.match(r'([0-9A-F]+):([0-9A-F]{2}):',line)
        if m: c[(int(m.group(1),16),int(m.group(2),16))]+=1
    return c
ph={n:addrs(f'tr_{n}.txt') for n in ['idle','setup','alibi1','alibi2','alibi3','q13_1','q13_2','q13_3']}
idle=set(ph['idle'])
al=set(ph['alibi1'])|set(ph['alibi2'])|set(ph['alibi3'])
q=set(ph['q13_1'])|set(ph['q13_2'])|set(ph['q13_3'])
def pages(s):
    c=Counter(p for p,_ in s); return dict(sorted(c.items()))
print('total distinct executed:', len(idle|set(ph['setup'])|al|q), 'of 2048')
print('idle', len(idle), pages(idle))
print('setup-only', len(set(ph['setup'])-idle), pages(set(ph['setup'])-idle))
print('alibi-only', len(al-idle-set(ph['setup'])), pages(al-idle-set(ph['setup'])))
print('alibi-idle', len(al-idle), pages(al-idle))
print('q13-idle-alibi', len(q-idle-al), pages(q-idle-al))
import json
json.dump({k:[f'{p:X}:{a:02X}' for p,a in sorted(v)] for k,v in {'idle':idle,'setup':set(ph['setup']),'alibi':al,'q13':q}.items()}, open('cover.json','w'))
