# brats-moe-distmap-fusion-1

**Loss auxiliaire de type *distance map* pour la segmentation de tumeurs cérébrales :
analyse centrée sur les fragments et plafond de saturation du filtrage post-hoc par consensus de composantes connexes**

*Version française. English version: [README.md](README.md).*

Code, artefacts de données et source du papier pour une étude BraTS 2023 GLI.

> *Note de nomenclature.* Les premières versions utilisaient le label « fusion MoE ». Cette version abandonne ce label : la règle n'est pas un Mixture-of-Experts au sens strict (pas de réseau de gating appris, pas de routage doux). Il s'agit d'un **filtre de consensus en dur, post-hoc, au niveau des composantes connexes** — décrit précisément comme **filtre CC-consensus** dans tout le document. Le slug du dépôt (`brats-moe-distmap-fusion-1`) est conservé pour la stabilité URL / DOI.

[![viewer interactif](https://img.shields.io/badge/🌐_viewer_interactif-guillaume--cassez.fr-blue)](https://guillaume-cassez.fr/imagerie-medicale/viewer/)
[![page paper](https://img.shields.io/badge/📄_page_paper-guillaume--cassez.fr-blue)](https://guillaume-cassez.fr/imagerie-medicale/)
[![HF Baseline](https://img.shields.io/badge/🤗-MedNeXt%20Baseline-yellow)](https://huggingface.co/GuillaumeCassez/mednext-baseline-brats2023gli)
[![HF DistMap](https://img.shields.io/badge/🤗-MedNeXt%20DistMap-yellow)](https://huggingface.co/GuillaumeCassez/mednext-distmap-brats2023gli)
[![licence](https://img.shields.io/badge/licence-MIT-green)](LICENSE)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.19695263.svg)](https://doi.org/10.5281/zenodo.19695263)

---

## L'histoire derrière ce dépôt

J'ai démarré ce projet emballé par une idée simple : les losses auxiliaires de type distance map ont amélioré la segmentation sur **d'autres tâches médicales** (organes abdominaux, foie, atrium cardiaque — Ma MIDL 2020 ; Xue AAAI 2020), la même approche devrait aider sur BraTS 2023 GLI — surtout avec le backbone récent MedNeXt-B. L'hypothèse était facile à tester.

**Première surprise** : à 10 epochs, le delta Dice paraissait excellent (+0,74 pp moyen), mais à 300 epochs sur la CV 5-fold complète (1196 patients), le delta s'est dissous dans le bruit de mesure (+0,09 pp, p > 0,25 par région). DistMap ne donne donc pas du Dice gratuit.

**Deuxième surprise** : en comparant les prédictions, un détail a attiré l'attention — DistMap produisait davantage de petits blobs isolés que Baseline, surtout visibles sur NCR (cœur nécrotique). Quantifié : ×1,5 plus de fragments. Un mode de défaillance que personne n'avait encore signalé sur BraTS.

**Troisième surprise, la plus enthousiasmante** : une correction post-hoc sans paramètre — un filtre par consensus de composantes connexes qui oppose un veto aux composantes exclusives à DistMap en utilisant Baseline comme second détecteur — élimine **66 % des fragments NCR** sur 1196 patients (Wilcoxon p < 10⁻¹⁸⁹) à coût Dice nul, ET améliore significativement HD95 sur NCR avec p = 5,7 × 10⁻¹⁴.

L'histoire finale n'est donc pas « DistMap est meilleur ». C'est « DistMap a une surface de décision différente, produit un artefact spécifique, et une règle post-hoc simple transforme cela en un gain cliniquement pertinent sur la qualité de frontière de la nécrose tumorale ». Le Dice cachait le vrai signal. C'est ça, le papier.

---

## TL;DR

1. **À convergence sur 1196 patients en CV 5-fold**, l'ajout d'une loss auxiliaire Signed Distance Transform (SDT) sur MedNeXt-B / nnU-Net v2 **n'améliore PAS significativement le Dice** (Δ = +0,09 pp, Wilcoxon p > 0,25 par région). Les deux modèles sont Dice-équivalents aux erreurs de mesure près.

2. Mais la loss SDT introduit un nouveau mode de défaillance : **composantes connexes isolées fallacieuses (« fragments »)** absentes de la vérité terrain, particulièrement marquées sur NCR (cœur nécrotique) et ED (œdème).

3. Un **filtre par consensus de composantes connexes sans paramètre (filtre CC-consensus)** — partir de DistMap, supprimer toute composante connexe qui n'a aucun recouvrement avec Baseline dans la même classe — **élimine 66 % des fragments NCR** sur 1196 patients (Wilcoxon p < 10⁻¹⁸⁹, définition topologique : CC − 1 par classe), 52 % sur ED (p < 10⁻¹⁶²), 33 % sur ET (p = 1,1 × 10⁻⁵³), sans coût en Dice, ET **améliore significativement HD95 sur NCR** (4,86 → 4,48 mm, p = 5,7 × 10⁻¹⁴). Le gain de qualité de frontière est cliniquement pertinent sur la nécrose tumorale — précisément la région où des fragments fallacieux peuvent induire en erreur un radiothérapeute.

4. Sur 1196 patients (CV 5-fold), la **borne supérieure oracle de sélection par classe** n'est que **+0,005 Dice avg** au-dessus de la règle CC-consensus par défaut. **Aucun classifieur** (RF / LR / GBM) entraîné sur 31 features fabriquées à la main (morphologie GT + accord inter-modèles) **ne bat robustement le défaut en CV**. Combler cet écart nécessite un vote probabiliste au niveau voxel ou une diversité architecturale.

→ Le filtre CC-consensus par défaut est déjà quasi-optimal dans le paradigme post-hoc hard-label. Les améliorations futures doivent cibler des **losses sensibles aux fragments à l'entraînement** (Paper 2), pas davantage d'ingénierie post-hoc.

---

## Viewer 3D interactif

**→ [guillaume-cassez.fr/brats/](https://guillaume-cassez.fr/brats/)**

Six patients (C1–C6) sont épinglés en tête du menu déroulant Patient. Chacun illustre un ordonnancement distinct entre Baseline / DistMap / Fusion sur le Dice. Basculer entre les modèles, tourner, couper, comparer à la vérité terrain en un clic.

| Cas | Patient | B | D | F | Enseignement |
|---|---|---|---|---|---|
| C1 — B > D | 00048-001 | 0,983 | 0,308 | 0,973 | DistMap hallucine TC/ET sur un cas uniquement œdème |
| C2 — D > B | 01437-000 | 0,589 | 0,923 | 0,923 | DistMap sauve un Baseline sous-segmentant |
| C3 — B < F < D | 01428-000 | 0,618 | 0,656 | 0,645 | Fusion entre les deux, tirée côté baseline |
| C4 — D < F < B | 00017-001 | 0,991 | 0,657 | 0,890 | Fusion sauve DistMap par consensus |
| C5 — F < min(B,D) | 01530-000 | 0,241 | 0,541 | 0,169 | Fusion supprime une grosse CC DistMap légitime |
| C6 — F > max(B,D) | 00540-000 | 0,785 | 0,795 | 0,869 | Synergie nette |

---

## Essayer le filtre CC-consensus sur vos propres prédictions

La règle est sans paramètre (seule la connectivité 26). Branchez vos deux tableaux de segmentation (DistMap + Baseline, deux label maps dans `{0, 1, 2, 3}`) :

```python
import numpy as np
from scipy import ndimage as ndi

STRUCT_26 = ndi.generate_binary_structure(3, 3)

def cc_consensus_filter(distmap_seg, baseline_seg, classes=(1, 2, 3)):
    """Filtre de consensus de composantes connexes.
    Part de DistMap ; pour chaque classe, supprime toute CC de DistMap dont
    le masque de classe identique n'a aucun voxel commun avec Baseline.
    Sans paramètre (connectivité 26)."""
    filtered = distmap_seg.copy()
    for c in classes:
        d_mask = (distmap_seg == c); b_mask = (baseline_seg == c)
        if not d_mask.any(): continue
        lab, n = ndi.label(d_mask, structure=STRUCT_26)
        for cc_id in range(1, n + 1):
            cc = (lab == cc_id)
            if not np.any(cc & b_mask):
                filtered[cc] = 0  # fragment non confirmé
    return filtered
```

---

## Structure du dépôt

```
├── paper.md                     Source du paper (anglais, Markdown)
├── paper.pdf                    Paper (anglais, compilé)
├── paper_fr.md                  Source du paper (français, Markdown)
├── paper_fr.pdf                 Paper (français, compilé)
├── README.md                    Version anglaise
├── README_fr.md                 Ce fichier
├── LICENSE                      MIT
├── CITATION.cff                 Citation lisible par machine
├── scripts/                     Scripts d'analyse (Python)
│   ├── extract_patient_features.py        20 features GT-morpho (tour-only : NIfTI requis)
│   ├── extract_agreement_features.py      11 features accord inter-modèles (tour-only)
│   ├── sweep_adaptive_fusion.py           Balayage de seuil {20…∞} vx (tour-only)
│   ├── compute_hd95_per_class.py          HD95 per-class NCR/ED/ET (tour-only)
│   ├── count_fragments_topological.py     Comptage fragments topologiques (CC−1 par classe) par variant (tour-only)
│   ├── select_demo_patients.py            Sélection champions C1–C6
│   ├── analyze_case_features.py           Mann-Whitney + importance RF par cas
│   ├── oracle_per_class.py                Oracles patient + par classe
│   ├── analyze_sweep.py                   Classification du balayage (lit data/sweep.csv)
│   ├── meta_selector.py                   Meta-classifieur au niveau patient
│   ├── meta_selector_perregion.py         3 classifieurs × par région × CV 5-fold
│   ├── simple_combinations.py             27 règles fixes + recherche 1-feature
│   └── simple_rule_cv.py                  Règle 1-feature en CV 5-fold (test overfit)
├── data/                        CSV pré-extraits (1196 patients, prêt à l'emploi)
│   ├── rankings.json                      Dice + HD95 par patient (B/D/F × WT/TC/ET)
│   ├── all_cases.json                     Les 6 classifications de cas
│   ├── C1_*..C6_*.csv                     Un CSV par cas, classé
│   ├── patient_features.csv               20 features morpho × 1196 patients
│   ├── patient_agreement_features.csv     11 features d'accord × 1196 patients
│   └── sweep.csv                          Dice par patient × seuil (6 seuils)
├── analysis/                    Sorties générées (reproductibles depuis data/)
│   ├── mann_whitney.csv
│   ├── rf_importance_BvD.csv
│   ├── rf_importance_fusion4.csv
│   ├── per_case_stats.csv
│   ├── meta_selector.txt
│   ├── meta_selector_perregion.txt
│   ├── adaptive_fusion_summary.txt
│   ├── hd95_per_class_cv.csv              HD95 per-class (NCR/ED/ET) pour B/D/F × 1196 patients
│   └── fragments_topological_cv.csv       Comptage fragments topologiques (CC−1 par classe) pour B/D/F × 1196 patients
└── viewer/                      Pointeur vers le viewer 3D interactif
    └── README.md
```

Les images NIfTI brutes BraTS 2023 GLI ne sont **pas** redistribuées ici (licence challenge). À récupérer sur le [portail officiel BraTS 2023](https://www.synapse.org/#!Synapse:syn51156910).

---

## Reproduire les chiffres

```bash
# 1. Installer les dépendances minimales
pip install numpy scipy scikit-learn scikit-image nibabel

# 2. Exécuter n'importe quel script d'analyse (tous lisent les CSV dans data/)
python3 scripts/oracle_per_class.py                # oracles patient + par classe
python3 scripts/analyze_case_features.py           # tests Mann-Whitney + stats par cas
python3 scripts/select_demo_patients.py            # classification C1-C6 → data/
python3 scripts/meta_selector.py                   # meta-classifieur niveau patient
python3 scripts/meta_selector_perregion.py         # 3 classifieurs × par région × CV 5-fold
python3 scripts/simple_combinations.py             # 27 règles fixes + recherche 1-feature
python3 scripts/simple_rule_cv.py                  # règle 1-feature CV (test overfit)
python3 scripts/analyze_sweep.py                   # stats du balayage de seuil adaptatif
```

Ces scripts ne lisent que les CSV et JSON livrés dans `data/` — entièrement reproductibles depuis un clone.

L'extraction de features par patient (`extract_patient_features.py`, `extract_agreement_features.py`), le balayage de seuil (`sweep_adaptive_fusion.py`) et le HD95 per-class (`compute_hd95_per_class.py`) requièrent les NIfTI de prédictions baseline/DistMap *et* (pour les features morpho + HD95) les NIfTI de vérité terrain — aucun n'est redistribué ici (licence challenge BraTS 2023). L'entraînement des modèles requiert le pipeline nnU-Net v2 complet avec backbone MedNeXt.

---

## Citer

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

## À propos de l'auteur

**Guillaume Cassez** ([ORCID 0009-0007-0987-3931](https://orcid.org/0009-0007-0987-3931)) a construit ce projet en 2026 en **recherche indépendante** (hors cadre institutionnel), avec les conseils méthodologiques et la relecture de **Stanislas Larnier** (mentor de formation). La trajectoire complète de la recherche — Rapport de recherche 1 sur la fusion post-hoc (ici) et Rapport 2 sur les losses d'entraînement pénalisant les fragments (en cours) — est motivée par une observation simple : les meilleurs outils aujourd'hui rapportent des scores Dice, mais les cliniciens se soucient de savoir si la segmentation contient des artefacts qu'un radiologue signalerait immédiatement.

**Je suis actuellement en recherche d'opportunités**, idéalement :

- **ML / Research engineering** en imagerie médicale, IA clinique ou computer vision biomédicale
- **Postes de recherche ML appliquée** (CDD, CDI, **thèse / PhD**, post-doc industriel, équipe R&D)
- **MLOps / engineering** en contexte health-tech

Si votre équipe fait ce genre de travail, un échange serait apprécié — ne serait-ce que pour partager des notes sur l'analyse de plafond ou le phénomène des fragments.

→ [cassez.guillaume@gmail.com](mailto:cassez.guillaume@gmail.com)
→ [guillaume-cassez.fr](https://guillaume-cassez.fr)
→ [Bluesky @guillaume-cassez.bsky.social](https://bsky.app/profile/guillaume-cassez.bsky.social)
→ [ORCID 0009-0007-0987-3931](https://orcid.org/0009-0007-0987-3931)

Pour une discussion technique sur ce travail spécifiquement, merci d'ouvrir une [issue GitHub](https://github.com/guillaume-cassez/brats-moe-distmap-fusion-1/issues) — cela aide les futurs lecteurs.

---

## Licence

Le **code** de ce dépôt est publié sous [licence MIT](LICENSE).
Les **figures et le texte du paper** (paper.md, paper_fr.md et figures dérivées) sont publiés sous [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/) : redistribution et remix autorisés avec attribution.
Les données d'imagerie brutes BraTS 2023 ne sont **pas** redistribuées et restent sous leur licence challenge d'origine.
