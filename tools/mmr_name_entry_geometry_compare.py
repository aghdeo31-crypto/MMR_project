#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""MMR name-entry original-vs-candidate geometry comparator v2.

Input:
  original/row1.png ... row5.png
  candidate/row1.png ... row5.png

Each set must show the same page/state with only the cursor moved through rows
1..5. A tight grid crop is supplied as --crop X,Y,W,H.

The tool reconstructs a cursor-free screen by per-pixel median, isolates the
cursor/highlight in each capture by diffing against that median, measures
cursor bbox/center/Y-step, estimates visible text-row bboxes, and checks
adjacent-row overlap plus original-vs-candidate geometry.

No OCR. No ROM/emulator writes.
"""
from __future__ import annotations
import argparse,json,statistics
from pathlib import Path
from PIL import Image

ROWS=5

def load_set(d:Path):
    imgs=[]
    for i in range(1,ROWS+1):
        p=d/f"row{i}.png"
        if not p.is_file():raise FileNotFoundError(p)
        imgs.append(Image.open(p).convert("RGB"))
    size=imgs[0].size
    if any(im.size!=size for im in imgs):raise ValueError(f"capture size mismatch in {d}")
    return imgs

def median_rgb(images):
    w,h=images[0].size
    src=[im.load() for im in images]
    out=Image.new("RGB",(w,h));q=out.load()
    for y in range(h):
        for x in range(w):
            vals=[src[k][x,y] for k in range(5)]
            q[x,y]=tuple(sorted(v[c] for v in vals)[2] for c in range(3))
    return out

def color_dist(a,b):return max(abs(a[i]-b[i]) for i in range(3))

def bbox(coords):
    if not coords:return None
    xs=[x for x,y in coords];ys=[y for x,y in coords]
    return [min(xs),min(ys),max(xs)+1,max(ys)+1]

def diff_mask(im,base,crop,threshold):
    x0,y0,w,h=crop;p=im.load();b=base.load();out=[]
    for y in range(y0,y0+h):
        for x in range(x0,x0+w):
            if color_dist(p[x,y],b[x,y])>=threshold:out.append((x,y))
    return out

def mode_color(im,crop):
    x0,y0,w,h=crop
    c=im.crop((x0,y0,x0+w,y0+h)).getcolors(maxcolors=w*h)
    if c:return max(c,key=lambda z:z[0])[1]
    q=im.crop((x0,y0,x0+w,y0+h)).quantize(colors=16)
    n,idx=max(q.getcolors());pal=q.getpalette()
    return tuple(pal[idx*3:idx*3+3])

def row_visible_bboxes(base,crop,cursor_centers,threshold):
    x0,y0,w,h=crop;bg=mode_color(base,crop)
    centers=[c[1] for c in cursor_centers]
    bounds=[y0]+[int(round((a+b)/2)) for a,b in zip(centers,centers[1:])]+[y0+h]
    p=base.load();out=[]
    for r in range(ROWS):
        coords=[]
        for y in range(max(y0,bounds[r]),min(y0+h,bounds[r+1])):
            for x in range(x0,x0+w):
                if color_dist(p[x,y],bg)>=threshold:coords.append((x,y))
        out.append(bbox(coords))
    return out,bg

def overlap(a0,a1,b0,b1):return max(0,min(a1,b1)-max(a0,b0))

def analyze(images,crop,cursor_threshold,fg_threshold):
    base=median_rgb(images);boxes=[];centers=[];counts=[]
    for im in images:
        coords=diff_mask(im,base,crop,cursor_threshold);bb=bbox(coords)
        if bb is None:raise ValueError("cursor/highlight diff not detected")
        boxes.append(bb);counts.append(len(coords))
        centers.append(((bb[0]+bb[2]-1)/2,(bb[1]+bb[3]-1)/2))
    steps=[centers[i+1][1]-centers[i][1] for i in range(4)]
    row_boxes,bg=row_visible_bboxes(base,crop,centers,fg_threshold)
    ovs=[]
    for r,cb in enumerate(boxes):
        item={"row":r+1,"above_px":0,"below_px":0}
        if r and row_boxes[r-1]:
            item["above_px"]=overlap(cb[1],cb[3],row_boxes[r-1][1],row_boxes[r-1][3])
        if r<4 and row_boxes[r+1]:
            item["below_px"]=overlap(cb[1],cb[3],row_boxes[r+1][1],row_boxes[r+1][3])
        ovs.append(item)
    vh=[b[3]-b[1] if b else 0 for b in row_boxes]
    return {
      "cursor_bboxes":boxes,
      "cursor_centers":centers,
      "cursor_widths":[b[2]-b[0] for b in boxes],
      "cursor_heights":[b[3]-b[1] for b in boxes],
      "cursor_changed_pixels":counts,
      "row_steps_y":steps,
      "row_step_mean":statistics.mean(steps),
      "row_step_range":max(steps)-min(steps),
      "cursor_height_mean":statistics.mean(b[3]-b[1] for b in boxes),
      "cursor_width_mean":statistics.mean(b[2]-b[0] for b in boxes),
      "static_row_visible_bboxes":row_boxes,
      "static_row_visible_heights":vh,
      "static_row_visible_height_mean":statistics.mean(vh),
      "adjacent_row_overlap":ovs,
      "max_adjacent_row_overlap_px":max(max(x["above_px"],x["below_px"]) for x in ovs),
      "background_rgb":bg,
      "static_image":base
    }

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--original",type=Path,required=True)
    ap.add_argument("--candidate",type=Path,required=True)
    ap.add_argument("--crop",required=True,help="X,Y,W,H")
    ap.add_argument("--cursor-threshold",type=int,default=24)
    ap.add_argument("--fg-threshold",type=int,default=18)
    ap.add_argument("--row-step-tolerance",type=float,default=1.0)
    ap.add_argument("--cursor-height-tolerance",type=float,default=1.0)
    ap.add_argument("--font-height-tolerance",type=float,default=2.0)
    ap.add_argument("--out",type=Path,required=True)
    a=ap.parse_args()
    crop=tuple(int(x,0) for x in a.crop.split(","))
    if len(crop)!=4 or crop[2]<=0 or crop[3]<=0:raise SystemExit("bad --crop X,Y,W,H")
    oi=load_set(a.original);ci=load_set(a.candidate)
    if oi[0].size!=ci[0].size:raise SystemExit("original/candidate screenshot dimensions differ")
    o=analyze(oi,crop,a.cursor_threshold,a.fg_threshold)
    c=analyze(ci,crop,a.cursor_threshold,a.fg_threshold)
    a.out.mkdir(parents=True,exist_ok=True)
    o["static_image"].save(a.out/"ORIGINAL_static_median.png")
    c["static_image"].save(a.out/"CANDIDATE_static_median.png")
    del o["static_image"];del c["static_image"]
    checks={
      "candidate_adjacent_row_overlap_zero":c["max_adjacent_row_overlap_px"]==0,
      "candidate_row_step_stable":c["row_step_range"]<=a.row_step_tolerance,
      "original_row_step_stable":o["row_step_range"]<=a.row_step_tolerance,
      "row_step_matches_original":abs(c["row_step_mean"]-o["row_step_mean"])<=a.row_step_tolerance,
      "cursor_height_matches_original":abs(c["cursor_height_mean"]-o["cursor_height_mean"])<=a.cursor_height_tolerance,
      "name_font_visible_height_matches_original":abs(c["static_row_visible_height_mean"]-o["static_row_visible_height_mean"])<=a.font_height_tolerance
    }
    passed=all(checks.values())
    report={
      "schema":"MMR_NAME_ENTRY_GEOMETRY_COMPARE_V2_AUTO_CAPTURE",
      "classification":"PASS_NAME_ENTRY_GEOMETRY" if passed else "FAIL_NAME_ENTRY_GEOMETRY",
      "crop_xywh":crop,
      "thresholds":{"cursor":a.cursor_threshold,"foreground":a.fg_threshold},
      "tolerances":{"row_step_px":a.row_step_tolerance,"cursor_height_px":a.cursor_height_tolerance,"font_visible_height_px":a.font_height_tolerance},
      "original":o,"candidate":c,"checks":checks,
      "hard_rule":"Candidate adjacent-row overlap must be 0 px. Five captures must be same page/state and evidence must belong to one exact candidate SHA."
    }
    (a.out/"MMR_NAME_ENTRY_GEOMETRY_COMPARE.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps(report,ensure_ascii=False,indent=2))
    raise SystemExit(0 if passed else 2)

if __name__=="__main__":main()
