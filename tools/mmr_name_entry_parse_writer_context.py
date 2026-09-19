#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Parse MMR name-entry writer context logs."""
from __future__ import annotations
import argparse,hashlib,json,re
from pathlib import Path

HIT=re.compile(r'MMRNECTX HIT n=(\d+) pc=([0-9A-F]+)')
CODE=re.compile(r'MMRNECTX CODE ((?:[0-9A-F]{2} ?)+)')

def spec(s):
 if '=' not in s:raise argparse.ArgumentTypeError('label=path')
 k,v=s.split('=',1);return k,Path(v)

def main():
 ap=argparse.ArgumentParser()
 ap.add_argument('--log',action='append',type=spec,required=True)
 ap.add_argument('-o','--out',type=Path,required=True)
 a=ap.parse_args()
 if len(a.log)<3:raise SystemExit('need >=3 logs')
 rows=[];allcodes=[]
 for label,p in a.log:
  txt=p.read_text(encoding='utf-8',errors='replace')
  hits=HIT.findall(txt);codes=CODE.findall(txt)
  code_norm=[' '.join(x.split()) for x in codes]
  allcodes+=code_norm
  rows.append({'label':label,'file':p.name,'hits':len(hits),
               'pcs':sorted(set(pc for n,pc in hits)),
               'code_windows':len(code_norm),
               'code_sha256s':sorted(set(hashlib.sha256(bytes.fromhex(x)).hexdigest() for x in code_norm))})
 nonzero=all(x['hits']>0 for x in rows)
 onepc=set()
 for x in rows:onepc.update(x['pcs'])
 stable_pc=(len(onepc)==1)
 stable_code=(len(set(allcodes))==1 and len(allcodes)>=len(rows))
 strong=nonzero and stable_pc and stable_code
 out={'schema':'MMR_NAME_ENTRY_WRITER_CONTEXT_PARSE_V1',
      'classification':'NAME_ENTRY_WRITER_CONTEXT_CANDIDATE' if strong else 'NAME_ENTRY_WRITER_CONTEXT_NOT_READY',
      'logs':rows,'writer_pcs':sorted(onepc),
      'all_logs_hit':nonzero,'single_writer_pc':stable_pc,'code_window_stable':stable_code,
      'code_window_sha256':hashlib.sha256(bytes.fromhex(allcodes[0])).hexdigest() if stable_code else None,
      'authority':{'writer_context_frozen':strong,'name_buffer_semantics_proven':False,
                   'rule':'Next: mode-aware disassembly/dataflow from selected-table read through writer and save/load path.'}}
 a.out.write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps(out,ensure_ascii=False,indent=2))
 raise SystemExit(0 if strong else 2)
if __name__=='__main__':main()
