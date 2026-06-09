#!/usr/bin/env python3
"""Paper 1 V2 (DistMap CC-consensus) — official BraTS-2023 LESION-WISE evaluation, 5-fold held-out CV.

Region-wise (Legacy) HD95 showed no Kervadec gain. The OFFICIAL BraTS-2023 HD95 is
lesion-wise (per connected component, FP/FN penalised at 374 mm, GT lesions <=50 vox
dropped, dil_factor=3): Saluja et al., github.com/rachitsaluja/BraTS-2023-Metrics.
It is the one metric where a boundary loss can show an effect the region-wise hides
(e.g. fewer spurious false-positive islands -> much lower lesion-wise HD95).

For each (method, fold, patient) we call the official get_LesionWiseResults and record,
per region (WT/TC/ET): Legacy_HD95 (=region-wise, for cross-check), LesionWise_HD95,
Legacy_Dice, LesionWise_Dice, Num_FP, Num_FN. Predictions are the nnU-Net per-fold
validation outputs already on disk (no re-inference). GT = nnU-Net raw labelsTr.

Output (long format, durable): outputs/cv_kervadec_paper2/lesionwise_per_patient.csv
Streamed+fsynced per patient so a crash keeps partial progress.
"""
import csv
import glob
import os
import sys
import traceback
from multiprocessing import Pool

REPO = "/home/ser/Bureau/BRATS"
METRICS_DIR = os.path.join(REPO, "external", "BraTS-2023-Metrics")
sys.path.insert(0, METRICS_DIR)
from metrics import get_LesionWiseResults  # noqa: E402

GT_DIR = os.path.join(REPO, "nnunet_data", "raw", "Dataset001_BraTS2023GLI", "labelsTr")
RES = os.path.join(REPO, "nnunet_data", "results", "Dataset001_BraTS2023GLI")
T7 = "/media/ser/T7/BRATS/nnunet_data/results/Dataset001_BraTS2023GLI"
OUT = os.path.join(REPO, "outputs", "cv_kervadec_paper2", "lesionwise_per_patient.csv")
FOLDS = [0, 1, 2, 3, 4]
REGIONS = ["WT", "TC", "ET"]
CHALLENGE = "BraTS-GLI"


def kervadec_dir(f):
    return f"{RES}/nnUNetTrainerMedNeXtKervadec__nnUNetPlans_96GB_mednext__3d_fullres/fold_{f}/validation"


def baseline_dir(f):
    # fold 0 from the paper-1 headline run on T7 (extra fold_0 level); folds 1-4 local CV
    if f == 0:
        return f"{T7}/nnUNetTrainerMedNeXtBaseline__nnUNetPlans_96GB_mednext__3d_fullres__baseline_f0/fold_0/validation"
    return f"{RES}/nnUNetTrainerMedNeXtBaseline__nnUNetPlans_96GB_mednext__3d_fullres/fold_{f}/validation"


def distmap_dir(f):
    if f == 0:
        return f"{T7}/nnUNetTrainerMedNeXtDistMap__nnUNetPlans_96GB_mednext__3d_fullres__lambda0.1_f0/fold_0/validation"
    return f"{RES}/nnUNetTrainerMedNeXtDistMap__nnUNetPlans_96GB_mednext__3d_fullres/fold_{f}/validation"


def consensus_db_dir(f):
    return f"{REPO}/outputs/cv_kervadec_paper2/consensus_DB/fold_{f}/validation"


def consensus_dk_dir(f):
    return f"{REPO}/outputs/cv_kervadec_paper2/consensus_DK/fold_{f}/validation"


DIRS = {"kervadec": kervadec_dir, "baseline": baseline_dir, "distmap": distmap_dir,
        "consensus_DB": consensus_db_dir, "consensus_DK": consensus_dk_dir}
FIELDS = ["method", "fold", "patient_id", "region",
          "legacy_hd95", "lw_hd95", "legacy_dice", "lw_dice",
          "num_tp", "num_fp", "num_fn", "sensitivity", "specificity"]


def build_tasks(methods=None, folds=None):
    """-> list of (method, fold, patient_id, pred_path, gt_path); validates dirs."""
    methods = methods or list(DIRS)
    folds = folds if folds is not None else FOLDS
    tasks = []
    print("Resolved prediction dirs (n preds):")
    for method in methods:
        fn = DIRS[method]
        for f in folds:
            d = fn(f)
            preds = sorted(glob.glob(os.path.join(d, "*.nii.gz")))
            print(f"  {method:9s} fold{f}: {len(preds):3d}  {d}")
            for p in preds:
                pid = os.path.basename(p)[:-len(".nii.gz")]
                gt = os.path.join(GT_DIR, pid + ".nii.gz")
                if not os.path.exists(gt):
                    print(f"    !! GT missing for {pid}")
                    continue
                tasks.append((method, f, pid, p, gt))
    return tasks


def run_one(task):
    method, f, pid, pred, gt = task
    try:
        df = get_LesionWiseResults(pred, gt, CHALLENGE)
        df = df.set_index("Labels")
        rows = []
        for reg in REGIONS:
            r = df.loc[reg]
            rows.append({
                "method": method, "fold": f, "patient_id": pid, "region": reg,
                "legacy_hd95": float(r["Legacy_HD95"]),
                "lw_hd95": float(r["LesionWise_Score_HD95"]),
                "legacy_dice": float(r["Legacy_Dice"]),
                "lw_dice": float(r["LesionWise_Score_Dice"]),
                "num_tp": float(r["Num_TP"]),
                "num_fp": float(r["Num_FP"]),
                "num_fn": float(r["Num_FN"]),
                "sensitivity": float(r["Sensitivity"]),
                "specificity": float(r["Specificity"]),
            })
        return rows
    except Exception:
        sys.stderr.write(f"FAIL {method} fold{f} {pid}\n{traceback.format_exc()}\n")
        return None


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--methods", help="csv subset e.g. baseline,distmap")
    ap.add_argument("--folds", help="csv subset e.g. 0")
    ap.add_argument("--append", action="store_true", help="append to OUT, no header")
    ap.add_argument("--out", default=OUT)
    a = ap.parse_args()
    methods = a.methods.split(",") if a.methods else None
    folds = [int(x) for x in a.folds.split(",")] if a.folds else None
    tasks = build_tasks(methods, folds)
    print(f"\nTotal tasks: {len(tasks)}\n", flush=True)
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    done = 0
    fail = 0
    with open(a.out, "a" if a.append else "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS)
        if not a.append:
            w.writeheader()
        with Pool(processes=16) as pool:
            for rows in pool.imap_unordered(run_one, tasks, chunksize=4):
                done += 1
                if rows is None:
                    fail += 1
                else:
                    w.writerows(rows)
                if done % 200 == 0:
                    fh.flush()
                    os.fsync(fh.fileno())
                    print(f"  {done}/{len(tasks)}  (fail={fail})", flush=True)
        fh.flush()
        os.fsync(fh.fileno())
    print(f"\nDONE {done}/{len(tasks)}  fail={fail}\n-> {a.out}")


if __name__ == "__main__":
    main()
