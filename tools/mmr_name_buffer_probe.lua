-- MMR name buffer write probe v1
-- READ-ONLY observation. Does not modify RAM/ROM.
-- External corroboration candidates:
-- Hunter name: 7E:8000..8004
-- Tank #1 name: 7E:8300..8305
-- These addresses must be confirmed by original-JP runtime before promotion.

local function hx(v,w)
  return string.format("%0"..w.."X", v or 0)
end

local ranges = {
  {name="HUNTER_NAME_CANDIDATE", s=0x7E8000, e=0x7E8004},
  {name="TANK1_NAME_CANDIDATE",  s=0x7E8300, e=0x7E8305},
}

local function cpuState()
  local ok,s=pcall(function() return emu.getState() end)
  if ok and s then return s end
  return {}
end

for _,r in ipairs(ranges) do
  emu.addMemoryCallback(function(addr,val)
    local s=cpuState()
    local pc=s.pc or s.PC or 0
    local a=s.a or s.A or 0
    local x=s.x or s.X or 0
    local y=s.y or s.Y or 0
    emu.log(string.format(
      "MMR_NAMEBUF WRITE kind=%s addr=%s value=%s pc=%s A=%s X=%s Y=%s",
      r.name,hx(addr,6),hx(val,2),hx(pc,6),hx(a,4),hx(x,4),hx(y,4)
    ))
  end, emu.callbackType.write, r.s, r.e, emu.cpuType.snes, emu.memType.snesMemory)
end

emu.log("MMR_NAMEBUF_READY hunter=7E8000-7E8004 tank1=7E8300-7E8305 READ_ONLY")
