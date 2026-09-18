#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""MMR Mona12 source-raster builder (non-ROM-writing).

Purpose
-------
Create exact 12x12 monochrome source glyphs from Mona12 Regular without
changing MMR renderer/storage assumptions. The output is intended to be fed
into the existing MMR glyph packer once the current project workspace is
available again.

Safety
------
- Does not patch ROMs.
- Does not assume SNES tile packing / glyph slot addresses.
- Does not redistribute the input font.
- Keeps Unicode -> bitmap mapping explicit in JSON/TSV.
"""
from __future__ import annotations
import argparse, json, csv, hashlib
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

CELL_W=CELL_H=12
FONT_PX=12
DEFAULT_DIAG=(
    "가각값없읽닭밖꽃괜됐않찮젊갉넓앉얽밟싫"
    "메탈맥스리턴즈기록선택이름설정레드울프이삭의샘비트라몬스터전차"
)

def sha256(p:Path)->str:
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1<<20),b''): h.update(b)
    return h.hexdigest()

def uniq(s:str)->str:
    return ''.join(dict.fromkeys(s))

def load_chars(path:Path|None, all_hangul:bool)->str:
    chars=''
    if path:
        chars=''.join(c for c in path.read_text(encoding='utf-8-sig') if not c.isspace())
    if all_hangul:
        chars += ''.join(chr(c) for c in range(0xAC00,0xD7A4))
    chars += DEFAULT_DIAG
    return uniq(chars)

def render(font:ImageFont.FreeTypeFont,ch:str)->Image.Image:
    # Mona12 at 12 px is already a true monochrome pixel font. Pillow bbox for
    # Hangul is typically (0,1,12,12). y=-1 aligns the visible 11-row body to
    # rows 0..10 and leaves row 11 as vertical breathing room.
    im=Image.new('1',(CELL_W,CELL_H),0)
    ImageDraw.Draw(im).text((0,-1),ch,font=font,fill=1)
    return im

def packed_rows_16be(im:Image.Image)->bytes:
    """12 pixels/row -> big-endian 16-bit row, upper 12 bits used.
    Neutral source format only; not a claim about MMR ROM packing.
    """
    p=im.load(); out=bytearray()
    for y in range(CELL_H):
        v=0
        for x in range(CELL_W):
            if p[x,y]: v |= 1 << (15-x)
        out += v.to_bytes(2,'big')
    return bytes(out)

def metrics(im:Image.Image):
    bb=im.getbbox(); pix=sum(1 for v in im.getdata() if v)
    if bb: bw,bh=bb[2]-bb[0],bb[3]-bb[1]
    else: bw=bh=0
    return pix,bw,bh,bb

def build(font_path:Path,out:Path,chars:str):
    out.mkdir(parents=True,exist_ok=True)
    font=ImageFont.truetype(str(font_path),FONT_PX)
    rows=[]; glyphs=[]; raw=bytearray()
    for i,ch in enumerate(chars):
        im=render(font,ch); glyphs.append(im)
        off=len(raw); b=packed_rows_16be(im); raw += b
        pix,bw,bh,bb=metrics(im)
        rows.append({
            'index':i,'char':ch,'unicode':f'U+{ord(ch):04X}',
            'offset':off,'bytes':len(b),'pixels':pix,'bbox_w':bw,'bbox_h':bh,
            'bbox':list(bb) if bb else None,
        })
    (out/'mona12_regular_12x12_row16be.srcbin').write_bytes(raw)
    with (out/'mona12_regular_12x12_index.tsv').open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]),delimiter='\t'); w.writeheader(); w.writerows(rows)
    cols=32; scale=3; rows_n=(len(glyphs)+cols-1)//cols
    atlas=Image.new('1',(cols*CELL_W,rows_n*CELL_H),0)
    for i,g in enumerate(glyphs): atlas.paste(g,((i%cols)*CELL_W,(i//cols)*CELL_H))
    atlas.resize((atlas.width*scale,atlas.height*scale),Image.Resampling.NEAREST).save(out/'mona12_regular_12x12_atlas.png')
    rep={
      'profile':'MMR_MONA12_REGULAR_12X12_SOURCE_V1',
      'font_input_name':font_path.name,
      'font_input_sha256':sha256(font_path),
      'font_embedded_or_redistributed':False,
      'font_px':FONT_PX,'cell':[CELL_W,CELL_H],
      'glyph_count':len(glyphs),
      'source_format':'12 rows x big-endian 16-bit; upper 12 bits are pixels',
      'bytes_per_glyph':24,'raw_bytes':len(raw),
      'rom_layout_assumed':False,'rom_written':False,
      'missing_count':sum(1 for r in rows if r['bbox'] is None),
      'overflow_count':sum(1 for r in rows if r['bbox_w']>12 or r['bbox_h']>12),
      'mean_pixels':round(sum(r['pixels'] for r in rows)/len(rows),3),
      'mean_bbox_w':round(sum(r['bbox_w'] for r in rows)/len(rows),3),
      'mean_bbox_h':round(sum(r['bbox_h'] for r in rows)/len(rows),3),
      'vertical_alignment':'draw y=-1; typical Hangul visible body rows 0..10; row11 breathing',
      'next':'Map these Unicode glyphs through the current Stage1467 font-slot/packer authority; do not invent slot packing here.'
    }
    (out/'MMR_MONA12_12X12_SOURCE_REPORT.json').write_text(json.dumps(rep,ensure_ascii=False,indent=2),encoding='utf-8')
    return rep

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--font',type=Path,required=True)
    ap.add_argument('--chars',type=Path)
    ap.add_argument('--all-hangul',action='store_true')
    ap.add_argument('--out',type=Path,default=Path('MMR_MONA12_SOURCE'))
    a=ap.parse_args()
    chars=load_chars(a.chars,a.all_hangul)
    if not chars: raise SystemExit('no characters')
    print(json.dumps(build(a.font,a.out,chars),ensure_ascii=False,indent=2))
if __name__=='__main__': main()
