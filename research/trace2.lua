package.path = "D:/claude/GAMES/electronic_detective/research/?.lua;" .. package.path
local L = require("ed2")
local m = manager.machine
local D = "D:/claude/GAMES/electronic_detective/research/dasm/"
math.randomseed(tonumber(os.getenv("ED_SEED") or "1") * 7919 + 17)
m.debugger:command("go")
L.run(function()
  emu.wait(1); L.press("O"); emu.wait(6)
  L.press("3"); emu.wait(0.5); L.press("1"); emu.wait(0.5)
  local f = io.open(D .. "pre_ram.txt", "w")
  -- dump full 144-nibble RAM just before ENTER
  local sp = m.devices[":maincpu"].spaces["data"]
  local t = {} for a = 0, 0x8f do t[#t+1] = string.format("%x", sp:read_u8(a) & 0xf) end
  f:write(table.concat(t), "\n"); f:close()
  m.debugger:command("trace " .. D .. "tr_setup_regs.txt,maincpu,noloop,{tracelog \"A=%X X=%X Y=%X | \",a,x,y}")
  L.press("E"); emu.wait(3)
  m.debugger:command("trace off,maincpu")
  emu.wait(52)
  L.rec("crime", L.read_after(0.5))
  local t2 = {} for a = 0, 0x8f do t2[#t2+1] = string.format("%x", sp:read_u8(a) & 0xf) end
  L.rec("ram_full", table.concat(t2))
  L.finish(D .. "trace2_records.tsv")
end)
