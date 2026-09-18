#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build an MMR FONT_ASSETS_ONLY Mona12 candidate from a pinned baseline ROM.

Fail-closed rules:
- exact baseline SHA256 is mandatory;
- current Stage432 2400-entry pointer table must be byte-exact;
- current 2350 native12 records must resolve to exactly one vertical orientation;
- only EB:8000 1310 records and EC:8000 1040 records may change;
- pointer table, blank fail-safe, code, D12/KMODE/ECC6 and checksum bytes stay unchanged;
- no source-token changes and no translation changes.

Output ROM is local test media only. No IPS is emitted by design.
"""
from __future__ import annotations
import argparse,hashlib,json,struct
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont

TOTAL=2350
SPLIT=1310
PTR_TOTAL=2400
REC=25
PTR_OFF=0x354000
EB_OFF=0x358000
EC_OFF=0x360000
BLANK_OFF=0x366600
EB_BYTES=SPLIT*REC
EC_BYTES=(TOTAL-SPLIT)*REC
CELL=12
FONT_PX=12
YOFF=-1

def sha(b): return hashlib.sha256(b).hexdigest()

def ptr_for_id(i):
    if i<SPLIT:
        bank,addr=0xEB,0x8000+i*REC
    elif i<TOTAL:
        bank,addr=0xEC,0x8000+(i-SPLIT)*REC
    else:
        bank,addr=0xEC,0xE600
    return bytes((addr&255,(addr>>8)&255,bank))

def exp_ptr():
    return b''.join(ptr_for_id(i) for i in range(PTR_TOTAL))

def resolve_orientation(eb,ec):
    blob=eb+ec
    hi=lo=badw=nonblank=0
    for i in range(TOTAL):
        r=blob[i*REC:(i+1)*REC]
        badw+=int(r[0]!=0x0c)
        ws=struct.unpack('<12H',r[1:])
        nonblank+=int(any(ws))
        hi+=int(any(w&0xF000 for w in ws))
        lo+=int(any(w&0x000F for w in ws))
    if badw or nonblank!=TOTAL:
        return None,{'width_bad':badw,'nonblank':nonblank,'high_nonzero_records':hi,'low_nonzero_records':lo}
    if hi==0 and lo>0:
        o='bit0_top'
    elif lo==0 and hi>0:
        o='bit15_top'
    else:
        o=None
    return o,{'width_bad':badw,'nonblank':nonblank,'high_nonzero_records':hi,'low_nonzero_records':lo}

def ks2350():
    out=[]
    for a in range(0xB0,0xC9):
        for b in range(0xA1,0xFF):
            out.append(bytes((a,b)).decode('euc_kr'))
    assert len(out)==2350 and out[0]=='가' and out[-1]=='힝'
    return out

def ibbox(font,ch):
    t=Image.new('1',(32,20),0)
    ImageDraw.Draw(t).text((8,YOFF),ch,font=font,fill=1)
    b=t.getbbox()
    return None if not b else (b[0]-8,b[1],b[2]-8,b[3])

def render(font,ch):
    b=ibbox(font,ch)
    if not b:
        raise RuntimeError('blank glyph '+ch)
    x0,y0,x1,y1=b
    xoff=(CELL-(x1-x0))//2-x0
    im=Image.new('1',(CELL,CELL),0)
    ImageDraw.Draw(im).text((xoff,YOFF),ch,font=font,fill=1)
    if not im.getbbox():
        raise RuntimeError('blank raster '+ch)
    return im

def pack(im,orientation):
    p=im.load()
    o=bytearray([0x0c])
    for x in range(12):
        w=0
        for y in range(12):
            if p[x,y]:
                w |= 1 << (y if orientation=='bit0_top' else 15-y)
        o += struct.pack('<H',w)
    return bytes(o)

def build_font(font_path,orientation):
    font=ImageFont.truetype(str(font_path),FONT_PX)
    recs=[pack(render(font,ch),orientation) for ch in ks2350()]
    if len(set(recs))!=TOTAL:
        raise RuntimeError(f'Mona12 records not unique: {len(set(recs))}/{TOTAL}')
    return b''.join(recs[:SPLIT]),b''.join(recs[SPLIT:])

def diff_runs(a,b):
    if len(a)!=len(b):
        raise ValueError('size mismatch')
    out=[]
    s=None
    for i,(x,y) in enumerate(zip(a,b)):
        if x!=y and s is None:
            s=i
        elif x==y and s is not None:
            out.append((s,i))
            s=None
    if s is not None:
        out.append((s,len(a)))
    return out

def allowed(i):
    return EB_OFF<=i<EB_OFF+EB_BYTES or EC_OFF<=i<EC_OFF+EC_BYTES

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--rom',type=Path,required=True)
    ap.add_argument('--expected-sha256',required=True)
    ap.add_argument('--font',type=Path,required=True)
    ap.add_argument('--out-rom',type=Path,required=True)
    ap.add_argument('--report',type=Path,required=True)
    a=ap.parse_args()
    src=a.rom.read_bytes()
    got=sha(src)
    if got.lower()!=a.expected_sha256.lower():
        raise SystemExit(f'REFUSED baseline SHA mismatch: {got}')
    if len(src)<BLANK_OFF+REC:
        raise SystemExit('REFUSED ROM too small for Stage432 layout')
    ptr=src[PTR_OFF:PTR_OFF+PTR_TOTAL*3]
    if ptr!=exp_ptr():
        raise SystemExit('REFUSED current pointer table is not exact Stage432 2400-entry layout')
    blank=src[BLANK_OFF:BLANK_OFF+REC]
    if blank!=bytes([0x0c])+bytes(24):
        raise SystemExit('REFUSED current blank fail-safe record mismatch')
    oldeb=src[EB_OFF:EB_OFF+EB_BYTES]
    oldec=src[EC_OFF:EC_OFF+EC_BYTES]
    orientation,ores=resolve_orientation(oldeb,oldec)
    if orientation is None:
        raise SystemExit('REFUSED current native12 orientation is ambiguous/nonconforming: '+json.dumps(ores))
    neweb,newec=build_font(a.font,orientation)
    dst=bytearray(src)
    dst[EB_OFF:EB_OFF+EB_BYTES]=neweb
    dst[EC_OFF:EC_OFF+EC_BYTES]=newec
    dst=bytes(dst)
    runs=diff_runs(src,dst)
    bad=[(s,e) for s,e in runs if any(not allowed(i) for i in range(s,e))]
    if bad:
        raise SystemExit('REFUSED non-font diff '+repr(bad[:8]))
    if dst[PTR_OFF:PTR_OFF+PTR_TOTAL*3]!=ptr:
        raise SystemExit('REFUSED pointer table changed')
    if dst[BLANK_OFF:BLANK_OFF+REC]!=blank:
        raise SystemExit('REFUSED blank fail-safe changed')
    changed=sum(e-s for s,e in runs)
    report={
      'schema':'MMR_STAGE1468_MONA12_FONT_ASSETS_ONLY_V1',
      'classification':'PASS_FONT_ASSETS_ONLY_CANDIDATE_BUILT',
      'baseline':{'name':a.rom.name,'bytes':len(src),'sha256':got},
      'candidate':{'name':a.out_rom.name,'bytes':len(dst),'sha256':sha(dst)},
      'font_input':{'name':a.font.name,'sha256':sha(a.font.read_bytes()),'redistributed':False},
      'orientation':orientation,
      'orientation_evidence':ores,
      'font_banks':{
        'old_eb_sha256':sha(oldeb),'old_ec_sha256':sha(oldec),
        'new_eb_sha256':sha(neweb),'new_ec_sha256':sha(newec),
        'new_eb_bytes':len(neweb),'new_ec_bytes':len(newec)
      },
      'changed_bytes':changed,
      'diff_run_count':len(runs),
      'diff_runs':[{'start':f'0x{s:06X}','end_exclusive':f'0x{e:06X}','bytes':e-s} for s,e in runs],
      'allowed_ranges':[
        {'label':'EB_FONT_1310','start':'0x358000','end_exclusive':f'0x{EB_OFF+EB_BYTES:06X}'},
        {'label':'EC_FONT_1040','start':'0x360000','end_exclusive':f'0x{EC_OFF+EC_BYTES:06X}'}
      ],
      'pointer_table_changed':False,
      'blank_failsafe_changed':False,
      'checksum_bytes_changed':False,
      'd12_kmode_ecc6_changed':False,
      'translation_bytes_changed':False,
      'source_token_0x58_changed':False,
      'runtime_status':'NOT_RUN',
      'new_real_evidence':False,
      'note':'Local diagnostic component candidate. Runtime PASS must be established separately.'
    }
    a.out_rom.write_bytes(dst)
    a.report.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False,indent=2))

if __name__=='__main__':
    main()
