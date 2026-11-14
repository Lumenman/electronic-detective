-- ed2: coroutine-based driver with sub-frame random timing (emu.wait)
local M = {}
local m = manager.machine
local KEYS = {}
for _, port in pairs(m.ioport.ports) do
  for name, field in pairs(port.fields) do KEYS[name] = field end
end
local SEG = {[0x3f]="0",[0x06]="1",[0x5b]="2",[0x4f]="3",[0x66]="4",[0x6d]="5",[0x7d]="6",[0x07]="7",
  [0x7f]="8",[0x6f]="9",[0x67]="9",[0x77]="A",[0x7c]="b",[0x39]="C",[0x5e]="d",[0x79]="E",[0x71]="F",
  [0x54]="n",[0x5c]="o",[0x00]=" ",[0x37]="N",[0x40]="-"}
local MAP = {S="Suspect",Q="Private Question",A="I Accuse",E="Enter",T="End Turn",O="Power On"}

function M.display()
  local s = ""
  for i = 6, 0, -1 do
    local v = m.output:get_value("digit" .. i) & 0x7f
    s = s .. (SEG[v] or string.format("{%02x}", v))
  end
  return s
end
function M.ram()
  local sp = m.devices[":maincpu"].spaces["data"]
  local t = {}
  for a = 0, 127 do t[#t + 1] = string.format("%x", sp:read_u8(a) & 0xf) end
  return table.concat(t)
end
-- random duration in seconds, not aligned to frames
local function jit(lo, hi) return lo + (hi - lo) * math.random() end
function M.press(name)
  local f = KEYS[MAP[name] or name]
  f:set_value(1); emu.wait(jit(0.20, 0.35)); f:clear_value(); emu.wait(jit(0.25, 0.45))
end
function M.keys(str) for c in str:gmatch(".") do M.press(c) end end
-- wait, then sample display for a while and return most common non-blank reading
function M.read_after(sec)
  emu.wait(sec)
  local cnt, best, bn = {}, "       ", 0
  for i = 1, 12 do
    local d = M.display()
    if d:match("%S") then cnt[d] = (cnt[d] or 0) + 1; if cnt[d] > bn then best, bn = d, cnt[d] end end
    emu.wait(0.05)
  end
  return best
end
M.records = {}
function M.rec(label, val) M.records[#M.records + 1] = label .. "\t" .. val end
function M.start(diff, players)
  emu.wait(jit(0.5, 1.5)); M.press("O"); emu.wait(jit(3, 12))
  M.press(tostring(diff)); emu.wait(jit(0.2, 2)); M.press(tostring(players)); emu.wait(jit(0.2, 2))
  M.press("E")
  emu.wait(55)
  M.rec("crime", M.read_after(1)); M.rec("ram0", M.ram())
end
function M.query(label, keystr, sec)
  M.keys(keystr); M.rec(label, M.read_after(sec or 2.5))
end
function M.finish(path)
  local f = io.open(path, "w"); f:write(table.concat(M.records, "\n"), "\n"); f:close()
  m:exit()
end
function M.run(fn)
  local co = coroutine.create(fn)
  local ok, err = coroutine.resume(co)
  if not ok then local f = io.open(os.getenv("ED_OUT") .. ".err", "w"); f:write(tostring(err)); f:close(); m:exit() end
end
return M
