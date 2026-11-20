"""The game machine without the ROM: key entry, turns, answers, display and sounds.

It behaves like the original (compared key by key with the ROM in research/emu/diff_machine.py), but the case is
dealt by rules.deal() and the answers come from rules.observe(). Four oddities of the original are left out
unless rom_like=True (which the comparison uses): SUSPECT pressed again before ENTER shows EE; the I ACCUSE key
forgets the turn's suspect, so another one can be questioned; a rejected mode key leaves the previous mode on, so
the next number is read as something else; questions go to the previous suspect when nobody is being questioned
(the victim); suspects 11-15 answer question 12, which is not on their cards; a finished game switches itself off. It offers the same interface as board.ElecDet,
so the window can drive either. Time is counted in CPU cycles of the original (IPS per second).

    m = Machine(); m.power_on(); m.run(3 * SEC); m.key('3'); m.key('1'); m.key('ENTER'); m.run(6 * SEC); m.display()
"""
import os, random, sys
from board import IPS, SEG
from rules import deal, deal_lies, observe
from sounds import SOUNDS

GLYPH = {'A': 'A', 'B': 'b', 'C': 'C', 'D': 'd', 'E': 'E', 'F': 'F'}
MASK = {ch: m for m, ch in SEG.items() if m != 0x67}
BLANK, EE, END, ON = ' ' * 7, '     EE', '  ENd  ', '     0N'
SEC = int(IPS)
NUMBER = 7                                         # digits in the number of a case


# The games of the machine. name: (index in the seed, digit held with ON, deal(rng), the solver's function that must
# find only the murderer in a dealt case, or None, its name in the status). The index must stay: old numbers keep their cases.
VARIANTS = {
    'fair': (0, None, deal, None, 'the usual game'),
    'lies': (1, '2', deal_lies, 'lie_suspects', 'two false alibis'),
}


def number_rng(number, variant):
    """The deals of a case number. The games draw apart: the same number must not be the same murder in two of them."""
    return random.Random(number + VARIANTS[variant][0] * 10 ** NUMBER)


def deal_checked(rng, variant, check=None):
    """The first deal of rng that the solver can solve (about 1 in 25 with two false alibis cannot), and the deals
    skipped before it. check: the solver's function; by default imported, and no solver here means no check."""
    deal, name = VARIANTS[variant][2:4]
    if name and check is None:
        sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'research', 'solver'))
        try:
            check = getattr(__import__('solver'), name)    # on the phone the solver lies beside this file
        except ImportError:
            name = None                  # no solver here: the case is played unchecked
    skip = 0
    while True:
        case = deal(rng)
        if not name or len(check(observe(case)[0])) == 1: return case, skip
        skip += 1
BLINK, BLINK_NO = (0.44, 0.14), (0.26, 0.14)       # seconds on, off
OFF_AFTER, OFF_EXTEND = 240, 177                   # a finished game switches itself off; END TURN gives more time


def digits(n, width=2):
    return str(n).rjust(width).replace('6', 'b')


class Machine:
    def __init__(self, rng=None, case=None, rom_like=False, variant='fair', take=None, ask=False, number=None,
                 most=10 ** NUMBER - 1):
        self.most = most                         # the largest number taken when asked (ask=True)
        self.rng, self.fixed_case, self.rom_like = rng or random.SystemRandom(), case, rom_like
        self.variant, self.take = variant, take  # a name in VARIANTS; take(variant) gives (number, case) dealt ahead, or None
        self.ask, self.given = ask, number       # switched on only to take the number of a case; the case to play
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
        if self.powered and self.off_at and self.rom_like and end >= self.off_at:
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
        self.powered, self.state = True, 'number' if self.ask else 'setup'
        self.number = self.given          # of the case: the same number is the same case (none for a case given from outside)
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
        {'number': self.key_number, 'setup': self.key_setup}.get(self.state, self.key_play)(k)

    def echo(self):
        t = self.typed.lstrip('0') or self.typed[-1:]
        self.show(digits(t, 7))

    def key_number(self, k):
        if k.isdigit():
            self.typed = (self.typed + k)[-NUMBER:]; self.echo()
        else:
            t, self.typed = self.typed, ''
            if k == 'ENTER' and t and 0 < int(t) <= self.most:
                self.number = int(t); self.power_off()       # the window keeps it for the next game; the screen goes dark
            else: self.show(ON)

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
        ahead = VARIANTS[self.variant][3] and self.number is None and self.take and self.take(self.variant)
        if self.fixed_case:
            self.case = self.fixed_case
        elif ahead:
            self.number, self.case = ahead
        else:                             # shortcut: a checked deal is checked here - the machine waits (seconds on a phone)
            self.number = self.number or self.rng.randrange(1, 10 ** NUMBER)
            self.case = deal_checked(number_rng(self.number, self.variant), self.variant)[0]
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
            if k == 'ACCUSE' and self.rom_like: self.active = self.touched = False   # forgets the turn's suspect
            asked = self.mode in ('SUSPECT', 'PQ') if self.rom_like else self.active
            ok = k == 'ACCUSE' or (asked if k == 'PQ' else not self.touched)   # checked when the key is pressed
            self.typed, self.fresh = '', False
            if ok:
                self.mode = k; self.show(BLANK)
                if k == 'SUSPECT': self.active, self.touched = False, self.rom_like and not self.over
            else:
                self.show(EE)
                if not self.rom_like: self.mode = None             # the ROM keeps the previous mode in force
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
        self.touched = not self.over      # one suspect per turn (the ROM marks the turn already when SUSPECT is pressed)
        if n == self.victim:              # as in the original: the victim keeps the previous suspect's answers
            return '0000000'
        self.active, self.who = True, n
        a = self.obs['alibi'][n]
        mates = [digits(m) for m in a.get('with', ())]
        told = dict(self.case.get('lies', ())).get(n, n)            # a liar shows the alibi as its owner would
        row = next(r for r in range(5) if told in self.case['rows'][r]['people'])
        if row == 4 and 'area' in a and mates:                     # place of three, second position: right-hand field
            mates = ['  '] + mates
        return str(a.get('side', ' ')) + str(a.get('area', ' ')) + GLYPH.get(a.get('place'), ' ') + ''.join(mates).ljust(4)

    def enter_question(self, q, repeat=False):
        """The order of the checks is the original's, found by comparing with the ROM."""
        limit = self.used >= self.level and not self.over           # a closed case can be reviewed without limit
        if q is None and self.rom_like:   # nothing typed: the ROM reads the number from the right end of the display,
            t = self.shown[5:7].strip()   # blank after a mode key, YES, a letter or a number; no number after NO and EE
            q, repeat = (None if not t else int(t) if t.isdigit() else 0), False
        if q is not None and not 1 <= q <= 14:
            return self.answer(EE)        # no such question: costs nothing, even when the turn is used up
        if repeat:                        # ENTER again: END once the turn is used up, unless EE is showing
            return self.end() if limit and not self.last_ee else self.answer(EE)
        if limit:
            return self.end()
        if not self.over: self.used += 1  # nothing typed, or a question that is not on the card: lost as well
        if q is None:
            return self.answer(EE)
        if self.who is None: self.deviation = True                 # the victim first: the original answers nonsense
        a = self.obs['ans'].get((self.who, q), self.obs['hidden'].get((self.who, q)) if self.rom_like else None)
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
