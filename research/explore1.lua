package.path = "D:/claude/GAMES/electronic_detective/research/?.lua;" .. package.path
local L = require("edlib")
local m = manager.machine
L.keys("O"); L.wait(120)
L.keys("3"); L.wait(30); L.keys("1"); L.wait(30); L.keys("E"); L.wait(60*40)
L.keys("S7E"); L.wait(600)
L.keys("Q2E"); L.wait(600)
L.keys("Q5E"); L.wait(600)
L.keys("Q12E"); L.wait(600)
L.keys("Q13E"); L.wait(600)
L.keys("T"); L.wait(300)
L.call(function()
  local f=io.open("D:/claude/GAMES/electronic_detective/research/explore1.log","w")
  for _,e in ipairs(L.events) do f:write(string.format("%8.2f %6d [%s]\n", e.t, e.frame, e.disp)) end
  f:close(); m:exit() end)
sub = emu.add_machine_frame_notifier(L.tick)
