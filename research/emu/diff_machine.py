"""Compare game/machine.py with the ROM, key by key, on random key sequences.

Both get the same case (the ROM's table is read from RAM and handed to the model) and the same keys; after
every key the settled display must be equal.
    python diff_machine.py [sessions] [keys per session] [first seed]
Prints each difference with the keys that led to it (digits of answers are shown: SPOILERS for these cases only).
"""
import copy, os, pickle, random, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'game'))
from board import ElecDet, IPS, load_romset
from dealer import Dealer
from machine import Machine
from rules import from_ram

ROMZIP = 'D:/Downloads/elecdet.zip'
HERE = os.path.dirname(os.path.abspath(__file__))
SETTLE = 0.7


def started(level, players, deal_seed):
    """ROM board with a case already built (cached), dealt by the dealer."""
    f = os.path.join(HERE, 'start_%d%d_%d.pkl' % (level, players, deal_seed))
    if os.path.exists(f):
        return pickle.load(open(f, 'rb'))
    b = ElecDet(load_romset(ROMZIP)); d = Dealer(random.Random(deal_seed))
    def run(s):
        for _ in range(round(s * 60)): b.run(int(IPS / 60)); d.tick(b.cpu)
    def press(k):
        b.set_key(k, True); run(0.15); b.set_key(k, False); run(0.3)
    b.power_on(); run(6.5)
    for k in (str(level), str(players), 'ENTER'): press(k)
    run(7)
    b.sound_events = []
    case = from_ram(b.cpu.ram)
    pickle.dump((b, case), open(f, 'wb'))
    return b, case


def random_keys(rng, n, victim, murderer):
    """Mostly sensible play with some nonsense mixed in."""
    out = []
    while len(out) < n:
        r = rng.random()
        if r < 0.30:
            s = victim if rng.random() < 0.06 else rng.randint(1, 20)
            out += ['SUSPECT', *str(s), 'ENTER']
        elif r < 0.70:
            q = rng.choice([rng.randint(1, 14)] * 8 + [0, 15, 19, 20])
            out += ['PQ', *str(q), 'ENTER']
        elif r < 0.84:
            out += ['ENDTURN']
        elif r < 0.89:
            a = murderer if rng.random() < 0.3 else rng.randint(0, 21)
            out += ['ACCUSE', *str(a), 'ENTER']
        else:
            out += [rng.choice(['SUSPECT', 'PQ', 'ACCUSE', 'ENTER', 'ENDTURN', *'0123456789'])]
    return out[:n]


def view(run, display, seconds=0.6):
    """What the display shows over a short while: one text, or a text and blank when it blinks."""
    seen = {}
    for _ in range(round(seconds / 0.04)):
        run(0.04); d = display()
        if '?' not in d: seen[d] = seen.get(d, 0) + 1
    return frozenset(d for d, k in seen.items() if k >= 2)


def session(seed, nkeys, verbose=True):
    rng = random.Random(seed)
    level, players = rng.choice([1, 2, 3]), rng.choice([1, 1, 2, 3])
    b, case = started(level, players, seed % 12)
    b = copy.deepcopy(b)
    m = Machine(case=case); m.power_on(); m.run(int(3 * IPS))
    for k in (str(level), str(players), 'ENTER'): m.key(k)
    m.run(int(7 * IPS))
    keys = random_keys(rng, nkeys, m.victim, m.murderer)
    brun, mrun = (lambda s: b.run(int(s * IPS))), (lambda s: m.run(int(s * IPS)))
    accusing = blinking = False
    for i, k in enumerate(keys):
        if k == 'ACCUSE': accusing = True
        wait = 9.0 if (k == 'ENTER' and accusing) else 0.1          # sirens, shots and the march take their time
        hold = 0.8 if blinking else 0.15                         # the ROM misses short presses while it blinks
        b.set_key(k, True); brun(hold); b.set_key(k, False); brun(wait)
        m.key(k); mrun(hold + wait)
        if k in ('ENTER', 'SUSPECT', 'PQ', 'ENDTURN'): accusing = False
        want, got = view(brun, b.display), view(mrun, m.display)
        blinking = len(want) > 1
        if want != got:
            if verbose:
                print('seed %d level %d players %d, after %d keys: ROM %s, model %s; keys: %s' % (
                    seed, level, players, i + 1, sorted(want), sorted(got),
                    ' '.join(keys[:i + 1]).replace('SUSPECT', 'S').replace('ENTER', 'E').replace('ENDTURN', 'T')
                    .replace('PQ', 'Q').replace('ACCUSE', 'A')))
            return i + 1
    return None


if __name__ == '__main__':
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 20
    nkeys = int(sys.argv[2]) if len(sys.argv) > 2 else 60
    first = int(sys.argv[3]) if len(sys.argv) > 3 else 0
    from multiprocessing import Pool
    from functools import partial
    with Pool(2) as p:
        bad = sum(r is not None for r in p.imap(partial(session, nkeys=nkeys), range(first, first + n)))
    print('%d sessions of %d keys: %d differ' % (n, nkeys, bad))
