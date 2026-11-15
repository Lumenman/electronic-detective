"""What does the ROM show for odd entries at the level/players prompt?  (display after each key, then 7 s later)"""
import copy, sys
from diff_machine import ElecDet, IPS, load_romset, ROMZIP
base = ElecDet(load_romset(ROMZIP)); base.power_on(); base.run(int(6.5 * IPS))
ALIAS = {'S': 'SUSPECT', 'Q': 'PQ', 'A': 'ACCUSE', 'E': 'ENTER', 'T': 'ENDTURN'}
for seq in sys.argv[1:]:
    b = copy.deepcopy(base); out = []
    for tok in seq.split():
        k = ALIAS.get(tok, tok)
        b.set_key(k, True); b.run(int(0.15 * IPS)); b.set_key(k, False); b.run(int(0.7 * IPS))
        out.append('%s:%r' % (tok, b.display().strip()))
    b.run(int(7 * IPS)); d = b.display().strip()
    print('%-14s %s   +7s: %r' % (seq, ' '.join(out), d if not d[:1].isdigit() or len(d) < 3 else 'case'))
