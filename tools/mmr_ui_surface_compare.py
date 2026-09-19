#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""MMR original-vs-candidate UI text-surface geometry comparator.

For fixed text/UI regions, not name-entry cursor motion.
A manifest supplies text-only crop rectangles. The tool measures visible
foreground bbox/height within each crop relative to the dominant background
color and compares Japanese original vs Korean candidate.

No OCR; wording may differ. Goal: font occupancy/baseline/overflow.
"""
from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path
from PIL import Image

JP_SHA="6a68e1806d8d72accb4a5218330210e178880216863c1c38b8865032c5c28724"

def sha(p):
    h=hashlib.sha256()
    with Path(p).open("rb") as f:
        for b in iter(lambda:f.read(1<<20),b""):h.update(b)
    return h.hexdigest()

def dist(a,b):return max(abs(a[i]-b[i]) for i in range(3))

def mode_color(im,box):
    c=im.crop(box).getcolors(maxcolors=(box[2]-box[0])*(box[3]-box[1]))
    if c:return max(c,key=lambda z:z[0])[1]
    q=im.crop(box).quantize(colors=16);n,idx=max(q.getcolors());pal=q.getpalette()
    return tuple(pal[idx*3:idx*3+3])

def measure(im,crop,threshold):
    x,y,w,h=crop;box=(x,y,x+w,y+h);bg=mode_color(im,box);p=im.load();pts=[]
    for yy in range(y,y+h):
        for xx in range(x,x+w):
            if dist(p[xx,yy],bg)>=threshold:pts.append((xx,yy))
    if not pts:
        return {"empty":True,"background_rgb":bg,"bbox":None,"visible_w":0,"visible_h":0,
                "top_margin":None,"bottom_margin":None,"left_margin":None,"right_margin":None,
                "touches_crop_edge":False,"foreground_pixels":0}
    xs=[q[0] for q in pts];ys=[q[1] for q in pts]
    b=[min(xs),min(ys),max(xs)+1,max(ys)+1]
    return {"empty":False,"background_rgb":bg,"bbox":b,"visible_w":b[2]-b[0],"visible_h":b[3]-b[1],
            "top_margin":b[1]-y,"bottom_margin":y+h-b[3],"left_margin":b[0]-x,"right_margin":x+w-b[2],
            "touches_crop_edge":b[0]<=x or b[1]<=y or b[2]>=x+w or b[3]>=y+h,
            "foreground_pixels":len(pts)}

def size_class(h):
    if h<=0:return "EMPTY"
    if h<=9:return "SMALL_9_OR_LESS"
    if h<=12:return "MEDIUM_10_12"
    return "LARGE_13_PLUS"

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--original",type=Path,required=True)
    ap.add_argument("--candidate",type=Path,required=True)
    ap.add_argument("--manifest",type=Path,required=True)
    ap.add_argument("--candidate-sha256",required=True)
    ap.add_argument("--original-rom-sha256",default=JP_SHA)
    ap.add_argument("--out",type=Path,required=True)
    a=ap.parse_args()
    if a.original_rom_sha256.lower()!=JP_SHA:raise SystemExit("REFUSED wrong JP ROM SHA")
    cand=a.candidate_sha256.lower()
    if len(cand)!=64 or any(c not in "0123456789abcdef" for c in cand):raise SystemExit("bad candidate sha")
    o=Image.open(a.original).convert("RGB");c=Image.open(a.candidate).convert("RGB")
    if o.size!=c.size:raise SystemExit("screenshot size mismatch")
    m=json.loads(a.manifest.read_text(encoding="utf-8-sig"));regions=m.get("regions") or []
    if not regions:raise SystemExit("manifest has no regions")
    results=[];allpass=True
    for r in regions:
        crop=r["crop"];th=int(r.get("threshold",18))
        ht=float(r.get("height_tolerance_px",2));at=float(r.get("anchor_tolerance_px",2))
        om=measure(o,crop,th);cm=measure(c,crop,th)
        checks={
          "original_nonempty":not om["empty"],
          "candidate_nonempty":not cm["empty"],
          "candidate_no_crop_edge_touch":not cm["touches_crop_edge"],
          "visible_height_matches":not om["empty"] and not cm["empty"] and abs(cm["visible_h"]-om["visible_h"])<=ht,
          "top_anchor_matches":not om["empty"] and not cm["empty"] and abs(cm["top_margin"]-om["top_margin"])<=at
        }
        passed=all(checks.values());allpass &= passed
        results.append({"id":r["id"],"crop":crop,"original":om,"candidate":cm,
                        "original_size_class":size_class(om["visible_h"]),
                        "candidate_size_class":size_class(cm["visible_h"]),
                        "checks":checks,"pass":passed})
    report={
      "schema":"MMR_UI_SURFACE_COMPARE_V1",
      "classification":"PASS_UI_FONT_SURFACES" if allpass else "FAIL_UI_FONT_SURFACES",
      "original_rom_sha256":JP_SHA,"candidate_sha256":cand,
      "evidence":{"original_png":a.original.name,"original_png_sha256":sha(a.original),
                  "candidate_png":a.candidate.name,"candidate_png_sha256":sha(a.candidate),
                  "manifest":a.manifest.name,"manifest_sha256":sha(a.manifest)},
      "regions":results,"pass_count":sum(x["pass"] for x in results),"total":len(results),
      "rule":"Crops must contain text content only. Candidate may differ in wording but must preserve original occupancy class and avoid crop overflow."
    }
    a.out.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps(report,ensure_ascii=False,indent=2))
    raise SystemExit(0 if allpass else 2)

if __name__=="__main__":main()
