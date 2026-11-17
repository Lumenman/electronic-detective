"""Ideal Electronic Detective board around the TMS0980 core (port of MAME hh_tms1k.cpp elecdet_state).
Same as research/emu/elecdet.py, plus: ROM comes as a {name: bytes} dict, speaker level changes are logged for audio.
The ROM files are NOT part of this code."""
import hashlib, math, os, zipfile
from tms0980 import TMS0980, PLA

CLOCK = 450000
IPS = CLOCK / 6          # instructions per second
FULL = 0.04              # share of time a lit segment is on: 0.04..0.15 by screen (measured), the dimmest is full

# key -> (input row, bit). Rows 0-3 are muxed by O0,O1,O4,O6; row 4 (Vss) is always active.
KEYS = {
    '4': (0, 0x01), '6': (0, 0x04), 'PQ': (0, 0x08), '5': (0, 0x10),
    '0': (1, 0x04), 'ENTER': (1, 0x08),
    '7': (2, 0x01), '9': (2, 0x04), 'ACCUSE': (2, 0x08), '8': (2, 0x10),
    '1': (3, 0x01), '3': (3, 0x04), 'SUSPECT': (3, 0x08), '2': (3, 0x10),
    'ENDTURN': (4, 0x08),
}
SEG = {0x3f: '0', 0x06: '1', 0x5b: '2', 0x4f: '3', 0x66: '4', 0x6d: '5', 0x7d: '6', 0x07: '7', 0x7f: '8',
       0x6f: '9', 0x67: '9', 0x77: 'A', 0x7c: 'b', 0x39: 'C', 0x5e: 'd', 0x79: 'E', 0x71: 'F', 0x37: 'N', 0: ' '}

# MAME romset (sha1)
ROMSET = {
    'mp6100a': '240bdb44b7d67d3b13ebf75851635ac4b4ca2bfd',
    'tms0980_common1_instr.pla': '2d127d98028ec8ec6ea10c179c25e447b14ba4d0',
    'tms0980_common1_micro.pla': 'd28ee59ded7f3b9dc3f0594a32a98391b6e9c961',
    'tms0980_elecdet_output.pla': 'e486802151a704c6273d4a8682c9c374d27d1e6d',
    'tms0980_common1_segment.pla': '72c56c58fde3fbb657d69647a9543b5f8fc74279',
}


def load_romset(path):
    """Folder or MAME zip -> {name: bytes}. Raises ValueError with a readable message."""
    files = {}
    if os.path.isdir(path):
        for n in ROMSET:
            p = os.path.join(path, n)
            if os.path.isfile(p):
                files[n] = open(p, 'rb').read()
    elif zipfile.is_zipfile(path):
        with zipfile.ZipFile(path) as z:
            for info in z.infolist():
                n = os.path.basename(info.filename)
                if n in ROMSET:
                    files[n] = z.read(info)
    else:
        raise ValueError('Not a folder or zip file: %s' % path)
    missing = [n for n in ROMSET if n not in files]
    if missing:
        raise ValueError('Missing ROM file(s): ' + ', '.join(missing))
    bad = [n for n in ROMSET if hashlib.sha1(files[n]).hexdigest() != ROMSET[n]]
    if bad:
        raise ValueError('ROM file(s) do not match the known dump: ' + ', '.join(bad))
    return files


def bitswap8(v, *bits):
    return sum(((v >> b) & 1) << (7 - i) for i, b in enumerate(bits))


class ElecDet:
    SPEAKER = (0, 1, 1, 2)       # R7+R8 (they switch together in practice)

    def __init__(self, files):
        txt = lambda n: files[n].decode('ascii')
        data = files['mp6100a']
        words = [(data[i] << 8 | data[i + 1]) for i in range(0, len(data), 2)]
        self.inputs = [0] * 5
        self.inp_mux = 0
        self.o = self.r = 0
        self.segtime = [[-10**12] * 7 for _ in range(7)]   # [digit][segment] -> cycle when last lit
        self.acc, self.mark, self.since = {}, 0, 0         # (R digits, segments) -> cycles lit, since the last brightness()
        self.glow = [[0.0] * 7 for _ in range(7)]          # [digit][segment] smoothed share of time lit
        self.level = 0
        self.sound_events = []                             # (cycle, speaker level)
        self.powered = False
        self.cpu = TMS0980(words,
                           PLA(txt('tms0980_common1_instr.pla'), 9, 22),
                           PLA(txt('tms0980_common1_micro.pla'), 6, 20),
                           PLA(txt('tms0980_elecdet_output.pla'), 4, 8),
                           PLA(txt('tms0980_common1_segment.pla'), 3, 8),
                           self._read_k, self._write_o, self._write_r, self._power_off)

    # --- board callbacks (elecdet_state) ---
    def _read_k(self):
        k = self.inputs[4]
        for i in range(4):
            if self.inp_mux >> i & 1:
                k |= self.inputs[i]
        return k

    def _speaker(self):
        lv = self.SPEAKER[self.r >> 7 & 3] if self.o & 0x80 else 0
        if lv != self.level and hasattr(self, 'cpu'):
            self.level = lv
            self.sound_events.append((self.cpu.cycles, lv))

    def _lit(self):
        """Credit the time since the last R/O change to what was lit during it."""
        if not hasattr(self, 'cpu'):           # the CPU writes R/O while it is being built
            return
        now = self.cpu.cycles
        segs = bitswap8(self.o, 7, 5, 2, 1, 4, 0, 6, 3) & 0x7f
        if segs and self.r & 0x7f and now > self.mark:
            key = (self.r & 0x7f, segs)
            self.acc[key] = self.acc.get(key, 0) + now - self.mark
        self.mark = now

    def _write_o(self, data):
        self._lit()
        self.inp_mux = (data & 3) | (data >> 2 & 4) | (data >> 3 & 8)
        self.o = data
        self._speaker()

    def _write_r(self, data):
        self._lit()
        self.r = data
        self._speaker()
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

    def power_off(self):
        self.powered = False

    def set_key(self, key, down):
        row, bit = KEYS[key]
        if down:
            self.inputs[row] |= bit
        else:
            self.inputs[row] &= ~bit

    def run(self, n):
        step, end = self.cpu.step, self.cpu.cycles + n
        while self.powered and self.cpu.cycles < end:
            step()
        self.cpu.cycles = max(self.cpu.cycles, end)   # time keeps moving while switched off

    def segments(self, window=0.05):
        """Lit segment masks per digit, left to right (digit 6 is leftmost)."""
        now, w = self.cpu.cycles, window * IPS
        if not self.powered:
            return [0] * 7
        return [sum(1 << b for b in range(7) if now - self.segtime[i][b] <= w) for i in range(6, -1, -1)]

    def brightness(self, tau=0.02):
        """Per digit, left to right: 7 segment levels 0..1 from the share of time each was lit,
        smoothed over tau seconds like the eye. A segment touched for a few instructions stays dark."""
        self._lit()
        now = self.cpu.cycles
        dt, self.since = now - self.since, now
        duty = [[0.0] * 7 for _ in range(7)]
        if self.powered and dt > 0:
            for (r, s), t in self.acc.items():
                for i in range(7):
                    if r >> i & 1:
                        for b in range(7):
                            if s >> b & 1:
                                duty[i][b] += t / dt
        self.acc.clear()
        k = math.exp(-dt / (tau * IPS)) if self.powered else 0
        self.glow = [[g * k + d * (1 - k) for g, d in zip(gr, dr)] for gr, dr in zip(self.glow, duty)]
        # sqrt: perceived brightness grows slower than the time lit
        return [[min(1.0, g / FULL) ** 0.5 for g in self.glow[i]] for i in range(6, -1, -1)]

    def display(self, window=0.05):
        return ''.join(SEG.get(s, '?') for s in self.segments(window))
