local m = manager.machine
local D = "D:/claude/GAMES/electronic_detective/research/emu/"
local KEYS = {}
for _, port in pairs(m.ioport.ports) do for name, f in pairs(port.fields) do KEYS[name] = f end end
local MAP = {SUSPECT="Suspect", PQ="Private Question", ENTER="Enter", ACCUSE="I Accuse", ENDTURN="End Turn"}
-- tiny JSON-ish parse of schedule.json
local s = io.open(D .. "schedule.json"):read("a")
local ev = {}
for idx, key, down in s:gmatch('%[(%d+),"([%w]+)",(%d)%]') do ev[#ev+1] = {tonumber(idx), key, tonumber(down)} end
m.debugger:command("trace " .. D .. "ref/keys.txt,maincpu,,{tracelog \"%X %X %X | \",a,x,y}")
m.debugger:command("go")
local co = coroutine.create(function()
  local t0 = m.time:as_double()
  for _, e in ipairs(ev) do
    local target = e[1] * 6 / 450000
    emu.wait(target - (m.time:as_double() - t0))
    local f = KEYS[MAP[e[2]] or e[2]]
    if e[3] == 1 then f:set_value(1) else f:clear_value() end
  end
  emu.wait(2)
  m.debugger:command("trace off,maincpu")
  m:exit()
end)
coroutine.resume(co)
