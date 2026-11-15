"""Time line of the real machine (ROM in the emulator) for a key script: what the display shows and when it sounds.

    python transcript.py "ON w7 3 1 E w62 S 1 E w2 Q 1 E w2 T w1"
Tokens: ON, digits, M W V (number of the murderer, of a wrong suspect, of the victim), S Q A E T (keys, held 0.15 s, 0.3 s apart), wN = wait N seconds, hN = next key held N seconds.
Add fair (first argument) to let game/dealer.py deal. Output: start time, duration, display, sound (Hz, level).
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'game'))
from board import ElecDet, IPS, load_romset

ROMZIP = 'D:/Downloads/elecdet.zip'
ALIAS = {'S': 'SUSPECT', 'Q': 'PQ', 'A': 'ACCUSE', 'E': 'ENTER', 'T': 'ENDTURN'}
STEP = 0.02


class Recorder:
    def __init__(self, dealer=None, seed=None):
        self.b = ElecDet(load_romset(ROMZIP)); self.t = 0.0; self.rows = []; self.dealer = dealer

    def run(self, seconds, label=''):
        b = self.b
        for _ in range(max(1, round(seconds / STEP))):
            c0 = b.cpu.cycles
            b.run(int(STEP * IPS))
            if self.dealer and b.powered: self.dealer.tick(b.cpu)
            ev, b.sound_events = b.sound_events, []
            ups = sum(1 for _, lv in ev if lv)                     # rising edges in this slice
            lvl = max((lv for _, lv in ev), default=0)
            d = b.display() if b.powered else '<off>'
            self.rows.append((self.t, d, ups, lvl, label)); label = ''
            self.t += STEP

    def key(self, k, hold=0.15, gap=0.3):
        if k == 'ON':
            self.b.power_on(); self.rows.append((self.t, '', 0, 0, 'ON')); return
        k = ALIAS.get(k, k)
        self.b.set_key(k, True); self.run(hold, 'key ' + k); self.b.set_key(k, False); self.run(gap)

    def play(self, script):
        hold = 0.15
        for tok in script.split():
            if tok[0] == 'w' and tok[1:].replace('.', '').isdigit(): self.run(float(tok[1:]))
            elif tok[0] == 'h' and tok[1:].replace('.', '').isdigit(): hold = float(tok[1:])
            elif tok in ('M', 'W', 'V'):                       # murderer, a wrong suspect, the victim (from RAM)
                R = lambda r, c: self.b.cpu.ram[r * 16 + c]
                num = lambda r: R(r, 10) + (10 * R(r, 11) if R(r, 11) < 10 else 0)   # 4:D is reused as key-hold counter
                m, v = num(0), num(4)
                n = {'M': m, 'V': v, 'W': next(x for x in range(1, 21) if x not in (m, v))}[tok]
                for ch in str(n): self.key(ch)
            else: self.key(tok, hold); hold = 0.15
        return self

    def segments(self):
        """Merge slices with the same display and the same kind of sound."""
        out = []
        for t, d, ups, lvl, label in self.rows:
            hz = round(ups / STEP)
            snd = 0 if hz == 0 else hz
            if out and not label and out[-1][2] == d and (out[-1][3] == 0) == (snd == 0) and \
                    (snd == 0 or abs(out[-1][3] - snd) <= max(60, 0.12 * snd)):
                out[-1][1] = t + STEP - out[-1][0]; out[-1][5] += 1; out[-1][6] += snd
            else:
                out.append([t, STEP, d, snd, lvl, 1, snd, label])
        return [(t, dur, d, round(tot / n), lvl, label) for t, dur, d, snd, lvl, n, tot, label in out]


if __name__ == '__main__':
    args = sys.argv[1:]; dealer = None
    if args[0] == 'fair':
        import random
        from dealer import Dealer
        dealer = Dealer(random.Random(1)); args = args[1:]
    r = Recorder(dealer).play(' '.join(args))
    for t, dur, d, hz, lvl, label in r.segments():
        print('%8.2f %6.2f  %-9r %s %s' % (t, dur, d, ('%5d Hz L%d' % (hz, lvl)) if hz else '      -    ', label))
