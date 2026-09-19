#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate a read-only Mesen write-PC probe from MMR name-entry WRAM diff.

Input must be MMR_NAME_ENTRY_WRAM_DIFF_V1 with strong candidates.
The generated Lua registers WRITE callbacks only on selected candidate fields.

It logs callback address/value and CPU state. It does not write ROM/RAM.
"""
from __future__ import annotations
import argparse,json
from pathlib import Path

def load(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def num(v):return int(str(v),0)

def main():
 ap=argparse.ArgumentParser()
 ap.add_argument('report',type=Path)
 ap.add_argument('-o','--out',type=Path,required=True)
 ap.add_argument('--fields',type=int,default=8)
 a=ap.parse_args();r=load(a.report)
 if r.get('classification')!='NAME_BUFFER_DIFFERENTIAL_CANDIDATES':
  raise SystemExit('FAIL CLOSED: differential report not ready')
 fs=[x for x in r.get('top_fields',[]) if x.get('all_variants_unique') and x.get('delete_restores_base')]
 if not fs:raise SystemExit('FAIL CLOSED: no strong fields')
 fs=fs[:max(1,a.fields)]
 # Deduplicate exact field ranges.
 seen=set();sel=[]
 for i,x in enumerate(fs,1):
  start=num(x['address']);width=int(x['width']);end=start+width-1
  key=(start,end)
  if key in seen:continue
  seen.add(key);sel.append((len(sel)+1,start,end,width,x.get('score')))
 rows='\n'.join(f'  {{id={i},s=0x{s:06X},e=0x{e:06X},w={w}}},' for i,s,e,w,score in sel)
 lua=f'''-- MMR name-entry candidate write-PC probe
-- READ ONLY. Generated from {a.report.name}
local FIELDS={{
{rows}
}}
local function hx(v,w)
 if v==nil then return "NA" end
 return string.format("%0"..tostring(w).."X",v)
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
 for _,k in ipairs({{"pc","a","x","y","s","d","db","p"}}) do o[k]=find(s,k,0) end
 return o
end
local mem=emu.memType.snesMemory or emu.memType.snesDebug
local wt=emu.callbackType.write
local cpu=emu.cpuType.snes
local refs={{}}
local function reg(f)
 local function cb(addr,val)
  local s=st()
  emu.log(string.format(
   "MMRNE WRITE field=%d addr=%s value=%s pc=%s A=%s X=%s Y=%s S=%s D=%s DB=%s P=%s",
   f.id,hx(addr&0xFFFFFF,6),hx(val,2),hx(s.pc,6),hx(s.a,4),hx(s.x,4),hx(s.y,4),
   hx(s.s,4),hx(s.d,4),hx(s.db,2),hx(s.p,2)))
 end
 local ok,ref=pcall(function()
  return emu.addMemoryCallback(cb,wt,f.s,f.e,cpu,mem)
 end)
 if ok then
  refs[#refs+1]=ref
  emu.log(string.format("MMRNE REG_OK field=%d start=%s end=%s",f.id,hx(f.s,6),hx(f.e,6)))
 else
  emu.log(string.format("MMRNE REG_FAIL field=%d start=%s end=%s",f.id,hx(f.s,6),hx(f.e,6)))
 end
end
if type(emu)~="table" or type(emu.addMemoryCallback)~="function" or wt==nil or cpu==nil or mem==nil then
 emu.log("MMRNE API_FAIL")
else
 for _,f in ipairs(FIELDS) do reg(f) end
 emu.log("MMRNE READY fields="..tostring(#FIELDS))
end
'''
 a.out.write_text(lua,encoding='utf-8')
 summary={'schema':'MMR_NAME_ENTRY_WRITE_PC_PROBE_GEN_V1','classification':'WRITE_PC_PROBE_READY',
          'source_report':a.report.name,'field_count':len(sel),
          'fields':[{'id':i,'start':f'0x{s:06X}','end':f'0x{e:06X}','width':w,'source_score':score} for i,s,e,w,score in sel],
          'rom_ram_write_performed':False}
 print(json.dumps(summary,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
