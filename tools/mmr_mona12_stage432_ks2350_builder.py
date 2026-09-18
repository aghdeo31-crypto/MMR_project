#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build Stage432-layout-compatible Mona12 KS X 1001 glyph assets.

This tool is intentionally ROM-agnostic and fail-closed on the one still
unrecovered Stage432 detail: vertical bit orientation inside each LE16 column.
It emits BOTH bit0-top and bit15-top font-bank candidates plus the common
KS2350 slot/token/pointer map. A later comparison against the current MMR
packer/ROM selects one orientation; this tool never guesses it.

Confirmed Stage432 layout authority used here:
- KS X 1001 Hangul order, 2350 glyphs
- record = width 0x0C + 12 x LE16 column words = 25 bytes
- IDs 0..1309 -> EB:8000 + id*25
- IDs 1310..2349 -> EC:8000 + (id-1310)*25
- IDs 2350..2399 -> EC:E600 blank fail-safe
- 2400-entry 24-bit pointer table at EA:C000
- private token id=(hi-1)*160+(lo-0x60), lead=0x08

No font file is redistributed. No ROM/IPS is written.
"""
from __future__ import annotations
import argparse,csv,hashlib,json,struct
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont

CELL=12
FONT_PX=12
YOFF=-1
WIDTH_BYTE=0x0C
SPLIT=1310
TOTAL=2350
PTR_TOTAL=2400
BLANK_PTR=(0xEC,0xE600)

def sha256_bytes(b:bytes)->str:return hashlib.sha256(b).hexdigest()
def sha256_file(p:Path)->str:return sha256_bytes(p.read_bytes())

def ks2350():
    out=[]
    for lead in range(0xB0,0xC9):
        for trail in range(0xA1,0xFF):
            ch=bytes((lead,trail)).decode('euc_kr')
            out.append((ch,lead,trail))
    assert len(out)==2350 and out[0][0]=='가' and out[-1][0]=='힝'
    return out

def intrinsic_bbox(font,ch):
    tmp=Image.new('1',(32,20),0)
    ImageDraw.Draw(tmp).text((8,YOFF),ch,font=font,fill=1)
    bb=tmp.getbbox()
    if not bb:return None
    return (bb[0]-8,bb[1],bb[2]-8,bb[3])

def render_centered(font,ch):
    ib=intrinsic_bbox(font,ch)
    if not ib:return Image.new('1',(CELL,CELL),0),None,0
    x0,y0,x1,y1=ib; w=x1-x0
    xoff=((CELL-w)//2)-x0
    im=Image.new('1',(CELL,CELL),0)
    ImageDraw.Draw(im).text((xoff,YOFF),ch,font=font,fill=1)
    return im,ib,xoff

def pack_record(im:Image.Image,orientation:str)->bytes:
    p=im.load(); out=bytearray([WIDTH_BYTE])
    for x in range(CELL):
        word=0
        for y in range(CELL):
            if p[x,y]:
                bit=y if orientation=='bit0_top' else 15-y
                word |= 1<<bit
        out += struct.pack('<H',word)
    assert len(out)==25
    return bytes(out)

def snes_ptr_for_id(i:int):
    if i<SPLIT:return 0xEB,0x8000+i*25
    if i<TOTAL:return 0xEC,0x8000+(i-SPLIT)*25
    return BLANK_PTR

def ptr24_le(bank:int,addr:int)->bytes:
    return bytes((addr&0xFF,(addr>>8)&0xFF,bank&0xFF))

def private_token(i:int):
    hi=i//160+1; lo=i%160+0x60
    assert 1<=hi<=0x0F and 0x60<=lo<=0xFF
    return bytes((0x08,hi,lo))

def atlas(images,cols=47,scale=2):
    rows=(len(images)+cols-1)//cols
    a=Image.new('1',(cols*CELL,rows*CELL),0)
    for i,g in enumerate(images):a.paste(g,((i%cols)*CELL,(i//cols)*CELL))
    return a.resize((a.width*scale,a.height*scale),Image.Resampling.NEAREST)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--font',type=Path,required=True)
    ap.add_argument('--out',type=Path,required=True)
    a=ap.parse_args();a.out.mkdir(parents=True,exist_ok=True)
    font=ImageFont.truetype(str(a.font),FONT_PX)
    ks=ks2350(); imgs=[]; rows=[]
    packed={'bit0_top':[],'bit15_top':[]}
    for i,(ch,e1,e2) in enumerate(ks):
        im,ib,xoff=render_centered(font,ch); imgs.append(im)
        bb=im.getbbox(); pix=sum(im.getdata())
        if not bb: raise SystemExit(f'blank glyph {i} {ch}')
        for mode in packed:packed[mode].append(pack_record(im,mode))
        bank,addr=snes_ptr_for_id(i); tok=private_token(i)
        rows.append({
            'id':i,'char':ch,'unicode':f'U+{ord(ch):04X}','euc_kr':f'{e1:02X}{e2:02X}',
            'private_token':' '.join(f'{x:02X}' for x in tok),
            'snes_ptr':'$'+f'{bank:02X}:{addr:04X}','ptr24_le':ptr24_le(bank,addr).hex(' ').upper(),
            'pixels':pix,'bbox_w':bb[2]-bb[0],'bbox_h':bb[3]-bb[1],
            'left_margin':bb[0],'right_margin':CELL-bb[2],'x_offset':xoff,
        })
    ptr=bytearray()
    for i in range(PTR_TOTAL):
        bank,addr=snes_ptr_for_id(i);ptr+=ptr24_le(bank,addr)
    (a.out/'Mona12_KS2350_pointer_table_2400_LE24.bin').write_bytes(ptr)
    orient_reports={}
    for mode,recs in packed.items():
        eb=b''.join(recs[:SPLIT]);ec=b''.join(recs[SPLIT:])
        assert len(eb)==32750 and len(ec)==26000
        (a.out/f'Mona12_KS2350_EB8000_{mode}.bin').write_bytes(eb)
        (a.out/f'Mona12_KS2350_EC8000_{mode}.bin').write_bytes(ec)
        orient_reports[mode]={
            'EB_bytes':len(eb),'EB_sha256':sha256_bytes(eb),
            'EC_bytes':len(ec),'EC_sha256':sha256_bytes(ec),
            'unique_records':len(set(recs)),'blank_records':sum(r[1:]==bytes(24) for r in recs),
        }
    blank=bytes([0x0C])+bytes(24)
    (a.out/'Mona12_KS2350_blank_failsafe_candidate.bin').write_bytes(blank)
    with (a.out/'Mona12_KS2350_index.tsv').open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]),delimiter='\t',lineterminator='\n');w.writeheader();w.writerows(rows)
    atlas(imgs).save(a.out/'Mona12_KS2350_centered_atlas.png')
    pilot={}
    expected={'탄':'08 0D AF','약':'08 09 C3','보':'08 07 63','급':'08 01 FB'}
    for ch,exp in expected.items():
        i=next(r['id'] for r in rows if r['char']==ch);got=rows[i]['private_token']
        pilot[ch]={'id':i,'euc_kr':rows[i]['euc_kr'],'private_token':got,'expected':exp,'match':got==exp}
    crosses=[]
    for i in range(TOTAL):
        b,addr=snes_ptr_for_id(i)
        if addr+25>0x10000:crosses.append(i)
    report={
      'schema':'MMR_MONA12_STAGE432_KS2350_LAYOUT_PREP_V1',
      'classification':'PASS_LAYOUT_AND_MAPPING__PACKING_ORIENTATION_DUAL_CANDIDATE',
      'font_input_name':a.font.name,'font_input_sha256':sha256_file(a.font),'font_redistributed':False,
      'raster':{'font_px':12,'cell':[12,12],'y_offset':-1,'horizontal':'centered'},
      'ksx1001':{'glyphs':TOTAL,'first':ks[0][0],'last':ks[-1][0],'order':'EUC-KR B0A1..C8FE row-major'},
      'record_contract':{'bytes':25,'width_byte':'0C','columns':12,'column_word':'LE16'},
      'vertical_bit_orientation':'UNRESOLVED_FROM_RECOVERED_STAGE432_DOCS__BOTH_EMITTED',
      'orientations':orient_reports,
      'pointer_table':{'entries':PTR_TOTAL,'bytes':len(ptr),'sha256':sha256_bytes(ptr),'address':'$EA:C000','candidate_encoding':'addr_lo,addr_hi,bank'},
      'banks':{'part1':'$EB:8000 IDs 0..1309','part2':'$EC:8000 IDs 1310..2349','blank_failsafe':'$EC:E600 IDs 2350..2399'},
      'bank_crossing_real_records':crosses,
      'pilot_token_identity':pilot,'pilot_all_match':all(x['match'] for x in pilot.values()),
      'blank_failsafe_candidate':{'bytes':25,'hex':blank.hex(' ').upper(),'sha256':sha256_bytes(blank),'authority':'CANDIDATE_UNTIL_CURRENT_PACKER_COMPARE'},
      'safety':['NO_ROM_WRITE','NO_IPS_WRITE','NO_FONT_FILE_REDISTRIBUTION','DO_NOT_SELECT_VERTICAL_BIT_ORIENTATION_WITHOUT_CURRENT_PACKER_OR_STAGE432_ASSET_COMPARISON']
    }
    (a.out/'MMR_MONA12_STAGE432_KS2350_QA.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
