#!/usr/bin/env python3
"""Per-patient nested-region (WT/TC/ET) HD95 with medpy, for the §5.3 boundary-quality table.

Companion to compute_hd95_per_class.py (which does the individual classes NCR/ED/ETc). Both use
the SAME standard implementation — medpy.metric.binary.hd95 — so every HD95 reported in the paper
comes from one library; there is no in-house Hausdorff code anywhere in the pipeline.

Regions (standard BraTS composition):
  WT = labels {1,2,3}   TC = labels {1,3}   ET = label {3}
CC-Consensus (F) = start from DistMap, drop per-class 26-connectivity components without same-class
Baseline overlap (identical rule to compute_hd95_per_class.py).
Conventions: both masks empty -> HD95 = 0; exactly one empty -> NaN (dropped at aggregation).

Optimisation: each patient is cropped to the bounding box of the union of all non-zero labels
(+5 vox margin) before the medpy call. medpy runs distance_transform_edt over the whole 240^3
volume; cropping is ~10-50x faster and the value is IDENTICAL (every surface voxel and its nearest
neighbour stay inside the crop).

NOTE: requires tower-local GT + baseline/distmap prediction NIfTIs (not redistributed). The
analysis output is pre-computed and shipped as analysis/hd95_regions_medpy.csv.
"""
import csv
import glob
import os
import numpy as np
import nibabel as nib
from pathlib import Path
from scipy.ndimage import label as cc_label, generate_binary_structure
from medpy.metric.binary import hd95
from multiprocessing import Pool

BASE_PRED = Path("/home/ser/Bureau/BRATS/outputs/predictions/baseline")
DIST_PRED = Path("/home/ser/Bureau/BRATS/outputs/predictions/distmap")
GT_DIR    = Path("/home/ser/Bureau/BRATS/nnunet_data/preprocessed/Dataset001_BraTS2023GLI/gt_segmentations")
OUT_CSV   = Path("/home/ser/Bureau/BRATS/outputs/hd95_regions_medpy.csv")

STRUCT_26 = generate_binary_structure(3, 3)
REGIONS = {"WT": (1, 2, 3), "TC": (1, 3), "ET": (3,)}
KEYS = ["patient_id"] + [f"hd95_{r}_{v}" for r in REGIONS for v in ("B", "D", "F")] + ["error"]


def bbox_crop(arrays, margin=5):
    union = np.zeros(arrays[0].shape, dtype=bool)
    for a in arrays:
        union |= (a != 0)
    if not union.any():
        return arrays
    nz = np.where(union)
    sl = tuple(slice(max(int(c.min()) - margin, 0), min(int(c.max()) + margin + 1, s))
               for c, s in zip(nz, arrays[0].shape))
    return [a[sl] for a in arrays]


def cc_consensus(Pd, Pb):
    Pf = Pd.copy()
    for c in (1, 2, 3):
        dmask = (Pd == c)
        if not dmask.any():
            continue
        bmask = (Pb == c)
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
        return float("nan")
    return float(hd95(pred, gt, voxelspacing=voxelspacing))


def process(pid):
    try:
        pb_img = nib.load(str(BASE_PRED / f"{pid}.nii.gz"))
        Pb = pb_img.get_fdata().astype(np.int16)
        Pd = nib.load(str(DIST_PRED / f"{pid}.nii.gz")).get_fdata().astype(np.int16)
        G = nib.load(str(GT_DIR / f"{pid}.nii.gz")).get_fdata().astype(np.int16)
        vs = tuple(float(x) for x in pb_img.header.get_zooms()[:3])
        Pb, Pd, G = bbox_crop([Pb, Pd, G])
        Pf = cc_consensus(Pd, Pb)
        out = {"patient_id": pid, "error": ""}
        for rname, labels in REGIONS.items():
            Gm = np.isin(G, labels)
            for v, P in [("B", Pb), ("D", Pd), ("F", Pf)]:
                out[f"hd95_{rname}_{v}"] = safe_hd95(np.isin(P, labels), Gm, vs)
        return out
    except Exception as e:
        return {"patient_id": pid, "error": str(e)}


def main():
    pids = sorted(os.path.basename(p)[:-7] for p in glob.glob(str(BASE_PRED / "*.nii.gz")))
    pids = [p for p in pids if (DIST_PRED / f"{p}.nii.gz").exists() and (GT_DIR / f"{p}.nii.gz").exists()]
    print(f"{len(pids)} patients", flush=True)
    with open(OUT_CSV, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=KEYS)
        w.writeheader()
        done = 0
        with Pool(10) as pool:
            for r in pool.imap_unordered(process, pids, chunksize=2):
                w.writerow(r)
                f.flush()
                done += 1
                if done % 100 == 0:
                    print(f"  {done}/{len(pids)}", flush=True)
    print(f"DONE {done} -> {OUT_CSV}")


if __name__ == "__main__":
    main()
