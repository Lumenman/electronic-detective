"""Every game of the standard start (level, players, ENTER), played on the emulator, not derived from a model.

For each of the 7776 tumbler ticks of one full period, ENTER is pressed at that tick and held; every 1/3 step of
the hold counter 4:D a copy of the machine releases it, and for each new value of 4:D the copy plays the setup to
the end (the case is complete 4.7 s after the release). Prints counts only (no cases).
Result 2026-11-18: 124,416 games, 15,342 distinct cases; NOT all games: the table keeps changing while ENTER is
held, so longer holds (up to ~0.83 s, when the ROM goes on by itself) reach more (95 of 400 sweep1 games are
outside), and a release inside a pass can matter. The work was dropped there. Run it with PyPy (6x faster):

    pypy all_games.py [workers]      output: all_games/ticks.jsonl (resumable)
    pypy all_games.py summary
"""
import copy, json, os, sys
from multiprocessing import Pool
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'game'))
from rules import from_ram
from elecdet import ALIAS, ElecDet, IPS, KEYS
from probe_reads import ROM

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'all_games')
FILE = os.path.join(OUT, 'ticks.jsonl')
EXIT = 1 << 7 | 0x29          # 1:29 = end of every tumbler tick (count_games.py)
PERIOD = 7776
STEP = 0.0133                 # seconds of ENTER hold per step of 4:D (measured)
ROW, BIT = KEYS[ALIAS.get('E', 'E')]


def base():
    ed = ElecDet(ROM)
    ed.power_on(); ed.run_seconds(6.3); ed.press('3'); ed.press('1')
    return ed


def next_tick(ed):
    cpu = ed.cpu
    while True:
        hit = cpu.rom_address == EXIT
        cpu.step()
        if hit: return


def games_at(ed):
    """ENTER pressed now: {4:D value: [hold, case]} for the shortest hold giving each value."""
    e = copy.deepcopy(ed)
    e.inputs[ROW] |= BIT
    e.run_seconds(0.08)
    found, held = {}, 0.08
    while len(found) < 16 and held < 0.10 + 40 * STEP:
        e.run_seconds(STEP / 3); held += STEP / 3
        r = copy.deepcopy(e); r.inputs[ROW] &= ~BIT; r.run_seconds(0.02)
        d = r.cpu.ram[4 * 16 + 13]
        if d in found: continue
        r.run_seconds(4.78)
        found[d] = [round(held, 4), json.dumps(from_ram(r.cpu.ram), sort_keys=True)]
    return found


def chunk(job):
    a, b, skip = job
    ed = base()
    for _ in range(a): next_tick(ed)
    out = []
    for i in range(a, b):
        next_tick(ed)
        if i not in skip: out.append({'tick': i, 'games': games_at(ed)})
    return out


def main():
    workers = int(sys.argv[1]) if len(sys.argv) > 1 else 4
    os.makedirs(OUT, exist_ok=True)
    done = {json.loads(l)['tick'] for l in open(FILE)} if os.path.exists(FILE) else set()
    n = 200                                             # small chunks: progress is saved often
    jobs = [(PERIOD * k // n, PERIOD * (k + 1) // n) for k in range(n)]
    jobs = [(a, b, done) for a, b in jobs if not all(i in done for i in range(a, b))]
    print('ticks done', len(done), 'of', PERIOD, '| chunks to play', len(jobs), flush=True)
    with Pool(workers) as p, open(FILE, 'a') as f:
        for k, res in enumerate(p.imap_unordered(chunk, jobs)):
            for r in res: f.write(json.dumps(r) + '\n')
            f.flush()
            print('  chunks done', k + 1, 'of', len(jobs), flush=True)
    summary()


def summary():
    ticks = [json.loads(l) for l in open(FILE)]
    full = sum(len(t['games']) == 16 for t in ticks)
    cases = {}
    for t in ticks:
        for d, (hold, case) in t['games'].items():
            cases.setdefault(case, set()).add(int(d))
    per_tick = {len({c for _, c in t['games'].values()}) for t in ticks}
    print('ticks played', len(ticks), '| with all 16 values of 4:D', full)
    print('games played', sum(len(t['games']) for t in ticks), '| distinct cases', len(cases))
    print('distinct cases per tick (set of counts):', sorted(per_tick))
    print('cases reached by more than one value of 4:D:', sum(len(v) > 1 for v in cases.values()))


if __name__ == '__main__':
    summary() if sys.argv[1:] == ['summary'] else main()
