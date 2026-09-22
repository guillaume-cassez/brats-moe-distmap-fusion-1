# D'où viennent les 55 exclusions — provenance mesurée (1 251 → 1 196 cas)

*Généré le 2026-09-22 20:23 UTC par `scripts/paper1_exclusions_provenance.py` à partir des
artefacts de `scripts/audit_exclusions_1251_1196.py`,
`scripts/audit_exclusions_integrity.py`, `scripts/sonde_5_cas_exclus.py` et
`scripts/compare_3_copies_exclus.sh`. Aucun chiffre ci-dessous n'est tapé à la main : tous sont
lus de ces mesures, et le générateur refuse d'écrire tant qu'un contrôle échoue.*

## 1. L'affirmation, et ce sur quoi elle repose désormais

Le papier rapporte **1 196 cas** sur les **1 251** cas BraTS-2023
GLI unifiés. La formulation publique antérieure — « les 55 restants ont des problèmes de format ou
des labels incohérents » — **n'était pas étayée par une mesure**. Cette note la remplace par ce qui
a été constaté, y compris là où elle était fausse.

| Grandeur | Valeur mesurée | Source |
|---|---|---|
| Dossiers patients unifiés (source) | 1 251 | `data/processed/brats_unified/` |
| Cas du jeu nnU-Net (destination) | 1 196 | `<nnUNet_raw>/Dataset001_BraTS2023GLI/labelsTr/` |
| Fichiers de modalités dans `imagesTr` | 4 784 = 1 196 × 4 | idem |
| `numTraining` de `dataset.json` | 1 196 | idem |
| **Cas exclus** | **55** (4.4 % de la source) | différence d'ensembles, `analysis/exclusions_1251_to_1196.csv` |
| Cas inclus sans dossier source | 0 | idem |

## 2. Pourquoi ces 55 cas ont été écartés — le mécanisme réel

Les 55 exclusions proviennent d'un unique filtre à la conversion
(`scripts/convert_brats_to_nnunet.py`) : un cas est sauté quand son identifiant, **ou celui de son
patient** (`BraTS-GLI-xxxxx`), figure dans `corrupted_patients.txt`.

| Déclencheur | Cas | Signification |
|---|---|---|
| Identifiant exact dans la liste | 5 | ajoutés le 2026-03-10 après `scripts/audit_feature_quality.py` (audit complet des 1 251 cas) |
| Identifiant patient dans la liste (expansion au patient) | 50 | la liste signalait 699 **acquisitions de suivi longitudinal** (suffixe `-100` … `-109`) appartenant à 272 patients ; le convertisseur écarte *tous* les cas de ces patients, d'où les 0 cas du jeu unifié (suffixe `-000`/`-001`) attrapés |

La liste elle-même : **706 lignes non vides, 705
identifiants uniques** (doublon : BraTS-GLI-01163-000 (2×)). Son historique git date les entrées —
- `2afb4ee98` 2026-03-05 : 701 lignes uniques (+701)
- `1332a2445` 2026-03-10 : 705 lignes uniques (+4)

Point décisif : les acquisitions de suivi qui constituent l'essentiel de la liste **ne font pas
partie du jeu unifié** (qui ne contient que des cas `-000` et `-001`) ; elles avaient été signalées
lors de la vérification du téléchargement. L'exclusion des 50 cas est donc une
**précaution au niveau patient, prise avant tout entraînement et toute métrique**, et non une
mesure faite sur ces fichiers.

## 3. Ces 55 fichiers exclus ont-ils réellement un défaut ? Non — mesuré

`scripts/audit_exclusions_integrity.py` a lu tous les fichiers des 55 cas exclus
et d'un échantillon témoin apparié de 55 cas inclus (graine 42) :
lisibilité NIfTI, forme, dtype, NaN, Inf, variance nulle, amplitude extrême, accord des affines
entre les quatre modalités et la segmentation, jeu de labels de la segmentation.

| Contrôle | Exclus (55) | Témoins (55) |
|---|---|---|
| Cas incomplets | 0 | 0 |
| Fichiers illisibles | 0 | 0 |
| Voxels NaN | 0 | 0 |
| Voxels Inf | 0 | 0 |
| Volumes à variance nulle | 0 | 0 |
| Amplitudes extrêmes | 0 | 0 |
| Affines divergents | 0 | 0 |
| Labels hors {0,1,2,3} | 0 | 0 |
| Formes observées | (240, 240, 155) | (240, 240, 155) |

Les deux groupes sont indiscernables sur chacun de ces contrôles. Détail par fichier :
`analysis/integrite_exclus_vs_temoins.csv` (régénérable à la demande).

## 4. Les cinq drapeaux de 03/2026 ne se reproduisent pas non plus

La note de session `14-03-2026.md` attribue des défauts précis aux 5 cas
marqués par identifiant exact (label de segmentation `34359738368 = 2^35`, un voxel Inf dans un T2,
un outlier d'intensité extrême). `scripts/sonde_5_cas_exclus.py` a rejoué ces contrôles **sur le
chemin de code littéral de cet audit** (`nib.load(...).get_fdata().astype(np.int64)`) :

| Cas | Défaut annoncé en 03/2026 | Mesuré aujourd'hui |
|---|---|---|
| `BraTS-GLI-00170-000` | label seg corrompu (34359738368) | NaN 0 · Inf 0 · voxels 2^35 0 · labels seg [0.0, 2.0, 3.0] · hors-jeu 0 · modalités lues 4 |
| `BraTS-GLI-00658-000` | label seg corrompu (34359738368) | NaN 0 · Inf 0 · voxels 2^35 0 · labels seg [0.0, 1.0, 2.0, 3.0] · hors-jeu 0 · modalités lues 4 |
| `BraTS-GLI-01433-000` | label seg corrompu (34359738368) | NaN 0 · Inf 0 · voxels 2^35 0 · labels seg [0.0, 1.0, 2.0] · hors-jeu 0 · modalités lues 4 |
| `BraTS-GLI-00219-000` | 1 voxel Inf dans T2 | NaN 0 · Inf 0 · voxels 2^35 0 · labels seg [0.0, 1.0, 2.0, 3.0] · hors-jeu 0 · modalités lues 4 |
| `BraTS-GLI-01163-000` | outlier extrême (z=30-35, 4 modalités) | NaN 0 · Inf 0 · voxels 2^35 0 · labels seg [0.0, 1.0, 2.0, 3.0] · hors-jeu 0 · modalités lues 4 |
| `BraTS-GLI-00000-000` *(témoin inclus)* | — | NaN 0 · Inf 0 · voxels 2^35 0 · labels seg [0.0, 1.0, 2.0, 3.0] · hors-jeu 0 · modalités lues 4 |
| `BraTS-GLI-00002-000` *(témoin inclus)* | — | NaN 0 · Inf 0 · voxels 2^35 0 · labels seg [0.0, 1.0, 2.0, 3.0] · hors-jeu 0 · modalités lues 4 |

Le rapport d'audit d'origine (`outputs/feature_audit/`) est ABSENT du dépôt : la preuve
de mars n'est plus consultable. Deux contrôles supplémentaires ferment l'hypothèse « une autre copie
était abîmée » : les trois copies survive du jeu unifié sur la machine (copie de travail NVMe, copie
de secours HDD, disque 8 To) sont **identiques octet pour octet** sur ces cas —
30 fichiers comparés sur 3 copies,
**0 divergence** — et leurs horodatages précèdent l'audit.

## 5. Ce que cela change, et ce que cela ne change pas

* **Aucun résultat ne change.** Tous les nombres du papier sont calculés sur le jeu nnU-Net de
  1 196 cas ; l'exclusion est en amont de tout entraînement et de toute métrique.
* **La validation croisée est une partition propre** (contrôlée par le même audit) :
  5 folds de 240 / 239 / 239 / 239 / 239 cas de validation, `val ∩ train = 0` dans
  chaque fold, et l'union des folds de validation vaut exactement les 1 196 cas —
  aucun patient n'est validé deux fois, aucune prédiction n'est in-fold.
* **La formulation doit être corrigée** : les 55 exclusions sont *conservatoires*
  (précaution au niveau patient consignée en mars 2026), et non la correction d'un défaut de fichier
  mesuré sur ces cas. Le texte v10 et le site le disent désormais ainsi, et renvoient ici.
* **Les réinclure n'est justifié par aucun défaut mesuré**, mais exigerait de reprétraiter et de
  réentraîner toute la validation croisée : cela changerait les nombres publiés. Nous conservons le
  jeu de 1 196 cas et publions la liste, pour que le lecteur borne l'effet
  (55/1 251 = 4.4 % des cas).

## 6. Reproduire cette note

```bash
python3 scripts/audit_exclusions_1251_1196.py       # 55 exclusions, raisons, folds  -> PASS/ÉCHEC
python3 scripts/audit_exclusions_integrity.py        # intégrité fichiers vs témoins -> PASS/ÉCHEC
python3 scripts/sonde_5_cas_exclus.py                # les cinq drapeaux de mars, re-mesurés
bash    scripts/compare_3_copies_exclus.sh           # md5 sur les trois copies du jeu
python3 scripts/paper1_exclusions_provenance.py      # cette note, régénérée depuis les mesures
```

Artefacts : `analysis/exclusions_1251_to_1196.csv` (les 55 identifiants, le
déclencheur, la date git de l'entrée de liste déclenchante), `analysis/exclusions_1251_to_1196.json`
(synthèse mesurée, historique de la liste, partition des folds),
`analysis/integrite_exclus_vs_temoins.csv` et `.json`, `analysis/sonde_5_cas_exacts.json`,
`analysis/comparaison_3_copies.tsv`.
