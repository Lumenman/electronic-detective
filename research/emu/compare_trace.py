"""Compare the emulator against a MAME debugger trace (format: 'A X Y | P:PC: mnemonic').
MAME collapses loops as '(loops for N instructions)': N executed instructions were not printed."""
import re, sys
from elecdet import ElecDet, ROM



def mame_entries(path):
    for line in open(path):
        m = re.match(r'([0-9A-F]) ([0-9A-F]) ([0-9A-F]) \| ([0-9A-F]):([0-9A-F]{2}):', line)
        if m:
            a, x, y, p, pc = (int(g, 16) for g in m.groups())
            yield ('ins', (p << 7 | pc, a, x, y))
        else:
            m = re.search(r'loops for (\d+) instructions', line)
            if m:
                yield ('skip', int(m.group(1)))


def compare(path, ed=None, limit=None):
    ed = ed or ElecDet(ROM)
    cpu = ed.cpu
    ed.power_on()
    cpu.step()          # first step only fetches the first opcode (MAME logs at fetch)
    n = 0
    for kind, v in mame_entries(path):
        if kind == 'skip':
            ed.run(v)
            continue
        mine = (cpu.rom_address, cpu.a, cpu.x, cpu.y)
        if mine != v:
            f = lambda t: '%X:%02X A=%X X=%X Y=%X' % (t[0] >> 7, t[0] & 0x7f, t[1], t[2], t[3])
            print(f'MISMATCH at entry {n} (cycle {cpu.cycles}): mame {f(v)}  emu {f(mine)}')
            return False
        cpu.step()
        n += 1
        if limit and n >= limit:
            break
    print(f'OK: {n} printed instructions matched, {cpu.cycles} executed')
    return True


if __name__ == '__main__':
    compare(sys.argv[1])
