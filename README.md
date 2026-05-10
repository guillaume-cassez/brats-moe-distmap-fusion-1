# brats-moe-distmap-fusion-1

**Distance Map Auxiliary Loss for Brain Tumor Segmentation:
A Fragment-Centric Analysis and the Saturation Ceiling of Post-hoc Connected-Component Consensus Filtering**

*English version. Version française : [README_fr.md](README_fr.md).*

Code, data artefacts, and paper source for a BraTS 2023 GLI study.

> *Note on naming.* Earlier drafts used "MoE fusion". This version drops that label : the rule is not a Mixture-of-Experts in the strict sense (no learned gating network, no soft routing). It is a **hard-label, post-hoc, connected-component-level consensus filter** — precisely described as **CC-consensus filter** throughout. The repository slug (`brats-moe-distmap-fusion-1`) is kept for URL / DOI stability.

[![interactive viewer](https://img.shields.io/badge/🌐_interactive_viewer-guillaume--cassez.fr%2Fbrats-blue)](https://guillaume-cassez.fr/brats/)
[![paper page](https://img.shields.io/badge/📄_paper_landing-guillaume--cassez.fr%2Fbrats%2Fpaper1-blue)](https://guillaume-cassez.fr/brats/paper1/)
[![license](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.19695263.svg)](https://doi.org/10.5281/zenodo.19695263)

---

## The story behind this repo

I started this project excited by a simple idea : distance-map auxiliary losses have lifted segmentation in **other medical imaging tasks** (abdominal organs, liver, cardiac — Ma MIDL 2020 ; Xue AAAI 2020), so the same should help on BraTS 2023 GLI — especially with the recent MedNeXt-B backbone. The hypothesis felt cheap to test.

**The first surprise**: at 10 epochs the Dice delta looked great (+0.74 pp avg), but at 300 epochs on the full 5-fold CV (1196 patients) the delta dissolved into measurement noise (+0.09 pp, p > 0.25 per region). So DistMap doesn't give you Dice for free.

**The second surprise**: while comparing predictions, something caught my eye — DistMap was producing more tiny isolated blobs than Baseline, most visible on NCR (necrotic core). Quantified: ×1.5 more fragments. A failure mode nobody had reported before on BraTS.

**The third surprise, and the most exciting**: a parameter-free post-hoc fix — a connected-component consensus filter that vetoes DistMap-exclusive components using Baseline as a second detector — cuts **66 % of NCR fragments** on 1196 patients (Wilcoxon p < 10⁻¹⁸⁹) at zero Dice cost, AND significantly improves HD95 on NCR with p = 5.7 × 10⁻¹⁴.

So the final story is not "DistMap is better". It is "DistMap has a different decision surface, produces a specific artefact, and a simple post-hoc rule turns that into a clinically meaningful boundary-quality gain on tumor necrosis". The Dice metric was hiding the real signal. That is the paper.

---

## TL;DR

1. **At convergence on 1196 patients in 5-fold CV**, adding a Signed Distance Transform (SDT) auxiliary loss on top of MedNeXt-B / nnU-Net v2 **does NOT significantly improve Dice** (Δ = +0.09 pp, Wilcoxon p > 0.25 per region). The two models are Dice-equivalent within measurement error.

2. But the SDT loss introduces a new failure mode: **spurious isolated connected components ("fragments")** not present in the ground truth, most acute on NCR (necrotic core) and ED (edema).

3. A **parameter-free connected-component consensus filter (CC-consensus filter)** — start from DistMap, drop any connected component that does not overlap Baseline in the same class — **removes 66 % of NCR fragments** on 1196 patients (Wilcoxon p < 10⁻¹⁸⁹, topological definition: CC − 1 per class), 52 % on ED (p < 10⁻¹⁶²), 33 % on ET (p = 1.1 × 10⁻⁵³), at no Dice cost, AND **significantly improves HD95 on NCR** (4.86 → 4.48 mm, p = 5.7 × 10⁻¹⁴) and WT (3.86 → 3.76 mm, p = 2.7 × 10⁻⁴). The boundary-quality gain is clinically relevant on tumor necrosis — the exact region where spurious fragments could mislead a radiotherapist.

4. On 1196 patients (5-fold CV), the **oracle per-class selection upper-bound** is only **+0.005 Dice avg** above this default CC-consensus rule. **No classifier** (RF / LR / GBM) trained on 31 hand-crafted features (GT morphology + inter-model agreement) **robustly beats the default in CV**. Closing the gap requires voxel-level probabilistic voting or architectural diversity.

→ The default CC-consensus filter is already near-optimal within the hard-label post-hoc paradigm. Further improvement should target **training-time fragment-aware losses** (Paper 2), not more post-hoc engineering.

---

## Interactive 3D viewer

**→ [guillaume-cassez.fr/brats/](https://guillaume-cassez.fr/brats/)**

Six patients (C1–C6) are pinned at the top of the Patient dropdown. Each one illustrates a distinct ordering between Baseline / DistMap / Fusion on the Dice metric. Toggle between the models, rotate, slice, and compare against Ground Truth in one click.

| Case | Patient | B | D | F | Take-away |
|---|---|---|---|---|---|
| C1 — B > D | 00048-001 | 0.983 | 0.308 | 0.973 | DistMap hallucinates TC/ET on an oedema-only case |
| C2 — D > B | 01437-000 | 0.589 | 0.923 | 0.923 | DistMap rescues an under-segmenting Baseline |
| C3 — B < F < D | 01428-000 | 0.618 | 0.656 | 0.645 | Fusion sits between, pulled baseline-side |
| C4 — D < F < B | 00017-001 | 0.991 | 0.657 | 0.890 | Fusion rescues DistMap via consensus |
| C5 — F < min(B,D) | 01530-000 | 0.241 | 0.541 | 0.169 | Fusion deletes a legitimate large DistMap CC |
| C6 — F > max(B,D) | 00540-000 | 0.785 | 0.795 | 0.869 | Clean synergy |

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
  title   = {Distance Map Auxiliary Loss for Brain Tumor Segmentation:
             A Fragment-Centric Analysis and the Saturation Ceiling of
             Post-hoc Connected-Component Consensus Filtering},
  author  = {Cassez, Guillaume},
  journal = {arXiv preprint},
  year    = {2026},
  url     = {https://guillaume-cassez.fr/brats/paper1/},
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
