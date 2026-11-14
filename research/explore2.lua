package.path = "D:/claude/GAMES/electronic_detective/research/?.lua;" .. package.path
local L = require("edlib")
local m = manager.machine
L.wait(60); L.keys("O"); L.wait(600)
L.keys("3"); L.wait(120); L.keys("1"); L.wait(120); L.keys("E"); L.wait(60*60)
L.keys("S"); L.wait(60); L.keys("7"); L.wait(60); L.keys("E"); L.wait(600)
L.call(function()
  local f=io.open("D:/claude/GAMES/electronic_detective/research/explore2.log","w")
  for _,e in ipairs(L.events) do f:write(string.format("%8.2f %6d [%s]\n", e.t, e.frame, e.disp)) end
  f:close(); m:exit() end)
sub = emu.add_machine_frame_notifier(L.tick)
