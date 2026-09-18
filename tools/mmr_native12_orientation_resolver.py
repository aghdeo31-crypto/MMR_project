#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Resolve MMR Stage432-compatible native12 vertical bit orientation.

Read-only. Inspect either a headerless ROM containing Stage432-layout font
assets, or separate EB/EC font-bank files.

Primary proof is the 12-pixel-in-16-bit padding invariant across all 2350
records:
  bit0_top  => bits 12..15 are zero padding
  bit15_top => bits 0..3 are zero padding

If both/neither hypotheses are clean, return HOLD.
"""
from __future__ import annotations
import argparse, hashlib, json, struct
from pathlib import Path

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

def sha(b:bytes)->str:
    return hashlib.sha256(b).hexdigest()

def ptr_for_id(i:int)->bytes:
    if i<SPLIT:
        bank,addr=0xEB,0x8000+i*REC
    elif i<TOTAL:
        bank,addr=0xEC,0x8000+(i-SPLIT)*REC
    else:
        bank,addr=0xEC,0xE600
    return bytes((addr&0xff,(addr>>8)&0xff,bank))

def expected_ptr_table()->bytes:
    return b''.join(ptr_for_id(i) for i in range(PTR_TOTAL))

def records(eb:bytes,ec:bytes):
    if len(eb)!=EB_BYTES:
        raise ValueError(f'EB size {len(eb)} != {EB_BYTES}')
    if len(ec)!=EC_BYTES:
        raise ValueError(f'EC size {len(ec)} != {EC_BYTES}')
    blob=eb+ec
    for i in range(TOTAL):
        yield i,blob[i*REC:(i+1)*REC]

def analyze_padding(eb:bytes,ec:bytes):
    high_bad=low_bad=both_bad=width_bad=nonblank=0
    high_bits=low_bits=0
    pilots=[]
    for i,r in records(eb,ec):
        if r[0]!=0x0c: width_bad+=1
        words=struct.unpack('<12H',r[1:])
        nonblank+=int(any(words))
        hp=sum((w&0xF000).bit_count() for w in words)
        lp=sum((w&0x000F).bit_count() for w in words)
        high_bits+=hp
        low_bits+=lp
        hb=any(w&0xF000 for w in words)
        lb=any(w&0x000F for w in words)
        high_bad+=int(hb)
        low_bad+=int(lb)
        both_bad+=int(hb and lb)
        if i in (155,963,1379,1999):
            pilots.append({
                'id':i,'width':r[0],
                'words':[f'{w:04X}' for w in words],
                'high_padding_nonzero':hb,
                'low_padding_nonzero':lb,
            })
    bit0=(high_bad==0 and low_bad>0)
    bit15=(low_bad==0 and high_bad>0)
    if bit0 and not bit15:
        cls='PASS_BIT0_TOP'
        orient='bit0_top'
    elif bit15 and not bit0:
        cls='PASS_BIT15_TOP'
        orient='bit15_top'
    else:
        cls='HOLD_ORIENTATION_AMBIGUOUS'
        orient=None
    return {
        'classification':cls,'orientation':orient,'glyphs':TOTAL,
        'nonblank_records':nonblank,'width_byte_bad_records':width_bad,
        'records_with_nonzero_high_padding_bits_12_15':high_bad,
        'records_with_nonzero_low_padding_bits_0_3':low_bad,
        'records_with_both_padding_sides_nonzero':both_bad,
        'set_bits_in_high_nibble':high_bits,
        'set_bits_in_low_nibble':low_bits,
        'pilot_records':pilots,
        'proof_rule':'bit0_top: bits12..15 zero for all 2350 and low nibble used; bit15_top: bits0..3 zero for all 2350 and high nibble used',
    }

def extract_from_rom(path:Path):
    rom=path.read_bytes()
    need=BLANK_OFF+REC
    if len(rom)<need:
        raise ValueError(f'ROM too small {len(rom)} < {need}')
    ptr=rom[PTR_OFF:PTR_OFF+PTR_TOTAL*3]
    eb=rom[EB_OFF:EB_OFF+EB_BYTES]
    ec=rom[EC_OFF:EC_OFF+EC_BYTES]
    blank=rom[BLANK_OFF:BLANK_OFF+REC]
    exp=expected_ptr_table()
    return rom,eb,ec,{
        'pointer_table_exact':ptr==exp,
        'pointer_mismatch_bytes':sum(a!=b for a,b in zip(ptr,exp)),
        'pointer_sha256':sha(ptr),
        'expected_pointer_sha256':sha(exp),
        'blank_record_hex':blank.hex(' ').upper(),
        'blank_record_is_0C_plus_24_zero':blank==bytes([0x0c])+bytes(24),
    }

def main():
    ap=argparse.ArgumentParser()
    src=ap.add_mutually_exclusive_group(required=True)
    src.add_argument('--rom',type=Path)
    src.add_argument('--eb',type=Path)
    ap.add_argument('--ec',type=Path)
    ap.add_argument('-o','--out',type=Path,default=Path('MMR_NATIVE12_ORIENTATION_REPORT.json'))
    a=ap.parse_args()
    layout=None
    if a.rom:
        rom,eb,ec,layout=extract_from_rom(a.rom)
        source={'kind':'rom','name':a.rom.name,'bytes':len(rom),'sha256':sha(rom)}
    else:
        if not a.ec:
            ap.error('--ec is required with --eb')
        eb=a.eb.read_bytes()
        ec=a.ec.read_bytes()
        source={'kind':'banks','eb':a.eb.name,'eb_sha256':sha(eb),'ec':a.ec.name,'ec_sha256':sha(ec)}
    pad=analyze_padding(eb,ec)
    result={
        'schema':'MMR_NATIVE12_ORIENTATION_RESOLVER_V1',
        'source':source,
        'stage432_layout':{
            'pointer_file_offset':'0x354000',
            'eb_file_offset':'0x358000',
            'ec_file_offset':'0x360000',
            'blank_file_offset':'0x366600',
            'record_bytes':25,
            'glyphs':2350,
        },
        'layout_validation':layout,
        **pad,
        'safe_to_choose_orientation':pad['classification'].startswith('PASS_') and (layout is None or layout['pointer_table_exact']),
        'rom_written':False,
        'ips_written':False,
    }
    if layout is not None and not layout['pointer_table_exact']:
        result['classification']='HOLD_POINTER_LAYOUT_MISMATCH'
        result['orientation']=None
        result['safe_to_choose_orientation']=False
    a.out.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False,indent=2))
    return 0 if result['safe_to_choose_orientation'] else 2

if __name__=='__main__':
    raise SystemExit(main())
