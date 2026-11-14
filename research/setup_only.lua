package.path = "D:/claude/GAMES/electronic_detective/research/?.lua;" .. package.path
local L = require("ed2")
math.randomseed(tonumber(os.getenv("ED_SEED") or "0") * 7919 + 17)
L.run(function()
  L.start(3, 1)
  L.finish(os.getenv("ED_OUT"))
end)
