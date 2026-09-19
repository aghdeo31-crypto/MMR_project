#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""MMR Mona12 Custom v0.1 raster builder.

Base:
- Mona12 Regular
- 12px / 12x12
- y=-1
- horizontal centering

MMR-specific art rule v0.1:
- For syllables whose medial vowel is ㅡ (U+1173 / Jungseong EU), locate the
  dominant horizontal vowel run in rows 2..7.
- If that run is >=9 px, trim exactly one pixel from each end.
- Do not geometrically scale any glyph.

Reason:
Mona12's ㅗ/ㅜ/ㅛ/ㅠ vs ㅡ families can differ by only one stem pixel in a
crowded 12x12 syllable. Narrowing the ㅡ bar preserves its visual identity while
increasing separation from horizontal-vowel neighbors.

This tool creates neutral raster/native12 source assets only. It does not write
a ROM and does not choose MMR vertical-bit orientation.
"""
from __future__ import annotations
import argparse,csv,hashlib,json
from collections import defaultdict
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont

CELL=12; PX=12; YOFF=-1; V_EU=18

def sha256(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(1<<20),b''):h.update(b)
    return h.hexdigest()

def ks2350():
    return [bytes((a,b)).decode('euc_kr') for a in range(0xB0,0xC9) for b in range(0xA1,0xFF)]

def dec(ch):
    n=ord(ch)-0xAC00
    return n//588,(n%588)//28,n%28

def render(font,ch):
    t=Image.new('1',(32,20),0)
    ImageDraw.Draw(t).text((8,YOFF),ch,font=font,fill=1)
    b=t.getbbox()
    if not b:return Image.new('1',(CELL,CELL),0),True
    x0,y0,x1,y1=b;x0-=8;x1-=8
    xoff=(CELL-(x1-x0))//2-x0
    clip=x0+xoff<0 or x1+xoff>CELL or y0<0 or y1>CELL
    out=Image.new('1',(CELL,CELL),0)
    ImageDraw.Draw(out).text((xoff,YOFF),ch,font=font,fill=1)
    return out,clip

def longest_run(xs):
    if not xs:return None
    s=p=xs[0];runs=[]
    for x in xs[1:]:
        if x==p+1:p=x
        else:runs.append((s,p));s=p=x
    runs.append((s,p))
    return max(runs,key=lambda r:r[1]-r[0]+1)

def eu_trim(im):
    out=im.copy();p=out.load();best=None
    for y in range(2,8):
        xs=[x for x in range(CELL) if p[x,y]]
        r=longest_run(xs)
        if not r:continue
        ln=r[1]-r[0]+1
        if best is None or ln>best[0]:best=(ln,y,r[0],r[1])
    if best and best[0]>=9:
        _,y,x0,x1=best
        p[x0,y]=0;p[x1,y]=0
        return out,True,{'row':y,'old_run':[x0,x1],'new_run':[x0+1,x1-1]}
    return out,False,None

def bits(im):
    p=im.load();v=0;k=0
    for y in range(CELL):
        for x in range(CELL):
            if p[x,y]:v|=1<<k
            k+=1
    return v

def one_jamo_dist(chars,bb):
    groups=[defaultdict(list),defaultdict(list),defaultdict(list)]
    for ch in chars:
        l,v,t=dec(ch)
        groups[0][(v,t)].append(ch);groups[1][(l,t)].append(ch);groups[2][(l,v)].append(ch)
    seen=set();d=[]
    for g in groups:
        for vals in g.values():
            for i in range(len(vals)):
                for j in range(i+1,len(vals)):
                    key=tuple(sorted((vals[i],vals[j])))
                    if key in seen:continue
                    seen.add(key);d.append((bb[key[0]]^bb[key[1]]).bit_count())
    return {str(k):sum(x<=k for x in d) for k in (1,2,3,4,5,6,8,10)}

def make_atlas(glyphs,cols=47,scale=3):
    rows=(len(glyphs)+cols-1)//cols
    a=Image.new('1',(cols*CELL,rows*CELL),0)
    for i,g in enumerate(glyphs):a.paste(g,((i%cols)*CELL,(i//cols)*CELL))
    return a.resize((a.width*scale,a.height*scale),Image.Resampling.NEAREST)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--font',type=Path,required=True)
    ap.add_argument('--out',type=Path,required=True)
    a=ap.parse_args();a.out.mkdir(parents=True,exist_ok=True)
    font=ImageFont.truetype(str(a.font),PX);chars=ks2350()
    base={};custom={};clips=[];blank=[];changes=[]
    for ch in chars:
        im,cl=render(font,ch);base[ch]=im
        if cl:clips.append(ch)
        if not im.getbbox():blank.append(ch)
        _,v,_=dec(ch)
        if v==V_EU:
            out,changed,meta=eu_trim(im)
            if changed:changes.append({'char':ch,'unicode':f'U+{ord(ch):04X}',**meta})
            custom[ch]=out
        else:custom[ch]=im.copy()
    b0={ch:bits(im) for ch,im in base.items()}
    b1={ch:bits(im) for ch,im in custom.items()}
    rev=defaultdict(list)
    for ch,v in b1.items():rev[v].append(ch)
    dup=[v for v in rev.values() if len(v)>1]
    sent={}
    for x,y in [('한','힌'),('한','이'),('이','히'),('개','게'),('애','에'),('독','득'),('눅','늑'),('종','증'),('용','응'),('돌','들'),('둘','들'),('굴','글')]:
        sent[x+'/'+y]={'base':(b0[x]^b0[y]).bit_count(),'custom':(b1[x]^b1[y]).bit_count()}
    base_dist=one_jamo_dist(chars,b0);custom_dist=one_jamo_dist(chars,b1)
    imgs=[custom[ch] for ch in chars]
    make_atlas(imgs).save(a.out/'MMR_Mona12_Custom_v0.1_KS2350_atlas.png')
    with (a.out/'MMR_Mona12_Custom_v0.1_changes.tsv').open('w',encoding='utf-8-sig',newline='') as f:
        fields=['char','unicode','row','old_run','new_run']
        w=csv.DictWriter(f,fieldnames=fields,delimiter='\t',lineterminator='\n');w.writeheader()
        for r in changes:
            q=dict(r);q['old_run']=','.join(map(str,q['old_run']));q['new_run']=','.join(map(str,q['new_run']));w.writerow(q)
    report={
      'schema':'MMR_MONA12_CUSTOM_V0_1_QA',
      'classification':'PASS_STATIC_CUSTOM_CANDIDATE' if not (clips or blank or dup) else 'FAIL_STRUCTURE',
      'base_font':a.font.name,'base_font_sha256':sha256(a.font),
      'cell':[12,12],'font_px':12,'y_offset':-1,'horizontal':'centered',
      'rule':'EU_TRIM_1PX_EACH_END_ON_DOMINANT_RUN_GE9',
      'ks2350':2350,'changed_glyphs':len(changes),
      'blank':len(blank),'clipped':len(clips),'duplicate_bitmap_groups':len(dup),
      'one_jamo_neighbor_counts_base':base_dist,
      'one_jamo_neighbor_counts_custom':custom_dist,
      'sentinels':sent,
      'art_status':'CANDIDATE_REQUIRES_GAME_CORPUS_P0_REVIEW_AND_RUNTIME_CAPTURE',
      'rom_written':False
    }
    (a.out/'MMR_Mona12_Custom_v0.1_QA.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
