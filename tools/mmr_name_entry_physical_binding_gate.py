#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""MMR name-entry physical binding validator.

Validates a recovered/constructed physical binding contract AFTER the Japanese
original name-entry storage path has been identified.

This tool intentionally does NOT assume private08, 1-byte, 2-byte, dialogue
KS2350 IDs, or English-patch name codes.

Contract JSON must explicitly state the confirmed physical encoding/storage
contract and map all 200 logical cells to physical code payloads.
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
    c=load(a.contract); cand=a.candidate_sha256.lower()
    fail=[]
    if c.get('original_rom_sha256','').lower()!=JP_SHA:
        fail.append('ORIGINAL_ROM_SHA_MISMATCH')
    if c.get('candidate_sha256','').lower()!=cand:
        fail.append('CANDIDATE_SHA_MISMATCH')
    enc=c.get('encoding_contract') or {}
    required_enc=[
      'confirmed','selection_table_encoding','name_buffer_encoding',
      'terminator_or_length_contract','evidence'
    ]
    for k in required_enc:
        if k not in enc: fail.append('MISSING_ENCODING_FIELD:'+k)
    if enc.get('confirmed') is not True:
        fail.append('ENCODING_CONTRACT_NOT_CONFIRMED')
    if not str(enc.get('evidence') or '').strip():
        fail.append('ENCODING_EVIDENCE_EMPTY')

    rows=c.get('mappings') or []
    if len(rows)!=200:
        fail.append(f'MAPPING_COUNT_{len(rows)}_NOT_200')
    logical=[]
    chars=[]
    payloads=[]
    for n,r in enumerate(rows):
        try: idx=int(r.get('logical_index'))
        except: idx=-1
        logical.append(idx)
        ch=str(r.get('char') or '')
        chars.append(ch)
        ph=str(r.get('physical_code_hex') or '').strip()
        payloads.append(ph)
        if idx!=n:
            fail.append(f'LOGICAL_INDEX_MISMATCH_ROW_{n}_GOT_{idx}')
        if len(ch)!=1 or not ('가'<=ch<='힣'):
            fail.append(f'INVALID_CHAR_ROW_{n}:{ch!r}')
        if not ph or not HEX_RE.match(ph):
            fail.append(f'INVALID_PHYSICAL_CODE_ROW_{n}:{ph!r}')
        if r.get('control_collision_checked') is not True:
            fail.append(f'CONTROL_COLLISION_NOT_CHECKED_ROW_{n}')
        if r.get('roundtrip_decoded_char')!=ch:
            fail.append(f'ROUNDTRIP_CHAR_MISMATCH_ROW_{n}')

    if len(set(chars))!=200:
        fail.append('LOGICAL_CHARS_NOT_UNIQUE_200')
    if len(set(payloads))!=200:
        fail.append('PHYSICAL_PAYLOADS_NOT_UNIQUE_200')

    pages=c.get('pages') or []
    if len(pages)!=4:
        fail.append('PAGE_COUNT_NOT_4')
    else:
        for i,p in enumerate(pages,1):
            if p.get('page')!=i: fail.append(f'PAGE_NUMBER_BAD_{i}')
            ids=p.get('logical_indices') or []
            exp=list(range((i-1)*50,i*50))
            if ids!=exp: fail.append(f'PAGE_LOGICAL_INDICES_BAD_{i}')
            if p.get('physical_table_evidence_confirmed') is not True:
                fail.append(f'PAGE_TABLE_EVIDENCE_NOT_CONFIRMED_{i}')

    rt=c.get('runtime_contract') or {}
    if rt.get('selection_to_buffer_path_confirmed') is not True:
        fail.append('SELECTION_TO_BUFFER_PATH_NOT_CONFIRMED')
    if rt.get('delete_complete_cancel_semantics_confirmed') is not True:
        fail.append('DELETE_COMPLETE_CANCEL_NOT_CONFIRMED')
    if rt.get('save_reset_load_roundtrip_confirmed') is not True:
        fail.append('SAVE_RESET_LOAD_NOT_CONFIRMED')

    out={
      'schema':'MMR_NAME_ENTRY_PHYSICAL_BINDING_GATE_V1',
      'classification':'PASS_NAME_ENTRY_PHYSICAL_BINDING' if not fail else 'HOLD_NAME_ENTRY_PHYSICAL_BINDING',
      'candidate_sha256':cand,
      'original_rom_sha256':JP_SHA,
      'mapping_count':len(rows),
      'unique_chars':len(set(chars)),
      'unique_physical_payloads':len(set(payloads)),
      'encoding_contract':enc,
      'failures':fail,
      'rule':'No encoding family is assumed. PASS requires a confirmed original-JP physical contract and exact 200-cell mapping.'
    }
    a.out.write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(out,ensure_ascii=False,indent=2))
    raise SystemExit(0 if not fail else 2)

if __name__=='__main__':
    main()
