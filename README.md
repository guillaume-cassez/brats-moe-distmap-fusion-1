# brats-moe-distmap-fusion-1

**Distance Map Auxiliary Loss for Brain Tumor Segmentation:
A Fragment-Centric Analysis and the Saturation Ceiling of Post-hoc MoE Fusion**

Code, data artefacts, and paper source for a BraTS 2023 GLI study.

[![interactive viewer](https://img.shields.io/badge/🌐_interactive_viewer-guillaume--cassez.fr%2Fbrats-blue)](https://guillaume-cassez.fr/brats/)
[![paper page](https://img.shields.io/badge/📄_paper_landing-guillaume--cassez.fr%2Fbrats%2Fpaper1-blue)](https://guillaume-cassez.fr/brats/paper1/)
[![license](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.19695264.svg)](https://doi.org/10.5281/zenodo.19695264)

---

## TL;DR

1. Adding a Signed Distance Transform (SDT) auxiliary loss on top of MedNeXt-B / nnU-Net v2 gives a robust **+0.63 to +0.96 percentage-point Dice gain per region** (Wilcoxon p < 10⁻⁶, n = 240).

2. The SDT loss introduces a new failure mode: **spurious isolated connected components ("fragments")** not present in the ground truth, most acute on NCR (necrotic core) and ED (edema).

3. A **parameter-free Mixture-of-Experts (MoE) fusion rule** — start from DistMap, drop any connected component whose same-class mask has zero overlap with Baseline — **removes 81 % of NCR fragments** (Wilcoxon p = 7 × 10⁻⁴) at no Dice cost.

4. On 1196 patients (5-fold CV), the **oracle per-class selection upper-bound** is only **+0.005 Dice avg** above this default fusion rule. **No classifier** (RF / LR / GBM) trained on 31 hand-crafted features (GT morphology + inter-model agreement) **robustly beats the default in CV**. Closing the gap requires voxel-level probabilistic voting or architectural diversity.

→ The default MoE fusion is already near-optimal within the hard-label post-hoc paradigm. Further improvement should target **training-time fragment-aware losses** (Paper 2), not more post-hoc engineering.

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

## Try the MoE fusion rule on your own predictions

The rule is parameter-free (only 26-connectivity). Plug in your own two segmentation arrays (DistMap + Baseline, both label maps in `{0, 1, 2, 3}`):

```python
import numpy as np
from scipy import ndimage as ndi

STRUCT_26 = ndi.generate_binary_structure(3, 3)

def moe_fusion(distmap_seg, baseline_seg, classes=(1, 2, 3)):
    """Start from DistMap, remove any CC of each class that has no
    voxel overlap with Baseline same-class. Parameter-free."""
    fused = distmap_seg.copy()
    for c in classes:
        d_mask = (distmap_seg == c); b_mask = (baseline_seg == c)
        if not d_mask.any(): continue
        lab, n = ndi.label(d_mask, structure=STRUCT_26)
        for cc_id in range(1, n + 1):
            cc = (lab == cc_id)
            if not np.any(cc & b_mask):
                fused[cc] = 0  # unconfirmed fragment
    return fused
```

---

## Repository layout

```
├── paper.md                     Paper source (Markdown)
├── README.md                    This file
├── LICENSE                      MIT
├── CITATION.cff                 Machine-readable citation
├── scripts/                     All analysis scripts (Python)
│   ├── extract_patient_features.py        20 GT-morphology features per patient
│   ├── extract_agreement_features.py      11 inter-model agreement features
│   ├── select_demo_patients.py            C1–C6 champion selection
│   ├── analyze_case_features.py           Mann-Whitney + per-case RF importance
│   ├── oracle_per_class.py                Patient + per-class oracle bounds
│   ├── sweep_adaptive_fusion.py           Threshold sweep {20…∞} vx
│   ├── analyze_sweep.py                   Sweep classification
│   ├── meta_selector.py                   Patient-level meta-classifier
│   ├── meta_selector_perregion.py         3 classifiers per region × 5-fold CV
│   ├── simple_combinations.py             27 fixed rules + 1-feature search
│   └── simple_rule_cv.py                  1-feature rule in 5-fold CV (overfit)
├── data/                        Pre-extracted CSVs (1196 patients)
│   ├── all_cases.json                     All 6 case classifications
│   ├── C1_*..C6_*.csv                     One CSV per case, ranked
│   ├── patient_features.csv               20 morpho features × 1196 patients
│   └── patient_agreement_features.csv     11 agreement features × 1196 patients
├── analysis/                    Generated outputs (reproducible)
│   ├── mann_whitney.csv
│   ├── rf_importance_BvD.csv
│   ├── rf_importance_fusion4.csv
│   ├── per_case_stats.csv
│   ├── meta_selector.txt
│   ├── meta_selector_perregion.txt
│   └── adaptive_fusion_summary.txt
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
python3 scripts/analyze_case_features.py           # Mann-Whitney tests
python3 scripts/meta_selector_perregion.py         # 3 RF + CV
python3 scripts/simple_rule_cv.py                  # 1-feature rule CV (overfit check)
```

Patient-level feature extraction (`extract_patient_features.py`, `extract_agreement_features.py`) requires the ground-truth NIfTI files *and* the baseline/DistMap predictions (not redistributed). Training the models requires the full nnU-Net v2 pipeline with the MedNeXt backbone.

---

## Cite

```bibtex
@article{cassez2026moefusion,
  title   = {Distance Map Auxiliary Loss for Brain Tumor Segmentation:
             A Fragment-Centric Analysis and the Saturation Ceiling of
             Post-hoc MoE Fusion},
  author  = {Cassez, Guillaume},
  journal = {arXiv preprint},
  year    = {2026},
  url     = {https://guillaume-cassez.fr/brats/paper1/}
}
```

---

## About the author

I'm **Guillaume Cassez** ([ORCID 0009-0007-0987-3931](https://orcid.org/0009-0007-0987-3931)), and I built this project in 2026 during a PhD candidacy in medical AI / computer vision. The full trajectory of the research — Paper 1 on post-hoc fusion (here) and Paper 2 on fragment-penalising training-time losses (in progress) — is motivated by a simple observation: our best tools report Dice scores, but clinicians care about whether the segmentation has artefacts that a radiologist would flag immediately.

**I'm currently looking for opportunities**, ideally:

- **ML / Research engineering** in medical imaging, clinical AI, or biomedical computer vision
- **Applied ML research** positions (CDD, CDI, PhD, industrial post-doc)
- **MLOps / engineering** in health-tech contexts

If this kind of work is what your team does, I'd love to chat — even just to exchange notes on the ceiling analysis or the fragment phenomenon.

→ [guillaumecassezwork@gmail.com](mailto:guillaumecassezwork@gmail.com)
→ [guillaume-cassez.fr](https://guillaume-cassez.fr)

For technical discussion on this work specifically, please open a [GitHub issue](https://github.com/guillaume-cassez/brats-moe-distmap-fusion-1/issues) — it helps future readers.

---

## License

The **code** in this repository is released under the [MIT License](LICENSE).
The **figures and text of the paper** (paper.md and any derivative figures) are released under [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/): redistribution and remix permitted with attribution.
BraTS 2023 raw imaging data is **not** redistributed and remains under its original challenge licence.
