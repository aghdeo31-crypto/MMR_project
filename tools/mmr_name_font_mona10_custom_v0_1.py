#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""MMR name-entry small-font builder — Mona10 Custom v0.1.

This is intentionally separate from the 12x12 dialogue font.

Candidate:
- Mona10 Regular native 10px
- glyph raster canvas 10x12
- centered horizontally
- y=0
- NO geometric scaling
- 200 logical name-entry syllables only

Important:
10x12 is a raster candidate, NOT a final cursor/cell geometry claim.
The Japanese original must determine the physical row step, cursor rectangle,
anchor, and screen-cell pitch.

MMR custom v0.1 art rule:
For Jungseong ㅡ syllables, locate the dominant horizontal vowel run in rows
2..7. If it is >=8 pixels, trim exactly one endpoint pixel from both ends.
This improves separation from ㅗ/ㅜ/ㅛ/ㅠ families in a small raster.

No ROM/IPS writes.
"""
from __future__ import annotations
import argparse,csv,hashlib,json
from collections import Counter
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont

CELL_W=10
CELL_H=12
FONT_PX=10
YOFF=0
V_EU=18

PAGES=[
["김","이","박","최","정","강","조","윤","장","임",
 "한","오","서","신","권","황","안","송","전","홍",
 "유","류","고","문","양","손","배","백","허","남",
 "심","노","하","곽","성","차","주","우","구","민",
 "진","지","원","천","방","공","현","채","은","예"],
["준","연","수","영","희","재","호","태","도","시",
 "아","혜","경","상","철","광","기","대","종","창",
 "용","석","선","빈","율","린","다","미","가","온",
 "동","별","찬","훈","웅","범","인","근","효","혁",
 "형","승","나","솔","로","라","루","리","소","해"],
["레","드","울","프","비","트","메","스","모","키",
 "토","버","밴","티","거","에","브","럼","탱","크",
 "카","코","맘","플","데","타","랙","터","헌","론",
 "디","그","파","르","헤","처","판","셔","먼","제",
 "더","랑","켄","살","넬","롬","멜","체","펠","료"],
["포","총","검","칼","폭","풍","불","물","암","흑",
 "붉","악","왕","사","막","늑","여","요","무","법",
 "자","탄","약","화","염","빙","설","괴","마","냥",
 "꾼","야","와","게","롯","삭","샘","저","탈","맥",
 "턴","갑","옥","결","켓","즈","복","말","새","의"]
]

def sha256(p:Path)->str:
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1<<20),b''):
            h.update(b)
    return h.hexdigest()

def dec(ch:str):
    n=ord(ch)-0xAC00
    return n//588,(n%588)//28,n%28

def intrinsic_bbox(font,ch):
    t=Image.new('1',(32,24),0)
    ImageDraw.Draw(t).text((8,YOFF),ch,font=font,fill=1)
    b=t.getbbox()
    if not b:return None
    return (b[0]-8,b[1],b[2]-8,b[3])

def render(font,ch):
    b=intrinsic_bbox(font,ch)
    if not b:return Image.new('1',(CELL_W,CELL_H),0),True
    x0,y0,x1,y1=b
    w=x1-x0
    xoff=(CELL_W-w)//2-x0
    clip=(x0+xoff<0 or x1+xoff>CELL_W or y0<0 or y1>CELL_H)
    im=Image.new('1',(CELL_W,CELL_H),0)
    ImageDraw.Draw(im).text((xoff,YOFF),ch,font=font,fill=1)
    return im,clip

def longest_run(xs):
    if not xs:return None
    runs=[]
    s=p=xs[0]
    for x in xs[1:]:
        if x==p+1:p=x
        else:runs.append((s,p));s=p=x
    runs.append((s,p))
    return max(runs,key=lambda r:r[1]-r[0]+1)

def eu_trim(im):
    out=im.copy();p=out.load();best=None
    for y in range(2,8):
        xs=[x for x in range(CELL_W) if p[x,y]]
        r=longest_run(xs)
        if not r:continue
        ln=r[1]-r[0]+1
        if best is None or ln>best[0]:
            best=(ln,y,r[0],r[1])
    if best and best[0]>=8:
        _,y,x0,x1=best
        p[x0,y]=0
        p[x1,y]=0
        return out,True,{'row':y,'old_run':[x0,x1],'new_run':[x0+1,x1-1]}
    return out,False,None

def bits(im):
    p=im.load();v=0;k=0
    for y in range(CELL_H):
        for x in range(CELL_W):
            if p[x,y]:v|=1<<k
            k+=1
    return v

def make_page(glyphs,scale=4):
    a=Image.new('1',(10*CELL_W,5*CELL_H),0)
    for i,ch in enumerate(glyphs):
        a.paste(glyphs[ch],((i%10)*CELL_W,(i//10)*CELL_H))
    return a.resize((a.width*scale,a.height*scale),Image.Resampling.NEAREST)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--font',type=Path,required=True)
    ap.add_argument('--out',type=Path,required=True)
    a=ap.parse_args();a.out.mkdir(parents=True,exist_ok=True)
    font=ImageFont.truetype(str(a.font),FONT_PX)
    chars=[c for p in PAGES for c in p]
    if len(chars)!=200 or len(set(chars))!=200:
        raise SystemExit('logical name table must be exactly 200 unique chars')

    glyphs={}
    changes=[]
    clip=[]
    blank=[]
    rows=[]
    for idx,ch in enumerate(chars):
        im,cl=render(font,ch)
        if cl:clip.append(ch)
        if not im.getbbox():blank.append(ch)
        _,v,_=dec(ch)
        if v==V_EU:
            im,changed,meta=eu_trim(im)
            if changed:
                changes.append({'char':ch,'logical_index':idx,**meta})
        glyphs[ch]=im
        bb=im.getbbox()
        rows.append({
          'logical_index':idx,
          'page':idx//50+1,
          'row':(idx%50)//10,
          'column':idx%10,
          'char':ch,
          'unicode':f'U+{ord(ch):04X}',
          'bbox_w':bb[2]-bb[0],
          'bbox_h':bb[3]-bb[1],
          'left_margin':bb[0],
          'right_margin':CELL_W-bb[2],
          'top_margin':bb[1],
          'bottom_margin':CELL_H-bb[3],
          'set_pixels':sum(im.getdata())
        })

    bmap={ch:bits(im) for ch,im in glyphs.items()}
    rev={}
    for ch,v in bmap.items():
        rev.setdefault(v,[]).append(ch)
    dup=[v for v in rev.values() if len(v)>1]

    pairs=[]
    for i,x in enumerate(chars):
        for y in chars[i+1:]:
            d=(bmap[x]^bmap[y]).bit_count()
            if d<=3:
                pairs.append({'char_a':x,'char_b':y,'hamming':d})
    pairs.sort(key=lambda q:(q['hamming'],q['char_a'],q['char_b']))

    with (a.out/'MMR_NameFont_Mona10_Custom_v0.1_index.tsv').open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]),delimiter='\t',lineterminator='\n')
        w.writeheader();w.writerows(rows)

    with (a.out/'MMR_NameFont_Mona10_Custom_v0.1_review.tsv').open('w',encoding='utf-8-sig',newline='') as f:
        fields=['char_a','char_b','hamming','status','note']
        w=csv.DictWriter(f,fieldnames=fields,delimiter='\t',lineterminator='\n')
        w.writeheader()
        for p in pairs:
            w.writerow({**p,'status':'REVIEW_REQUIRED','note':''})

    for n,page in enumerate(PAGES,1):
        g={ch:glyphs[ch] for ch in page}
        img=Image.new('1',(10*CELL_W,5*CELL_H),0)
        for i,ch in enumerate(page):
            img.paste(g[ch],((i%10)*CELL_W,(i//10)*CELL_H))
        img.resize((img.width*4,img.height*4),Image.Resampling.NEAREST).save(
            a.out/f'MMR_NameFont_Mona10_Custom_v0.1_page{n}.png')

    report={
      'schema':'MMR_NAME_FONT_MONA10_CUSTOM_V0_1_QA',
      'classification':'PASS_STATIC_NAME_FONT_CANDIDATE__ORIGINAL_GEOMETRY_REQUIRED'
          if not blank and not clip and not dup else 'FAIL_NAME_FONT_STRUCTURE',
      'base_font':a.font.name,
      'base_font_sha256':sha256(a.font),
      'font_px':FONT_PX,
      'glyph_cell':[CELL_W,CELL_H],
      'y_offset':YOFF,
      'horizontal_alignment':'centered',
      'geometric_scaling':False,
      'name_glyphs':len(chars),
      'blank':len(blank),
      'clipped':len(clip),
      'duplicate_bitmap_groups':len(dup),
      'bbox_width_counts':dict(Counter(r['bbox_w'] for r in rows)),
      'bbox_height_counts':dict(Counter(r['bbox_h'] for r in rows)),
      'custom_rule':'Jungseong EU dominant horizontal run >=8: trim one pixel each endpoint',
      'changed_glyphs':[r['char'] for r in changes],
      'review_distance_le_1':sum(p['hamming']<=1 for p in pairs),
      'review_distance_le_2':sum(p['hamming']<=2 for p in pairs),
      'review_distance_le_3':sum(p['hamming']<=3 for p in pairs),
      'cursor_geometry':'UNRESOLVED__MUST_MEASURE_JP_ORIGINAL',
      'screen_cell_pitch':'UNRESOLVED__MUST_MEASURE_JP_ORIGINAL',
      'rule':'Do not derive cursor Y-step or box height from this 10x12 raster candidate.'
    }
    (a.out/'MMR_NAME_FONT_MONA10_CUSTOM_V0_1_QA.json').write_text(
        json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False,indent=2))
    raise SystemExit(0 if report['classification'].startswith('PASS') else 2)

if __name__=='__main__':
    main()
