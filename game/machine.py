"""The game machine without the ROM: key entry, turns, answers, display and sounds.

It behaves like the original (compared key by key with the ROM in research/emu/diff_machine.py), but the case is
dealt by rules.deal() and the answers come from rules.observe(). It offers the same interface as board.ElecDet,
so the window can drive either. Time is counted in CPU cycles of the original (IPS per second).

    m = Machine(); m.power_on(); m.run(3 * SEC); m.key('3'); m.key('1'); m.key('ENTER'); m.run(6 * SEC); m.display()
"""
import random
from board import IPS, SEG
from rules import deal, observe
from sounds import SOUNDS

GLYPH = {'A': 'A', 'B': 'b', 'C': 'C', 'D': 'd', 'E': 'E', 'F': 'F'}
MASK = {ch: m for m, ch in SEG.items() if m != 0x67}
BLANK, EE, END, ON = ' ' * 7, '     EE', '  ENd  ', '     0N'
SEC = int(IPS)
BLINK, BLINK_NO = (0.44, 0.14), (0.26, 0.14)       # seconds on, off
OFF_AFTER, OFF_EXTEND = 240, 177                   # a finished game switches itself off; END TURN gives more time


def digits(n, width=2):
    return str(n).rjust(width).replace('6', 'b')


class Machine:
    def __init__(self, rng=None, case=None):
        self.rng, self.fixed_case = rng or random.SystemRandom(), case
        self.powered = False
        self.cycles = self.busy_until = 0
        self.off_at = None
        self.cpu = self                   # the window reads board.cpu.cycles
        self.sound_events, self.sound_queue, self.timeline = [], [], []

    # --- time ---
    def run(self, n):
        end = self.cycles + n
        while self.powered and self.timeline and self.timeline[0][0] <= end:
            self.cycles, _, fn = self.timeline.pop(0); fn()
        self.cycles = end
        if self.powered and self.off_at and end >= self.off_at:
            self.power_off()
        q = self.sound_queue; i = 0
        while i < len(q) and q[i][0] <= end: i += 1
        self.sound_events += q[:i]; del q[:i]

    def at(self, seconds, fn):
        self.timeline.append((self.cycles + int(seconds * SEC), len(self.timeline), fn)); self.timeline.sort()

    def show(self, text, blink=None):
        self.shown, self.blink = text, (blink + (self.cycles,)) if blink else None

    def sound(self, name):
        """Queue a sound; returns its length in seconds. Keys are ignored while it plays."""
        t = self.cycles
        for lv, hi, lo, n in SOUNDS[name]:
            for _ in range(n):
                if lv: self.sound_queue.append((t, lv)); self.sound_queue.append((t + hi, 0))
                t += hi + lo
        self.busy_until = t
        return (t - self.cycles) / SEC

    # --- power, display ---
    def power_on(self):
        self.powered, self.state = True, 'setup'
        self.timeline, self.sound_queue = [], []
        self.typed, self.fresh, self.off_at = '', False, None
        self.show(BLANK)
        self.at(self.sound('power_on'), lambda: self.show(ON))

    def power_off(self):
        self.powered = False
        self.sound_queue = []

    def display(self):
        if not self.powered: return BLANK
        if self.blink:
            on, off, start = self.blink
            if (self.cycles - start) % int((on + off) * SEC) >= int(on * SEC): return BLANK
        return self.shown

    def segments(self):
        return [MASK.get(ch, 0) for ch in self.display()]

    # --- keys ---
    def set_key(self, key, down):
        if down: self.key(key)

    def key(self, k):
        if not self.powered or self.cycles < self.busy_until:
            return                        # a sound is playing: the original does not look at the keys either
        (self.key_setup if self.state == 'setup' else self.key_play)(k)

    def echo(self):
        t = self.typed.lstrip('0') or self.typed[-1:]
        self.show(digits(t, 7))

    def key_setup(self, k):
        if k.isdigit():
            self.typed = (self.typed + k)[-2:]; self.echo()
        else:
            t, self.typed = self.typed, ''
            if k == 'ENTER' and len(t) == 2 and t[0] in '123' and t[1] in '1234':
                self.level, self.left = int(t[0]), int(t[1])       # questions per turn; players still in the game
                self.start_case(t)
            else:
                self.show(ON)

    def start_case(self, typed):
        self.case = self.fixed_case or deal(self.rng)
        self.obs, self.murderer = observe(self.case)
        self.victim = self.obs['victim']
        self.over = self.deviation = False   # solved, or everybody is out; known difference from the ROM met
        self.who = None                   # the suspect whose answers are loaded (survives END TURN and the victim)
        self.new_turn()
        self.state = 'play'
        self.show(typed.ljust(7))
        self.at(0.8, lambda: self.show(BLANK))
        self.at(self.sound('crime'), lambda: self.show(digits(self.victim) + GLYPH[self.obs['scene']] + '    '))

    def new_turn(self):
        self.active = self.touched = False   # a suspect is being questioned; something was entered this turn
        self.used, self.mode, self.typed, self.fresh, self.last_ee = 0, None, '', False, False

    def key_play(self, k):
        if k in ('SUSPECT', 'PQ', 'ACCUSE'):
            if k == 'ACCUSE': self.active = self.touched = False     # as in the original: this forgets the turn's suspect
            ok = k == 'ACCUSE' or ((self.mode in ('SUSPECT', 'PQ')) if k == 'PQ' else not self.touched)   # checked at once
            self.typed, self.fresh = '', False
            if ok:
                self.mode = k; self.show(BLANK)
                if k == 'SUSPECT': self.active, self.touched = False, not self.over   # one suspect per turn
            else: self.show(EE)                                    # the previous mode stays in force
        elif k.isdigit():
            if self.fresh: self.typed, self.fresh = '', False
            self.typed = (self.typed + k)[-2:]; self.echo()
        elif k == 'ENDTURN':
            self.new_turn(); self.show(BLANK); self.sound('bong')
            if self.off_at: self.off_at = self.cycles + OFF_EXTEND * SEC
        elif k == 'ENTER':
            n = int(self.typed) if self.typed else None
            repeat, self.fresh = self.fresh, True                    # ENTER again, with nothing new typed
            if repeat: n = None
            if self.mode == 'SUSPECT': self.show(self.enter_suspect(n))
            elif self.mode == 'PQ': self.enter_question(n, repeat)
            elif self.mode == 'ACCUSE': self.enter_accuse(n)
            else: self.show(EE)

    def enter_suspect(self, n):
        if n is None or not 1 <= n <= 20 or self.active:
            return EE
        if n == self.victim:              # as in the original: the victim keeps the previous suspect's answers
            return '0000000'
        self.active, self.who = True, n
        a = self.obs['alibi'][n]
        mates = [digits(m) for m in a.get('with', ())]
        row = next(r for r in range(5) if n in self.case['rows'][r]['people'])
        if row == 4 and 'area' in a and mates:                     # place of three, second position: right-hand field
            mates = ['  '] + mates
        return str(a.get('side', ' ')) + str(a.get('area', ' ')) + GLYPH.get(a.get('place'), ' ') + ''.join(mates).ljust(4)

    def enter_question(self, q, repeat=False):
        """The order of the checks is the original's, found by comparing with the ROM."""
        limit = self.used >= self.level and not self.over           # a closed case can be reviewed without limit
        if q is not None and not 1 <= q <= 14:
            return self.answer(EE)        # no such question: costs nothing, even when the turn is used up
        if repeat:                        # ENTER again: END once the turn is used up, unless EE is showing
            return self.end() if limit and not self.last_ee else self.answer(EE)
        if q is None:                     # nothing typed after the mode key: a lost question, if one was left
            if not limit and not self.over: self.used += 1
            return self.answer(EE)
        if limit:
            return self.end()
        if not self.over: self.used += 1  # a question that is not on the card is lost as well
        if self.who is None: self.deviation = True                 # the victim first: the original answers nonsense
        a = self.obs['ans'].get((self.who, q), self.obs['hidden'].get((self.who, q)))
        self.answer(EE if a is None else '  4E5  ' if a == 'Y' else '     N0' if a == 'N' else '0000000' if a == '?'
                    else '  ' + GLYPH[a] + '    ' if a in GLYPH else ' ' + a + '     ')

    def answer(self, text):
        self.last_ee = text == EE
        self.show(text)

    def end(self):
        self.last_ee = False
        self.show(BLANK)
        self.at(self.sound('bong'), lambda: self.show(END))

    def enter_accuse(self, n):
        self.active = self.touched = False; self.mode = None      # the questions used this turn stay used
        self.show(BLANK)
        if n == self.murderer:
            self.at(self.sound('solved') + 0.2, lambda: self.show(digits(self.murderer) + '4E5  ', BLINK))
            self.off_at = self.cycles + OFF_AFTER * SEC; self.over = True
            return
        self.left = max(self.left - 1, 0)
        no = lambda: self.show('     N0')
        self.at(1.4, no); self.at(1.84, lambda: self.show(BLANK)); self.at(1.98, no)
        if self.left > 0:                 # the others play on
            self.sound('wrong')
            self.at(2.6, lambda: self.show('     N0', BLINK_NO))
        else:                             # everybody is out: the machine names the murderer
            self.over = True
            self.at(2.3, lambda: self.show(BLANK))
            self.at(self.sound('wrong_last'), lambda: self.show(digits(self.murderer) + 'd1d  ', BLINK))
