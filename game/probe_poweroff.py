"""After a correct accusation: when does the machine switch itself off, does END TURN extend it,
can suspects still be questioned ("review the case")? Prints no solution data.
    python probe_poweroff.py <ROM folder>"""
import sys
from board import ElecDet, IPS, load_romset

files = load_romset(sys.argv[1])


def game(extend_at=None):
    b = ElecDet(files)
    run = lambda s: b.run(int(s * IPS))

    def press(k):
        b.set_key(k, True); run(0.15); b.set_key(k, False); run(0.3)

    b.power_on(); run(6.3)
    for k in '31': press(k)
    b.set_key('ENTER', True); run(0.3); b.set_key('ENTER', False); run(60)
    R = [b.cpu.ram[i * 16:(i + 1) * 16] for i in range(8)]
    c = R[4][0xd]; v = R[0][c]; M = [v or 10, v, (v or 10) + 10, v + 10][c]
    for k in ['ACCUSE', *str(M), 'ENTER']: press(k)
    run(5)
    review = None
    if extend_at is None:
        V = [R[4][R[4][0xc]] or 10, R[4][R[4][0xc]], (R[4][R[4][0xc]] or 10) + 10, R[4][R[4][0xc]] + 10][R[4][0xc]]
        s = 1 if V != 1 else 2
        run(60)                                      # let the siren finish
        for k in ['SUSPECT', str(s), 'ENTER']: press(k)
        run(1.5)
        d = b.display().replace(' ', '')
        review = 'alibi shown' if d and d not in ('EE', '0000000') else 'display %r' % ('EE' if d == 'EE' else 'other')
        press('ENDTURN')
    t, extended = 5.0 + (61.5 + 1.95 if extend_at is None else 0), False
    while b.powered and t < 900:
        if extend_at is not None and not extended and t >= extend_at:
            press('ENDTURN'); t += 0.45; extended = True
        run(1); t += 1
    return t, review


t_off, review = game()
print('review after solving: %s; switched off %.0f s after the accusation' % (review, t_off), flush=True)
t2, _ = game(extend_at=200)
print('END TURN at 200 s after the accusation -> switched off at %.0f s' % t2, flush=True)
