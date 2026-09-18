#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""MMR Japanese-original translation review gate.

This is a review-safety gate, not a translator.
It permits an EDIT only when the row carries Japanese-original evidence.
English text may exist as auxiliary context but can never authorize an edit.

Expected TSV columns
--------------------
required:
  record_id
  action                 KEEP | EDIT | HOLD
  japanese_text
  korean_before
  korean_after
  evidence_type

optional but recommended:
  translation_id
  jp_source_sha256
  control_signature_before
  control_signature_after
  note

Allowed EDIT evidence_type values:
  EXACT_JP_TEXT
  EXACT_JP_RECORD_DECODE
  CONFIRMED_JP_TEXT_ID_MATCH
  PRESERVED_RUNTIME_RECORD_IDENTITY
  AUTHORITATIVE_EXPLICIT_RECORD_BINDING

Explicitly non-authoritative examples:
  ENGLISH
  ENGLISH_ONLY
  FAN_TRANSLATION_ONLY
  SEMANTIC_CANDIDATE
  STRONG_UNBOUND
"""
from __future__ import annotations
import argparse, csv, hashlib, json, re
from pathlib import Path

ALLOWED_EDIT_EVIDENCE={
    'EXACT_JP_TEXT',
    'EXACT_JP_RECORD_DECODE',
    'CONFIRMED_JP_TEXT_ID_MATCH',
    'PRESERVED_RUNTIME_RECORD_IDENTITY',
    'AUTHORITATIVE_EXPLICIT_RECORD_BINDING',
}
FORBIDDEN_AUTHORITY_WORDS=('ENGLISH','ENG_ONLY','ENGLISH_ONLY')
ACTIONS={'KEEP','EDIT','HOLD'}
TOKEN_RE=re.compile(r'<[^>]+>')

def sha256(p:Path)->str:
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1<<20),b''): h.update(b)
    return h.hexdigest()

def tokens(s:str):
    return TOKEN_RE.findall(s or '')

def main():
    ap=argparse.ArgumentParser(description='Fail-closed Japanese-original authority gate for MMR dialogue review')
    ap.add_argument('ledger',type=Path)
    ap.add_argument('-o','--out',type=Path,default=Path('MMR_JP_TRANSLATION_REVIEW_GATE.json'))
    a=ap.parse_args()
    with a.ledger.open(encoding='utf-8-sig',newline='') as f:
        rows=list(csv.DictReader(f,delimiter='\t'))
    required={'record_id','action','japanese_text','korean_before','korean_after','evidence_type'}
    missing=sorted(required-set(rows[0].keys() if rows else []))
    fail=[]; counts={'rows':len(rows),'KEEP':0,'EDIT':0,'HOLD':0}
    if missing:
        fail.append({'row':0,'reason':'MISSING_REQUIRED_COLUMNS','columns':missing})
    seen=set()
    for n,r in enumerate(rows,2):
        rid=(r.get('record_id') or '').strip()
        action=(r.get('action') or '').strip().upper()
        ev=(r.get('evidence_type') or '').strip().upper()
        jp=(r.get('japanese_text') or '').strip()
        kb=r.get('korean_before') or ''
        ka=r.get('korean_after') or ''
        if not rid:
            fail.append({'row':n,'reason':'EMPTY_RECORD_ID'})
        elif rid in seen:
            fail.append({'row':n,'record_id':rid,'reason':'DUPLICATE_RECORD_ID'})
        seen.add(rid)
        if action not in ACTIONS:
            fail.append({'row':n,'record_id':rid,'reason':'INVALID_ACTION','value':action})
            continue
        counts[action]+=1
        if action=='EDIT':
            if not jp:
                fail.append({'row':n,'record_id':rid,'reason':'EDIT_WITHOUT_JAPANESE_TEXT'})
            if ev not in ALLOWED_EDIT_EVIDENCE:
                fail.append({'row':n,'record_id':rid,'reason':'EDIT_WITHOUT_AUTHORITATIVE_JP_EVIDENCE','evidence_type':ev})
            if any(w in ev for w in FORBIDDEN_AUTHORITY_WORDS):
                fail.append({'row':n,'record_id':rid,'reason':'ENGLISH_USED_AS_EDIT_AUTHORITY','evidence_type':ev})
            if not ka.strip():
                fail.append({'row':n,'record_id':rid,'reason':'EDIT_WITH_EMPTY_KOREAN_AFTER'})
            # Preserve explicit angle-bracket control tokens exactly and in order.
            if tokens(kb)!=tokens(ka):
                fail.append({'row':n,'record_id':rid,'reason':'CONTROL_TOKEN_SEQUENCE_CHANGED',
                             'before':tokens(kb),'after':tokens(ka)})
            cb=(r.get('control_signature_before') or '').strip()
            ca=(r.get('control_signature_after') or '').strip()
            if cb or ca:
                if cb!=ca:
                    fail.append({'row':n,'record_id':rid,'reason':'CONTROL_SIGNATURE_CHANGED','before':cb,'after':ca})
        elif action=='KEEP':
            if ka and ka!=kb:
                fail.append({'row':n,'record_id':rid,'reason':'KEEP_ROW_HAS_CHANGED_KOREAN_TEXT'})
    result={
        'schema':'MMR_JP_TRANSLATION_REVIEW_GATE_V1',
        'classification':'PASS_JP_AUTHORITY_REVIEW_GATE' if not fail else 'FAIL_JP_AUTHORITY_REVIEW_GATE',
        'ledger':a.ledger.name,
        'ledger_sha256':sha256(a.ledger),
        'counts':counts,
        'allowed_edit_evidence':sorted(ALLOWED_EDIT_EVIDENCE),
        'english_role':'AUXILIARY_REFERENCE_ONLY',
        'failures':fail,
        'note':'PASS means edits are provenance/control-safe for review; it does not independently certify translation quality or ROM binding.'
    }
    a.out.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False,indent=2))
    raise SystemExit(0 if not fail else 2)

if __name__=='__main__':
    main()
