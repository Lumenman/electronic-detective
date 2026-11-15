"""Which questions does the ROM really accept from each suspect? (the printed cards say three each, plus 13 and 14)"""
import copy, sys
from multiprocessing import Pool
from diff_machine import started, IPS
sys.path.insert(0, '../../game')
from rules import CARDS


def probe(job):
    seed, s = job
    b, case = started(3, 1, seed)
    ok = []
    for q in range(1, 15):
        x = copy.deepcopy(b)
        for k in ['SUSPECT', *str(s), 'ENTER', 'PQ', *str(q), 'ENTER']:
            x.set_key(k, True); x.run(int(0.15 * IPS)); x.set_key(k, False); x.run(int(0.45 * IPS))
        if x.display().strip() != 'EE': ok.append(q)
    return s, ok


if __name__ == '__main__':
    out = {}
    for seed in (0, 4):
        b, case = started(3, 1, seed)
        victim = case['rows'][4]['people'][case['vcol']]
        with Pool(2) as p:
            for s, ok in p.imap(probe, [(seed, s) for s in range(1, 21) if s != victim and s not in out]):
                out[s] = ok
    for s in sorted(out):
        extra = [q for q in out[s] if q not in CARDS[s] + (13, 14)]
        missing = [q for q in CARDS[s] + (13, 14) if q not in out[s]]
        print('%2d: accepted %-28s card %-12s extra %s missing %s' % (s, out[s], CARDS[s], extra, missing))
