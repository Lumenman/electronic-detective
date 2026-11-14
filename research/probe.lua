-- probe: list ports/fields and output names, then exit
local m = manager.machine
local f = io.open("probe_out.txt","w")
for tag,port in pairs(m.ioport.ports) do
  for name,field in pairs(port.fields) do f:write(tag," | ",name,"\n") end
end
f:close()
local n=0
sub = emu.add_machine_frame_notifier(function()
  n=n+1
  if n==5 then
    local g=io.open("probe_out.txt","a")
    for i=0,8 do g:write("digit",i,"=",tostring(m.output:get_value("digit"..i)),"\n") end
    g:close()
    m:exit()
  end
end)
