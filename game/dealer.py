"""'Classic without patterns': the original ROM, but the shell deals the cards.

The ROM has no random generator: its table only rotates, which leaves regularities a player can exploit.
Here the shell overwrites the table in RAM just before the ROM builds the case (while the gunshots play), and
sets the murder-weapon flag just after. Everything else - alibis, answers, sounds - is still the ROM.
Full-case check of this code: research/emu/fair.py.
"""
import random

ADDR = [1, 2, 3, 5, 6, 7]                 # side: bit 2 = East; area: low bits 1/2/3
LETTER = [10, 6, 12, 13, 14, 15]          # A b C d E F


def pre(ram, rng):
    for col in range(4):                  # who is where: any order, not just a rotation
        v = [ram[r * 16 + col] for r in range(5)]; rng.shuffle(v)
        for r in range(5): ram[r * 16 + col] = v[r]
    for col, vals in ((4, ADDR), (5, LETTER)):
        v = vals[:]; rng.shuffle(v)
        for r in range(6): ram[r * 16 + col] = v[r]
    t = [1, 2, 3, 4, 5]; rng.shuffle(t)   # alibi templates, no longer tied to the odd woman
    for r, x in zip((0, 1, 2, 3, 5), t): ram[r * 16 + 6] = x
    ram[4 * 16 + 6] = 6
    ram[4 * 16 + 13] = rng.randrange(16)  # murderer / victim categories, instead of the ENTER hold time


def post(ram, rng):
    ram[1 * 16 + 9] = ram[1 * 16 + 9] & ~2 | rng.choice((0, 2))   # bit 1: the .38 is the murder weapon


class Dealer:
    """Call tick(cpu) between emulation steps (any period up to ~0.1 s)."""

    def __init__(self, rng=None):
        self.rng, self.dealt, self.wait = rng or random.SystemRandom(), False, 0

    def tick(self, cpu):
        ram = cpu.ram
        if not ram[3 * 16 + 12] & 1:
            self.wait = 0
            if cpu.rom_address >> 7 == 13:
                pre(ram, self.rng); self.dealt = True
        elif self.dealt:
            self.wait += 1
            if self.wait == 2:            # one tick later: the ROM has finished building the case
                post(ram, self.rng); self.dealt = False
