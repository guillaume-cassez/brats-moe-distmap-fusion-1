#!/usr/bin/env python3
"""Compute per-class HD95 on 1196 CV patients for Baseline / DistMap / CC-Consensus.

Per-class = on individual labels {NCR=1, ED=2, ET=3}, not on nested regions
{WT, TC, ET} which are the standard BraTS composition. Clinically the per-class
view is essential: fragments concentrate on NCR and ED.

CC-Consensus is computed on-the-fly (veto DistMap CCs without Baseline overlap).

Output CSV columns:
  patient_id, fold,
  hd95_NCR_B, hd95_NCR_D, hd95_NCR_F,
  hd95_ED_B,  hd95_ED_D,  hd95_ED_F,
  hd95_ETc_B, hd95_ETc_D, hd95_ETc_F   (ETc = class-3-only, same as region ET)

Conventions:
  - both empty -> HD95 = 0
  - one empty  -> HD95 = NaN (dropped at aggregation)

NOTE: Requires tower-local GT + baseline/distmap prediction NIfTIs (not
redistributed). The analysis output is pre-computed and shipped as
analysis/hd95_per_class_cv.csv.
"""
import csv
import json
import numpy as np
import nibabel as nib
from pathlib import Path
from scipy.ndimage import label as cc_label, generate_binary_structure
from medpy.metric.binary import hd95
from multiprocessing import Pool
import sys, os

BASE_PRED = Path("/home/ser/Bureau/BRATS/outputs/predictions/baseline")
DIST_PRED = Path("/home/ser/Bureau/BRATS/outputs/predictions/distmap")
GT_DIR    = Path("/home/ser/Bureau/BRATS/nnunet_data/preprocessed/Dataset001_BraTS2023GLI/gt_segmentations")
OUT_CSV   = Path("/home/ser/Bureau/BRATS/outputs/hd95_per_class_cv.csv")
SPLITS    = Path("/home/ser/Bureau/BRATS/nnunet_data/preprocessed/Dataset001_BraTS2023GLI/splits_final.json")

STRUCT_26 = generate_binary_structure(3, 3)

def cc_consensus(Pd, Pb):
    """Apply CC-consensus filter: start from Pd, drop CC whose same-class mask has no overlap with Pb."""
    Pf = Pd.copy()
    for c in (1, 2, 3):
        dmask = (Pd == c)
        bmask = (Pb == c)
        if not dmask.any():
            continue
        labeled, n = cc_label(dmask, structure=STRUCT_26)
        for cc_id in range(1, n + 1):
            cc = (labeled == cc_id)
            if not (cc & bmask).any():
                Pf[cc] = 0
    return Pf

def safe_hd95(pred, gt, voxelspacing=None):
    if not pred.any() and not gt.any():
        return 0.0
    if not pred.any() or not gt.any():
        return np.nan
    return hd95(pred, gt, voxelspacing=voxelspacing)

def process(pid_fold):
    pid, fold = pid_fold
    try:
        pb = nib.load(BASE_PRED / f"{pid}.nii.gz")
        pd_ = nib.load(DIST_PRED / f"{pid}.nii.gz")
        gt = nib.load(GT_DIR / f"{pid}.nii.gz")
        Pb = pb.get_fdata().astype(np.int32)
        Pd = pd_.get_fdata().astype(np.int32)
        G  = gt.get_fdata().astype(np.int32)
        Pf = cc_consensus(Pd, Pb)
        vs = tuple(float(x) for x in pb.header.get_zooms()[:3])
        out = {"patient_id": pid, "fold": fold}
        for cls_name, cls in [("NCR", 1), ("ED", 2), ("ETc", 3)]:
            Gm = (G == cls)
            for v, Pv in [("B", Pb), ("D", Pd), ("F", Pf)]:
                out[f"hd95_{cls_name}_{v}"] = safe_hd95(Pv == cls, Gm, voxelspacing=vs)
        return out
    except Exception as e:
        return {"patient_id": pid, "fold": fold, "error": str(e)}

def main():
    splits = json.loads(SPLITS.read_text())
    # map patient -> fold
    pid_fold = []
    for f_i, sp in enumerate(splits):
        for pid in sp.get("val", []):
            pid_fold.append((pid, f_i))
    print(f"[hd95] {len(pid_fold)} patient/fold pairs", flush=True)

    # filter: prediction files must exist
    valid = [(pid, f) for pid, f in pid_fold
             if (BASE_PRED/f"{pid}.nii.gz").exists() and (DIST_PRED/f"{pid}.nii.gz").exists() and (GT_DIR/f"{pid}.nii.gz").exists()]
    print(f"[hd95] {len(valid)} have all 3 files", flush=True)

    n_workers = int(os.environ.get("N_WORKERS", "10"))
    print(f"[hd95] using {n_workers} workers", flush=True)
    # run pool
    with Pool(n_workers) as pool:
        results = []
        for i, r in enumerate(pool.imap_unordered(process, valid, chunksize=2)):
            results.append(r)
            if (i + 1) % 50 == 0:
                print(f"[hd95] {i+1}/{len(valid)}", flush=True)

    # write CSV
    keys = ["patient_id", "fold",
            "hd95_NCR_B", "hd95_NCR_D", "hd95_NCR_F",
            "hd95_ED_B",  "hd95_ED_D",  "hd95_ED_F",
            "hd95_ETc_B", "hd95_ETc_D", "hd95_ETc_F"]
    with OUT_CSV.open("w") as f:
        w = csv.DictWriter(f, fieldnames=keys + ["error"])
        w.writeheader()
        for r in results:
            w.writerow(r)
    print(f"[hd95] wrote {OUT_CSV}")

if __name__ == "__main__":
    main()
