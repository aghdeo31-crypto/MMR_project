#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate and verify the MMR Korean name-entry 200-char logical map.

Output:
 logical index/page/row/column -> intended char -> KS2350 ID -> private token.

This does NOT prove runtime page/table binding. It proves the intended table is
internally exact before ROM insertion.
"""
from __future__ import annotations
import argparse,csv,json
from pathlib import Path

PAGES=[
["김","이","박","최","정","강","조","윤","장","임","한","오","서","신","권","황","안","송","전","홍","유","류","고","문","양","손","배","백","허","남","심","노","하","곽","성","차","주","우","구","민","진","지","원","천","방","공","현","채","은","예"],
["준","연","수","영","희","재","호","태","도","시","아","혜","경","상","철","광","기","대","종","창","용","석","선","빈","율","린","다","미","가","온","동","별","찬","훈","웅","범","인","근","효","혁","형","승","나","솔","로","라","루","리","소","해"],
["레","드","울","프","비","트","메","스","모","키","토","버","밴","티","거","에","브","럼","탱","크","카","코","맘","플","데","타","랙","터","헌","론","디","그","파","르","헤","처","판","셔","먼","제","더","랑","켄","살","넬","롬","멜","체","펠","료"],
["포","총","검","칼","폭","풍","불","물","암","흑","붉","악","왕","사","막","늑","여","요","무","법","자","탄","약","화","염","빙","설","괴","마","냥","꾼","야","와","게","롯","삭","샘","저","탈","맥","턴","갑","옥","결","켓","즈","복","말","새","의"]]

def main():
 ap=argparse.ArgumentParser()
 ap.add_argument('--outdir',type=Path,required=True)
 a=ap.parse_args();a.outdir.mkdir(parents=True,exist_ok=True)
 ks=[bytes((x,y)).decode('euc_kr') for x in range(0xB0,0xC9) for y in range(0xA1,0xFF)]
 cmap={c:i for i,c in enumerate(ks)}
 chars=[c for p in PAGES for c in p]
 fail=[];rows=[];seen=set()
 if len(chars)!=200:fail.append({'reason':'COUNT','value':len(chars)})
 for p,page in enumerate(PAGES,1):
  for n,ch in enumerate(page):
   logical=(p-1)*50+n
   if ch in seen:fail.append({'char':ch,'reason':'DUPLICATE'})
   seen.add(ch)
   if ch not in cmap:
    fail.append({'char':ch,'reason':'NOT_KS2350'});continue
   gid=cmap[ch];hi=gid//160+1;lo=gid%160+0x60
   rid=(hi-1)*160+(lo-0x60);decoded=ks[rid]
   ok=rid==gid and decoded==ch
   if not ok:fail.append({'char':ch,'reason':'ROUNDTRIP','decoded':decoded})
   rows.append({
    'logical_index':logical,'page':p,'row':n//10,'column':n%10,'char':ch,
    'unicode':f'U+{ord(ch):04X}','euc_kr':ch.encode('euc_kr').hex().upper(),
    'ks2350_id':gid,'private_token':f'08 {hi:02X} {lo:02X}',
    'decoded_char':decoded,'roundtrip_pass':ok})
 with (a.outdir/'MMR_NAME_ENTRY_200_LOGICAL_TO_KS2350.tsv').open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]),delimiter='\t',lineterminator='\n');w.writeheader();w.writerows(rows)
 sent={}
 for ch in ('한','힌','이','히','탄','약','보','급'):
  gid=cmap[ch];hi=gid//160+1;lo=gid%160+0x60
  sent[ch]={'id':gid,'token':f'08 {hi:02X} {lo:02X}'}
 rep={
  'schema':'MMR_NAME_ENTRY_200_LOGICAL_MAP_V1',
  'classification':'PASS_NAME_ENTRY_LOGICAL_IDENTITY' if not fail and len(rows)==200 else 'FAIL_NAME_ENTRY_LOGICAL_IDENTITY',
  'logical_chars':200,'unique_chars':len(seen),'mapped_rows':len(rows),
  'roundtrip_failures':fail,'all_in_ks2350':not any(x.get('reason')=='NOT_KS2350' for x in fail),
  'all_roundtrip':all(r['roundtrip_pass'] for r in rows),'sentinels':sent,
  'rule':'logical index -> intended char -> KS2350 ID -> private token must be exact before runtime page binding',
  'runtime_binding_status':'NOT_YET_PROVEN'}
 (a.outdir/'MMR_NAME_ENTRY_200_LOGICAL_MAP_QA.json').write_text(json.dumps(rep,ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps(rep,ensure_ascii=False,indent=2))
 raise SystemExit(0 if rep['classification'].startswith('PASS') else 2)

if __name__=='__main__':main()
