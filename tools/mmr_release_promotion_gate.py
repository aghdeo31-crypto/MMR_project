#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""MMR third-attempt release promotion gate.

Fail closed. It never builds a ROM; it only decides whether one exact candidate
SHA has enough evidence to be called release-ready.
"""
from __future__ import annotations
import argparse,json
from pathlib import Path

def load(p):
    return json.loads(Path(p).read_text(encoding='utf-8-sig'))

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--parent',required=True)
    ap.add_argument('--identity',required=True)
    ap.add_argument('--font-quality',required=True)
    ap.add_argument('--font-review',required=True)
    ap.add_argument('--font-diff',required=True)
    ap.add_argument('--jp-translation',required=True)
    ap.add_argument('--runtime-matrix',required=True)
    ap.add_argument('--language-sweep',required=True)
    ap.add_argument('--candidate-sha256',required=True)
    ap.add_argument('-o','--out',required=True)
    a=ap.parse_args()
    cand=a.candidate_sha256.lower()
    docs={k:load(v) for k,v in {
      'parent':a.parent,'identity':a.identity,'font_quality':a.font_quality,
      'font_review':a.font_review,'font_diff':a.font_diff,'jp_translation':a.jp_translation,
      'runtime_matrix':a.runtime_matrix,'language_sweep':a.language_sweep}.items()}
    checks=[]

    def add(name,ok,detail):
        checks.append({'gate':name,'pass':bool(ok),'detail':detail})

    p=docs['parent']
    add('G0_exact_parent', p.get('pass') is True, p.get('classification'))

    i=docs['identity']
    add('G1_glyph_identity',
        i.get('classification')=='PASS_KS2350_IDENTITY' and not i.get('failures'),
        i.get('classification'))

    fq=docs['font_quality']
    add('G2_font_structure',
        fq.get('blank',1)==0 and fq.get('clipped',1)==0 and fq.get('duplicate_bitmap_groups',1)==0,
        fq.get('classification'))

    fr=docs['font_review']
    unresolved=fr.get('p0_unresolved')
    add('G3_font_art_review', unresolved==0 and fr.get('classification')=='PASS_FONT_ART_REVIEW',
        {'classification':fr.get('classification'),'p0_unresolved':unresolved})

    fd=docs['font_diff']
    fdsha=(fd.get('candidate') or {}).get('sha256','').lower()
    add('G6_static_binary_font_diff',
        fd.get('classification')=='PASS_FONT_ONLY_DIFF' and fdsha==cand and not fd.get('violations'),
        {'classification':fd.get('classification'),'candidate_sha':fdsha})

    jp=docs['jp_translation']
    add('G5_japanese_original_translation',
        jp.get('classification') in ('PASS_JP_AUTHORITY_REVIEW_GATE','PASS_JP_TRANSLATION_FINAL'),
        jp.get('classification'))

    rm=docs['runtime_matrix']
    paths=rm.get('paths',[])
    same=rm.get('candidate_sha256','').lower()==cand
    allpass=bool(paths) and all(x.get('status')=='PASS' for x in paths)
    add('G7_runtime_matrix',same and allpass,
        {'same_candidate':same,'pass_count':sum(x.get('status')=='PASS' for x in paths),'total':len(paths)})

    ls=docs['language_sweep']
    same2=ls.get('candidate_sha256','').lower()==cand
    add('G8_language_art_sweep',same2 and ls.get('classification')=='PASS_LANGUAGE_ART_SWEEP',
        {'same_candidate':same2,'classification':ls.get('classification')})

    # G4 small font family is represented in runtime matrix + explicit font review manifest.
    small_ok=fr.get('small_font_family_complete') is True
    add('G4_small_font_family',small_ok,fr.get('small_font_family_status'))

    allowed=all(x['pass'] for x in checks)
    out={
      'schema':'MMR_THIRD_ATTEMPT_RELEASE_PROMOTION_V1',
      'candidate_sha256':cand,
      'classification':'RELEASE_ALLOWED' if allowed else 'HOLD_RELEASE_NOT_ALLOWED',
      'release_allowed':allowed,
      'checks':checks,
      'failed_gates':[x['gate'] for x in checks if not x['pass']],
      'rule':'One exact candidate SHA only; no cross-build evidence mixing.'
    }
    Path(a.out).write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(out,ensure_ascii=False,indent=2))
    raise SystemExit(0 if allowed else 2)

if __name__=='__main__':main()
