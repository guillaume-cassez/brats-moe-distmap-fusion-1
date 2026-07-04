# Loss auxiliaire de type *distance map* pour la segmentation de tumeurs cérébrales : ré-évaluation sous les métriques officielles BraTS-2023 — une tête SDT orientée rappel et un consensus de composantes connexes qui bat la baseline

**Guillaume Cassez**

Recherche indépendante · [ORCID 0009-0007-0987-3931](https://orcid.org/0009-0007-0987-3931) · `cassez.guillaume@gmail.com` · [guillaume-cassez.fr](https://guillaume-cassez.fr)

*BraTS 2023 GLI · nnU-Net v2 · MedNeXt-B · 1196 patients de validation*

---

## Résumé

On évalue l'ajout d'une tête de régression auxiliaire de type *distance map* signée (SDT — Signed Distance Transform) sur un pipeline MedNeXt-B / nnU-Net v2 pour la segmentation 3D de gliomes adultes (BraTS 2023 GLI), sous le **jeu complet des métriques officielles BraTS-2023** — Dice et HD95 *lesion-wise* (les métriques de classement du challenge), Dice et HD95 régionaux *legacy*, et détection lésionnelle — en validation croisée 5-fold à convergence (300 epochs, n = 1196). Sur les **critères primaires pré-spécifiés** — les deux métriques de classement officielles, moyennées sur les régions, corrigées Holm — la tête SDT **n'a aucun effet significatif** (Dice lesion-wise Δ = −0,003, Holm p = 1,0 ; HD95 lesion-wise Δ = +1,12 mm, Holm p = 1,0) ; elle est aussi **neutre sur le Dice régional** (Δ = +0,001, p = 0,24). Le gain Dice annoncé dans une version antérieure à budget d'entraînement réduit **ne survit pas à la convergence**.

Le seul effet robuste de la tête SDT est un **déplacement orienté rappel** : sensibilité régionale en hausse (Δ = +0,002, r = +0,20, p = 2,0 × $10^{-9}$) et moins de lésions manquées (Δ FN = −0,006, p = 8,3 × $10^{-3}$), au prix d'une **perte de spécificité** (r = −0,26, p = 1,2 × $10^{-14}$) — c'est-à-dire davantage de **composantes connexes fallacieuses** (« fragments ») sur TC et ET. On caractérise cet artefact topologique sur les 1196 patients (DistMap : ×1,5 fragments NCR vs Baseline, ×1,2 ED), un mode de défaillance jusqu'ici non rapporté dans la littérature BraTS et **invisible au Dice**.

On exploite ce compromis par un **filtre de consensus de composantes connexes** (CC-consensus) post-hoc et sans paramètre, qui ne conserve une composante DistMap que si un second modèle — Baseline (`CC(D∩B)`), ou la tête Kervadec plus spécifique (`CC(D∩K)`, Paper 2) — la corrobore dans la même classe. Le consensus supprime **~41 % des lésions fallacieuses** (FP lésions 0,396 → 0,234 par cas, p = 6,0 × $10^{-34}$) à un **coût de rappel négligeable**, et est **la première configuration à battre significativement la baseline sur les deux métriques de classement officielles** : Dice lesion-wise **+0,024** (Holm p = 4,5 × $10^{-16}$) et HD95 lesion-wise **−9,49 mm** (Holm p = 5,7 × $10^{-26}$). Ce gain est **invisible au Dice régional** — saturé : l'oracle par classe n'est qu'à +0,005 au-dessus du défaut — mais important sous la métrique lesion-wise officielle, ce qui justifie de rapporter le jeu complet. Une part du gain HD95 provient de la pénalité de 374 mm que la métrique officielle impose par lésion fallacieuse ; on l'énonce explicitement plutôt que d'impliquer un gain de précision de frontière sur les vraies lésions. Complémentairement, sur les distances *legacy* par classe, le filtre réduit aussi HD95 NCR (4,86 → 4,48 mm, p = 5,7 × $10^{-14}$) en éliminant 66 % des fragments NCR.

**Contributions.** (1) Une évaluation à convergence (300 ep, CV 5-fold, n = 1196) d'une tête SDT auxiliaire sous **toutes** les métriques officielles BraTS-2023, avec un critère primaire pré-spécifié — sans cherry-picking de métrique : la tête SDT est **neutre/nulle sur le classement officiel**. (2) La caractérisation quantitative, à grande échelle et invisible au Dice, d'un artefact topologique de fragments (la contrepartie « perte de spécificité » du déplacement orienté rappel), avec une définition topologique sans seuil de taille. (3) Un filtre CC-consensus simple et sans paramètre qui transforme ce compromis en **système battant la baseline sur les métriques officielles** (Dice lesion-wise +0,024 ; HD95 lesion-wise −9,49 mm) — seule configuration ici à y parvenir.

---

## 1. Introduction

La segmentation de tumeurs cérébrales sur IRM multi-modalités (challenge BraTS) est dominée ces dernières années par des dérivés de nnU-Net [Isensee 2021]. La tâche canonique est une classification 3D de voxels en quatre classes : fond, cœur nécrotique (NCR, label 1), œdème péri-tumoral (ED, label 2) et tumeur rehaussée (ET, label 3). La performance est habituellement rapportée via des coefficients de Dice sur trois régions emboîtées : WT = {1,2,3}, TC = {1,3}, ET = {3}.

Les équipes les plus performantes raffinent le backbone (MedNeXt [Roy MICCAI 2023], Swin-UNETR) tout en laissant la loss d'entraînement quasi inchangée : Dice + cross-entropy. En parallèle, la **régression auxiliaire de *distance maps*** [Ma MIDL 2020 ; Xue AAAI 2020] est régulièrement proposée pour rendre le réseau sensible à la forme, avec des résultats empiriques mitigés. Des applications spécifiques à BraTS existent — multi-tâche à décodeurs parallèles [Huang 2021], losses Hausdorff-aware [Karimi & Salcudean 2020], et formulations géodésiques « régression seule » [Dang 2024, SiNGR] — mais aucune à ce jour ne rapporte ni n'analyse l'artefact de fragments caractérisé ici (§5.2).

Ce papier poursuit trois objectifs :

* **Caractérisation empirique** de la tâche SDT auxiliaire à convergence sur MedNeXt-B / nnU-Net v2 : à 300 epochs en CV 5-fold sur 1196 patients, DistMap ne produit **pas** de gain Dice significatif (p > 0,25 par région), contrairement à l'impression tirée de comparaisons à budget d'entraînement réduit.
* **Analyse de mode de défaillance** : identification et quantification d'un artefact sous-rapporté de la tâche SDT — la production de composantes connexes petites et isolées qui gonflent les faux positifs sans toucher significativement au Dice. Cette observation qualitative a été rendue possible par un **viewer 3D interactif compagnon** construit spécifiquement pour ce projet, qui rend côte-à-côte les meshes Baseline / DistMap / CC-Consensus pour les 1196 patients ([guillaume-cassez.fr/brats/](https://guillaume-cassez.fr/brats/)).
* **Analyse du plafond** d'un filtre CC-consensus post-hoc qui corrige cet artefact, avec une étude sur 1196 patients délimitant ce qu'un meta-selector à base de features peut atteindre en l'absence d'accès aux softmax ou de diversité de modèles.

---

## 2. Travaux connexes

**Losses auxiliaires par *distance maps* en segmentation médicale.** [Ma 2020] propose une tête de régression SDT auxiliaire pour des structures abdominales / cardiaques (LiTS, LA atrium), établissant la recette tanh + MSE reprise ici. [Xue 2020] utilise des distance maps signées comme **sortie principale** (non auxiliaire) sur des organes, avec λ = 10 sans ablation. [Karimi & Salcudean 2020] dérivent une loss Hausdorff-aware à partir de distance transforms, évaluée sur nnU-Net + BraTS, mais comme **modification de loss** et non comme tête de régression auxiliaire. Aucun de ces travaux ne signale le phénomène de fragments caractérisé ici.

**Approches distance-map spécifiquement appliquées à BraTS.** L'idée d'associer une supervision de forme par distance à la segmentation BraTS **n'est pas nouvelle en soi** ; deux travaux antérieurs sont particulièrement proches du dispositif présenté et doivent être signalés explicitement.

- [Huang et al. 2021] entraînent un V-Net avec deux *décodeurs parallèles* sur BraTS 2018–2020 — l'un produisant le masque de segmentation, l'autre régressant une distance transform *non signée* à travers une sigmoid. C'est l'état de l'art le plus proche de ce travail. Le présent travail s'en distingue par trois points concrets : (i) une tête auxiliaire légère `Conv3d(32→3) + tanh` au lieu d'un décodeur parallèle complet (<0,1 % de paramètres ajoutés vs un décodeur dupliqué) ; (ii) distance euclidienne *signée* avec MSE, et non distance non signée avec sigmoid ; (iii) MedNeXt-B / nnU-Net v2 sur BraTS 2023 GLI (1196 patients) au lieu d'un V-Net sur BraTS 2018–2020.
- [Dang et al. 2024, *SiNGR*] proposent une régression **géodésique normalisée signée** avec loss Focal-L1 sur sortie tanh, qui **remplace** la sortie de segmentation sur BraTS 2020 (backbones Swin-UNETR / UNet3D). Le présent travail est multi-tâche (conservation de la sortie Dice + CE softmax à côté de la régression SDT) et utilise la distance euclidienne signée classique, et non une transformée géodésique.

Ni Huang et al. ni SiNGR ne rapportent ou n'analysent l'artefact de fragments décrit en §5.2 de ce papier ; c'est la contribution empirique spécifique revendiquée ici.

**Ensembling et fusion.** Les gagnants BraTS classiques s'appuient sur l'ensembling 5-fold (soft-voting des softmax). Les règles de sélection de modèle ou de stacking au niveau patient sont peu courantes ; les règles de consensus au niveau des composantes connexes le sont encore moins dans la littérature BraTS publiée.

**Analyse des modes de défaillance.** Des métriques au niveau composante (F1 lesion-wise) ont été introduites dans le challenge BraTS 2023 mais restent secondaires au Dice / HD95 dans les publications. À notre connaissance, aucun travail antérieur ne quantifie ni ne localise le biais de fragments induit par les losses SDT auxiliaires sur BraTS.

---

## 3. Méthodes

### 3.1 Architecture et entraînement

**Backbone.** MedNeXt-B [Roy MICCAI 2023] ré-implémenté dans nnU-Net v2 avec le plan `nnUNetPlans_96GB_mednext` (patch 128³, BS 2, BF16, RTX PRO 6000 Blackwell).

**Tête auxiliaire.** Un unique Conv3D(32 → 3, noyau 1 × 1 × 1) + tanh prédisant une carte SDT normalisée pour chacune des régions NCR, ED, ET. La SDT de référence est pré-calculée une fois par patient via `scipy.ndimage.distance_transform_edt` sur chaque masque binarisé de région, signée par sign(intérieur − extérieur), clippée min-max à [−1, 1] avec bord = 0.

**Loss.** $\mathcal{L} = \mathcal{L}_{\mathrm{Dice+CE}} + \lambda \cdot \mathcal{L}_{\mathrm{MSE}}^{\mathrm{SDT}}$, avec $\lambda = 1$ par défaut (calibration équilibrée par gradient ÷ 5 ; ablation statique sur 11 valeurs détaillée Annexe A).

### 3.2 Nommage des variantes

| Variante | Trainer | Auxiliaire ? |
|---|---|---|
| **Baseline** | `nnUNetTrainerMedNeXtBaseline` | pas de SDT |
| **DistMap** | `nnUNetTrainerMedNeXtDistMap` | SDT, λ = 1 |
| **CC-Consensus** | règle post-hoc (§3.3) sur DistMap + Baseline | post-hoc |

![**Schéma 1. Architectures des variantes Baseline et DistMap.** Les deux variantes partagent le même backbone MedNeXt-B / nnU-Net v2 et la même tête de segmentation (Dice + entropie croisée, supervision profonde). DistMap ajoute, à partir des mêmes features du décodeur, une tête de régression SDT auxiliaire `Conv3d(32 → 3) + tanh` entraînée par MSE contre la distance signée, pondérée par λ.](figures/p1_variants.png){width=90%}

### 3.3 Règle de filtrage CC-consensus[^moe]

[^moe]: Les versions antérieures de ce travail désignaient cette règle par « fusion MoE (Mixture-of-Experts) ». Ce label est abandonné : il n'y a ni réseau de gating appris, ni routage doux des inputs, ni entraînement conjoint experts-gate. Le terme neutre « filtre CC-consensus » est employé dans tout le document.

Étant données la prédiction Baseline $P_B$ et la prédiction DistMap $P_D$ (tous deux des tenseurs de labels dans {0, 1, 2, 3}), la prédiction filtrée $P_F$ est calculée classe par classe :

```
P_F := copy(P_D)
pour chaque classe c $\in$ {1, 2, 3}:
    D_mask  := (P_D == c)
    B_mask  := (P_B == c)
    labeled, n := cc_label(D_mask, structure=connectivité-26)
    pour chaque cc_id $\in$ 1..n:
        cc := (labeled == cc_id)
        si cc $\cap$ B_mask = $\emptyset$:
            P_F[cc] := 0        # on supprime le fragment non confirmé
```

La règle a quatre effets qualitatifs :

1. Les fragments DistMap isolés de la classe correspondante Baseline → **supprimés**.
2. Les raffinements de frontière DistMap sans recouvrement avec Baseline → **conservés** (on part toujours de $P_D$).
3. Les trous Baseline comblés par DistMap → **conservés** ($P_D$ est non nul à ces endroits).
4. Les faux positifs Baseline rejetés par DistMap → **restent rejetés** ($P_D$ est nul à ces endroits).

La règle n'a **aucun paramètre appris** et un seul hyperparamètre (connectivité 26 vs 6), fixé à 26 partout. C'est une opération de *veto* : Baseline n'ajoute aucun voxel nouveau ; il ne peut que supprimer des composantes que DistMap a prédites sans confirmation.

![**Schéma 2. Filtre CC-consensus (D∩B).** Pour chaque classe (NCR/ED/ET), on étiquette les composantes connexes (26-connexité) de la prédiction DistMap ; une composante n'est conservée que si elle recouvre la prédiction Baseline de la même classe, sinon elle est retirée. Opération de veto sans paramètre appris : on part toujours de DistMap, et Baseline ne fait que supprimer les fragments non confirmés.](figures/p1_fusion.png){width=90%}

### 3.4 Analyse du plafond

Pour caractériser le plafond de qualité atteignable par toute politique de sélection au niveau patient ou région sur les trois prédictions disponibles, on définit, pour chaque patient $p$ avec Dice régional $(D^B, D^D, D^F) \in \mathbb{R}^3$ par région $r \in \{\mathrm{WT}, \mathrm{TC}, \mathrm{ET}\}$ :

$$\mathrm{Oracle}_{\mathrm{patient}}(p) = \max_{m \in \{B,D,F\}} \tfrac{1}{3}\sum_r D^m_r$$

$$\mathrm{Oracle}_{\mathrm{par\text{-}classe}}(p) = \tfrac{1}{3}\sum_r \max_{m \in \{B,D,F\}} D^m_r$$

L'écart entre ces oracles et la moyenne CC-consensus par défaut est le gain maximal atteignable par toute politique de sélection. Les politiques candidates évaluées (seuil taille-adaptatif, meta-classifieurs, règle à une feature) et leurs résultats sont rapportés en §5.4 et détaillés en Annexe B.

---

## 4. Expériences

### 4.1 Données

BraTS 2023 GLI (1251 patients, 4 modalités chacun). La standardisation spatiale est assurée en amont par le pipeline officiel BraTS (recalage rigide sur l'atlas SRI24, ré-échantillonnage isotrope 1 mm³ et skull-stripping) ; aucune harmonisation d'intensité inter-scanner n'est appliquée au niveau du jeu de données. La normalisation d'intensité est ensuite assurée par nnU-Net v2 : chaque modalité est normalisée par z-score par patient (schéma `ZScoreNormalization`, calculé sur le volume entier, `use_mask_for_norm=False`), avec cropping automatique, et MedNeXt-B consomme directement ces tenseurs normalisés. Labels de vérité terrain {0, 1, 2, 3}. Partition des patients : validation croisée 5-fold stratifiée par ID. Toutes les métriques ci-dessous sont calculées sur l'ensemble de validation (n = 239 pour le fold 0) ou agrégées sur les 5 folds (n = 1196).

### 4.2 Métriques

**Métriques officielles BraTS-2023 (implémentation de référence).** Toutes les métriques de classement et de détection sont calculées avec l'implémentation de référence du challenge [Saluja *et al.* 2023, *BraTS-2023-Metrics*] (paramètres GLI : dilatation 3, seuil de volume lésionnel 50 voxels, pénalité HD95 de 374 mm par lésion FP/FN), sur des prédictions hors-fold identiques pour tous les modèles (statistiques appariées) :

- **Dice et HD95 *lesion-wise*** — les deux métriques de classement officielles BraTS-2023 (composantes en 26-connectivité, lésions GT fusionnées par dilatation) ;
- **Dice régional *legacy*** (recouvrement WT/TC/ET) et **HD95 de surface** [Nikolov *et al.* 2021] ;
- **sensibilité et spécificité régionales** (niveau voxel) et **comptes de lésions faux-positives / faux-négatives**.

Une HD95 maison antérieure (95ᵉ percentile poolé non standard, à enroulement torique de surface) est **abandonnée** au profit de la HD95 de surface officielle : une métrique réimplémentée à la main ne se justifie que si elle capture ce que les officielles ne capturent pas, ce qui n'est pas le cas ici.

**Critère primaire pré-spécifié et multiplicité.** Le critère primaire est constitué des **deux métriques de classement officielles** (Dice et HD95 lesion-wise), moyennées sur les régions, corrigées Holm sur cette famille de 2 métriques. Toutes les autres métriques et tous les résultats par région sont **exploratoires** : correction Holm sur les 3 régions au sein de chaque métrique, et correction FDR de Benjamini–Hochberg sur l'ensemble de la famille exploratoire (216 tests = métrique × {WT, TC, ET} × paire de modèles) — **106/216 survivent à q < 0,05**, dont tous les effets de consensus et de détection rapportés ci-dessous. Tests de Wilcoxon signés appariés (bilatéraux) sur folds identiques ; taille d'effet rank-biserial appariée r (signe : + favorise le premier modèle). Toutes les p brutes et corrigées sont rapportées ; aucune métrique n'est sélectionnée par convenance. Pipeline : `scripts/eval_lesionwise_kervadec.py` → `scripts/paper_stats.py` ; tableaux par `scripts/make_tables.py` (source de vérité unique `paper_stats.json`).

**Convention de Dice régional.** Le Dice *legacy* par région (WT, TC, ED, ET) suit la convention standard nnU-Net / MONAI : *Dice = 1 si la GT et la prédiction sont toutes deux vides*. Voir §5.5 pour les précautions lors de la comparaison aux leaderboards BraTS challenge.

**Comptage de fragments (définition topologique).** Un **fragment** est une composante connexe (connectivité 26) d'une classe donnée qui n'est **pas la plus grosse** composante de sa classe — c'est-à-dire une CC topologiquement déconnectée du corps tumoral principal. Par classe $c$ sur une prédiction $P$, le nombre de fragments est :
$$\mathrm{fragments}(P, c) = \max(0, \; \mathrm{nb\_CC}(P == c, \text{26-conn}) - 1)$$
Pas de seuil de taille — la 26-connectivité (faces, arêtes, coins partagés) suffit à définir ce qui est topologiquement lié. Cette définition traite symétriquement petites et grandes composantes accessoires.

**Features d'accord inter-modèles (11)** : Dice(Baseline, DistMap) pour WT/TC/ET ; différence volumétrique normalisée $|{|P_B^c|} - {|P_D^c|}| / ({|P_B^c|} + {|P_D^c|})$ pour ET et NCR ; nombre / fraction / taille max des CC DistMap sans recouvrement Baseline, pour ET et NCR.

**Features morphologiques (20)** : volume par région, ratios de volumes, comptage et taille des CC en connectivité 26 pour NCR/ET, élongation du tenseur d'inertie (λ₁/λ₃), sphéricité $(\pi^{1/3}(6V)^{2/3})/S$, rugosité de surface $S_{\mathrm{pred}}/S_{\mathrm{sphère}}$, nombre d'Euler ([scikit-image] `euler_number`, connectivité 3) pour WT/TC/ET, comptage de cavités pour WT (diff `binary_fill_holes`), comptage de CC baseline / distmap par NCR et ET, dispersion des CC d'ET (écart-type des distances centroïdes).

---

## 5. Résultats

### 5.1 Sous les métriques officielles, la tête SDT est nulle sur le classement et neutre en Dice

Évaluation sur les 1196 patients agrégés hors-fold de la CV 5-fold (schedule 300 epochs par fold ; DistMap fold 0 arrêté à 178 ep, les 9 autres entraînements complets), avec l'implémentation officielle BraTS-2023 (§4.2).

**Critères primaires pré-spécifiés** (métriques de classement officielles, moyennées sur les régions, corrigées Holm sur la famille de 2 métriques). La tête SDT n'a aucun effet significatif :

- **Dice lesion-wise** : Δ = −0,003, r = +0,02, p brute = 0,55, **Holm p = 1,0** → non significatif.
- **HD95 lesion-wise** : Δ = +1,12 mm, r = +0,02, p brute = 0,55, **Holm p = 1,0** → non significatif.

Les métriques de classement officielles du challenge **ne séparent pas** DistMap de Baseline. Détail complet (les deux métriques de classement + métriques *legacy*) :

| Métrique | Région | DistMap | Baseline | Δ | r | gains/pertes | p | p(Holm) |
|---|---|---|---|---|---|---|---|---|
| Dice lesion-wise | WT | 0,816 | 0,812 | +0,004 | +0,05 | 609/586 | 0,159 | 0,477 |
|  | TC | 0,862 | 0,870 | −0,008 | +0,01 | 605/584 | 0,741 | 1,000 |
|  | ET | 0,792 | 0,798 | −0,006 | −0,00 | 577/584 | 0,947 | 1,000 |
|  | **avg** | **0,823** | **0,826** | **−0,003** | +0,02 | 622/573 | **0,550** | — |
| HD95 lesion-wise (mm) | WT | 51,11 | 53,09 | −1,98 | +0,10 | 363/294 | 0,023\* | 0,069 |
|  | TC | 28,14 | 24,68 | +3,46 | −0,01 | 246/214 | 0,901 | 0,901 |
|  | ET | 46,76 | 44,89 | +1,87 | −0,06 | 205/212 | 0,324 | 0,649 |
|  | **avg** | **42,01** | **40,89** | **+1,12** | +0,02 | 465/406 | **0,553** | — |
| Dice legacy | WT | 0,936 | 0,935 | +0,001 | +0,01 | 589/606 | 0,716 | 1,000 |
|  | TC | 0,917 | 0,918 | −0,000 | +0,04 | 612/577 | 0,243 | 0,729 |
|  | ET | 0,871 | 0,869 | +0,002 | +0,01 | 582/581 | 0,720 | 1,000 |
|  | **avg** | **0,908** | **0,907** | **+0,001** | +0,04 | 620/575 | **0,237** | — |
| HD95 legacy (mm) | WT | 5,51 | 5,79 | −0,28 | +0,07 | 306/276 | 0,172 | 0,344 |
|  | TC | 5,89 | 6,00 | −0,11 | +0,14 | 242/186 | 0,010\* | 0,030† |
|  | ET | 11,54 | 11,62 | −0,08 | +0,07 | 178/163 | 0,270 | 0,344 |
|  | **avg** | **7,65** | **7,81** | **−0,16** | +0,11 | 438/365 | **0,008\*** | — |

Δ = DistMap − Baseline. r = rank-biserial apparié (+ favorise DistMap). \* p brute < 0,05 ; † p Holm < 0,05 (sur les 3 régions). n = 1196. Test de Wilcoxon signé apparié bilatéral.

Le Dice régional *legacy* est **neutre** (avg Δ = +0,001, p = 0,24) : l'avantage Dice rapporté à budget d'entraînement réduit ne survit pas à la convergence. La seule métrique de recouvrement à bouger est la HD95 *legacy* régionale, qui s'améliore légèrement en moyenne (Δ = −0,16 mm, p = 8 × $10^{-3}$), portée par le cœur tumoral (TC −0,11 mm, Holm 0,030†) ; en lesion-wise, la HD95 s'améliore sur la tumeur entière (WT −1,98 mm, p = 0,023) mais le gain est annulé sur TC/ET, d'où une moyenne nulle — cohérent avec le compromis de détection ci-dessous.

**Le seul effet robuste : un déplacement orienté rappel.** Sur la détection lésionnelle, le signal est faible en magnitude absolue mais d'une cohérence directionnelle remarquable (rank-biserial, gains/pertes) et survit à la correction FDR :

| Métrique | Région | DistMap | Baseline | Δ | r | gains/pertes | p | p(Holm) |
|---|---|---|---|---|---|---|---|---|
| FP lésions | WT | 0,297 | 0,337 | −0,040 | +0,08 | 133/108 | 0,159 | 0,159 |
|  | TC | 0,188 | 0,132 | +0,056 | −0,37 | 34/65 | 0,005\* | 0,014† |
|  | ET | 0,836 | 0,718 | +0,118 | −0,13 | 73/106 | 0,051 | 0,103 |
|  | **avg** | **0,440** | **0,396** | **+0,045** | −0,08 | 180/201 | 0,177 | — |
| FN lésions | WT | 0,075 | 0,080 | −0,005 | +0,49 | 8/2 | 0,058 | 0,137 |
|  | TC | 0,030 | 0,037 | −0,007 | +0,71 | 10/3 | 0,046\* | 0,137 |
|  | ET | 0,035 | 0,042 | −0,007 | +0,41 | 10/3 | 0,046\* | 0,137 |
|  | **avg** | **0,047** | **0,053** | **−0,006** | +0,57 | 16/8 | **0,008\*** | — |
| Sensibilité | WT | 0,931 | 0,929 | +0,002 | +0,16 | 667/525 | 1,7e-06\* | 3,3e-06† |
|  | TC | 0,921 | 0,921 | −0,001 | +0,14 | 685/500 | 3,4e-05\* | 3,4e-05† |
|  | ET | 0,880 | 0,877 | +0,004 | +0,20 | 681/471 | 2,7e-09\* | 8,0e-09† |
|  | **avg** | **0,910** | **0,909** | **+0,002** | +0,20 | 697/498 | **2,0e-09\*** | — |
| Spécificité | WT | 1,000 | 1,000 | −0,000 | −0,22 | 494/701 | 4,0e-11\* | 8,0e-11† |
|  | TC | 1,000 | 1,000 | +0,000 | −0,18 | 505/678 | 4,2e-08\* | 4,2e-08† |
|  | ET | 1,000 | 1,000 | −0,000 | −0,28 | 471/702 | 1,5e-16\* | 4,6e-16† |
|  | **avg** | **1,000** | **1,000** | **−0,000** | −0,26 | 456/739 | **1,2e-14\*** | — |

La tête SDT rend le modèle **plus sensible** — sensibilité régionale en hausse sur les 3 régions (avg Δ = +0,002, r = +0,20, p = 2,0 × $10^{-9}$) et moins de lésions manquées (FN avg Δ = −0,006, p = 8,3 × $10^{-3}$) — au prix d'une **perte de spécificité** systématique (avg r = −0,26, p = 1,2 × $10^{-14}$) : davantage de lésions fallacieuses sur le cœur tumoral et le rehaussement (FP TC Δ = +0,056, Holm 0,014† ; FP ET Δ = +0,118, p = 0,051), tout en réduisant celles de la tumeur entière (FP WT Δ = −0,040). On recadre donc la tête SDT comme un **régularisateur de frontière orienté rappel**, non un booster de Dice.

**Implication.** DistMap produit des prédictions *différentes* de Baseline (les deux modèles divergent sur 1195/1196 patients) mais leurs désaccords se compensent sur les métriques de recouvrement. La contrepartie « perte de spécificité » de ce déplacement a une signature topologique précise — l'apparition de petites composantes connexes fallacieuses — qui fait l'objet de la section suivante.

### 5.2 DistMap introduit des fragments fallacieux

L'inspection qualitative des prédictions DistMap visait des frontières plus nettes — comportement attendu d'une loss sensible à la distance. Au lieu de cela, les prédictions DistMap montrent systématiquement davantage de composantes connexes isolées que Baseline — la **manifestation topologique de la perte de spécificité** quantifiée en §5.1 (hausse des lésions FP sur TC/ET). Quantification topologique sur les 1196 patients de la CV 5-fold (moyennes par patient, fragments = CC − 1 par classe, 26-connectivité) :

| Fragments / patient | Baseline | DistMap | **CC-Consensus** | Δ D−B | Δ F−D | Réduction F/D |
|---|---|---|---|---|---|---|
| **NCR** | 79,7 | 93,3 | **31,3** | +13,6 | −61,9 | **−66 %** |
| **ED** | 28,9 | 35,3 | **17,0** | +6,4 | −18,3 | **−52 %** |
| **ET** | 2,15 | 2,33 | **1,57** | +0,18 | −0,76 | **−33 %** |

Tests de Wilcoxon signés unilatéraux sur les 1196 patients :

- **DistMap inflate les fragments vs Baseline** sur les 3 classes : NCR (p = 5,5 × $10^{-42}$), ED (p = 2,0 × $10^{-49}$), ET (p = 1,3 × $10^{-3}$). L'artefact est statistiquement massif et systématique.
- **CC-Consensus réduit les fragments vs DistMap** : NCR (p < $10^{-189}$), ED (p < $10^{-162}$), ET (p = 1,1 × $10^{-53}$).
- **CC-Consensus réduit aussi vs Baseline** : NCR (p < $10^{-188}$), ED (p < $10^{-144}$), ET (p = 1,4 × $10^{-30}$) — le filtre post-hoc corrige même les fragments hérités du Baseline quand DistMap n'y avait pas d'overlap.

Cet effet **ne se voit pas sur le Dice** (§5.3 : Dice moyens B / D / F à 0,9078 / 0,9088 / 0,9090, différences dans le bruit) — des fragments de quelques voxels n'impactent pas une métrique de recouvrement quand le volume tumoral médian fait ~90 000 voxels. C'est précisément pourquoi la littérature passée n'avait pas rapporté l'artefact : le Dice est aveugle à la topologie.

![Figure 1 — Comptage moyen de fragments par patient (composantes connexes non-principales, 26-connectivité, sans seuil de taille) pour chaque classe × variante, sur les 1196 patients de la CV 5-fold. DistMap inflate le nombre de fragments NCR de +17 % par rapport à Baseline ; le filtre CC-consensus le ramène à 31,3 — une réduction de **66 %** par rapport à DistMap (Wilcoxon p < $10^{-189}$).](figures/fragment_counts.png){width=90%}

**Illustrations qualitatives sur les six cas de référence.** Les figures 2–7 ci-dessous montrent, pour chacun des six patients épinglés (C1–C6) du viewer 3D compagnon, les segmentations produites par GT / Baseline / DistMap / CC-Consensus, vue sagittale gauche, régions tumorales seules (Brain masqué pour focus). Chaque figure illustre l'un des six modes de comportement identifiés en Annexe E.

**Note sur le rendu 3D (deux pipelines).** Le viewer propose un mode lissé et un mode voxel, chacun servi par un pipeline distinct selon la nature du mesh.

*Mode voxel (vérité brute).* *Greedy voxel meshing* : chaque voxel de la segmentation est converti en une face cubique fusionnée avec ses voisins coplanaires. Aucune interpolation, aucun lissage — ce que le modèle a prédit au voxel près. Sert de référence de vérité quand on veut compter ou localiser précisément.

*Mode lissé (défaut, figures 2–7), meshes principaux.* Pipeline `fill_holes + dilation + marching cubes` : le masque binaire est pré-rempli (`scipy.ndimage.binary_fill_holes` pour supprimer les cavités internes — ventricules, sulci), dilaté d'un voxel (`binary_dilation`, 1 itération) pour adoucir les escaliers du marching cubes, puis marching-cubed au seuil 0,5. C'est le pipeline utilisé pour les meshes des corps tumoraux et du Brain (figures 2–7).

*Mode lissé, fragments et cavités.* Pour les petites composantes (< 4 voxels jusqu'aux fragments sub-voxel), un pipeline **champ de distance signée** (*signed distance field*) distinct est employé : dilatation 26-connectivité pour bridger les voxels touchant par coin/arête, transformée de distance euclidienne intérieure et extérieure (`scipy.ndimage.distance_transform_edt`) pour construire le champ de distance signée, upsampling spline cubique ×2 pour résolution sub-voxel, puis marching cubes au niveau iso = −0,3 (calibré empiriquement pour préservation volumique). Ce pipeline est **nécessaire pour les petits fragments** car un marching cubes naïf au seuil 0,5 sur un masque 1-voxel rend 1/6 du volume réel (erreur ×6) alors que le champ de distance signée préserve le volume à ±5 % sur toutes les tailles.

*Propriété commune aux deux pipelines lisses.* Ils **préservent la topologie** (mêmes composantes connexes, même comptage en 26-connectivité que le mode voxel) ; la différence est purement cosmétique. Le lissage est le défaut parce qu'il produit un rendu proche de la console clinique ; le mode voxel reste un clic de distance pour toute inspection qui requiert la vérité voxel-exacte.

\clearpage

![Figure 2 — Cas **C1** (patient `BraTS-GLI-00048-001`) : Baseline > DistMap. La GT ne contient que de l'œdème (vert) ; Baseline reproduit correctement ce pattern. **DistMap hallucine une masse NCR** (rouge) au sein de l'œdème — typique des cas où la pression SDT engendre des composantes fallacieuses. **CC-Consensus supprime cette hallucination** car la composante NCR de DistMap n'a aucun recouvrement avec la prédiction Baseline (veto), restaurant quasi intégralement le score (Dice avg 0,308 → 0,973).](figures/patient_C1_00048-001_4models.png){width=100%}

\clearpage

![Figure 3 — Cas **C2** (patient `BraTS-GLI-01437-000`) : DistMap > Baseline. Baseline sous-segmente la tumeur (Dice 0,589) tandis que DistMap capture correctement l'extension tumorale (Dice 0,923) grâce à sa sensibilité de frontière. **CC-Consensus égale DistMap** (0,923) car aucune composante n'est hallucinée à supprimer — le filtre préserve la prédiction de meilleure qualité quand elle est confirmée par Baseline.](figures/patient_C2_01437-000_4models.png){width=100%}

\clearpage

![Figure 4 — Cas **C3** (patient `BraTS-GLI-01428-000`) : B < F < D, filtre tiré côté baseline. Baseline (0,618) et DistMap (0,656) encadrent le résultat CC-Consensus (0,645). Le filtre supprime certaines composantes DistMap légitimes que Baseline ne prédit pas, dégradant légèrement le score vers Baseline. C'est le mode de dégradation le plus courant (390 / 1196 patients, 32,6 %).](figures/patient_C3_01428-000_4models.png){width=100%}

\clearpage

![Figure 5 — Cas **C4** (patient `BraTS-GLI-00017-001`) : D < F < B, sauvetage partiel. Baseline est excellent (0,991) ; DistMap est à moitié hallucinée (0,657). CC-Consensus supprime les composantes DistMap fallacieuses et récupère une partie de la qualité Baseline (0,890), sans pouvoir l'atteindre puisqu'il part des voxels de DistMap.](figures/patient_C4_00017-001_4models.png){width=100%}

\clearpage

![Figure 6 — Cas **C5** (patient `BraTS-GLI-01530-000`) : F < min(B, D), le filtre casse. Baseline = 0,241, DistMap = 0,541, CC-Consensus = 0,169. Le filtre **supprime une grosse composante DistMap légitime** car Baseline a raté la tumeur et ne peut pas la confirmer. 463 / 1196 patients (38,7 %) — c'est le principal mode de défaillance du filtre, quand Baseline et DistMap échouent différemment.](figures/patient_C5_01530-000_4models.png){width=100%}

\clearpage

![Figure 7 — Cas **C6** (patient `BraTS-GLI-00540-000`) : synergie nette. Baseline (0,785) et DistMap (0,795) sont tous deux compétents mais aucun n'est parfait. **CC-Consensus combine leurs forces** pour atteindre 0,869 — strictement supérieur aux deux parents. C'est le comportement recherché sur 157/1196 patients (13,1 %) où le filtre dépasse ses sources.](figures/patient_C6_00540-000_4models.png){width=100%}

### 5.3 Le CC-consensus bat la baseline sur les métriques officielles

C'est la conclusion centrale du papier. En ne conservant que les composantes DistMap corroborées par un second modèle (§3.3), le filtre CC-consensus est **la seule configuration évaluée ici à améliorer significativement les deux métriques de classement officielles** par rapport à Baseline. Deux modèles de veto sont évalués : Baseline (`CC(D∩B)`) et la tête Kervadec plus spécifique (`CC(D∩K)`, Paper 2) ; ils sont statistiquement équivalents sur le critère primaire (`CC(D∩K)` vs `CC(D∩B)` : p = 0,76 / 0,80 sur Dice / HD95 lesion-wise).

**Critères primaires officiels — `CC(D∩B)` vs Baseline** (n = 1196, moyenne sur régions, Holm) :

- **Dice lesion-wise** : Δ = +0,024, r = +0,27, **Holm p = 4,5 × $10^{-16}$** → significatif.
- **HD95 lesion-wise** : Δ = −9,49 mm, r = +0,42, **Holm p = 5,7 × $10^{-26}$** → significatif.

| Métrique | Région | CC(D∩B) | Baseline | Δ | r | gains/pertes | p | p(Holm) |
|---|---|---|---|---|---|---|---|---|
| Dice lesion-wise | WT | 0,854 | 0,812 | +0,042 | +0,10 | 577/617 | 0,004\* | 0,008† |
|  | TC | 0,880 | 0,870 | +0,011 | +0,07 | 605/582 | 0,051 | 0,051 |
|  | ET | 0,817 | 0,798 | +0,019 | +0,15 | 618/540 | 6,2e-06\* | 1,9e-05† |
|  | **avg** | **0,850** | **0,826** | **+0,024** | +0,27 | 680/514 | **4,5e-16\*** | — |
| HD95 lesion-wise (mm) | WT | 36,49 | 53,09 | −16,61 | +0,39 | 403/226 | 1,1e-17\* | 3,2e-17† |
|  | TC | 20,68 | 24,68 | −4,00 | +0,20 | 238/178 | 4,4e-04\* | 4,4e-04† |
|  | ET | 37,03 | 44,89 | −7,86 | +0,34 | 220/149 | 1,6e-08\* | 3,2e-08† |
|  | **avg** | **31,40** | **40,89** | **−9,49** | +0,42 | 532/300 | **5,7e-26\*** | — |
| Dice legacy | WT | 0,935 | 0,935 | −0,000 | −0,12 | 507/687 | 3,9e-04\* | 0,001† |
|  | TC | 0,918 | 0,918 | −0,000 | +0,01 | 589/598 | 0,739 | 1,000 |
|  | ET | 0,872 | 0,869 | +0,003 | +0,01 | 583/578 | 0,673 | 1,000 |
|  | **avg** | **0,908** | **0,907** | **+0,001** | −0,01 | 588/606 | **0,680** | — |
| HD95 legacy (mm) | WT | 5,67 | 5,79 | −0,12 | +0,06 | 311/269 | 0,181 | 0,543 |
|  | TC | 6,21 | 6,00 | +0,21 | +0,07 | 217/193 | 0,227 | 0,543 |
|  | ET | 11,59 | 11,62 | −0,03 | −0,02 | 168/170 | 0,780 | 0,780 |
|  | **avg** | **7,82** | **7,81** | **+0,02** | +0,05 | 419/374 | **0,270** | — |

Δ = CC(D∩B) − Baseline. r = rank-biserial apparié (+ favorise CC(D∩B)). \* p brute < 0,05 ; † p Holm < 0,05. n = 1196.

Le gain est **purement lesion-wise** : le Dice régional *legacy* reste neutre (avg Δ = +0,001, p = 0,68) et la HD95 *legacy* aussi (avg Δ = +0,02 mm, p = 0,27). Le consensus ne change pas la qualité de segmentation de la tumeur principale — il **nettoie la détection lésion par lésion**. Mécaniquement, il **supprime ~41 % des lésions fallacieuses** de Baseline (FP lésions avg 0,396 → 0,234, r = +0,85, p = 6,0 × $10^{-34}$) à coût de rappel négligeable (FN avg +0,003 ; sensibilité avg +0,001, p = 0,026) :

| Métrique | Région | CC(D∩B) | Baseline | Δ | r | gains/pertes | p | p(Holm) |
|---|---|---|---|---|---|---|---|---|
| FP lésions | WT | 0,146 | 0,337 | −0,191 | +0,79 | 152/22 | 8,3e-21\* | 2,5e-20† |
|  | TC | 0,080 | 0,132 | −0,052 | +0,68 | 44/6 | 5,6e-06\* | 5,6e-06† |
|  | ET | 0,474 | 0,718 | −0,244 | +0,86 | 100/9 | 4,2e-16\* | 8,3e-16† |
|  | **avg** | **0,234** | **0,396** | **−0,162** | +0,85 | 237/29 | **6,0e-34\*** | — |
| FN lésions | WT | 0,083 | 0,080 | +0,003 | −1,00 | 0/3 | 0,083 | 0,137 |
|  | TC | 0,040 | 0,037 | +0,003 | −1,00 | 0/4 | 0,046\* | 0,137 |
|  | ET | 0,045 | 0,042 | +0,003 | −1,00 | 0/4 | 0,046\* | 0,137 |
|  | **avg** | **0,056** | **0,053** | **+0,003** | −1,00 | 0/10 | 0,003\* | — |
| Sensibilité | WT | 0,929 | 0,929 | +0,000 | −0,02 | 570/624 | 0,469 | 0,469 |
|  | TC | 0,919 | 0,921 | −0,002 | −0,08 | 570/613 | 0,012\* | 0,024† |
|  | ET | 0,881 | 0,877 | +0,004 | +0,20 | 676/474 | 8,2e-09\* | 2,4e-08† |
|  | **avg** | **0,910** | **0,909** | **+0,001** | +0,07 | 635/559 | 0,026\* | — |
| Spécificité | WT | 1,000 | 1,000 | −0,000 | −0,17 | 520/672 | 7,5e-07\* | 1,5e-06† |
|  | TC | 1,000 | 1,000 | +0,000 | +0,02 | 606/570 | 0,587 | 0,587 |
|  | ET | 1,000 | 1,000 | −0,000 | −0,27 | 475/694 | 1,5e-15\* | 4,6e-15† |
|  | **avg** | **1,000** | **1,000** | **−0,000** | −0,19 | 492/702 | 2,7e-08\* | — |

**Honnêteté sur la HD95 lesion-wise.** Une large part du gain HD95 lesion-wise (−9,49 mm) provient de ce que la métrique officielle pénalise chaque lésion fallacieuse de **374 mm** : retirer ces lésions retire ces pénalités. On l'énonce explicitement plutôt que de laisser entendre un gain de précision de frontière sur les vraies lésions ; le gain Dice lesion-wise (+0,024), lui, est un gain de détection authentique. Le veto Kervadec est équivalent (`CC(D∩K)` vs Baseline : Dice lesion-wise +0,024, Holm p = 1,2 × $10^{-11}$ ; HD95 lesion-wise −9,95 mm, Holm p = 2,3 × $10^{-20}$) en préservant marginalement mieux le rappel (FN ≈ +0,000 vs Baseline), cohérent avec sa plus grande spécificité (Paper 2).

**Vue complémentaire — recouvrement régional et distances par classe.** Au niveau du recouvrement régional, ce nettoyage lésionnel est par construction invisible (le Dice régional est dominé par le volume de la tumeur, insensible aux petites composantes), mais il laisse une trace sur les distances *legacy* par classe — notamment HD95 NCR, la classe où les fragments prolifèrent.

Agrégation des prédictions hors-fold sur les 5 folds (n = 1196), au niveau du recouvrement régional :

| Stratégie | Dice avg | Δ vs CC-consensus par défaut |
|---|---|---|
| Baseline seule | 0,9078 | −0,00115 |
| DistMap seule | 0,9088 | −0,00020 |
| CC-Consensus (règle par défaut) | 0,9090 | 0 (réf.) |
| **Oracle au niveau patient** | 0,9131 | **+0,00412** |
| **Oracle par classe** | 0,9139 | **+0,00494** |

Classification par patient (en notant $F$ la sortie du CC-consensus) :

| Cas | Effectif | % |
|---|---|---|
| Baseline bat DistMap (B > D) | 602 | 50,3 % |
| DistMap bat Baseline (D > B) | 593 | 49,6 % |
| Sortie du filtre entre B et D | 559 | 46,7 % |
| **Filtre < les deux (dégradation)** | **463** | **38,7 %** |
| **Filtre > les deux (synergie)** | **157** | **13,1 %** |

Le filtre CC-consensus dégrade le score patient dans 38,7 % des cas contre 13,1 % de synergie. Par région, CC-Consensus l'emporte strictement sur 2,7 % des patients pour WT, **21,7 % pour TC** et 6,9 % pour ET. Le bénéfice du filtre en Dice est donc concentré sur TC ; pour WT et ET, le choix Baseline-seule ou DistMap-seule domine déjà.

**Qualité de frontière HD95 par classe (diagnostic).** En complément du HD95 régional *legacy* officiel (tableau ci-dessus, WT/TC/ET tous n.s.), on rapporte les distances de Hausdorff à 95 % **par classe individuelle** (NCR, ED) où vivent les fragments — toutes calculées avec l'implémentation standard `medpy` (`medpy.metric.binary.hd95`), comme l'ensemble des HD95 de ce travail (n varie par ligne selon le nombre de patients à HD95 fini sur la classe) :

| Région / classe | Composition | Baseline | DistMap | CC-Consensus | Δ CC-Cons. vs DistMap |
|---|---|---|---|---|---|
| WT | {1, 2, 3} | 3,99 mm | 3,99 mm | 4,03 mm | +0,05 mm, n.s. |
| TC | {1, 3} | 3,14 mm | 2,89 mm | 2,96 mm | +0,07 mm, n.s. |
| ET | {3} | 2,64 mm | 2,59 mm | 2,68 mm | +0,09 mm, n.s. |
| **NCR** | {1} | 4,89 mm | 4,86 mm | **4,48 mm** | **−0,38 mm, p = 5,7 × $10^{-14}$** |
| ED | {2} | 4,25 mm | 4,33 mm | 4,21 mm | −0,12 mm, n.s. (p = 0,82) |

Test de Wilcoxon signé apparié, hypothèse unilatérale HD95(CC-Consensus) < HD95(DistMap). n = 1160 pour WT/TC/ET (patients à HD95 fini sur les 3 régions emboîtées), 1153 pour NCR, 1193 pour ED.

**Le signal est sur NCR** : CC-Consensus réduit HD95 NCR de 0,38 mm (p = 5,7 × $10^{-14}$) — confirmation quantitative directe que la suppression des fragments améliore la qualité de frontière sur la classe où ils prolifèrent majoritairement (NCR : ×1,5 plus de fragments DistMap vs Baseline, cf. §5.2). Le gain **ne se propage pas** aux régions emboîtées : les HD95 WT, TC et ET sont inchangés (tous n.s.), car la distance de Hausdorff à 95 % sur les grandes régions est dominée par le corps tumoral principal et bouge à peine quand on retire de petits fragments NCR. Sur ED, la réduction de fragments (−61 %) ne se traduit pas non plus en gain HD95 significatif — l'œdème a une variabilité intrinsèque de frontière qui domine les outliers introduits par les fragments.

Le CC-consensus délivre donc un gain quantitatif mesurable sur **HD95 NCR spécifiquement** — la métrique per-class sur la région où les fragments prolifèrent —, là où le Dice de recouvrement reste insensible. Cliniquement, NCR est précisément la région où des fragments fallacieux peuvent induire en erreur un radiothérapeute sur l'emprise de la nécrose tumorale.

\clearpage

![Figure 8 — 1196 patients de validation représentés dans le plan de désaccord entre modèles : x = Dice(DistMap) − Dice(Baseline) (une valeur positive signifie que DistMap l'emporte au niveau patient), y = Dice(CC-Cons.) − max(Dice(B), Dice(D)) (une valeur négative signifie que le filtre CC-consensus est pire que chaque modèle pris isolément). Le nuage *rouge* C5 sous y = 0 rassemble 38,7 % des patients pour lesquels le filtre dégrade le score ; les points *verts* C6 au-dessus de y = 0 ne représentent que 13,1 %. Cette asymétrie visuelle est l'observation empirique centrale du papier.](figures/case_scatter.png){width=100%}

### 5.4 Le plafond hard-label est saturé (en Dice de recouvrement régional)

Cette analyse porte spécifiquement sur le **Dice de recouvrement régional** : elle **ne borne pas** le gain lesion-wise officiel établi en §5.3 (lequel récompense la suppression de lésions fallacieuses, invisible au Dice régional, et que le consensus réalise déjà). L'écart entre CC-consensus par défaut et oracle par classe (+0,005 Dice avg régional) borne supérieurement le gain de toute politique de sélection au niveau patient ou région à partir des trois prédictions {B, D, F}. On évalue trois familles de politiques en CV 5-fold (seuil taille-adaptatif sur τ $\in$ {20, 50, 100, 200, 500, ∞} voxels ; meta-classifieurs RF/LR/GBM × patient/région sur 31 features ; règle à une feature par recherche exhaustive) ; **aucune ne bat robustement le CC-consensus par défaut**. La règle à une feature, attirante en fit toutes données (+0,00119), s'effondre en CV 5-fold (−0,00096) : la meilleure feature et le meilleur seuil changent entre folds (TC : 4 features distinctes sur 5 folds ; ET : 4 features distinctes). Un RandomForest par région atteint 50 %, 43 %, 51 % de précision argmax (vs 33 % au hasard), ce qui confirme la présence de signal — mais lorsque le classifieur se trompe, il choisit un modèle strictement pire, aboutissant à un bilan net négatif.

Le détail complet — tableau des 7 politiques évaluées, importances RF par région, classification du sweep adaptatif, partition par fold de la règle à une feature — est en **Annexe B**. Le plafond hard-label est essentiellement atteint ; combler l'écart à l'oracle nécessite un vote probabiliste au niveau voxel ou une diversité architecturale (§6.3).

### 5.5 Positionnement par rapport aux gagnants BraTS 2023 GLI

Le CC-consensus atteint Dice avg = 0,909 (WT 0,935, TC 0,919, ET 0,873) en CV 5-fold sur 1196 patients, avec un setup mono-modèle (pas d'ensemble multi-fold, pas de TTA, une seule architecture). C'est à moins d'un point de pourcentage de la fourchette des gagnants publiés BraTS 2023 GLI sur test set privé (0,87–0,89 Dice avg ; Ferreira *et al.* 2024). Deux précautions à la comparaison directe : (i) jeu d'évaluation différent (CV 5-fold sur train + val vs test set privé, écart typique 1–2 pp en défaveur du test set) ; (ii) convention Dice = 1 sur région vide (nnU-Net / MONAI) qui inflate ET de ~0,003 par rapport à la convention lesion-wise du challenge (32/1196 patients sans ET en GT).

On ne revendique pas un nouvel état de l'art ; le filtre CC-consensus est **orthogonal à l'ensembling** — la réduction de fragments est un gain qui se cumule avec les astuces multi-fold / TTA classiques sans les dupliquer.

### 5.6 Robustesse à la graine d'entraînement (3 graines, fold 0)

L'analyse §5.1 utilise la graine 42 pour tous les folds. Pour estimer la variance inter-graine et vérifier que la non-significativité n'est pas un artefact d'initialisation, trois entraînements indépendants (graines 1, 2, 3) sont conduits pour Baseline et DistMap (λ=0,1, meilleur λ selon l'Annexe A) sur fold 0 (n≈240 patients), 300 epochs chacun.

**Dice de validation fold 0 (nnU-Net, 240 patients) :**

| Config | Graine 1 | Graine 2 | Graine 3 | Moy. ± σ |
|---|---|---|---|---|
| Baseline | 0,9078 | 0,9066 | 0,9078 | **0,9074 ± 0,0007** |
| DistMap (λ=0,1) | 0,9074 | 0,9043 | 0,9021 | **0,9046 ± 0,0027** |
| Δ (B − D) | +0,04 pp | +0,23 pp | +0,57 pp | +0,28 pp |

Test t apparié (n=3 graines) : t=1,83, p=0,21 — non significatif. La non-significativité constatée en CV 5-fold (§5.1, Δ=+0,09 pp, p>0,25) se confirme sur les trois graines : Baseline devance légèrement DistMap dans les trois cas sans qu'aucun écart n'atteigne 1 pp ou le seuil de significativité.

Deux observations :

- **Instabilité DistMap (×4).** La variance inter-graine de DistMap (σ=0,0027) est 4× celle de Baseline (σ=0,0007). La loss SDT auxiliaire rend l'entraînement sensiblement plus sensible à l'initialisation. Ceci explique l'avantage apparent de DistMap observé à la graine de référence (42) dans l'Annexe A (+0,13 pp à λ=0,1) : il s'agit d'une fluctuation d'initialisation, non d'un signal robuste.

- **Avantage baseline monotone.** L'écart Δ(B−D) croît de +0,04 pp (graine 1) à +0,57 pp (graine 3). Avec n=3, aucune tendance causale ne peut être établie ; l'observation est cohérente avec la variance aléatoire plus élevée de DistMap.

**Métriques officielles BraTS-2023 et CC-consensus (D$\cap$B) par graine.** Évaluation complète sur les 3×240 patients (720 paires valides) avec les métriques officielles *BraTS-2023-Metrics* (Legacy Dice, LW Dice, HD95), sur des prédictions vérifiées exemptes de fragments résiduels — la baseline lesion-wise est ainsi identique à celle rapportée dans le paper 3 sur les mêmes prédictions. Sur Legacy Dice, ni DistMap ni le consensus ne se distinguent de Baseline (p > 0,35 Wilcoxon partout). Le bénéfice se concentre sur la détection lésion par lésion de la tumeur entière : le filtre CC-consensus améliore significativement **LW Dice WT** (0,810 → 0,853, +4,28 pp, p < $10^{-4}$ Wilcoxon) et **LW HD95 WT** (54,5 → 37,3 mm, −17,2 mm, p < $10^{-4}$), sans aucun coût sur le Dice volumétrique. DistMap seul améliore déjà partiellement **LW Dice WT** (+1,54 pp, p = 0,041 Wilcoxon), le consensus amplifiant ce gain.

**Tableau A — Baseline vs DistMap (λ=0,1), métriques officielles, fold 0, 3 graines**

| Métrique | Région | Baseline (moy.±σ) | DistMap (moy.±σ) | Δ | p t-test | p Wilcoxon |
|---|---|---|---|---|---|---|
| Legacy Dice | WT | 0,9361 ± 0,0006 | 0,9359 ± 0,0012 | −0,02 pp | 0,89 | 0,44 |
| Legacy Dice | TC | 0,9208 ± 0,0006 | 0,9170 ± 0,0040 | −0,38 pp | 0,35 | 0,36 |
| Legacy Dice | ET | 0,8668 ± 0,0029 | 0,8616 ± 0,0017 | −0,53 pp | 0,12 | 0,64 |
| LW Dice | WT | 0,8103 ± 0,0080 | 0,8257 ± 0,0081 | +1,54 pp | 0,27 | **0,041** |
| LW Dice | TC | 0,8670 ± 0,0067 | 0,8649 ± 0,0069 | −0,21 pp | 0,75 | 0,54 |
| LW Dice | ET | 0,8071 ± 0,0109 | 0,7997 ± 0,0074 | −0,74 pp | 0,32 | 0,97 |
| Legacy HD95 | WT | 6,42 ± 0,28 mm | 6,04 ± 0,47 mm | −0,38 mm | 0,35 | 0,55 |
| Legacy HD95 | TC | 5,95 ± 0,90 mm | 6,02 ± 0,65 mm | +0,07 mm | 0,95 | 0,96 |
| Legacy HD95 | ET | 13,85 ± 1,33 mm | 15,41 ± 0,64 mm | +1,56 mm | 0,19 | 0,98 |
| LW HD95 | WT | 54,52 ± 2,84 mm | 48,04 ± 3,45 mm | −6,48 mm | 0,24 | 0,071 |
| LW HD95 | TC | 26,82 ± 2,73 mm | 26,12 ± 2,28 mm | −0,70 mm | 0,86 | 0,61 |
| LW HD95 | ET | 41,59 ± 4,68 mm | 44,26 ± 2,40 mm | +2,67 mm | 0,44 | 1,00 |

Sur les 12 comparaisons Baseline/DistMap, seule **LW Dice WT** franchit le seuil au test de Wilcoxon (+1,54 pp, p = 0,041) ; les onze autres restent non significatives (p > 0,07). DistMap déplace donc déjà légèrement la détection lésion-wise de la tumeur entière, mais ce signal seul est fragile (non significatif au test t apparié, p = 0,27). L'instabilité TC constatée sur le Dice nnU-Net (σ×4) se reflète ici par une σ DistMap×6 sur Legacy Dice TC.

**Tableau B — CC-consensus (D$\cap$B) vs Baseline, métriques officielles, fold 0, 3 graines**

| Métrique | Région | Baseline (moy.±σ) | CC(D$\cap$B) (moy.±σ) | Δ | p t-test | p Wilcoxon |
|---|---|---|---|---|---|---|
| Legacy Dice | WT | 0,9361 ± 0,0006 | 0,9359 ± 0,0012 | −0,02 pp | 0,90 | 0,41 |
| Legacy Dice | TC | 0,9208 ± 0,0006 | 0,9184 ± 0,0025 | −0,24 pp | 0,39 | 0,57 |
| Legacy Dice | ET | 0,8668 ± 0,0029 | 0,8629 ± 0,0008 | −0,39 pp | 0,13 | 0,91 |
| LW Dice | WT | 0,8103 ± 0,0080 | **0,8531 ± 0,0041** | **+4,28 pp** | **0,017** | **5,5×$10^{-5}$** |
| LW Dice | TC | 0,8670 ± 0,0067 | 0,8668 ± 0,0034 | −0,02 pp | 0,97 | 0,85 |
| LW Dice | ET | 0,8071 ± 0,0109 | 0,8018 ± 0,0047 | −0,54 pp | 0,42 | 0,69 |
| Legacy HD95 | WT | 6,42 ± 0,28 mm | 6,48 ± 0,05 mm | +0,06 mm | 0,81 | 0,82 |
| Legacy HD95 | TC | 5,95 ± 0,90 mm | 5,50 ± 0,12 mm | −0,45 mm | 0,56 | 0,67 |
| Legacy HD95 | ET | 13,85 ± 1,33 mm | 14,89 ± 0,74 mm | +1,04 mm | 0,14 | 0,60 |
| LW HD95 | WT | 54,52 ± 2,84 mm | **37,31 ± 2,18 mm** | **−17,21 mm** | **0,015** | **6,0×$10^{-5}$** |
| LW HD95 | TC | 26,82 ± 2,73 mm | 25,42 ± 1,92 mm | −1,39 mm | 0,71 | 0,63 |
| LW HD95 | ET | 41,59 ± 4,68 mm | 43,48 ± 1,32 mm | +1,89 mm | 0,57 | 0,87 |

Le filtre CC-consensus reproduit sur fold 0 multi-graine les gains lesion-wise déjà observés en CV 5-fold (§5.3) et les concentre sur la tumeur entière : amélioration significative et robuste de **LW Dice WT** (+4,28 pp) et **LW HD95 WT** (−17,2 mm), avec p < $10^{-4}$ au test de Wilcoxon et p < 0,02 au test t apparié sur n=3 graines, sans aucun coût sur le Legacy Dice (Δ < 0,1 pp, non significatif). **Aucune tendance n'est observée sur TC ni ET** (|Δ| < 1,4 pp et < 1,4 mm, p > 0,6) : le bénéfice est purement WT.

Ce recadrage est délibéré, et il est à la fois plus honnête et plus cohérent cliniquement. Plus honnête statistiquement : une version antérieure de cette analyse rapportait une « tendance » d'amélioration sur TC, mais elle reposait sur une évaluation où des fragments parasites résiduels dégradaient artificiellement la baseline lesion-wise (LW Dice WT 0,78 au lieu de 0,81) ; sur des prédictions vérifiées sans fragments, cette tendance TC disparaît, et la baseline coïncide exactement avec celle du paper 3. Plus cohérent cliniquement : le bénéfice du consensus est un **nettoyage de faux positifs de détection** — la suppression de fausses petites lésions — et non un gain de précision volumétrique (le Legacy Dice est inchangé). Il est donc logique qu'il se manifeste précisément là où ces fragments abondent, sur la tumeur entière (WT), la région la plus étendue et la plus propice aux composantes de bord, et qu'il soit absent sur les régions compactes (TC, ET). Le consensus améliore la fiabilité de détection lésion par lésion sans modifier la qualité de segmentation de la tumeur principale.

---

## 6. Discussion

### 6.1 Pourquoi DistMap génère des fragments

Mécanisme plausible — non démontré : la pression SDT sensibilise le réseau à de petits signaux *boundary-like* dans les tissus de transition (interfaces œdème–substance blanche, cavités post-chirurgicales, NCR hétérogène), produisant des voxels à forte réponse SDT qui survivent parfois à l'argmax sous forme de blobs isolés. Cette hypothèse est cohérente avec deux observations : l'augmentation du comptage de fragments est concentrée sur NCR et ED (régions aux frontières les plus longues et irrégulières), et beaucoup plus faible sur ET dont le rehaussement au gadolinium offre un contraste de frontière plus tranché. Trois contrôles directs (ablation λ × comptage de fragments, visualisation de la carte SDT aux emplacements des fragments, bins de distance vs MSE) sont décrits en **Annexe C** et déférés à des travaux futurs ; la contribution principale ici est la caractérisation et l'atténuation post-hoc de l'artefact, pas son explication mécaniste.

### 6.2 Pourquoi le filtre CC-consensus fonctionne

Baseline ne partage pas la pression SDT et ne produit donc pas la même classe de blobs fallacieux liés à la frontière. Exiger un recouvrement avec Baseline pour qu'une CC DistMap survive équivaut à un **test de consensus** sur un détecteur secondaire aux perturbations disjointes. C'est une application de l'idée classique « accord de classifieurs indépendants », adaptée ici aux composantes connexes plutôt qu'aux voxels.

La règle a deux propriétés souhaitables :

* **Asymétrique par construction.** On part de DistMap (meilleure qualité de frontière) et Baseline est utilisé uniquement comme veto. La meilleure frontière est préservée partout où le veto ne se déclenche pas.
* **Sans paramètre.** Pas de seuil, pas de poids appris — la connectivité CC est le seul hyperparamètre (26-connexe).

### 6.3 Pourquoi l'oracle ne peut être atteint

Deux modèles de la même famille (architecture, données, augmentations, famille de loss identiques, ne différant que par l'auxiliaire SDT) produisent trop peu de diversité pour qu'une classification à 3 issues « B vs D vs F » soit apprenable de façon fiable à partir de features de forme seules. Les deux modèles vivent dans le même voisinage de décision ; leurs désaccords sont dominés par du bruit spatial haute fréquence que la morphologie globale ne capture pas.

Combler l'écart de +0,005 Dice nécessite presque certainement l'une des voies suivantes :

* **Vote probabiliste au niveau voxel.** Exporter les sorties softmax (pas uniquement les labels argmax) et fusionner au niveau voxel brise le plafond du vote en dur. Une moyenne pondérée $\alpha \cdot \mathbf{p}_B + (1-\alpha) \cdot \mathbf{p}_D$ avec α appris par région est une étape suivante naturelle.
* **Diversité architecturale.** Ajouter un backbone non-MedNeXt (nnU-Net vanilla, Swin-UNETR) augmente drastiquement la marge oracle, comme le montrent régulièrement les gagnants BraTS 2023.
* **Ensemble multi-seed / multi-fold.** La recette classique gagne +0,5 à +2 points de Dice sur BraTS ; pleinement compatible avec — et orthogonal à — la règle CC-consensus proposée ici.

### 6.4 Limites

* **Backbone unique.** Toutes les expériences utilisent MedNeXt-B ; la généralisation à Swin-UNETR / nnU-Net vanilla / Restormer renforcerait la conclusion.
* **Pas de baseline de fusion probabiliste.** Seul le filtrage en dur est rapporté car les sorties softmax n'ont pas été persistées à l'inférence. L'analyse du plafond adresse explicitement ce gap pour le cas hard-label.
* **Setup mono-modèle-par-patient.** Le filtre CC-consensus proposé atteint un Dice avg de 0,909 sur la CV 5-fold à 1196 patients sans ensembling multi-fold, sans TTA ni vote multi-architectures. L'ajout de ces astuces classiques placerait probablement le résultat dans ou au-dessus de la fourchette des gagnants BraTS 2023 GLI, mais il s'agirait d'une contribution de calcul parallèle orthogonale à la question de caractérisation des fragments que ce papier adresse.
* **La convention Dice inflate légèrement ET.** Les patients à GT vide sur ET (2,7 % de BraTS 2023 GLI, cas non-rehaussés, 32/1196 vérifié) sont scorés Dice = 1,0 sous la convention nnU-Net / MONAI, ce qui inflate légèrement la moyenne ET (−0,003 seulement sous la convention lesion-wise). Les comparaisons internes Baseline / DistMap / CC-Consensus ne sont pas affectées (les trois utilisent la même convention), mais la moyenne ET absolue n'est pas directement comparable aux leaderboards challenge qui utilisent une convention lesion-wise (voir §5.5).
* **BraTS 2023 GLI uniquement.** L'extension à BraTS-MET (métastases) et BraTS-PED (pédiatrique) est laissée aux travaux futurs ; on s'attend à ce que le biais de fragments soit plus sévère sur les métastases (pattern multi-lésions).
* **Pas de petites tumeurs dans le dataset.** Le volume WT minimum sur BraTS 2023 GLI est de 2808 voxels, la médiane à ~89 500 voxels. La définition topologique de fragment adoptée en §4.2 (CC − 1 par classe, sans seuil de taille) est **intrinsèquement robuste à la taille** et ne nécessite aucune recalibration pour des tumeurs plus petites. Cependant, **le pipeline évalué ici n'a pas été testé sur le régime cliniquement critique des petites tumeurs** (quelques centaines de voxels), où la détection précoce a un impact pronostique majeur. Les features morphologiques absolues (`vol_*`, `nb_cc_*`) seraient hors-distribution sur ce régime et devraient être réexaminées avant usage clinique ; les features topologiques et relatives (`ratio_ET_WT`, `frac_small_cc_*`, sphéricité, élongation) sont robustes par construction.
* **Pas d'harmonisation inter-scanner explicite.** BraTS agrège de multiples institutions, scanners et intensités de champ ; le pipeline officiel standardise la géométrie mais n'applique aucune harmonisation d'intensité inter-scanner, et le z-score par patient ci-dessus aligne les deux premiers moments sans retirer les effets propres au scanner (biais de champ résiduel, contraste). Nous n'appliquons ni correction de biais N4 ni ComBat : le bénéfice de N4 n'est pas établi pour la segmentation profonde de tumeurs — le prétraitement d'égalisation d'intensité est négligeable voire légèrement délétère, seule l'unification du voxel spacing (déjà fournie par BraTS) compte [Kondrateva et al. 2024] — et ComBat est inapplicable ici car la conversion DICOM→NIfTI supprime les métadonnées scanner (pas de labels de batch). Ce facteur de confusion étant partagé par toutes les méthodes comparées (mêmes folds), il ne biaise pas la comparaison relative ; il ne borne que la généralisation absolue inter-centres.

---

## 7. Conclusion

Sous le jeu complet des métriques officielles BraTS-2023, à convergence (300 ep, CV 5-fold, n = 1196), une tête SDT auxiliaire sur MedNeXt-B / nnU-Net v2 est **nulle sur les métriques de classement officielles** (Dice et HD95 lesion-wise, critères primaires pré-spécifiés, Holm p = 1,0) et **neutre en Dice régional** ; le gain Dice rapporté à budget d'entraînement réduit ne survit pas à la convergence. Son seul effet robuste est un **déplacement orienté rappel** — plus de sensibilité et moins de lésions manquées (p = 2 × $10^{-9}$), au prix d'une perte de spécificité (p = 1,2 × $10^{-14}$) dont la signature topologique est l'apparition de petites composantes connexes fallacieuses (« fragments », ×1,5 sur NCR). Une analyse multi-graine indépendante (3 graines × fold 0, §5.6) confirme la non-significativité et révèle une instabilité d'entraînement DistMap quatre fois supérieure à celle de Baseline (σ inter-graine ×4).

Lu comme un point de fonctionnement et combiné par un **filtre de consensus de composantes connexes sans paramètre** — qui oppose un veto aux composantes DistMap qu'un second modèle ne corrobore pas —, ce rappel devient un **système qui bat la baseline** : c'est la **seule configuration évaluée à améliorer significativement les deux métriques de classement officielles** (Dice lesion-wise +0,024, Holm p = 4,5 × $10^{-16}$ ; HD95 lesion-wise −9,49 mm, Holm p = 5,7 × $10^{-26}$), en supprimant ~41 % des lésions fallacieuses à coût de rappel négligeable, sans aucun coût sur le Dice de recouvrement. Une part du gain HD95 tient à la pénalité de 374 mm par lésion fallacieuse de la métrique officielle ; le gain Dice lesion-wise, lui, est un nettoyage de détection authentique. Complémentairement, le filtre réduit HD95 NCR *legacy* (4,86 → 4,48 mm, p = 5,7 × $10^{-14}$) en éliminant 66 % des fragments NCR.

Le gain de **recouvrement régional**, lui, reste plafonné (l'oracle par classe n'est qu'à +0,005 Dice avg au-dessus du défaut, et aucun meta-selector à 31 features ne le bat en CV) : combler cet écart sur le Dice régional motive un **vote probabiliste au niveau voxel** ou des **loss d'entraînement sensibles aux fragments** (travaux futurs), plutôt que davantage d'ingénierie post-hoc. La leçon transversale : une loss auxiliaire doit être rapportée sur **toutes** les métriques officielles, lue par son mécanisme (ici, l'axe rappel–précision qu'elle déplace), et exploitée — non comme un booster de Dice, mais comme un point de fonctionnement alimentant un consensus.

---

## 8. Perspectives

**Loss d'entraînement sensible aux fragments (travaux futurs).** L'hypothèse §6.1 suggère que les fragments sont un effet de gradient. Un terme de pénalité au moment de l'entraînement comptant les composantes connexes prédites sur l'argmax de chaque mini-batch — et pénalisant les petits blobs isolés — devrait pousser le réseau à ne pas les instancier, rendant le filtre post-hoc CC-consensus inutile. C'est la direction de ces travaux futurs.

**Extensions de dataset.** BraTS-MET (métastases, pattern multi-lésions) est le prochain test le plus informatif : les fragments DistMap devraient y être plus sévères, et le filtre CC-consensus en bénéficier davantage. BraTS-PED (pédiatrique) testerait la généralisation à travers des shifts démographiques.

---

## Remerciements

L'auteur remercie **Stanislas Larnier** pour ses conseils méthodologiques, ses retours sur la formulation des questions de recherche, et ses relectures attentives des versions successives de ce papier.

---

## Annexe A — Calibration de λ (loss auxiliaire SDT)

À l'epoch 0 avec un réseau initialisé aléatoirement (seed 42), on mesure $|\mathcal{L}_{\mathrm{Dice+CE}}| = 0{,}57$ et $\mathcal{L}_{\mathrm{MSE}}^{\mathrm{SDT}} = 0{,}12$, ce qui donne un λ « équilibré par gradient » de 4,70.

Une ablation statique sur λ $\in$ {0 ; 0,1 ; 0,5 ; 1 ; 2 ; 5 ; 6 ; 7 ; 8 ; 9 ; 10} (100 epochs, fold 0, seed 42) donne des Dice avg tous compris dans une fenêtre de 0,5 pp :

| λ | Dice avg | Δ vs Baseline |
|---|---|---|
| 0 (Baseline) | 0,9064 | 0 |
| 0,1 | 0,9077 | +0,0013 |
| 0,5 | 0,9070 | +0,0006 |
| 1,0 | 0,9067 | +0,0003 |
| 2,0 | 0,9060 | −0,0004 |
| 5,0 | 0,9105 | +0,0041 |
| 9,0 | 0,9104 | +0,0040 |

Sur ce fold unique et sans test de significativité par patient, aucun λ ne se distingue clairement du baseline. Ce résultat est en cohérence avec la non-significativité du gain DistMap observée en CV 5-fold sur 1196 patients (§5.1). L'entraînement par défaut rapporté dans le corps utilise λ = 1 (proche des heuristiques publiées et de la calibration équilibrée ÷ 5).

Un schéma de pondération dynamique — DWA (Dynamic Weight Average, Liu CVPR 2019) — qui suit les taux d'apprentissage relatifs des têtes Dice+CE et SDT au cours de l'entraînement, est une piste à explorer : s'il existe un régime où SDT contribue vraiment sans saturer, un balayage statique ne peut pas le trouver.

---

## Annexe B — Étude détaillée du plafond hard-label

L'écart entre CC-consensus par défaut et oracle par classe (+0,005 Dice avg) est le gain maximal de toute politique de sélection par région. On évalue des politiques progressivement plus riches :

| Politique | Dice avg | Δ vs CC-consensus |
|---|---|---|
| Meilleur seuil taille-adaptatif (τ = 200 vx) | 0,90909 | +0,00012 |
| 27 règles fixes par région — meilleur = D/F/F | 0,90935 | +0,00038 |
| Meta-LR (31 features, niveau patient) | 0,90940 | +0,00043 |
| Meta-RF (31 features, par région) | 0,90807 | **−0,00090** |
| Meta-LR (31 features, par région) | 0,90844 | −0,00053 |
| Meta-GBM (31 features, par région) | 0,90833 | −0,00064 |
| Règle à une feature (fit toutes données) | 0,91016 | +0,00119 |
| **Règle à une feature (CV 5-fold)** | **0,90801** | **−0,00096** |

La règle à une feature, attirante en fit toutes données (+0,00119), s'effondre en CV 5-fold (−0,00096) : la meilleure feature et le meilleur seuil changent entre folds (TC : 4 features distinctes sur 5 folds ; ET : 4 features distinctes). Quatre features « meilleures » différentes sur cinq folds pour TC seule indiquent clairement que le signal n'est pas assez robuste pour lui faire confiance.

Un RandomForest entraîné par région atteint 50 %, 43 % et 51 % de précision en argmax (WT, TC, ET) contre 33 % au hasard, ce qui confirme la présence de signal dans les features — mais lorsque le classifieur se trompe, il choisit un modèle strictement pire, aboutissant à un bilan net négatif.

L'importance des features (RF sur toutes les données, top-3 par région) étaye le récit : pour ET, `frac_removed_distmap_ET` (0,13) et `max_orphan_cc_ET` (0,09) — toutes deux des features d'accord inter-modèles — dominent. Le signal est réel, simplement pas assez fort pour survivre à la CV.

\clearpage

![Figure A1 — Top-8 des importances features d'un RandomForest entraîné à prédire argmax(Baseline, DistMap, CC-Consensus) pour chaque région (WT / TC / ET). Barres bleues : features morphologiques issues de la GT (20). Barres rouges : features d'accord inter-modèles (11). Pour ET spécifiquement, les 3 premières importances — `frac_removed_distmap_ET`, `max_orphan_cc_ET`, `n_no_overlap_distmap_ET` — sont toutes des features d'accord, confirmant que la décision « faire confiance au filtre CC-consensus sur ET ou non » est pilotée par la quantité de sur-prédiction de DistMap par rapport à Baseline.](figures/rf_importance.png){width=100%}

---

## Annexe C — Hypothèse mécaniste : contrôles déférés

L'hypothèse de §6.1 (la pression SDT engendre des voxels à forte réponse aux interfaces ambigües, qui survivent parfois à l'argmax) reste à ce stade une **hypothèse de travail non démontrée**. Les trois contrôles directs suivants sont tous réalisables sur les checkpoints existants et sont déférés à des travaux futurs :

1. **Ablation de λ croisée avec comptage de fragments.** Vérifier que le nombre moyen de fragments par patient croît monotoniquement avec λ. Une croissance monotone confirmerait le lien causal entre pression SDT et artefact ; une absence de monotonie suggérerait que le bruit d'optimisation domine.
2. **Visualisation de la carte SDT aux emplacements des fragments.** Pour un échantillon de patients, superposer la sortie tanh de la tête auxiliaire et la carte de fragments ; les fragments devraient coïncider avec des voxels à forte réponse SDT proches d'une interface tissulaire.
3. **Bins de distance vs MSE.** Remplacer la tête `Conv3D(32 → 3) + tanh + MSE` par une tête de classification en bins de distance (ex. 16 bins équi-probables dans [−1, 1]). Si l'artefact disparaît ou diminue substantiellement, il est spécifique à la formulation MSE-SDT et non à la supervision de distance en général.

Exécuter ces trois contrôles ferait passer §6.1 d'« hypothèse de travail » à « mécanisme démontré ».

---

## Annexe D — Temps d'exécution et reproductibilité

Tout le code, les 20 + 11 features pré-extraites, les scores par modèle et par patient, les CSV d'oracles / classification de cas, les résultats du balayage de seuil et les sorties des meta-selectors sont disponibles dans le dépôt compagnon [github.com/guillaume-cassez/brats-moe-distmap-fusion-1](https://github.com/guillaume-cassez/brats-moe-distmap-fusion-1) et archivés sur Zenodo (DOI conceptuel [10.5281/zenodo.19695263](https://doi.org/10.5281/zenodo.19695263)).

Les checkpoints des modèles entraînés (5 folds de cross-validation pour chaque variante, poids au format `safetensors`, sans état d'optimiseur) sont publiés sur Hugging Face Hub :

- Baseline : [huggingface.co/GuillaumeCassez/mednext-baseline-brats2023gli](https://huggingface.co/GuillaumeCassez/mednext-baseline-brats2023gli)
- DistMap (SDT auxiliaire) : [huggingface.co/GuillaumeCassez/mednext-distmap-brats2023gli](https://huggingface.co/GuillaumeCassez/mednext-distmap-brats2023gli)

L'extraction des 31 features par patient sur les 1196 prédictions tourne en **~10 min** sur 14 threads P-cores (`taskset -c 0-13`) d'un i7-14700K ; le balayage complet de meta-classifieurs (4 familles × 5 folds × 31 dim) tourne en ~2 min sur le même hôte. **Temps d'entraînement par fold : ~13 h 30 pour 300 epochs** sur une unique RTX PRO 6000 Blackwell (96 Go), variantes Baseline et DistMap à durée équivalente (la tête de régression SDT auxiliaire ajoute < 1 % de surcoût GPU sur 300 ep).

---

## Annexe E — Les six patients de démonstration

Six patients sont mis en avant pour couvrir les six cas d'ordonnancement de modèle, utilisés à la fois pour les figures et comme ancres épinglées dans le viewer 3D compagnon. Dans le tableau, $F$ désigne la sortie du filtre CC-consensus. Les identifiants patient sont affichés sans le préfixe `BraTS-GLI-` pour compacité (le dataset le préfixe systématiquement).

```{=latex}
\begin{center}
\renewcommand{\arraystretch}{1.3}
\footnotesize
\setlength{\tabcolsep}{2pt}
\begin{tabular}{|p{3.4cm}|c|c|c|c|c|p{7.7cm}|}
\hline
\textbf{Tag} & \textbf{Patient} & \textbf{Fold} & \textbf{B} & \textbf{D} & \textbf{F} & \textbf{Enseignement} \\
\hline
C1 (baseline $>$ distmap) & 00048-001 & 1 & 0,983 & 0,308 & 0,973 & DistMap hallucine TC/ET sur un cas uniquement œdème \\
\hline
C2 (distmap $>$ baseline) & 01437-000 & 2 & 0,589 & 0,923 & 0,923 & DistMap sauve un Baseline sous-segmentant \\
\hline
C3 (B $<$ F $<$ D) & 01428-000 & 1 & 0,618 & 0,656 & 0,645 & Sortie du filtre entre les deux, tirée côté baseline \\
\hline
C4 (D $<$ F $<$ B) & 00017-001 & 0 & 0,991 & 0,657 & 0,890 & Sortie du filtre sauve DistMap par consensus \\
\hline
C5 (filtre pire) & 01530-000 & 1 & 0,241 & 0,541 & 0,169 & Le filtre supprime une grosse CC DistMap légitime \\
\hline
C6 (filtre meilleur) & 00540-000 & 1 & 0,785 & 0,795 & 0,869 & Synergie nette \\
\hline
\end{tabular}
\end{center}
```

---

## Références

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
* Saluja R., *et al.* (2023). *BraTS-2023-Metrics : Official BraTS 2023 Segmentation Performance Metrics*. [github.com/rachitsaluja/BraTS-2023-Metrics](https://github.com/rachitsaluja/BraTS-2023-Metrics).
* Nikolov S., Blackwell S., Zverovitch A., Mendes R., Livne M., De Fauw J., *et al.* (2021). *Clinically applicable segmentation of head and neck anatomy for radiotherapy: deep learning algorithm development and validation study*. **Journal of Medical Internet Research** 23(7), e26151. DOI: 10.2196/26151.
