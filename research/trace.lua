-- trace execution per phase with the headless MAME debugger
package.path = "D:/claude/GAMES/electronic_detective/research/?.lua;" .. package.path
local L = require("ed2")
local m = manager.machine
local D = "D:/claude/GAMES/electronic_detective/research/dasm/tr_"
math.randomseed(tonumber(os.getenv("ED_SEED") or "1") * 7919 + 17)
local function tr_on(name) m.debugger:command("trace " .. D .. name .. ".txt,maincpu,noloop") end
local function tr_off() m.debugger:command("trace off,maincpu") end
m.debugger:command("go")
L.run(function()
  emu.wait(1); L.press("O"); emu.wait(6)
  tr_on("idle"); emu.wait(2); tr_off()
  L.press("3"); emu.wait(0.5); L.press("1"); emu.wait(0.5)
  tr_on("setup"); L.press("E"); emu.wait(55); tr_off()
  L.rec("crime", L.read_after(0.5)); L.rec("ram0", L.ram())
  for s = 1, 3 do
    tr_on("alibi" .. s); L.keys("S" .. s .. "E"); emu.wait(1.5); tr_off()
    L.rec("alibi" .. s, L.display())
    tr_on("q13_" .. s); L.keys("Q13E"); emu.wait(1.0); tr_off()
    L.rec("q13_" .. s, L.display())
    L.press("T"); emu.wait(1)
  end
  L.finish(D .. "records.tsv")
end)
