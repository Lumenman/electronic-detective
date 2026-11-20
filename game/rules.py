"""Rules of the original as code (SPOILERS: this is research/RULES.md section 5 in executable form).

A case is the ROM table after generation: six rows (murderer's place, .38, .45, second place of four,
place of three, scene) plus the categories of victim and murderer and the weapon flag.
observe(case) returns everything a player can learn: all alibis and all answers.

    python rules.py     compares the rules with 300 recorded MAME games (../research/data/h_*.tsv)
"""
CARDS = {1: (1, 2, 9), 2: (2, 3, 9), 3: (3, 4, 5), 4: (4, 5, 9), 5: (1, 4, 9), 6: (5, 6, 12), 7: (2, 5, 12),
         8: (3, 5, 12), 9: (1, 5, 12), 10: (7, 8, 12), 11: (6, 7, 11), 12: (2, 6, 11), 13: (3, 7, 11),
         14: (1, 6, 11), 15: (4, 7, 11), 16: (6, 8, 10), 17: (2, 7, 10), 18: (1, 8, 10), 19: (3, 8, 10), 20: (4, 8, 10)}
OFF_CARD = (11, 12, 13, 14, 15)      # the original also answers question 12 for these, though their cards do not list it
LETTER = {10: 'A', 6: 'B', 12: 'C', 13: 'D', 14: 'E', 15: 'F'}
# template -> column -> (fields, companion columns); s = side, a = area, p = place
TPL = {1: [('s', (1, 3)), ('p', ()), ('a', (0,)), ('a', ())], 2: [('p', (3,)), ('ap', ()), ('sa', ()), ('s', (1, 2))],
       3: [('p', (1,)), ('', (2, 3)), ('s', ()), ('a', ())], 4: [('sa', ()), ('p', ()), ('', (1, 3)), ('', (0, 2))],
       5: [('sp', ()), ('a', (0,)), ('', (0, 1)), ('', (1, 2))]}
THREE = [('ap', None), ('sa', 2), ('s', 0)]          # place of three: position -> (fields, companion position)


FRAMED = (1, 2, 3, 8)                # the accomplice game: questions answered by the false story


def male(n): return n <= 10
def col_of(n): return (0 if n % 2 == 0 else 1) + (0 if n <= 10 else 2)
def yn(b): return 'Y' if b else 'N'


def story(rows, r, s):
    """Answers to 1, 2, 3, 8 if suspect s, at row r, were the murderer."""
    return {1: yn(rows[r]['side'] == 2), 2: yn(male(s)), 3: str(rows[r]['area']), 8: yn(rows[r]['letter'] in 'ABC')}


def from_ram(ram):
    """Case from a RAM dump (list of nibbles, rows of 16) taken after generation."""
    R = lambda r, c: ram[r * 16 + c]
    who = lambda r, c: [R(r, c) or 10, R(r, c), (R(r, c) or 10) + 10, R(r, c) + 10][c]
    return {'rows': [{'people': [who(r, c) for c in range(4)] if r < 5 else [], 'side': 2 if R(r, 4) & 4 else 1,
                      'area': 2 + (R(r, 4) & 3), 'letter': LETTER[R(r, 5)], 'tpl': R(r, 6)} for r in range(6)],
            'vcol': R(4, 12), 'mcol': R(4, 13), 'w38': bool(R(1, 9) & 2)}


def deal(rng):
    """A random case: every column shuffled, any address and letter order, categories and weapon at random."""
    cols = [[2, 4, 6, 8, 10], [1, 3, 5, 7, 9], [12, 14, 16, 18, 20], [11, 13, 15, 17, 19]]
    for c in cols: rng.shuffle(c)
    addr = [(s, a) for s in (1, 2) for a in (3, 4, 5)]; rng.shuffle(addr)
    let = list('ABCDEF'); rng.shuffle(let)
    tpl = [1, 2, 3, 4, 5]; rng.shuffle(tpl); tpl = tpl[:4] + [6, tpl[4]]
    rows = [{'people': [cols[c][r] for c in range(4)] if r < 5 else [], 'side': addr[r][0], 'area': addr[r][1],
             'letter': let[r], 'tpl': tpl[r]} for r in range(6)]
    return {'rows': rows, 'vcol': rng.randrange(4), 'mcol': rng.randrange(4), 'w38': rng.random() < 0.5}


def deal_lies(rng):
    """The game of two false alibis: the murderer and one more suspect say they were where they were not - each
    tells the alibi of somebody of the same sex and parity who really was at another place (never one with a gun:
    the murderer is never there, so nobody would say so). All answers to questions stay true.
    The case gets 'lies': [[liar, whose alibi], ...]. Whether it can be solved is for the caller to check."""
    case = deal(rng)
    rows = case['rows']
    victim, murderer = rows[4]['people'][case['vcol']], rows[0]['people'][case['mcol']]
    row_of = {s: r for r, row in enumerate(rows) for s in row['people'] if s != victim}
    doubles = lambda s, second: [o for o in sorted(row_of) if col_of(o) == col_of(s) and o not in (murderer, second)
                                 and row_of[o] not in (row_of[s], 1, 2)]
    second = rng.choice([s for s in sorted(row_of) if s != murderer and doubles(s, s) and doubles(murderer, s)])
    case['lies'] = [[s, rng.choice(doubles(s, second))] for s in (murderer, second)]
    return case


def deal_frame(rng):
    """The accomplice game: the murderer and an accomplice answer 1, 2, 3, 8 as if an innocent one (framed, never at
    a gun) had done it; all alibis and other answers are true. The framed one differs from the truth in as many of
    these answers as can be, and the accomplice is one whose card asks the most of the differing ones (research/
    solver/frame.py 'far loud': always solvable, the pair always known). The case gets 'frame': [murderer,
    accomplice, framed]."""
    case = deal(rng)
    rows = case['rows']
    victim, murderer = rows[4]['people'][case['vcol']], rows[0]['people'][case['mcol']]
    row_of = {s: r for r, row in enumerate(rows) for s in row['people'] if s != victim}
    true = story(rows, 0, murderer)
    best = lambda pool, score: [s for s in pool if score(s) == max(map(score, pool))]
    diff = lambda s: sum(story(rows, row_of[s], s)[q] != true[q] for q in FRAMED)
    x = rng.choice(best([s for s in sorted(row_of) if s != murderer and row_of[s] not in (1, 2) and diff(s)], diff))
    false = story(rows, row_of[x], x)
    loud = lambda c: sum(q in CARDS[c] and false[q] != true[q] for q in FRAMED)
    case['frame'] = [murderer, rng.choice(best([s for s in sorted(row_of) if s not in (murderer, x)], loud)), x]
    return case


def observe(case):
    rows, vcol, mcol, w38 = case['rows'], case['vcol'], case['mcol'], case['w38']
    victim, murderer = rows[4]['people'][vcol], rows[0]['people'][mcol]
    loc = {s: (r, c) for r in range(5) for c, s in enumerate(rows[r]['people']) if s != victim}
    alibi, ans, hidden = {}, {}, {}
    for s, (r, c) in loc.items():
        row = rows[r]
        if r < 4:
            f, mates = TPL[row['tpl']][c]; mates = [row['people'][x] for x in mates]
        else:
            pos = {x: x for x in range(3)}
            if vcol != 3: pos[3] = vcol; del pos[vcol]                  # the odd woman takes the victim's position
            f, mp = THREE[pos[c]]
            mates = [row['people'][x] for x in pos if pos[x] == mp] if mp is not None else []
        a = {}
        if 's' in f: a['side'] = row['side']
        if 'a' in f: a['area'] = row['area']
        if 'p' in f: a['place'] = row['letter']
        if mates: a['with'] = mates
        alibi[s] = a
        same = male(s) == male(murderer)
        q13 = '?' if r != 1 else yn(murderer % 2 == 1 if same else True) if w38 else yn(s % 2 == 0)
        q14 = '?' if r != 2 else yn(same and murderer % 2 == 1)
        table = {1: yn(rows[0]['side'] == 2), 2: yn(male(murderer)), 3: str(rows[0]['area']), 4: yn(w38),
                 5: rows[1]['letter'], 6: rows[2]['letter'], 7: rows[4]['letter'], 8: yn(rows[0]['letter'] in 'ABC'),
                 9: yn(row['side'] == 2), 10: str(row['area']), 11: yn(row['letter'] in 'ABC'), 12: yn(r in (1, 2)),
                 13: q13, 14: q14}
        for q in CARDS[s] + (13, 14): ans[(s, q)] = table[q]
        if s in OFF_CARD: hidden[(s, 12)] = table[12]
    for s, o in case.get('lies', ()): alibi[s] = dict(alibi[o])        # the liar tells the other one's alibi
    if case.get('frame'):                                               # the pair tells the framed one's story
        m, c, x = case['frame']; false = story(rows, loc[x][0], x)
        for s in (m, c):
            for q in FRAMED:
                if (s, q) in ans: ans[(s, q)] = false[q]
    return {'victim': victim, 'scene': rows[5]['letter'], 'alibi': alibi, 'ans': ans, 'hidden': hidden}, murderer


if __name__ == '__main__':
    import glob, os, sys
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'research'))
    from analyze import load, alibi as parse_alibi
    NORM = {'4E5': 'Y', 'N0': 'N', '0000000': '?', 'b': 'B', 'd': 'D'}
    games = diffs = 0
    for fn in sorted(glob.glob(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'research', 'data', 'h_*.tsv'))):
        g = load(fn)
        if 'ram0' not in g or 'murderer' not in g: continue
        obs, murderer = observe(from_ram(g['ram0'])); games += 1; bad = []
        if (obs['victim'], obs['scene'], murderer) != (g['victim'], g['scene'], g['murderer']): bad.append('crime')
        for s, lst in g['alibis'].items():
            if s == g['victim']: continue
            a = parse_alibi(lst[0]); a.pop('dk', None)
            if 'town' in a: a['area'] = a.pop('town')
            if a != obs['alibi'][s]: bad.append('alibi %d: %r vs %r' % (s, a, obs['alibi'][s]))
        for (s, q), lst in g['q'].items():
            if s == g['victim']: continue
            if NORM.get(lst[0], lst[0]) != obs['ans'].get((s, q)): bad.append('q%d to %d: %r vs %r' % (q, s, lst[0], obs['ans'].get((s, q))))
        if bad: diffs += 1; print(os.path.basename(fn), bad[:4])
    print('%d games compared, %d with differences' % (games, diffs))
