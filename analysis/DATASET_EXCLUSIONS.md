# Where the 55 exclusions come from — measured provenance (1,251 → 1,196 cases)

*Generated on 2026-09-22 20:23 UTC by `scripts/paper1_exclusions_provenance.py` from the
artefacts of `scripts/audit_exclusions_1251_1196.py`,
`scripts/audit_exclusions_integrity.py`, `scripts/sonde_5_cas_exclus.py` and
`scripts/compare_3_copies_exclus.sh`. No number below is typed by hand: every figure is read
from those measurements, and the generator refuses to write anything as long as one control
fails.*

## 1. The claim, and what it now rests on

The paper reports **1,196 cases** out of the **1,251** unified
BraTS-2023 GLI cases. The earlier public wording — "the remaining 55 have format problems or
inconsistent labels" — was **not supported by measurement**. This note replaces it with what was
actually found, including where that wording was wrong.

| Quantity | Measured value | Source |
|---|---|---|
| Unified patient folders (source) | 1,251 | `data/processed/brats_unified/` |
| Cases in the nnU-Net dataset (destination) | 1,196 | `<nnUNet_raw>/Dataset001_BraTS2023GLI/labelsTr/` |
| Modality files in `imagesTr` | 4,784 = 1,196 × 4 | idem |
| `dataset.json` `numTraining` | 1,196 | idem |
| **Excluded cases** | **55** (4.4 % of the source) | set difference, `analysis/exclusions_1251_to_1196.csv` |
| Included cases with no source folder | 0 | idem |

## 2. Why those 55 cases were dropped — the real mechanism

All 55 exclusions come from a single filter at conversion time
(`scripts/convert_brats_to_nnunet.py`): a case is skipped when its identifier, **or its patient
identifier** (`BraTS-GLI-xxxxx`), appears in `corrupted_patients.txt`.

| Trigger | Cases | What it means |
|---|---|---|
| Exact identifier in the list | 5 | added on 2026-03-10 after `scripts/audit_feature_quality.py` (full audit of the 1,251 cases) |
| Patient identifier in the list (patient-level expansion) | 50 | the list flagged 699 **longitudinal follow-up** acquisitions (suffix `-100` … `-109`) belonging to 272 patients; the converter drops *every* case of those patients, which is how 0 cases of the unified set (suffix `-000`/`-001`) were caught |

The list itself: **706 non-empty lines, 705 unique
identifiers** (duplicate: BraTS-GLI-01163-000 (2×)). Its git history dates the entries —
- `2afb4ee98` 2026-03-05: 701 unique lines (+701)
- `1332a2445` 2026-03-10: 705 unique lines (+4)

Crucially, the follow-up acquisitions that make up the bulk of the list **are not part of the
unified dataset** (which only contains `-000` and `-001` cases): they were flagged during
download verification. The exclusion of the 50 baseline/second cases is therefore a
**patient-level precaution taken before any training or metric**, not a measurement on those files.

## 3. Do the 55 excluded files actually have a defect? No — measured

`scripts/audit_exclusions_integrity.py` read every file of the 55 excluded cases
and of a matched control sample of 55 included cases (seed 42):
NIfTI readability, shape, dtype, NaN, Inf, zero-variance, extreme amplitude, affine agreement
between the four modalities and the segmentation, and segmentation label set.

| Check | Excluded (55) | Control (55) |
|---|---|---|
| Missing/incomplete cases | 0 | 0 |
| Unreadable files | 0 | 0 |
| NaN voxels | 0 | 0 |
| Inf voxels | 0 | 0 |
| Zero-variance volumes | 0 | 0 |
| Extreme amplitudes | 0 | 0 |
| Divergent affines | 0 | 0 |
| Labels outside {0,1,2,3} | 0 | 0 |
| Shapes observed | (240, 240, 155) | (240, 240, 155) |

The two groups are indistinguishable on every one of these checks. Per-file detail:
`analysis/integrite_exclus_vs_temoins.csv` (regenerated on demand).

## 4. The five 2026-03 flags do not reproduce either

The session note `14-03-2026.md` attributes specific defects to the 5 exactly-flagged
cases (segmentation label `34359738368 = 2^35`, one Inf voxel in a T2, an extreme intensity
outlier). `scripts/sonde_5_cas_exclus.py` re-ran those checks **on the literal code path of that
audit** (`nib.load(...).get_fdata().astype(np.int64)`):

| Case | Defect claimed in 03/2026 | Measured today |
|---|---|---|
| `BraTS-GLI-00170-000` | label seg corrompu (34359738368) | NaN 0 · Inf 0 · voxels 2^35 0 · labels seg [0.0, 2.0, 3.0] · hors-jeu 0 · modalités lues 4 |
| `BraTS-GLI-00658-000` | label seg corrompu (34359738368) | NaN 0 · Inf 0 · voxels 2^35 0 · labels seg [0.0, 1.0, 2.0, 3.0] · hors-jeu 0 · modalités lues 4 |
| `BraTS-GLI-01433-000` | label seg corrompu (34359738368) | NaN 0 · Inf 0 · voxels 2^35 0 · labels seg [0.0, 1.0, 2.0] · hors-jeu 0 · modalités lues 4 |
| `BraTS-GLI-00219-000` | 1 voxel Inf dans T2 | NaN 0 · Inf 0 · voxels 2^35 0 · labels seg [0.0, 1.0, 2.0, 3.0] · hors-jeu 0 · modalités lues 4 |
| `BraTS-GLI-01163-000` | outlier extrême (z=30-35, 4 modalités) | NaN 0 · Inf 0 · voxels 2^35 0 · labels seg [0.0, 1.0, 2.0, 3.0] · hors-jeu 0 · modalités lues 4 |
| `BraTS-GLI-00000-000` *(included control)* | — | NaN 0 · Inf 0 · voxels 2^35 0 · labels seg [0.0, 1.0, 2.0, 3.0] · hors-jeu 0 · modalités lues 4 |
| `BraTS-GLI-00002-000` *(included control)* | — | NaN 0 · Inf 0 · voxels 2^35 0 · labels seg [0.0, 1.0, 2.0, 3.0] · hors-jeu 0 · modalités lues 4 |

The original audit report (`outputs/feature_audit/`) is ABSENT du dépôt, so the March
evidence cannot be re-examined. Two further controls close the "maybe another copy was broken"
hypothesis: the three surviving copies of the unified dataset on the machine
(NVMe working copy, HDD rescue copy, 8 TB disk) are **byte-identical** for those cases —
30 files compared across 3 copies,
**0 divergence** — and their timestamps precede the audit.

## 5. What this changes, and what it does not

* **No result changes.** Every number in the paper is computed on the 1,196-case
  nnU-Net dataset; the exclusion is upstream of all training and all metrics.
* **The cross-validation is a clean partition** (this audit also checked it):
  5 folds of 240 / 239 / 239 / 239 / 239 validation cases, `val ∩ train = 0` in
  every fold, and the union of validation folds equals exactly the 1,196 cases —
  so no patient is validated twice and no prediction is in-fold.
* **The wording must be corrected**: the 55 exclusions are *conservative*
  (patient-level caution recorded in March 2026), not the correction of a measured file defect in
  those cases. The v10 text and the website now say exactly that, and point here.
* **Re-including them is not justified by a measured defect**, but it would require
  re-preprocessing and re-training the whole cross-validation; it would change published numbers.
  We keep the 1,196-case set and publish the list, so a reader can bound the
  effect (55/1,251 = 4.4 % of cases).

## 6. Reproducing this note

```bash
python3 scripts/audit_exclusions_1251_1196.py       # 55 exclusions, reasons, folds  -> PASS/ÉCHEC
python3 scripts/audit_exclusions_integrity.py        # file-level integrity vs controls -> PASS/ÉCHEC
python3 scripts/sonde_5_cas_exclus.py                # the five March flags, re-measured
bash    scripts/compare_3_copies_exclus.sh           # md5 across the three dataset copies
python3 scripts/paper1_exclusions_provenance.py      # this note, regenerated from the above
```

Artefacts: `analysis/exclusions_1251_to_1196.csv` (the 55 identifiers, trigger,
git date of the triggering list entry), `analysis/exclusions_1251_to_1196.json` (measured summary,
list history, fold partition), `analysis/integrite_exclus_vs_temoins.csv` and `.json`,
`analysis/sonde_5_cas_exacts.json`, `analysis/comparaison_3_copies.tsv`.
