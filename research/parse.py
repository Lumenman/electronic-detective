import glob, re
NUM = {'0':0,'1':1,'2':2,'3':3,'4':4,'5':5,'6':6,'b':6,'7':7,'8':8,'9':9}
def decode_alibi(s):
    s = s[:7].ljust(7)
    r = {}
    if s.strip()=='' : return r
    if s == '0000000': return {'dontknow':True}
    if s[0]!=' ': r['side'] = s[0]
    if s[1]!=' ': r['town'] = s[1]
    if s[2]!=' ': r['place'] = s[2].upper()
    sus=[]
    for a,b in ((3,4),(5,6)):
        t=(s[a]+s[b]).strip()
        if t: sus.append(int(''.join(str(NUM[c]) for c in t)))
    if sus: r['with']=sus
    return r
def load(prefix):
    games=[]
    for fn in sorted(glob.glob(f'data/{prefix}_*.tsv'), key=lambda x:int(re.findall(r'_(\d+)',x)[0])):
        g={'file':fn,'alibi':{},'q':{},'raw':{}}
        for line in open(fn):
            lab,_,val=line.rstrip('\n').partition('\t')
            g['raw'][lab]=val
            if lab=='crime':
                d=val[:7]; g['victim']=int(''.join(str(NUM[c]) for c in d[:2].strip())); g['scene']=d[2].upper()
            elif lab.startswith('alibi'):
                g['alibi'][int(lab[5:])]=decode_alibi(val)
            elif lab.startswith('ram'):
                g[lab]=[int(c,16) for c in val]
        games.append(g)
    return games
