import json
from elecdet import ElecDet, KEYS, ROM
ed = ElecDet(ROM)
ed.power_on(); cpu = ed.cpu
ev = [[-(-(i - 1246) // 1250) * 1250 + 1246, k, d] for i, k, d in json.load(open('schedule.json'))]
for i, k, d in ev[:5]:
    ed.run(i - cpu.cycles); row, bit = KEYS[k]
    if d: ed.inputs[row] |= bit
    else: ed.inputs[row] &= ~bit
    print(i, k, d, repr(ed.display()))
for s in range(8):
    ed.run_seconds(1); print('t+%d' % (s+1), repr(ed.display()))
from collections import Counter
c = Counter()
orig = ed._write_r
def spy(data):
    c[(ed.o, data)] += 1; orig(data)
ed.cpu.write_r = spy
ed.run_seconds(0.1)
for (o, d), n in sorted(c.items()): print('o=%02x r=%03x n=%d' % (o, d, n))
