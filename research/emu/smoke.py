import time
from elecdet import ElecDet, ROM
ed = ElecDet(ROM)
t = time.time()
ed.power_on(); ed.run_seconds(6.3)
print('after on', repr(ed.display()))
ed.press('3'); print('3 ->', repr(ed.display()))
ed.press('1'); print('1 ->', repr(ed.display()))
ed.press('E', gap=0)
snaps = []
for k in range(8):
    ed.run_seconds(0.25); snaps.append(ed.ram())
ed.run_seconds(55); final = ed.ram()
tbl = lambda r: r[:0x60]
print('table final from snapshot', next((i for i, s in enumerate(snaps) if tbl(s) == tbl(final)), None), '(x0.25s)')
print('crime', repr(ed.display()))
ed.keys('S7E'); ed.run_seconds(1.5); print('alibi 7', repr(ed.display()))
print('speed x realtime', round((ed.cpu.cycles / 75000) / (time.time() - t), 2))
