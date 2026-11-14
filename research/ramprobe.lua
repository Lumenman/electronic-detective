local m = manager.machine
local f=io.open("D:/claude/GAMES/electronic_detective/research/ramprobe.txt","w")
for tag,dev in pairs(m.devices) do f:write("dev ",tag,"\n") end
local cpu = m.devices[":maincpu"]
for name,sp in pairs(cpu.spaces) do f:write("space ",name," width=",tostring(sp.data_width)," addr=",tostring(sp.address_mask),"\n") end
f:close(); m:exit()
