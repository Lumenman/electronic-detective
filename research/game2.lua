package.path = "D:/claude/GAMES/electronic_detective/research/?.lua;" .. package.path
local L = require("edlib")
local m = manager.machine
local seed = tonumber(os.getenv("ED_SEED") or "0")
local CARDS = {{1,2,9},{2,3,9},{3,4,5},{4,5,9},{1,4,9},{5,6,12},{2,5,12},{3,5,12},{1,5,12},{7,8,12},
  {6,7,11},{2,6,11},{3,7,11},{1,6,11},{4,7,11},{6,8,10},{2,7,10},{1,8,10},{3,8,10},{4,8,10}}
local QW = 200
L.start_game(3, 1, 300 + seed*13)
L.record_ram("ram0")
for s=1,20 do
  local c = CARDS[s]
  L.query("alibi"..s, "S"..s.."E", QW)
  for _,q in ipairs(c) do L.query("q"..s.."_"..q, "Q"..q.."E", QW) end
  L.keys("T"); L.wait(60)
  L.query("alibi"..s.."b", "S"..s.."E", QW)
  for _,q in ipairs({13,14,13}) do L.query("q"..s.."_"..q, "Q"..q.."E", QW) end
  L.keys("T"); L.wait(60)
  L.query("alibi"..s.."c", "S"..s.."E", QW)
  for _,q in ipairs({14,13,14}) do L.query("q"..s.."_"..q, "Q"..q.."E", QW) end
  L.keys("T"); L.wait(60)
  -- off-card question and over-limit check
  local off = 1; while off==c[1] or off==c[2] or off==c[3] do off = off + 1 end
  L.query("alibi"..s.."d", "S"..s.."E", QW)
  L.query("off"..s.."_"..off, "Q"..off.."E", QW)
  L.keys("T"); L.wait(60)
end
L.record_ram("ram1")
-- accuse suspect 1, sample display afterwards
L.keys("A1E")
for k=1,40 do L.wait(45); L.call(function() L.records[#L.records+1]={label="acc"..k, disp=L.read_display()} end) end
L.call(function() L.dump(os.getenv("ED_OUT")); m:exit() end)
sub = emu.add_machine_frame_notifier(L.tick)
