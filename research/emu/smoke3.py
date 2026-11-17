import json
from elecdet import ElecDet, KEYS
ed = ElecDet('D:/claude/GAMES/electronic_detective/elecdet')
ed.power_on(); cpu = ed.cpu
ev = [[-(-(i - 1246) // 1250) * 1250 + 1246, k, d] for i, k, d in json.load(open('schedule.json'))]
for i, k, d in ev[:4]:
    ed.run(i - cpu.cycles); row, bit = KEYS[k]
    if d: ed.inputs[row] |= bit
    else: ed.inputs[row] &= ~bit
ed.run(20000)
log=[]
orig = ed._write_r
def spy(data): log.append((cpu.cycles, ed.o, data, cpu.a)); orig(data)
cpu.write_r = spy
ed.run(400)
for c,o,d,a in log: print(c, 'o=%02x r=%03x A=%x' % (o,d,a))
print([hex(x) for x in cpu.ram[0x70:0x80]])
