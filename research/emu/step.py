"""Show the ROM's and the model's display after every key.
    python step.py <level> <players> <deal seed> "S 1 6 E w2 Q 1 3 E"      (wN = wait N seconds)"""
import copy, sys
from diff_machine import started, Machine, IPS, view
ALIAS = {'S': 'SUSPECT', 'Q': 'PQ', 'A': 'ACCUSE', 'E': 'ENTER', 'T': 'ENDTURN'}
level, players, seed = int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3])
b, case = started(level, players, seed); b = copy.deepcopy(b)
m = Machine(case=case); m.power_on(); m.run(int(3 * IPS))
for k in (str(level), str(players), 'ENTER'): m.key(k)
m.run(int(7 * IPS))
print('victim', m.victim, 'murderer', m.murderer)
brun, mrun = (lambda s: b.run(int(s * IPS))), (lambda s: m.run(int(s * IPS)))
for tok in sys.argv[4].split():
    if tok[0] == 'w': brun(float(tok[1:])); mrun(float(tok[1:]))
    else:
        hold = 0.8 if tok.endswith('!') else 0.15                  # 'S!' = held long
        k = ALIAS.get(tok.rstrip('!'), tok.rstrip('!'))
        b.set_key(k, True); brun(hold); b.set_key(k, False); brun(0.1)
        m.key(k); mrun(hold + 0.1)
    x, y = view(brun, b.display), view(mrun, m.display)
    f = lambda v: '/'.join(sorted(d.strip() or '_' for d in v))
    print('%-4s ROM %-14s model %-14s%s' % (tok, f(x), f(y), '' if x == y else '  <<<'))
