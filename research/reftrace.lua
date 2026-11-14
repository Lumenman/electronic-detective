local m = manager.machine
local D = "D:/claude/GAMES/electronic_detective/research/emu/ref/"
m.debugger:command("trace " .. D .. "reset.txt,maincpu,,{tracelog \"%X %X %X | \",a,x,y}")
m.debugger:command("go")
local co = coroutine.create(function()
  emu.wait(3)
  m.debugger:command("trace off,maincpu")
  m:exit()
end)
coroutine.resume(co)
