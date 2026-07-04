#!/usr/bin/env python3
"""Generate CC-consensus predictions for official-metric evaluation, on the SAME per-fold
validation predictions used for the individual models (no provenance mismatch).

CC-consensus (as defined in scripts/compute_hd95_per_class.py): start from DistMap (Pd), and for
each class c in {1=NCR, 2=ED, 3=ET} drop every 26-connectivity connected component of Pd==c that
has zero overlap with the veto model's same-class mask. This suppresses DistMap's spurious
components that the veto model does not corroborate (false-positive suppression by agreement).

Two variants (DistMap supplies recall; the veto supplies precision):
  consensus_DB : veto = Baseline   (the originally implemented system)
  consensus_DK : veto = Kervadec   (motivated by the recall/precision finding — Kervadec is the
                                    most specific model, so it should veto more aggressively)

Output mirrors the nnU-Net validation layout so eval_lesionwise_kervadec.py can read it:
  outputs/cv_kervadec_paper2/{consensus_DB,consensus_DK}/fold_{N}/validation/<pid>.nii.gz
"""
import os
import sys
import glob
import traceback
from multiprocessing import Pool

import numpy as np
import nibabel as nib
from scipy.ndimage import label as cc_label, generate_binary_structure

REPO = "/home/ser/Bureau/BRATS"
RES = os.path.join(REPO, "nnunet_data", "results", "Dataset001_BraTS2023GLI")
T7 = "/media/ser/T7/BRATS/nnunet_data/results/Dataset001_BraTS2023GLI"
OUTROOT = os.path.join(REPO, "outputs", "cv_kervadec_paper2")
FOLDS = [0, 1, 2, 3, 4]
STRUCT_26 = generate_binary_structure(3, 3)


def kervadec_dir(f):
    return f"{RES}/nnUNetTrainerMedNeXtKervadec__nnUNetPlans_96GB_mednext__3d_fullres/fold_{f}/validation"


def baseline_dir(f):
    if f == 0:
        return f"{T7}/nnUNetTrainerMedNeXtBaseline__nnUNetPlans_96GB_mednext__3d_fullres__baseline_f0/fold_0/validation"
    return f"{RES}/nnUNetTrainerMedNeXtBaseline__nnUNetPlans_96GB_mednext__3d_fullres/fold_{f}/validation"


def distmap_dir(f):
    if f == 0:
        return f"{T7}/nnUNetTrainerMedNeXtDistMap__nnUNetPlans_96GB_mednext__3d_fullres__lambda0.1_f0/fold_0/validation"
    return f"{RES}/nnUNetTrainerMedNeXtDistMap__nnUNetPlans_96GB_mednext__3d_fullres/fold_{f}/validation"


def cc_consensus(Pd, Pv):
    """Pd vetoed by Pv: drop Pd components (per class) with no same-class overlap in Pv."""
    Pf = Pd.copy()
    for c in (1, 2, 3):
        dmask = (Pd == c)
        if not dmask.any():
            continue
        vmask = (Pv == c)
        labeled, n = cc_label(dmask, structure=STRUCT_26)
        for cc_id in range(1, n + 1):
            cc = (labeled == cc_id)
            if not (cc & vmask).any():
                Pf[cc] = 0
    return Pf


def process(task):
    fold, pid = task
    try:
        pd_img = nib.load(os.path.join(distmap_dir(fold), pid + ".nii.gz"))
        Pd = pd_img.get_fdata().astype(np.int16)
        Pb = nib.load(os.path.join(baseline_dir(fold), pid + ".nii.gz")).get_fdata().astype(np.int16)
        Pk = nib.load(os.path.join(kervadec_dir(fold), pid + ".nii.gz")).get_fdata().astype(np.int16)
        for tag, Pv in [("consensus_DB", Pb), ("consensus_DK", Pk)]:
            Pf = cc_consensus(Pd, Pv)
            outdir = os.path.join(OUTROOT, tag, f"fold_{fold}", "validation")
            os.makedirs(outdir, exist_ok=True)
            out = nib.Nifti1Image(Pf.astype(np.uint8), pd_img.affine, pd_img.header)
            nib.save(out, os.path.join(outdir, pid + ".nii.gz"))
        return 1
    except Exception:
        sys.stderr.write(f"FAIL fold{fold} {pid}\n{traceback.format_exc()}\n")
        return 0


def main():
    tasks = []
    for f in FOLDS:
        for p in sorted(glob.glob(os.path.join(kervadec_dir(f), "*.nii.gz"))):
            tasks.append((f, os.path.basename(p)[:-len(".nii.gz")]))
    print(f"{len(tasks)} patient/fold pairs -> 2 consensus variants each", flush=True)
    ok = 0
    with Pool(16) as pool:
        for i, r in enumerate(pool.imap_unordered(process, tasks, chunksize=4)):
            ok += r
            if (i + 1) % 200 == 0:
                print(f"  {i+1}/{len(tasks)}  ok={ok}", flush=True)
    print(f"DONE_CONSENSUS {ok}/{len(tasks)}")


if __name__ == "__main__":
    main()
