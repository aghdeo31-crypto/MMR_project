#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Correlate two MMR name-entry WRAM differential reports.

Use report A for first name slot and report B for second name slot, with the
same three logical test characters and identical experimental procedure.

Ranks pairs of strong fields that have:
- equal width;
- small positive address stride;
- identical variant-distinctness shape;
- delete restoration in both experiments.

This can suggest buffer element width/stride but still does not prove encoding.
"""
from __future__ import annotations
import argparse,json
from pathlib import Path

def load(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def addr(x):return int(str(x),0)

def main():
 ap=argparse.ArgumentParser()
 ap.add_argument('slot1',type=Path);ap.add_argument('slot2',type=Path)
 ap.add_argument('-o','--out',type=Path,required=True)
 a=ap.parse_args();r1=load(a.slot1);r2=load(a.slot2)
 if r1.get('classification')!='NAME_BUFFER_DIFFERENTIAL_CANDIDATES' or r2.get('classification')!='NAME_BUFFER_DIFFERENTIAL_CANDIDATES':
  raise SystemExit('input reports not ready')
 f1=[x for x in r1.get('top_fields',[]) if x.get('all_variants_unique') and x.get('delete_restores_base')]
 f2=[x for x in r2.get('top_fields',[]) if x.get('all_variants_unique') and x.get('delete_restores_base')]
 cand=[]
 for x in f1:
  for y in f2:
   if x.get('width')!=y.get('width'):continue
   s=addr(y['address'])-addr(x['address'])
   if not (1<=s<=16):continue
   shape=(x.get('distinct_values')==y.get('distinct_values'))
   score=100+(50 if s==x['width'] else 0)+(25 if shape else 0)-abs(s-x['width'])*2
   cand.append({'slot1_address':x['address'],'slot2_address':y['address'],
                'width':x['width'],'stride':s,'stride_equals_width':s==x['width'],
                'variant_shape_match':shape,'score':score,
                'slot1_variant_hex':x.get('variant_hex'),'slot2_variant_hex':y.get('variant_hex')})
 cand.sort(key=lambda x:(-x['score'],x['stride'],x['width'],x['slot1_address']))
 strong=[x for x in cand if x['stride_equals_width'] and x['variant_shape_match']]
 out={'schema':'MMR_NAME_ENTRY_WRAM_STRIDE_V1',
      'classification':'NAME_BUFFER_STRIDE_CANDIDATES' if strong else 'NAME_BUFFER_STRIDE_NOT_READY',
      'slot1_report':a.slot1.name,'slot2_report':a.slot2.name,
      'strong_count':len(strong),'top_candidates':cand[:100],
      'authority':{'buffer_stride_proven':False,'encoding_proven':False,
                   'rule':'Strong stride candidate still requires write-PC evidence and save/reset/load confirmation.'}}
 a.out.write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps(out,ensure_ascii=False,indent=2))
 raise SystemExit(0 if strong else 2)
if __name__=='__main__':main()
