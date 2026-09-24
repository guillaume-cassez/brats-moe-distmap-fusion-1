# brats-moe-distmap-fusion-1

**Two Models That Agree Beat the Best of Them Alone: Parameter-Free Connected-Component Consensus That Beats the Baseline under the Official BraTS-2023 Metrics**

*English version. Version française : [README_fr.md](README_fr.md).*

Code, data artefacts, and paper source for a BraTS 2023 GLI study.

> *Note on naming.* Earlier drafts used "MoE fusion". This version drops that label : the rule is not a Mixture-of-Experts in the strict sense (no learned gating network, no soft routing). It is a **hard-label, post-hoc, connected-component-level consensus filter** — precisely described as **CC-consensus filter** throughout. The repository slug (`brats-moe-distmap-fusion-1`) is kept for URL / DOI stability.

[![interactive viewer](https://img.shields.io/badge/🌐_interactive_viewer-guillaume--cassez.fr-blue)](https://guillaume-cassez.fr/imagerie-medicale/viewer/)
[![paper page](https://img.shields.io/badge/📄_paper_landing-guillaume--cassez.fr-blue)](https://guillaume-cassez.fr/imagerie-medicale/)
[![HF Baseline](https://img.shields.io/badge/🤗-MedNeXt%20Baseline-yellow)](https://huggingface.co/GuillaumeCassez/mednext-baseline-brats2023gli)
[![HF DistMap](https://img.shields.io/badge/🤗-MedNeXt%20DistMap-yellow)](https://huggingface.co/GuillaumeCassez/mednext-distmap-brats2023gli)
[![license](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.19695263.svg)](https://doi.org/10.5281/zenodo.19695263)

---

## What changed in v10 (2026-09-22)

1. **§4.6 provenance restored.** The multi-seed robustness tables (Table A/B) are reported
   from the *complete, fragment-cleaned* evaluation run (n = 720 valid pairs,
   `data/multiseed/stats.json`, md5 `fe5d513e…`) — the same numbers published since v7. A
   work-in-progress revision had silently quoted a superseded, incomplete run
   (n = 719/684 with ~5 % failed consensus cases, LW Dice WT 0.7815 instead of 0.8103). That
   superseded run is **not** shipped: the archive carries only the artifacts backing the retained
   numbers (`data/multiseed/`), and the cross-check `scripts/check_5_6_provenance.py` fails the
   release if any of its signatures reappears (120/120 table values verified, both languages).
2. **English/French full parity.** The EN manuscript is rebuilt from the FR revision of
   2026-09-01 (30 sections since the 2026-09-19 plan alignment, 9 figures, same table counts), both re-titled *Two Models That
   Agree Beat the Best of Them Alone…*.
3. **Both authors.** Guillaume Cassez (first) and Stanislas Larnier (second) now appear on
   the title page, `CITATION.cff` and `.zenodo.json`; the bibtex below lists both.
4. **Demonstration patients refreshed.** C1–C6 are the six cases re-selected on 2026-08-31
   (montages in `figures/`, table below); the five retired montages and the two superseded
   pipeline schematics are removed.
5. **Vocabulary corrected (2026-09-22, after an external audit of the v9 supplement).** A false
   positive is no longer called a “hallucination” — in the generative-model literature that word
   names a different phenomenon (a fluent output with no grounding). Both manuscripts and every
   document of this archive now say **spurious (false-positive) connected component** /
   *composante connexe fallacieuse (faux positif)*, and §1 states the choice explicitly. The word
   survives only where the text rejects it. No measurement changes.
6. **Dataset exclusions documented (2026-09-22, same audit).** §3.1 no longer presents the study
   set as “the 1251 downloaded cases”: it is **1196**, and the **55 dropped cases are now listed
   one by one** — trigger, git date of the triggering entry, and a re-measurement of their file
   integrity — in `analysis/DATASET_EXCLUSIONS.md` (EN) and `analysis/DATASET_EXCLUSIONS_fr.md`
   (FR), backed by `analysis/exclusions_1251_to_1196.csv`,
   `analysis/exclusions_1251_to_1196.json`, `analysis/integrite_exclus_vs_temoins.csv`,
   `analysis/integrite_exclus_vs_temoins.json`, `analysis/sonde_5_cas_exacts.json`,
   `analysis/comparaison_3_copies.tsv` and `analysis/folds.csv`. The exclusion is a patient-level
   precaution recorded in March 2026, upstream of every training run and every metric; no
   file-level defect reproduces on those 55 cases today (0 unreadable, 0 NaN/Inf, 0 out-of-set
   label, 0 divergent affine, against 55 included controls) and they are byte-identical across the
   three surviving copies of the dataset. **No published number changes**: every result here was
   computed on the 1196-case set.


## The story behind this repo

I started this project excited by a simple idea : distance-map auxiliary losses have lifted segmentation in **other medical imaging tasks** (abdominal organs, liver, cardiac — Ma MIDL 2020 ; Xue AAAI 2020), so the same should help on BraTS 2023 GLI — especially with the recent MedNeXt-B backbone. The hypothesis felt cheap to test.

**The first surprise**: at 10 epochs the Dice delta looked great (+0.74 pp avg), but at 300 epochs on the full 5-fold CV (1196 patients) the delta dissolved. Re-evaluated under the **complete set of official BraTS-2023 metrics** — including the two challenge **ranking** metrics, lesion-wise Dice and lesion-wise HD95 — the SDT head is **null on the official ranking** (lesion-wise Dice Δ = −0.003, Holm p = 1.0; lesion-wise HD95 Δ = +1.12 mm, Holm p = 1.0) and Dice-neutral on the legacy region overlap (Δ = +0.001, p = 0.24). The earlier reduced-budget Dice gain **does not survive to convergence**. So DistMap does not give you Dice — or any ranking-metric improvement — for free.

**The second surprise**: the one robust effect of the SDT head is a **recall-oriented shift** — higher region sensitivity (r = +0.20, p = 2.0 × 10⁻⁹), fewer missed lesions, at a specificity cost (r = −0.26, p = 1.2 × 10⁻¹⁴). Its topological signature: DistMap produces more tiny isolated blobs ("fragments") than Baseline, most visible on NCR (×1.5). A failure mode nobody had reported before on BraTS, and **invisible to Dice**.

**The third surprise, and the most exciting**: a parameter-free post-hoc fix — a connected-component **consensus** filter that keeps a DistMap component only if a second model corroborates it in the same class (Baseline `CC(D∩B)`, or the more-specific Kervadec head `CC(D∩K)`, Paper 2) — is the **first configuration here to significantly beat the baseline on both official ranking metrics**: lesion-wise Dice **+0.024** (Holm p = 4.5 × 10⁻¹⁶) and lesion-wise HD95 **−9.49 mm** (Holm p = 5.7 × 10⁻²⁶). It removes **~41 % of the spurious lesions** (FP lesions 0.396 → 0.234 per case) at negligible recall cost.

So the final story is not "DistMap is better". It is : **on the official BraTS-2023 ranking metrics, the SDT head is null** ; its only real effect is a recall-oriented shift whose price is a topological fragment artefact ; and a simple post-hoc consensus rule turns that trade-off into **the only system here that beats the baseline on the official lesion-wise metrics**, by cleaning up spurious detections. Part of the HD95 lesion-wise gain comes from the official metric's 374 mm penalty per spurious lesion — stated plainly, not implying a boundary-precision gain on true lesions. The Dice lesion-wise gain is a genuine detection clean-up. That is the paper.

---

## TL;DR

Everything is evaluated under the **complete set of official BraTS-2023 metrics** — lesion-wise Dice and HD95 (the challenge **ranking** metrics, pre-specified primary endpoints, Holm-corrected), legacy region-wise Dice/HD95, and lesion detection — at convergence (300 epochs), 5-fold CV, n = 1196.

1. **The SDT auxiliary head is null on the official ranking.** On the two pre-specified primary endpoints — lesion-wise Dice (Δ = −0.003, Holm p = 1.0) and lesion-wise HD95 (Δ = +1.12 mm, Holm p = 1.0) — it shows no significant effect, and it is Dice-neutral on the legacy region overlap (Δ = +0.001, p = 0.24). The reduced-budget Dice gain of an earlier version **does not survive to convergence**.

2. **Its one robust effect is a recall-oriented shift**: higher region sensitivity (r = +0.20, p = 2.0 × 10⁻⁹) and fewer missed lesions, paid for by a **specificity cost** (r = −0.26, p = 1.2 × 10⁻¹⁴). The topological signature of that lost specificity is **spurious isolated connected components ("fragments")**, most acute on NCR (×1.5 vs Baseline) — a failure mode unreported on BraTS and **invisible to Dice**.

3. **A parameter-free connected-component consensus filter (CC-consensus) is the only configuration here that significantly beats the baseline on both official ranking metrics.** It keeps a DistMap component only if a second model corroborates it in the same class (Baseline `CC(D∩B)`, or the more-specific Kervadec head `CC(D∩K)`, Paper 2), removing **~41 % of the spurious lesions** (FP lesions 0.396 → 0.234 per case, p = 6.0 × 10⁻³⁴) at negligible recall cost: lesion-wise Dice **+0.024** (Holm p = 4.5 × 10⁻¹⁶) and lesion-wise HD95 **−9.49 mm** (Holm p = 5.7 × 10⁻²⁶). Part of the HD95 gain comes from the official metric's 374 mm penalty per spurious lesion — stated explicitly, not a boundary-precision claim on true lesions ; the Dice lesion-wise gain is a genuine detection clean-up.

4. **The region-overlap ceiling is real.** The gain is invisible to legacy region Dice, which is saturated — the per-class **oracle is only +0.005 Dice avg** above the default rule — and **no classifier** (RF / LR / GBM) trained on 31 hand-crafted features robustly beats the default in CV. As a *secondary, diagnostic* per-class result, the filter also reduces NCR HD95 (4.86 → 4.48 mm, p = 5.7 × 10⁻¹⁴) by eliminating 66 % of NCR fragments. (Region-wise HD95 on WT/TC/ET is not significant under medpy — there is no WT gain.)

→ The CC-consensus filter is the right post-hoc move, but it is near the ceiling of the hard-label paradigm. Further improvement should target **training-time fragment-aware losses** (Paper 2), not more post-hoc engineering.

---

## Interactive 3D viewer

**→ [guillaume-cassez.fr/imagerie-medicale/brats/2023-distance-map/viewer/](https://guillaume-cassez.fr/imagerie-medicale/brats/2023-distance-map/viewer/)**

Six patients (C1–C6) are pinned at the top of the Patient dropdown. Each one illustrates a distinct ordering between Baseline / DistMap / Fusion on the Dice metric. Toggle between the models, rotate, slice, and compare against Ground Truth in one click.

| Case | Patient | B | D | F | Take-away |
|---|---|---|---|---|---|
| C1 — D < F < B | 01435-000 | 0.924 | 0.629 | 0.924 | DistMap generates spurious TC/ET components on an oedema-only case; major veto restores Baseline |
| C2 — F = D > B | 01094-000 | 0.643 | 0.968 | 0.968 | Dominant mode (98.9 %): the veto removes nothing, DistMap confirmed |
| C3 — B < F < D | 01530-000 | 0.241 | 0.542 | 0.285 | Filter pulled baseline-side: the uncorroborated DistMap core is removed |
| C4 — F = D > B | 00017-001 | 0.656 | 0.657 | 0.657 | Nothing to remove; both models miss the core (TC = 0) |
| C5 — F > max(B,D) | 00733-001 | 0.751 | 0.805 | 0.964 | Clean synergy: the WT contour restored beyond both parents |
| C6 — F < min(B,D) | 00388-000 | 0.923 | 0.922 | 0.921 | Break mode almost extinct in the official regime (2/1196, max gap 0.0007) |

---

## Try the CC-consensus filter on your own predictions

The rule is parameter-free (only 26-connectivity). Plug in your own two segmentation arrays (DistMap + Baseline, both label maps in `{0, 1, 2, 3}`):

```python
import numpy as np
from scipy import ndimage as ndi

STRUCT_26 = ndi.generate_binary_structure(3, 3)

def cc_consensus_filter(distmap_seg, baseline_seg, classes=(1, 2, 3)):
    """Connected-component consensus filter.
    Start from DistMap; for each class, drop any CC of DistMap whose same-class
    mask has zero voxel overlap with Baseline. Parameter-free (26-connectivity)."""
    filtered = distmap_seg.copy()
    for c in classes:
        d_mask = (distmap_seg == c); b_mask = (baseline_seg == c)
        if not d_mask.any(): continue
        lab, n = ndi.label(d_mask, structure=STRUCT_26)
        for cc_id in range(1, n + 1):
            cc = (lab == cc_id)
            if not np.any(cc & b_mask):
                filtered[cc] = 0  # unconfirmed fragment
    return filtered
```

---

## Repository layout

```
├── paper.md                     Paper source (English, Markdown)
├── paper.pdf                    Paper (English, compiled)
├── paper_fr.md                  Paper source (French, Markdown)
├── paper_fr.pdf                 Paper (French, compiled)
├── README.md                    This file (English)
├── README_fr.md                 Version française
├── LICENSE                      MIT
├── CITATION.cff                 Machine-readable citation
├── scripts/                     All analysis scripts (Python)
│   ├── extract_patient_features.py        20 GT-morphology features (tower-only: needs NIfTI)
│   ├── extract_agreement_features.py      11 inter-model agreement features (tower-only)
│   ├── sweep_adaptive_fusion.py           Threshold sweep {20…∞} vx (tower-only)
│   ├── compute_hd95_per_class.py          Per-class HD95 on NCR/ED/ET (tower-only)
│   ├── count_fragments_topological.py     Topological fragment count (CC−1 per class) per variant (tower-only)
│   ├── select_demo_patients.py            C1–C6 champion selection
│   ├── analyze_case_features.py           Mann-Whitney + per-case RF importance
│   ├── oracle_per_class.py                Patient + per-class oracle bounds
│   ├── analyze_sweep.py                   Sweep classification (reads data/sweep.csv)
│   ├── meta_selector.py                   Patient-level meta-classifier
│   ├── meta_selector_perregion.py         3 classifiers per region × 5-fold CV
│   ├── simple_combinations.py             27 fixed rules + 1-feature search
│   └── simple_rule_cv.py                  1-feature rule in 5-fold CV (overfit)
├── data/                        Pre-extracted CSVs (1196 patients, ready to use)
│   ├── rankings.json                      Per-patient Dice + HD95 (B/D/F × WT/TC/ET)
│   ├── all_cases.json                     All 6 case classifications
│   ├── C1_*..C6_*.csv                     One CSV per case, ranked
│   ├── patient_features.csv               20 morpho features × 1196 patients
│   ├── patient_agreement_features.csv     11 agreement features × 1196 patients
│   └── sweep.csv                          Threshold-sweep per-patient Dice (6 thresholds)
├── analysis/                    Generated outputs (reproducible from data/)
│   ├── mann_whitney.csv
│   ├── rf_importance_BvD.csv
│   ├── rf_importance_fusion4.csv
│   ├── per_case_stats.csv
│   ├── meta_selector.txt
│   ├── meta_selector_perregion.txt
│   ├── adaptive_fusion_summary.txt
│   ├── hd95_per_class_cv.csv              Per-class HD95 (NCR/ED/ET) for B/D/F × 1196 patients
│   └── fragments_topological_cv.csv       Topological fragment counts (CC−1 per class) for B/D/F × 1196 patients
└── viewer/                      Pointer to the interactive 3D viewer
    └── README.md
```

BraTS 2023 GLI raw NIfTI images are **not** redistributed here (challenge licence). Obtain them from the [official BraTS 2023 portal](https://www.synapse.org/#!Synapse:syn51156910).

---

## Reproduce the numbers

```bash
# 1. Install minimal deps
pip install numpy scipy scikit-learn scikit-image nibabel

# 2. Run any analysis script (all operate on the CSVs in data/)
python3 scripts/oracle_per_class.py                # patient + per-class oracles
python3 scripts/analyze_case_features.py           # Mann-Whitney tests + per-case stats
python3 scripts/select_demo_patients.py            # C1-C6 case classification → data/
python3 scripts/meta_selector.py                   # patient-level meta-classifier
python3 scripts/meta_selector_perregion.py         # 3 classifiers × per-region × 5-fold CV
python3 scripts/simple_combinations.py             # 27 fixed rules + 1-feature search
python3 scripts/simple_rule_cv.py                  # 1-feature rule CV (overfit check)
python3 scripts/analyze_sweep.py                   # adaptive threshold sweep stats
```

These scripts only read the CSVs and JSON shipped in `data/` — they are fully reproducible from a clone.

Patient-level feature extraction (`extract_patient_features.py`, `extract_agreement_features.py`), the threshold sweep (`sweep_adaptive_fusion.py`), and per-class HD95 (`compute_hd95_per_class.py`) require the baseline/DistMap prediction NIfTIs *and* (for morphology features + HD95) the ground-truth NIfTI files — none of which are redistributed here (BraTS 2023 challenge licence). Training the models requires the full nnU-Net v2 pipeline with the MedNeXt backbone.

---

## Cite

```bibtex
@article{cassez2026ccconsensus,
  title   = {Two Models That Agree Beat the Best of Them Alone:
             Parameter-Free Connected-Component Consensus That Beats the
             Baseline under the Official BraTS-2023 Metrics},
  author  = {Cassez, Guillaume and Larnier, Stanislas},
  journal = {Zenodo preprint},
  year    = {2026},
  url     = {https://guillaume-cassez.fr/imagerie-medicale/brats/2023-distance-map/},
  doi     = {10.5281/zenodo.19695263}
}
```

---

## About the author

I'm **Guillaume Cassez** ([ORCID 0009-0007-0987-3931](https://orcid.org/0009-0007-0987-3931)), and I built this project in 2026 as **independent research** (outside any institutional framework), with the methodological guidance and review of **Stanislas Larnier** (training mentor). The full trajectory — Research Report 1 on post-hoc fusion (here) and Report 2 on fragment-penalising training-time losses (in progress) — is motivated by a simple observation : the best tools today report Dice scores, but clinicians care about whether the segmentation has artefacts that a radiologist would flag immediately.

**I'm currently looking for opportunities**, ideally :

- **ML / Research engineering** in medical imaging, clinical AI, or biomedical computer vision
- **Applied ML research** positions (CDD, CDI, **PhD**, industrial post-doc, R&D teams)
- **MLOps / engineering** in health-tech contexts

If this kind of work is what your team does, I'd love to chat — even just to exchange notes on the ceiling analysis or the fragment phenomenon.

→ [cassez.guillaume@gmail.com](mailto:cassez.guillaume@gmail.com)
→ [guillaume-cassez.fr](https://guillaume-cassez.fr)
→ [Bluesky @guillaume-cassez.bsky.social](https://bsky.app/profile/guillaume-cassez.bsky.social)
→ [ORCID 0009-0007-0987-3931](https://orcid.org/0009-0007-0987-3931)

For technical discussion on this work specifically, please open a [GitHub issue](https://github.com/guillaume-cassez/brats-moe-distmap-fusion-1/issues) — it helps future readers.

---

## License

The **code** in this repository is released under the [MIT License](LICENSE).
The **figures and text of the paper** (paper.md and any derivative figures) are released under [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/): redistribution and remix permitted with attribution.
BraTS 2023 raw imaging data is **not** redistributed and remains under its original challenge licence.
