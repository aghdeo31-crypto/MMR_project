#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Apply explicit 12x12 MMR glyph overrides to a Mona12 raster set.

Override JSON:
{
  "한": [
    "..#.........",
    ...
    "............"
  ]
}
Each glyph must be exactly 12 rows x 12 chars using '#' and '.'.
This creates a reviewable art layer; it never edits a font file or ROM.
"""
from __future__ import annotations
import argparse,json
from pathlib import Path
from PIL import Image

CELL=12

def parse(rows,ch):
    if not isinstance(rows,list) or len(rows)!=CELL:
        raise ValueError(f'{ch}: expected 12 rows')
    im=Image.new('1',(CELL,CELL),0);p=im.load()
    for y,row in enumerate(rows):
        if len(row)!=CELL or any(c not in '.#' for c in row):
            raise ValueError(f'{ch}: row {y} must be 12 chars of .#')
        for x,c in enumerate(row):
            if c=='#':p[x,y]=1
    if not im.getbbox():raise ValueError(f'{ch}: blank override')
    return im

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--overrides',type=Path,required=True)
    ap.add_argument('--out',type=Path,required=True)
    a=ap.parse_args();a.out.mkdir(parents=True,exist_ok=True)
    data=json.loads(a.overrides.read_text(encoding='utf-8'))
    manifest={}
    for ch,rows in data.items():
        if len(ch)!=1 or not ('가'<=ch<='힣'):raise ValueError(f'invalid key {ch!r}')
        im=parse(rows,ch)
        p=a.out/(f'U+{ord(ch):04X}_{ch}.png')
        im.resize((CELL*16,CELL*16),Image.Resampling.NEAREST).save(p)
        manifest[ch]={'unicode':f'U+{ord(ch):04X}','preview':p.name,'rows':rows}
    (a.out/'MMR_FONT_OVERRIDE_MANIFEST.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'overrides':len(manifest),'chars':list(manifest)},ensure_ascii=False))

if __name__=='__main__':main()
