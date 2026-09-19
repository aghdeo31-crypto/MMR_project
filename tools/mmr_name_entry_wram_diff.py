#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""MMR name-entry WRAM differential analyzer.

Find physical name-buffer / selected-code candidates without assuming encoding.

Manifest example:
{
  "base": "empty.bin",
  "variants": [
    {"label":"charA","snapshot":"a.bin"},
    {"label":"charB","snapshot":"b.bin"},
    {"label":"charC","snapshot":"c.bin"}
  ],
  "delete_restore": "delete.bin",
  "address_base": "0x7E0000"
}

All snapshots cover the exact same WRAM range.
Best experiment: start from the same empty-name state and insert exactly one
DIFFERENT original-JP character into the same name slot for each variant.

Ranks compact fields that:
- differ from base in every variant;
- carry different values across variants;
- return to base after delete when supplied;
- are 1..4 bytes wide;
- are not embedded in a huge volatile block.

No encoding family is inferred. No ROM/RAM write is performed.
"""
from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path

def sha256(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(1<<20),b''):h.update(b)
    return h.hexdigest()

def num(v): return v if isinstance(v,int) else int(str(v),0)

def ranges(idx):
    if not idx:return []
    out=[];s=p=idx[0]
    for x in idx[1:]:
        if x==p+1:p=x
        else:out.append((s,p+1));s=p=x
    out.append((s,p+1));return out

def hx(b):return ' '.join(f'{x:02X}' for x in b)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('manifest',type=Path)
    ap.add_argument('-o','--out',type=Path,required=True)
    ap.add_argument('--top',type=int,default=100)
    a=ap.parse_args()
    m=json.loads(a.manifest.read_text(encoding='utf-8-sig'));root=a.manifest.parent
    basep=root/m['base'];vv=m.get('variants') or []
    if len(vv)<3:raise SystemExit('need >=3 variants')
    vp=[root/x['snapshot'] for x in vv]
    delp=(root/m['delete_restore']) if m.get('delete_restore') else None
    for p in [basep,*vp]+([delp] if delp else []):
        if not p.is_file():raise FileNotFoundError(p)
    paths=[basep,*vp]+([delp] if delp else [])
    blobs=[p.read_bytes() for p in paths]
    n=len(blobs[0])
    if any(len(x)!=n for x in blobs):raise SystemExit('snapshot size mismatch')
    base=blobs[0];variants=blobs[1:1+len(vp)];delete=blobs[-1] if delp else None
    addrbase=num(m.get('address_base','0x7E0000'))

    all_changed=[]
    byte_rows=[]
    for off in range(n):
        vals=[b[off] for b in variants]
        if all(v!=base[off] for v in vals):
            all_changed.append(off);distinct=len(set(vals));restored=(delete is None or delete[off]==base[off])
            score=50+min(30,distinct*10)+(20 if distinct==len(vals) else 0)+(30 if restored else -30)
            byte_rows.append({'offset':off,'address':addrbase+off,'base':base[off],
                              'variant_values':vals,'distinct_values':distinct,
                              'all_variants_unique':distinct==len(vals),
                              'delete_restores_base':restored,'score':score})

    cset=set(all_changed);fields=[]
    for start in all_changed:
        for width in (1,2,3,4):
            end=start+width
            if end>n or not all(i in cset for i in range(start,end)):continue
            vals=[b[start:end] for b in variants];distinct=len(set(vals))
            if distinct<2:continue
            restored=(delete is None or delete[start:end]==base[start:end])
            lo=max(0,start-16);hi=min(n,end+16);volatile=sum(i in cset for i in range(lo,hi))
            penalty=max(0,volatile-width-4)
            score=100+min(60,distinct*15)+(30 if distinct==len(vals) else 0)+(40 if restored else -50)-penalty*2
            fields.append({'offset':start,'address':addrbase+start,'width':width,
                           'base_hex':hx(base[start:end]),'variant_hex':[hx(x) for x in vals],
                           'distinct_values':distinct,'all_variants_unique':distinct==len(vals),
                           'delete_restores_base':restored,'local_all_variant_changed_bytes':volatile,
                           'score':score})
    fields.sort(key=lambda x:(-x['score'],x['width'],x['offset']))
    byte_rows.sort(key=lambda x:(-x['score'],x['offset']))
    strong=[x for x in fields if x['all_variants_unique'] and x['delete_restores_base']]

    summary=[]
    for meta,b,p in zip(vv,variants,vp):
        idx=[i for i,(x,y) in enumerate(zip(base,b)) if x!=y]
        summary.append({'label':meta.get('label'),'snapshot':p.name,'sha256':sha256(p),
                        'changed_bytes':len(idx),
                        'changed_ranges':[{'address_start':f'0x{addrbase+s:06X}',
                                           'address_end_exclusive':f'0x{addrbase+e:06X}',
                                           'bytes':e-s} for s,e in ranges(idx)[:200]]})
    delete_summary=None
    if delp:
        idx=[i for i,(x,y) in enumerate(zip(base,delete)) if x!=y]
        delete_summary={'snapshot':delp.name,'sha256':sha256(delp),
                        'bytes_not_restored_to_base':len(idx),
                        'ranges_not_restored':[{'address_start':f'0x{addrbase+s:06X}',
                                                'address_end_exclusive':f'0x{addrbase+e:06X}',
                                                'bytes':e-s} for s,e in ranges(idx)[:200]]}

    report={'schema':'MMR_NAME_ENTRY_WRAM_DIFF_V1',
      'classification':'NAME_BUFFER_DIFFERENTIAL_CANDIDATES' if strong else 'NAME_BUFFER_DIFFERENTIAL_NOT_READY',
      'manifest':a.manifest.name,
      'base':{'snapshot':basep.name,'sha256':sha256(basep),'bytes':n,'address_base':f'0x{addrbase:06X}'},
      'variants':summary,'delete_restore':delete_summary,
      'all_variants_changed_byte_count':len(all_changed),
      'strong_field_count':len(strong),
      'top_fields':[{**x,'address':f"0x{x['address']:06X}"} for x in fields[:a.top]],
      'top_byte_candidates':[{**x,'address':f"0x{x['address']:06X}",
                              'base_hex':f"{x['base']:02X}",
                              'variant_values_hex':[f'{v:02X}' for v in x['variant_values']]} for x in byte_rows[:a.top]],
      'authority':{'encoding_inferred':False,'name_buffer_proven':False,
                   'selection_table_proven':False,
                   'rule':'Require a second independent name-slot experiment plus write-PC/runtime-path evidence before physical-binding authority.'}}
    a.out.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False,indent=2))
    raise SystemExit(0 if strong else 2)
if __name__=='__main__':main()
