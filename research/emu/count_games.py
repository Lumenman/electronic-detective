"""How many different games can the machine produce? Enumerates the tumbler states in the emulator."""
import sys, json
sys.path.insert(0, r'D:\claude\GAMES\electronic_detective\research\emu')
from collections import Counter
from elecdet import ElecDet
from probe_reads import ROM
ed = ElecDet(ROM); cpu = ed.cpu
states = []; os_ = cpu.step; EXIT = 1 << 7 | 0x29      # 1:29 = end of every tumbler tick
def st():
    if cpu.rom_address == EXIT:
        r = cpu.ram
        states.append((''.join('%x' % r[x * 16 + c] for c in range(7) for x in range(6)), '%x%x%x%x' % tuple(r[12:16])))
    os_()
cpu.step = st
ed.power_on(); ed.run_seconds(6.3); n0 = len(states); ed.run_seconds(21)
S = states[n0:]
print('ticks recorded', len(S))
first = S[0]; per = [i for i in range(1, len(S)) if S[i] == first]
print('period (ticks):', per[:3])
P = per[0]; cyc = S[:P]
assert S[P:2 * P] == cyc[:len(S[P:2 * P])]
tabs = Counter(t for t, c in cyc)
print('distinct tables in one period:', len(tabs), 'max repeats', max(tabs.values()))
for name, digs in (('standard start (level, players, ENTER)', 'ace'), ('one extra key before ENTER', 'bdf')):
    T = {t for t, c in cyc if c[0] in digs}
    games = set()
    for t in T:
        col = [t[c * 6:(c + 1) * 6] for c in range(7)]
        for m in range(4):
            for v in range(4):
                a, l = list(col[4]), list(col[5])
                if m < 2: l[0], l[5] = l[5], l[0]
                else:
                    l[0], l[4] = l[4], l[0]
                    k = 4 if v % 2 == 0 else 2; a[0], a[k] = a[k], a[0]
                games.add((col[0], col[1], col[2], col[3], ''.join(a), ''.join(l), m, v))
    print(name, '-> tables', len(T), ' games', len(games))
    if len(sys.argv) > 1: json.dump(sorted(T), open(sys.argv[1] + '_' + digs + '.json', 'w'))
