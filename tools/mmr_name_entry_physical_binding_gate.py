#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""MMR name-entry physical binding validator v2.

Validates a recovered/constructed physical binding contract AFTER the Japanese
original name-entry storage path has been identified.

No encoding family is assumed: private08, 1-byte, 2-byte, dialogue KS2350 IDs,
and English-patch codes are all non-authoritative until proven.

Two levels:
- PASS_NAME_ENTRY_PHYSICAL_BINDING_STATIC
  exact original-JP encoding/storage contract + 200 logical->physical mappings
  + four physical page-table witnesses.
- PASS_NAME_ENTRY_PHYSICAL_BINDING_FULL
  STATIC plus runtime selection->buffer, edit semantics, and save/reset/load.

Preflight may require STATIC. Release must require FULL.
"""
from __future__ import annotations
import argparse,json,re
from pathlib import Path

JP_SHA="6a68e1806d8d72accb4a5218330210e178880216863c1c38b8865032c5c28724"
HEX_RE=re.compile(r'^(?:[0-9A-Fa-f]{2})(?: [0-9A-Fa-f]{2})*$')

def load(p):
    return json.loads(Path(p).read_text(encoding='utf-8-sig'))

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('contract',type=Path)
    ap.add_argument('--candidate-sha256',required=True)
    ap.add_argument('-o','--out',type=Path,required=True)
    a=ap.parse_args()
    c=load(a.contract);cand=a.candidate_sha256.lower()
    static_fail=[]
    runtime_fail=[]

    if c.get('original_rom_sha256','').lower()!=JP_SHA:
        static_fail.append('ORIGINAL_ROM_SHA_MISMATCH')
    if c.get('candidate_sha256','').lower()!=cand:
        static_fail.append('CANDIDATE_SHA_MISMATCH')

    enc=c.get('encoding_contract') or {}
    for k in ('confirmed','selection_table_encoding','name_buffer_encoding',
              'terminator_or_length_contract','evidence'):
        if k not in enc:static_fail.append('MISSING_ENCODING_FIELD:'+k)
    if enc.get('confirmed') is not True:
        static_fail.append('ENCODING_CONTRACT_NOT_CONFIRMED')
    if not str(enc.get('evidence') or '').strip():
        static_fail.append('ENCODING_EVIDENCE_EMPTY')

    rows=c.get('mappings') or []
    if len(rows)!=200:
        static_fail.append(f'MAPPING_COUNT_{len(rows)}_NOT_200')
    chars=[];payloads=[]
    for n,r in enumerate(rows):
        try:idx=int(r.get('logical_index'))
        except:idx=-1
        ch=str(r.get('char') or '')
        ph=str(r.get('physical_code_hex') or '').strip()
        chars.append(ch);payloads.append(ph)
        if idx!=n:static_fail.append(f'LOGICAL_INDEX_MISMATCH_ROW_{n}_GOT_{idx}')
        if len(ch)!=1 or not ('가'<=ch<='힣'):
            static_fail.append(f'INVALID_CHAR_ROW_{n}:{ch!r}')
        if not ph or not HEX_RE.match(ph):
            static_fail.append(f'INVALID_PHYSICAL_CODE_ROW_{n}:{ph!r}')
        if r.get('control_collision_checked') is not True:
            static_fail.append(f'CONTROL_COLLISION_NOT_CHECKED_ROW_{n}')
        if r.get('roundtrip_decoded_char')!=ch:
            static_fail.append(f'ROUNDTRIP_CHAR_MISMATCH_ROW_{n}')

    if len(set(chars))!=200:static_fail.append('LOGICAL_CHARS_NOT_UNIQUE_200')
    if len(set(payloads))!=200:static_fail.append('PHYSICAL_PAYLOADS_NOT_UNIQUE_200')

    pages=c.get('pages') or []
    if len(pages)!=4:
        static_fail.append('PAGE_COUNT_NOT_4')
    else:
        for i,p in enumerate(pages,1):
            if p.get('page')!=i:static_fail.append(f'PAGE_NUMBER_BAD_{i}')
            ids=p.get('logical_indices') or []
            exp=list(range((i-1)*50,i*50))
            if ids!=exp:static_fail.append(f'PAGE_LOGICAL_INDICES_BAD_{i}')
            if p.get('physical_table_evidence_confirmed') is not True:
                static_fail.append(f'PAGE_TABLE_EVIDENCE_NOT_CONFIRMED_{i}')
            if not str(p.get('evidence') or '').strip():
                static_fail.append(f'PAGE_TABLE_EVIDENCE_EMPTY_{i}')

    rt=c.get('runtime_contract') or {}
    if rt.get('selection_to_buffer_path_confirmed') is not True:
        runtime_fail.append('SELECTION_TO_BUFFER_PATH_NOT_CONFIRMED')
    if rt.get('delete_complete_cancel_semantics_confirmed') is not True:
        runtime_fail.append('DELETE_COMPLETE_CANCEL_NOT_CONFIRMED')
    if rt.get('save_reset_load_roundtrip_confirmed') is not True:
        runtime_fail.append('SAVE_RESET_LOAD_NOT_CONFIRMED')
    if not str(rt.get('evidence') or '').strip():
        runtime_fail.append('RUNTIME_EVIDENCE_EMPTY')

    static_pass=not static_fail
    full_pass=static_pass and not runtime_fail
    if full_pass:
        cls='PASS_NAME_ENTRY_PHYSICAL_BINDING_FULL'
    elif static_pass:
        cls='PASS_NAME_ENTRY_PHYSICAL_BINDING_STATIC'
    else:
        cls='HOLD_NAME_ENTRY_PHYSICAL_BINDING'

    out={
      'schema':'MMR_NAME_ENTRY_PHYSICAL_BINDING_GATE_V2',
      'classification':cls,
      'candidate_sha256':cand,
      'original_rom_sha256':JP_SHA,
      'static_pass':static_pass,
      'full_pass':full_pass,
      'mapping_count':len(rows),
      'unique_chars':len(set(chars)),
      'unique_physical_payloads':len(set(payloads)),
      'encoding_contract':enc,
      'static_failures':static_fail,
      'runtime_failures':runtime_fail,
      'rule':'No encoding family is assumed. Runtime-test preflight may use STATIC; release requires FULL.'
    }
    a.out.write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(out,ensure_ascii=False,indent=2))
    raise SystemExit(0 if static_pass else 2)

if __name__=='__main__':
    main()
