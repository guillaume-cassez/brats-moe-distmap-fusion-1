#!/usr/bin/env python3
"""Topological fragment count on 1196 CV patients for Baseline / DistMap / CC-Consensus.

Fragment = any 26-connectivity connected component that is NOT the largest CC
of its class. No voxel-size threshold. A class with n CCs has (n-1) fragments
(0 if n <= 1).

Per class (NCR=1, ED=2, ET=3) and per variant (B=baseline, D=distmap, F=fusion),
we output : nb_cc and nb_fragments = max(0, nb_cc - 1).

CC-Consensus is computed on-the-fly (veto DistMap CCs without Baseline overlap).

NOTE: Requires tower-local baseline/distmap prediction NIfTIs. Output shipped
as analysis/fragments_topological_cv.csv.
"""
import csv
import json
import os
import sys
from pathlib import Path
from multiprocessing import Pool

import numpy as np
import nibabel as nib
from scipy.ndimage import label as cc_label, generate_binary_structure

BASE_PRED = Path("/home/ser/Bureau/BRATS/outputs/predictions/baseline")
DIST_PRED = Path("/home/ser/Bureau/BRATS/outputs/predictions/distmap")
SPLITS    = Path("/home/ser/Bureau/BRATS/nnunet_data/preprocessed/Dataset001_BraTS2023GLI/splits_final.json")
OUT_CSV   = Path("/home/ser/Bureau/BRATS/outputs/fragments_topological_cv.csv")

STRUCT_26 = generate_binary_structure(3, 3)

def cc_consensus(Pd, Pb):
    Pf = Pd.copy()
    for c in (1, 2, 3):
        dmask = (Pd == c); bmask = (Pb == c)
        if not dmask.any(): continue
        labeled, n = cc_label(dmask, structure=STRUCT_26)
        for cc_id in range(1, n + 1):
            cc = (labeled == cc_id)
            if not (cc & bmask).any():
                Pf[cc] = 0
    return Pf

def count_cc(mask):
    if not mask.any():
        return 0
    _, n = cc_label(mask, structure=STRUCT_26)
    return int(n)

def process(pid_fold):
    pid, fold = pid_fold
    try:
        Pb = nib.load(BASE_PRED / f"{pid}.nii.gz").get_fdata().astype(np.int32)
        Pd = nib.load(DIST_PRED / f"{pid}.nii.gz").get_fdata().astype(np.int32)
        Pf = cc_consensus(Pd, Pb)
        out = {"patient_id": pid, "fold": fold}
        for cls_name, cls in [("NCR", 1), ("ED", 2), ("ET", 3)]:
            for v_name, V in [("B", Pb), ("D", Pd), ("F", Pf)]:
                n = count_cc(V == cls)
                out[f"nb_cc_{v_name}_{cls_name}"]   = n
                out[f"frags_{v_name}_{cls_name}"]   = max(0, n - 1)
        return out
    except Exception as e:
        return {"patient_id": pid, "fold": fold, "error": str(e)}

def main():
    splits = json.loads(SPLITS.read_text())
    pid_fold = [(pid, f_i) for f_i, sp in enumerate(splits) for pid in sp.get("val", [])]
    valid = [(p, f) for p, f in pid_fold if (BASE_PRED/f"{p}.nii.gz").exists() and (DIST_PRED/f"{p}.nii.gz").exists()]
    print(f"[frags] {len(valid)} patients", flush=True)

    n_workers = int(os.environ.get("N_WORKERS", "10"))
    with Pool(n_workers) as pool:
        results = []
        for i, r in enumerate(pool.imap_unordered(process, valid, chunksize=2)):
            results.append(r)
            if (i + 1) % 100 == 0:
                print(f"[frags] {i+1}/{len(valid)}", flush=True)

    keys = ["patient_id", "fold"]
    for cls in ("NCR", "ED", "ET"):
        for v in ("B", "D", "F"):
            keys += [f"nb_cc_{v}_{cls}", f"frags_{v}_{cls}"]
    with OUT_CSV.open("w") as f:
        w = csv.DictWriter(f, fieldnames=keys + ["error"])
        w.writeheader()
        for r in results:
            w.writerow(r)
    print(f"[frags] wrote {OUT_CSV}")

if __name__ == "__main__":
    main()
