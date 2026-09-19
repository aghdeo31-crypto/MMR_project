#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""MMR name-entry original-vs-candidate geometry ledger calculator.

This tool intentionally does not guess geometry from screenshots.
Feed measured coordinates from JP original and KR candidate JSON.

Input JSON example:
{
  "original": {
    "glyph_bbox_h": 9,
    "row_centers_y": [62,74,86,98,110],
    "cursor_boxes": [[10,56,19,67], ...]
  },
  "candidate": {...}
}

The tool derives row step consistency, cursor height, cursor-center alignment,
and adjacent-row overlap risk. Screenshot measurement/probe is separate.
"""
from __future__ import annotations
import argparse,json,statistics
from pathlib import Path

def side(d):
 rows=d['row_centers_y'];boxes=d['cursor_boxes']
 if len(rows)<2 or len(boxes)!=len(rows):raise ValueError('row/box count mismatch')
 steps=[rows[i+1]-rows[i] for i in range(len(rows)-1)]
 heights=[b[3]-b[1] for b in boxes]
 centers=[(b[1]+b[3])/2 for b in boxes]
 offsets=[centers[i]-rows[i] for i in range(len(rows))]
 return {
  'row_steps':steps,'row_step_min':min(steps),'row_step_max':max(steps),
  'row_step_constant':len(set(steps))==1,
  'cursor_heights':heights,'cursor_height_constant':len(set(heights))==1,
  'cursor_center_offsets':offsets,
  'cursor_center_offset_constant':max(offsets)-min(offsets)<=0.5,
  'glyph_bbox_h':d['glyph_bbox_h']
 }

def main():
 ap=argparse.ArgumentParser()
 ap.add_argument('measurements',type=Path)
 ap.add_argument('-o','--out',type=Path,required=True)
 a=ap.parse_args();m=json.loads(a.measurements.read_text(encoding='utf-8'))
 o=side(m['original']);k=side(m['candidate'])
 # Conservative visible-row-overlap condition:
 # cursor height must not reach the next row's visible glyph body.
 kstep=min(k['row_steps']);kh=max(k['cursor_heights']);gh=k['glyph_bbox_h']
 safe=(kh<=kstep and k['row_step_constant'] and k['cursor_height_constant'] and k['cursor_center_offset_constant'])
 out={
  'schema':'MMR_NAME_ENTRY_GEOMETRY_COMPARE_V1',
  'classification':'PASS_GEOMETRY_STATIC_MEASUREMENT' if safe else 'FAIL_GEOMETRY_MEASUREMENT',
  'original':o,'candidate':k,
  'candidate_cursor_height_le_row_step':kh<=kstep,
  'candidate_adjacent_row_overlap_risk':not (kh<=kstep),
  'same_row_step_as_original':o['row_steps']==k['row_steps'],
  'same_cursor_height_as_original':o['cursor_heights']==k['cursor_heights'],
  'rule':'Runtime capture still required; this calculator validates measured geometry only.'
 }
 a.out.write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps(out,ensure_ascii=False,indent=2))
 raise SystemExit(0 if safe else 2)

if __name__=='__main__':main()
