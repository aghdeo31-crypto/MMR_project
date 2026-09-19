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
    ap.add_argument('--name-entry-original-compare',required=True)
    ap.add_argument('--name-entry-geometry',required=True)
    ap.add_argument('--runtime-matrix',required=True)
    ap.add_argument('--language-sweep',required=True)
    ap.add_argument('--candidate-sha256',required=True)
    ap.add_argument('-o','--out',required=True)
    a=ap.parse_args()
    cand=a.candidate_sha256.lower()
    docs={k:load(v) for k,v in {
      'parent':a.parent,
      'identity':a.identity,
      'font_quality':a.font_quality,
      'font_review':a.font_review,
      'font_diff':a.font_diff,
      'jp_translation':a.jp_translation,
      'name_entry_original_compare':a.name_entry_original_compare,
      'name_entry_geometry':a.name_entry_geometry,
      'runtime_matrix':a.runtime_matrix,
      'language_sweep':a.language_sweep}.items()}
    checks=[]

    def add(name,ok,detail):
        checks.append({'gate':name,'pass':bool(ok),'detail':detail})

    p=docs['parent']
    add('G0_exact_parent',p.get('pass') is True,p.get('classification'))

    ne=docs['name_entry_original_compare']
    ne_same=ne.get('candidate_sha256','').lower()==cand
    comps=ne.get('comparisons',[])
    ne_all=bool(comps) and all(x.get('status')=='PASS' for x in comps)
    add('G1_name_entry_original_compare',
        ne_same and ne_all and ne.get('classification')=='PASS_NAME_ENTRY_ORIGINAL_COMPARE',
        {'same_candidate':ne_same,'classification':ne.get('classification'),
         'pass_count':sum(x.get('status')=='PASS' for x in comps),'total':len(comps)})

    ng=docs['name_entry_geometry']
    ng_same=ng.get('candidate_sha256','').lower()==cand
    ng_checks=ng.get('checks') or {}
    add('G2_name_entry_geometry_auto',
        ng_same and ng.get('classification')=='PASS_NAME_ENTRY_GEOMETRY'
        and ng_checks.get('candidate_adjacent_row_overlap_zero') is True,
        {'same_candidate':ng_same,
         'classification':ng.get('classification'),
         'max_adjacent_row_overlap_px':(ng.get('candidate') or {}).get('max_adjacent_row_overlap_px'),
         'checks':ng_checks})

    i=docs['identity']
    add('G3_glyph_identity',
        i.get('classification')=='PASS_KS2350_IDENTITY' and not i.get('failures'),
        i.get('classification'))

    fq=docs['font_quality']
    add('G4_font_structure',
        fq.get('blank',1)==0 and fq.get('clipped',1)==0 and fq.get('duplicate_bitmap_groups',1)==0,
        fq.get('classification'))

    fr=docs['font_review']
    unresolved=fr.get('p0_unresolved')
    add('G5_font_art_review',
        unresolved==0 and fr.get('classification')=='PASS_FONT_ART_REVIEW',
        {'classification':fr.get('classification'),'p0_unresolved':unresolved})

    add('G6_small_font_family',
        fr.get('small_font_family_complete') is True,
        fr.get('small_font_family_status'))

    jp=docs['jp_translation']
    add('G7_japanese_original_translation',
        jp.get('classification') in ('PASS_JP_AUTHORITY_REVIEW_GATE','PASS_JP_TRANSLATION_FINAL'),
        jp.get('classification'))

    fd=docs['font_diff']
    fdsha=(fd.get('candidate') or {}).get('sha256','').lower()
    add('G8_static_binary_font_diff',
        fd.get('classification')=='PASS_FONT_ONLY_DIFF' and fdsha==cand and not fd.get('violations'),
        {'classification':fd.get('classification'),'candidate_sha':fdsha})

    rm=docs['runtime_matrix']
    paths=rm.get('paths',[])
    same=rm.get('candidate_sha256','').lower()==cand
    critical=[x for x in paths if x.get('critical') is True]
    all_critical=bool(critical) and all(x.get('status')=='PASS' for x in critical)
    all_paths=bool(paths) and all(x.get('status')=='PASS' for x in paths)
    add('G9_system_ui_name_entry_runtime',
        same and all_critical,
        {'same_candidate':same,
         'critical_pass':sum(x.get('status')=='PASS' for x in critical),
         'critical_total':len(critical)})
    add('G10_full_runtime_matrix',
        same and all_paths,
        {'same_candidate':same,
         'pass_count':sum(x.get('status')=='PASS' for x in paths),
         'total':len(paths)})

    ls=docs['language_sweep']
    same2=ls.get('candidate_sha256','').lower()==cand
    add('G11_language_art_sweep',
        same2 and ls.get('classification')=='PASS_LANGUAGE_ART_SWEEP',
        {'same_candidate':same2,'classification':ls.get('classification')})

    allowed=all(x['pass'] for x in checks)
    out={
      'schema':'MMR_THIRD_ATTEMPT_RELEASE_PROMOTION_V3_NAME_GEOMETRY_LOCKED',
      'candidate_sha256':cand,
      'classification':'RELEASE_ALLOWED' if allowed else 'HOLD_RELEASE_NOT_ALLOWED',
      'release_allowed':allowed,
      'checks':checks,
      'failed_gates':[x['gate'] for x in checks if not x['pass']],
      'hard_rules':[
        'Name-entry original-JP comparison must PASS on the same candidate SHA.',
        'Automatic name-entry geometry compare must PASS with adjacent-row overlap = 0 px.',
        'All critical SYSTEM/UI/NAME_ENTRY runtime paths must PASS.',
        'One exact candidate SHA only; no cross-build evidence mixing.'
      ]
    }
    Path(a.out).write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(out,ensure_ascii=False,indent=2))
    raise SystemExit(0 if allowed else 2)

if __name__=='__main__':
    main()
