#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""MMR Mona10 System/UI Custom v0.2 builder.

Full KS X 1001 Hangul coverage for compact system/UI candidates.
This is separate from the name-entry 200-char logical table, although it uses
the same native Mona10 Regular base and the same conservative jamo-aware art
rules.

Base:
- Mona10 Regular native 10px
- 10x12 neutral raster
- y=0
- horizontal centering
- no geometric scaling

v0.2 targeted rules only trigger when a structurally related counterpart is
dangerously close (<=2 pixel Hamming distance):
- ㅓ vs ㅣ: extend the ㅓ arm by 1 pixel toward the consonant side.
- ㅡ vs ㅗ: shorten the ㅡ bar below the ㅗ stem symmetrically.
- ㅕ vs ㅓ: strengthen the second ㅕ arm by 1 pixel.

No ROM/IPS writes. This does not claim which UI surface uses 10px; Japanese
original surface measurement remains authority.
"""
from __future__ import annotations
import argparse,csv,hashlib,json
from collections import Counter,defaultdict
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont

W,H=10,12
PX=10
YOFF=0

def sha256(p:Path)->str:
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1<<20),b''):h.update(b)
    return h.hexdigest()

def ks2350():
    out=[]
    for a in range(0xB0,0xC9):
        for b in range(0xA1,0xFF):
            out.append(bytes((a,b)).decode('euc_kr'))
    assert len(out)==2350 and out[0]=='가' and out[-1]=='힝'
    return out

def dec(ch):
    n=ord(ch)-0xAC00
    return n//588,(n%588)//28,n%28

def counterpart(ch,vnew):
    l,v,t=dec(ch)
    return chr(0xAC00+l*588+vnew*28+t)

def render(font,ch):
    tmp=Image.new('1',(32,24),0)
    ImageDraw.Draw(tmp).text((8,YOFF),ch,font=font,fill=1)
    bb=tmp.getbbox()
    if not bb:return Image.new('1',(W,H),0),True
    x0,y0,x1,y1=bb;x0-=8;x1-=8
    xoff=(W-(x1-x0))//2-x0
    clip=(x0+xoff<0 or x1+xoff>W or y0<0 or y1>H)
    im=Image.new('1',(W,H),0)
    ImageDraw.Draw(im).text((xoff,YOFF),ch,font=font,fill=1)
    return im,clip

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
    if v!=4:return im,None
    ref=counterpart(ch,20) # ㅣ
    if ref not in base:return im,None
    rim=base[ref];before=hd(im,rim)
    if before>2:return im,None
    p=im.load();pr=rim.load();byrow=defaultdict(list)
    for y in range(H):
        for x in range(W):
            if p[x,y] and not pr[x,y]:byrow[y].append(x)
    if not byrow:return im,None
    y,xs=max(byrow.items(),key=lambda kv:len(kv[1]));xmin=min(xs)
    out=im.copy();q=out.load()
    for x in range(xmin-1,-1,-1):
        if not q[x,y]:
            q[x,y]=1
            return out,{'rule':'EO_ARM_EXTEND','ref':ref,'row':y,'x':x,'before':before,'after':hd(out,rim)}
    return im,None

def tweak_eu(ch,im,base):
    l,v,t=dec(ch)
    if v!=18:return im,None
    ref=counterpart(ch,8) # ㅗ
    if ref not in base:return im,None
    rim=base[ref];before=hd(im,rim)
    if before>2:return im,None
    p=im.load();pr=rim.load()
    diff_ref=[(x,y) for y in range(H) for x in range(W) if pr[x,y] and not p[x,y]]
    if not diff_ref:return im,None
    maxy=max(y for x,y in diff_ref)
    out=im.copy();q=out.load()
    for y in range(maxy+1,H):
        xs=[x for x in range(W) if p[x,y] and pr[x,y]]
        if not xs:continue
        runs=[];s=prev=xs[0]
        for x in xs[1:]:
            if x==prev+1:prev=x
            else:runs.append((s,prev));s=prev=x
        runs.append((s,prev))
        r=max(runs,key=lambda z:z[1]-z[0]+1)
        if r[1]-r[0]+1>=6:
            q[r[0],y]=0;q[r[1],y]=0
            return out,{'rule':'EU_VS_O_BAR_TRIM','ref':ref,'row':y,'old':[r[0],r[1]],'new':[r[0]+1,r[1]-1],'before':before,'after':hd(out,rim)}
    return im,None

def tweak_yeo(ch,im,base):
    l,v,t=dec(ch)
    if v!=6:return im,None
    ref=counterpart(ch,4) # ㅓ
    if ref not in base:return im,None
    rim=base[ref];before=hd(im,rim)
    if before>2:return im,None
    p=im.load();pr=rim.load()
    unique=[(x,y) for y in range(H) for x in range(W) if p[x,y] and not pr[x,y]]
    if not unique:return im,None
    y=max(y for x,y in unique);xs=sorted(x for x,yy in unique if yy==y)
    target=min(xs)-1
    if target<0 or p[target,y]:return im,None
    out=im.copy();q=out.load();q[target,y]=1
    return out,{'rule':'YEO_SECOND_ARM_EXTEND','ref':ref,'row':y,'x':target,'before':before,'after':hd(out,rim)}

def one_jamo_pairs(chars,bmap,maxd=3):
    groups=[defaultdict(list),defaultdict(list),defaultdict(list)]
    for ch in chars:
        l,v,t=dec(ch)
        groups[0][(v,t)].append(ch)
        groups[1][(l,t)].append(ch)
        groups[2][(l,v)].append(ch)
    seen=set();out=[]
    for g in groups:
        for vals in g.values():
            for i in range(len(vals)):
                for j in range(i+1,len(vals)):
                    a,b=vals[i],vals[j];key=tuple(sorted((a,b)))
                    if key in seen:continue
                    seen.add(key)
                    d=(bmap[a]^bmap[b]).bit_count()
                    if d<=maxd:out.append((d,key[0],key[1]))
    return sorted(out)

def atlas(chars,glyphs,cols=47,scale=2):
    rows=(len(chars)+cols-1)//cols
    im=Image.new('1',(cols*W,rows*H),0)
    for i,ch in enumerate(chars):im.paste(glyphs[ch],((i%cols)*W,(i//cols)*H))
    return im.resize((im.width*scale,im.height*scale),Image.Resampling.NEAREST)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--font',type=Path,required=True)
    ap.add_argument('--out',type=Path,required=True)
    a=ap.parse_args();a.out.mkdir(parents=True,exist_ok=True)
    font=ImageFont.truetype(str(a.font),PX);chars=ks2350()
    base={};clips=[]
    for ch in chars:
        im,cl=render(font,ch);base[ch]=im
        if cl:clips.append(ch)
    custom={ch:base[ch].copy() for ch in chars};changes=[]
    for ch in chars:
        im=custom[ch]
        for fn in (tweak_eo,tweak_eu,tweak_yeo):
            im,meta=fn(ch,im,base)
            if meta:changes.append({'char':ch,**meta})
        custom[ch]=im
    blank=[ch for ch,im in custom.items() if not im.getbbox()]
    rev=defaultdict(list)
    for ch,im in custom.items():rev[bits(im)].append(ch)
    dup=[v for v in rev.values() if len(v)>1]
    base_b={ch:bits(im) for ch,im in base.items()}
    cust_b={ch:bits(im) for ch,im in custom.items()}
    base_pairs=one_jamo_pairs(chars,base_b,3)
    cust_pairs=one_jamo_pairs(chars,cust_b,3)
    metrics=[]
    for ch in chars:
        bb=custom[ch].getbbox()
        metrics.append({'char':ch,'unicode':f'U+{ord(ch):04X}','euc_kr':ch.encode('euc_kr').hex().upper(),
                        'bbox_w':bb[2]-bb[0],'bbox_h':bb[3]-bb[1],
                        'set_pixels':sum(custom[ch].getdata())})
    with (a.out/'MMR_Mona10_UI_Custom_v0.2_KS2350_index.tsv').open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(metrics[0]),delimiter='\t',lineterminator='\n');w.writeheader();w.writerows(metrics)
    with (a.out/'MMR_Mona10_UI_Custom_v0.2_changes.tsv').open('w',encoding='utf-8-sig',newline='') as f:
        fields=['char','rule','ref','row','x','old','new','before','after']
        w=csv.DictWriter(f,fieldnames=fields,delimiter='\t',lineterminator='\n');w.writeheader()
        for r in changes:
            q={k:r.get(k,'') for k in fields}
            if isinstance(q['old'],list):q['old']=','.join(map(str,q['old']))
            if isinstance(q['new'],list):q['new']=','.join(map(str,q['new']))
            w.writerow(q)
    atlas(chars,custom).save(a.out/'MMR_Mona10_UI_Custom_v0.2_KS2350_atlas.png')
    report={
      'schema':'MMR_MONA10_UI_CUSTOM_V0_2_KS2350_QA',
      'classification':'PASS_STATIC_SMALL_UI_FONT_CANDIDATE__SURFACE_MAPPING_PENDING' if not (blank or clips or dup) else 'FAIL_SMALL_UI_FONT_STRUCTURE',
      'base_font':a.font.name,'base_font_sha256':sha256(a.font),
      'font_px':PX,'raster_candidate':[W,H],'y_offset':YOFF,'geometric_scaling':False,
      'ks2350':len(chars),'blank':len(blank),'clipped':len(clips),'duplicate_bitmap_groups':len(dup),
      'changed_glyphs':len(changes),
      'bbox_width_counts':dict(Counter(x['bbox_w'] for x in metrics)),
      'bbox_height_counts':dict(Counter(x['bbox_h'] for x in metrics)),
      'mean_set_pixels':sum(x['set_pixels'] for x in metrics)/len(metrics),
      'one_jamo_neighbor_counts_regular':{str(k):sum(d<=k for d,_,_ in base_pairs) for k in (1,2,3)},
      'one_jamo_neighbor_counts_custom':{str(k):sum(d<=k for d,_,_ in cust_pairs) for k in (1,2,3)},
      'surface_mapping':'UNRESOLVED__JP_ORIGINAL_PER_SURFACE_MEASUREMENT_REQUIRED',
      'rule':'This font is only a full-coverage compact candidate. Do not bind any UI renderer/surface before original-JP size/route measurement.'
    }
    (a.out/'MMR_MONA10_UI_CUSTOM_V0_2_KS2350_QA.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False,indent=2))
    raise SystemExit(0 if report['classification'].startswith('PASS') else 2)

if __name__=='__main__':main()
