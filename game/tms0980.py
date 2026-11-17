# SPDX-License-Identifier: BSD-3-Clause
# Port of MAME code: copyright-holders Wilbert Pol, hap, Curt Coder, Aaron Giles (see LICENSE-MAME). The rest of this project is MIT (see LICENSE).
"""TMS0980 CPU core, a line-by-line port of MAME 0.289 (src/devices/cpu/tms1000:
tms1k_base.cpp, tms0970.cpp, tms0980.cpp) and its Berkeley PLA parser.

One call to step() runs one instruction (6 subcycles of MAME's execute_one, in order).
Board hooks: read_k() -> 5-bit K inputs, write_o(o), write_r(r), power_off().
"""

# microinstruction flags (tms1k_base.h)
M_15TN, M_ATN, M_AUTA, M_AUTY, M_C8, M_CIN, M_CKM, M_CKN, M_CKP, M_MTN, M_MTP, M_NATN, M_NE, M_STO, M_STSL, \
    M_YTP, M_CME, M_DMTP, M_NDMTP, M_SSE, M_SSS, M_SETR, M_RSTR, M_UNK1 = (1 << i for i in range(24))
# fixed instruction flags
F_BR, F_CALL, F_CLO, F_COMC, F_COMX, F_COMX8, F_LDP, F_LDX, F_RBIT, F_RETN, F_RSTR, F_SBIT, F_SETR, F_TDO, F_TPC, \
    F_TAX, F_TXA, F_TRA, F_TAC, F_TCA, F_TADM, F_TMA, F_OFF, F_REAC, F_SAL, F_SBL, F_SEAC, F_XDA = (1 << i for i in range(28))


class PLA:
    """MAME pla_device fed by plaparse.cpp (Berkeley format, no .phase used here)."""

    def __init__(self, text, inputs, outputs):
        self.terms = []
        for line in text.splitlines():
            line = line.split('#', 1)[0].strip()
            if not line or line.startswith('.'):
                continue
            ins, outs = line.split()
            assert len(ins) == inputs and len(outs) == outputs, line
            if '~' in ins:          # inhibited term never fires
                continue
            care = val = 0
            for i, c in enumerate(ins):     # char i <-> input bit i
                if c in '01':
                    care |= 1 << i
                    val |= (c == '1') << i
            orm = sum(1 << j for j, c in enumerate(outs) if c == '1')
            self.terms.append((care, val, orm))
        self.cache = {}

    def read(self, x):
        r = self.cache.get(x)
        if r is None:
            r = 0
            for care, val, orm in self.terms:
                if x & care == val:
                    r |= orm
            self.cache[x] = r
        return r


def rev(x, n):
    return int(format(x, f'0{n}b')[::-1], 2)


REV4 = [rev(i, 4) for i in range(16)]


def _lfsr_next(pc):
    fb = int((pc << 1 & 0x40) == (pc & 0x40))
    if pc == 0x3f:
        fb = 1
    elif pc == 0x7f:
        fb = 0
    return (pc << 1 | fb) & 0x7f


NEXT_PC = [_lfsr_next(pc) for pc in range(128)]   # speed: table instead of computing per instruction


class TMS0980:
    PC_BITS, X_BITS, O_MASK, R_MASK = 7, 4, 0xff, 0x1ff

    def __init__(self, rom_words, ipla, mpla, opla, spla, read_k, write_o, write_r, power_off=lambda v: None):
        self.rom = rom_words
        self.ipla, self.mpla, self.opla, self.spla = ipla, mpla, opla, spla
        self.read_k, self.write_o, self.write_r, self.power_off = read_k, write_o, write_r, power_off
        self.ram = [0] * 0x100  # 0x00-0x7f RAM, 0x80-0x8f DAM (mirrored by address masking)
        self._decode()
        self.reset()

    # --- decode tables (tms0980_cpu_device::device_reset) ---
    def _decode_micro(self, offset):
        offset = rev(offset, 6)                     # lines are reversed
        mask = self.mpla.read(offset) ^ 0x43fc3     # invert active-negative
        md = [M_NDMTP, M_DMTP, M_AUTY, M_AUTA, M_CKM, M_SSE, M_CKP, M_YTP, M_MTP, M_ATN, M_NATN, M_MTN, M_15TN,
              M_CKN, M_NE, M_C8, M_SSS, M_CME, M_CIN, M_STO, M_RSTR, M_UNK1]
        d = 0
        for bit in range(20):                       # mpla has 20 outputs
            if mask & (1 << bit):
                d |= md[bit]
        return d

    def _decode_fixed(self, op):
        mask = self.ipla.read(op)
        ids = [F_LDP, F_SBL, F_OFF, F_RBIT, F_SAL, F_XDA, F_REAC, F_SETR, F_RETN, F_SBIT, F_TDO, F_COMX8, F_COMX,
               F_LDX, F_SEAC]
        d = 0
        for bit in range(15):
            if mask & (0x80 << bit):
                d |= ids[bit]
        return d

    def _decode(self):
        self.fixed_decode = [0] * 0x200
        self.micro_decode = [0] * 0x200
        for op in range(0x200):
            if op & 0x100:
                self.fixed_decode[op] = F_CALL if op & 0x80 else F_BR
            self.micro_decode[op] = self._decode_micro(self.ipla.read(op) & 0x3f)
            self.fixed_decode[op] |= self._decode_fixed(op)
        for op in range(0x40):          # MAME clears these (they always go through micro_direct)
            self.micro_decode[op] = 0
        self.micro_direct = [self._decode_micro(op) for op in range(0x40)]

    def reset(self):
        self.pa = self.pb = 0xf
        self.pc = self.ca = self.cb = self.cs = 0
        self.sr = 0
        self.eac = self.bl = self.add = self.status = self.clatch = 0
        self.opcode = self.micro = self.fixed = 0
        self.a = self.x = self.y = 0
        self.r = self.o = 0
        self.cki = self.c4 = 0
        self.status_latch = self.carry_out = 0
        self.adder_out = 0
        self.ram_address = 0
        self.rom_address = 0
        self.cycles = 0          # instructions executed
        self.r = 0
        self.write_r(0)
        self._write_o_reg(0)
        self.write_r(0)
        self.power_off(0)

    # --- memory ---
    def _rd(self, addr):
        return self.ram[addr if addr < 0x80 else 0x80 | (addr & 0xf)] & 0xf

    def _wr(self, addr, v):
        self.ram[addr if addr < 0x80 else 0x80 | (addr & 0xf)] = v & 0xf

    # --- helpers ---
    def _write_o_reg(self, index):          # tms0970 override: segment PLA
        self.o = self.spla.read(index)
        self.write_o(self.o & self.O_MASK)

    def _next_pc(self):
        self.pc = NEXT_PC[self.pc]

    def _read_opcode(self):
        op = self.rom[self.rom_address] & 0x1ff
        self.opcode = op
        self.c4 = REV4[op & 0xf]
        self.fixed = self.fixed_decode[op]
        r0 = op >> 8 & 1
        if self.ipla.read(op) & 0x40 and not ((r0 & self.bl) ^ r0):
            self.micro = self.micro_direct[op & 0x3f]
        else:
            self.micro = self.micro_decode[op]
        if self.micro & M_RSTR:
            self.fixed |= F_RSTR
        if self.micro & M_SETR:
            self.fixed |= F_SETR
        self._next_pc()

    def _set_cki_bus(self):
        g = self.opcode & 0x1f8
        if g == 0x008:
            k = self.read_k() & 0x1f
            self.cki = (k & 0xf) | (3 if k & 0x10 else 0)
        elif g in (0x020, 0x0a0):
            self.cki = (1 << (self.c4 >> 2)) ^ 0xf
        elif 0x040 <= g <= 0x078 or 0x0c0 <= g <= 0x0f8:
            self.cki = self.c4
        else:
            self.cki = 0

    # --- one instruction = subcycles 0..5 ---
    def step(self):
        f, m = self.fixed, self.micro
        # subcycle 0: br/call/retn (stack_levels == 1 variants), read ram, cki
        if f & F_BR and self.status:
            if self.clatch == 0:
                self.pa = self.pb
            self.ca = self.cb
            self.pc = self.opcode & 0x7f
        if f & F_CALL and self.status:
            prev_pa = self.pa
            if not self.clatch:
                self.clatch = 1
                self.sr = self.pc
                self.pa = self.pb
                self.cs = self.ca
            self.ca = self.cb
            self.pb = prev_pa
            self.pc = self.opcode & 0x7f
        if f & F_RETN:
            if self.clatch:
                self.clatch = 0
                self.pc = self.sr
                self.ca = self.cs
            self.add = 0
            self.bl = 0
            self.pa = self.pb
        self._set_cki_bus()
        ram_in = self._rd(self.ram_address)
        dam_in = self._rd(self.ram_address | 0x80)
        p = n = cin = 0
        # subcycle 1: rom address, alu inputs
        self.rom_address = (self.ca << 11) | (self.pa << 7) | self.pc
        if m & M_15TN: n |= 0xf
        if m & M_ATN: n |= self.a
        if m & M_NATN: n |= ~self.a & 0xf
        if m & M_CKN: n |= self.cki
        if m & M_MTN: n |= ram_in
        if m & M_CKP: p |= self.cki
        if m & M_MTP: p |= ram_in
        if m & M_YTP: p |= self.y
        if m & M_DMTP: p |= dam_in
        if m & M_NDMTP: p |= ~dam_in & 0xf
        if m & M_CIN: cin |= 1
        if m & M_SSS: cin |= self.eac
        # subcycle 2: alu, fixed ops, write ram
        self.adder_out = p + n + cin
        carry_out = self.adder_out >> 4 & 1
        status = 1
        ram_out = -1
        if m & M_C8: status &= carry_out
        if m & M_NE: status &= int(n != p)
        if m & M_CKM: ram_out = self.cki
        if m & M_SSE:
            self.eac = self.carry_out
            if self.add:
                self.eac |= carry_out
        self.carry_out = carry_out
        if m & M_STO or (m & M_CME and self.eac == self.add):
            ram_out = self.a
        if f & F_SBIT:
            if ram_out == -1: ram_out = ram_in
            ram_out |= self.cki ^ 0xf
        if f & F_RBIT:
            if ram_out == -1: ram_out = ram_in
            ram_out &= self.cki
        if f & F_SETR:      # tms0970 override: DDIG
            ddig = 0 if (~self.opla.read(self.a) & self.o) else 1
            self.r = (self.r & ~(1 << self.y)) | (ddig << self.y)
        if f & F_RSTR:
            self.r &= ~(1 << self.y)
            self.write_r(self.r & self.R_MASK)
        if f & F_TDO:       # tms0970 override
            self._write_o_reg(self.a & 7)
            self.write_r(self.r & self.R_MASK)
        if f & F_CLO:
            self._write_o_reg(0)
        if f & F_LDX: self.x = self.c4 >> (4 - self.X_BITS)
        if f & F_COMX: self.x ^= 0xf >> 1          # tms0980: not the MSB
        if f & F_COMX8: self.x ^= 1 << (self.X_BITS - 1)
        if f & F_LDP: self.pb = self.c4
        if f & F_OFF: self.power_off(1)
        if f & F_SEAC: self.eac = 1
        if f & F_REAC: self.eac = 0
        if f & F_SAL: self.add = 1
        if f & F_SBL: self.bl = 1
        if f & F_XDA: self.ram_address |= 0x80
        self.status = status
        if ram_out != -1:
            self._wr(self.ram_address, ram_out)
        # subcycle 4: register store, fetch next
        if m & M_AUTA: self.a = self.adder_out & 0xf
        if m & M_AUTY: self.y = self.adder_out & 0xf
        if m & M_STSL: self.status_latch = self.status
        self._read_opcode()
        self.ram_address = self.x << 4 | self.y
        self.cycles += 1
