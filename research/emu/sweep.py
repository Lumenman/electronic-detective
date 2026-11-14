"""Play many game setups in the emulator with random human-like timing and decode the solution from RAM.
Writes one JSON line per game: timing, victim, murderer, places, weapons."""
import json, random, sys
from multiprocessing import Pool
from elecdet import ElecDet
from probe_reads import ROM

PLACE = {10: 'A', 6: 'B', 12: 'C', 13: 'D', 14: 'E', 15: 'F'}


def decode(ram):
    R = [ram[i * 16:(i + 1) * 16] for i in range(8)]
    def who(row, col):
        v = R[row][col]
        return [v or 10, v, (v or 10) + 10, v + 10][col]
    vcol, mcol = R[4][0xc], R[4][0xd]
    places = {}
    for i in range(6):
        places[PLACE[R[i][5]]] = {'row': i, 'addr': R[i][4],
                                  'occ': [who(i, c) for c in range(4)] if i < 5 else []}
    victim = who(4, vcol)
    places[PLACE[R[4][5]]]['occ'].remove(victim)
    return {'victim': victim, 'murderer': who(0, mcol), 'vcol': vcol, 'mcol': mcol,
            'murder_weapon': '.38' if R[1][9] == 2 else '.45',
            'p38': PLACE[R[1][5]], 'p45': PLACE[R[2][5]], 'scene': PLACE[R[5][5]],
            'places': places}


def one(seed):
    rnd = random.Random(seed)
    ed = ElecDet(ROM)
    pre = 6.3 + rnd.random() * 4
    hold = 0.08 + rnd.random() * 0.4
    ed.power_on(); ed.run_seconds(pre)
    ed.press('3'); ed.press('1')
    ed.press('E', hold=hold, gap=0); ed.run_seconds(5)
    ram = [ed.cpu.ram[a] for a in range(0x90)]
    d = decode(ram)
    d.update(seed=seed, pre=pre, hold=hold, display=ed.display(), ram=''.join('%x' % v for v in ram))
    return d


if __name__ == '__main__':
    a, b, out = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3]
    with Pool(4) as p, open(out, 'w') as f:
        for d in p.imap_unordered(one, range(a, b)):
            f.write(json.dumps(d) + '\n'); f.flush()
