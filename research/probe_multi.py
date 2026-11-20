"""What does the machine show in a 2-player game: wrong accusation by one player, then by the other?
Prints display patterns with digits masked as '#', so no solution leaks.
    python probe_multi.py <ROM folder>"""
import re, sys
import os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "game"))  # board.py of the game
from board import ElecDet, IPS, load_romset

b = ElecDet(load_romset(sys.argv[1]))


def run(s): b.run(int(s * IPS))


def press(k, hold=0.15):
    b.set_key(k, True); run(hold); b.set_key(k, False); run(0.3)


def keys(*ks):
    for k in ks: press(k)


def mask(d): return re.sub(r'[0-9]', '#', d)


def watch(label, seconds, step=0.25):
    seen = []
    for _ in range(int(seconds / step)):
        run(step)
        m = mask(b.display()) if b.powered else '<off>'
        if not seen or seen[-1] != m:
            seen.append(m)
    print('%-28s %s' % (label, ' -> '.join(repr(x) for x in seen)), flush=True)


def ram_people():
    R = [b.cpu.ram[i * 16:(i + 1) * 16] for i in range(8)]
    who = lambda r, c: [R[r][c] or 10, R[r][c], (R[r][c] or 10) + 10, R[r][c] + 10][c]
    return who(0, R[4][0xd]), who(4, R[4][0xc])        # murderer, victim


b.power_on(); run(6.3)
keys('3', '2'); press('ENTER', 0.3); run(60)
M, V = ram_people()
wrong = [x for x in range(1, 21) if x not in (M, V)]
keys('SUSPECT', *str(wrong[0]), 'ENTER'); run(1.5); press('ENDTURN'); run(1)            # player 1: a turn
keys('ACCUSE', *str(wrong[1]), 'ENTER'); watch('P2 wrong accusation', 70)              # player 2
keys('SUSPECT', *str(wrong[2]), 'ENTER'); watch('P1 questions after that', 2)
press('ENDTURN'); run(1)
keys('SUSPECT', *str(wrong[3]), 'ENTER'); watch('P1 again (no P2 turn?)', 2)
press('ENDTURN'); run(1)
keys('ACCUSE', *str(wrong[4]), 'ENTER'); watch('P1 wrong accusation (last)', 70)
keys('SUSPECT', *str(wrong[5]), 'ENTER'); watch('after all out: questioning', 2)
