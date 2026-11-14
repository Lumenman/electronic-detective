package.path = "D:/claude/GAMES/electronic_detective/research/?.lua;" .. package.path
local L = require("ed2")
math.randomseed(tonumber(os.getenv("ED_SEED") or "0") * 7919 + 17)
local CARDS = {{1,2,9},{2,3,9},{3,4,5},{4,5,9},{1,4,9},{5,6,12},{2,5,12},{3,5,12},{1,5,12},{7,8,12},
  {6,7,11},{2,6,11},{3,7,11},{1,6,11},{4,7,11},{6,8,10},{2,7,10},{1,8,10},{3,8,10},{4,8,10}}
L.run(function()
  L.start(3, 1)
  for s = 1, 20 do
    local c = CARDS[s]
    L.query("alibi" .. s, "S" .. s .. "E", 1.5)
    for _, q in ipairs(c) do L.query("q" .. s .. "_" .. q, "Q" .. q .. "E", 1.0) end
    L.press("T"); emu.wait(1)
    L.query("alibi" .. s .. "b", "S" .. s .. "E", 1.5)
    L.query("q" .. s .. "_13", "Q13E", 1.0)
    L.query("q" .. s .. "_14", "Q14E", 1.0)
    local off = 1; while off == c[1] or off == c[2] or off == c[3] do off = off + 1 end
    L.query("off" .. s .. "_" .. off, "Q" .. off .. "E", 1.0)
    L.press("T"); emu.wait(1)
  end
  L.rec("ram1", L.ram())
  L.keys("A1E")
  for k = 1, 30 do emu.wait(0.37); L.rec("acc" .. k, L.display()) end
  L.finish(os.getenv("ED_OUT"))
end)
