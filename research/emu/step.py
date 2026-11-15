"""Show the ROM's and the model's display after every key.   python step.py <level> <deal seed> "S 1 6 E 7 Q 1 3 E" """
import copy, sys
from diff_machine import started, Machine, IPS
ALIAS = {'S': 'SUSPECT', 'Q': 'PQ', 'A': 'ACCUSE', 'E': 'ENTER', 'T': 'ENDTURN'}
level, seed = int(sys.argv[1]), int(sys.argv[2])
b, case = started(level, 1, seed); b = copy.deepcopy(b)
m = Machine(case=case); m.power_on(); m.run(int(3 * IPS))
for k in (str(level), '1', 'ENTER'): m.key(k)
m.run(int(7 * IPS))
print('victim', m.victim, 'murderer', m.murderer)
for tok in sys.argv[3].split():
    k = ALIAS.get(tok, tok)
    b.set_key(k, True); b.run(int(0.15 * IPS)); b.set_key(k, False); b.run(int(0.7 * IPS))
    m.key(k); m.run(int(0.15 * IPS) + int(0.7 * IPS))
    print('%-8s ROM %r  model %r %s' % (tok, b.display(), m.display(), '' if b.display() == m.display() else '  <<<'))
