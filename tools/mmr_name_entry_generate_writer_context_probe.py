#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate a bounded read-only context probe for an MMR name-entry writer PC.

Consumes MMR_NAME_ENTRY_WRITE_PC_PARSE_V1 and selects the strongest recurrent
writer PC. Generated Lua logs CPU state plus bounded code/stack/DP context.
No ROM/RAM writes.
"""
from __future__ import annotations
import argparse,json
from pathlib import Path

def load(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))

def main():
 ap=argparse.ArgumentParser()
 ap.add_argument('report',type=Path)
 ap.add_argument('-o','--out',type=Path,required=True)
 a=ap.parse_args();r=load(a.report)
 if r.get('classification')!='NAME_ENTRY_WRITE_PC_CANDIDATES':
  raise SystemExit('FAIL CLOSED: writer report not ready')
 c=[x for x in (r.get('top_candidates') or [])
    if int(x.get('independent_logs',0))>=3 and x.get('pc') not in (None,'NA')]
 if not c:raise SystemExit('FAIL CLOSED: no recurrent writer PC')
 best=c[0];pc=int(best['pc'],16)
 lua=f'''-- MMR name-entry writer context probe
-- READ ONLY. writer=0x{pc:06X}
local TARGET=0x{pc:06X}
local hits=0
local function hx(v,w) if v==nil then return "NA" end return string.format("%0"..tostring(w).."X",v) end
local function r8(a)
 local ok,v=pcall(function() return emu.read(a&0xFFFFFF,emu.memType.snesDebug) end)
 return ok and v or nil
end
local function dump(a,n)
 if a==nil then return "NA" end
 local t={{}}
 for i=0,n-1 do t[#t+1]=hx(r8((a+i)&0xFFFFFF),2) end
 return table.concat(t," ")
end
local function find(t,k,d)
 if type(t)~="table" or d>5 then return nil end
 for kk,v in pairs(t) do
  if type(kk)=="string" and string.lower(kk)==k and type(v)=="number" then return v end
 end
 for _,v in pairs(t) do
  if type(v)=="table" then local q=find(v,k,d+1);if q~=nil then return q end end
 end
 return nil
end
local function st()
 local ok,s=pcall(function() return emu.getState() end)
 if not ok or type(s)~="table" then return {{}} end
 local o={{}}
 for _,k in ipairs({{"pc","a","x","y","s","d","db","p","e"}}) do o[k]=find(s,k,0) end
 return o
end
local function hit(addr,val)
 hits=hits+1
 local s=st()
 local sp=s.s
 local nativeStack=sp and (sp&0xFFFF) or nil
 local emuStack=sp and (0x0100|(sp&0xFF)) or nil
 local dp=s.d and (s.d&0xFFFF) or nil
 emu.log(string.format(
  "MMRNECTX HIT n=%d pc=%s A=%s X=%s Y=%s S=%s D=%s DB=%s P=%s E=%s",
  hits,hx(addr&0xFFFFFF,6),hx(s.a,4),hx(s.x,4),hx(s.y,4),hx(s.s,4),hx(s.d,4),
  hx(s.db,2),hx(s.p,2),hx(s.e,1)))
 emu.log("MMRNECTX CODE "..dump((TARGET-16)&0xFFFFFF,48))
 emu.log("MMRNECTX STACK_NATIVE "..dump(nativeStack,32))
 emu.log("MMRNECTX STACK_EMU "..dump(emuStack,32))
 emu.log("MMRNECTX DP "..dump(dp,32))
end
local mem=emu.memType.snesMemory or emu.memType.snesDebug
local ok,ref=pcall(function()
 return emu.addMemoryCallback(hit,emu.callbackType.exec,TARGET,TARGET,emu.cpuType.snes,mem)
end)
if ok then
 emu.log("MMRNECTX READY target=0x"..hx(TARGET,6))
else
 emu.log("MMRNECTX API_FAIL target=0x"..hx(TARGET,6))
end
'''
 a.out.write_text(lua,encoding='utf-8')
 print(json.dumps({'schema':'MMR_NAME_ENTRY_WRITER_CONTEXT_GEN_V1',
                   'classification':'WRITER_CONTEXT_PROBE_READY',
                   'writer_pc':f'{pc:06X}','field':best.get('field'),
                   'independent_logs':best.get('independent_logs'),
                   'total_hits':best.get('total_hits'),
                   'rom_ram_write_performed':False},indent=2))
if __name__=='__main__':main()
