```{=latex}
\clearpage
```

# Deux modèles qui s'accordent battent le meilleur des deux : un consensus de composantes connexes sans paramètre qui bat le baseline sous les métriques officielles BraTS-2023

> **Révision éditoriale du 2026-09-22 — vocabulaire et provenance du jeu de
> données.** Nous ne qualifions plus un faux positif d'« hallucination » : dans la littérature des
> modèles génératifs, ce mot désigne un autre phénomène, et ce qui est mesuré ici est une
> **composante connexe fallacieuse (faux positif)** — une lésion prédite là où la vérité terrain
> n'en porte aucune. Le §1 énonce ce choix explicitement. Le §3.1 liste désormais un à un les 55
> cas écartés entre le téléchargement de 1251 cas et le jeu d'étude de 1196
> (`analysis/DATASET_EXCLUSIONS_fr.md`), avec le motif de chaque exclusion et une re-mesure de
> l'intégrité des fichiers ; l'exclusion est une précaution au niveau patient consignée en mars
> 2026, en amont de tout entraînement et de toute métrique. Aucun chiffre de ce manuscrit ne change.
>
> **Révision éditoriale du 2026-09-19 — structure et titre.** Le plan des sections est aligné sur
> les Papiers 2 et 3 : les Méthodes absorbent désormais les données (§3.1) et le protocole
> d’évaluation (§3.5), qui déclare d’emblée les deux échelles utilisées — les métriques
> officielles BraTS-2023 lésion-wise et le protocole interne voxel-wise ; les Limites deviennent
> une section autonome (§6) ; les Perspectives sont fusionnées dans la Conclusion (§7). Le
> sous-titre est resserré autour de la même accroche. Aucun résultat n’est modifié ; les renvois
> de sections sont renumérotés (§5.x → §4.x, §6.x → §5.x).
>
> **Révision du 2026-09-01 — auteurs et titre.** Stanislas Larnier rejoint la liste des auteurs
> en deuxième position, d'un commun accord entre les deux auteurs ; la section Remerciements est
> remplacée par une section Contributions. Aucun chiffre du manuscrit n'est modifié. Le dépôt
> Zenodo porte, jusqu'à la v9 (2026-07-03), la liste d'auteurs précédente : la présente liste
> prend effet à la v10 du dépôt (DOI de concept `10.5281/zenodo.19695263`).
>
> **Révision éditoriale du 2026-08-11.** Le texte citable reste le dépôt Zenodo (DOI de concept
> `10.5281/zenodo.19695263`), dont l'évaluation sous les métriques officielles
> BraTS-2023 donne au consensus de composantes connexes **+0,024 de Dice lésion-wise**
> (p de Holm = 4,5 × 10⁻¹⁶) et **−9,49 mm de HD95 lésion-wise** (p de Holm = 5,7 × 10⁻²⁶) sur le
> baseline, en retirant ~41 % des lésions parasites. La présente révision ne change aucun chiffre :
> elle remet en tête ce que le travail établit — le consensus — et déplace en second le résultat
> nul de la tête auxiliaire seule. Titre aligné sur celui du dépôt. Les chiffres ci-dessous sont
> ceux du protocole interne (Dice voxel-wise, fragments, HD95 par classe) tel qu'il était mesuré
> dans ce manuscrit ; ils ne remplacent pas les métriques officielles du dépôt.

**Guillaume Cassez · Stanislas Larnier**

Recherche indépendante

*Guillaume Cassez* — [ORCID 0009-0007-0987-3931](https://orcid.org/0009-0007-0987-3931) · `cassez.guillaume@gmail.com` · [guillaume-cassez.fr](https://guillaume-cassez.fr)  
*Stanislas Larnier* — `stanislaslarnier@gmail.com` · [HAL stanislas-larnier](https://cv.hal.science/stanislas-larnier)

*BraTS 2023 GLI · nnU-Net v2 · MedNeXt-B · 1196 patients de validation*

---

## Résumé

**Exiger que deux modèles soient d'accord vaut mieux que le meilleur des deux.** Sur BraTS 2023
GLI, un filtre de **consensus de composantes connexes** (CC-consensus), post-hoc et **sans aucun
paramètre**, qui supprime toute composante d'un modèle qu'un second modèle ne corrobore pas,
élimine **66 % des fragments NCR** (Wilcoxon p < 10⁻¹⁸⁹, définition topologique : CC − 1 par
classe) **sans coût en Dice**, et **améliore significativement le HD95** sur NCR (4,86 → 4,48 mm,
p = 5,7 × 10⁻¹⁴) et sur WT (3,86 → 3,76 mm, p = 2,7 × 10⁻⁴), sur 1196 patients en validation
croisée 5-fold. Sous les métriques officielles du challenge, cette même règle est la seule
configuration de l'étude qui batte significativement le baseline (voir le bandeau de version).
Cliniquement, NCR est précisément la région où des fragments fallacieux peuvent induire en erreur
un radiothérapeute sur l'emprise de la nécrose tumorale : le gain de qualité de frontière mesuré
ici est caché par le Dice et visible via HD95. En configuration mono-modèle — pas d'ensemble
multi-fold, pas de TTA, une seule architecture — le CC-consensus atteint 0,909 de Dice moyen, à
moins d'un point de la fourchette des gagnants publiés de BraTS 2023 GLI (§4.5).

**Le mécanisme vaut plus que l'ingrédient.** La loss auxiliaire de type *distance map* (SDT —
Signed Distance Transform) qui alimente ce consensus n'apporte, prise seule, aucun gain
significatif : à convergence sur 1196 patients en CV 5-fold, Δ Dice avg = +0,09 pp, Wilcoxon
p > 0,25 par région — un résultat confirmé par une analyse multi-graine (3 graines indépendantes,
fold 0, Δ Dice avg = −0,28 pp, t-test p = 0,21) qui révèle de surcroît une instabilité
d'entraînement DistMap quatre fois supérieure à celle du baseline (σ inter-graine ×4). Ce
résultat nul est rapporté en entier, et il ouvre l'analyse plutôt qu'il ne la conclut : ce que la
tête SDT produit de robuste n'est pas du Dice, c'est un **décalage vers le rappel**, dont la
contrepartie est un mode de défaillance jusqu'ici non rapporté dans la littérature BraTS — des
**composantes connexes isolées fallacieuses** (« fragments ») absentes de la vérité terrain,
particulièrement marquées sur NCR (×1,5 vs baseline) et ED (×1,2). C'est exactement ce qu'un
second modèle sait vetoter, et c'est pourquoi le consensus fonctionne. Note de vocabulaire : nous écartons délibérément le terme « hallucination », qui désigne un autre phénomène dans la littérature des modèles génératifs (une sortie fluide mais sans ancrage) ; ce qui est mesuré ici est une **composante connexe faussement prédite** — une lésion prédite absente de la vérité terrain.

**Ce que le post-hoc ne pourra pas donner de plus.** Une étude du plafond hard-label montre que la
règle est déjà proche de la saturation : l'oracle par classe n'est qu'à +0,005 de Dice avg au-dessus
du défaut, et aucun meta-selector à 31 features (4 familles de classifieurs) ne bat robustement le
CC-consensus en CV 5-fold (Annexe B). Combler cet écart demande un vote probabiliste au niveau
voxel ou une diversité architecturale — ce qui motive le Paper 2 vers une loss sensible aux
fragments à l'entraînement plutôt que davantage d'ingénierie post-hoc.

**Contributions.** (1) Un filtre CC-consensus simple et sans paramètre qui élimine 66 % des
fragments NCR sans coût en Dice et **améliore significativement le HD95 NCR** (p = 5,7 × 10⁻¹⁴) —
un gain de qualité de frontière cliniquement pertinent que le Dice ne montre pas. (2) La
caractérisation quantitative de l'artefact topologique de fragments induit par la loss SDT
auxiliaire — invisible au Dice, prévalent sur NCR — avec une définition topologique sans seuil de
taille, à grande échelle (1196 patients), qui explique *pourquoi* le consensus a de la matière à
retirer. (3) La délimitation du plafond de tout filtrage post-hoc sur ces prédictions, mesurée
plutôt qu'affirmée.

---

## 1. Introduction

La segmentation de tumeurs cérébrales sur IRM multi-modalités (challenge BraTS) est dominée ces dernières années par des dérivés de nnU-Net [Isensee 2021]. La tâche canonique est une classification 3D de voxels en quatre classes : fond, cœur nécrotique (NCR, label 1), œdème péri-tumoral (ED, label 2) et tumeur rehaussée (ET, label 3). La performance est habituellement rapportée via des coefficients de Dice sur trois régions emboîtées : WT = {1,2,3}, TC = {1,3}, ET = {3}.

Les équipes les plus performantes raffinent le backbone (MedNeXt [Roy MICCAI 2023], Swin-UNETR) tout en laissant la loss d'entraînement quasi inchangée : Dice + cross-entropy. En parallèle, la **régression auxiliaire de *distance maps*** [Ma MIDL 2020 ; Xue AAAI 2020] est régulièrement proposée pour rendre le réseau sensible à la forme, avec des résultats empiriques mitigés. Des applications spécifiques à BraTS existent — multi-tâche à décodeurs parallèles [Huang 2021], losses Hausdorff-aware [Karimi & Salcudean 2020], et formulations géodésiques « régression seule » [Dang 2024, SiNGR] — mais aucune à ce jour ne rapporte ni n'analyse l'artefact de fragments caractérisé ici (§4.2).

Ce qui est moins exploré, et qui porte le résultat de ce papier, c'est ce que devient une
prédiction quand un **second modèle doit la corroborer**. Les règles de consensus au niveau des
composantes connexes sont rares dans la littérature BraTS publiée (§2), alors qu'elles sont
gratuites — aucun paramètre, aucun entraînement supplémentaire — et qu'elles agissent exactement
là où la métrique lésion-wise du challenge pénalise : la composante parasite. C'est le mécanisme
que ce papier isole, mesure et plafonne.

Ce papier poursuit quatre objectifs :

* **Un opérateur de consensus, et ce qu'il rapporte** : une règle de veto par composante connexe,
  sans paramètre, qui retire 66 % des fragments NCR sans coût en Dice et améliore significativement
  le HD95 (§4.3) — la seule configuration de l'étude qui batte le baseline sous les métriques
  officielles du challenge.
* **Caractérisation empirique** de la tâche SDT auxiliaire à convergence sur MedNeXt-B / nnU-Net v2 : à 300 epochs en CV 5-fold sur 1196 patients, DistMap ne produit **pas** de gain Dice significatif (p > 0,25 par région), contrairement à l'impression tirée de comparaisons à budget d'entraînement réduit.
* **Analyse de mode de défaillance** : identification et quantification d'un artefact sous-rapporté de la tâche SDT — la production de composantes connexes petites et isolées qui gonflent les faux positifs sans toucher significativement au Dice. Cette observation qualitative a été rendue possible par un **viewer 3D interactif compagnon** construit spécifiquement pour ce projet, qui rend côte-à-côte les meshes Baseline / DistMap / CC-Consensus pour les 1196 patients ([guillaume-cassez.fr/brats/](https://guillaume-cassez.fr/brats/)).
* **Analyse du plafond** d'un filtre CC-consensus post-hoc qui corrige cet artefact, avec une étude sur 1196 patients délimitant ce qu'un meta-selector à base de features peut atteindre en l'absence d'accès aux softmax ou de diversité de modèles.

---

## 2. Travaux connexes

**Losses auxiliaires par *distance maps* en segmentation médicale.** [Ma 2020] propose une tête de régression SDT auxiliaire pour des structures abdominales / cardiaques (LiTS, LA atrium), établissant la recette tanh + MSE reprise ici. [Xue 2020] utilise des distance maps signées comme **sortie principale** (non auxiliaire) sur des organes, avec λ = 10 sans ablation. [Karimi & Salcudean 2020] dérivent une loss Hausdorff-aware à partir de distance transforms, évaluée sur nnU-Net + BraTS, mais comme **modification de loss** et non comme tête de régression auxiliaire. Aucun de ces travaux ne signale le phénomène de fragments caractérisé ici.

**Approches distance-map spécifiquement appliquées à BraTS.** L'idée d'associer une supervision de forme par distance à la segmentation BraTS **n'est pas nouvelle en soi** ; deux travaux antérieurs sont particulièrement proches du dispositif présenté et doivent être signalés explicitement.

- [Huang et al. 2021] entraînent un V-Net avec deux *décodeurs parallèles* sur BraTS 2018–2020 — l'un produisant le masque de segmentation, l'autre régressant une distance transform *non signée* à travers une sigmoid. C'est l'état de l'art le plus proche de ce travail. Le présent travail s'en distingue par trois points concrets : (i) une tête auxiliaire légère `Conv3d(32→3) + tanh` au lieu d'un décodeur parallèle complet (<0,1 % de paramètres ajoutés vs un décodeur dupliqué) ; (ii) distance euclidienne *signée* avec MSE, et non distance non signée avec sigmoid ; (iii) MedNeXt-B / nnU-Net v2 sur BraTS 2023 GLI (1196 patients) au lieu d'un V-Net sur BraTS 2018–2020.
- [Dang et al. 2024, *SiNGR*] proposent une régression **géodésique normalisée signée** avec loss Focal-L1 sur sortie tanh, qui **remplace** la sortie de segmentation sur BraTS 2020 (backbones Swin-UNETR / UNet3D). Le présent travail est multi-tâche (conservation de la sortie Dice + CE softmax à côté de la régression SDT) et utilise la distance euclidienne signée classique, et non une transformée géodésique.

Ni Huang et al. ni SiNGR ne rapportent ou n'analysent l'artefact de fragments décrit en §4.2 de ce papier ; c'est la contribution empirique spécifique revendiquée ici.

**Ensembling et fusion.** Les gagnants BraTS classiques s'appuient sur l'ensembling 5-fold (soft-voting des softmax). Les règles de sélection de modèle ou de stacking au niveau patient sont peu courantes ; les règles de consensus au niveau des composantes connexes le sont encore moins dans la littérature BraTS publiée.

**Analyse des modes de défaillance.** Des métriques au niveau composante (F1 lesion-wise) ont été introduites dans le challenge BraTS 2023 mais restent secondaires au Dice / HD95 dans les publications. À notre connaissance, aucun travail antérieur ne quantifie ni ne localise le biais de fragments induit par les losses SDT auxiliaires sur BraTS.

---

## 3. Méthodes

### 3.1 Données et backbone

**Jeu de données.** BraTS 2023 GLI (1251 patients, 4 modalités chacun). Pré-traitement via les réglages par défaut de nnU-Net v2 (z-score par patient, cropping automatique, ré-échantillonnage isotrope 1 mm³). Labels de vérité terrain {0, 1, 2, 3}. Sur les 1251 cas unifiés, 1196 ont été retenus pour l'entraînement et l'évaluation : les 55 cas écartés sont listés un par un — motif, date git de l'entrée déclenchante, et re-mesure de leur intégrité fichier — dans `analysis/DATASET_EXCLUSIONS_fr.md`. L'exclusion est une précaution au niveau patient consignée en mars 2026, en amont de tout entraînement et de toute métrique ; aucun défaut fichier (NIfTI illisible, NaN/Inf, label hors jeu, affine divergent) ne se reproduit aujourd'hui sur ces 55 cas, identiques octet pour octet sur les trois copies survive du jeu. Partition des patients : validation croisée 5-fold stratifiée par ID. Toutes les métriques ci-dessous sont calculées sur l'ensemble de validation (n = 239 pour le fold 0) ou agrégées sur les 5 folds (n = 1196).

**Backbone.** MedNeXt-B [Roy MICCAI 2023] ré-implémenté dans nnU-Net v2 avec le plan `nnUNetPlans_96GB_mednext` (patch 128³, BS 2, BF16, RTX PRO 6000 Blackwell).

**Tête auxiliaire.** Un unique Conv3D(32 → 3, noyau 1 × 1 × 1) + tanh prédisant une carte SDT normalisée pour chacune des régions NCR, ED, ET. La SDT de référence est pré-calculée une fois par patient via `scipy.ndimage.distance_transform_edt` sur chaque masque binarisé de région, signée par sign(intérieur − extérieur), clippée min-max à [−1, 1] avec bord = 0.

**Loss.** $\mathcal{L} = \mathcal{L}_{\mathrm{Dice+CE}} + \lambda \cdot \mathcal{L}_{\mathrm{MSE}}^{\mathrm{SDT}}$, avec $\lambda = 1$ par défaut (calibration équilibrée par gradient ÷ 5 ; ablation statique sur 11 valeurs détaillée Annexe A).

```{=latex}
\needspace{15\baselineskip}
```

### 3.2 Nommage des variantes

| Variante | Trainer | Auxiliaire ? |
|---|---|---|
| **Baseline** | `nnUNetTrainerMedNeXtBaseline` | pas de SDT |
| **DistMap** | `nnUNetTrainerMedNeXtDistMap` | SDT, λ = 1 |
| **CC-Consensus** | règle post-hoc (§3.3) sur DistMap + Baseline | post-hoc |

### 3.3 Règle de filtrage CC-consensus[^moe]

[^moe]: Les versions antérieures de ce travail désignaient cette règle par « fusion MoE (Mixture-of-Experts) ». Ce label est abandonné : il n'y a ni réseau de gating appris, ni routage doux des inputs, ni entraînement conjoint experts-gate. Le terme neutre « filtre CC-consensus » est employé dans tout le document.

Étant données la prédiction Baseline $P_B$ et la prédiction DistMap $P_D$ (tous deux des tenseurs de labels dans {0, 1, 2, 3}), la prédiction filtrée $P_F$ est calculée classe par classe :

```
P_F := copy(P_D)
pour chaque classe c ∈ {1, 2, 3}:
    D_mask  := (P_D == c)
    B_mask  := (P_B == c)
    labeled, n := cc_label(D_mask, structure=connectivité-26)
    pour chaque cc_id ∈ 1..n:
        cc := (labeled == cc_id)
        si cc ∩ B_mask = ∅:
            P_F[cc] := 0        # on supprime le fragment non confirmé
```

La règle a quatre effets qualitatifs :

1. Les fragments DistMap isolés de la classe correspondante Baseline → **supprimés**.
2. Les raffinements de frontière DistMap sans recouvrement avec Baseline → **conservés** (on part toujours de $P_D$).
3. Les trous Baseline comblés par DistMap → **conservés** ($P_D$ est non nul à ces endroits).
4. Les faux positifs Baseline rejetés par DistMap → **restent rejetés** ($P_D$ est nul à ces endroits).

La règle n'a **aucun paramètre appris** et un seul hyperparamètre (connectivité 26 vs 6), fixé à 26 partout. C'est une opération de *veto* : Baseline n'ajoute aucun voxel nouveau ; il ne peut que supprimer des composantes que DistMap a prédites sans confirmation.

### 3.4 Analyse du plafond

Pour caractériser le plafond de qualité atteignable par toute politique de sélection au niveau patient ou région sur les trois prédictions disponibles, on définit, pour chaque patient $p$ avec Dice régional $(D^B, D^D, D^F) \in \mathbb{R}^3$ par région $r \in \{\mathrm{WT}, \mathrm{TC}, \mathrm{ET}\}$ :

$$\mathrm{Oracle}_{\mathrm{patient}}(p) = \max_{m \in \{B,D,F\}} \tfrac{1}{3}\sum_r D^m_r$$

$$\mathrm{Oracle}_{\mathrm{par\text{-}classe}}(p) = \tfrac{1}{3}\sum_r \max_{m \in \{B,D,F\}} D^m_r$$

L'écart entre ces oracles et la moyenne CC-consensus par défaut est le gain maximal atteignable par toute politique de sélection. Les politiques candidates évaluées (seuil taille-adaptatif, meta-classifieurs, règle à une feature) et leurs résultats sont rapportés en §4.4 et détaillés en Annexe B.

### 3.5 Évaluation

**Deux échelles, déclarées d’emblée.** Chaque tableau de ce manuscrit indique laquelle des deux échelles d’évaluation il rapporte ; les deux ne sont jamais mélangées dans un même tableau. (1) L’**échelle officielle BraTS-2023** — la boîte à outils *BraTS-2023-Metrics* du challenge (paramètres GLI) : Dice et HD95 lésion-wise par région (WT, TC, ET) après nettoyage des composantes connexes (composantes < 1000/250/500 voxels retirées par région), plus le *Legacy Dice* voxel-wise de l’outil pour référence. C’est l’échelle du résultat principal porté par le bandeau de version ci-dessus et par le dépôt : en CV 5-fold, le CC-consensus gagne +0,024 de Dice lésion-wise et −9,49 mm de HD95 lésion-wise sur le baseline (corrigé de Holm), tout en retirant ~41 % des lésions parasites ; l’évaluation officielle par graine est tabulée §4.6 (Tableaux A et B). (2) Le **protocole interne** — Dice voxel-wise avec la convention nnU-Net / MONAI des régions vides, comptages de fragments, features d’accord et de morphologie : l’échelle des analyses de mécanisme du corps du texte (§4.1–§4.4). Les deux échelles répondent à des questions différentes : l’officielle note l’accord au niveau lésion, tel que le lit le challenge ; l’interne mesure le recouvrement voxel et la topologie, et ses valeurs absolues ne sont pas comparables aux leaderboards du challenge (§4.5).

**Protocole interne — Dice** par région (WT, TC, ED, ET) avec la convention standard nnU-Net / MONAI : *Dice = 1 si la GT et la prédiction sont toutes deux vides*. Voir §4.5 pour les précautions à prendre lors de la comparaison aux leaderboards BraTS challenge.

**Comptage de fragments (définition topologique).** Un **fragment** est une composante connexe (connectivité 26) d'une classe donnée qui n'est **pas la plus grosse** composante de sa classe — c'est-à-dire une CC topologiquement déconnectée du corps tumoral principal. Par classe $c$ sur une prédiction $P$, le nombre de fragments est :
$$\mathrm{fragments}(P, c) = \max(0, \; \mathrm{nb\_CC}(P == c, \text{26-conn}) - 1)$$
Pas de seuil de taille — la 26-connectivité (faces, arêtes, coins partagés) suffit à définir ce qui est topologiquement lié. Cette définition traite symétriquement petites et grandes composantes accessoires.

**Features d'accord inter-modèles (11)** : Dice(Baseline, DistMap) pour WT/TC/ET ; différence volumétrique normalisée $|{|P_B^c|} - {|P_D^c|}| / ({|P_B^c|} + {|P_D^c|})$ pour ET et NCR ; nombre / fraction / taille max des CC DistMap sans recouvrement Baseline, pour ET et NCR.

**Features morphologiques (20)** : volume par région, ratios de volumes, comptage et taille des CC en connectivité 26 pour NCR/ET, élongation du tenseur d'inertie (λ₁/λ₃), sphéricité $(\pi^{1/3}(6V)^{2/3})/S$, rugosité de surface $S_{\mathrm{pred}}/S_{\mathrm{sphère}}$, nombre d'Euler ([scikit-image] `euler_number`, connectivité 3) pour WT/TC/ET, comptage de cavités pour WT (diff `binary_fill_holes`), comptage de CC baseline / distmap par NCR et ET, dispersion des CC d'ET (écart-type des distances centroïdes).

---

```{=latex}
\needspace{22\baselineskip}
```

## 4. Résultats

### 4.1 À convergence, DistMap et Baseline sont équivalents en Dice

Sur les 1196 patients agrégés hors-fold de la CV 5-fold (schedule 300 epochs par fold ; DistMap fold 0 arrêté à 178 ep, les 9 autres entraînements complets), DistMap et Baseline produisent des Dice **statistiquement indiscernables** :

| Région | Baseline | DistMap | ΔDice | p-value | Améliorés / dégradés / égaux |
|---|---|---|---|---|---|
| WT | 0,9354 | 0,9360 | +0,006 pp | 0,72 | 577 / 618 / 1 |
| TC | 0,9185 | 0,9180 | −0,005 pp | 0,27 | 595 / 596 / 5 |
| ET | 0,8696 | 0,8723 | +0,027 pp | 0,54 | 568 / 596 / 32 |
| **Avg** | **0,9078** | **0,9088** | **+0,009 pp** | **0,50** | — |

Test de Wilcoxon signé apparié, hypothèse unilatérale DistMap $>$ Baseline. Aucune région n'atteint le seuil de significativité standard (p > 0,25 partout) ; sur WT, davantage de patients sont dégradés qu'améliorés par DistMap (618 vs 577). Le Δ = +0,09 pp de Dice avg est dans la variance de mesure.

**Implication.** La loss SDT auxiliaire, telle que formulée ici (tête Conv3D(32→3)+tanh, régression MSE, λ = 1), ne confère pas d'amélioration Dice significative à convergence sur BraTS 2023 GLI. Cela n'exclut pas que DistMap produise des prédictions *différentes* de Baseline : les deux modèles divergent sur 1195/1196 patients (1 seule égalité stricte en Dice avg), mais leurs désaccords se compensent en moyenne sur le Dice global. Cette différence de topologie sans magnitude Dice motive l'analyse de fragments qui suit.

```{=latex}
\needspace{21\baselineskip}
```

### 4.2 DistMap introduit des fragments fallacieux

L'inspection qualitative des prédictions DistMap visait des frontières plus nettes — comportement attendu d'une loss sensible à la distance. Au lieu de cela, les prédictions DistMap montrent systématiquement davantage de composantes connexes isolées que Baseline. Quantification topologique sur les 1196 patients de la CV 5-fold (moyennes par patient, fragments = CC − 1 par classe, 26-connectivité) :

| Fragments / patient | Baseline | DistMap | **CC-Consensus** | Δ D−B | Δ F−D | Réduction F/D |
|---|---|---|---|---|---|---|
| **NCR** | 79,7 | 93,3 | **31,3** | +13,6 | −61,9 | **−66 %** |
| **ED** | 28,9 | 35,3 | **17,0** | +6,4 | −18,3 | **−52 %** |
| **ET** | 2,15 | 2,33 | **1,57** | +0,18 | −0,76 | **−33 %** |

Tests de Wilcoxon signés unilatéraux sur les 1196 patients :

- **DistMap inflate les fragments vs Baseline** sur les 3 classes : NCR (p = 5,5 × 10⁻⁴²), ED (p = 2,0 × 10⁻⁴⁹), ET (p = 1,3 × 10⁻³). L'artefact est statistiquement massif et systématique.
- **CC-Consensus réduit les fragments vs DistMap** : NCR (p < 10⁻¹⁸⁹), ED (p < 10⁻¹⁶²), ET (p = 1,1 × 10⁻⁵³).
- **CC-Consensus réduit aussi vs Baseline** : NCR (p < 10⁻¹⁸⁸), ED (p < 10⁻¹⁴⁴), ET (p = 1,4 × 10⁻³⁰) — le filtre post-hoc corrige même les fragments hérités du Baseline quand DistMap n'y avait pas d'overlap.

Cet effet **ne se voit pas sur le Dice** (§4.3 : Dice moyens B / D / F à 0,9078 / 0,9088 / 0,9090, différences dans le bruit) — des fragments de quelques voxels n'impactent pas une métrique de recouvrement quand le volume tumoral médian fait ~90 000 voxels. C'est précisément pourquoi la littérature passée n'avait pas rapporté l'artefact : le Dice est aveugle à la topologie.

![Figure 1 — Comptage moyen de fragments par patient (composantes connexes non-principales, 26-connectivité, sans seuil de taille) pour chaque classe × variante, sur les 1196 patients de la CV 5-fold. DistMap inflate le nombre de fragments NCR de +17 % par rapport à Baseline ; le filtre CC-consensus le ramène à 31,3 — une réduction de **66 %** par rapport à DistMap (Wilcoxon p < 10⁻¹⁸⁹).](figures/fragment_counts.png){width=90%}

**Illustrations qualitatives sur les six cas de référence.** Les figures 2–7 ci-dessous montrent, pour chacun des six patients épinglés (C1–C6) du viewer 3D compagnon, les segmentations produites par GT / Baseline / DistMap / CC-Consensus, vue sagittale gauche, régions tumorales seules (Brain masqué pour focus) — le rendu du viewer en régime officiel, sur fond blanc pour l'impression. Les cas ont été ré-élus le 2026-08-31 sur les données régénérées en régime officiel clean (nettoyage de composantes 1000/250/500) : les scores cités dans les légendes sont des Dice lésion-wise officiels moyennés sur les 3 régions, par opposition au protocole interne (Dice voxel-wise) utilisé dans le corps du texte. Chaque figure illustre l'un des six modes de comportement identifiés en Annexe E.

\clearpage

**Note sur le rendu 3D (deux pipelines).** Le viewer propose un mode lissé et un mode voxel, chacun servi par un pipeline distinct selon la nature du mesh.

*Mode voxel (vérité brute).* *Greedy voxel meshing* : chaque voxel de la segmentation est converti en une face cubique fusionnée avec ses voisins coplanaires. Aucune interpolation, aucun lissage — ce que le modèle a prédit au voxel près. Sert de référence de vérité quand on veut compter ou localiser précisément.

*Mode lissé (défaut, figures 2–7), meshes principaux.* Pipeline `fill_holes + dilation + marching cubes` : le masque binaire est pré-rempli (`scipy.ndimage.binary_fill_holes` pour supprimer les cavités internes — ventricules, sulci), dilaté d'un voxel (`binary_dilation`, 1 itération) pour adoucir les escaliers du marching cubes, puis marching-cubed au seuil 0,5. C'est le pipeline utilisé pour les meshes des corps tumoraux et du Brain (figures 2–7).

*Mode lissé, fragments et cavités.* Pour les petites composantes (< 4 voxels jusqu'aux fragments sub-voxel), un pipeline **champ de distance signée** (*signed distance field*) distinct est employé : dilatation 26-connectivité pour bridger les voxels touchant par coin/arête, transformée de distance euclidienne intérieure et extérieure (`scipy.ndimage.distance_transform_edt`) pour construire le champ de distance signée, upsampling spline cubique ×2 pour résolution sub-voxel, puis marching cubes au niveau iso = −0,3 (calibré empiriquement pour préservation volumique). Ce pipeline est **nécessaire pour les petits fragments** car un marching cubes naïf au seuil 0,5 sur un masque 1-voxel rend 1/6 du volume réel (erreur ×6) alors que le champ de distance signée préserve le volume à ±5 % sur toutes les tailles.

*Propriété commune aux deux pipelines lisses.* Ils **préservent la topologie** (mêmes composantes connexes, même comptage en 26-connectivité que le mode voxel) ; la différence est purement cosmétique. Le lissage est le défaut parce qu'il produit un rendu proche de la console clinique ; le mode voxel reste un clic de distance pour toute inspection qui requiert la vérité voxel-exacte.

![Figure 2 — Cas **C1** (patient `BraTS-GLI-01435-000`) : mode D < F < B (4/1196, 0,3 %), cas le plus marqué. Baseline (0,924) ≫ DistMap (0,629) : DistMap prédit une masse tumorale entière éloignée de la tumeur réelle (Dice WT/TC ≈ 0,44, HD95 ≈ 189 mm). **Le CC-Consensus supprime les composantes de DistMap non corroborées par Baseline** (veto) et restaure 0,924.](figures/patient_C1_01435-000_4models.png){width=100%}

\clearpage

![Figure 3 — Cas **C2** (patient `BraTS-GLI-01094-000`) : le filtre confirme DistMap (1183/1196, 98,9 % des patients — mode majoritaire en régime officiel). Baseline sous-segmente la tumeur (0,643 ; WT ≈ 0,49, HD95 ≈ 188 mm) ; DistMap est précis (0,968, HD95 1,0 mm) et ne génère aucune composante fallacieuse : après le nettoyage officiel, toutes ses composantes sont corroborées par Baseline, le veto ne retire rien (**F = D = 0,968**).](figures/patient_C2_01094-000_4models.png){width=100%}

\clearpage

![Figure 4 — Cas **C3** (patient `BraTS-GLI-01530-000`) : mode B < F < D (3/1196, 0,3 %) : le filtre est tiré côté Baseline. Baseline ne détecte aucune tumeur rehaussée (TC/ET = 0 ; 0,241) ; le veto retire la composante noyau de DistMap (TC 0,770), non corroborée. La fusion garde le contour WT de DistMap (0,855, HD95 4 mm) mais perd le noyau : **0,285 < 0,542**.](figures/patient_C3_01530-000_4models.png){width=100%}

\clearpage

![Figure 5 — Cas **C4** (patient `BraTS-GLI-00017-001`) : le veto n'a ici rien à retirer, mais les deux modèles ratent le noyau. Après le nettoyage officiel (composantes < 1000/250/500 voxels), les faux positifs non corroborés sont déjà retirés : le filtre confirme DistMap (**F = D = 0,657 > B = 0,656**). Contour WT quasi parfait (0,969) mais noyau manqué (TC = 0, HD95 TC = sentinelle officielle 374 mm).](figures/patient_C4_00017-001_4models.png){width=100%}

\clearpage

![Figure 6 — Cas **C5** (patient `BraTS-GLI-00733-001`) : synergie, **F > max(B, D)** (2/1196, 0,2 %). Baseline (0,751) et DistMap (0,805) perdent tous deux une grande partie de la tumeur entière (Dice WT ≈ 0,32/0,48, HD95 ≈ 250/188 mm) ; le CC-Consensus restaure le contour WT (0,955, HD95 1,4 mm) et atteint **0,964 — strictement supérieur aux deux parents**.](figures/patient_C5_00733-001_4models.png){width=100%}

\clearpage

![Figure 7 — Cas **C6** (patient `BraTS-GLI-00388-000`) : mode « casse » quasi éteint en régime officiel : **F < min(B, D)** pour seulement 2/1196 (0,2 %), écart maximal 0,0007. Ici la fusion reste juste sous le pire parent (**0,921** contre 0,923/0,922). Mesuré avec la même méthode sur les mêmes 1196 patients, ce mode valait 47/1196 (3,9 %) sur les prédictions brutes, avant le nettoyage officiel.](figures/patient_C6_00388-000_4models.png){width=100%}

```{=latex}
\needspace{18\baselineskip}
```

### 4.3 Le CC-consensus améliore HD95 NCR sans coût Dice

Agrégation des prédictions hors-fold sur les 5 folds (n = 1196) :

| Stratégie | Dice avg | Δ vs CC-consensus par défaut |
|---|---|---|
| Baseline seule | 0,9078 | −0,00115 |
| DistMap seule | 0,9088 | −0,00020 |
| CC-Consensus (règle par défaut) | 0,9090 | 0 (réf.) |
| **Oracle au niveau patient** | 0,9131 | **+0,00412** |
| **Oracle par classe** | 0,9139 | **+0,00494** |

```{=latex}
\needspace{16\baselineskip}
```

Classification par patient (en notant $F$ la sortie du CC-consensus) :

| Cas | Effectif | % |
|---|---|---|
| Baseline bat DistMap (B > D) | 602 | 50,3 % |
| DistMap bat Baseline (D > B) | 593 | 49,6 % |
| Sortie du filtre entre B et D | 559 | 46,7 % |
| **Filtre < les deux (dégradation)** | **463** | **38,7 %** |
| **Filtre > les deux (synergie)** | **157** | **13,1 %** |

Le filtre CC-consensus dégrade le score patient dans 38,7 % des cas contre 13,1 % de synergie. Par région, CC-Consensus l'emporte strictement sur 2,7 % des patients pour WT, **21,7 % pour TC** et 6,9 % pour ET. Le bénéfice du filtre en Dice est donc concentré sur TC ; pour WT et ET, le choix Baseline-seule ou DistMap-seule domine déjà.

```{=latex}
\needspace{19\baselineskip}
```

**Qualité de frontière (HD95).** Complément du Dice, les distances de Hausdorff à 95 % sur les régions emboîtées BraTS (WT/TC/ET) **et** sur les classes individuelles (NCR, ED) où vivent les fragments (n varie par ligne selon le nombre de patients à HD95 fini sur la classe concernée) :

| Région / classe | Composition | Baseline | DistMap | CC-Consensus | Δ CC-Cons. vs DistMap |
|---|---|---|---|---|---|
| WT | {1, 2, 3} | 3,91 mm | 3,86 mm | **3,76 mm** | **−0,10 mm, p = 2,7 × 10⁻⁴** |
| TC | {1, 3} | 3,08 mm | 2,79 mm | 2,88 mm | +0,09 mm, n.s. |
| ET | {3} | 2,62 mm | 2,59 mm | 2,70 mm | +0,11 mm, n.s. |
| **NCR** | {1} | 4,89 mm | 4,86 mm | **4,48 mm** | **−0,38 mm, p = 5,7 × 10⁻¹⁴** |
| ED | {2} | 4,25 mm | 4,33 mm | 4,21 mm | −0,12 mm, n.s. (p = 0,82) |

Test de Wilcoxon signé apparié, hypothèse unilatérale HD95(CC-Consensus) < HD95(DistMap). n = 1160 pour WT/TC/ET (restriction aux patients à HD95 fini sur les 3 régions emboîtées), 1153 pour NCR, 1193 pour ED.

**Le signal dominant est sur NCR** : CC-Consensus réduit HD95 NCR de 0,38 mm (p = 5,7 × 10⁻¹⁴) — confirmation quantitative directe que la suppression des fragments améliore la qualité de frontière sur la classe où ils prolifèrent majoritairement (NCR : ×1,5 plus de fragments DistMap vs Baseline, cf. §4.2). Le signal sur WT (−0,10 mm, p = 2,7 × 10⁻⁴) en est l'écho : NCR ⊂ WT, donc les fragments NCR contribuent à l'erreur de frontière WT. Sur ED, la réduction de fragments (−61 %) ne se traduit pas en gain HD95 statistiquement significatif — l'œdème a une variabilité intrinsèque de frontière qui domine les outliers introduits par les fragments. Sur TC et ET (classe 3), les HD95 sont préservés.

Le CC-consensus délivre donc un gain quantitatif mesurable sur HD95 NCR et HD95 WT, là où le Dice reste insensible. Cliniquement, NCR est précisément la région où des fragments fallacieux peuvent induire en erreur un radiothérapeute sur l'emprise de la nécrose tumorale.

\clearpage

![Figure 8 — 1196 patients de validation représentés dans le plan de désaccord entre modèles : x = Dice(DistMap) − Dice(Baseline) (une valeur positive signifie que DistMap l'emporte au niveau patient), y = Dice(CC-Cons.) − max(Dice(B), Dice(D)) (une valeur négative signifie que le filtre CC-consensus est pire que chaque modèle pris isolément). Le nuage *rouge* C5 sous y = 0 rassemble 38,7 % des patients pour lesquels le filtre dégrade le score ; les points *verts* C6 au-dessus de y = 0 ne représentent que 13,1 %. Cette asymétrie visuelle est l'observation empirique centrale du papier.](figures/case_scatter.png){width=100%}

### 4.4 Le plafond hard-label est saturé

L'écart entre CC-consensus par défaut et oracle par classe (+0,005 Dice avg) borne supérieurement le gain de toute politique de sélection au niveau patient ou région à partir des trois prédictions {B, D, F}. On évalue trois familles de politiques en CV 5-fold (seuil taille-adaptatif sur τ ∈ {20, 50, 100, 200, 500, ∞} voxels ; meta-classifieurs RF/LR/GBM × patient/région sur 31 features ; règle à une feature par recherche exhaustive) ; **aucune ne bat robustement le CC-consensus par défaut**. La règle à une feature, attirante en fit toutes données (+0,00119), s'effondre en CV 5-fold (−0,00096) : la meilleure feature et le meilleur seuil changent entre folds (TC : 4 features distinctes sur 5 folds ; ET : 4 features distinctes). Un RandomForest par région atteint 50 %, 43 %, 51 % de précision argmax (vs 33 % au hasard), ce qui confirme la présence de signal — mais lorsque le classifieur se trompe, il choisit un modèle strictement pire, aboutissant à un bilan net négatif.

Le détail complet — tableau des 7 politiques évaluées, importances RF par région, classification du sweep adaptatif, partition par fold de la règle à une feature — est en **Annexe B**. Le plafond hard-label est essentiellement atteint ; combler l'écart à l'oracle nécessite un vote probabiliste au niveau voxel ou une diversité architecturale (§5.3).

### 4.5 Positionnement par rapport aux gagnants BraTS 2023 GLI

Le CC-consensus atteint Dice avg = 0,909 (WT 0,935, TC 0,919, ET 0,873) en CV 5-fold sur 1196 patients, avec un setup mono-modèle (pas d'ensemble multi-fold, pas de TTA, une seule architecture). C'est à moins d'un point de pourcentage de la fourchette des gagnants publiés BraTS 2023 GLI sur test set privé (0,87–0,89 Dice avg ; Ferreira *et al.* 2024). Deux précautions à la comparaison directe : (i) jeu d'évaluation différent (CV 5-fold sur train + val vs test set privé, écart typique 1–2 pp en défaveur du test set) ; (ii) convention Dice = 1 sur région vide (nnU-Net / MONAI) qui inflate ET de ~0,003 par rapport à la convention lesion-wise du challenge (32/1196 patients sans ET en GT).

On ne revendique pas un nouvel état de l'art ; le filtre CC-consensus est **orthogonal à l'ensembling** — la réduction de fragments est un gain qui se cumule avec les astuces multi-fold / TTA classiques sans les dupliquer.

### 4.6 Robustesse à la graine d'entraînement (3 graines, fold 0)

L'analyse §4.1 utilise la graine 42 pour tous les folds. Pour estimer la variance inter-graine et vérifier que la non-significativité n'est pas un artefact d'initialisation, trois entraînements indépendants (graines 1, 2, 3) sont conduits pour Baseline et DistMap (λ=0,1, meilleur λ selon l'Annexe A) sur fold 0 (n≈240 patients), 300 epochs chacun.

```{=latex}
\needspace{14\baselineskip}
```

**Dice de validation fold 0 (nnU-Net, 240 patients) :**

| Config | Graine 1 | Graine 2 | Graine 3 | Moy. ± σ |
|---|---|---|---|---|
| Baseline | 0,9078 | 0,9066 | 0,9078 | **0,9074 ± 0,0007** |
| DistMap (λ=0,1) | 0,9074 | 0,9043 | 0,9021 | **0,9046 ± 0,0027** |
| Δ (B − D) | +0,04 pp | +0,23 pp | +0,57 pp | +0,28 pp |

Test t apparié (n=3 graines) : t=1,83, p=0,21 — non significatif. La non-significativité constatée en CV 5-fold (§4.1, Δ=+0,09 pp, p>0,25) se confirme sur les trois graines : Baseline devance légèrement DistMap dans les trois cas sans qu'aucun écart n'atteigne 1 pp ou le seuil de significativité.

Deux observations :

- **Instabilité DistMap (×4).** La variance inter-graine de DistMap (σ=0,0027) est 4× celle de Baseline (σ=0,0007). La loss SDT auxiliaire rend l'entraînement sensiblement plus sensible à l'initialisation. Ceci explique l'avantage apparent de DistMap observé à la graine de référence (42) dans l'Annexe A (+0,13 pp à λ=0,1) : il s'agit d'une fluctuation d'initialisation, non d'un signal robuste.

- **Avantage baseline monotone.** L'écart Δ(B−D) croît de +0,04 pp (graine 1) à +0,57 pp (graine 3). Avec n=3, aucune tendance causale ne peut être établie ; l'observation est cohérente avec la variance aléatoire plus élevée de DistMap.

**Métriques officielles BraTS-2023 et CC-consensus (D∩B) par graine.** Évaluation complète sur les 3×240 patients (720 paires valides) avec les métriques officielles *BraTS-2023-Metrics* (Legacy Dice, LW Dice, HD95), sur des prédictions vérifiées exemptes de fragments résiduels — la baseline lesion-wise est ainsi identique à celle rapportée dans le Paper 2 sur les mêmes prédictions. Sur Legacy Dice, ni DistMap ni le consensus ne se distinguent de Baseline (p > 0,35 Wilcoxon partout). Le bénéfice se concentre sur la détection lésion par lésion de la tumeur entière : le filtre CC-consensus améliore significativement **LW Dice WT** (0,810 → 0,853, +4,28 pp, p < 10⁻⁴ Wilcoxon) et **LW HD95 WT** (54,5 → 37,3 mm, −17,2 mm, p < 10⁻⁴), sans aucun coût sur le Dice volumétrique. DistMap seul améliore déjà partiellement **LW Dice WT** (+1,54 pp, p = 0,041 Wilcoxon), le consensus amplifiant ce gain.

```{=latex}
\needspace{22\baselineskip}
```

**Tableau A — Baseline vs DistMap (λ=0,1), métriques officielles, fold 0, 3 graines**

| Métrique | Région | Baseline (moy.±σ) | DistMap (moy.±σ) | Δ | p t-test | p Wilcoxon |
|---|---|---|---|---|---|---|
| Legacy Dice | WT | 0,9361 ± 0,0006 | 0,9359 ± 0,0012 | −0,02 pp | 0,89 | 0,44 |
| Legacy Dice | TC | 0,9208 ± 0,0006 | 0,9170 ± 0,0040 | −0,38 pp | 0,35 | 0,36 |
| Legacy Dice | ET | 0,8668 ± 0,0029 | 0,8616 ± 0,0017 | −0,53 pp | 0,12 | 0,63 |
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

```{=latex}
\needspace{22\baselineskip}
```

**Tableau B — CC-consensus (D∩B) vs Baseline, métriques officielles, fold 0, 3 graines**

| Métrique | Région | Baseline (moy.±σ) | CC(D∩B) (moy.±σ) | Δ | p t-test | p Wilcoxon |
|---|---|---|---|---|---|---|
| Legacy Dice | WT | 0,9361 ± 0,0006 | 0,9359 ± 0,0012 | −0,02 pp | 0,90 | 0,41 |
| Legacy Dice | TC | 0,9208 ± 0,0006 | 0,9184 ± 0,0025 | −0,24 pp | 0,39 | 0,56 |
| Legacy Dice | ET | 0,8668 ± 0,0029 | 0,8629 ± 0,0008 | −0,39 pp | 0,13 | 0,91 |
| LW Dice | WT | 0,8103 ± 0,0080 | **0,8531 ± 0,0041** | **+4,28 pp** | **0,017** | **5,5 × 10⁻⁵** |
| LW Dice | TC | 0,8670 ± 0,0067 | 0,8668 ± 0,0034 | −0,02 pp | 0,97 | 0,85 |
| LW Dice | ET | 0,8071 ± 0,0109 | 0,8018 ± 0,0047 | −0,54 pp | 0,42 | 0,69 |
| Legacy HD95 | WT | 6,42 ± 0,28 mm | 6,48 ± 0,05 mm | +0,06 mm | 0,81 | 0,82 |
| Legacy HD95 | TC | 5,95 ± 0,90 mm | 5,50 ± 0,12 mm | −0,45 mm | 0,56 | 0,67 |
| Legacy HD95 | ET | 13,85 ± 1,33 mm | 14,89 ± 0,74 mm | +1,04 mm | 0,14 | 0,60 |
| LW HD95 | WT | 54,52 ± 2,84 mm | **37,31 ± 2,18 mm** | **−17,21 mm** | **0,015** | **6,0 × 10⁻⁵** |
| LW HD95 | TC | 26,82 ± 2,73 mm | 25,42 ± 1,92 mm | −1,39 mm | 0,71 | 0,63 |
| LW HD95 | ET | 41,59 ± 4,68 mm | 43,48 ± 1,32 mm | +1,89 mm | 0,57 | 0,87 |

Le filtre CC-consensus reproduit sur fold 0 multi-graine les gains lesion-wise déjà observés en CV 5-fold (§4.3) et les concentre sur la tumeur entière : amélioration significative et robuste de **LW Dice WT** (+4,28 pp) et **LW HD95 WT** (−17,2 mm), avec p < 10⁻⁴ au test de Wilcoxon et p < 0,02 au test t apparié sur n=3 graines, sans aucun coût sur le Legacy Dice (Δ < 0,1 pp, non significatif). **Aucune tendance n'est observée sur TC ni ET** (|Δ| < 0,6 pp sur LW Dice et < 1,9 mm sur LW HD95, p > 0,6 Wilcoxon) : le bénéfice est purement WT.

---

## 5. Discussion

### 5.1 Pourquoi DistMap génère des fragments

Mécanisme plausible — non démontré : la pression SDT sensibilise le réseau à de petits signaux *boundary-like* dans les tissus de transition (interfaces œdème–substance blanche, cavités post-chirurgicales, NCR hétérogène), produisant des voxels à forte réponse SDT qui survivent parfois à l'argmax sous forme de blobs isolés. Cette hypothèse est cohérente avec deux observations : l'augmentation du comptage de fragments est concentrée sur NCR et ED (régions aux frontières les plus longues et irrégulières), et beaucoup plus faible sur ET dont le rehaussement au gadolinium offre un contraste de frontière plus tranché. Trois contrôles directs (ablation λ × comptage de fragments, visualisation de la carte SDT aux emplacements des fragments, bins de distance vs MSE) sont décrits en **Annexe C** et déférés à des travaux futurs ; la contribution principale ici est la caractérisation et l'atténuation post-hoc de l'artefact, pas son explication mécaniste.

### 5.2 Pourquoi le filtre CC-consensus fonctionne

Baseline ne partage pas la pression SDT et ne produit donc pas la même classe de blobs fallacieux liés à la frontière. Exiger un recouvrement avec Baseline pour qu'une CC DistMap survive équivaut à un **test de consensus** sur un détecteur secondaire aux perturbations disjointes. C'est une application de l'idée classique « accord de classifieurs indépendants », adaptée ici aux composantes connexes plutôt qu'aux voxels.

La règle a deux propriétés souhaitables :

* **Asymétrique par construction.** On part de DistMap (meilleure qualité de frontière) et Baseline est utilisé uniquement comme veto. La meilleure frontière est préservée partout où le veto ne se déclenche pas.
* **Sans paramètre.** Pas de seuil, pas de poids appris — la connectivité CC est le seul hyperparamètre (26-connexe).

### 5.3 Pourquoi l'oracle ne peut être atteint

Deux modèles de la même famille (architecture, données, augmentations, famille de loss identiques, ne différant que par l'auxiliaire SDT) produisent trop peu de diversité pour qu'une classification à 3 issues « B vs D vs F » soit apprenable de façon fiable à partir de features de forme seules. Les deux modèles vivent dans le même voisinage de décision ; leurs désaccords sont dominés par du bruit spatial haute fréquence que la morphologie globale ne capture pas.

Combler l'écart de +0,005 Dice nécessite presque certainement l'une des voies suivantes :

* **Vote probabiliste au niveau voxel.** Exporter les sorties softmax (pas uniquement les labels argmax) et fusionner au niveau voxel brise le plafond du vote en dur. Une moyenne pondérée $\alpha \cdot \mathbf{p}_B + (1-\alpha) \cdot \mathbf{p}_D$ avec α appris par région est une étape suivante naturelle.
* **Diversité architecturale.** Ajouter un backbone non-MedNeXt (nnU-Net vanilla, Swin-UNETR) augmente drastiquement la marge oracle, comme le montrent régulièrement les gagnants BraTS 2023.
* **Ensemble multi-seed / multi-fold.** La recette classique gagne +0,5 à +2 points de Dice sur BraTS ; pleinement compatible avec — et orthogonal à — la règle CC-consensus proposée ici.

## 6. Limites

* **Backbone unique.** Toutes les expériences utilisent MedNeXt-B ; la généralisation à Swin-UNETR / nnU-Net vanilla / Restormer renforcerait la conclusion.
* **Pas de baseline de fusion probabiliste.** Seul le filtrage en dur est rapporté car les sorties softmax n'ont pas été persistées à l'inférence. L'analyse du plafond adresse explicitement ce gap pour le cas hard-label.
* **Setup mono-modèle-par-patient.** Le filtre CC-consensus proposé atteint un Dice avg de 0,909 sur la CV 5-fold à 1196 patients sans ensembling multi-fold, sans TTA ni vote multi-architectures. L'ajout de ces astuces classiques placerait probablement le résultat dans ou au-dessus de la fourchette des gagnants BraTS 2023 GLI, mais il s'agirait d'une contribution de calcul parallèle orthogonale à la question de caractérisation des fragments que ce papier adresse.
* **La convention Dice inflate légèrement ET.** Les patients à GT vide sur ET (2,7 % de BraTS 2023 GLI, cas non-rehaussés, 32/1196 vérifié) sont scorés Dice = 1,0 sous la convention nnU-Net / MONAI, ce qui inflate légèrement la moyenne ET (−0,003 seulement sous la convention lesion-wise). Les comparaisons internes Baseline / DistMap / CC-Consensus ne sont pas affectées (les trois utilisent la même convention), mais la moyenne ET absolue n'est pas directement comparable aux leaderboards challenge qui utilisent une convention lesion-wise (voir §4.5).
* **BraTS 2023 GLI uniquement.** L'extension à BraTS-MET (métastases) et BraTS-PED (pédiatrique) est laissée aux travaux futurs ; on s'attend à ce que le biais de fragments soit plus sévère sur les métastases (pattern multi-lésions).
* **Pas de petites tumeurs dans le dataset.** Le volume WT minimum sur BraTS 2023 GLI est de 2808 voxels, la médiane à ~89 500 voxels. La définition topologique de fragment adoptée en §3.5 (CC − 1 par classe, sans seuil de taille) est **intrinsèquement robuste à la taille** et ne nécessite aucune recalibration pour des tumeurs plus petites. Cependant, **le pipeline évalué ici n'a pas été testé sur le régime cliniquement critique des petites tumeurs** (quelques centaines de voxels), où la détection précoce a un impact pronostique majeur. Les features morphologiques absolues (`vol_*`, `nb_cc_*`) seraient hors-distribution sur ce régime et devraient être réexaminées avant usage clinique ; les features topologiques et relatives (`ratio_ET_WT`, `frac_small_cc_*`, sphéricité, élongation) sont robustes par construction.

---

## 7. Conclusion

Sur MedNeXt-B / nnU-Net v2, la loss SDT auxiliaire ne produit pas de gain Dice significatif à convergence (Δ Dice avg = +0,09 pp, Wilcoxon p > 0,25 par région, CV 5-fold 1196 patients). Une analyse multi-graine indépendante (3 graines × fold 0, §4.6) confirme la non-significativité (t-test p = 0,21) et révèle une instabilité d'entraînement DistMap quatre fois supérieure à celle de Baseline (σ inter-graine ×4). La loss SDT change en revanche la topologie des prédictions en introduisant un biais de fragments que la métrique Dice échoue à rapporter. Un filtre de consensus de composantes connexes sans paramètre, qui oppose un veto aux CC DistMap sans recouvrement Baseline, élimine 66 % des fragments NCR sur 1196 patients (p < 10⁻¹⁸⁹) sans coût en Dice, et **améliore significativement HD95 sur NCR** (4,86 → 4,48 mm, p = 5,7 × 10⁻¹⁴) ainsi que sur WT (3,86 → 3,76 mm, p = 2,7 × 10⁻⁴) — un gain de qualité de frontière caché par le Dice, cliniquement pertinent sur la nécrose tumorale.

Sur 1196 patients en CV 5-fold, on établit que cette règle est déjà proche du plafond de saturation de toute politique de sélection post-hoc en hard-label : l'oracle par classe est à +0,005 Dice avg au-dessus du défaut, et aucun meta-selector à 31 features (4 familles de classifieurs) ne bat robustement ce défaut en CV. Combler cet écart motive des **loss d'entraînement sensibles aux fragments** (Paper 2) plutôt que davantage d'ingénierie post-hoc.

**Perspectives — loss d'entraînement sensible aux fragments (Paper 2).** L'hypothèse §5.1 suggère que les fragments sont un effet de gradient. Un terme de pénalité au moment de l'entraînement comptant les composantes connexes prédites sur l'argmax de chaque mini-batch — et pénalisant les petits blobs isolés — devrait pousser le réseau à ne pas les instancier, rendant le filtre post-hoc CC-consensus inutile. C'est la direction de Paper 2.

**Extensions de dataset.** BraTS-MET (métastases, pattern multi-lésions) est le prochain test le plus informatif : les fragments DistMap devraient y être plus sévères, et le filtre CC-consensus en bénéficier davantage. BraTS-PED (pédiatrique) testerait la généralisation à travers des shifts démographiques.

---

## Contributions des auteurs

**Guillaume Cassez** (auteur principal) : conception de l'étude, entraînement des modèles,
évaluations et analyses, rédaction du manuscrit. **Stanislas Larnier** : formulation des
questions de recherche, conseils méthodologiques, relectures attentives des versions
successives du papier. Les deux auteurs ont approuvé la version finale et l'ordre des auteurs.

---

## Annexe A — Calibration de λ (loss auxiliaire SDT)

À l'epoch 0 avec un réseau initialisé aléatoirement (seed 42), on mesure $|\mathcal{L}_{\mathrm{Dice+CE}}| = 0{,}57$ et $\mathcal{L}_{\mathrm{MSE}}^{\mathrm{SDT}} = 0{,}12$, ce qui donne un λ « équilibré par gradient » de 4,70.

```{=latex}
\needspace{20\baselineskip}
```

Une ablation statique sur λ ∈ {0 ; 0,1 ; 0,5 ; 1 ; 2 ; 5 ; 6 ; 7 ; 8 ; 9 ; 10} (100 epochs, fold 0, seed 42) donne des Dice avg tous compris dans une fenêtre de 0,5 pp :

| λ | Dice avg | Δ vs Baseline |
|---|---|---|
| 0 (Baseline) | 0,9064 | 0 |
| 0,1 | 0,9077 | +0,0013 |
| 0,5 | 0,9070 | +0,0006 |
| 1,0 | 0,9067 | +0,0003 |
| 2,0 | 0,9060 | −0,0004 |
| 5,0 | 0,9105 | +0,0041 |
| 9,0 | 0,9104 | +0,0040 |

Sur ce fold unique et sans test de significativité par patient, aucun λ ne se distingue clairement du baseline. Ce résultat est en cohérence avec la non-significativité du gain DistMap observée en CV 5-fold sur 1196 patients (§4.1). L'entraînement par défaut rapporté dans le corps utilise λ = 1 (proche des heuristiques publiées et de la calibration équilibrée ÷ 5).

Un schéma de pondération dynamique — DWA (Dynamic Weight Average, Liu CVPR 2019) — qui suit les taux d'apprentissage relatifs des têtes Dice+CE et SDT au cours de l'entraînement, est une piste à explorer : s'il existe un régime où SDT contribue vraiment sans saturer, un balayage statique ne peut pas le trouver.

---

```{=latex}
\needspace{24\baselineskip}
```

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

L'hypothèse de §5.1 (la pression SDT engendre des voxels à forte réponse aux interfaces ambigües, qui survivent parfois à l'argmax) reste à ce stade une **hypothèse de travail non démontrée**. Les trois contrôles directs suivants sont tous réalisables sur les checkpoints existants et sont déférés à des travaux futurs :

1. **Ablation de λ croisée avec comptage de fragments.** Vérifier que le nombre moyen de fragments par patient croît monotoniquement avec λ. Une croissance monotone confirmerait le lien causal entre pression SDT et artefact ; une absence de monotonie suggérerait que le bruit d'optimisation domine.
2. **Visualisation de la carte SDT aux emplacements des fragments.** Pour un échantillon de patients, superposer la sortie tanh de la tête auxiliaire et la carte de fragments ; les fragments devraient coïncider avec des voxels à forte réponse SDT proches d'une interface tissulaire.
3. **Bins de distance vs MSE.** Remplacer la tête `Conv3D(32 → 3) + tanh + MSE` par une tête de classification en bins de distance (ex. 16 bins équi-probables dans [−1, 1]). Si l'artefact disparaît ou diminue substantiellement, il est spécifique à la formulation MSE-SDT et non à la supervision de distance en général.

Exécuter ces trois contrôles ferait passer §5.1 d'« hypothèse de travail » à « mécanisme démontré ».

---

## Annexe D — Temps d'exécution et reproductibilité

Tout le code, les 20 + 11 features pré-extraites, les scores par modèle et par patient, les CSV d'oracles / classification de cas, les résultats du balayage de seuil et les sorties des meta-selectors sont disponibles dans le dépôt compagnon [github.com/guillaume-cassez/brats-moe-distmap-fusion-1](https://github.com/guillaume-cassez/brats-moe-distmap-fusion-1) et archivés sur Zenodo (DOI conceptuel [10.5281/zenodo.19695263](https://doi.org/10.5281/zenodo.19695263)).

Les checkpoints des modèles entraînés (5 folds de cross-validation pour chaque variante, poids au format `safetensors`, sans état d'optimiseur) sont publiés sur Hugging Face Hub :

- Baseline : [huggingface.co/GuillaumeCassez/mednext-baseline-brats2023gli](https://huggingface.co/GuillaumeCassez/mednext-baseline-brats2023gli)
- DistMap (SDT auxiliaire) : [huggingface.co/GuillaumeCassez/mednext-distmap-brats2023gli](https://huggingface.co/GuillaumeCassez/mednext-distmap-brats2023gli)

L'extraction des 31 features par patient sur les 1196 prédictions tourne en **~10 min** sur 14 threads P-cores (`taskset -c 0-13`) d'un i7-14700K ; le balayage complet de meta-classifieurs (4 familles × 5 folds × 31 dim) tourne en ~2 min sur le même hôte. **Temps d'entraînement par fold : ~13 h 30 pour 300 epochs** sur une unique RTX PRO 6000 Blackwell (96 Go), variantes Baseline et DistMap à durée équivalente (la tête de régression SDT auxiliaire ajoute < 1 % de surcoût GPU sur 300 ep).

---

## Annexe E — Les six patients de démonstration

Six patients sont mis en avant pour couvrir les six cas d'ordonnancement de modèle, utilisés à la fois pour les figures et comme ancres épinglées dans le viewer 3D compagnon. Dans le tableau, $F$ désigne la sortie du filtre CC-consensus. Les identifiants patient sont affichés sans le préfixe `BraTS-GLI-` pour compacité (le dataset le préfixe systématiquement). Les cas ont été ré-élus le 2026-08-31 sur les données régénérées ; les scores B / D / F sont les Dice lésion-wise officiels BraTS-2023 (régime clean, nettoyage 1000/250/500, moyenne des 3 régions) — par opposition au Dice voxel-wise du protocole interne utilisé dans le corps du texte.

```{=latex}
\needspace{16\baselineskip}
\begin{center}
\renewcommand{\arraystretch}{1.3}
\footnotesize
\setlength{\tabcolsep}{2pt}
\begin{tabular}{|l|c|c|c|c|c|l|}
\hline
\textbf{Tag} & \textbf{Patient} & \textbf{Fold} & \textbf{B} & \textbf{D} & \textbf{F} & \textbf{Enseignement} \\
\hline
C1 (D $<$ F $<$ B) & 01435-000 & 4 & 0,924 & 0,629 & 0,924 & Veto majeur : masse éloignée fallacieuse de DistMap ; le filtre restaure Baseline \\
\hline
C2 (F = D $>$ B) & 01094-000 & 3 & 0,643 & 0,968 & 0,968 & Mode dominant (98,9 \%) : le veto ne retire rien, DistMap confirmé \\
\hline
C3 (B $<$ F $<$ D) & 01530-000 & 1 & 0,241 & 0,542 & 0,285 & Filtre tiré côté Baseline : le noyau DistMap non corroboré est retiré \\
\hline
C4 (F = D $>$ B) & 00017-001 & 0 & 0,656 & 0,657 & 0,657 & Rien à retirer ; les deux modèles ratent le noyau (TC = 0) \\
\hline
C5 (F $>$ max(B, D)) & 00733-001 & 2 & 0,751 & 0,805 & 0,964 & Synergie nette : le contour WT restauré au-delà des deux parents \\
\hline
C6 (F $<$ min(B, D)) & 00388-000 & 2 & 0,923 & 0,922 & 0,921 & Mode casse quasi éteint en régime officiel (2/1196, écart max 0,0007) \\
\hline
\end{tabular}
\end{center}
```

---

## Références

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
