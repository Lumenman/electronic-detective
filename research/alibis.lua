package.path = "D:/claude/GAMES/electronic_detective/research/?.lua;" .. package.path
local L = require("edlib")
local m = manager.machine
local seed = tonumber(os.getenv("ED_SEED") or "0")
local out = os.getenv("ED_OUT")
L.start_game(3, 1, 300 + seed*7)
for rep=1,2 do
  for s=1,20 do
    L.query("alibi"..s, "S"..s.."E", 240)
    L.keys("T"); L.wait(120)
  end
end
L.call(function() L.dump(out); m:exit() end)
sub = emu.add_machine_frame_notifier(L.tick)
