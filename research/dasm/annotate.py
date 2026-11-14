import json, re
cov={k:set(v) for k,v in json.load(open('cover.json')).items()}
out=[]
for line in open('listing.txt'):
    m=re.match(r'  ([0-9A-F]):([0-9A-F]{2})  ',line)
    if m:
        a=f'{m.group(1)}:{m.group(2)}'
        tag=''.join(c if a in cov[k] else '.' for c,k in (('I','idle'),('S','setup'),('A','alibi'),('Q','q13')))
        line=tag+line
    else: line='    '+line
    out.append(line.rstrip('\n'))
open('annotated.txt','w').write('\n'.join(out)+'\n')
