#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""MMR name-entry font — Mona10 Custom v0.2.

Native small-font candidate for the 200-char Korean name table.
Separate from dialogue 12x12.

v0.2 fixes the v0.1 weakness: art edits are counterpart-aware rather than
searching an arbitrary horizontal run.

Rules are only applied when the base pair is <=2 pixels apart:
- ㅓ vs same L/T ㅣ: extend ㅓ arm one pixel toward consonant side
- ㅡ vs same L/T ㅗ: trim the shared ㅡ bar symmetrically below the ㅗ stem
- ㅕ vs same L/T ㅓ: strengthen lower ㅕ arm by one pixel

No geometric scaling. No ROM writes.
"""
from __future__ import annotations
import argparse,csv,hashlib,json
from collections import defaultdict
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont

W,H,PX,YOFF=10,12,10,0
PAGES=[
["김","이","박","최","정","강","조","윤","장","임","한","오","서","신","권","황","안","송","전","홍","유","류","고","문","양","손","배","백","허","남","심","노","하","곽","성","차","주","우","구","민","진","지","원","천","방","공","현","채","은","예"],
["준","연","수","영","희","재","호","태","도","시","아","혜","경","상","철","광","기","대","종","창","용","석","선","빈","율","린","다","미","가","온","동","별","찬","훈","웅","범","인","근","효","혁","형","승","나","솔","로","라","루","리","소","해"],
["레","드","울","프","비","트","메","스","모","키","토","버","밴","티","거","에","브","럼","탱","크","카","코","맘","플","데","타","랙","터","헌","론","디","그","파","르","헤","처","판","셔","먼","제","더","랑","켄","살","넬","롬","멜","체","펠","료"],
["포","총","검","칼","폭","풍","불","물","암","흑","붉","악","왕","사","막","늑","여","요","무","법","자","탄","약","화","염","빙","설","괴","마","냥","꾼","야","와","게","롯","삭","샘","저","탈","맥","턴","갑","옥","결","켓","즈","복","말","새","의"]]
CHARS=[c for p in PAGES for c in p]
assert len(CHARS)==200 and len(set(CHARS))==200

def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()

def dec(ch):
 n=ord(ch)-0xAC00
 return n//588,(n%588)//28,n%28

def cp(ch,vnew):
 l,v,t=dec(ch)
 return chr(0xAC00+l*588+vnew*28+t)

def render(font,ch):
 t=Image.new('1',(32,24),0)
 ImageDraw.Draw(t).text((8,YOFF),ch,font=font,fill=1)
 b=t.getbbox()
 if not b:return Image.new('1',(W,H),0)
 x0,y0,x1,y1=b;x0-=8;x1-=8
 xoff=(W-(x1-x0))//2-x0
 im=Image.new('1',(W,H),0)
 ImageDraw.Draw(im).text((xoff,YOFF),ch,font=font,fill=1)
 return im

def bits(im):
 p=im.load();v=k=0
 for y in range(H):
  for x in range(W):
   if p[x,y]:v|=1<<k
   k+=1
 return v

def dist(a,b):return (bits(a)^bits(b)).bit_count()

def tweak_eo(ch,im,raw):
 if dec(ch)[1]!=4:return im,None
 ref=cp(ch,20)
 if ref not in raw or dist(im,raw[ref])>2:return im,None
 p=im.load();r=raw[ref].load();by=defaultdict(list)
 for y in range(H):
  for x in range(W):
   if p[x,y] and not r[x,y]:by[y].append(x)
 if not by:return im,None
 y,xs=max(by.items(),key=lambda kv:len(kv[1]))
 out=im.copy();q=out.load()
 for x in range(min(xs)-1,-1,-1):
  if not q[x,y]:
   q[x,y]=1
   return out,{'rule':'EO_ARM_EXTEND','ref':ref,'row':y,'x':x}
 return im,None

def tweak_eu(ch,im,raw):
 if dec(ch)[1]!=18:return im,None
 ref=cp(ch,8)
 if ref not in raw or dist(im,raw[ref])>2:return im,None
 p=im.load();r=raw[ref].load()
 diff=[(x,y) for y in range(H) for x in range(W) if r[x,y] and not p[x,y]]
 if not diff:return im,None
 maxy=max(y for x,y in diff)
 for y in range(maxy+1,H):
  xs=[x for x in range(W) if p[x,y] and r[x,y]]
  if not xs:continue
  runs=[];s=pr=xs[0]
  for x in xs[1:]:
   if x==pr+1:pr=x
   else:runs.append((s,pr));s=pr=x
  runs.append((s,pr));rr=max(runs,key=lambda z:z[1]-z[0]+1)
  if rr[1]-rr[0]+1>=6:
   out=im.copy();q=out.load();q[rr[0],y]=0;q[rr[1],y]=0
   return out,{'rule':'EU_VS_O_BAR_TRIM','ref':ref,'row':y,'old':[rr[0],rr[1]],'new':[rr[0]+1,rr[1]-1]}
 return im,None

def tweak_yeo(ch,im,raw):
 if dec(ch)[1]!=6:return im,None
 ref=cp(ch,4)
 if ref not in raw or dist(im,raw[ref])>2:return im,None
 p=im.load();r=raw[ref].load()
 unique=[(x,y) for y in range(H) for x in range(W) if p[x,y] and not r[x,y]]
 if not unique:return im,None
 y=max(y for x,y in unique);xs=[x for x,yy in unique if yy==y]
 x=min(xs)-1
 if x<0 or p[x,y]:return im,None
 out=im.copy();out.putpixel((x,y),1)
 return out,{'rule':'YEO_SECOND_ARM_EXTEND','ref':ref,'row':y,'x':x}

def main():
 ap=argparse.ArgumentParser()
 ap.add_argument('--font',type=Path,required=True)
 ap.add_argument('--out',type=Path,required=True)
 a=ap.parse_args();a.out.mkdir(parents=True,exist_ok=True)
 font=ImageFont.truetype(str(a.font),PX)
 raw={c:render(font,c) for c in CHARS}
 glyph={};changes=[]
 for c in CHARS:
  im=raw[c].copy()
  for fn in (tweak_eo,tweak_eu,tweak_yeo):
   im,m=fn(c,im,raw)
   if m:changes.append({'char':c,**m})
  glyph[c]=im

 blank=[c for c,i in glyph.items() if not i.getbbox()]
 rev=defaultdict(list)
 for c,i in glyph.items():rev[bits(i)].append(c)
 dup=[v for v in rev.values() if len(v)>1]
 pairs=[]
 for i,x in enumerate(CHARS):
  for y in CHARS[i+1:]:
   d=(bits(glyph[x])^bits(glyph[y])).bit_count()
   if d<=3:pairs.append((d,x,y))
 pairs.sort()
 low2=[p for p in pairs if p[0]<=2]

 with (a.out/'MMR_NameFont_Mona10_Custom_v0.2_changes.tsv').open('w',encoding='utf-8-sig',newline='') as f:
  fields=['char','rule','ref','row','x','old','new']
  w=csv.DictWriter(f,fieldnames=fields,delimiter='\t',lineterminator='\n');w.writeheader()
  for r in changes:
   q={k:r.get(k,'') for k in fields}
   for k in ('old','new'):
    if isinstance(q[k],list):q[k]=','.join(map(str,q[k]))
   w.writerow(q)

 report={
  'schema':'MMR_NAME_FONT_MONA10_CUSTOM_V0_2_QA',
  'classification':'PASS_STATIC_NAME_FONT_CANDIDATE__ORIGINAL_GEOMETRY_REQUIRED' if not blank and not dup else 'FAIL_STRUCTURE',
  'font':a.font.name,'font_sha256':sha(a.font),'font_px':PX,'raster':[W,H],
  'logical_chars':200,'blank':len(blank),'duplicate_bitmap_groups':len(dup),
  'distance_le_1':sum(d<=1 for d,x,y in pairs),'distance_le_2':len(low2),
  'remaining_le_2':[{'a':x,'b':y,'distance':d} for d,x,y in low2],
  'changes':changes,
  'cursor_geometry':'UNRESOLVED__JP_ORIGINAL_REQUIRED',
  'release_status':'HOLD'}
 (a.out/'MMR_NAME_FONT_MONA10_CUSTOM_V0_2_QA.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps(report,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
