# Distance Map Auxiliary Loss for Brain Tumor Segmentation: Honest Re-evaluation under the Official BraTS-2023 Metrics — a Recall-Oriented SDT Head and a Connected-Component Consensus that Beats the Baseline

**Guillaume Cassez**

Independent research · [ORCID 0009-0007-0987-3931](https://orcid.org/0009-0007-0987-3931) · `cassez.guillaume@gmail.com` · [guillaume-cassez.fr](https://guillaume-cassez.fr)

*BraTS 2023 GLI · nnU-Net v2 · MedNeXt-B · 1196 validation patients*

---

## Abstract

We evaluate the addition of a signed distance-map (SDT — Signed Distance Transform) auxiliary regression head on top of a MedNeXt-B / nnU-Net v2 pipeline for 3D adult glioma segmentation (BraTS 2023 GLI), under the **complete set of official BraTS-2023 metrics** — lesion-wise Dice and HD95 (the challenge ranking metrics), legacy region-wise Dice and HD95, and lesion detection — in 5-fold cross-validation at convergence (300 epochs, n = 1196). On the **pre-specified primary endpoints** — the two official ranking metrics, region-averaged, Holm-corrected — the SDT head shows **no significant effect** (lesion-wise Dice Δ = −0.003, Holm p = 1.0; lesion-wise HD95 Δ = +1.12 mm, Holm p = 1.0); it is also **Dice-neutral** on the legacy region overlap (Δ = +0.001, p = 0.24). The Dice gain claimed in an earlier reduced-training-budget version **does not survive to convergence**.

The only robust effect of the SDT head is a **recall-oriented shift**: higher region sensitivity (Δ = +0.002, r = +0.20, p = 2.0 × $10^{-9}$) and fewer missed lesions (FN Δ = −0.006, p = 8.3 × $10^{-3}$), at a **specificity cost** (r = −0.26, p = 1.2 × $10^{-14}$) — i.e. more **spurious connected components** ("fragments") on TC and ET. We characterise this topological artefact on all 1196 patients (DistMap: ×1.5 NCR fragments vs Baseline, ×1.2 ED), a failure mode so far unreported in the BraTS literature and **invisible to Dice**.

We exploit this trade-off with a **connected-component consensus filter** (CC-consensus), post-hoc and parameter-free, that keeps a DistMap component only if a second model — Baseline (`CC(D∩B)`), or the more-specific Kervadec head (`CC(D∩K)`, Paper 2) — corroborates it in the same class. The consensus removes **~41 % of the spurious lesions** (FP lesions 0.396 → 0.234 per case, p = 6.0 × $10^{-34}$) at a **negligible recall cost**, and is **the first configuration to significantly beat the baseline on both official ranking metrics**: lesion-wise Dice **+0.024** (Holm p = 4.5 × $10^{-16}$) and lesion-wise HD95 **−9.49 mm** (Holm p = 5.7 × $10^{-26}$). This gain is **invisible to legacy region Dice** — which is saturated: the per-class oracle is only +0.005 above the default — but material under the official lesion-wise metric, which is why we report the full set. Part of the HD95 gain comes from the 374 mm penalty the official metric imposes per spurious lesion; we state this explicitly rather than implying a boundary-precision gain on true lesions. Complementarily, on the legacy per-class distances, the filter also reduces NCR HD95 (4.86 → 4.48 mm, p = 5.7 × $10^{-14}$) by eliminating 66 % of NCR fragments.

**Contributions.** (1) A convergence-time evaluation (300 ep, 5-fold CV, n = 1196) of an SDT auxiliary head under **all** official BraTS-2023 metrics, with a pre-specified primary endpoint — no metric cherry-picking: the SDT head is **neutral/null on the official ranking**. (2) The quantitative, large-scale, Dice-invisible characterisation of a topological fragment artefact (the "specificity-cost" counterpart of the recall-oriented shift), with a topological definition free of size threshold. (3) A simple, parameter-free CC-consensus filter that turns this trade-off into a **system that beats the baseline on the official metrics** (lesion-wise Dice +0.024; lesion-wise HD95 −9.49 mm) — the only configuration here to do so.

---

## 1. Introduction

Brain tumor segmentation on multi-modal MRI (BraTS challenge) has been dominated in recent years by nnU-Net [Isensee 2021] derivatives. The canonical task is 3D voxel classification into four classes: background, necrotic core (NCR, label 1), peritumoral edema (ED, label 2) and enhancing tumor (ET, label 3). Performance is usually reported as Dice coefficients on three nested regions WT = {1,2,3}, TC = {1,3}, ET = {3}.

Top-performing teams refine the backbone (MedNeXt [Roy MICCAI 2023], Swin-UNETR) while leaving the training loss essentially unchanged: Dice + cross-entropy. In parallel, **auxiliary distance-map regression** [Ma MIDL 2020 ; Xue AAAI 2020] is regularly proposed to make the network shape-aware, with mixed empirical results. Applications specific to BraTS exist — parallel-decoder multi-task learning [Huang 2021], Hausdorff-aware losses [Karimi & Salcudean 2020], and regression-only geodesic formulations [Dang 2024, SiNGR] — but none to date report or analyse the fragment artefact characterised here (§5.2).

This paper pursues three objectives:

* **Empirical characterisation** of the auxiliary SDT task at convergence on MedNeXt-B / nnU-Net v2: at 300 epochs in 5-fold CV on 1196 patients, DistMap produces **no** significant Dice gain (p > 0.25 per region), contrary to the impression drawn from comparisons at reduced training budgets.
* **Failure-mode analysis**: identification and quantification of an under-reported artefact of the SDT task — the production of small, spatially-isolated connected components that inflate false-positive counts without materially affecting Dice. This qualitative observation was made possible by an **interactive companion 3D viewer** built specifically for this project, which renders Baseline / DistMap / CC-Consensus meshes side-by-side for all 1196 patients ([guillaume-cassez.fr/brats/](https://guillaume-cassez.fr/brats/)).
* **Ceiling analysis** of a post-hoc CC-consensus filter that corrects this artefact, with a 1196-patient study delimiting what a feature-based meta-selector can achieve without softmax access or model diversity.

---

## 2. Related work

**Distance-transform auxiliary losses on medical segmentation.** [Ma 2020] proposes an auxiliary SDT regression head for abdominal / cardiac structures (LiTS, LA atrium), establishing the tanh + MSE recipe adopted here. [Xue 2020] uses signed distance maps as the **main output** (not auxiliary) on organ datasets with λ = 10 and no ablation. [Karimi & Salcudean 2020] derive a Hausdorff-distance-aware loss from distance transforms and evaluate it on nnU-Net + BraTS, but as a **loss modification** rather than as an auxiliary regression head. None of these works report the fragment phenomenon characterised here.

**Distance-map approaches applied specifically to BraTS.** The idea of combining distance-based shape supervision with BraTS segmentation is **not novel in itself**; two prior works are particularly close to the present setup and must be flagged explicitly.

- [Huang et al. 2021] train a V-Net with two *parallel decoders* on BraTS 2018–2020 — one producing the segmentation mask, the other regressing an *unsigned* distance transform through a sigmoid activation. This is the closest published prior art. The present work differs in three concrete ways: (i) a lightweight `Conv3d(32→3) + tanh` auxiliary head rather than a full parallel decoder (<0.1 % added parameters vs a doubled decoder path); (ii) *signed* Euclidean distance with MSE, not unsigned DT with sigmoid; (iii) MedNeXt-B / nnU-Net v2 on BraTS 2023 GLI (1196 patients) rather than V-Net on BraTS 2018–2020.
- [Dang et al. 2024, *SiNGR*] propose a **signed normalised geodesic** regression with Focal-L1 on tanh-activated outputs, **replacing** the segmentation output on BraTS 2020 (Swin-UNETR / UNet3D backbones). The present work is multi-task (keeps the Dice + CE softmax output alongside the SDT regression) and uses plain signed Euclidean distance, not a geodesic transform.

Neither Huang et al. nor SiNGR report or analyse the fragment artefact described in §5.2 of this paper; this is the specific empirical contribution claimed here.

**Ensembling and fusion.** Classical BraTS winners rely on 5-fold ensembling (soft-voting of softmax outputs). Model-selection or stacking rules at the patient level are uncommon; connected-component-level consensus rules are rarer still in the published BraTS literature.

**Failure-mode analysis.** Component-level metrics (lesion-wise F1) have been introduced in the BraTS 2023 challenge but remain secondary to Dice / HD95 in published work. To our knowledge, no prior work quantifies and localises the fragment bias of SDT-auxiliary losses on BraTS.

---

## 3. Methods

### 3.1 Architecture and training

**Backbone.** MedNeXt-B [Roy MICCAI 2023] re-implemented inside nnU-Net v2 with the `nnUNetPlans_96GB_mednext` plan (patch 128³, BS 2, BF16, RTX PRO 6000 Blackwell).

**Auxiliary head.** A single 1 × 1 × 1 Conv3D(32 → 3) + tanh predicting a normalised SDT map for each of NCR, ED, ET regions. Ground-truth SDT is pre-computed once per patient via `scipy.ndimage.distance_transform_edt` on each binarised region mask, signed by sign(inside − outside), and min-max clipped to [−1, 1] with boundary = 0.

**Loss.** $\mathcal{L} = \mathcal{L}_{\mathrm{Dice+CE}} + \lambda \cdot \mathcal{L}_{\mathrm{MSE}}^{\mathrm{SDT}}$, with $\lambda = 1$ as the default (gradient-balanced calibration ÷ 5; full static ablation over 11 values detailed in Appendix A).

### 3.2 Variant naming

| Variant | Trainer | Auxiliary? |
|---|---|---|
| **Baseline** | `nnUNetTrainerMedNeXtBaseline` | no SDT |
| **DistMap** | `nnUNetTrainerMedNeXtDistMap` | SDT, λ = 1 |
| **CC-Consensus** | post-hoc rule (§3.3) on DistMap + Baseline | post-hoc |

### 3.3 CC-consensus filtering rule[^moe]

[^moe]: Earlier versions of this work referred to this rule as "MoE (Mixture-of-Experts) fusion". That label is dropped: there is no learned gating network, no soft routing of inputs, and no joint training of experts and gate. The neutral name "CC-consensus filter" is used throughout the document.

Given Baseline prediction $P_B$ and DistMap prediction $P_D$ (both class-label tensors in {0, 1, 2, 3}), the filtered prediction $P_F$ is computed class-by-class:

```
P_F := copy(P_D)
for each class c $\in$ {1, 2, 3}:
    D_mask  := (P_D == c)
    B_mask  := (P_B == c)
    labeled, n := cc_label(D_mask, structure=26-connectivity)
    for each cc_id $\in$ 1..n:
        cc := (labeled == cc_id)
        if cc $\cap$ B_mask = $\emptyset$:
            P_F[cc] := 0            # remove unconfirmed fragment
```

The rule has four qualitative effects:

1. DistMap fragments isolated from same-class Baseline → **removed**.
2. DistMap boundary refinement not overlapping Baseline → **kept** (the rule always starts from $P_D$).
3. Baseline holes that DistMap fills → **kept** ($P_D$ is non-zero there).
4. Baseline false positives that DistMap rejects → **stay rejected** ($P_D$ is zero there).

The rule has **no learnable parameter** and a single hyper-parameter (26- vs 6-connectivity), kept at 26 throughout. It is a *veto* operation: Baseline does not contribute any new voxels; it can only delete components that DistMap predicted without its confirmation.

### 3.4 Ceiling analysis

To characterise the quality ceiling reachable by any patient- or region-level selection policy over the three available predictions, we define, for each patient $p$ with regional Dice $(D^B, D^D, D^F) \in \mathbb{R}^3$ per region $r \in \{\mathrm{WT}, \mathrm{TC}, \mathrm{ET}\}$:

$$\mathrm{Oracle}_{\mathrm{patient}}(p) = \max_{m \in \{B,D,F\}} \tfrac{1}{3}\sum_r D^m_r$$

$$\mathrm{Oracle}_{\mathrm{per\text{-}class}}(p) = \tfrac{1}{3}\sum_r \max_{m \in \{B,D,F\}} D^m_r$$

The gap between these oracles and the default CC-consensus mean is the maximum achievable gain of any selection policy. Candidate policies evaluated (size-adaptive threshold, meta-classifiers, one-feature rule) and their results are reported in §5.4 and detailed in Appendix B.

---

## 4. Experiments

### 4.1 Data

BraTS 2023 GLI (1251 patients, 4 modalities each). Spatial standardization is handled upstream by the official BraTS pipeline (rigid co-registration to the SRI24 atlas, 1 mm³ isotropic resampling, and skull-stripping); no cross-scanner intensity harmonization is applied at the dataset level. Intensity normalization is then handled by nnU-Net v2: each modality is z-scored per patient (`ZScoreNormalization`, computed over the whole volume, `use_mask_for_norm=False`), with automatic cropping, and MedNeXt-B consumes these normalized tensors directly. Ground-truth labels {0, 1, 2, 3}. Patient split: 5-fold cross-validation stratified by patient ID. All metrics below are computed on the fold-out set (n = 239 for fold 0) or aggregated over all 5 folds (n = 1196).

### 4.2 Metrics

**Official BraTS-2023 metrics (reference implementation).** All ranking and detection metrics are computed with the challenge reference implementation [Saluja *et al.* 2023, *BraTS-2023-Metrics*] (GLI parameters: dilation 3, lesion-volume threshold 50 voxels, 374 mm HD95 penalty per FP/FN lesion), on out-of-fold predictions identical across all models (paired statistics):

- **lesion-wise Dice and HD95** — the two official BraTS-2023 ranking metrics (26-connectivity components, dilation-merged GT lesions);
- **legacy region-wise Dice** (WT/TC/ET overlap) and **surface-distance HD95** [Nikolov *et al.* 2021];
- **region (voxel-level) sensitivity and specificity**, and **false-positive / false-negative lesion counts**.

An earlier in-house HD95 (a non-standard pooled 95th-percentile with a toroidal-wrap surface) is **dropped** in favour of the official surface-distance HD95: a hand-rolled metric is only justified when it captures something the official ones do not, which is not the case here.

**Pre-specified primary endpoint and multiplicity.** The primary endpoint is the **two official ranking metrics** (lesion-wise Dice and HD95), region-averaged, Holm-corrected across that 2-metric family. All other metrics and all per-region results are **exploratory**: Holm correction across the 3 regions within each metric, and a Benjamini–Hochberg false-discovery-rate control across the entire exploratory family (216 tests = metric × {WT, TC, ET} × model pair) — **106/216 survive at q < 0.05**, including every consensus and detection effect reported below. Paired two-sided Wilcoxon signed-rank tests on identical folds; matched-pairs rank-biserial effect size r (sign: + favours the first model). All raw and corrected p-values are reported; no metric is selected for convenience. Pipeline: `scripts/eval_lesionwise_kervadec.py` → `scripts/paper_stats.py`; tables by `scripts/make_tables.py` (single source of truth `paper_stats.json`).

**Legacy Dice convention.** The legacy per-region Dice (WT, TC, ED, ET) follows the standard nnU-Net / MONAI convention: *Dice = 1 if GT and prediction are both empty*. See §5.5 for caveats when comparing to BraTS challenge leaderboards.

**Fragment count (topological definition).** A **fragment** is a connected component (26-connectivity) of a given class that is **not the largest** component of its class — i.e. a CC topologically disconnected from the main tumor body. Per class $c$ on a prediction $P$, the fragment count is:
$$\mathrm{fragments}(P, c) = \max(0, \; \mathrm{nb\_CC}(P == c, \text{26-conn}) - 1)$$
No size threshold — 26-connectivity (shared face, edge, or corner) alone defines what is topologically linked. This definition treats small and large accessory components symmetrically.

**Inter-model agreement features (11)**: Dice(Baseline, DistMap) for WT/TC/ET; volumetric difference $|{|P_B^c|} - {|P_D^c|}| / ({|P_B^c|} + {|P_D^c|})$ for ET and NCR; number / fraction / max size of DistMap CC with no Baseline overlap, per ET and NCR.

**Morphology features (20)**: volume per region, volume ratios, 26-connectivity CC count and size for NCR/ET, inertia-tensor elongation (λ₁/λ₃), sphericity $(\pi^{1/3}(6V)^{2/3})/S$, surface roughness $S_{\mathrm{pred}}/S_{\mathrm{sphere}}$, Euler number ([scikit-image] `euler_number`, connectivity 3) for WT/TC/ET, cavity count of WT (`binary_fill_holes` diff), baseline / distmap CC counts per NCR and ET, ET CC spread (std of centroid distances).

---

## 5. Results

### 5.1 Under the official metrics, the SDT head is null on the ranking and Dice-neutral

Evaluation on the 1196 patients aggregated out-of-fold from the 5-fold CV (300-epoch schedule per fold; DistMap fold 0 stopped at 178 ep, the other 9 training runs complete), with the official BraTS-2023 implementation (§4.2).

**Pre-specified primary endpoints** (official ranking metrics, region-averaged, Holm-corrected across the 2-metric family). The SDT head shows no significant effect:

- **Lesion-wise Dice**: Δ = −0.003, r = +0.02, raw p = 0.55, **Holm p = 1.0** → not significant.
- **Lesion-wise HD95**: Δ = +1.12 mm, r = +0.02, raw p = 0.55, **Holm p = 1.0** → not significant.

The official challenge ranking metrics **do not separate** DistMap from Baseline. Full detail (both ranking metrics + legacy metrics):

| Metric | Region | DistMap | Baseline | Δ | r | win/loss | p | p(Holm) |
|---|---|---|---|---|---|---|---|---|
| Lesion-wise Dice | WT | 0.816 | 0.812 | +0.004 | +0.05 | 609/586 | 0.159 | 0.477 |
|  | TC | 0.862 | 0.870 | -0.008 | +0.01 | 605/584 | 0.741 | 1.000 |
|  | ET | 0.792 | 0.798 | -0.006 | -0.00 | 577/584 | 0.947 | 1.000 |
|  | **avg** | **0.823** | **0.826** | **-0.003** | +0.02 | 622/573 | **0.550** | -- |
| Lesion-wise HD95 (mm) | WT | 51.11 | 53.09 | -1.98 | +0.10 | 363/294 | 0.023* | 0.069 |
|  | TC | 28.14 | 24.68 | +3.46 | -0.01 | 246/214 | 0.901 | 0.901 |
|  | ET | 46.76 | 44.89 | +1.87 | -0.06 | 205/212 | 0.324 | 0.649 |
|  | **avg** | **42.01** | **40.89** | **+1.12** | +0.02 | 465/406 | **0.553** | -- |
| Legacy Dice | WT | 0.936 | 0.935 | +0.001 | +0.01 | 589/606 | 0.716 | 1.000 |
|  | TC | 0.917 | 0.918 | -0.000 | +0.04 | 612/577 | 0.243 | 0.729 |
|  | ET | 0.871 | 0.869 | +0.002 | +0.01 | 582/581 | 0.720 | 1.000 |
|  | **avg** | **0.908** | **0.907** | **+0.001** | +0.04 | 620/575 | **0.237** | -- |
| Legacy HD95 (mm) | WT | 5.51 | 5.79 | -0.28 | +0.07 | 306/276 | 0.172 | 0.344 |
|  | TC | 5.89 | 6.00 | -0.11 | +0.14 | 242/186 | 0.010* | 0.030† |
|  | ET | 11.54 | 11.62 | -0.08 | +0.07 | 178/163 | 0.270 | 0.344 |
|  | **avg** | **7.65** | **7.81** | **-0.16** | +0.11 | 438/365 | **0.008\*** | -- |

Δ = DistMap − Baseline. r = matched-pairs rank-biserial (+ favours DistMap). \* raw p < 0.05; † Holm-corrected p < 0.05 (across the 3 regions). n = 1196. Paired two-sided Wilcoxon signed-rank test.

Legacy region Dice is **neutral** (avg Δ = +0.001, p = 0.24): the Dice advantage reported at a reduced training budget does not survive to convergence. The only overlap metric that moves is the legacy region HD95, which improves slightly on average (Δ = −0.16 mm, p = 8 × $10^{-3}$), driven by the tumor core (TC −0.11 mm, Holm 0.030†); on the lesion-wise side, HD95 improves on the whole tumor (WT −1.98 mm, p = 0.023) but the gain is cancelled on TC/ET, hence a null average — consistent with the detection trade-off below.

**The only robust effect: a recall-oriented shift.** On lesion detection, the signal is small in absolute magnitude but remarkably consistent in direction (rank-biserial, win/loss) and survives FDR correction:

| Metric | Region | DistMap | Baseline | Δ | r | win/loss | p | p(Holm) |
|---|---|---|---|---|---|---|---|---|
| FP lesions | WT | 0.297 | 0.337 | -0.040 | +0.08 | 133/108 | 0.159 | 0.159 |
|  | TC | 0.188 | 0.132 | +0.056 | -0.37 | 34/65 | 0.005* | 0.014† |
|  | ET | 0.836 | 0.718 | +0.118 | -0.13 | 73/106 | 0.051 | 0.103 |
|  | **avg** | **0.440** | **0.396** | **+0.045** | -0.08 | 180/201 | 0.177 | -- |
| FN lesions | WT | 0.075 | 0.080 | -0.005 | +0.49 | 8/2 | 0.058 | 0.137 |
|  | TC | 0.030 | 0.037 | -0.007 | +0.71 | 10/3 | 0.046* | 0.137 |
|  | ET | 0.035 | 0.042 | -0.007 | +0.41 | 10/3 | 0.046* | 0.137 |
|  | **avg** | **0.047** | **0.053** | **-0.006** | +0.57 | 16/8 | **0.008\*** | -- |
| Sensitivity | WT | 0.931 | 0.929 | +0.002 | +0.16 | 667/525 | 1.7e-06* | 3.3e-06† |
|  | TC | 0.921 | 0.921 | -0.001 | +0.14 | 685/500 | 3.4e-05* | 3.4e-05† |
|  | ET | 0.880 | 0.877 | +0.004 | +0.20 | 681/471 | 2.7e-09* | 8.0e-09† |
|  | **avg** | **0.910** | **0.909** | **+0.002** | +0.20 | 697/498 | **2.0e-09\*** | -- |
| Specificity | WT | 1.000 | 1.000 | -0.000 | -0.22 | 494/701 | 4.0e-11* | 8.0e-11† |
|  | TC | 1.000 | 1.000 | +0.000 | -0.18 | 505/678 | 4.2e-08* | 4.2e-08† |
|  | ET | 1.000 | 1.000 | -0.000 | -0.28 | 471/702 | 1.5e-16* | 4.6e-16† |
|  | **avg** | **1.000** | **1.000** | **-0.000** | -0.26 | 456/739 | **1.2e-14\*** | -- |

The SDT head makes the model **more sensitive** — region sensitivity rises on all 3 regions (avg Δ = +0.002, r = +0.20, p = 2.0 × $10^{-9}$) and fewer lesions are missed (FN avg Δ = −0.006, p = 8.3 × $10^{-3}$) — at a systematic **specificity cost** (avg r = −0.26, p = 1.2 × $10^{-14}$): more spurious lesions on the tumor core and the enhancing tumor (FP TC Δ = +0.056, Holm 0.014†; FP ET Δ = +0.118, p = 0.051), while reducing those of the whole tumor (FP WT Δ = −0.040). We therefore re-frame the SDT head as a **recall-oriented boundary regularizer**, not a Dice booster.

**Implication.** DistMap produces predictions that *differ* from Baseline (the two models disagree on 1195/1196 patients) but their disagreements cancel on overlap metrics. The "specificity-cost" counterpart of this shift has a precise topological signature — the appearance of small spurious connected components — which is the subject of the next section.

### 5.2 DistMap introduces spurious fragments

Qualitative inspection of DistMap predictions targeted cleaner boundaries — the expected behaviour of a distance-aware loss. Instead, DistMap predictions consistently show more isolated connected components than Baseline — the **topological manifestation of the specificity loss** quantified in §5.1 (the rise in FP lesions on TC/ET). Topological quantification on the 1196 patients of the 5-fold CV (per-patient means, fragments = CC − 1 per class, 26-connectivity):

| Fragments / patient | Baseline | DistMap | **CC-Consensus** | Δ D−B | Δ F−D | F/D reduction |
|---|---|---|---|---|---|---|
| **NCR** | 79.7 | 93.3 | **31.3** | +13.6 | −61.9 | **−66 %** |
| **ED** | 28.9 | 35.3 | **17.0** | +6.4 | −18.3 | **−52 %** |
| **ET** | 2.15 | 2.33 | **1.57** | +0.18 | −0.76 | **−33 %** |

One-sided paired Wilcoxon signed-rank tests on the 1196 patients:

- **DistMap inflates fragments vs Baseline** on all three classes: NCR (p = 5.5 × $10^{-42}$), ED (p = 2.0 × $10^{-49}$), ET (p = 1.3 × $10^{-3}$). The artefact is statistically massive and systematic.
- **CC-Consensus reduces fragments vs DistMap**: NCR (p < $10^{-189}$), ED (p < $10^{-162}$), ET (p = 1.1 × $10^{-53}$).
- **CC-Consensus also reduces vs Baseline**: NCR (p < $10^{-188}$), ED (p < $10^{-144}$), ET (p = 1.4 × $10^{-30}$) — the post-hoc filter even corrects fragments inherited from Baseline when DistMap does not overlap them.

This effect **is invisible on Dice** (§5.3: mean Dice B / D / F = 0.9078 / 0.9088 / 0.9090, differences within noise) — a few-voxel fragment does not affect an overlap metric when the median tumor volume is ~90 000 voxels. This is precisely why prior literature had not reported the artefact: Dice is blind to topology.

![Figure 1 — Mean fragment count per patient (non-largest connected components, 26-connectivity, no size threshold) for each class × variant, on the 1196 patients of the 5-fold CV. DistMap inflates the NCR fragment count by +17 % over Baseline; the CC-consensus filter brings it down to 31.3 — a **66 %** reduction from DistMap (Wilcoxon p < $10^{-189}$).](figures/fragment_counts.png){width=90%}

**Qualitative illustrations on the six reference cases.** Figures 2–7 below show, for each of the six pinned patients (C1–C6) of the companion 3D viewer, the segmentations produced by GT / Baseline / DistMap / CC-Consensus, left sagittal view, tumor regions only (Brain masked for focus). Each figure illustrates one of the six behaviour modes identified in Appendix E.

**Note on 3D rendering (two pipelines).** The viewer offers a smooth mode and a voxel mode, each served by a distinct pipeline depending on the nature of the mesh.

*Voxel mode (raw truth).* *Greedy voxel meshing*: each voxel of the segmentation is turned into a cubic face merged with its coplanar neighbours. No interpolation, no smoothing — exactly what the model predicted at the voxel level. Used as ground-truth reference whenever one needs to count or precisely localise.

*Smooth mode (default for Figures 2–7), main meshes.* Pipeline `fill_holes + dilation + marching cubes`: the binary mask is first filled (`scipy.ndimage.binary_fill_holes` to remove internal cavities such as ventricles, sulci), dilated by one voxel (`binary_dilation`, 1 iteration) to soften the marching-cubes staircase, then marching-cubed at level 0.5. This is the pipeline used for the tumor-body and Brain meshes shown in Figures 2–7.

*Smooth mode, fragments and cavities.* For small components (< 4 voxels down to sub-voxel fragments), a separate **signed distance field** pipeline is used: 26-connectivity dilation to bridge voxels touching only by corner/edge, Euclidean inner and outer distance transforms (`scipy.ndimage.distance_transform_edt`) to build the signed distance field, cubic spline upsampling ×2 for sub-voxel resolution, then marching cubes at level iso = −0.3 (empirically calibrated for volume preservation). This pipeline is **necessary for small fragments** because naive marching cubes at 0.5 on a 1-voxel mask renders 1/6 of the true volume (×6 error) while the signed distance field preserves volume to ±5 % across all sizes.

*Shared property of both smooth pipelines.* They **preserve topology** (same connected components, same 26-connectivity count as voxel mode); the difference is purely cosmetic. Smooth is the default because the rendering is close to a clinical console; voxel mode remains one click away whenever voxel-exact inspection is needed.

\clearpage

![Figure 2 — Case **C1** (patient `BraTS-GLI-00048-001`): Baseline > DistMap. The GT contains only oedema (green); Baseline reproduces this pattern correctly. **DistMap hallucinates an NCR mass** (red) inside the oedema — typical of cases where the SDT pressure induces spurious components. **CC-Consensus removes this hallucination** because the NCR component in DistMap has no overlap with the Baseline prediction (veto), restoring the score almost completely (Dice avg 0.308 → 0.973).](figures/patient_C1_00048-001_4models.png){width=100%}

\clearpage

![Figure 3 — Case **C2** (patient `BraTS-GLI-01437-000`): DistMap > Baseline. Baseline under-segments the tumor (Dice 0.589) while DistMap captures the tumor extent correctly (Dice 0.923) thanks to its boundary sensitivity. **CC-Consensus matches DistMap** (0.923) because no hallucinated component needs to be removed — the filter preserves the higher-quality prediction when it is confirmed by Baseline.](figures/patient_C2_01437-000_4models.png){width=100%}

\clearpage

![Figure 4 — Case **C3** (patient `BraTS-GLI-01428-000`): B < F < D, filter pulled baseline-side. Baseline (0.618) and DistMap (0.656) bracket the CC-Consensus result (0.645). The filter removes some legitimate DistMap components that Baseline does not predict, mildly degrading the score toward Baseline. This is the most common damage mode (390 / 1196 patients, 32.6 %).](figures/patient_C3_01428-000_4models.png){width=100%}

\clearpage

![Figure 5 — Case **C4** (patient `BraTS-GLI-00017-001`): D < F < B, partial rescue. Baseline is excellent (0.991); DistMap is half-hallucinated (0.657). CC-Consensus deletes the spurious DistMap components and recovers part of Baseline's quality (0.890), but cannot reach Baseline because it starts from DistMap's voxels.](figures/patient_C4_00017-001_4models.png){width=100%}

\clearpage

![Figure 6 — Case **C5** (patient `BraTS-GLI-01530-000`): F < min(B, D), the filter breaks. Baseline = 0.241, DistMap = 0.541, CC-Consensus = 0.169. The filter **deletes a legitimate large DistMap component** because Baseline failed to find the tumor and cannot confirm it. 463 / 1196 patients (38.7 %) — the dominant failure mode of the filter, when Baseline and DistMap fail differently.](figures/patient_C5_01530-000_4models.png){width=100%}

\clearpage

![Figure 7 — Case **C6** (patient `BraTS-GLI-00540-000`): clean synergy. Both Baseline (0.785) and DistMap (0.795) are competent but neither is perfect. **CC-Consensus combines their strengths** to reach 0.869 — strictly above both parents. This is the target behaviour on 157/1196 patients (13.1 %) where the filter improves beyond its sources.](figures/patient_C6_00540-000_4models.png){width=100%}

### 5.3 The CC-consensus beats the baseline on the official metrics

This is the central conclusion of the paper. By keeping only the DistMap components corroborated by a second model (§3.3), the CC-consensus filter is **the only configuration evaluated here to significantly improve both official ranking metrics** over Baseline. Two veto models are evaluated: Baseline (`CC(D∩B)`) and the more-specific Kervadec head (`CC(D∩K)`, Paper 2); they are statistically equivalent on the primary endpoint (`CC(D∩K)` vs `CC(D∩B)`: p = 0.76 / 0.80 on lesion-wise Dice / HD95).

**Official primary endpoints — `CC(D∩B)` vs Baseline** (n = 1196, region-averaged, Holm):

- **Lesion-wise Dice**: Δ = +0.024, r = +0.27, **Holm p = 4.5 × $10^{-16}$** → significant.
- **Lesion-wise HD95**: Δ = −9.49 mm, r = +0.42, **Holm p = 5.7 × $10^{-26}$** → significant.

| Metric | Region | CC(D∩B) | Baseline | Δ | r | win/loss | p | p(Holm) |
|---|---|---|---|---|---|---|---|---|
| Lesion-wise Dice | WT | 0.854 | 0.812 | +0.042 | +0.10 | 577/617 | 0.004* | 0.008† |
|  | TC | 0.880 | 0.870 | +0.011 | +0.07 | 605/582 | 0.051 | 0.051 |
|  | ET | 0.817 | 0.798 | +0.019 | +0.15 | 618/540 | 6.2e-06* | 1.9e-05† |
|  | **avg** | **0.850** | **0.826** | **+0.024** | +0.27 | 680/514 | **4.5e-16\*** | -- |
| Lesion-wise HD95 (mm) | WT | 36.49 | 53.09 | -16.61 | +0.39 | 403/226 | 1.1e-17* | 3.2e-17† |
|  | TC | 20.68 | 24.68 | -4.00 | +0.20 | 238/178 | 4.4e-04* | 4.4e-04† |
|  | ET | 37.03 | 44.89 | -7.86 | +0.34 | 220/149 | 1.6e-08* | 3.2e-08† |
|  | **avg** | **31.40** | **40.89** | **-9.49** | +0.42 | 532/300 | **5.7e-26\*** | -- |
| Legacy Dice | WT | 0.935 | 0.935 | -0.000 | -0.12 | 507/687 | 3.9e-04* | 0.001† |
|  | TC | 0.918 | 0.918 | -0.000 | +0.01 | 589/598 | 0.739 | 1.000 |
|  | ET | 0.872 | 0.869 | +0.003 | +0.01 | 583/578 | 0.673 | 1.000 |
|  | **avg** | **0.908** | **0.907** | **+0.001** | -0.01 | 588/606 | **0.680** | -- |
| Legacy HD95 (mm) | WT | 5.67 | 5.79 | -0.12 | +0.06 | 311/269 | 0.181 | 0.543 |
|  | TC | 6.21 | 6.00 | +0.21 | +0.07 | 217/193 | 0.227 | 0.543 |
|  | ET | 11.59 | 11.62 | -0.03 | -0.02 | 168/170 | 0.780 | 0.780 |
|  | **avg** | **7.82** | **7.81** | **+0.02** | +0.05 | 419/374 | **0.270** | -- |

Δ = CC(D∩B) − Baseline. r = matched-pairs rank-biserial (+ favours CC(D∩B)). \* raw p < 0.05; † Holm-corrected p < 0.05. n = 1196.

The gain is **purely lesion-wise**: legacy region Dice stays neutral (avg Δ = +0.001, p = 0.68) and so does legacy HD95 (avg Δ = +0.02 mm, p = 0.27). The consensus does not change the segmentation quality of the main tumor — it **cleans up detection lesion by lesion**. Mechanically, it **removes ~41 % of Baseline's spurious lesions** (FP lesions avg 0.396 → 0.234, r = +0.85, p = 6.0 × $10^{-34}$) at a negligible recall cost (FN avg +0.003; sensitivity avg +0.001, p = 0.026):

| Metric | Region | CC(D∩B) | Baseline | Δ | r | win/loss | p | p(Holm) |
|---|---|---|---|---|---|---|---|---|
| FP lesions | WT | 0.146 | 0.337 | -0.191 | +0.79 | 152/22 | 8.3e-21* | 2.5e-20† |
|  | TC | 0.080 | 0.132 | -0.052 | +0.68 | 44/6 | 5.6e-06* | 5.6e-06† |
|  | ET | 0.474 | 0.718 | -0.244 | +0.86 | 100/9 | 4.2e-16* | 8.3e-16† |
|  | **avg** | **0.234** | **0.396** | **-0.162** | +0.85 | 237/29 | **6.0e-34\*** | -- |
| FN lesions | WT | 0.083 | 0.080 | +0.003 | -1.00 | 0/3 | 0.083 | 0.137 |
|  | TC | 0.040 | 0.037 | +0.003 | -1.00 | 0/4 | 0.046* | 0.137 |
|  | ET | 0.045 | 0.042 | +0.003 | -1.00 | 0/4 | 0.046* | 0.137 |
|  | **avg** | **0.056** | **0.053** | **+0.003** | -1.00 | 0/10 | 0.003* | -- |
| Sensitivity | WT | 0.929 | 0.929 | +0.000 | -0.02 | 570/624 | 0.469 | 0.469 |
|  | TC | 0.919 | 0.921 | -0.002 | -0.08 | 570/613 | 0.012* | 0.024† |
|  | ET | 0.881 | 0.877 | +0.004 | +0.20 | 676/474 | 8.2e-09* | 2.4e-08† |
|  | **avg** | **0.910** | **0.909** | **+0.001** | +0.07 | 635/559 | 0.026* | -- |
| Specificity | WT | 1.000 | 1.000 | -0.000 | -0.17 | 520/672 | 7.5e-07* | 1.5e-06† |
|  | TC | 1.000 | 1.000 | +0.000 | +0.02 | 606/570 | 0.587 | 0.587 |
|  | ET | 1.000 | 1.000 | -0.000 | -0.27 | 475/694 | 1.5e-15* | 4.6e-15† |
|  | **avg** | **1.000** | **1.000** | **-0.000** | -0.19 | 492/702 | 2.7e-08* | -- |

**Honesty on lesion-wise HD95.** A large part of the lesion-wise HD95 gain (−9.49 mm) comes from the official metric penalising each spurious lesion by **374 mm**: removing those lesions removes those penalties. We state this explicitly rather than implying a boundary-precision gain on true lesions; the lesion-wise Dice gain (+0.024), by contrast, is a genuine detection gain. The Kervadec veto is equivalent (`CC(D∩K)` vs Baseline: lesion-wise Dice +0.024, Holm p = 1.2 × $10^{-11}$; lesion-wise HD95 −9.95 mm, Holm p = 2.3 × $10^{-20}$) while preserving recall marginally better (FN ≈ +0.000 vs Baseline), consistent with its higher specificity (Paper 2).

**Complementary region-wise / per-class view — regional overlap and per-class distances.** At the level of regional overlap, this lesion-level cleanup is invisible by construction (regional Dice is dominated by the tumor volume, insensitive to small components), but it leaves a trace on the legacy per-class distances — notably NCR HD95, the class where fragments proliferate.

Aggregating fold-out predictions from all 5 folds (n = 1196), at the regional-overlap level:

| Strategy | Dice avg | Δ vs default CC-consensus |
|---|---|---|
| Baseline only | 0.9078 | −0.00115 |
| DistMap only | 0.9088 | −0.00020 |
| CC-Consensus (default rule) | 0.9090 | 0 (ref) |
| **Oracle patient-level** | 0.9131 | **+0.00412** |
| **Oracle per-class** | 0.9139 | **+0.00494** |

Per-patient case classification (noting $F$ for the CC-consensus output):

| Case | Count | % |
|---|---|---|
| Baseline beats DistMap (B > D) | 602 | 50.3 % |
| DistMap beats Baseline (D > B) | 593 | 49.6 % |
| Filter result between B and D | 559 | 46.7 % |
| **Filter < both (damaged)** | **463** | **38.7 %** |
| **Filter > both (synergy)** | **157** | **13.1 %** |

The CC-consensus filter damages the patient-level score in 38.7 % of cases against only 13.1 % of synergy. Per region, CC-Consensus wins (strictly) on only 2.7 % of patients for WT, **21.7 % for TC**, and 6.9 % for ET. The Dice benefit of the filter is therefore concentrated on TC; for WT and ET, Baseline-only or DistMap-only choices already dominate.

**Per-class boundary quality HD95 (diagnostic).** Complementing the official *legacy* region HD95 (table above, WT/TC/ET all n.s.), we report 95th-percentile Hausdorff distances on the **individual classes** (NCR, ED) where fragments live — all computed with the standard `medpy` implementation (`medpy.metric.binary.hd95`), as for every HD95 in this work (n varies per row depending on finite-HD95 patients for that class):

| Region / class | Composition | Baseline | DistMap | CC-Consensus | Δ CC-Cons vs DistMap |
|---|---|---|---|---|---|
| WT | {1, 2, 3} | 3.99 mm | 3.99 mm | 4.03 mm | +0.05 mm, n.s. |
| TC | {1, 3} | 3.14 mm | 2.89 mm | 2.96 mm | +0.07 mm, n.s. |
| ET | {3} | 2.64 mm | 2.59 mm | 2.68 mm | +0.09 mm, n.s. |
| **NCR** | {1} | 4.89 mm | 4.86 mm | **4.48 mm** | **−0.38 mm, p = 5.7 × $10^{-14}$** |
| ED | {2} | 4.25 mm | 4.33 mm | 4.21 mm | −0.12 mm, n.s. (p = 0.82) |

Paired signed-rank Wilcoxon, one-sided hypothesis HD95(CC-Consensus) < HD95(DistMap). n = 1160 for WT/TC/ET (patients with finite HD95 on all 3 nested regions), 1153 for NCR, 1193 for ED.

**The signal is on NCR**: CC-Consensus reduces NCR HD95 by 0.38 mm (p = 5.7 × $10^{-14}$) — direct quantitative confirmation that fragment deletion improves boundary quality on the class where they proliferate (NCR: ×1.5 more DistMap fragments than Baseline, cf. §5.2). The gain **does not propagate** to the nested regions: WT, TC and ET HD95 are unchanged (all n.s.), because the 95th-percentile Hausdorff distance on the large nested regions is dominated by the main tumor body and barely moves when small NCR fragments are removed. On ED, the fragment reduction (−61 %) likewise does not translate into a significant HD95 gain — oedema has intrinsic boundary variability that dominates the outliers introduced by fragments.

CC-consensus thus delivers a quantitatively measurable gain on **NCR HD95 specifically** — the per-class metric on the region where fragments proliferate — where overlap Dice remains insensitive. Clinically, NCR is precisely the region where spurious fragments may mislead a radiotherapist on the extent of tumor necrosis.

\clearpage

![Figure 8 — 1196 validation patients plotted in the model-disagreement plane: x = Dice(DistMap) − Dice(Baseline) (positive means DistMap wins at the patient level), y = Dice(CC-Cons.) − max(Dice(B), Dice(D)) (negative means the CC-consensus filter is worse than either model alone). The *red* C5 cloud below y = 0 collects 38.7 % of patients where the filter damages the score; the *green* C6 points above y = 0 represent only 13.1 %. This visual asymmetry is the central empirical observation of the paper.](figures/case_scatter.png){width=100%}

### 5.4 The hard-label ceiling is saturated (in regional-overlap Dice)

This analysis concerns specifically the **regional-overlap Dice**: it **does not bound** the official lesion-wise gain established in §5.3 (which rewards the removal of spurious lesions, invisible to regional Dice, and which the consensus already achieves). The gap between default CC-consensus and the per-class oracle (+0.005 regional Dice avg) upper-bounds the gain of any patient- or region-level selection policy from the three predictions {B, D, F}. We evaluate three families of policies in 5-fold CV (size-adaptive threshold over τ $\in$ {20, 50, 100, 200, 500, ∞} voxels; meta-classifiers RF/LR/GBM × patient/region on 31 features; one-feature rule via exhaustive search); **none robustly beats the default CC-consensus**. The one-feature rule, attractive on all-data fit (+0.00119), collapses in 5-fold CV (−0.00096): the best feature and threshold change across folds (TC: 4 distinct features over 5 folds; ET: 4 distinct features). A per-region RandomForest reaches 50 %, 43 %, 51 % argmax accuracy (vs 33 % random), confirming the presence of signal — but when the classifier is wrong, it picks a strictly worse model, yielding a net negative outcome.

The full detail — table of the 7 evaluated policies, RF importances per region, classification of the adaptive sweep, per-fold partition of the one-feature rule — is in **Appendix B**. The hard-label ceiling is essentially reached; closing the gap to the oracle requires voxel-level probabilistic voting or architectural diversity (§6.3).

### 5.5 Position relative to BraTS 2023 GLI winners

CC-consensus reaches Dice avg = 0.909 (WT 0.935, TC 0.919, ET 0.873) on 1196-patient 5-fold CV with a single-model setup (no multi-fold ensemble, no TTA, single architecture). This is within one percentage point of the published BraTS 2023 GLI winner range on private test set (0.87–0.89 Dice avg; Ferreira *et al.* 2024). Two caveats apply to the direct comparison: (i) different evaluation set (5-fold CV on train + val pool vs private test set, typical 1–2 pp gap to the disadvantage of the test set); (ii) the Dice = 1 on empty-region convention (nnU-Net / MONAI) inflates ET by ~0.003 relative to the lesion-wise convention used by the challenge (32/1196 patients with empty ET in GT).

We do not claim a new state-of-the-art; the CC-consensus filter is **orthogonal to ensembling** — fragment reduction is a gain that stacks with classical multi-fold / TTA tricks without duplicating them.

### 5.6 Robustness to the training seed (3 seeds, fold 0)

§5.1 uses seed 42 for all folds. To estimate inter-seed variance and verify that the non-significance is not an initialisation artefact, three independent trainings (seeds 1, 2, 3) are run for Baseline and DistMap (λ=0.1, best λ per Appendix A) on fold 0 (n≈240 patients), 300 epochs each.

**Fold-0 validation Dice (nnU-Net, 240 patients):**

| Config | Seed 1 | Seed 2 | Seed 3 | Mean ± σ |
|---|---|---|---|---|
| Baseline | 0.9078 | 0.9066 | 0.9078 | **0.9074 ± 0.0007** |
| DistMap (λ=0.1) | 0.9074 | 0.9043 | 0.9021 | **0.9046 ± 0.0027** |
| Δ (B − D) | +0.04 pp | +0.23 pp | +0.57 pp | +0.28 pp |

Paired t-test (n=3 seeds): t=1.83, p=0.21 — not significant. The non-significance found in 5-fold CV (§5.1, Δ=+0.09 pp, p>0.25) is confirmed across the three seeds: Baseline slightly leads DistMap in all three cases, with no gap reaching 1 pp or the significance threshold.

Two observations:

- **DistMap instability (×4).** DistMap's inter-seed variance (σ=0.0027) is 4× that of Baseline (σ=0.0007). The auxiliary SDT loss makes training markedly more sensitive to initialisation. This explains the apparent DistMap advantage seen at the reference seed (42) in Appendix A (+0.13 pp at λ=0.1): it is an initialisation fluctuation, not a robust signal.
- **Monotone baseline advantage.** The gap Δ(B−D) grows from +0.04 pp (seed 1) to +0.57 pp (seed 3). With n=3 no causal trend can be established; the observation is consistent with DistMap's higher random variance.

**Official BraTS-2023 metrics and CC-consensus (D$\cap$B) per seed.** Full evaluation on the 3×240 patients (720 valid pairs) with the official *BraTS-2023-Metrics* (Legacy Dice, LW Dice, HD95), on predictions verified free of residual fragments — the lesion-wise baseline is therefore identical to the one reported in Paper 2 on the same predictions. On Legacy Dice, neither DistMap nor the consensus differs from Baseline (p > 0.35 Wilcoxon throughout). The benefit concentrates on lesion-wise detection of the whole tumor: the CC-consensus filter significantly improves **LW Dice WT** (0.810 → 0.853, +4.28 pp, p < $10^{-4}$ Wilcoxon) and **LW HD95 WT** (54.5 → 37.3 mm, −17.2 mm, p < $10^{-4}$), at no cost on the volumetric Dice. DistMap alone already partially improves **LW Dice WT** (+1.54 pp, p = 0.041 Wilcoxon), with the consensus amplifying the gain.

**Table A — Baseline vs DistMap (λ=0.1), official metrics, fold 0, 3 seeds**

| Metric | Region | Baseline (mean±σ) | DistMap (mean±σ) | Δ | p t-test | p Wilcoxon |
|---|---|---|---|---|---|---|
| Legacy Dice | WT | 0.9361 ± 0.0006 | 0.9359 ± 0.0012 | −0.02 pp | 0.89 | 0.44 |
| Legacy Dice | TC | 0.9208 ± 0.0006 | 0.9170 ± 0.0040 | −0.38 pp | 0.35 | 0.36 |
| Legacy Dice | ET | 0.8668 ± 0.0029 | 0.8616 ± 0.0017 | −0.53 pp | 0.12 | 0.64 |
| LW Dice | WT | 0.8103 ± 0.0080 | 0.8257 ± 0.0081 | +1.54 pp | 0.27 | **0.041** |
| LW Dice | TC | 0.8670 ± 0.0067 | 0.8649 ± 0.0069 | −0.21 pp | 0.75 | 0.54 |
| LW Dice | ET | 0.8071 ± 0.0109 | 0.7997 ± 0.0074 | −0.74 pp | 0.32 | 0.97 |
| Legacy HD95 | WT | 6.42 ± 0.28 mm | 6.04 ± 0.47 mm | −0.38 mm | 0.35 | 0.55 |
| Legacy HD95 | TC | 5.95 ± 0.90 mm | 6.02 ± 0.65 mm | +0.07 mm | 0.95 | 0.96 |
| Legacy HD95 | ET | 13.85 ± 1.33 mm | 15.41 ± 0.64 mm | +1.56 mm | 0.19 | 0.98 |
| LW HD95 | WT | 54.52 ± 2.84 mm | 48.04 ± 3.45 mm | −6.48 mm | 0.24 | 0.071 |
| LW HD95 | TC | 26.82 ± 2.73 mm | 26.12 ± 2.28 mm | −0.70 mm | 0.86 | 0.61 |
| LW HD95 | ET | 41.59 ± 4.68 mm | 44.26 ± 2.40 mm | +2.67 mm | 0.44 | 1.00 |

Across the 12 Baseline/DistMap comparisons, only **LW Dice WT** crosses the Wilcoxon threshold (+1.54 pp, p = 0.041); the other eleven remain non-significant (p > 0.07). DistMap thus already slightly shifts whole-tumor lesion-wise detection, but this signal alone is fragile (not significant under the paired t-test, p = 0.27). The TC instability seen on the nnU-Net Dice (σ×4) is reflected here by a σ DistMap×6 on Legacy Dice TC.

**Table B — CC-consensus (D$\cap$B) vs Baseline, official metrics, fold 0, 3 seeds**

| Metric | Region | Baseline (mean±σ) | CC(D$\cap$B) (mean±σ) | Δ | p t-test | p Wilcoxon |
|---|---|---|---|---|---|---|
| Legacy Dice | WT | 0.9361 ± 0.0006 | 0.9359 ± 0.0012 | −0.02 pp | 0.90 | 0.41 |
| Legacy Dice | TC | 0.9208 ± 0.0006 | 0.9184 ± 0.0025 | −0.24 pp | 0.39 | 0.57 |
| Legacy Dice | ET | 0.8668 ± 0.0029 | 0.8629 ± 0.0008 | −0.39 pp | 0.13 | 0.91 |
| LW Dice | WT | 0.8103 ± 0.0080 | **0.8531 ± 0.0041** | **+4.28 pp** | **0.017** | **5.5×$10^{-5}$** |
| LW Dice | TC | 0.8670 ± 0.0067 | 0.8668 ± 0.0034 | −0.02 pp | 0.97 | 0.85 |
| LW Dice | ET | 0.8071 ± 0.0109 | 0.8018 ± 0.0047 | −0.54 pp | 0.42 | 0.69 |
| Legacy HD95 | WT | 6.42 ± 0.28 mm | 6.48 ± 0.05 mm | +0.06 mm | 0.81 | 0.82 |
| Legacy HD95 | TC | 5.95 ± 0.90 mm | 5.50 ± 0.12 mm | −0.45 mm | 0.56 | 0.67 |
| Legacy HD95 | ET | 13.85 ± 1.33 mm | 14.89 ± 0.74 mm | +1.04 mm | 0.14 | 0.60 |
| LW HD95 | WT | 54.52 ± 2.84 mm | **37.31 ± 2.18 mm** | **−17.21 mm** | **0.015** | **6.0×$10^{-5}$** |
| LW HD95 | TC | 26.82 ± 2.73 mm | 25.42 ± 1.92 mm | −1.39 mm | 0.71 | 0.63 |
| LW HD95 | ET | 41.59 ± 4.68 mm | 43.48 ± 1.32 mm | +1.89 mm | 0.57 | 0.87 |

On multi-seed fold 0, the CC-consensus filter reproduces the lesion-wise gains already seen in 5-fold CV (§5.3) and concentrates them on the whole tumor: a significant and robust improvement in **LW Dice WT** (+4.28 pp) and **LW HD95 WT** (−17.2 mm), with p < $10^{-4}$ under Wilcoxon and p < 0.02 under the paired t-test on n=3 seeds, at no cost on Legacy Dice (Δ < 0.1 pp, non-significant). **No trend is observed on TC or ET** (|Δ| < 1.4 pp and < 1.4 mm, p > 0.6): the benefit is purely WT.

This framing is deliberate, and it is both more honest and more clinically coherent. More statistically honest: an earlier version of this analysis reported a "trend" toward improvement on TC, but it rested on an evaluation in which residual spurious fragments artificially degraded the lesion-wise baseline (LW Dice WT 0.78 instead of 0.81); on predictions verified free of fragments this TC trend vanishes, and the baseline coincides exactly with the one in Paper 2. More clinically coherent: the consensus benefit is a **cleanup of detection false positives** — the removal of false small lesions — not a gain in volumetric precision (Legacy Dice is unchanged). It is therefore expected to surface precisely where such fragments abound, on the whole tumor (WT), the largest region and the most prone to boundary components, and to be absent on the compact regions (TC, ET). The consensus improves lesion-wise detection reliability without altering the segmentation quality of the main tumor mass.

---

## 6. Discussion

### 6.1 Why DistMap creates fragments

Plausible mechanism — not demonstrated: the SDT pressure sensitises the network to small *boundary-like* signals in transition tissues (oedema–white matter interfaces, post-surgical cavities, heterogeneous NCR), producing high-SDT-response voxels that occasionally survive the argmax as isolated blobs. This hypothesis is consistent with two observations: the increase in fragment count is concentrated on NCR and ED (regions with the longest and most irregular boundaries) and is much smaller on ET, whose gadolinium enhancement provides sharper boundary contrast. Three direct controls (λ ablation × fragment count, SDT response-map visualisation at fragment locations, distance-bin vs MSE) are described in **Appendix C** and deferred to future work; the primary contribution here is the characterisation and post-hoc mitigation of the artefact, not its mechanistic explanation.

### 6.2 Why the CC-consensus filter works

Baseline does not share the SDT pressure and therefore does not produce the same class of boundary-spurious blobs. Requiring overlap with Baseline for a DistMap CC to survive is equivalent to a **consensus test** on a perturbation-disjoint second detector. This is a principled application of the classical "agreement of independent classifiers" idea, adapted to connected components rather than voxels.

The rule has two desirable properties:

* **Asymmetric by design.** The rule starts from DistMap (superior boundary quality) and uses Baseline only as a veto. The better boundary is preserved wherever the veto does not fire.
* **Parameter-free.** No threshold, no learnable weight — the structure of CC connectivity is the only hyper-parameter (26-connectivity).

### 6.3 Why the oracle cannot be reached

Two same-family models (identical architecture, data, augmentations, loss family, differing only by the SDT auxiliary) produce too little diversity for a 3-way classification "B vs D vs F" to be reliably learned from shape features alone. Both models live in the same decision neighbourhood; their disagreements are dominated by high-frequency spatial noise that global morphology does not capture.

Closing the +0.005 Dice gap almost certainly requires one of:

* **Voxel-level probabilistic voting.** Exporting softmax outputs (not just argmax labels) and fusing at the voxel level breaks the hard-vote ceiling. A weighted average $\alpha \cdot \mathbf{p}_B + (1-\alpha) \cdot \mathbf{p}_D$ with α learned per region is a natural next step.
* **Architectural diversity.** Adding a non-MedNeXt backbone (nnU-Net vanilla, Swin-UNETR) increases oracle headroom dramatically, as the BraTS 2023 winners routinely demonstrate.
* **Multi-seed / multi-fold ensembling.** The classical recipe gains +0.5 to +2 Dice points on BraTS; fully compatible with — and orthogonal to — the CC-consensus rule proposed here.

### 6.4 Limitations

* **Single backbone.** All experiments use MedNeXt-B; generalisation to Swin-UNETR / nnU-Net vanilla / Restormer would strengthen the conclusion.
* **No probabilistic fusion baseline.** Only hard-label filtering is reported because softmax outputs were not persisted at inference time. The ceiling analysis explicitly addresses this gap for the hard-label setting.
* **Single-model-per-patient setup.** The CC-consensus filter reaches Dice avg 0.909 on 1196-patient 5-fold CV without multi-fold ensembling, TTA, or multi-architecture voting. Adding these standard tricks would likely push the score into, or above, the BraTS 2023 GLI winner range, but this would be a parallel-compute contribution orthogonal to the fragment-characterisation question this paper addresses.
* **Dice convention slightly inflates ET.** Empty-GT ET patients (2.7 % of BraTS 2023 GLI, non-enhancing cases, 32/1196 verified) are scored Dice = 1.0 under the nnU-Net / MONAI convention, which slightly inflates the ET regional mean (−0.003 only under the lesion-wise convention). The relative comparisons between Baseline, DistMap and CC-Consensus are not affected (all three use the same convention), but absolute ET Dice is not directly comparable to challenge leaderboards using the lesion-wise convention (see §5.5).
* **BraTS 2023 GLI only.** Extension to BraTS-MET (metastases) and BraTS-PED (paediatric) is left to future work; we expect the fragment bias to be more severe on metastases (multi-lesion pattern).
* **No small tumors in the dataset.** The minimum WT volume on BraTS 2023 GLI is 2808 voxels, median ~89 500 voxels. The topological fragment definition adopted in §4.2 (CC − 1 per class, no size threshold) is **intrinsically size-robust** and requires no recalibration for smaller tumors. However, **the pipeline evaluated here has not been tested on the clinically critical regime of small tumors** (a few hundred voxels), where early detection has major prognostic impact. Absolute morphology features (`vol_*`, `nb_cc_*`) would be out-of-distribution in that regime and would need re-examination before clinical use; the topological and relative features (`ratio_ET_WT`, `frac_small_cc_*`, sphericity, elongation) are size-robust by construction.
* **No explicit cross-scanner harmonization.** BraTS aggregates multiple institutions, scanners and field strengths; the official pipeline standardizes geometry but applies no cross-scanner intensity harmonization, and the per-patient z-scoring above aligns first- and second-order moments without removing scanner-specific effects (residual bias field, contrast). We apply neither N4 bias-field correction nor ComBat: N4 has not been shown to benefit deep-learning tumor segmentation — intensity-equalisation preprocessing is negligible or slightly detrimental, only voxel-spacing unification (already provided by BraTS) matters [Kondrateva et al. 2024] — and ComBat is inapplicable here because the DICOM→NIfTI conversion strips scanner metadata (no batch labels). This confound is shared across all compared methods (identical folds), so it does not bias the relative comparison; it only bounds absolute cross-site generalisation.

---

## 7. Conclusion

Under the complete set of official BraTS-2023 metrics, at convergence (300 ep, 5-fold CV, n = 1196), an auxiliary SDT head on MedNeXt-B / nnU-Net v2 is **null on the official ranking metrics** (lesion-wise Dice and HD95, pre-specified primary endpoints, Holm p = 1.0) and **Dice-neutral on the legacy region overlap**; the Dice gain reported at a reduced training budget does not survive to convergence. Its only robust effect is a **recall-oriented shift** — higher sensitivity and fewer missed lesions (p = 2 × $10^{-9}$), at a specificity cost (p = 1.2 × $10^{-14}$) whose topological signature is the appearance of small spurious connected components ("fragments", ×1.5 on NCR). An independent multi-seed analysis (3 seeds × fold 0, §5.6) confirms the non-significance and reveals a DistMap training instability four times that of Baseline (×4 inter-seed σ).

Read as an operating point and combined through a **parameter-free connected-component consensus filter** — which vetoes the DistMap components that a second model does not corroborate — this recall becomes a **system that beats the baseline**: it is the **only configuration evaluated to significantly improve both official ranking metrics** (lesion-wise Dice +0.024, Holm p = 4.5 × $10^{-16}$; lesion-wise HD95 −9.49 mm, Holm p = 5.7 × $10^{-26}$), removing ~41 % of the spurious lesions at a negligible recall cost, at no cost on overlap Dice. Part of the HD95 gain owes to the official metric's 374 mm penalty per spurious lesion; the lesion-wise Dice gain, by contrast, is a genuine detection cleanup. Complementarily, the filter reduces legacy NCR HD95 (4.86 → 4.48 mm, p = 5.7 × $10^{-14}$) by eliminating 66 % of NCR fragments.

The **regional-overlap** gain, by contrast, remains capped (the per-class oracle is only +0.005 Dice avg above the default, and no 31-feature meta-selector beats it in CV): closing this gap on the regional Dice motivates **voxel-level probabilistic voting** or **training-time fragment-aware losses** (future work), rather than further post-hoc engineering. The transversal lesson: an auxiliary loss should be reported on **all** official metrics, read by its mechanism (here, the recall–precision axis it moves), and exploited — not as a Dice booster, but as an operating point feeding a consensus.

---

## 8. Perspectives

**Training-time fragment-aware loss (future work).** The hypothesis in §6.1 suggests fragments are a gradient effect. A training-time penalty term counting predicted connected components on the argmax of each mini-batch — and penalising small isolated blobs — should push the network not to instantiate them, making the post-hoc CC-consensus filter unnecessary. This is the direction of this future work.

**Dataset extensions.** BraTS-MET (metastases, multi-lesion pattern) is the most informative next test: DistMap fragments should be more severe there, and the CC-consensus filter should benefit more. BraTS-PED (paediatric) would test generalisation across demographic shifts.

---

## Acknowledgments

The author thanks **Stanislas Larnier** for methodological guidance, feedback on the framing of research questions, and careful reviews of successive drafts of this paper.

---

## Appendix A — Calibration of λ (auxiliary SDT loss)

At epoch 0 with a random-initialised network (seed 42), we measure $|\mathcal{L}_{\mathrm{Dice+CE}}| = 0{.}57$ and $\mathcal{L}_{\mathrm{MSE}}^{\mathrm{SDT}} = 0{.}12$, yielding a "gradient-balanced" λ = 4.70.

A static ablation over λ $\in$ {0, 0.1, 0.5, 1, 2, 5, 6, 7, 8, 9, 10} (100 epochs, fold 0, seed 42) produces Dice-avg scores all within a 0.5 pp window:

| λ | Dice avg | Δ vs Baseline |
|---|---|---|
| 0 (Baseline) | 0.9064 | 0 |
| 0.1 | 0.9077 | +0.0013 |
| 0.5 | 0.9070 | +0.0006 |
| 1.0 | 0.9067 | +0.0003 |
| 2.0 | 0.9060 | −0.0004 |
| 5.0 | 0.9105 | +0.0041 |
| 9.0 | 0.9104 | +0.0040 |

On this single fold and without per-patient significance testing, no λ clearly outperforms the baseline. This is consistent with the non-significance of the DistMap gain observed in 5-fold CV on 1196 patients (§5.1). Default training reported in the body uses λ = 1 (close to published heuristics and to the gradient-balanced calibration ÷ 5).

A dynamic weighting scheme — DWA (Dynamic Weight Average, Liu CVPR 2019) — that tracks the relative learning rates of the Dice+CE and SDT heads over training is a natural next direction: if a regime exists where SDT genuinely contributes without saturating, a static sweep cannot find it.

---

## Appendix B — Detailed hard-label ceiling study

The gap between default CC-consensus and the per-class oracle (+0.005 Dice avg) is the maximum gain of any per-region selection policy. We evaluate progressively richer policies:

| Policy | Dice avg | Δ vs CC-consensus |
|---|---|---|
| Best size-adaptive threshold (τ = 200 vx) | 0.90909 | +0.00012 |
| 27 fixed per-region rules — best = D/F/F | 0.90935 | +0.00038 |
| Meta-LR (31 features, patient-level) | 0.90940 | +0.00043 |
| Meta-RF (31 features, per-region) | 0.90807 | **−0.00090** |
| Meta-LR (31 features, per-region) | 0.90844 | −0.00053 |
| Meta-GBM (31 features, per-region) | 0.90833 | −0.00064 |
| 1-feature decision rule (all-data fit) | 0.91016 | +0.00119 |
| **1-feature decision rule (5-fold CV)** | **0.90801** | **−0.00096** |

The one-feature rule, attractive on all-data fit (+0.00119), collapses in 5-fold CV (−0.00096): the best feature and threshold change across folds (TC: 4 distinct features over 5 folds; ET: 4 distinct features). Four different "best" features over five folds for TC alone clearly indicate that the signal is not robust enough to trust.

A RandomForest trained per region reaches 50 %, 43 % and 51 % argmax accuracy (WT, TC, ET) versus 33 % random, confirming the presence of signal in the features — yet when the classifier is wrong it picks a strictly worse model, yielding a net negative outcome.

Feature importance (full-data RF, top-3 per region) supports the narrative: for ET, `frac_removed_distmap_ET` (0.13) and `max_orphan_cc_ET` (0.09) — both inter-model agreement features — dominate. The signal is real; it is simply not strong enough to survive CV.

\clearpage

![Figure A1 — Top-8 feature importances of a RandomForest classifier trained to predict argmax(Baseline, DistMap, CC-Consensus) for each region (WT / TC / ET). Blue bars: morphology features from GT (20). Red bars: inter-model agreement features (11). For ET specifically, the 3 top importances — `frac_removed_distmap_ET`, `max_orphan_cc_ET`, `n_no_overlap_distmap_ET` — are all agreement features, confirming that the decision "trust the CC-consensus filter on ET or not" is driven by how much DistMap over-predicts relative to Baseline.](figures/rf_importance.png){width=100%}

---

## Appendix C — Mechanism hypothesis: deferred controls

The hypothesis in §6.1 (the SDT pressure produces high-response voxels at ambiguous interfaces, which occasionally survive the argmax) remains at this stage a **working hypothesis, not demonstrated**. The following three direct controls are all feasible on the existing checkpoints and are deferred to future work:

1. **λ ablation crossed with fragment count.** Verify that the mean number of fragments per patient grows monotonically with λ. Monotonic growth would confirm the causal link between SDT pressure and artefact; absence of monotonicity would suggest that optimisation noise dominates.
2. **SDT response-map visualisation at fragment locations.** For a sample of patients, overlay the tanh output of the auxiliary head and the fragment map; fragments should coincide with high-SDT-response voxels close to a tissue interface.
3. **Distance bins vs MSE.** Replace the `Conv3D(32 → 3) + tanh + MSE` head with a distance-bin classification head (e.g. 16 equi-probable bins in [−1, 1]). If the artefact disappears or substantially decreases, it is specific to the MSE-SDT formulation and not to distance supervision in general.

Running these three controls would move §6.1 from "working hypothesis" to "demonstrated mechanism".

---

## Appendix D — Runtime and reproducibility

All code, the 20 + 11 pre-extracted features, per-patient model scores, oracle / case-classification CSVs, threshold-sweep results and meta-selector outputs are available in the companion repository [github.com/guillaume-cassez/brats-moe-distmap-fusion-1](https://github.com/guillaume-cassez/brats-moe-distmap-fusion-1) and archived on Zenodo (concept DOI [10.5281/zenodo.19695263](https://doi.org/10.5281/zenodo.19695263)).

The trained model checkpoints (5 cross-validation folds for each variant, weights as `safetensors`, no optimiser state) are released on the Hugging Face Hub :

- Baseline : [huggingface.co/GuillaumeCassez/mednext-baseline-brats2023gli](https://huggingface.co/GuillaumeCassez/mednext-baseline-brats2023gli)
- DistMap (auxiliary SDT) : [huggingface.co/GuillaumeCassez/mednext-distmap-brats2023gli](https://huggingface.co/GuillaumeCassez/mednext-distmap-brats2023gli)

Per-patient extraction of the 31 features on the 1196 predictions runs in **~10 min** on 14 P-core threads (`taskset -c 0-13`) of an i7-14700K; the full meta-classifier sweep (4 families × 5 folds × 31-dim input) in ~2 min on the same host. **Training time per fold: ~13 h 30 min for 300 epochs** on a single RTX PRO 6000 Blackwell (96 GB), Baseline and DistMap variants at equivalent duration (the auxiliary SDT regression head adds < 1 % GPU overhead at 300 ep).

---

## Appendix E — The six demonstration patients

Six patients are highlighted to span the six model-ordering cases, used both for the figures and as pinned anchors in the companion 3D viewer. In the table, $F$ denotes the CC-consensus filter output. Patient identifiers are shown without the `BraTS-GLI-` prefix for compactness (the dataset prefixes them systematically).

```{=latex}
\begin{center}
\renewcommand{\arraystretch}{1.3}
\footnotesize
\setlength{\tabcolsep}{2pt}
\begin{tabular}{|p{3.4cm}|c|c|c|c|c|p{7.7cm}|}
\hline
\textbf{Tag} & \textbf{Patient} & \textbf{Fold} & \textbf{B} & \textbf{D} & \textbf{F} & \textbf{Take-away} \\
\hline
C1 (baseline $>$ distmap) & 00048-001 & 1 & 0.983 & 0.308 & 0.973 & DistMap hallucinates TC/ET on an oedema-only case \\
\hline
C2 (distmap $>$ baseline) & 01437-000 & 2 & 0.589 & 0.923 & 0.923 & DistMap rescues an under-segmenting Baseline \\
\hline
C3 (B $<$ F $<$ D) & 01428-000 & 1 & 0.618 & 0.656 & 0.645 & Filter output sits between the two, pulled baseline-side \\
\hline
C4 (D $<$ F $<$ B) & 00017-001 & 0 & 0.991 & 0.657 & 0.890 & Filter output rescues DistMap via consensus \\
\hline
C5 (filter worst) & 01530-000 & 1 & 0.241 & 0.541 & 0.169 & Filter deletes a legitimate large DistMap CC \\
\hline
C6 (filter best) & 00540-000 & 1 & 0.785 & 0.795 & 0.869 & Clean synergy \\
\hline
\end{tabular}
\end{center}
```

---

## References

* Isensee F., Jaeger P. F., Kohl S. A. A., Petersen J., Maier-Hein K. H. (2021). *nnU-Net: a self-configuring method for deep learning-based biomedical image segmentation*. **Nature Methods** 18, 203–211. DOI: 10.1038/s41592-020-01008-z.
* Roy S., Koehler G., Ulrich C., Baumgartner M., Petersen J., Isensee F., Jaeger P. F., Maier-Hein K. H. (2023). *MedNeXt: transformer-driven scaling of ConvNets for medical image segmentation*. **MICCAI 2023**, LNCS 14222, 405–415. DOI: 10.1007/978-3-031-43901-8_39.
* Ma J. (2020). *Distance transform maps improve semantic segmentation of medical images*. **Medical Imaging with Deep Learning (MIDL) 2020**, short paper track.
* Xue Y., Tang H., Qiao Z., Gong G., Yin Y., Qian Z., Huang C., Fan W., Huang X. (2020). *Shape-aware organ segmentation by predicting signed distance maps*. **AAAI 2020**, 34(07), 12565–12572. DOI: 10.1609/aaai.v34i07.6946.
* Karimi D., Salcudean S. E. (2020). *Reducing the Hausdorff distance in medical image segmentation with convolutional neural networks*. **IEEE Transactions on Medical Imaging** 39(2), 499–513. DOI: 10.1109/TMI.2019.2930068. arXiv:1904.10030.
* Huang H., Yang G., Zhang W., Xu X., Yang W., Jiang W., Lai X. (2021). *A deep multi-task learning framework for brain tumor segmentation*. **Frontiers in Oncology** 11, 690244. DOI: 10.3389/fonc.2021.690244.
* Dang T., Nguyen H. H., Tiulpin A. (2024). *SiNGR: Brain tumor segmentation via signed normalized geodesic transform regression*. **MICCAI 2024**. arXiv:2405.16813.
* Kondrateva E., Druzhinina P., Dalechina A., Zolotova S., Golanov A., Shirokikh B., Belyaev M., Kurmukov A. (2024). *Negligible effect of brain MRI data preprocessing for tumor segmentation*. **Biomedical Signal Processing and Control** 96:106599. arXiv:2204.05278.
* Ferreira A., Solak N., Li J., Dammann P., Kleesiek J., Alves V., Egger J. (2024). *How we won BraTS 2023 adult glioma challenge? Just faking it! Enhanced synthetic data augmentation and model ensemble for brain tumour segmentation*. **arXiv:2402.17317**.
* Liu S., Johns E., Davison A. J. (2019). *End-to-end multi-task learning with attention* (DWA — Dynamic Weight Average). **CVPR 2019**, 1871–1880. DOI: 10.1109/CVPR.2019.00197.
* Baid U., Ghodasara S., Mohan S., Bilello M., Calabrese E., Colak E., *et al.* (2021). *The RSNA-ASNR-MICCAI BraTS 2021 benchmark on brain tumor segmentation and radiogenomic classification*. **arXiv:2107.02314**.
* Menze B. H., Jakab A., Bauer S., *et al.* (2015). *The multimodal brain tumor image segmentation benchmark (BRATS)*. **IEEE TMI** 34(10), 1993–2024. DOI: 10.1109/TMI.2014.2377694.
* Saluja R., *et al.* (2023). *BraTS-2023-Metrics: Official BraTS 2023 Segmentation Performance Metrics*. [github.com/rachitsaluja/BraTS-2023-Metrics](https://github.com/rachitsaluja/BraTS-2023-Metrics).
* Nikolov S., Blackwell S., Zverovitch A., Mendes R., Livne M., De Fauw J., *et al.* (2021). *Clinically applicable segmentation of head and neck anatomy for radiotherapy: deep learning algorithm development and validation study*. **Journal of Medical Internet Research** 23(7), e26151. DOI: 10.2196/26151.
