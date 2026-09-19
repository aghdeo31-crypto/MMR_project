#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""MMR 12x12 Hangul visual-quality analyzer.

Builds a fail-closed QA queue rather than pretending every mathematically close
pair is unreadable. Exact duplicate bitmaps are hard failures. One-jamo neighbor
pairs with very low pixel distance are REVIEW_REQUIRED, prioritized by actual
game-corpus usage when a corpus is supplied.

The review queue is designed for an MMR-specific override layer.
"""
from __future__ import annotations
import argparse,csv,hashlib,json,re
from collections import Counter,defaultdict
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont

CELL=12; FONT_PX=12; YOFF=-1
HANGUL_RE=re.compile(r'[가-힣]')
L=['ㄱ','ㄲ','ㄴ','ㄷ','ㄸ','ㄹ','ㅁ','ㅂ','ㅃ','ㅅ','ㅆ','ㅇ','ㅈ','ㅉ','ㅊ','ㅋ','ㅌ','ㅍ','ㅎ']
V=['ㅏ','ㅐ','ㅑ','ㅒ','ㅓ','ㅔ','ㅕ','ㅖ','ㅗ','ㅘ','ㅙ','ㅚ','ㅛ','ㅜ','ㅝ','ㅞ','ㅟ','ㅠ','ㅡ','ㅢ','ㅣ']
T=['','ㄱ','ㄲ','ㄳ','ㄴ','ㄵ','ㄶ','ㄷ','ㄹ','ㄺ','ㄻ','ㄼ','ㄽ','ㄾ','ㄿ','ㅀ','ㅁ','ㅂ','ㅄ','ㅅ','ㅆ','ㅇ','ㅈ','ㅊ','ㅋ','ㅌ','ㅍ','ㅎ']

def ks2350():
    return [bytes((a,b)).decode('euc_kr') for a in range(0xB0,0xC9) for b in range(0xA1,0xFF)]

def dec(ch):
    n=ord(ch)-0xAC00
    return n//588,(n%588)//28,n%28

def sha256(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(1<<20),b''):h.update(b)
    return h.hexdigest()

def render(font,ch):
    tmp=Image.new('1',(32,20),0)
    ImageDraw.Draw(tmp).text((8,YOFF),ch,font=font,fill=1)
    b=tmp.getbbox()
    if not b:return Image.new('1',(CELL,CELL),0),True
    x0,y0,x1,y1=b; x0-=8; x1-=8; w=x1-x0
    xoff=(CELL-w)//2-x0
    clip=(x0+xoff<0 or x1+xoff>CELL or y0<0 or y1>CELL)
    out=Image.new('1',(CELL,CELL),0)
    ImageDraw.Draw(out).text((xoff,YOFF),ch,font=font,fill=1)
    return out,clip

def bits(im):
    p=im.load();v=0;k=0
    for y in range(CELL):
        for x in range(CELL):
            if p[x,y]:v|=1<<k
            k+=1
    return v

def hamming(a,b):return (a^b).bit_count()

def load_corpus(path,column):
    if not path:return Counter(),None
    if path.suffix.lower() in ('.tsv','.csv'):
        delim='\t' if path.suffix.lower()=='.tsv' else ','
        with path.open(encoding='utf-8-sig',newline='') as f:rows=list(csv.DictReader(f,delimiter=delim))
        if not rows:return Counter(),{'rows':0}
        if not column:
            low={k.lower():k for k in rows[0]}
            for n in ('korean','ko','korean_current','translation','translated_text','ko_text'):
                if n in low:column=low[n];break
        if not column or column not in rows[0]:raise ValueError('cannot find Korean column; pass --column')
        text='\n'.join(r.get(column,'') or '' for r in rows); row_count=len(rows)
    else:
        text=path.read_text(encoding='utf-8-sig');row_count=None
    c=Counter(HANGUL_RE.findall(text))
    return c,{'name':path.name,'sha256':sha256(path),'rows':row_count,'hangul_occurrences':sum(c.values()),'unique_hangul':len(c)}

def component_diff(a,b):
    x=dec(a);y=dec(b)
    idx=[i for i in range(3) if x[i]!=y[i]]
    if len(idx)!=1:return None
    i=idx[0]
    if i==0:return 'L',L[x[0]],L[y[0]]
    if i==1:return 'V',V[x[1]],V[y[1]]
    return 'T',T[x[2]],T[y[2]]

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--font',type=Path,required=True)
    ap.add_argument('--corpus',type=Path)
    ap.add_argument('--column')
    ap.add_argument('--review-distance',type=int,default=3)
    ap.add_argument('-o','--outdir',type=Path,required=True)
    a=ap.parse_args();a.outdir.mkdir(parents=True,exist_ok=True)
    font=ImageFont.truetype(str(a.font),FONT_PX)
    chars=ks2350();imgs={};bbits={};clips=[];blank=[]
    for ch in chars:
        im,cl=render(font,ch);imgs[ch]=im;bbits[ch]=bits(im)
        if cl:clips.append(ch)
        if not im.getbbox():blank.append(ch)
    rev=defaultdict(list)
    for ch,v in bbits.items():rev[v].append(ch)
    dup=[x for x in rev.values() if len(x)>1]

    corpus,corpus_meta=load_corpus(a.corpus,a.column)
    groups=[defaultdict(list),defaultdict(list),defaultdict(list)]
    for ch in chars:
        l,v,t=dec(ch)
        groups[0][(v,t)].append(ch)
        groups[1][(l,t)].append(ch)
        groups[2][(l,v)].append(ch)
    seen=set();queue=[]
    for gi,g in enumerate(groups):
        for vals in g.values():
            for i in range(len(vals)):
                for j in range(i+1,len(vals)):
                    x,y=vals[i],vals[j]
                    key=tuple(sorted((x,y)))
                    if key in seen:continue
                    seen.add(key)
                    d=hamming(bbits[x],bbits[y])
                    if d>a.review_distance:continue
                    cd=component_diff(x,y)
                    ux,uy=corpus.get(x,0),corpus.get(y,0)
                    queue.append({
                      'char_a':x,'char_b':y,'hamming':d,
                      'component':cd[0] if cd else '',
                      'part_a':cd[1] if cd else '','part_b':cd[2] if cd else '',
                      'usage_a':ux,'usage_b':uy,'both_used':bool(ux and uy),
                      'priority':'P0_BOTH_USED' if ux and uy else ('P1_ONE_USED' if ux or uy else 'P2_UNUSED'),
                      'review_status':'REVIEW_REQUIRED',
                      'override_required':'',
                      'note':''
                    })
    queue.sort(key=lambda r:({'P0_BOTH_USED':0,'P1_ONE_USED':1,'P2_UNUSED':2}[r['priority']],r['hamming'],-r['usage_a']-r['usage_b'],r['char_a'],r['char_b']))
    with (a.outdir/'MMR_FONT_CONFUSABLE_REVIEW_QUEUE.tsv').open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(queue[0]) if queue else ['char_a'],delimiter='\t',lineterminator='\n');w.writeheader();w.writerows(queue)

    sentinels=[]
    for x,y in [('한','힌'),('한','이'),('이','히'),('개','게'),('애','에'),('독','득'),('눅','늑')]:
        if x in bbits and y in bbits:
            sentinels.append({'a':x,'b':y,'hamming':hamming(bbits[x],bbits[y]),'usage_a':corpus.get(x,0),'usage_b':corpus.get(y,0)})

    hard=[]
    if blank:hard.append({'reason':'BLANK_GLYPHS','count':len(blank),'sample':blank[:32]})
    if clips:hard.append({'reason':'CLIPPED_GLYPHS','count':len(clips),'sample':clips[:32]})
    if dup:hard.append({'reason':'DUPLICATE_BITMAP_GLYPHS','groups':len(dup),'sample':dup[:16]})

    report={
      'schema':'MMR_FONT_VISUAL_QUALITY_V1',
      'classification':'FAIL_FONT_STRUCTURE' if hard else 'PASS_STRUCTURE_REVIEW_REQUIRED',
      'font':a.font.name,'font_sha256':sha256(a.font),'cell':[12,12],'font_px':12,'y_offset':-1,'horizontal':'centered',
      'glyphs':len(chars),'blank':len(blank),'clipped':len(clips),'duplicate_bitmap_groups':len(dup),
      'review_distance':a.review_distance,'review_pairs':len(queue),
      'p0_both_used':sum(r['priority']=='P0_BOTH_USED' for r in queue),
      'p1_one_used':sum(r['priority']=='P1_ONE_USED' for r in queue),
      'corpus':corpus_meta,'sentinels':sentinels,'hard_failures':hard,
      'release_rule':'Structure must pass. Every P0 pair must be visually reviewed; any ambiguous P0 pair requires an MMR custom override before RC promotion.'
    }
    (a.outdir/'MMR_FONT_VISUAL_QUALITY_REPORT.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False,indent=2))
    raise SystemExit(2 if hard else 0)

if __name__=='__main__':main()
