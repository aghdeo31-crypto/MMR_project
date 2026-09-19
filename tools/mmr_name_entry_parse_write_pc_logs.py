#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Parse multiple MMR name-entry candidate write-PC probe logs.

Use one log per controlled experiment/character. Example:
  --log charA=a.log --log charB=b.log --log charC=c.log

A strong write-PC candidate must recur for the same field/address family across
at least three independent labeled logs. This still does not prove name-buffer
semantics; it narrows the exact writer for targeted tracing.
"""
from __future__ import annotations
import argparse,json,re
from collections import Counter,defaultdict
from pathlib import Path

RX=re.compile(r'MMRNE WRITE field=(\d+) addr=([0-9A-F]+) value=([0-9A-F]+|NA) pc=([0-9A-F]+|NA)')

def spec(s):
 if '=' not in s:raise argparse.ArgumentTypeError('use label=path')
 k,v=s.split('=',1);return k,Path(v)

def main():
 ap=argparse.ArgumentParser()
 ap.add_argument('--log',action='append',type=spec,required=True)
 ap.add_argument('-o','--out',type=Path,required=True)
 a=ap.parse_args()
 if len(a.log)<3:raise SystemExit('need >=3 independent logs')
 per=[];byfield=defaultdict(lambda:defaultdict(Counter))
 for label,p in a.log:
  if not p.is_file():raise FileNotFoundError(p)
  events=[]
  for line in p.read_text(encoding='utf-8',errors='replace').splitlines():
   m=RX.search(line)
   if not m:continue
   f=int(m.group(1));addr=m.group(2);val=m.group(3);pc=m.group(4)
   events.append({'field':f,'addr':addr,'value':val,'pc':pc})
   if pc!='NA':byfield[f][label][pc]+=1
  per.append({'label':label,'file':p.name,'events':len(events)})
 ranked=[]
 for f,labmap in byfield.items():
  pcs=set()
  for c in labmap.values():pcs.update(c)
  for pc in pcs:
   hit_labels=[lab for lab,c in labmap.items() if c.get(pc,0)>0]
   total=sum(c.get(pc,0) for c in labmap.values())
   ranked.append({'field':f,'pc':pc,'independent_logs':len(hit_labels),
                  'labels':hit_labels,'total_hits':total,
                  'all_logs':len(hit_labels)==len(a.log)})
 ranked.sort(key=lambda x:(-x['independent_logs'],-x['total_hits'],x['field'],x['pc']))
 strong=[x for x in ranked if x['independent_logs']>=3]
 out={'schema':'MMR_NAME_ENTRY_WRITE_PC_PARSE_V1',
      'classification':'NAME_ENTRY_WRITE_PC_CANDIDATES' if strong else 'NAME_ENTRY_WRITE_PC_NOT_READY',
      'logs':per,'candidate_count':len(ranked),'strong_count':len(strong),
      'top_candidates':ranked[:100],
      'authority':{'writer_pc_proven':False,'name_buffer_proven':False,
                   'rule':'Strong recurrent writer requires targeted exec/dataflow trace and save/reset/load proof.'}}
 a.out.write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps(out,ensure_ascii=False,indent=2))
 raise SystemExit(0 if strong else 2)
if __name__=='__main__':main()
