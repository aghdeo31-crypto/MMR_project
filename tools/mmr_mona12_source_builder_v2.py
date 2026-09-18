#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""MMR Mona12 12x12 source builder v2.

Compared with v1, v2 can horizontally center the actual monochrome glyph body
inside the 12x12 cell. This better matches the historical MMR Japanese-base
font direction of a ~10x12 Korean body centered in a 12x12 active cell.

This tool NEVER writes a ROM and does not guess the MMR packer layout.
"""
from __future__ import annotations
import argparse,csv,hashlib,json
from collections import Counter
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont

CELL_W=CELL_H=12
FONT_PX=12
YOFF=-1
DEFAULT_DIAG=("가각값없읽닭밖꽃괜됐않찮젊갉넓앉얽밟싫"
              "메탈맥스리턴즈기록선택이름설정레드울프이삭의샘비트라몬스터전차")

def sha256(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()

def uniq(s): return ''.join(dict.fromkeys(s))

def load_chars(path,all_hangul):
 s=''
 if path:s=''.join(c for c in Path(path).read_text(encoding='utf-8-sig') if not c.isspace())
 if all_hangul:s+=''.join(chr(c) for c in range(0xAC00,0xD7A4))
 s+=DEFAULT_DIAG
 return uniq(s)

def intrinsic_pixel_bbox(font,ch):
 im=Image.new('1',(32,20),0)
 ImageDraw.Draw(im).text((8,YOFF),ch,font=font,fill=1)
 bb=im.getbbox()
 if not bb:return None
 return (bb[0]-8,bb[1],bb[2]-8,bb[3])

def render(font,ch,align='center'):
 ib=intrinsic_pixel_bbox(font,ch)
 if ib is None:return Image.new('1',(CELL_W,CELL_H),0),0,None
 x0,y0,x1,y1=ib; w=x1-x0
 xoff=0 if align=='raw' else ((CELL_W-w)//2-x0)
 im=Image.new('1',(CELL_W,CELL_H),0)
 ImageDraw.Draw(im).text((xoff,YOFF),ch,font=font,fill=1)
 return im,xoff,ib

def packed_rows_16be(im):
 p=im.load();o=bytearray()
 for y in range(CELL_H):
  v=0
  for x in range(CELL_W):
   if p[x,y]:v|=1<<(15-x)
  o+=v.to_bytes(2,'big')
 return bytes(o)

def build(font_path,out,chars,align):
 out.mkdir(parents=True,exist_ok=True)
 font=ImageFont.truetype(str(font_path),FONT_PX)
 recs=[];raw=bytearray();glyphs=[];margin_pairs=Counter();clip=0
 for i,ch in enumerate(chars):
  im,xoff,ib=render(font,ch,align);bb=im.getbbox();glyphs.append(im)
  if ib:
   x0,y0,x1,y1=ib;sx0=x0+xoff;sx1=x1+xoff
   if sx0<0 or sx1>CELL_W or y0<0 or y1>CELL_H:clip+=1
  b=packed_rows_16be(im);off=len(raw);raw+=b
  if bb:
   l,t,r,bt=bb;margin_pairs[(l,CELL_W-r)]+=1;pix=sum(im.getdata())
  else:l=t=r=bt=pix=0
  recs.append({'index':i,'char':ch,'unicode':f'U+{ord(ch):04X}','offset':off,'bytes':24,
               'x_offset':xoff,'left_margin':l,'right_margin':CELL_W-r if bb else 0,
               'bbox_w':r-l if bb else 0,'bbox_h':bt-t if bb else 0,'pixels':pix})
 stem=f'mona12_regular_12x12_{align}'
 (out/f'{stem}_row16be.srcbin').write_bytes(raw)
 with (out/f'{stem}_index.tsv').open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(recs[0]),delimiter='\t');w.writeheader();w.writerows(recs)
 cols=32;scale=3;rn=(len(glyphs)+cols-1)//cols
 atlas=Image.new('1',(cols*12,rn*12),0)
 for i,g in enumerate(glyphs):atlas.paste(g,((i%cols)*12,(i//cols)*12))
 atlas.resize((atlas.width*scale,atlas.height*scale),Image.Resampling.NEAREST).save(out/f'{stem}_atlas.png')
 report={'schema':'MMR_MONA12_12X12_SOURCE_V2','font':font_path.name,'font_sha256':sha256(font_path),
         'cell':[12,12],'font_px':12,'y_offset':YOFF,'horizontal_alignment':align,
         'glyph_count':len(chars),'clip_count':clip,'raw_bytes':len(raw),
         'mean_pixels':sum(r['pixels'] for r in recs)/len(recs),
         'width_counts':dict(Counter(r['bbox_w'] for r in recs)),
         'margin_pair_counts':{f'{a},{b}':n for (a,b),n in sorted(margin_pairs.items())},
         'source_format':'12 rows x BE16; upper 12 bits pixels; neutral source only, not MMR ROM packing',
         'rom_written':False,'font_embedded_or_redistributed':False}
 (out/f'{stem}_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
 return report

def main():
 ap=argparse.ArgumentParser()
 ap.add_argument('--font',type=Path,required=True)
 ap.add_argument('--chars',type=Path)
 ap.add_argument('--all-hangul',action='store_true')
 ap.add_argument('--align',choices=['raw','center'],default='center')
 ap.add_argument('--out',type=Path,required=True)
 a=ap.parse_args()
 print(json.dumps(build(a.font,a.out,load_chars(a.chars,a.all_hangul),a.align),ensure_ascii=False,indent=2))

if __name__=='__main__':main()
