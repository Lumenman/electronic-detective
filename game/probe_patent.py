"""Check two claims of US patent 4,394,018 against the ROM (digits masked, no spoilers):
 1) a question not on the card gives EE *and* uses up one of the turn's questions;
 2) questioning a new suspect without END TURN gives EE (patent) or END (manual).
    python probe_patent.py <ROM folder or zip>"""
import re, sys
from board import ElecDet, IPS, load_romset

b = ElecDet(load_romset(sys.argv[1]))
def run(s): b.run(int(s * IPS))
def press(k, hold=0.15): b.set_key(k, True); run(hold); b.set_key(k, False); run(0.3)
def keys(*ks):
    for k in ks: press(k)
def show(label): run(1.5); print('%-40s %r' % (label, re.sub(r'[0-9]', '#', b.display())), flush=True)

b.power_on(); run(6.3)
keys('2', '1'); press('ENTER', 0.3); run(60)               # level 2 (two questions), 1 player
v = int(re.sub(r'\D', '', b.display())[:2] or 0)
s = 1 if v != 1 else 2                                      # suspect 1 (card 1,2,9) or 2 (2,3,9)
q_bad, q_ok = (5, (1, 2)) if s == 1 else (5, (2, 3))
keys('SUSPECT', str(s), 'ENTER'); show(f'alibi of #{s}')
keys('PQ', str(q_bad), 'ENTER'); show(f'Q{q_bad} (not on card)')
keys('PQ', str(q_ok[0]), 'ENTER'); show(f'Q{q_ok[0]} valid (1st)')
keys('PQ', str(q_ok[1]), 'ENTER'); show(f'Q{q_ok[1]} valid (2nd; END if docked)')
keys('SUSPECT', '3' if v != 3 else '4', 'ENTER'); show('new suspect, no END TURN')
keys('SUSPECT', '3' if v != 3 else '4', 'ENTER'); show('again, no END TURN')
press('ENDTURN'); run(1)
keys('SUSPECT', '3' if v != 3 else '4', 'ENTER'); show('after END TURN')
