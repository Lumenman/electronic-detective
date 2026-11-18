"""Does the moment of the keys before ENTER change which games ENTER can reach? For each delay of the first key,
a few ENTER moments are played (one hold) and checked against all_games/ticks.jsonl. Prints counts only."""
import copy, json, os, sys
from multiprocessing import Pool
import all_games as A
from elecdet import ElecDet
from probe_reads import ROM


def variant(job):
    pre, hold1 = job
    ed = ElecDet(ROM); ed.power_on(); ed.run_seconds(pre); ed.press('3', hold=hold1); ed.press('1')
    out = []
    for i in range(24):
        A.next_tick(ed)
        if i % 3: continue
        e = copy.deepcopy(ed); e.press('E', hold=0.2, gap=0.02); e.run_seconds(4.78)
        out.append(json.dumps(A.from_ram(e.cpu.ram), sort_keys=True))
    return pre, hold1, out


if __name__ == '__main__':
    S = set()
    for l in open(A.FILE):
        for h, c in json.loads(l)['games'].values(): S.add(c)
    jobs = [(6.3 + k * 0.0003, 0.2) for k in range(32)] + [(6.3, 0.2 + k * 0.0003) for k in range(1, 32)]
    with Pool(4) as p:
        for pre, hold1, out in p.imap(variant, jobs):
            print('pre %.4f hold of 3 %.4f: inside %d of %d' % (pre, hold1, sum(c in S for c in out), len(out)), flush=True)
