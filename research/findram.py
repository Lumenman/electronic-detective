from parse import load
gs = load('g')
# co-location pairs and place facts
best=[]
for base in range(0,128-20):
  for stride in (1,2):
    ok=tot=0
    for g in gs:
      r=g['ram0']
      def v(s):
        i=base+(s-1)*stride
        return r[i] if i<128 else None
      for s,a in g['alibi'].items():
        for t in a.get('with',[]):
          tot+=1; ok+= v(s)==v(t)
    best.append((ok/tot if tot else 0, base, stride, tot))
best.sort(reverse=True); print(best[:8])
