#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""MMR Stage1467 FONT_ONLY binary diff gate.

Compares an exact Stage1467 baseline ROM with a font-only candidate. Changes are
allowed only inside explicit file-offset ranges supplied by JSON. This tool does
not know or guess MMR font locations.
"""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path

def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()

def num(v):
    if isinstance(v, int):
        return v
    if isinstance(v, str):
        return int(v, 0)
    raise TypeError(v)

def load_ranges(path: Path):
    obj = json.loads(path.read_text(encoding='utf-8'))
    out=[]
    for r in obj.get('ranges', []):
        s=num(r['start']); e=num(r['end_exclusive'])
        if not (0 <= s < e):
            raise ValueError(f'bad range: {r}')
        out.append((s,e,str(r.get('label','font'))))
    if not out:
        raise ValueError('no allowed ranges')
    return obj, out

def allowed(off, ranges):
    return any(s <= off < e for s,e,_ in ranges)

def diff_runs(a: bytes, b: bytes):
    if len(a) != len(b):
        raise ValueError(f'size mismatch: {len(a)} != {len(b)}')
    runs=[]; start=None
    for i,(x,y) in enumerate(zip(a,b)):
        if x != y and start is None:
            start=i
        elif x == y and start is not None:
            runs.append((start,i)); start=None
    if start is not None:
        runs.append((start,len(a)))
    return runs

def main():
    ap=argparse.ArgumentParser(description='MMR Stage1467 font-only diff gate')
    ap.add_argument('baseline', type=Path)
    ap.add_argument('candidate', type=Path)
    ap.add_argument('--allowed-ranges', type=Path, required=True)
    ap.add_argument('--out', type=Path, default=Path('MMR_FONT_ONLY_DIFF_REPORT.json'))
    ns=ap.parse_args()
    a=ns.baseline.read_bytes(); b=ns.candidate.read_bytes()
    spec,ranges=load_ranges(ns.allowed_ranges)
    runs=diff_runs(a,b)
    changed=sum(e-s for s,e in runs)
    bad=[]; per=[]
    for s,e in runs:
        outside=[i for i in range(s,e) if not allowed(i,ranges)]
        rec={'start':s,'end_exclusive':e,'bytes':e-s,
             'start_hex':f'0x{s:06X}','end_exclusive_hex':f'0x{e:06X}',
             'outside_allowed_count':len(outside)}
        per.append(rec)
        if outside:
            bad.append({'run':rec,'first_outside_hex':f'0x{outside[0]:06X}'})
    cls='PASS_FONT_ONLY_DIFF' if not bad else 'FAIL_NON_FONT_CHANGE_DETECTED'
    report={
        'schema':'MMR_STAGE1467_FONT_ONLY_DIFF_GATE_V1',
        'classification':cls,
        'baseline':{'name':ns.baseline.name,'size':len(a),'sha256':sha256_bytes(a)},
        'candidate':{'name':ns.candidate.name,'size':len(b),'sha256':sha256_bytes(b)},
        'allowed_range_schema':spec.get('schema'),
        'allowed_ranges':[{'start_hex':f'0x{s:06X}','end_exclusive_hex':f'0x{e:06X}','label':lab} for s,e,lab in ranges],
        'changed_bytes':changed,
        'diff_run_count':len(runs),
        'diff_runs':per,
        'violations':bad,
        'stage1467_semantics_assumed':False,
        'note':'Allowed font ranges must come from current Stage1467 packer/slot authority; this gate never guesses them.'
    }
    ns.out.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False,indent=2))
    raise SystemExit(0 if cls.startswith('PASS') else 2)

if __name__=='__main__':
    main()
