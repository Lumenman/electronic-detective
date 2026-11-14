import random, sys
from elecdet import ElecDet
from tracer import Tracer
from probe_reads import ROM
ed = ElecDet(ROM); rnd = random.Random(int(sys.argv[1]) if len(sys.argv) > 1 else 1)
ed.power_on(); ed.run_seconds(6.3 + rnd.random() * 3); ed.press('3'); ed.press('1')
pre = ed.ram()
with Tracer(ed, 'setup_trace.txt', pages={2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12}):
    ed.press('E', gap=0); ed.run_seconds(5)
print('pre ', pre); print('post', ed.ram()); print(repr(ed.display()))
