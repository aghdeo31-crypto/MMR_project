#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""MMR name-entry 4-page ROM binding gate.

Builds the expected 200 logical name-entry characters in KS X 1001 order and
encodes each as the confirmed private token form 08 hi lo where:
  id=(hi-1)*160+(lo-0x60)

For an exact candidate ROM, searches each 50-character page byte sequence
(150 bytes/page) and the concatenated 4-page sequence (600 bytes).

This is a static identity gate only. It does not prove runtime code actually
selects these tables; runtime visible-glyph identity remains required.
No ROM writes.
"""
from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path

PAGES=[
["김","이","박","최","정","강","조","윤","장","임","한","오","서","신","권","황","안","송","전","홍","유","류","고","문","양","손","배","백","허","남","심","노","하","곽","성","차","주","우","구","민","진","지","원","천","방","공","현","채","은","예"],
["준","연","수","영","희","재","호","태","도","시","아","혜","경","상","철","광","기","대","종","창","용","석","선","빈","율","린","다","미","가","온","동","별","찬","훈","웅","범","인","근","효","혁","형","승","나","솔","로","라","루","리","소","해"],
["레","드","울","프","비","트","메","스","모","키","토","버","밴","티","거","에","브","럼","탱","크","카","코","맘","플","데","타","랙","터","헌","론","디","그","파","르","헤","처","판","셔","먼","제","더","랑","켄","살","넬","롬","멜","체","펠","료"],
["포","총","검","칼","폭","풍","불","물","암","흑","붉","악","왕","사","막","늑","여","요","무","법","자","탄","약","화","염","빙","설","괴","마","냥","꾼","야","와","게","롯","삭","샘","저","탈","맥","턴","갑","옥","결","켓","즈","복","말","새","의"]
]

def sha(b):return hashlib.sha256(b).hexdigest()

def ks2350():
    return [bytes((a,b)).decode("euc_kr") for a in range(0xB0,0xC9) for b in range(0xA1,0xFF)]
KS=ks2350();C2I={c:i for i,c in enumerate(KS)}

def token(ch):
    i=C2I[ch];hi=i//160+1;lo=i%160+0x60
    return bytes((0x08,hi,lo))

def find_all(blob,needle):
    out=[];start=0
    while True:
        p=blob.find(needle,start)
        if p<0:return out
        out.append(p);start=p+1

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--rom",type=Path,required=True)
    ap.add_argument("--expected-sha256",required=True)
    ap.add_argument("-o","--out",type=Path,required=True)
    a=ap.parse_args();rom=a.rom.read_bytes();got=sha(rom)
    if got.lower()!=a.expected_sha256.lower():raise SystemExit(f"REFUSED ROM SHA mismatch {got}")
    flat=[c for p in PAGES for c in p]
    if len(flat)!=200 or len(set(flat))!=200:raise SystemExit("logical table not 200 unique chars")
    missing=[c for c in flat if c not in C2I]
    if missing:raise SystemExit("chars outside KS2350:"+''.join(missing))
    pages=[]
    for n,p in enumerate(PAGES,1):
        seq=b''.join(token(c) for c in p);hits=find_all(rom,seq)
        pages.append({"page":n,"bytes":len(seq),"sha256":sha(seq),
                      "exact_hits":[f"0x{x:06X}" for x in hits],"hit_count":len(hits)})
    allseq=b''.join(b''.join(token(c) for c in p) for p in PAGES);allhits=find_all(rom,allseq)
    sent={}
    for ch in ("한","힌","이","히","탄","약","보","급"):
        i=C2I[ch];t=token(ch)
        sent[ch]={"id":i,"token":' '.join(f"{x:02X}" for x in t),"rom_hits":len(find_all(rom,t))}
    all_page_unique=all(x["hit_count"]==1 for x in pages)
    contiguous_unique=len(allhits)==1
    cls="PASS_NAME_ENTRY_ROM_BINDING_EXACT" if all_page_unique else "HOLD_NAME_ENTRY_ROM_BINDING_NOT_EXACT"
    report={
      "schema":"MMR_NAME_ENTRY_ROM_BINDING_GATE_V1",
      "classification":cls,
      "candidate":{"name":a.rom.name,"bytes":len(rom),"sha256":got},
      "logical_chars":200,"unique_chars":200,"encoding":"private08 08 hi lo / KS2350 id",
      "pages":pages,
      "concatenated_600_bytes":{"sha256":sha(allseq),"exact_hits":[f"0x{x:06X}" for x in allhits],"hit_count":len(allhits)},
      "all_pages_have_one_exact_hit":all_page_unique,
      "all_pages_contiguous_one_exact_hit":contiguous_unique,
      "sentinels":sent,
      "runtime_binding_proven":False,
      "rule":"PASS proves exact 50-entry page payloads exist once each in this ROM. Runtime cursor/index -> page payload selection must still be observed separately."
    }
    a.out.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps(report,ensure_ascii=False,indent=2))
    raise SystemExit(0 if cls.startswith("PASS") else 2)
if __name__=="__main__":main()
