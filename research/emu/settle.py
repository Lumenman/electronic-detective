from elecdet import ElecDet, IPS
ed = ElecDet('D:/claude/GAMES/electronic_detective/elecdet')
ed.power_on(); ed.run_seconds(6.3); ed.press('3'); ed.press('1')
ed.press('E', gap=0)
prev = ed.ram(); t = 0; changes = []
while t < 60:
    ed.run_seconds(0.1); t += 0.1
    r = ed.ram()
    if r != prev:
        diff = [i for i in range(0x90) if r[i] != prev[i]]
        changes.append((round(t, 1), diff))
    prev = r
for t, d in changes[:12]: print(t, ['%02x' % i for i in d])
print('...', len(changes), 'change points; last:', changes[-1][0] if changes else None)
print('cells that ever changed after 3s:', sorted({'%02x' % i for t, d in changes if t > 3 for i in d}))
for cell in (0x04, 0x05, 0x24, 0x45, 0x0a, 0x0b, 0x49, 0x4a):
    ts = [t for t, d in changes if cell in d and t > 1]
    print('%02x' % cell, ts[:8], len(ts))
