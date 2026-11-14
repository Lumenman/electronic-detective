"""TMS0980 disassembler for mp6100a (Electronic Detective).
Tables are parsed from MAME's tms1k_dasm.cpp (mame0289) so mnemonics match the MAME debugger.
Output: one listing per 128-word page, in execution (LFSR) order, with labels for branch/call targets.
Usage: python tms0980_dasm.py ROM tms1k_dasm.cpp > listing.txt"""
import re, sys

rom_path, src_path = sys.argv[1], sys.argv[2]
src = open(src_path).read()

def c_array(name):
    body = re.search(name + r'\[[^\]]*\]\s*=\s*\{(.*?)\};', src, re.S).group(1)
    body = re.sub(r'//[^\n]*', '', body)
    return [t.strip() for t in body.split(',') if t.strip()]

enum = re.search(r'enum tms1000_base_disassembler::e_mnemonics : unsigned\s*\{(.*?)\};', src, re.S).group(1)
enum = [t.strip().split('=')[0].strip() for t in re.sub(r'//[^\n]*', '', enum).split(',') if t.strip()]
idx = {n: i for i, n in enumerate(enum)}
names = [s.strip('"') for s in c_array(r'const char \*const tms1000_base_disassembler::s_mnemonic')]
bits = [int(x) for x in c_array(r'const u8 tms1000_base_disassembler::s_bits')]
lut = [idx[x] if x != '0' else 0 for x in c_array(r'const u8 tms0980_disassembler::tms0980_mnemonic')]
assert len(lut) == 512 and len(names) == len(bits) == len(enum)

I2 = [0, 2, 1, 3]; I3 = [0, 4, 2, 6, 1, 5, 3, 7]
I4 = [0x0, 0x8, 0x4, 0xc, 0x2, 0xa, 0x6, 0xe, 0x1, 0x9, 0x5, 0xd, 0x3, 0xb, 0x7, 0xf]

# LFSR order of the 7-bit PC (copy of tms1000_base_disassembler ctor)
order = []; pc = 0
for _ in range(128):
    order.append(pc)
    high = 1 << 6; fb = int((pc << 1 & high) == (pc & high))
    if pc == 0x3f: fb = 1
    elif pc == 0x7f: fb = 0
    pc = (pc << 1 | fb) & 0x7f
assert sorted(order) == list(range(128))

d = open(rom_path, 'rb').read()
words = [((d[i] << 8) | d[i + 1]) & 0x1ff for i in range(0, len(d), 2)]

def fmt(op):
    ins = lut[op]; n = names[ins]
    if n in ('AC0AC', 'AC1AC'):
        return 'A%dACC' % ((I4[op & 0xf] + (n == 'AC1AC')) & 0xf), None
    b = bits[ins]
    if b == 2: return f'{n:<7} {I2[op & 3]}', None
    if b == 3: return f'{n:<7} {I3[op & 7]}', None
    if b == 4: return f'{n:<7} {I4[op & 0xf]}', None
    if b == 6: return f'{n:<7}', op & 0x7f
    return n, None

# pass 1: track LDP (page buffer) within straight-line code to resolve branch pages
labels = {}
listing = []
for page in range(16):
    pb = page   # assumption: page buffer == current page unless LDP seen
    for pc in order:
        a = page * 128 + pc; op = words[a]
        text, tgt = fmt(op)
        if text.startswith('LDP'): pb = I4[op & 0xf]
        dest = None
        if tgt is not None:
            dest = pb * 128 + tgt
            labels.setdefault(dest, f'L{dest:03X}')
            if text.startswith('BRANCH') or text.startswith('CALL'): pb = page
        listing.append((a, page, pc, op, text, dest))

out = []
for a, page, pc, op, text, dest in listing:
    if pc == 0: out.append(f'\n; ===== page {page:X} =====')
    lab = labels.get(a, '')
    if lab: out.append(f'{lab}:')
    arg = f' {labels[dest]}  ; -> {dest >> 7:X}:{dest & 0x7f:02X}' if dest is not None else ''
    out.append(f'  {page:X}:{pc:02X}  {op:03X}  {text}{arg}')
print('\n'.join(out))
