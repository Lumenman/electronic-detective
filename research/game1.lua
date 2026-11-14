package.path = "D:/claude/GAMES/electronic_detective/research/?.lua;" .. package.path
local L = require("edlib")
local m = manager.machine
local seed = tonumber(os.getenv("ED_SEED") or "0")
L.start_game(3, 1, 300 + seed*13)
L.record_ram("ram0")
for s=1,20 do L.query("alibi"..s, "S"..s.."E", 200); L.keys("T"); L.wait(90) end
L.record_ram("ram1")
L.call(function() L.dump(os.getenv("ED_OUT")); m:exit() end)
sub = emu.add_machine_frame_notifier(L.tick)
