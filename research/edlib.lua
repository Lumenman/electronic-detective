-- edlib: tiny driver for Electronic Detective under MAME Lua
local M = {}
local m = manager.machine
local KEYS = {}
for tag,port in pairs(m.ioport.ports) do
  for name,field in pairs(port.fields) do KEYS[name]=field end
end
M.KEYS = KEYS
local SEG = {[0x3f]="0",[0x06]="1",[0x5b]="2",[0x4f]="3",[0x66]="4",[0x6d]="5",
  [0x7d]="6",[0x07]="7",[0x7f]="8",[0x6f]="9",[0x67]="9",[0x77]="A",[0x7c]="b",
  [0x39]="C",[0x5e]="d",[0x79]="E",[0x71]="F",[0x54]="n",[0x5c]="o",[0x00]=" ",
  [0x40]="-",[0x38]="L",[0x76]="H",[0x58]="c",[0x50]="r",[0x30]="I",[0x3e]="U",[0x73]="P",[0x37]="N",[0x6e]="y",[0x1c]="u",[0x78]="t",[0x7d]="6"}
function M.read_display()
  local s, raw = "", {}
  for i=6,0,-1 do
    local v = m.output:get_value("digit"..i) & 0x7f
    raw[#raw+1]=string.format("%02x",v)
    s = s .. (SEG[v] or ("{"..string.format("%02x",v).."}"))
  end
  return s, table.concat(raw,",")
end
-- action queue
local q, cur, held = {}, nil, nil
local frame = 0
local last_disp, stable_disp, stable_cnt = nil, nil, 0
M.events = {}         -- list of {t=, frame=, disp=} stable display changes
M.on_idle = nil       -- called when queue empty
function M.push(a) q[#q+1]=a end
M.hold=10; M.gap=10
function M.press(name, hold, gap) M.push({key=name, hold=hold or M.hold}); M.push({wait=gap or M.gap}) end
function M.wait(n) M.push({wait=n}) end
function M.call(fn) M.push({fn=fn}) end
function M.keys(str) -- e.g. "S07E" via mapping
  for c in str:gmatch(".") do
    local map={S="Suspect",Q="Private Question",A="I Accuse",E="Enter",T="End Turn",O="Power On",X="Power Off"}
    M.press(map[c] or c)
  end
end
M.stable_frames = 6
function M.tick()
  frame = frame + 1
  local d, raw = M.read_display(); d = d .. " " .. raw
  if d == last_disp then stable_cnt = stable_cnt + 1 else stable_cnt = 0; last_disp = d end
  if stable_cnt == M.stable_frames and d ~= stable_disp then
    stable_disp = d
    M.events[#M.events+1] = {t=m.time:as_double(), frame=frame, disp=d}
  end
  if cur == nil then
    if #q == 0 then if M.on_idle then M.on_idle() end; if #q==0 then return end end
    cur = table.remove(q,1); cur.n = 0
    if cur.key then KEYS[cur.key]:set_value(1) end
  end
  cur.n = cur.n + 1
  if cur.key and cur.n >= cur.hold then KEYS[cur.key]:clear_value(); cur=nil
  elseif cur and cur.wait and cur.n >= cur.wait then cur=nil
  elseif cur and cur.fn then local f=cur.fn; cur=nil; f() end
end
function M.frame() return frame end
function M.stable() return stable_disp end

M.records = {}
-- run key string, wait n frames, record stable display under label
function M.query(label, keystr, n)
  M.keys(keystr); M.wait(n or 240)
  M.call(function() M.records[#M.records+1] = {label=label, disp=M.stable(), cur=M.read_display()} end)
end
function M.start_game(diff, players, prewait)
  M.wait(60); M.keys("O"); M.wait(prewait or 600)
  M.keys(tostring(diff)); M.wait(60); M.keys(tostring(players)); M.wait(60)
  M.keys("E"); M.wait(60*60)
  M.call(function() M.records[#M.records+1] = {label="crime", disp=M.stable()} end)
end
function M.dump(path)
  local f=io.open(path,"w")
  for _,r in ipairs(M.records) do f:write(r.label,"\t",r.disp or "","\n") end
  f:close()
end

function M.ram()
  local sp = m.devices[":maincpu"].spaces["data"]
  local t = {}
  for a=0,127 do t[#t+1] = string.format("%x", sp:read_u8(a) & 0xf) end
  return table.concat(t)
end
function M.record_ram(label)
  M.call(function() M.records[#M.records+1] = {label=label, disp=M.ram()} end)
end
return M
