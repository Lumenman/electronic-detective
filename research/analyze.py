"""Aggregate statistics over collected Electronic Detective games (data/f_*.tsv).
Writes report.txt with aggregates only (no per-game solutions)."""
import glob, re
from collections import Counter, defaultdict

NUM = {'0': 0, '1': 1, '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, 'b': 6, '7': 7, '8': 8, '9': 9}
PLACE = {10: 'A', 6: 'B', 12: 'C', 13: 'D', 14: 'E', 15: 'F'}  # RAM col5 -> place


def num(s): return int(''.join(str(NUM[c]) for c in s))
def addr(v): return ('E' if v >= 5 else 'W', (v - 1) % 4 + 1)  # town 1=Up 2=Mid 3=Down
def male(s): return s <= 10
def odd(s): return s % 2 == 1
def cat(s): return ('M' if male(s) else 'F') + ('o' if odd(s) else 'e')


def alibi(s):
    s = s[:7].ljust(7); r = {}
    if s == '0000000': return {'dk': 1}
    if s[0] != ' ': r['side'] = int(s[0])
    if s[1] != ' ': r['town'] = int(s[1])
    if s[2] != ' ': r['place'] = s[2].upper()
    w = [num((s[a] + s[b]).strip()) for a, b in ((3, 4), (5, 6)) if (s[a] + s[b]).strip()]
    if w: r['with'] = w
    return r


def load(fn):
    g = {'q': defaultdict(list), 'alibis': defaultdict(list), 'off': {}}
    for line in open(fn):
        lab, _, val = line.rstrip('\n').partition('\t')
        if lab == 'crime':
            d = val[:7]; g['victim'] = num(d[:2].strip()); g['scene'] = d[2].upper()
        elif lab.startswith('ram'):
            g[lab] = [int(c, 16) for c in val]
        elif lab.startswith('alibi'):
            s = int(re.match(r'alibi(\d+)', lab).group(1)); g['alibis'][s].append(val[:7])
        elif lab.startswith('q'):
            s, q = map(int, re.match(r'q(\d+)_(\d+)', lab).groups()); g['q'][(s, q)].append(val[:7].strip())
        elif lab.startswith('off'):
            s, q = map(int, re.match(r'off(\d+)_(\d+)', lab).groups()); g['off'][(s, q)] = val[:7].strip()
        elif lab.startswith('acc'):
            v = val[:7].strip()
            mm = re.match(r'^([0-9b]+)d1d$', v) or re.match(r'^([0-9b]+)4E5$', v)
            if mm: g['murderer'] = num(mm.group(1))
    return g


def truth(g):
    r = g['ram0']; R = [r[i * 16:(i + 1) * 16] for i in range(8)]
    loc = {}; places = {}; used = set()
    for i in range(5):
        c = R[i]; p = PLACE[c[5]]; used.add(c[4])
        occ = [c[0] or 10, c[1], (c[2] or 10) + 10, c[3] + 10]
        occ = [s for s in occ if s != g['victim']]
        places[p] = {'addr': addr(c[4]), 'occ': occ}
        for s in occ: loc[s] = p
    scene = [p for p in 'ABCDEF' if p not in places]
    assert scene == [g['scene']], (scene, g['scene'])
    places[g['scene']] = {'addr': addr(({1, 2, 3, 5, 6, 7} - used).pop()), 'occ': []}
    return loc, places


import sys
PREFIX = sys.argv[1] if len(sys.argv) > 1 else 'h'


def main():
    out = []; P = lambda *a: out.append(' '.join(str(x) for x in a))
    C = defaultdict(Counter); bad = Counter(); n = 0
    prints = defaultdict(Counter)
    for fn in sorted(glob.glob(f'data/{PREFIX}_*.tsv')):
        g = load(fn)
        if 'murderer' not in g or 'ram0' not in g: bad['incomplete'] += 1; continue
        loc, places = truth(g); M = g['murderer']; V = g['victim']
        A = lambda s, q: g['q'].get((s, q), [])
        w38 = Counter(A(s, 5)[0].upper() for s in range(1, 21) if A(s, 5) and s != V)
        w45 = Counter(A(s, 6)[0].upper() for s in range(1, 21) if A(s, 6) and s != V)
        q4 = Counter(A(s, 4)[0] for s in range(1, 21) if A(s, 4) and s != V)
        if len(w38) != 1 or len(w45) != 1 or len(q4) != 1: bad['answers_disagree'] += 1; continue
        n += 1
        L38 = next(iter(w38)); L45 = next(iter(w45)); mw = '.38' if next(iter(q4)) == '4E5' else '.45'
        wloc = {'.38': L38, '.45': L45}
        three = [p for p, v in places.items() if len(v['occ']) == 3]
        # setup
        C['victim'][V] += 1; C['murderer'][M] += 1; C['scene'][g['scene']] += 1
        C['murder_weapon'][mw] += 1
        C['murderer_category'][cat(M)] += 1; C['victim_category'][cat(V)] += 1
        C['victim_same_sex_as_murderer'][male(V) == male(M)] += 1
        C['place_sizes'][tuple(sorted(len(v['occ']) for v in places.values()))] += 1
        C['three_place_missing_category_is_victims'][cat(V) not in [cat(s) for s in places[three[0]]['occ']]] += 1
        C['weapons_same_place'][L38 == L45] += 1
        C['weapon_at_scene'][g['scene'] in (L38, L45)] += 1
        C['murderer_at_weapon_place'][loc[M] in (L38, L45)] += 1
        C['murderer_in_three_place'][loc[M] == three[0]] += 1
        C['some_weapon_in_three_place'][three[0] in (L38, L45)] += 1
        C['addresses_are_permutation'][sorted(v['addr'] for v in places.values()) == sorted((s, t) for s in 'WE' for t in (1, 2, 3))] += 1
        C['n_samesex_witnesses_at_murder_weapon'][sum(male(s) == male(M) for s in places[wloc[mw]]['occ'])] += 1
        # alibis
        for s, lst in g['alibis'].items():
            if s == V: C['victim_alibi'][lst[0]] += 1; continue
            C['alibi_constant_within_game'][len(set(lst)) == 1] += 1
            a = alibi(lst[0]); p = loc[s]; ad = places[p]['addr']
            nw = len(a.get('with', []))
            C['alibi_nfacts'][sum(k in a for k in ('side', 'town', 'place')) + nw] += 1
            C['alibi_fields'][' '.join(k for k in ('side', 'town', 'place') if k in a) + f' with={nw}'] += 1
            C['alibi_(companions,named)'][(len(places[p]['occ']) - 1, nw)] += 1
            ok = True
            if 'side' in a: ok &= a['side'] == (1 if ad[0] == 'W' else 2)
            if 'town' in a: ok &= a['town'] == ad[1] + 2
            if 'place' in a: ok &= a['place'] == p
            for t in a.get('with', []): ok &= loc.get(t) == p and t != s
            C['alibi_truthful'][ok] += 1
        # private questions
        mp = loc[M]; mad = places[mp]['addr']
        yes = lambda b: '4E5' if b else 'N0'
        for (s, q), a in g['q'].items():
            if s == V: C['victim_answers'][a[0]] += 1
        for s in range(1, 21):
            p = loc[s] if s != V else three[0]
            ad = places[p]['addr']
            exp = {1: yes(mad[0] == 'E'), 2: yes(male(M)), 3: str(mad[1] + 2), 4: yes(mw == '.38'), 5: L38, 6: L45,
                   7: three[0], 8: yes(mp in 'ABC'), 9: yes(ad[0] == 'E'), 10: str(ad[1] + 2),
                   11: yes(p in 'ABC'), 12: yes(p in (L38, L45))}
            for q in range(1, 13):
                a = A(s, q)
                if a: C[(f'VICTIM_Q{q:02d}_as_if_at_three_place' if s == V else f'Q{q:02d}_correct')][a[0].upper() == exp[q].upper()] += 1
            for q, wn in ((13, '.38'), (14, '.45')):
                a = A(s, q)
                if not a: continue
                if s == V: C['VICTIM_prints_answer'][a[0]] += 1; continue
                if wloc[wn] != p:
                    k = 'no weapon here' if p not in (L38, L45) else 'other weapon here'
                    pat = a
                else:
                    k = ('murder weapon' if wn == mw else 'non-murder weapon') + ', ' + ('same sex' if male(s) == male(M) else 'opposite sex')
                    # =M: says parity equal to murderer's; !M: opposite
                    pat = ['=M' if (x == '4E5') == odd(M) else '!M' if x in ('4E5', 'N0') else x for x in a]
                    prints[f'{k}, Q{q} raw, murderer {"odd" if odd(M) else "even"}'][' '.join(a)] += 1
                prints[k][' '.join(pat)] += 1
        for (s, q), a in g['off'].items():
            C['offcard_answer'][a] += 1
            if a != 'EE': C['offcard_not_EE_(suspect,q,is_victim)'][(s, q, s == V)] += 1
    P(f'games analysed: {n}; skipped: {dict(bad)}')
    for k in sorted(C):
        items = sorted(C[k].items(), key=lambda kv: (-kv[1], str(kv[0])))
        P(f'\n## {k}'); P('   ' + ', '.join(f'{a}: {b}' for a, b in items[:25]))
    P('\n## prints Q13/Q14, 3 asks each (=M same parity as murderer, !M opposite)')
    for k in sorted(prints):
        P(f'  [{k}] n={sum(prints[k].values())}')
        for pat, c in prints[k].most_common(10): P(f'     {pat}: {c}')
    open('report.txt', 'w').write('\n'.join(out) + '\n')
    print(out[0])


main()
