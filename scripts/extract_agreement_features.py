#!/usr/bin/env python3
"""Extract agreement features between baseline and distmap predictions.

NOTE: This script requires the baseline/DistMap prediction NIfTIs (not shipped
with the repo — too large). It is NOT runnable from the cloned repo alone —
the output CSV (data/patient_agreement_features.csv) is pre-computed and
shipped so downstream analysis scripts ARE runnable. Edit the input paths
below to re-extract agreement features locally.

Features (per patient, computed from preds only, no GT needed) :
  dice_B_D_WT, dice_B_D_TC, dice_B_D_ET     # Dice(baseline, distmap) per region
  vol_diff_B_D_ET, vol_diff_B_D_NCR         # abs(|B|-|D|) / (|B|+|D|)  (symmetric)
  n_no_overlap_distmap_ET, n_no_overlap_distmap_NCR   # nb DistMap CC that fusion will remove
  frac_removed_distmap_ET, frac_removed_distmap_NCR   # fraction of DistMap voxels removed by fusion
  max_orphan_cc_ET, max_orphan_cc_NCR       # largest DistMap CC without baseline overlap (vx)
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

PRED_B = Path("/home/ser/Bureau/BRATS/outputs/predictions/baseline")
PRED_D = Path("/home/ser/Bureau/BRATS/outputs/predictions/distmap")
RANKINGS = Path("/home/ser/Bureau/BRATS/viewer/V3/static_bundle/rankings.json")
OUT_CSV = Path("/home/ser/Bureau/BRATS/outputs/patient_agreement_features.csv")

STRUCT_26 = ndi.generate_binary_structure(3, 3)

FIELDS = [
    "patient_id",
    "dice_B_D_WT", "dice_B_D_TC", "dice_B_D_ET",
    "vol_diff_B_D_ET", "vol_diff_B_D_NCR",
    "n_no_overlap_distmap_ET", "n_no_overlap_distmap_NCR",
    "frac_removed_distmap_ET", "frac_removed_distmap_NCR",
    "max_orphan_cc_ET", "max_orphan_cc_NCR",
]

def load(p): return nib.load(str(p)).get_fdata().astype(np.uint8)

def dice_bin(a, b):
    a_sum = int(a.sum()); b_sum = int(b.sum())
    if a_sum == 0 and b_sum == 0: return 1.0
    inter = int(np.logical_and(a, b).sum())
    denom = a_sum + b_sum
    return 2.0 * inter / denom if denom > 0 else 0.0

def process_one(pid):
    try:
        bp_path = PRED_B / f"{pid}.nii.gz"
        dp_path = PRED_D / f"{pid}.nii.gz"
        if not bp_path.exists() or not dp_path.exists():
            return None
        bp = load(bp_path); dp = load(dp_path)
        # Regions
        B_WT = bp > 0; D_WT = dp > 0
        B_TC = (bp == 1) | (bp == 3); D_TC = (dp == 1) | (dp == 3)
        B_ET = (bp == 3); D_ET = (dp == 3)
        B_NCR = (bp == 1); D_NCR = (dp == 1)

        dice_WT = dice_bin(B_WT, D_WT)
        dice_TC = dice_bin(B_TC, D_TC)
        dice_ET = dice_bin(B_ET, D_ET)

        def vol_diff(a, b):
            va = int(a.sum()); vb = int(b.sum())
            s = va + vb
            return (abs(va - vb) / s) if s > 0 else 0.0

        vd_ET = vol_diff(B_ET, D_ET)
        vd_NCR = vol_diff(B_NCR, D_NCR)

        def orphan_stats(d_mask, b_mask):
            """nb CC in d_mask that would be fully removed by fusion, their max size,
               and fraction of DistMap voxels removed."""
            if not d_mask.any():
                return 0, 0, 0.0
            lab, n = ndi.label(d_mask, structure=STRUCT_26)
            if n == 0:
                return 0, 0, 0.0
            n_removed = 0; max_size = 0; removed_vx = 0; total = int(d_mask.sum())
            for cc_id in range(1, n + 1):
                cc = (lab == cc_id)
                sz = int(cc.sum())
                if not np.any(cc & b_mask):
                    n_removed += 1
                    removed_vx += sz
                    if sz > max_size:
                        max_size = sz
            return n_removed, max_size, (removed_vx / total) if total > 0 else 0.0

        n_rm_ET, mx_ET, fr_ET = orphan_stats(D_ET, B_ET)
        n_rm_NCR, mx_NCR, fr_NCR = orphan_stats(D_NCR, B_NCR)

        return [
            pid,
            round(dice_WT, 6), round(dice_TC, 6), round(dice_ET, 6),
            round(vd_ET, 6), round(vd_NCR, 6),
            n_rm_ET, n_rm_NCR,
            round(fr_ET, 6), round(fr_NCR, 6),
            mx_ET, mx_NCR,
        ]
    except Exception as e:
        print(f"[err {pid}] {e}", flush=True); return None

def main():
    data = json.loads(RANKINGS.read_text())
    tasks = [r["patient_id"] for r in data["rows"]
             if r.get("baseline") and r.get("distmap") and r.get("fusion")]
    print(f"[start] {len(tasks)} patients")
    t0 = time.time(); done = 0
    with OUT_CSV.open("w", newline="") as fout:
        w = csv.writer(fout); w.writerow(FIELDS); fout.flush()
        with Pool(processes=10) as pool:
            for row in pool.imap_unordered(process_one, tasks, chunksize=4):
                if row is not None: w.writerow(row)
                done += 1
                if done % 100 == 0:
                    fout.flush()
                    el = time.time() - t0; rate = done / el; eta = (len(tasks) - done) / rate if rate else 0
                    print(f"[{done}/{len(tasks)}] {el:.0f}s eta={eta:.0f}s", flush=True)
    print(f"[done] {done}/{len(tasks)} in {time.time() - t0:.0f}s -> {OUT_CSV}")

if __name__ == "__main__":
    main()
