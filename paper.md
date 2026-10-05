```{=latex}
\clearpage
```

# Two Models That Agree Beat the Best of Them Alone: Parameter-Free Connected-Component Consensus That Beats the Baseline under the Official BraTS-2023 Metrics

> **Editorial revision of 2026-10-05 (v12) — dead links, false bibliographic entry.** Three
> `guillaume-cassez.fr` paths under `/brats/` returned **403** (measured 2026-10-05) and now
> resolve; the bibtex no longer cites a nonexistent arXiv preprint. No number changes: see
> `README.md`.
>
> **Editorial revision of 2026-10-05 — repository links and one corrected count.**
> The two Hugging Face model cards cited here now resolve to the `guillaume-cassez`
> namespace: the namespace they used to live under has been withdrawn, and its models were
> migrated with their content verified file by file. In the dataset-provenance note
> (`analysis/DATASET_EXCLUSIONS.md`), the patient-level exclusion is now stated to have
> caught **50** cases of the unified set, where v10 printed **0**. That 0 was not a
> measurement: it came from a generator that silently fell back to an empty count when the
> dataset volume was not mounted, and the CSV shipped inside this very archive already
> listed those 50 cases (`entree_exacte = non`). The generator now derives the figure from
> the shipped measurement *and* from a scan of the unified dataset, and refuses to write
> anything when the two disagree or when the scan is impossible. No metric, figure, table
> or conclusion of this manuscript changes: the 1251 → 1196 study set, the 55 dropped cases
> and every published number are those of v10.
>
> **Editorial revision of 2026-09-22 — vocabulary and dataset provenance.** We no
> longer call a false positive a “hallucination”: in the generative-model literature that word
> names a different phenomenon, and what is measured here is a **spurious connected component** — a
> lesion predicted where the ground truth carries none. §1 states the choice explicitly. §3.1 now
> lists one by one the 55 cases dropped between the 1251-case download and the 1196-case study set
> (`analysis/DATASET_EXCLUSIONS.md`), with the trigger of each exclusion and a re-measurement of
> file integrity; the exclusion is a patient-level precaution taken in March 2026, upstream of
> every training run and every metric. No number in this manuscript changes.
>
> **Editorial revision of 2026-09-19 — structure and title.** The section plan is aligned with
> Papers 2 and 3: the Methods now absorb the dataset (§3.1) and the evaluation protocol (§3.5),
> which declares up front the two scales used throughout — the official BraTS-2023 lesion-wise
> metrics and the internal voxel-wise protocol; Limitations becomes a standalone section (§6);
> Perspectives is merged into the Conclusion (§7). The subtitle is tightened around the same
> hook. No result is modified; section references are renumbered (§5.x → §4.x, §6.x → §5.x).
>
> **Revision of 2026-09-01 — authors and title.** Stanislas Larnier joins the author list in
> second position, by mutual agreement between the two authors; the Acknowledgements section is
> replaced by a Contributions section. No number in the manuscript is modified. The previous
> author list remains the one carried by the Zenodo deposit up to v9 (2026-07-03); the present
> list takes effect from v10 of the deposit (concept DOI `10.5281/zenodo.19695263`).
>
> **Editorial revision of 2026-08-11.** The citable text remains the Zenodo deposit (concept DOI
> `10.5281/zenodo.19695263`), whose evaluation under the official BraTS-2023 metrics gives the
> connected-component consensus **+0.024 lesion-wise Dice** (Holm p = 4.5 × 10⁻¹⁶) and
> **−9.49 mm lesion-wise HD95** (Holm p = 5.7 × 10⁻²⁶) over the baseline, while removing ~41 %
> of spurious lesions. This revision changes no number: it puts back at the front what the work
> establishes — the consensus — and moves the null result of the auxiliary head alone to second
> place. Title aligned with that of the deposit. The numbers below are those of the internal
> protocol (voxel-wise Dice, fragments, per-class HD95) as measured in this manuscript; they do
> not replace the official metrics of the deposit.

**Guillaume Cassez · Stanislas Larnier**

Independent research

*Guillaume Cassez* — [ORCID 0009-0007-0987-3931](https://orcid.org/0009-0007-0987-3931) · `cassez.guillaume@gmail.com` · [guillaume-cassez.fr](https://guillaume-cassez.fr)  
*Stanislas Larnier* — `stanislaslarnier@gmail.com` · [HAL stanislas-larnier](https://cv.hal.science/stanislas-larnier)

*BraTS 2023 GLI · nnU-Net v2 · MedNeXt-B · 1196 validation patients*

---

## Abstract

**Requiring two models to agree beats the best of them alone.** On BraTS 2023 GLI, a
**connected-component consensus** (CC-consensus) filter — post-hoc and **entirely parameter-free**
— which removes any component of one model that a second model does not corroborate, eliminates
**66 % of NCR fragments** (Wilcoxon p < $10^{-189}$, topological definition: CC − 1 per class)
**at no Dice cost**, and **significantly improves HD95** on NCR (4.86 → 4.48 mm,
p = 5.7 × $10^{-14}$) and on WT (3.86 → 3.76 mm, p = 2.7 × $10^{-4}$), over 1196 patients in
5-fold cross-validation. Under the challenge's official metrics, this same rule is the only
configuration of the study that significantly beats the baseline (see the version banner).
Clinically, NCR is precisely the region where spurious fragments can mislead a radiotherapist
about the extent of tumour necrosis: the boundary-quality gain measured here is hidden by Dice and
visible through HD95. In a single-model configuration — no multi-fold ensemble, no TTA, a single
architecture — the CC-consensus reaches a mean Dice of 0.909, within one point of the range of the
published BraTS 2023 GLI winners (§4.5).

**The mechanism matters more than the ingredient.** The *distance-map* auxiliary loss (SDT —
Signed Distance Transform) that feeds this consensus brings, taken alone, no significant gain: at
convergence over 1196 patients in 5-fold CV, mean Dice Δ = +0.09 pp, Wilcoxon p > 0.25 per region
— a result confirmed by a multi-seed analysis (3 independent seeds, fold 0, mean Dice
Δ = −0.28 pp, t-test p = 0.21), which further reveals a DistMap training instability four times
larger than the baseline's (inter-seed σ ×4). This null result is reported in full, and it opens
the analysis rather than closing it: what the SDT head robustly produces is not Dice, it is a
**shift towards recall**, whose counterpart is a failure mode so far unreported in the BraTS
literature — spurious, spatially isolated connected components ("fragments") absent from the
ground truth, most marked on NCR (×1.5 vs baseline) and ED (×1.2). That is exactly what a second
model knows how to veto, and that is why the consensus works. A note on vocabulary: we deliberately avoid the term “hallucination”, which in the generative-model literature designates a different phenomenon (a fluent output with no grounding); what is measured here is a **false-positive connected component** — a predicted lesion absent from the ground truth.

**What post-hoc processing cannot give any more.** A hard-label ceiling study shows the rule is
already close to saturation: the per-class oracle is only +0.005 mean Dice above the default, and
no meta-selector over 31 features (4 classifier families) robustly beats the CC-consensus in
5-fold CV (Appendix B). Closing that gap requires voxel-level probabilistic voting or
architectural diversity — which motivates Paper 2 towards a fragment-aware training loss rather
than further post-hoc engineering.

**Contributions.** (1) A simple, parameter-free CC-consensus filter that removes 66 % of NCR
fragments at no Dice cost and **significantly improves NCR HD95** (p = 5.7 × $10^{-14}$) — a
clinically relevant boundary-quality gain that Dice does not show. (2) The quantitative
characterisation of the topological fragment artefact induced by the auxiliary SDT loss — invisible
to Dice, prevalent on NCR — with a size-threshold-free topological definition, at scale (1196
patients), which explains *why* the consensus has something to remove. (3) The delimitation of the
ceiling of any post-hoc filtering over these predictions, measured rather than asserted.

---

## 1. Introduction

Brain tumor segmentation on multi-modal MRI (BraTS challenge) has been dominated in recent years by nnU-Net [Isensee 2021] derivatives. The canonical task is 3D voxel classification into four classes: background, necrotic core (NCR, label 1), peritumoral edema (ED, label 2) and enhancing tumor (ET, label 3). Performance is usually reported as Dice coefficients on three nested regions WT = {1,2,3}, TC = {1,3}, ET = {3}.

Top-performing teams refine the backbone (MedNeXt [Roy MICCAI 2023], Swin-UNETR) while leaving the training loss essentially unchanged: Dice + cross-entropy. In parallel, **auxiliary distance-map regression** [Ma MIDL 2020 ; Xue AAAI 2020] is regularly proposed to make the network shape-aware, with mixed empirical results. Applications specific to BraTS exist — parallel-decoder multi-task learning [Huang 2021], Hausdorff-aware losses [Karimi & Salcudean 2020], and regression-only geodesic formulations [Dang 2024, SiNGR] — but none to date report or analyse the fragment artefact characterised here (§4.2).

What is less explored, and what carries the result of this paper, is what becomes of a
prediction when a **second model has to corroborate it**. Connected-component-level consensus
rules are rare in the published BraTS literature (§2), yet they are free — no parameter, no
extra training — and they act exactly where the challenge's lesion-wise metric penalises: the
spurious component. That is the mechanism this paper isolates, measures and bounds.

This paper pursues four objectives:

* **A consensus operator, and what it buys**: a parameter-free, per-connected-component veto rule
  that removes 66 % of the NCR fragments at no Dice cost and significantly improves HD95 (§4.3) —
  the only configuration of the study that beats the baseline under the challenge's official
  metrics.
* **Empirical characterisation** of the auxiliary SDT task at convergence on MedNeXt-B / nnU-Net v2: at 300 epochs in 5-fold CV on 1196 patients, DistMap produces **no** significant Dice gain (p > 0.25 per region), contrary to the impression drawn from comparisons at reduced training budgets.
* **Failure-mode analysis**: identification and quantification of an under-reported artefact of the SDT task — the production of small, spatially-isolated connected components that inflate false-positive counts without materially affecting Dice. This qualitative observation was made possible by an **interactive companion 3D viewer** built specifically for this project, which renders Baseline / DistMap / CC-Consensus meshes side-by-side for all 1196 patients ([guillaume-cassez.fr/imagerie-medicale/brats/2023-distance-map/viewer/](https://guillaume-cassez.fr/imagerie-medicale/brats/2023-distance-map/viewer/)).
* **Ceiling analysis** of a post-hoc CC-consensus filter that corrects this artefact, with a 1196-patient study delimiting what a feature-based meta-selector can achieve without softmax access or model diversity.

---

## 2. Related work

**Distance-transform auxiliary losses on medical segmentation.** [Ma 2020] proposes an auxiliary SDT regression head for abdominal / cardiac structures (LiTS, LA atrium), establishing the tanh + MSE recipe adopted here. [Xue 2020] uses signed distance maps as the **main output** (not auxiliary) on organ datasets with λ = 10 and no ablation. [Karimi & Salcudean 2020] derive a Hausdorff-distance-aware loss from distance transforms and evaluate it on nnU-Net + BraTS, but as a **loss modification** rather than as an auxiliary regression head. None of these works report the fragment phenomenon characterised here.

**Distance-map approaches applied specifically to BraTS.** The idea of combining distance-based shape supervision with BraTS segmentation is **not novel in itself**; two prior works are particularly close to the present setup and must be flagged explicitly.

- [Huang et al. 2021] train a V-Net with two *parallel decoders* on BraTS 2018–2020 — one producing the segmentation mask, the other regressing an *unsigned* distance transform through a sigmoid activation. This is the closest published prior art. The present work differs in three concrete ways: (i) a lightweight `Conv3d(32→3) + tanh` auxiliary head rather than a full parallel decoder (<0.1 % added parameters vs a doubled decoder path); (ii) *signed* Euclidean distance with MSE, not unsigned DT with sigmoid; (iii) MedNeXt-B / nnU-Net v2 on BraTS 2023 GLI (1196 patients) rather than V-Net on BraTS 2018–2020.
- [Dang et al. 2024, *SiNGR*] propose a **signed normalised geodesic** regression with Focal-L1 on tanh-activated outputs, **replacing** the segmentation output on BraTS 2020 (Swin-UNETR / UNet3D backbones). The present work is multi-task (keeps the Dice + CE softmax output alongside the SDT regression) and uses plain signed Euclidean distance, not a geodesic transform.

Neither Huang et al. nor SiNGR report or analyse the fragment artefact described in §4.2 of this paper; this is the specific empirical contribution claimed here.

**Ensembling and fusion.** Classical BraTS winners rely on 5-fold ensembling (soft-voting of softmax outputs). Model-selection or stacking rules at the patient level are uncommon; connected-component-level consensus rules are rarer still in the published BraTS literature.

**Failure-mode analysis.** Component-level metrics (lesion-wise F1) have been introduced in the BraTS 2023 challenge but remain secondary to Dice / HD95 in published work. To our knowledge, no prior work quantifies and localises the fragment bias of SDT-auxiliary losses on BraTS.

---

## 3. Methods

### 3.1 Dataset and backbone

**Dataset.** BraTS 2023 GLI (1251 patients, 4 modalities each). Preprocessing through the nnU-Net v2 defaults (per-patient z-score, automatic cropping, 1 mm³ isotropic resampling). Ground-truth labels {0, 1, 2, 3}. Of the 1251 unified cases, 1196 were retained for training and evaluation: the 55 dropped cases are listed one by one — trigger, git date of the triggering entry, and a re-measurement of their file integrity — in `analysis/DATASET_EXCLUSIONS.md`. The exclusion is a patient-level precaution recorded in March 2026, upstream of every training run and every metric; no file-level defect (unreadable NIfTI, NaN/Inf, out-of-set label, divergent affine) reproduces on those 55 cases today, and they are byte-identical across the three surviving copies of the dataset. Patient split: 5-fold cross-validation stratified by patient ID. All metrics below are computed on the fold-out set (n = 239 for fold 0) or aggregated over all 5 folds (n = 1196).

**Backbone.** MedNeXt-B [Roy MICCAI 2023] re-implemented inside nnU-Net v2 with the `nnUNetPlans_96GB_mednext` plan (patch 128³, BS 2, BF16, RTX PRO 6000 Blackwell).

**Auxiliary head.** A single 1 × 1 × 1 Conv3D(32 → 3) + tanh predicting a normalised SDT map for each of NCR, ED, ET regions. Ground-truth SDT is pre-computed once per patient via `scipy.ndimage.distance_transform_edt` on each binarised region mask, signed by sign(inside − outside), and min-max clipped to [−1, 1] with boundary = 0.

**Loss.** $\mathcal{L} = \mathcal{L}_{\mathrm{Dice+CE}} + \lambda \cdot \mathcal{L}_{\mathrm{MSE}}^{\mathrm{SDT}}$, with $\lambda = 1$ as the default (gradient-balanced calibration ÷ 5; full static ablation over 11 values detailed in Appendix A).

```{=latex}
\needspace{15\baselineskip}
```

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
for each class c ∈ {1, 2, 3}:
    D_mask  := (P_D == c)
    B_mask  := (P_B == c)
    labeled, n := cc_label(D_mask, structure=26-connectivity)
    for each cc_id ∈ 1..n:
        cc := (labeled == cc_id)
        if cc ∩ B_mask = ∅:
            P_F[cc] := 0        # remove unconfirmed fragment
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

The gap between these oracles and the default CC-consensus mean is the maximum achievable gain of any selection policy. Candidate policies evaluated (size-adaptive threshold, meta-classifiers, one-feature rule) and their results are reported in §4.4 and detailed in Appendix B.

### 3.5 Evaluation

**Two scales, declared up front.** Every table in this manuscript states which of the two evaluation scales it reports; the two are never mixed within one table. (1) The **official BraTS-2023 scale** — the challenge’s *BraTS-2023-Metrics* toolkit (GLI parameters): lesion-wise Dice and HD95 per region (WT, TC, ET) after connected-component cleanup (components < 1000/250/500 voxels removed per region), plus the toolkit’s voxel-wise *Legacy Dice* for reference. This is the scale of the headline result carried by the version banner above and by the deposit: over the 5-fold CV, the CC-consensus gains +0.024 lesion-wise Dice and −9.49 mm lesion-wise HD95 over the baseline (Holm-corrected), while removing ~41 % of spurious lesions; the per-seed official evaluation is tabulated in §4.6 (Tables A and B). (2) The **internal protocol** — voxel-wise Dice with the nnU-Net / MONAI empty-region convention, fragment counts, agreement and morphology features: the scale of the mechanism analyses in the body (§4.1–§4.4). The two scales answer different questions: the official one scores lesion-level agreement, as read by the challenge; the internal one measures voxel-level overlap and topology, and its absolute values are not comparable to challenge leaderboards (§4.5).

**Internal protocol — Dice** per region (WT, TC, ED, ET) with the standard nnU-Net / MONAI convention: *Dice = 1 if GT and prediction are both empty*. See §4.5 for caveats when comparing to BraTS challenge leaderboards.

**Fragment count (topological definition).** A **fragment** is a connected component (26-connectivity) of a given class that is **not the largest** component of its class — i.e. a CC topologically disconnected from the main tumor body. Per class $c$ on a prediction $P$, the fragment count is:
$$\mathrm{fragments}(P, c) = \max(0, \; \mathrm{nb\_CC}(P == c, \text{26-conn}) - 1)$$
No size threshold — 26-connectivity (shared face, edge, or corner) alone defines what is topologically linked. This definition treats small and large accessory components symmetrically.

**Inter-model agreement features (11)**: Dice(Baseline, DistMap) for WT/TC/ET; volumetric difference $|{|P_B^c|} - {|P_D^c|}| / ({|P_B^c|} + {|P_D^c|})$ for ET and NCR; number / fraction / max size of DistMap CC with no Baseline overlap, per ET and NCR.

**Morphology features (20)**: volume per region, volume ratios, 26-connectivity CC count and size for NCR/ET, inertia-tensor elongation (λ₁/λ₃), sphericity $(\pi^{1/3}(6V)^{2/3})/S$, surface roughness $S_{\mathrm{pred}}/S_{\mathrm{sphere}}$, Euler number ([scikit-image] `euler_number`, connectivity 3) for WT/TC/ET, cavity count of WT (`binary_fill_holes` diff), baseline / distmap CC counts per NCR and ET, ET CC spread (std of centroid distances).

---

```{=latex}
\needspace{22\baselineskip}
```

## 4. Results

### 4.1 At convergence, DistMap and Baseline are equivalent in Dice

On the 1196 patients aggregated out-of-fold from the 5-fold CV (300-epoch schedule per fold; DistMap fold 0 stopped at 178 ep, the other 9 training runs complete), DistMap and Baseline produce **statistically indistinguishable** Dice:

| Region | Baseline | DistMap | ΔDice | p-value | Improved / degraded / tied |
|---|---|---|---|---|---|
| WT | 0.9354 | 0.9360 | +0.006 pp | 0.72 | 577 / 618 / 1 |
| TC | 0.9185 | 0.9180 | −0.005 pp | 0.27 | 595 / 596 / 5 |
| ET | 0.8696 | 0.8723 | +0.027 pp | 0.54 | 568 / 596 / 32 |
| **Avg** | **0.9078** | **0.9088** | **+0.009 pp** | **0.50** | — |

Paired signed Wilcoxon test, one-sided hypothesis DistMap $>$ Baseline. No region reaches the standard significance threshold (p > 0.25 everywhere); on WT, more patients are degraded than improved by DistMap (618 vs 577). The Δ = +0.09 pp of avg Dice is within measurement variance.

**Implication.** The auxiliary SDT loss, as formulated here (Conv3D(32→3)+tanh head, MSE regression, λ = 1), confers no significant Dice improvement at convergence on BraTS 2023 GLI. This does not rule out that DistMap produces predictions that *differ* from Baseline: the two models diverge on 1195/1196 patients (a single strict tie in avg Dice), but their disagreements cancel out on average in the global Dice. This topological difference without Dice magnitude motivates the fragment analysis that follows.

```{=latex}
\needspace{21\baselineskip}
```

### 4.2 DistMap introduces spurious fragments

Qualitative inspection of DistMap predictions targeted cleaner boundaries — the expected behaviour of a distance-aware loss. Instead, DistMap predictions consistently show more isolated connected components than Baseline. Topological quantification on the 1196 patients of the 5-fold CV (per-patient means, fragments = CC − 1 per class, 26-connectivity):

| Fragments / patient | Baseline | DistMap | **CC-Consensus** | Δ D−B | Δ F−D | F/D reduction |
|---|---|---|---|---|---|---|
| **NCR** | 79.7 | 93.3 | **31.3** | +13.6 | −61.9 | **−66 %** |
| **ED** | 28.9 | 35.3 | **17.0** | +6.4 | −18.3 | **−52 %** |
| **ET** | 2.15 | 2.33 | **1.57** | +0.18 | −0.76 | **−33 %** |

One-sided paired Wilcoxon signed-rank tests on the 1196 patients:

- **DistMap inflates fragments vs Baseline** on all three classes: NCR (p = 5.5 × $10^{-42}$), ED (p = 2.0 × $10^{-49}$), ET (p = 1.3 × $10^{-3}$). The artefact is statistically massive and systematic.
- **CC-Consensus reduces fragments vs DistMap**: NCR (p < $10^{-189}$), ED (p < $10^{-162}$), ET (p = 1.1 × $10^{-53}$).
- **CC-Consensus also reduces vs Baseline**: NCR (p < $10^{-188}$), ED (p < $10^{-144}$), ET (p = 1.4 × $10^{-30}$) — the post-hoc filter even corrects fragments inherited from Baseline when DistMap does not overlap them.

This effect **is invisible on Dice** (§4.3: mean Dice B / D / F = 0.9078 / 0.9088 / 0.9090, differences within noise) — a few-voxel fragment does not affect an overlap metric when the median tumor volume is ~90 000 voxels. This is precisely why prior literature had not reported the artefact: Dice is blind to topology.

![Figure 1 — Mean fragment count per patient (non-largest connected components, 26-connectivity, no size threshold) for each class × variant, on the 1196 patients of the 5-fold CV. DistMap inflates the NCR fragment count by +17 % over Baseline; the CC-consensus filter brings it down to 31.3 — a **66 %** reduction from DistMap (Wilcoxon p < $10^{-189}$).](figures/fragment_counts.png){width=90%}

**Qualitative illustrations on the six reference cases.** Figures 2–7 below show, for each of the six pinned patients (C1–C6) of the companion 3D viewer, the segmentations produced by GT / Baseline / DistMap / CC-Consensus, left sagittal view, tumor regions only (Brain masked for focus) — the viewer rendering under the official regime, on a white background for printing. The cases were re-selected on 2026-08-31 on the data regenerated under the clean official regime (1000/250/500 component cleanup): the scores quoted in the captions are official lesion-wise Dice averaged over the 3 regions, as opposed to the internal protocol (voxel-wise Dice) used in the body of the text. Each figure illustrates one of the six behaviour modes identified in Appendix E.

**Note on 3D rendering (two pipelines).** The viewer offers a smooth mode and a voxel mode, each served by a distinct pipeline depending on the nature of the mesh.

*Voxel mode (raw truth).* *Greedy voxel meshing*: each voxel of the segmentation is turned into a cubic face merged with its coplanar neighbours. No interpolation, no smoothing — exactly what the model predicted at the voxel level. Used as ground-truth reference whenever one needs to count or precisely localise.

*Smooth mode (default for Figures 2–7), main meshes.* Pipeline `fill_holes + dilation + marching cubes`: the binary mask is first filled (`scipy.ndimage.binary_fill_holes` to remove internal cavities such as ventricles, sulci), dilated by one voxel (`binary_dilation`, 1 iteration) to soften the marching-cubes staircase, then marching-cubed at level 0.5. This is the pipeline used for the tumor-body and Brain meshes shown in Figures 2–7.

*Smooth mode, fragments and cavities.* For small components (< 4 voxels down to sub-voxel fragments), a separate **signed distance field** pipeline is used: 26-connectivity dilation to bridge voxels touching only by corner/edge, Euclidean inner and outer distance transforms (`scipy.ndimage.distance_transform_edt`) to build the signed distance field, cubic spline upsampling ×2 for sub-voxel resolution, then marching cubes at level iso = −0.3 (empirically calibrated for volume preservation). This pipeline is **necessary for small fragments** because naive marching cubes at 0.5 on a 1-voxel mask renders 1/6 of the true volume (×6 error) while the signed distance field preserves volume to ±5 % across all sizes.

*Shared property of both smooth pipelines.* They **preserve topology** (same connected components, same 26-connectivity count as voxel mode); the difference is purely cosmetic. Smooth is the default because the rendering is close to a clinical console; voxel mode remains one click away whenever voxel-exact inspection is needed.

\clearpage

![Figure 2 — Case **C1** (patient `BraTS-GLI-01435-000`): mode D < F < B (4/1196, 0.3 %), the most striking case. Baseline (0.924) ≫ DistMap (0.629): DistMap predicts a whole tumor mass far from the actual tumor (WT/TC Dice ≈ 0.44, HD95 ≈ 189 mm). **CC-Consensus removes the DistMap components not corroborated by Baseline** (veto) and restores 0.924.](figures/patient_C1_01435-000_4models.png){width=100%}

\clearpage

![Figure 3 — Case **C2** (patient `BraTS-GLI-01094-000`): the filter confirms DistMap (1183/1196, 98.9 % of patients — the majority mode under the official regime). Baseline under-segments the tumor (0.643; WT ≈ 0.49, HD95 ≈ 188 mm); DistMap is accurate (0.968, HD95 1.0 mm) and produces no spurious component: after the official cleanup, all of its components are corroborated by Baseline, so the veto removes nothing (**F = D = 0.968**).](figures/patient_C2_01094-000_4models.png){width=100%}

\clearpage

![Figure 4 — Case **C3** (patient `BraTS-GLI-01530-000`): mode B < F < D (3/1196, 0.3 %): the filter is pulled baseline-side. Baseline detects no enhancing tumor (TC/ET = 0; 0.241); the veto removes the uncorroborated DistMap core component (TC 0.770). The fusion keeps the DistMap WT contour (0.855, HD95 4 mm) but loses the core: **0.285 < 0.542**.](figures/patient_C3_01530-000_4models.png){width=100%}

\clearpage

![Figure 5 — Case **C4** (patient `BraTS-GLI-00017-001`): the veto has nothing to remove here, but both models miss the core. After the official cleanup (components < 1000/250/500 voxels), the uncorroborated false positives are already gone: the filter confirms DistMap (**F = D = 0.657 > B = 0.656**). Near-perfect WT contour (0.969) but missed core (TC = 0, TC HD95 = official 374 mm sentinel).](figures/patient_C4_00017-001_4models.png){width=100%}

\clearpage

![Figure 6 — Case **C5** (patient `BraTS-GLI-00733-001`): synergy, **F > max(B, D)** (2/1196, 0.2 %). Baseline (0.751) and DistMap (0.805) both lose a large part of the whole tumor (WT Dice ≈ 0.32/0.48, HD95 ≈ 250/188 mm); CC-Consensus restores the WT contour (0.955, HD95 1.4 mm) and reaches **0.964 — strictly above both parents**.](figures/patient_C5_00733-001_4models.png){width=100%}

\clearpage

![Figure 7 — Case **C6** (patient `BraTS-GLI-00388-000`): the "break" mode is almost extinct under the official regime: **F < min(B, D)** for only 2/1196 (0.2 %), maximum gap 0.0007. Here the fusion stays just below the worst parent (**0.921** against 0.923/0.922). Measured with the same method on the same 1196 patients, this mode was worth 47/1196 (3.9 %) on the raw predictions, before the official cleanup.](figures/patient_C6_00388-000_4models.png){width=100%}

```{=latex}
\needspace{18\baselineskip}
```

### 4.3 The CC-consensus improves NCR HD95 at no Dice cost

Aggregation of the out-of-fold predictions over the 5 folds (n = 1196):

| Strategy | Avg Dice | Δ vs default CC-consensus |
|---|---|---|
| Baseline alone | 0.9078 | −0.00115 |
| DistMap alone | 0.9088 | −0.00020 |
| CC-Consensus (default rule) | 0.9090 | 0 (ref.) |
| **Patient-level oracle** | 0.9131 | **+0.00412** |
| **Per-class oracle** | 0.9139 | **+0.00494** |

```{=latex}
\needspace{16\baselineskip}
```

Per-patient classification (with $F$ denoting the CC-consensus output):

| Case | Count | % |
|---|---|---|
| Baseline beats DistMap (B > D) | 602 | 50.3 % |
| DistMap beats Baseline (D > B) | 593 | 49.6 % |
| Filter output between B and D | 559 | 46.7 % |
| **Filter < both (damage)** | **463** | **38.7 %** |
| **Filter > both (synergy)** | **157** | **13.1 %** |

The CC-consensus filter degrades the patient score in 38.7 % of the cases, against 13.1 % of synergy. Per region, CC-Consensus strictly wins on 2.7 % of patients for WT, **21.7 % for TC** and 6.9 % for ET. The Dice benefit of the filter is therefore concentrated on TC; for WT and ET, the Baseline-alone or DistMap-alone choice already dominates.

```{=latex}
\needspace{19\baselineskip}
```

**Boundary quality (HD95).** Complementing Dice, the 95 % Hausdorff distances on the nested BraTS regions (WT/TC/ET) **and** on the individual classes (NCR, ED) where the fragments live (n varies by row according to the number of patients with a finite HD95 on the class concerned):

| Region / class | Composition | Baseline | DistMap | CC-Consensus | Δ CC-Cons. vs DistMap |
|---|---|---|---|---|---|
| WT | {1, 2, 3} | 3.91 mm | 3.86 mm | **3.76 mm** | **−0.10 mm, p = 2.7 × $10^{-4}$** |
| TC | {1, 3} | 3.08 mm | 2.79 mm | 2.88 mm | +0.09 mm, n.s. |
| ET | {3} | 2.62 mm | 2.59 mm | 2.70 mm | +0.11 mm, n.s. |
| **NCR** | {1} | 4.89 mm | 4.86 mm | **4.48 mm** | **−0.38 mm, p = 5.7 × $10^{-14}$** |
| ED | {2} | 4.25 mm | 4.33 mm | 4.21 mm | −0.12 mm, n.s. (p = 0.82) |

Paired signed Wilcoxon test, one-sided hypothesis HD95(CC-Consensus) < HD95(DistMap). n = 1160 for WT/TC/ET (restriction to patients with a finite HD95 on the 3 nested regions), 1153 for NCR, 1193 for ED.

**The dominant signal is on NCR**: CC-Consensus reduces NCR HD95 by 0.38 mm (p = 5.7 × $10^{-14}$) — direct quantitative confirmation that removing the fragments improves boundary quality on the class where they mostly proliferate (NCR: ×1.5 more DistMap fragments than Baseline, cf. §4.2). The signal on WT (−0.10 mm, p = 2.7 × $10^{-4}$) is its echo: NCR ⊂ WT, so NCR fragments contribute to the WT boundary error. On ED, the fragment reduction (−61 %) does not translate into a statistically significant HD95 gain — oedema has an intrinsic boundary variability that dominates the outliers introduced by fragments. On TC and ET (class 3), the HD95 are preserved.

The CC-consensus therefore delivers a measurable quantitative gain on NCR HD95 and WT HD95, where Dice remains insensitive. Clinically, NCR is precisely the region where spurious fragments can mislead a radiotherapist about the extent of tumour necrosis.

\clearpage

![Figure 8 — 1196 validation patients plotted in the model-disagreement plane: x = Dice(DistMap) − Dice(Baseline) (positive means DistMap wins at the patient level), y = Dice(CC-Cons.) − max(Dice(B), Dice(D)) (negative means the CC-consensus filter is worse than either model alone). The *red* C5 cloud below y = 0 collects 38.7 % of patients where the filter damages the score; the *green* C6 points above y = 0 represent only 13.1 %. This visual asymmetry is the central empirical observation of the paper.](figures/case_scatter.png){width=100%}

### 4.4 The hard-label ceiling is saturated

The gap between default CC-consensus and the per-class oracle (+0.005 mean Dice avg) upper-bounds the gain of any patient- or region-level selection policy from the three predictions {B, D, F}. We evaluate three families of policies in 5-fold CV (size-adaptive threshold over τ $\in$ {20, 50, 100, 200, 500, ∞} voxels; meta-classifiers RF/LR/GBM × patient/region on 31 features; one-feature rule via exhaustive search); **none robustly beats the default CC-consensus**. The one-feature rule, attractive on all-data fit (+0.00119), collapses in 5-fold CV (−0.00096): the best feature and threshold change across folds (TC: 4 distinct features over 5 folds; ET: 4 distinct features). A per-region RandomForest reaches 50 %, 43 %, 51 % argmax accuracy (vs 33 % random), confirming the presence of signal — but when the classifier is wrong, it picks a strictly worse model, yielding a net negative outcome.

The full detail — table of the 7 evaluated policies, RF importances per region, classification of the adaptive sweep, per-fold partition of the one-feature rule — is in **Appendix B**. The hard-label ceiling is essentially reached; closing the gap to the oracle requires voxel-level probabilistic voting or architectural diversity (§5.3).

### 4.5 Position relative to BraTS 2023 GLI winners

CC-consensus reaches Dice avg = 0.909 (WT 0.935, TC 0.919, ET 0.873) on 1196-patient 5-fold CV with a single-model setup (no multi-fold ensemble, no TTA, single architecture). This is within one percentage point of the published BraTS 2023 GLI winner range on private test set (0.87–0.89 Dice avg; Ferreira *et al.* 2024). Two caveats apply to the direct comparison: (i) different evaluation set (5-fold CV on train + val pool vs private test set, typical 1–2 pp gap to the disadvantage of the test set); (ii) the Dice = 1 on empty-region convention (nnU-Net / MONAI) inflates ET by ~0.003 relative to the lesion-wise convention used by the challenge (32/1196 patients with empty ET in GT).

We do not claim a new state-of-the-art; the CC-consensus filter is **orthogonal to ensembling** — fragment reduction is a gain that stacks with classical multi-fold / TTA tricks without duplicating them.

### 4.6 Robustness to the training seed (3 seeds, fold 0)

§4.1 uses seed 42 for all folds. To estimate inter-seed variance and verify that the non-significance is not an initialisation artefact, three independent trainings (seeds 1, 2, 3) are run for Baseline and DistMap (λ=0.1, best λ per Appendix A) on fold 0 (n≈240 patients), 300 epochs each.

```{=latex}
\needspace{14\baselineskip}
```

**Fold-0 validation Dice (nnU-Net, 240 patients):**


| Config | Seed 1 | Seed 2 | Seed 3 | Mean ± σ |
|---|---|---|---|---|
| Baseline | 0.9078 | 0.9066 | 0.9078 | **0.9074 ± 0.0007** |
| DistMap (λ=0.1) | 0.9074 | 0.9043 | 0.9021 | **0.9046 ± 0.0027** |
| Δ (B − D) | +0.04 pp | +0.23 pp | +0.57 pp | +0.28 pp |

Paired t-test (n=3 seeds): t=1.83, p=0.21 — not significant. The non-significance found in 5-fold CV (§4.1, Δ=+0.09 pp, p>0.25) is confirmed across the three seeds: Baseline slightly leads DistMap in all three cases, with no gap reaching 1 pp or the significance threshold.

Two observations:

- **DistMap instability (×4).** DistMap's inter-seed variance (σ=0.0027) is 4× that of Baseline (σ=0.0007). The auxiliary SDT loss makes training markedly more sensitive to initialisation. This explains the apparent DistMap advantage seen at the reference seed (42) in Appendix A (+0.13 pp at λ=0.1): it is an initialisation fluctuation, not a robust signal.
- **Monotone baseline advantage.** The gap Δ(B−D) grows from +0.04 pp (seed 1) to +0.57 pp (seed 3). With n=3 no causal trend can be established; the observation is consistent with DistMap's higher random variance.

**Official BraTS-2023 metrics and CC-consensus (D∩B) per seed.** Full evaluation on the 3×240 patients (720 valid pairs) with the official *BraTS-2023-Metrics* (Legacy Dice, LW Dice, HD95), on predictions verified free of residual fragments — the lesion-wise baseline is therefore identical to the one reported in Paper 2 on the same predictions. On Legacy Dice, neither DistMap nor the consensus differs from Baseline (p > 0.35 Wilcoxon throughout). The benefit concentrates on lesion-wise detection of the whole tumor: the CC-consensus filter significantly improves **LW Dice WT** (0.810 → 0.853, +4.28 pp, p < 10⁻⁴ Wilcoxon) and **LW HD95 WT** (54.5 → 37.3 mm, −17.2 mm, p < 10⁻⁴), at no cost on the volumetric Dice. DistMap alone already partially improves **LW Dice WT** (+1.54 pp, p = 0.041 Wilcoxon), with the consensus amplifying the gain.

```{=latex}
\needspace{22\baselineskip}
```

**Table A — Baseline vs DistMap (λ=0.1), official metrics, fold 0, 3 seeds**

| Metric | Region | Baseline (mean±σ) | DistMap (mean±σ) | Δ | p t-test | p Wilcoxon |
|---|---|---|---|---|---|---|
| Legacy Dice | WT | 0.9361 ± 0.0006 | 0.9359 ± 0.0012 | −0.02 pp | 0.89 | 0.44 |
| Legacy Dice | TC | 0.9208 ± 0.0006 | 0.9170 ± 0.0040 | −0.38 pp | 0.35 | 0.36 |
| Legacy Dice | ET | 0.8668 ± 0.0029 | 0.8616 ± 0.0017 | −0.53 pp | 0.12 | 0.63 |
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

```{=latex}
\needspace{22\baselineskip}
```

**Table B — CC-consensus (D∩B) vs Baseline, official metrics, fold 0, 3 seeds**

| Metric | Region | Baseline (mean±σ) | CC(D∩B) (mean±σ) | Δ | p t-test | p Wilcoxon |
|---|---|---|---|---|---|---|
| Legacy Dice | WT | 0.9361 ± 0.0006 | 0.9359 ± 0.0012 | −0.02 pp | 0.90 | 0.41 |
| Legacy Dice | TC | 0.9208 ± 0.0006 | 0.9184 ± 0.0025 | −0.24 pp | 0.39 | 0.56 |
| Legacy Dice | ET | 0.8668 ± 0.0029 | 0.8629 ± 0.0008 | −0.39 pp | 0.13 | 0.91 |
| LW Dice | WT | 0.8103 ± 0.0080 | **0.8531 ± 0.0041** | **+4.28 pp** | **0.017** | **5.5×10⁻⁵** |
| LW Dice | TC | 0.8670 ± 0.0067 | 0.8668 ± 0.0034 | −0.02 pp | 0.97 | 0.85 |
| LW Dice | ET | 0.8071 ± 0.0109 | 0.8018 ± 0.0047 | −0.54 pp | 0.42 | 0.69 |
| Legacy HD95 | WT | 6.42 ± 0.28 mm | 6.48 ± 0.05 mm | +0.06 mm | 0.81 | 0.82 |
| Legacy HD95 | TC | 5.95 ± 0.90 mm | 5.50 ± 0.12 mm | −0.45 mm | 0.56 | 0.67 |
| Legacy HD95 | ET | 13.85 ± 1.33 mm | 14.89 ± 0.74 mm | +1.04 mm | 0.14 | 0.60 |
| LW HD95 | WT | 54.52 ± 2.84 mm | **37.31 ± 2.18 mm** | **−17.21 mm** | **0.015** | **6.0×10⁻⁵** |
| LW HD95 | TC | 26.82 ± 2.73 mm | 25.42 ± 1.92 mm | −1.39 mm | 0.71 | 0.63 |
| LW HD95 | ET | 41.59 ± 4.68 mm | 43.48 ± 1.32 mm | +1.89 mm | 0.57 | 0.87 |

On multi-seed fold 0, the CC-consensus filter reproduces the lesion-wise gains already seen in 5-fold CV (§4.3) and concentrates them on the whole tumor: a significant and robust improvement in **LW Dice WT** (+4.28 pp) and **LW HD95 WT** (−17.2 mm), with p < 10⁻⁴ under Wilcoxon and p < 0.02 under the paired t-test on n=3 seeds, at no cost on Legacy Dice (Δ < 0.1 pp, non-significant). **No trend is observed on TC or ET** (|Δ| < 0.6 pp on LW Dice and < 1.9 mm on LW HD95, p > 0.6 under Wilcoxon): the benefit is purely WT.

---

## 5. Discussion

### 5.1 Why DistMap creates fragments

Plausible mechanism — not demonstrated: the SDT pressure sensitises the network to small *boundary-like* signals in transition tissues (oedema–white matter interfaces, post-surgical cavities, heterogeneous NCR), producing high-SDT-response voxels that occasionally survive the argmax as isolated blobs. This hypothesis is consistent with two observations: the increase in fragment count is concentrated on NCR and ED (regions with the longest and most irregular boundaries) and is much smaller on ET, whose gadolinium enhancement provides sharper boundary contrast. Three direct controls (λ ablation × fragment count, SDT response-map visualisation at fragment locations, distance-bin vs MSE) are described in **Appendix C** and deferred to future work; the primary contribution here is the characterisation and post-hoc mitigation of the artefact, not its mechanistic explanation.

### 5.2 Why the CC-consensus filter works

Baseline does not share the SDT pressure and therefore does not produce the same class of boundary-spurious blobs. Requiring overlap with Baseline for a DistMap CC to survive is equivalent to a **consensus test** on a perturbation-disjoint second detector. This is a principled application of the classical "agreement of independent classifiers" idea, adapted to connected components rather than voxels.

The rule has two desirable properties:

* **Asymmetric by design.** The rule starts from DistMap (superior boundary quality) and uses Baseline only as a veto. The better boundary is preserved wherever the veto does not fire.
* **Parameter-free.** No threshold, no learnable weight — the structure of CC connectivity is the only hyper-parameter (26-connectivity).

### 5.3 Why the oracle cannot be reached

Two same-family models (identical architecture, data, augmentations, loss family, differing only by the SDT auxiliary) produce too little diversity for a 3-way classification "B vs D vs F" to be reliably learned from shape features alone. Both models live in the same decision neighbourhood; their disagreements are dominated by high-frequency spatial noise that global morphology does not capture.

Closing the +0.005 Dice gap almost certainly requires one of:

* **Voxel-level probabilistic voting.** Exporting softmax outputs (not just argmax labels) and fusing at the voxel level breaks the hard-vote ceiling. A weighted average $\alpha \cdot \mathbf{p}_B + (1-\alpha) \cdot \mathbf{p}_D$ with α learned per region is a natural next step.
* **Architectural diversity.** Adding a non-MedNeXt backbone (nnU-Net vanilla, Swin-UNETR) increases oracle headroom dramatically, as the BraTS 2023 winners routinely demonstrate.
* **Multi-seed / multi-fold ensembling.** The classical recipe gains +0.5 to +2 Dice points on BraTS; fully compatible with — and orthogonal to — the CC-consensus rule proposed here.

## 6. Limitations

* **Single backbone.** All experiments use MedNeXt-B; generalisation to Swin-UNETR / nnU-Net vanilla / Restormer would strengthen the conclusion.
* **No probabilistic fusion baseline.** Only hard-label filtering is reported because softmax outputs were not persisted at inference time. The ceiling analysis explicitly addresses this gap for the hard-label setting.
* **Single-model-per-patient setup.** The CC-consensus filter reaches Dice avg 0.909 on 1196-patient 5-fold CV without multi-fold ensembling, TTA, or multi-architecture voting. Adding these standard tricks would likely push the score into, or above, the BraTS 2023 GLI winner range, but this would be a parallel-compute contribution orthogonal to the fragment-characterisation question this paper addresses.
* **Dice convention slightly inflates ET.** Empty-GT ET patients (2.7 % of BraTS 2023 GLI, non-enhancing cases, 32/1196 verified) are scored Dice = 1.0 under the nnU-Net / MONAI convention, which slightly inflates the ET regional mean (−0.003 only under the lesion-wise convention). The relative comparisons between Baseline, DistMap and CC-Consensus are not affected (all three use the same convention), but absolute ET Dice is not directly comparable to challenge leaderboards using the lesion-wise convention (see §4.5).
* **BraTS 2023 GLI only.** Extension to BraTS-MET (metastases) and BraTS-PED (paediatric) is left to future work; we expect the fragment bias to be more severe on metastases (multi-lesion pattern).
* **No small tumors in the dataset.** The minimum WT volume on BraTS 2023 GLI is 2808 voxels, median ~89 500 voxels. The topological fragment definition adopted in §3.5 (CC − 1 per class, no size threshold) is **intrinsically size-robust** and requires no recalibration for smaller tumors. However, **the pipeline evaluated here has not been tested on the clinically critical regime of small tumors** (a few hundred voxels), where early detection has major prognostic impact. Absolute morphology features (`vol_*`, `nb_cc_*`) would be out-of-distribution in that regime and would need re-examination before clinical use; the topological and relative features (`ratio_ET_WT`, `frac_small_cc_*`, sphericity, elongation) are size-robust by construction.

---

## 7. Conclusion

On MedNeXt-B / nnU-Net v2, the auxiliary SDT loss produces no significant Dice gain at
convergence (Δ avg Dice = +0.09 pp, Wilcoxon p > 0.25 per region, 5-fold CV on 1196 patients).
An independent multi-seed analysis (3 seeds × fold 0, §4.6) confirms the non-significance
(t-test p = 0.21) and reveals a DistMap training instability four times that of Baseline
(×4 inter-seed σ). The SDT loss does, however, change the topology of the predictions, by
introducing a fragment bias that the Dice metric fails to report. A parameter-free
connected-component consensus filter, which vetoes the DistMap CCs with no Baseline overlap,
eliminates 66 % of the NCR fragments over 1196 patients (p < $10^{-189}$) at no Dice cost, and
**significantly improves HD95 on NCR** (4.86 → 4.48 mm, p = 5.7 × $10^{-14}$) as well as on WT
(3.86 → 3.76 mm, p = 2.7 × $10^{-4}$) — a boundary-quality gain hidden by Dice, and clinically
relevant on tumor necrosis.

Over 1196 patients in 5-fold CV, we establish that this rule is already close to the saturation
ceiling of any hard-label post-hoc selection policy: the per-class oracle is +0.005 mean Dice
above the default, and no 31-feature meta-selector (4 classifier families) robustly beats that
default in CV. Closing this gap motivates **training-time fragment-aware losses** (Paper 2)
rather than further post-hoc engineering.

**Perspectives — training-time fragment-aware loss (Paper 2).** The hypothesis in §5.1 suggests fragments are a gradient effect. A training-time penalty term counting predicted connected components on the argmax of each mini-batch — and penalising small isolated blobs — should push the network not to instantiate them, making the post-hoc CC-consensus filter unnecessary. This is the direction of Paper 2.

**Dataset extensions.** BraTS-MET (metastases, multi-lesion pattern) is the most informative next test: DistMap fragments should be more severe there, and the CC-consensus filter should benefit more. BraTS-PED (paediatric) would test generalisation across demographic shifts.

---

## Author contributions

**Guillaume Cassez** (lead author): study design, model training, evaluations and analyses,
manuscript writing. **Stanislas Larnier**: formulation of the research questions, methodological
guidance, careful reviews of successive drafts of the paper. Both authors approved the final
version and the author order.

---

## Appendix A — Calibration of λ (auxiliary SDT loss)

At epoch 0 with a random-initialised network (seed 42), we measure $|\mathcal{L}_{\mathrm{Dice+CE}}| = 0{.}57$ and $\mathcal{L}_{\mathrm{MSE}}^{\mathrm{SDT}} = 0{.}12$, yielding a "gradient-balanced" λ = 4.70.

```{=latex}
\needspace{20\baselineskip}
```

A static ablation over λ ∈ {0, 0.1, 0.5, 1, 2, 5, 6, 7, 8, 9, 10} (100 epochs, fold 0, seed 42) produces Dice-avg scores all within a 0.5 pp window:

| λ | Dice avg | Δ vs Baseline |
|---|---|---|
| 0 (Baseline) | 0.9064 | 0 |
| 0.1 | 0.9077 | +0.0013 |
| 0.5 | 0.9070 | +0.0006 |
| 1.0 | 0.9067 | +0.0003 |
| 2.0 | 0.9060 | −0.0004 |
| 5.0 | 0.9105 | +0.0041 |
| 9.0 | 0.9104 | +0.0040 |

On this single fold and without per-patient significance testing, no λ clearly outperforms the baseline. This is consistent with the non-significance of the DistMap gain observed in 5-fold CV on 1196 patients (§4.1). Default training reported in the body uses λ = 1 (close to published heuristics and to the gradient-balanced calibration ÷ 5).

A dynamic weighting scheme — DWA (Dynamic Weight Average, Liu CVPR 2019) — that tracks the relative learning rates of the Dice+CE and SDT heads over training is a natural next direction: if a regime exists where SDT genuinely contributes without saturating, a static sweep cannot find it.

---

```{=latex}
\needspace{24\baselineskip}
```

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

The hypothesis in §5.1 (the SDT pressure produces high-response voxels at ambiguous interfaces, which occasionally survive the argmax) remains at this stage a **working hypothesis, not demonstrated**. The following three direct controls are all feasible on the existing checkpoints and are deferred to future work:

1. **λ ablation crossed with fragment count.** Verify that the mean number of fragments per patient grows monotonically with λ. Monotonic growth would confirm the causal link between SDT pressure and artefact; absence of monotonicity would suggest that optimisation noise dominates.
2. **SDT response-map visualisation at fragment locations.** For a sample of patients, overlay the tanh output of the auxiliary head and the fragment map; fragments should coincide with high-SDT-response voxels close to a tissue interface.
3. **Distance bins vs MSE.** Replace the `Conv3D(32 → 3) + tanh + MSE` head with a distance-bin classification head (e.g. 16 equi-probable bins in [−1, 1]). If the artefact disappears or substantially decreases, it is specific to the MSE-SDT formulation and not to distance supervision in general.

Running these three controls would move §5.1 from "working hypothesis" to "demonstrated mechanism".

---

## Appendix D — Runtime and reproducibility

All code, the 20 + 11 pre-extracted features, per-patient model scores, oracle / case-classification CSVs, threshold-sweep results and meta-selector outputs are available in the companion repository [github.com/guillaume-cassez/brats-moe-distmap-fusion-1](https://github.com/guillaume-cassez/brats-moe-distmap-fusion-1) and archived on Zenodo (concept DOI [10.5281/zenodo.19695263](https://doi.org/10.5281/zenodo.19695263)).

The trained model checkpoints (5 cross-validation folds for each variant, weights as `safetensors`, no optimiser state) are released on the Hugging Face Hub :

- Baseline : [huggingface.co/guillaume-cassez/mednext-baseline-brats2023gli](https://huggingface.co/guillaume-cassez/mednext-baseline-brats2023gli)
- DistMap (auxiliary SDT) : [huggingface.co/guillaume-cassez/mednext-distmap-brats2023gli](https://huggingface.co/guillaume-cassez/mednext-distmap-brats2023gli)

Per-patient extraction of the 31 features on the 1196 predictions runs in **~10 min** on 14 P-core threads (`taskset -c 0-13`) of an i7-14700K; the full meta-classifier sweep (4 families × 5 folds × 31-dim input) in ~2 min on the same host. **Training time per fold: ~13 h 30 min for 300 epochs** on a single RTX PRO 6000 Blackwell (96 GB), Baseline and DistMap variants at equivalent duration (the auxiliary SDT regression head adds < 1 % GPU overhead at 300 ep).

---

## Appendix E — The six demonstration patients

Six patients are highlighted to span the six model-ordering cases, used both for the figures and as pinned anchors in the companion 3D viewer. In the table, $F$ denotes the CC-consensus filter output. Patient identifiers are shown without the `BraTS-GLI-` prefix for compactness (the dataset prefixes them systematically). The cases were re-selected on 2026-08-31 on the regenerated data; the B / D / F scores are the official BraTS-2023 lesion-wise Dice (clean regime, 1000/250/500 cleanup, mean of the 3 regions) — as opposed to the voxel-wise Dice of the internal protocol used in the body of the text.

```{=latex}
\needspace{16\baselineskip}
\begin{center}
\renewcommand{\arraystretch}{1.3}
\footnotesize
\setlength{\tabcolsep}{2pt}
\begin{tabular}{|l|c|c|c|c|c|l|}
\hline
\textbf{Tag} & \textbf{Patient} & \textbf{Fold} & \textbf{B} & \textbf{D} & \textbf{F} & \textbf{Take-away} \\
\hline
C1 (D $<$ F $<$ B) & 01435-000 & 4 & 0.924 & 0.629 & 0.924 & Major veto: DistMap generates a spurious distant mass, the filter restores Baseline \\
\hline
C2 (F = D $>$ B) & 01094-000 & 3 & 0.643 & 0.968 & 0.968 & Dominant mode (98.9 \%): the veto removes nothing, DistMap confirmed \\
\hline
C3 (B $<$ F $<$ D) & 01530-000 & 1 & 0.241 & 0.542 & 0.285 & Filter pulled baseline-side: the uncorroborated DistMap core is removed \\
\hline
C4 (F = D $>$ B) & 00017-001 & 0 & 0.656 & 0.657 & 0.657 & Nothing to remove; both models miss the core (TC = 0) \\
\hline
C5 (F $>$ max(B, D)) & 00733-001 & 2 & 0.751 & 0.805 & 0.964 & Clean synergy: the WT contour restored beyond both parents \\
\hline
C6 (F $<$ min(B, D)) & 00388-000 & 2 & 0.923 & 0.922 & 0.921 & Break mode almost extinct in the official regime (2/1196, max gap 0.0007) \\
\hline
\end{tabular}
\end{center}
```

---

## References

* Isensee F., Jaeger P. F., Kohl S. A. A., Petersen J., Maier-Hein K. H. (2021). *nnU-Net: a self-configuring method for deep learning-based biomedical image segmentation*. **Nature Methods** 18, 203–211. DOI: 10.1038/s41592-020-01008-z.
* Roy S., Koehler G., Ulrich C., Baumgartner M., Petersen J., Isensee F., Jaeger P. F., Maier-Hein K. H. (2023). *MedNeXt: transformer-driven scaling of ConvNets for medical image segmentation*. **MICCAI 2023**, LNCS 14222, 405–415. DOI: 10.1007/978-3-031-43901-8_39.
* Ma J., Wei Z., Zhang Y., Wang Y., Lv R., Zhu C., Chen G., Liu J., Peng C., Wang L., Wang Y., Chen J. (2020). *How distance transform maps boost segmentation CNNs: an empirical study*. **Medical Imaging with Deep Learning (MIDL) 2020**, PMLR 121, 479–492.
* Xue Y., Tang H., Qiao Z., Gong G., Yin Y., Qian Z., Huang C., Fan W., Huang X. (2020). *Shape-aware organ segmentation by predicting signed distance maps*. **AAAI 2020**, 34(07), 12565–12572. DOI: 10.1609/aaai.v34i07.6946.
* Karimi D., Salcudean S. E. (2020). *Reducing the Hausdorff distance in medical image segmentation with convolutional neural networks*. **IEEE Transactions on Medical Imaging** 39(2), 499–513. DOI: 10.1109/TMI.2019.2930068. arXiv:1904.10030.
* Huang H., Yang G., Zhang W., Xu X., Yang W., Jiang W., Lai X. (2021). *A deep multi-task learning framework for brain tumor segmentation*. **Frontiers in Oncology** 11, 690244. DOI: 10.3389/fonc.2021.690244.
* Dang T., Nguyen H. H., Tiulpin A. (2024). *SiNGR: Brain tumor segmentation via signed normalized geodesic transform regression*. **MICCAI 2024**. arXiv:2405.16813.
* Ferreira A., Solak N., Li J., Dammann P., Kleesiek J., Alves V., Egger J. (2024). *How we won BraTS 2023 adult glioma challenge? Just faking it! Enhanced synthetic data augmentation and model ensemble for brain tumour segmentation*. **arXiv:2402.17317**.
* Liu S., Johns E., Davison A. J. (2019). *End-to-end multi-task learning with attention* (DWA — Dynamic Weight Average). **CVPR 2019**, 1871–1880. DOI: 10.1109/CVPR.2019.00197.
* Baid U., Ghodasara S., Mohan S., Bilello M., Calabrese E., Colak E., *et al.* (2021). *The RSNA-ASNR-MICCAI BraTS 2021 benchmark on brain tumor segmentation and radiogenomic classification*. **arXiv:2107.02314**.
* Menze B. H., Jakab A., Bauer S., *et al.* (2015). *The multimodal brain tumor image segmentation benchmark (BRATS)*. **IEEE TMI** 34(10), 1993–2024. DOI: 10.1109/TMI.2014.2377694.
