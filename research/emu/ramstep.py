"""Show the ROM's display and the RAM cells that changed after every key (rows 7+ and scratch are noisy).
    python ramstep.py <level> <players> <deal seed> "S 5 E Q 9 E"  [cells to always print, e.g. 3:C,5:0]"""
import copy, sys
from diff_machine import started, IPS, view
ALIAS = {'S': 'SUSPECT', 'Q': 'PQ', 'A': 'ACCUSE', 'E': 'ENTER', 'T': 'ENDTURN'}
b, case = started(*map(int, sys.argv[1:4])); b = copy.deepcopy(b)
watch = [tuple(int(x, 16) for x in c.split(':')) for c in sys.argv[5].split(',')] if len(sys.argv) > 5 else []
run = lambda s: b.run(int(s * IPS))
for tok in sys.argv[4].split():
    old = list(b.cpu.ram)
    if tok[0] == 'w': run(float(tok[1:]))
    else:
        b.set_key(ALIAS.get(tok, tok), True); run(0.15); b.set_key(ALIAS.get(tok, tok), False); run(0.1)
    v = '/'.join(sorted(d.strip() or '_' for d in view(run, b.display)))
    new = b.cpu.ram
    ch = ' '.join('%X:%X=%X>%X' % (i // 16, i % 16, old[i], new[i]) for i in range(len(new)) if old[i] != new[i])
    print('%-3s %-8s %s | %s' % (tok, v, ' '.join('%X' % new[r * 16 + c] for r, c in watch), ch))
