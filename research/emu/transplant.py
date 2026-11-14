"""Locate the fingerprint-lie state: find a lying game L and a truthful game T, then copy non-layout cells T->L,
bisecting until the cell(s) that turn L's opposite-sex answer truthful are found. Uses 2 processes."""
import copy, sys
from multiprocessing import Pool
from permute_prints import make_snap, ask
from sweep import decode


def probe(seed):
    e = make_snap(seed)
    d = decode([e.cpu.ram[a] for a in range(0x90)]); M = d['murderer']
    q = 13 if d['murder_weapon'] == '.38' else 14
    wp = d['p38'] if q == 13 else d['p45']
    opp = [s for s in d['places'][wp]['occ'] if (s <= 10) != (M <= 10)]
    truth = '4E5' if M % 2 else 'n0'
    return seed, e, opp[0], q, truth, ask(copy.deepcopy(e), opp[0], q)


def main():
    with Pool(2) as p:
        games = p.map(probe, range(1, 11))
    for seed, e, w, q, truth, a in games:
        print('seed', seed, 'answer', a, 'lie' if a != truth else 'truth')
    L = next(g for g in games if g[5] != g[4] and g[5] in ('4E5', 'n0'))
    T = next(g for g in games if g[5] == g[4])
    _, eL, w, q, truth, _ = L; eT = T[1]
    cells = [r << 4 | c for r in range(5) for c in range(6, 16)] + list(range(0x50, 0x90))

    def lies_with(cs):
        e = copy.deepcopy(eL)
        for c in cs:
            e.cpu.ram[c] = eT.cpu.ram[c]
        return ask(e, w, q) != truth

    print('L seed', L[0], 'T seed', T[0], 'all copied ->', 'lie' if lies_with(cells) else 'truth')
    while len(cells) > 1:
        half = cells[:len(cells) // 2]
        cells = cells[len(cells) // 2:] if lies_with(half) else half
        print('narrowed to', ['%X:%X' % (c >> 4, c & 15) for c in cells])
    c = cells[0]
    print('cell %X:%X  L=%X T=%X' % (c >> 4, c & 15, eL.cpu.ram[c], eT.cpu.ram[c]))


if __name__ == '__main__':
    main()
