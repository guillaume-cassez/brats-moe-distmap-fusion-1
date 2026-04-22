#!/usr/bin/env python3
"""Extract 20 morphological/topological features per patient to discriminate
the 6 model-ordering cases (C1-C6) defined in the viewer analysis.

Input  : /tmp/rankings.json (classifier list), tower-local NIfTIs.
Output : /home/ser/Bureau/BRATS/outputs/patient_features.csv

Features (per patient):
  vol_WT, vol_TC, vol_ET, ratio_ET_WT,
  nb_cc_ET, nb_cc_NCR, frac_small_cc_ET, frac_small_cc_NCR, cc_spread_ET,
  euler_WT, euler_TC, euler_ET, cavities_WT,
  pca_elongation_WT, sphericity_WT, surface_roughness_WT,
  nb_cc_baseline_ET, nb_cc_distmap_ET, nb_cc_baseline_NCR, nb_cc_distmap_NCR

BraTS labels: 1=NCR, 2=ED, 3=ET. Regions: WT={1,2,3}, TC={1,3}, ET={3}.
26-connectivity everywhere (generate_binary_structure(3,3)).
"""
import json
import csv
import sys
import math
import time
from pathlib import Path
from multiprocessing import Pool

import numpy as np
import nibabel as nib
from scipy import ndimage as ndi
from skimage.measure import euler_number as sk_euler

DATA_DIR = Path("/home/ser/Bureau/BRATS/data/processed/brats_unified")
PRED_BASELINE = Path("/home/ser/Bureau/BRATS/outputs/predictions/baseline")
PRED_DISTMAP = Path("/home/ser/Bureau/BRATS/outputs/predictions/distmap")
RANKINGS = Path("/home/ser/Bureau/BRATS/viewer/V3/static_bundle/rankings.json")
OUT_CSV = Path("/home/ser/Bureau/BRATS/outputs/patient_features.csv")

STRUCT_26 = ndi.generate_binary_structure(3, 3)
SMALL_CC_VX = 20

FIELDS = [
    "patient_id", "fold",
    "vol_WT", "vol_TC", "vol_ET", "ratio_ET_WT",
    "nb_cc_ET", "nb_cc_NCR",
    "frac_small_cc_ET", "frac_small_cc_NCR",
    "cc_spread_ET",
    "euler_WT", "euler_TC", "euler_ET",
    "cavities_WT",
    "pca_elongation_WT", "sphericity_WT", "surface_roughness_WT",
    "nb_cc_baseline_ET", "nb_cc_distmap_ET",
    "nb_cc_baseline_NCR", "nb_cc_distmap_NCR",
]

def load_seg(path):
    return nib.load(str(path)).get_fdata().astype(np.uint8)

def cc_stats(mask, want_spread=False):
    """Return (nb_cc, frac_small, spread_or_none)."""
    if mask.sum() == 0:
        return 0, 0.0, 0.0
    lab, nb = ndi.label(mask, structure=STRUCT_26)
    if nb == 0:
        return 0, 0.0, 0.0
    sizes = ndi.sum(mask, lab, index=range(1, nb + 1))
    total = sizes.sum()
    small_vx = sizes[sizes < SMALL_CC_VX].sum()
    frac_small = small_vx / total if total > 0 else 0.0
    spread = 0.0
    if want_spread and nb > 1:
        centroids = np.array(ndi.center_of_mass(mask, lab, index=range(1, nb + 1)))
        weights = sizes / total
        main = (centroids * weights[:, None]).sum(axis=0)
        d = np.linalg.norm(centroids - main, axis=1)
        spread = float(np.sqrt((d * d * weights).sum()))
    return int(nb), float(frac_small), spread

def surface_area_6conn(mask):
    """Count face-exposed voxel faces: simple surrogate for surface area."""
    m = mask.astype(np.uint8)
    s = 0
    # 6-neighborhood face counts where neighbor is 0 or out-of-volume
    s += (m[:-1] & ~m[1:]).sum() + (~m[:-1] & m[1:]).sum()
    s += (m[:, :-1] & ~m[:, 1:]).sum() + (~m[:, :-1] & m[:, 1:]).sum()
    s += (m[:, :, :-1] & ~m[:, :, 1:]).sum() + (~m[:, :, :-1] & m[:, :, 1:]).sum()
    # Edges: faces flush with volume border count as surface
    s += m[0].sum() + m[-1].sum()
    s += m[:, 0].sum() + m[:, -1].sum()
    s += m[:, :, 0].sum() + m[:, :, -1].sum()
    return int(s)

def pca_elongation(mask):
    idx = np.argwhere(mask)
    if len(idx) < 3:
        return 1.0
    c = idx - idx.mean(axis=0)
    cov = np.cov(c.T)
    ev = np.linalg.eigvalsh(cov)
    ev = np.sort(ev)[::-1]
    if ev[-1] <= 1e-6:
        return float("inf")
    return float(math.sqrt(ev[0] / ev[-1]))

def sphericity(mask):
    V = int(mask.sum())
    if V == 0:
        return 0.0
    S = surface_area_6conn(mask)
    if S == 0:
        return 0.0
    return float((math.pi ** (1 / 3)) * ((6 * V) ** (2 / 3)) / S)

def surface_roughness(mask):
    V = int(mask.sum())
    if V == 0:
        return 0.0
    S = surface_area_6conn(mask)
    r = (3 * V / (4 * math.pi)) ** (1 / 3)
    S_sphere = 4 * math.pi * r * r
    if S_sphere <= 1e-6:
        return 0.0
    return float(S / S_sphere)

def cavities_count(mask):
    """Number of enclosed cavities inside the mask (3D topological holes)."""
    if mask.sum() == 0:
        return 0
    filled = ndi.binary_fill_holes(mask)
    diff = filled & ~mask
    if diff.sum() == 0:
        return 0
    _, nb = ndi.label(diff, structure=STRUCT_26)
    return int(nb)

def process_one(task):
    pid, fold = task
    try:
        gt_path = DATA_DIR / pid / f"{pid}-seg.nii.gz"
        b_path = PRED_BASELINE / f"{pid}.nii.gz"
        d_path = PRED_DISTMAP / f"{pid}.nii.gz"
        if not gt_path.exists() or not b_path.exists() or not d_path.exists():
            return None

        gt = load_seg(gt_path)
        b_pred = load_seg(b_path)
        d_pred = load_seg(d_path)

        # Region masks (GT)
        ncr = gt == 1
        ed = gt == 2
        et = gt == 3
        tc = ncr | et
        wt = ncr | ed | et

        vol_WT = int(wt.sum()); vol_TC = int(tc.sum()); vol_ET = int(et.sum())
        ratio = (vol_ET / vol_WT) if vol_WT > 0 else 0.0

        nb_et, fs_et, spread_et = cc_stats(et, want_spread=True)
        nb_ncr, fs_ncr, _ = cc_stats(ncr)

        euler_WT = int(sk_euler(wt, connectivity=3))
        euler_TC = int(sk_euler(tc, connectivity=3))
        euler_ET = int(sk_euler(et, connectivity=3))
        cav_WT = cavities_count(wt)

        pca = pca_elongation(wt)
        sph = sphericity(wt)
        rough = surface_roughness(wt)

        # Prediction CC counts
        bp_ET = b_pred == 3; bp_NCR = b_pred == 1
        dp_ET = d_pred == 3; dp_NCR = d_pred == 1
        _, nb_b_et = ndi.label(bp_ET, structure=STRUCT_26)
        _, nb_d_et = ndi.label(dp_ET, structure=STRUCT_26)
        _, nb_b_ncr = ndi.label(bp_NCR, structure=STRUCT_26)
        _, nb_d_ncr = ndi.label(dp_NCR, structure=STRUCT_26)

        return [
            pid, fold,
            vol_WT, vol_TC, vol_ET, round(ratio, 6),
            nb_et, nb_ncr, round(fs_et, 6), round(fs_ncr, 6), round(spread_et, 4),
            euler_WT, euler_TC, euler_ET, cav_WT,
            round(pca, 4), round(sph, 6), round(rough, 6),
            int(nb_b_et), int(nb_d_et), int(nb_b_ncr), int(nb_d_ncr),
        ]
    except Exception as e:
        print(f"[err {pid}] {e}", flush=True)
        return None

def main():
    if not RANKINGS.exists():
        print(f"missing {RANKINGS}", file=sys.stderr); sys.exit(1)
    data = json.loads(RANKINGS.read_text())
    tasks = []
    for r in data["rows"]:
        if r.get("baseline") and r.get("distmap") and r.get("fusion"):
            tasks.append((r["patient_id"], str(r.get("fold", ""))))
    print(f"[start] {len(tasks)} patients, writing {OUT_CSV}", flush=True)

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    done = 0
    with OUT_CSV.open("w", newline="") as fout:
        w = csv.writer(fout)
        w.writerow(FIELDS)
        fout.flush()
        with Pool(processes=10) as pool:
            for row in pool.imap_unordered(process_one, tasks, chunksize=2):
                if row is not None:
                    w.writerow(row)
                done += 1
                if done % 50 == 0:
                    fout.flush()
                    elapsed = time.time() - t0
                    rate = done / elapsed
                    eta = (len(tasks) - done) / rate if rate > 0 else 0
                    print(f"[{done}/{len(tasks)}] {elapsed:.0f}s  eta={eta:.0f}s", flush=True)
    print(f"[done] {done}/{len(tasks)} in {time.time() - t0:.0f}s  -> {OUT_CSV}")

if __name__ == "__main__":
    main()
