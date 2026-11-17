"""Which deals of Two False Alibis (rules.deal_lies) cannot be solved, and why? (SPOILERS: playing logic.)

For every deal: is it solvable with everything asked (solver.lie_suspects leaves one name)? For the unsolvable
ones: who else can be the murderer, and how that one stands to the murderer, the second liar and the suspects
whose alibis the two borrowed. Prints counts; the raw rows go to lies_unsolvable.jsonl.

    python lies_unsolvable.py n
"""
import json, os, random, sys
from collections import Counter
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..', '..', 'game'))
from rules import deal_lies, observe, col_of
from solver import lie_suspects


def run(seed):
    case = deal_lies(random.Random(seed))
    obs, m = observe(case)
    rows = case['rows']
    row_of = {s: r for r, row in enumerate(rows) for s in row['people'] if s != obs['victim']}
    (m_, m_as), (second, sec_as) = case['lies']
    found = lie_suspects(obs)
    rec = {'seed': seed, 'murderer': m, 'second': second, 'm_as': m_as, 'sec_as': sec_as, 'found': sorted(found),
           'row': {s: row_of[s] for s in (m, second, m_as, sec_as)},
           'same_col_liars': col_of(m) == col_of(second), 'second_row': row_of[second]}
    alts = []
    for a in sorted(found - {m}):
        alts.append({'who': a, 'is_second': a == second, 'is_m_double': a == m_as, 'is_sec_double': a == sec_as,
                     'same_col_m': col_of(a) == col_of(m), 'row': row_of[a],
                     'same_row_as': [k for k, s in (('m', m), ('second', second), ('m_as', m_as), ('sec_as', sec_as)) if row_of[s] == row_of[a]]})
    rec['alts'] = alts
    return rec


if __name__ == '__main__':
    from multiprocessing import Pool
    n = int(sys.argv[1])
    with Pool(2) as p:
        recs = p.map(run, range(n), chunksize=4)
    with open(os.path.join(HERE, 'lies_unsolvable.jsonl'), 'w') as f:
        for r in recs: f.write(json.dumps(r) + '\n')
    bad = [r for r in recs if len(r['found']) > 1]
    print('%d deals, unsolvable %d (%.1f%%), murderer lost %d' % (n, len(bad), 100 * len(bad) / n, sum(r['murderer'] not in r['found'] for r in recs)))
    print('candidates per unsolvable deal:', dict(Counter(len(r['found']) for r in bad)))
    alts = [a for r in bad for a in r['alts']]
    for k in ('is_second', 'is_m_double', 'is_sec_double', 'same_col_m'):
        print('  other candidate %-14s %d of %d' % (k, sum(a[k] for a in alts), len(alts)))
    print('  other candidate shares a row with:', Counter(tuple(a['same_row_as']) for a in alts).most_common())
    for name, group in (('unsolvable', bad), ('solvable', [r for r in recs if len(r['found']) == 1])):
        print('%s: liars in one category %.0f%%; row of second liar %s; row of the one murderer imitates %s' % (
            name, 100 * sum(r['same_col_liars'] for r in group) / len(group),
            dict(sorted(Counter(r['second_row'] for r in group).items())), dict(sorted(Counter(r['row'][str(r['m_as'])] if isinstance(next(iter(r['row'])), str) else r['row'][r['m_as']] for r in group).items()))))
