"""Ideal Electronic Detective board around the TMS0980 core (port of MAME hh_tms1k.cpp elecdet_state).

    ed = ElecDet(rom_dir)
    ed.power_on(); ed.run_seconds(1)
    ed.press('3'); ed.press('1'); ed.press('ENTER'); ed.run_seconds(55)
    print(ed.display())
The ROM files are NOT part of this code; pass the folder with mp6100a and the *.pla files.
"""
import os
from tms0980 import TMS0980, PLA

CLOCK = 450000
IPS = CLOCK / 6          # instructions per second

# key -> (input row, bit). Rows 0-3 are muxed by O0,O1,O4,O6; row 4 (Vss) is always active.
KEYS = {
    '4': (0, 0x01), '6': (0, 0x04), 'PQ': (0, 0x08), '5': (0, 0x10),
    '0': (1, 0x04), 'ENTER': (1, 0x08),
    '7': (2, 0x01), '9': (2, 0x04), 'ACCUSE': (2, 0x08), '8': (2, 0x10),
    '1': (3, 0x01), '3': (3, 0x04), 'SUSPECT': (3, 0x08), '2': (3, 0x10),
    'ENDTURN': (4, 0x08),
}
ALIAS = {'S': 'SUSPECT', 'Q': 'PQ', 'A': 'ACCUSE', 'E': 'ENTER', 'T': 'ENDTURN'}
SEG = {0x3f: '0', 0x06: '1', 0x5b: '2', 0x4f: '3', 0x66: '4', 0x6d: '5', 0x7d: '6', 0x07: '7', 0x7f: '8',
       0x6f: '9', 0x67: '9', 0x77: 'A', 0x7c: 'b', 0x39: 'C', 0x5e: 'd', 0x79: 'E', 0x71: 'F', 0x37: 'N', 0: ' '}


def bitswap8(v, *bits):
    return sum(((v >> b) & 1) << (7 - i) for i, b in enumerate(bits))


class ElecDet:
    def __init__(self, rom_dir):
        rd = lambda n: open(os.path.join(rom_dir, n)).read()
        data = open(os.path.join(rom_dir, 'mp6100a'), 'rb').read()
        words = [(data[i] << 8 | data[i + 1]) for i in range(0, len(data), 2)]
        self.inputs = [0] * 5
        self.inp_mux = 0
        self.o = 0
        # display is scanned per segment: segtime[digit][segment] = instruction count when last lit
        self.segtime = [[-10**12] * 7 for _ in range(7)]
        self.speaker_toggles = 0
        self.powered = False
        self.cpu = TMS0980(words,
                           PLA(rd('tms0980_common1_instr.pla'), 9, 22),
                           PLA(rd('tms0980_common1_micro.pla'), 6, 20),
                           PLA(rd('tms0980_elecdet_output.pla'), 4, 8),
                           PLA(rd('tms0980_common1_segment.pla'), 3, 8),
                           self._read_k, self._write_o, self._write_r, self._power_off)

    # --- board callbacks (elecdet_state) ---
    def _read_k(self):
        k = self.inputs[4]
        for i in range(4):
            if self.inp_mux >> i & 1:
                k |= self.inputs[i]
        return k

    def _write_o(self, data):
        self.inp_mux = (data & 3) | (data >> 2 & 4) | (data >> 3 & 8)
        self.o = data

    def _write_r(self, data):
        if self.o & 0x80 and data >> 7 & 3:
            self.speaker_toggles += 1
        segs = bitswap8(self.o, 7, 5, 2, 1, 4, 0, 6, 3) & 0x7f
        if segs and hasattr(self, 'cpu'):
            now = self.cpu.cycles
            for i in range(7):
                if data >> i & 1:
                    row = self.segtime[i]
                    for b in range(7):
                        if segs >> b & 1:
                            row[b] = now

    def _power_off(self, v):
        if v:
            self.powered = False

    # --- control ---
    def power_on(self):
        self.cpu.reset()
        self.powered = True

    def run(self, n):
        step = self.cpu.step
        for _ in range(n):
            step()

    def run_seconds(self, s):
        self.run(int(s * IPS))

    def press(self, key, hold=0.2, gap=0.3):
        row, bit = KEYS[ALIAS.get(key, key)]
        self.inputs[row] |= bit
        self.run_seconds(hold)
        self.inputs[row] &= ~bit
        self.run_seconds(gap)

    def keys(self, s):
        for c in s:
            self.press(c)

    def display(self, window=0.05):
        """Digits lit within the last `window` seconds, left to right (digit 6 is leftmost)."""
        now, w = self.cpu.cycles, window * IPS
        out = ''
        for i in range(6, -1, -1):
            segs = sum(1 << b for b in range(7) if now - self.segtime[i][b] <= w)
            out += SEG.get(segs, '{%02x}' % segs)
        return out

    def ram(self):
        return ''.join('%x' % self.cpu.ram[a] for a in range(0x90))
