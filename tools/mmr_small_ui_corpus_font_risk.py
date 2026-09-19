#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""MMR compact UI corpus font-risk gate.

Input TSV columns:
  surface_id    korean_text    font_family
Optional:
  source_note

Required P0 surfaces:
  MEMORY_CENTER_NOTICE
  RECORD_SELECTION
  MAIN_MENU
  ITEM_EQUIPMENT_STATUS
  SHOP_SERVICE_UI
  BATTLE_UI
  SAVE_LOAD_UI

The tool:
- extracts actual Hangul used by P0 UI surfaces;
- verifies all used chars are inside KS X 1001 2350;
- renders Mona10 Regular / MMR v0.2 compact candidate;
- reports dangerously close used-char pairs by pixel Hamming distance;
- prioritizes pairs when both chars occur in the same surface.

No ROM writes. This is a usage-risk inventory, not runtime proof.
"""
from __future__ import annotations
import argparse,csv,hashlib,json,re
from collections import Counter,defaultdict
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont

W,H,PX,YOFF=10,12,10,0
P0=[
 "MEMORY_CENTER_NOTICE","RECORD_SELECTION","MAIN_MENU","ITEM_EQUIPMENT_STATUS",
 "SHOP_SERVICE_UI","BATTLE_UI","SAVE_LOAD_UI"
]
HANGUL_RE=re.compile(r'[가-힣]')

def sha256(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()

def ks2350():
 return [bytes((a,b)).decode('euc_kr') for a in range(0xB0,0xC9) for b in range(0xA1,0xFF)]
KS=ks2350();KSSET=set(KS)

def dec(ch):
 n=ord(ch)-0xAC00
 return n//588,(n%588)//28,n%28

def counterpart(ch,vnew):
 l,v,t=dec(ch)
 return chr(0xAC00+l*588+vnew*28+t)

def render(font,ch):
 t=Image.new('1',(32,24),0)
 ImageDraw.Draw(t).text((8,YOFF),ch,font=font,fill=1)
 b=t.getbbox()
 if not b:return Image.new('1',(W,H),0)
 x0,y0,x1,y1=b;x0-=8;x1-=8
 xoff=(W-(x1-x0))//2-x0
 out=Image.new('1',(W,H),0)
 ImageDraw.Draw(out).text((xoff,YOFF),ch,font=font,fill=1)
 return out

def bits(im):
 p=im.load();v=0;k=0
 for y in range(H):
  for x in range(W):
   if p[x,y]:v|=1<<k
   k+=1
 return v

def hd(a,b):return (bits(a)^bits(b)).bit_count()

def tweak_eo(ch,im,base):
 l,v,t=dec(ch)
 if v!=4:return im
 ref=counterpart(ch,20)
 if ref not in base or hd(im,base[ref])>2:return im
 rim=base[ref];p=im.load();pr=rim.load();byrow=defaultdict(list)
 for y in range(H):
  for x in range(W):
   if p[x,y] and not pr[x,y]:byrow[y].append(x)
 if not byrow:return im
 y,xs=max(byrow.items(),key=lambda kv:len(kv[1]));xmin=min(xs)
 out=im.copy();q=out.load()
 for x in range(xmin-1,-1,-1):
  if not q[x,y]:
   q[x,y]=1;return out
 return im

def tweak_eu(ch,im,base):
 l,v,t=dec(ch)
 if v!=18:return im
 ref=counterpart(ch,8)
 if ref not in base or hd(im,base[ref])>2:return im
 rim=base[ref];p=im.load();pr=rim.load()
 d=[(x,y) for y in range(H) for x in range(W) if pr[x,y] and not p[x,y]]
 if not d:return im
 maxy=max(y for x,y in d);out=im.copy();q=out.load()
 for y in range(maxy+1,H):
  xs=[x for x in range(W) if p[x,y] and pr[x,y]]
  if not xs:continue
  runs=[];s=prev=xs[0]
  for x in xs[1:]:
   if x==prev+1:prev=x
   else:runs.append((s,prev));s=prev=x
  runs.append((s,prev));r=max(runs,key=lambda z:z[1]-z[0]+1)
  if r[1]-r[0]+1>=6:
   q[r[0],y]=0;q[r[1],y]=0;return out
 return im

def tweak_yeo(ch,im,base):
 l,v,t=dec(ch)
 if v!=6:return im
 ref=counterpart(ch,4)
 if ref not in base or hd(im,base[ref])>2:return im
 rim=base[ref];p=im.load();pr=rim.load()
 u=[(x,y) for y in range(H) for x in range(W) if p[x,y] and not pr[x,y]]
 if not u:return im
 y=max(y for x,y in u);xs=sorted(x for x,yy in u if yy==y);target=min(xs)-1
 if target<0 or p[target,y]:return im
 out=im.copy();out.load()[target,y]=1;return out

def main():
 ap=argparse.ArgumentParser()
 ap.add_argument('--ledger',type=Path,required=True)
 ap.add_argument('--font',type=Path,required=True)
 ap.add_argument('--risk-distance',type=int,default=3)
 ap.add_argument('-o','--out',type=Path,required=True)
 a=ap.parse_args()
 with a.ledger.open(encoding='utf-8-sig',newline='') as f:
  rows=list(csv.DictReader(f,delimiter='\t'))
 if not rows:raise SystemExit('empty ledger')
 need={'surface_id','korean_text','font_family'}
 if not need.issubset(rows[0]):raise SystemExit('ledger missing required columns')
 bysurf=defaultdict(Counter);allc=Counter()
 present=set()
 for r in rows:
  sid=(r.get('surface_id') or '').strip()
  present.add(sid)
  for ch in HANGUL_RE.findall(r.get('korean_text') or ''):
   bysurf[sid][ch]+=1;allc[ch]+=1
 missing_surfaces=[x for x in P0 if x not in present]
 outside=sorted(ch for ch in allc if ch not in KSSET)
 font=ImageFont.truetype(str(a.font),PX)
 base={ch:render(font,ch) for ch in KS}
 custom={}
 for ch in KS:
  im=base[ch].copy()
  im=tweak_eo(ch,im,base);im=tweak_eu(ch,im,base);im=tweak_yeo(ch,im,base)
  custom[ch]=im
 bmap={ch:bits(im) for ch,im in custom.items()}
 used=sorted(ch for ch in allc if ch in bmap)
 pairs=[]
 for i,x in enumerate(used):
  for y in used[i+1:]:
   d=(bmap[x]^bmap[y]).bit_count()
   if d>a.risk_distance:continue
   common=[sid for sid in P0 if bysurf[sid].get(x) and bysurf[sid].get(y)]
   ux,uy=allc[x],allc[y]
   pairs.append({
    'a':x,'b':y,'hamming':d,'usage_a':ux,'usage_b':uy,
    'same_p0_surfaces':common,
    'priority':'P0_SAME_SURFACE' if common else 'P1_BOTH_USED'
   })
 pairs.sort(key=lambda r:(0 if r['priority']=='P0_SAME_SURFACE' else 1,r['hamming'],-r['usage_a']-r['usage_b'],r['a'],r['b']))
 per_surface=[]
 for sid in P0:
  c=bysurf[sid]
  per_surface.append({'surface_id':sid,'hangul_occurrences':sum(c.values()),'unique_hangul':len(c),'chars':' '.join(sorted(c))})
 fail=[]
 if missing_surfaces:fail.append({'reason':'MISSING_P0_SURFACES','surfaces':missing_surfaces})
 if outside:fail.append({'reason':'HANGUL_OUTSIDE_KS2350','chars':outside})
 report={
  'schema':'MMR_SMALL_UI_CORPUS_FONT_RISK_V1',
  'classification':'FAIL_UI_CORPUS_INPUT' if fail else 'PASS_UI_CORPUS_INVENTORY__ART_REVIEW_REQUIRED',
  'ledger':a.ledger.name,'ledger_sha256':sha256(a.ledger),
  'font':a.font.name,'font_sha256':sha256(a.font),
  'candidate':'MMR Mona10 UI Custom v0.2',
  'p0_surfaces_required':P0,'p0_surfaces_present':sorted(present & set(P0)),
  'hangul_occurrences':sum(allc.values()),'unique_hangul':len(allc),
  'outside_ks2350':outside,'per_surface':per_surface,
  'risk_distance':a.risk_distance,'risk_pairs':pairs,
  'p0_same_surface_risk_pairs':sum(r['priority']=='P0_SAME_SURFACE' for r in pairs),
  'failures':fail,
  'rule':'Only actual P0 UI corpus pairs are art-review priorities. Do not modify unused KS2350 pairs merely because their base bitmaps are close.'
 }
 a.out.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps(report,ensure_ascii=False,indent=2))
 raise SystemExit(2 if fail else 0)

if __name__=='__main__':main()
