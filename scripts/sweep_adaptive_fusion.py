#!/usr/bin/env python3
"""Sweep size-adaptive fusion thresholds and compare to the default rule.

Default rule (fuse_predictions in evaluate_cv_fusion.py):
  For each class, remove DistMap CC if no overlap with Baseline same class.

Adaptive rule:
  Remove DistMap CC if (no overlap with Baseline) AND (CC size <= threshold_vx).
  Threshold=0 reproduces the default rule.

Output: CSV per (threshold, patient) with Dice WT/TC/ET avg + case classification
relative to threshold-specific fusion.
"""
import csv
import json
import sys
import time
from pathlib import Path
from multiprocessing import Pool

import numpy as np
import nibabel as nib
from scipy import ndimage as ndi

RANKINGS = Path("/home/ser/Bureau/BRATS/viewer/V3/static_bundle/rankings.json")
GT_DIR = Path("/home/ser/Bureau/BRATS/data/processed/brats_unified")
PRED_B = Path("/home/ser/Bureau/BRATS/outputs/predictions/baseline")
PRED_D = Path("/home/ser/Bureau/BRATS/outputs/predictions/distmap")
OUT_DIR = Path("/home/ser/Bureau/BRATS/outputs/adaptive_fusion_sweep")
OUT_DIR.mkdir(exist_ok=True)

STRUCT_26 = ndi.generate_binary_structure(3, 3)
CLASSES = (1, 2, 3)
THRESHOLDS = [20, 50, 100, 200, 500, 10**9]  # 10^9 = effectively infinite → reproduces default rule

def load(p): return nib.load(str(p)).get_fdata().astype(np.uint8)

def dice(pred, gt, cls_mask):
    if cls_mask == "WT": p_, g_ = pred > 0, gt > 0
    elif cls_mask == "TC": p_, g_ = (pred == 1) | (pred == 3), (gt == 1) | (gt == 3)
    else: p_, g_ = pred == 3, gt == 3
    p_sum = int(p_.sum()); g_sum = int(g_.sum())
    if p_sum == 0 and g_sum == 0: return 1.0
    inter = int(np.logical_and(p_, g_).sum())
    denom = p_sum + g_sum
    return 2.0 * inter / denom if denom > 0 else 0.0

def process_one(task):
    """Label each class once, then derive all threshold fusions by incremental removal.
    Small CCs get removed first (lowest threshold); bigger thresholds cumulatively remove more."""
    pid, fold, b_avg, d_avg = task
    try:
        gt = load(GT_DIR / pid / f"{pid}-seg.nii.gz")
        bp = load(PRED_B / f"{pid}.nii.gz")
        dp = load(PRED_D / f"{pid}.nii.gz")

        # Per class: list of (cc_size, cc_mask) for CCs without baseline overlap.
        removable_per_class = {}
        for cls in CLASSES:
            dmask = (dp == cls); bmask = (bp == cls)
            if not dmask.any():
                removable_per_class[cls] = []
                continue
            lab, n = ndi.label(dmask, structure=STRUCT_26)
            if n == 0:
                removable_per_class[cls] = []
                continue
            no_overlap = []
            for cc_id in range(1, n + 1):
                cc = (lab == cc_id)
                size = int(cc.sum())
                if not np.any(cc & bmask):
                    no_overlap.append((size, cc))
            no_overlap.sort(key=lambda x: x[0])
            removable_per_class[cls] = no_overlap

        out = {"pid": pid, "fold": fold, "b_avg": b_avg, "d_avg": d_avg}
        for thr in THRESHOLDS:
            fused = dp.copy()
            for cls in CLASSES:
                for size, cc in removable_per_class[cls]:
                    if size <= thr:
                        fused[cc] = 0
                    else:
                        break  # sorted ascending
            wt = dice(fused, gt, "WT"); tc = dice(fused, gt, "TC"); et = dice(fused, gt, "ET")
            out[f"f{thr}_WT"] = round(wt, 6)
            out[f"f{thr}_TC"] = round(tc, 6)
            out[f"f{thr}_ET"] = round(et, 6)
            out[f"f{thr}_avg"] = round((wt + tc + et) / 3.0, 6)
        return out
    except Exception as e:
        print(f"[err {pid}] {e}", flush=True)
        return None

def main():
    data = json.loads(RANKINGS.read_text())
    tasks = []
    for r in data["rows"]:
        b = r.get("baseline"); d = r.get("distmap"); f = r.get("fusion")
        if not (b and d and f): continue
        tasks.append((r["patient_id"], str(r.get("fold", "")),
                       b.get("dice_avg"), d.get("dice_avg")))
    print(f"[start] {len(tasks)} patients × {len(THRESHOLDS)} thresholds")
    out_csv = OUT_DIR / "sweep.csv"
    fields = ["pid","fold","b_avg","d_avg"] + [
        f"f{thr}_{suf}" for thr in THRESHOLDS for suf in ("WT","TC","ET","avg")
    ]
    t0 = time.time(); done = 0
    with out_csv.open("w", newline="") as fout:
        w = csv.DictWriter(fout, fieldnames=fields)
        w.writeheader()
        with Pool(processes=10) as pool:
            for row in pool.imap_unordered(process_one, tasks, chunksize=2):
                if row is not None: w.writerow(row)
                done += 1
                if done % 50 == 0:
                    fout.flush()
                    el = time.time() - t0; rate = done / el; eta = (len(tasks) - done) / rate if rate else 0
                    print(f"[{done}/{len(tasks)}] {el:.0f}s eta={eta:.0f}s", flush=True)
    print(f"[done] {done}/{len(tasks)} in {time.time() - t0:.0f}s -> {out_csv}")

if __name__ == "__main__":
    main()
