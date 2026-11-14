import json, sys
import compare_trace as ct
from elecdet import ElecDet, KEYS
off = int(sys.argv[1]) if len(sys.argv) > 1 else 0
Q = int(sys.argv[2]) if len(sys.argv) > 2 else 1
P = int(sys.argv[3]) if len(sys.argv) > 3 else 0
ev = [[-(-(i - P) // Q) * Q + P, k, d] for i, k, d in json.load(open("schedule.json"))]
ed = ElecDet(ct.ROM)
cpu = ed.cpu
orig = cpu.step
def step():
    while ev and ev[0][0] + off <= cpu.cycles:
        i, k, d = ev.pop(0); row, bit = KEYS[k]
        if d: ed.inputs[row] |= bit
        else: ed.inputs[row] &= ~bit
    orig()
cpu.step = step
ed.run = lambda n: [step() for _ in range(n)]
ct.compare('ref/keys.txt', ed)
