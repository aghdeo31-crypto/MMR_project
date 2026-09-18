#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build a Japanese-original-first MMR translation review queue.

The FINAL 3341-row Korean translation is translation-text authority, but it is
NOT automatically a Japanese-record crosswalk. This tool only marks rows
REVIEW_READY when an authoritative crosswalk witness exists AND readable
Japanese source text is present on the exact-JP record side.

No ROM writes. No English offsets/order. No duplicate propagation.
"""
from __future__ import annotations
import argparse,csv,hashlib,json,re
from pathlib import Path

ALLOWED_WITNESS={
 'AUTHORITATIVE_EXPLICIT_RECORD_BINDING',
 'EXACT_SOURCE_BYTES_WITH_TRANSLATION_ID',
 'CONFIRMED_JP_TEXT_ID_MATCH',
 'PRESERVED_RUNTIME_RECORD_IDENTITY',
}
UNSAFE_COLUMNS={'table_id','table_index','text_file_offset','snes_pointer','english_offset','en_offset'}
TOKEN_RE=re.compile(r'<[^>]+>')

def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()

def rows(p):
 with Path(p).open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f,delimiter='\t'))

def pick(d,names):
 low={k.lower():k for k in d}
 for n in names:
  if n.lower() in low:return low[n.lower()]
 return None

def control_tokens(s):return TOKEN_RE.findall(s or '')

def main():
 ap=argparse.ArgumentParser()
 ap.add_argument('translation_tsv',type=Path)
 ap.add_argument('exactjp_records_tsv',type=Path)
 ap.add_argument('authoritative_crosswalk_tsv',type=Path)
 ap.add_argument('-o','--outdir',type=Path,default=Path('MMR_JP_FIRST_AUDIT'))
 a=ap.parse_args();a.outdir.mkdir(parents=True,exist_ok=True)
 tr=rows(a.translation_tsv);jp=rows(a.exactjp_records_tsv);cw=rows(a.authoritative_crosswalk_tsv)
 fail=[]
 if len(tr)!=3341:fail.append(f'translation rows must be 3341, got {len(tr)}')
 if len(jp)!=3156:fail.append(f'exact-JP rows must be 3156, got {len(jp)}')
 if tr and any(c.lower() in UNSAFE_COLUMNS for c in tr[0]):
  fail.append('translation TSV contains unsafe English-layout/address columns')
 if not tr or not jp:
  fail.append('empty input')
 if fail:
  rep={'classification':'FAIL_CLOSED','reasons':fail}
  (a.outdir/'MMR_JP_FIRST_AUDIT_REPORT.json').write_text(json.dumps(rep,ensure_ascii=False,indent=2),encoding='utf-8')
  print(json.dumps(rep,ensure_ascii=False,indent=2));return 2

 tidk=pick(tr[0],['id','row_id','script_id','translation_id'])
 kok=pick(tr[0],['ko','korean','translation','translated_text','ko_text'])
 enk=pick(tr[0],['en','english','source','source_text','en_text'])
 ridk=pick(jp[0],['record_id'])
 rawshak=pick(jp[0],['raw_sha256','record_raw_sha256'])
 jptk=pick(jp[0],['japanese_text','jp_text','visible_japanese','decoded_japanese','confirmed_japanese_text'])
 rawhexk=pick(jp[0],['raw_hex','record_raw_hex'])
 if not tidk or not kok: fail.append('translation ID/Korean column missing')
 if not ridk or not rawshak: fail.append('exact-JP record_id/raw_sha256 column missing')
 if fail:
  rep={'classification':'FAIL_CLOSED','reasons':fail}
  (a.outdir/'MMR_JP_FIRST_AUDIT_REPORT.json').write_text(json.dumps(rep,ensure_ascii=False,indent=2),encoding='utf-8')
  print(json.dumps(rep,ensure_ascii=False,indent=2));return 2

 tmap={int(r[tidk]):r for r in tr}
 if sorted(tmap)!=list(range(3341)):fail.append('translation IDs are not exactly 0..3340')
 jmap={r[ridk]:r for r in jp}
 if len(jmap)!=3156:fail.append('duplicate exact-JP record_id')

 bound={}; badw=[]
 for n,w in enumerate(cw,2):
  try:tid=int(w.get('translation_id',''))
  except:badw.append(f'line {n}: invalid translation_id');continue
  rid=w.get('record_id','');typ=(w.get('witness_type') or '').strip()
  expected=(w.get('record_raw_sha256') or '').lower()
  if typ not in ALLOWED_WITNESS:badw.append(f'line {n}: unapproved witness {typ}');continue
  if tid not in tmap or rid not in jmap:badw.append(f'line {n}: unknown id/record');continue
  actual=(jmap[rid].get(rawshak) or '').lower()
  if expected!=actual:badw.append(f'line {n}: raw SHA mismatch');continue
  if tid in bound and bound[tid]!=rid:badw.append(f'line {n}: conflicting binding for {tid}');continue
  bound[tid]=rid
 if badw:fail+=badw

 queue=[];ready=hold=0
 for tid in range(3341):
  t=tmap[tid];rid=bound.get(tid,''); j=jmap.get(rid,{})
  jptext=(j.get(jptk,'') if jptk else '').strip()
  status='UNBOUND_HOLD'; reason='NO_AUTHORITATIVE_JP_RECORD_BINDING'
  if rid:
   if jptext:
    status='REVIEW_READY';reason='AUTHORITATIVE_BINDING_AND_JP_TEXT_PRESENT';ready+=1
   else:
    status='BOUND_RAW_ONLY_HOLD';reason='JP_RECORD_BOUND_BUT_READABLE_JP_TEXT_NOT_PRESENT';hold+=1
  else:hold+=1
  queue.append({
   'translation_id':tid,'record_id':rid,'status':status,'reason':reason,
   'japanese_text':jptext,'korean_current':t.get(kok,''),'korean_revised':'',
   'english_auxiliary':t.get(enk,'') if enk else '',
   'record_raw_sha256':j.get(rawshak,'') if rid else '',
   'record_raw_hex':j.get(rawhexk,'') if (rid and rawhexk) else '',
   'review_action':'HOLD' if status!='REVIEW_READY' else 'REVIEW',
   'evidence_type':'','review_note':''
  })

 fields=list(queue[0])
 with (a.outdir/'MMR_JP_FIRST_AUDIT_QUEUE.tsv').open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,fieldnames=fields,delimiter='\t',lineterminator='\n');w.writeheader();w.writerows(queue)
 rep={
  'schema':'MMR_JP_FIRST_AUDIT_QUEUE_V1',
  'classification':'PASS_QUEUE_BUILT' if not fail else 'FAIL_CLOSED',
  'translation_rows':len(tr),'exactjp_records':len(jp),'authoritative_bindings':len(bound),
  'review_ready_rows':ready,'hold_rows':hold,'japanese_text_column':jptk,
  'translation_sha256':sha(a.translation_tsv),'exactjp_sha256':sha(a.exactjp_records_tsv),
  'crosswalk_sha256':sha(a.authoritative_crosswalk_tsv),
  'english_role':'AUXILIARY_ONLY_NEVER_AUTHORITY',
  'ordinal_binding_used':False,'english_offset_binding_used':False,'duplicate_propagation_used':False,
  'reasons':fail,
  'next':'Translate/revise only REVIEW_READY rows from japanese_text; then feed reviewed EDIT rows to mmr_jp_translation_review_gate.py.'
 }
 (a.outdir/'MMR_JP_FIRST_AUDIT_REPORT.json').write_text(json.dumps(rep,ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps(rep,ensure_ascii=False,indent=2))
 return 0 if not fail else 2

if __name__=='__main__':raise SystemExit(main())
