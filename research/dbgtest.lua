local m = manager.machine
local f=io.open("D:/claude/GAMES/electronic_detective/research/dbgtest.txt","w")
f:write("debugger: ", tostring(m.debugger), "\n")
local cpu = m.devices[":maincpu"]
f:write("cpu.debug: ", tostring(cpu.debug), "\n")
f:close(); m:exit()
