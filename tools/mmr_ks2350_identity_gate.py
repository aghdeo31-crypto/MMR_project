#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""MMR KS2350 glyph identity / private-token round-trip gate.

Purpose
-------
Catch mapping/encoder faults such as an intended Hangul syllable resolving to
another glyph before a ROM is built.

Authoritative Stage432 contract:
  KS X 1001 Hangul 2350, EUC-KR B0A1..C8FE row-major
  private token = 08 hi lo
  id = (hi-1)*160 + (lo-0x60)

This tool does not touch a ROM.
"""
from __future__ import annotations
import argparse,csv,hashlib,json,re
from collections import Counter
from pathlib import Path

TOTAL=2350
TOKEN_LEAD=0x08
HANGUL_RE=re.compile(r'[가-힣]')

def ks2350():
    out=[]
    for a in range(0xB0,0xC9):
        for b in range(0xA1,0xFF):
            out.append(bytes((a,b)).decode('euc_kr'))
    assert len(out)==TOTAL and out[0]=='가' and out[-1]=='힝'
    return out

KS=ks2350()
CHAR_TO_ID={c:i for i,c in enumerate(KS)}

def token_for_id(i:int)->bytes:
    if not 0<=i<TOTAL: raise ValueError(i)
    hi=i//160+1
    lo=i%160+0x60
    return bytes((TOKEN_LEAD,hi,lo))

def decode_token(tok:bytes):
    if len(tok)!=3 or tok[0]!=TOKEN_LEAD:
        raise ValueError('not private token')
    hi,lo=tok[1],tok[2]
    i=(hi-1)*160+(lo-0x60)
    if not 0<=i<TOTAL:
        raise ValueError(f'out-of-range id {i}')
    return i,KS[i]

def sha256(p:Path):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1<<20),b''):h.update(b)
    return h.hexdigest()

def load_text(path:Path, column:str|None):
    if path.suffix.lower() in ('.tsv','.csv'):
        delim='\t' if path.suffix.lower()=='.tsv' else ','
        with path.open(encoding='utf-8-sig',newline='') as f:
            rows=list(csv.DictReader(f,delimiter=delim))
        if not rows:return '',0
        if column is None:
            names=[n for n in rows[0] if n]
            preferred=['korean','ko','korean_current','translation','translated_text','ko_text']
            low={n.lower():n for n in names}
            for x in preferred:
                if x in low:
                    column=low[x];break
        if not column or column not in rows[0]:
            raise ValueError('cannot locate Korean column; pass --column')
        return '\n'.join(r.get(column,'') or '' for r in rows),len(rows)
    return path.read_text(encoding='utf-8-sig'),None

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--corpus',type=Path)
    ap.add_argument('--column')
    ap.add_argument('-o','--out',type=Path,default=Path('MMR_KS2350_IDENTITY_GATE.json'))
    ap.add_argument('--ledger',type=Path,default=Path('MMR_KS2350_IDENTITY_LEDGER.tsv'))
    a=ap.parse_args()

    failures=[]
    ledger=[]
    seen_tokens=set()
    for i,ch in enumerate(KS):
        tok=token_for_id(i)
        rid,rch=decode_token(tok)
        euc=ch.encode('euc_kr')
        ok=(rid==i and rch==ch)
        if not ok: failures.append({'id':i,'char':ch,'reason':'ROUNDTRIP_MISMATCH','decoded_id':rid,'decoded_char':rch})
        if tok in seen_tokens: failures.append({'id':i,'char':ch,'reason':'TOKEN_COLLISION'})
        seen_tokens.add(tok)
        ledger.append({'id':i,'char':ch,'unicode':f'U+{ord(ch):04X}','euc_kr':euc.hex().upper(),
                       'private_token':' '.join(f'{x:02X}' for x in tok),'roundtrip_char':rch,'pass':ok})

    corpus_info=None
    outside=[]
    counts=Counter()
    critical={}
    if a.corpus:
        text,row_count=load_text(a.corpus,a.column)
        for ch in HANGUL_RE.findall(text):
            counts[ch]+=1
            if ch not in CHAR_TO_ID:outside.append(ch)
        for ch in sorted(counts):
            if ch in CHAR_TO_ID:
                i=CHAR_TO_ID[ch];tok=token_for_id(i);rid,rch=decode_token(tok)
                if rch!=ch: failures.append({'char':ch,'reason':'CORPUS_CHAR_ROUNDTRIP_MISMATCH','decoded_char':rch})
        corpus_info={'name':a.corpus.name,'sha256':sha256(a.corpus),'rows':row_count,
                     'hangul_occurrences':sum(counts.values()),'unique_hangul':len(counts),
                     'outside_ks2350_unique':sorted(set(outside))}
        if outside: failures.append({'reason':'CORPUS_CONTAINS_HANGUL_OUTSIDE_KS2350','chars':sorted(set(outside))})

    # Explicit regression sentinels for the user's observed failure family.
    for ch in ('한','힌','이','히'):
        i=CHAR_TO_ID[ch];tok=token_for_id(i);rid,rch=decode_token(tok)
        critical[ch]={'id':i,'token':' '.join(f'{x:02X}' for x in tok),'decoded':rch,'pass':rch==ch}
        if rch!=ch: failures.append({'char':ch,'reason':'CRITICAL_SENTINEL_MISMATCH','decoded':rch})

    with a.ledger.open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(ledger[0]),delimiter='\t',lineterminator='\n');w.writeheader();w.writerows(ledger)

    report={
      'schema':'MMR_KS2350_IDENTITY_GATE_V1',
      'classification':'PASS_KS2350_IDENTITY' if not failures else 'FAIL_KS2350_IDENTITY',
      'ks_order':'EUC-KR B0A1..C8FE row-major','glyphs':TOTAL,'unique_tokens':len(seen_tokens),
      'all_roundtrip':not any(x.get('reason') in ('ROUNDTRIP_MISMATCH','TOKEN_COLLISION') for x in failures),
      'critical_sentinels':critical,'corpus':corpus_info,'failures':failures,
      'note':'This proves encoder/token/id/character identity only. Runtime glyph-bank bytes are checked separately.'
    }
    a.out.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False,indent=2))
    raise SystemExit(0 if not failures else 2)

if __name__=='__main__':main()
