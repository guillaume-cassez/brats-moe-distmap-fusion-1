# Provenance des tableaux A/B du §5.6 — mesure du 2026-09-16 (carte #205, tâche 4)

**Verdict : le §5.6 du manuscrit FR révisé — et donc du EN v10 assemblé et des deux PDF
buildés ce jour — cite la run que le dépôt marque lui-même `_obsolete`.** Le §5.6 publié en
v9 (EN et FR) citait, lui, la run courante et complète. Déposer la v10 en l'état publierait
un retour silencieux à des résultats périmés dans une archive non retirable.

## 1. Le symptôme

Le corps EN v10 (§5.6 « Robustness to the training seed ») porte :

| Grandeur | FR révisé / EN v10 (staged) | v9 publié (EN ligne 386-424, FR ligne 391-429) |
|---|---|---|
| paires valides | « ≈719 paires, 684 pour le consensus, ~5 % d'échecs » | « 720 paires valides » |
| LW Dice WT Baseline | **0,7815 ± 0,0057** | **0,8103 ± 0,0080** |
| LW Dice WT DistMap | 0,8004 ± 0,0113 (+1,89 pp, p_wc 0,23 n.s.) | 0,8257 ± 0,0081 (+1,54 pp, **p_wc 0,041 significatif**) |
| LW Dice WT CC(D∩B) | 0,8230 ± 0,0085 (+4,15 pp, p_wc 0,006) | 0,8531 ± 0,0041 (**+4,28 pp**, p_wc 5,5×10⁻⁵) |
| LW HD95 WT Baseline → CC | 65,9 ± 2,2 → 49,1 ± 3,5 mm (−16,8, p_wc 0,005) | 54,52 ± 2,84 → **37,31 ± 2,18 mm** (−17,21, p_wc 6,0×10⁻⁵) |
| Legacy Dice ET Baseline | 0,8653 ± 0,0046 | 0,8668 ± 0,0029 |
| Legacy HD95 ET Baseline | 13,72 ± 1,91 mm | 13,8509 ± 1,3345 mm |

Deux effets publiés changent de nature, pas seulement de valeur : le gain du consensus passe
de p < 10⁻⁴ à p = 0,006 et de +4,28 à +4,15 pp ; et **l'unique effet significatif de DistMap
sur LW Dice WT (p = 0,041) disparaît** (p = 0,23), la phrase « seule LW Dice WT franchit le
seuil » devenant « aucune des 12 comparaisons n'est significative ».

## 2. La mesure qui tranche

Deux artefacts coexistent sur la Tour, produits le même jour à 45 minutes d'écart :

| Artefact | md5 | LW Dice WT B | n Wilcoxon | Complétude |
|---|---|---|---|---|
| `outputs/multiseed/stats.json` (15/06 **11:23**, run courante) | `fe5d513e563a0bc946db983c93e8013f` | **0,8103** ± 0,0080 | 720 | `per_patient.csv` **4320 lignes** = 3 graines × 240 patients × 3 régions × 2 configs, 18/18 groupes à 240 ; `consensus_per_patient.csv` **2160 lignes**, 9/9 groupes à 240 |
| `outputs/multiseed/_obsolete_20260615_105454/stats.json` (15/06 **10:54**) | `571b43aecdca77360208672c8490fdda` | **0,7815** ± 0,0057 | **719** / **684** | `per_patient.csv` 4315 lignes, **5/18 groupes incomplets** (min 239) ; `consensus_per_patient.csv` 2052 lignes, **9/9 groupes incomplets** (min 226, max 231 — il manque 108 mesures, ≈5 %) |

Les 12 valeurs du tableau A et les 12 du tableau B du §5.6 révisé se retrouvent **une à une,
à l'arrondi près, dans le fichier `_obsolete`** — y compris `n_wilcoxon = 719` et `684`, que le
manuscrit cite texto (« ≈719 paires valides pour comparaison directe, 684 pour consensus,
~5 % d'échecs BraTS-Metrics »). Le §5.6 révisé décrit donc littéralement la run ratée :
celle dont le scorer officiel n'a pas abouti sur ~5 % des cas de consensus (cf. la fiche
mémoire « le scorer officiel plante sporadiquement »), relancée intégralement 29 minutes plus
tard (`rerun_20260615.log` : « 240 total, 0 skip, 240 to run » sur les 6 configs, puis
« main: 4320 rows, consensus: 2160 rows »).

Contre-vérification indépendante : agrégation refaite ce jour depuis
`outputs/multiseed/per_patient.csv` + `consensus_per_patient.csv` (moyenne des moyennes par
graine) → LW Dice WT Baseline **0,8103** (par graine 0,8053 / 0,8039 / 0,8216), DistMap
**0,8257**, CC(D∩B) **0,8531** ; LW HD95 WT Baseline **54,52**, CC **37,31**. Soit
exactement `stats.json` courant, `table_variance.md` (md5 `9a7a024f346cbfbc054ae512e5ddb42f`)
et le §5.6 des deux manuscrits v9 publiés. Aucun artefact du dépôt ne produit 0,7815 en
dehors du dossier `_obsolete`.

## 3. Où la régression est entrée

- `git log -S"0,7815"` (papier 1) : la valeur apparaît pour la première fois dans
  `papers/paper4/CADRAGE.md` (commit `55f1b74ad` → repris par `f16768fe4`, 16/07) comme
  « réf. Paper 1, métriques officielles », puis dans `papers/paper1/publish/repo/paper_fr.md`
  à sa création par `f32033f4c` (22/07). Aucun commit du papier 1 n'a jamais contenu `0,8103`
  côté FR : **le FR de travail est né sur la run obsolète**, alors que le FR *publié* en v9
  (dans l'archive Zenodo) portait les bons chiffres.
- Le portage EN v10 (commits `a8c31e8d1`, `9c2e0df9a`) a fidèlement propagé la régression :
  le contrôle fail-closed `check_en_v10.py` vérifie l'égalité numérique EN ↔ FR, donc il ne
  pouvait pas la voir — les deux langues citaient la même run périmée.
- Périmètre mesuré de la contamination (`grep -rl` sur les `.md/.json/.yaml/.py` du dépôt,
  hors `_v9ref`) : `papers/paper1/publish/repo/paper_fr.md` (5 sites), `repo/paper.md` (5),
  `v10/paper.md` (5), `papers/paper4/CADRAGE.md` (2 : « 0,7815 → 0,8004 » et « +4,15 pp /
  −16,8 mm » cité comme cible à reproduire), et l'artefact obsolète lui-même. Le papier 2
  publiés utilise `papers/paper2/publish/repo/data/multiseed_stats.json`, qui porte
  **0,8103** (run courante) : il n'est pas touché.

## 4. Décision

1. **Ne pas déposer la v10 avant correction.** Un dépôt Zenodo est irrémédiable (la version
   et son DOI persistent) : publier un §5.6 qui revient en arrière sur des résultats déjà
   publiés, sans erratum et sans artefact qui le soutienne, est précisément le risque à éviter.
2. **Restaurer le §5.6 des deux langues depuis la run courante.** La source est doublement
   disponible et concordante : `outputs/multiseed/table_variance.md` (artefact) et le §5.6 des
   manuscrits v9 (FR ligne 391-429, EN ligne 386-424) — donc le texte FR correct existe déjà
   en français, il n'y a rien à réinventer. Les retailles de la révision du 01/09 sur le reste
   de la section sont conservées ; seuls les tableaux A/B et les phrases chiffrées reviennent
   à la run complète (n = 720, 0,8103/+4,28 pp/−17,21 mm, DistMap p = 0,041).
3. **Rendre la v10 auto-vérifiable sur ce point**, ce que la v9 ne permettait pas : aucun
   artefact multi-graine n'était archivé. Le bundle v10 embarque
   `data/multiseed/{stats.json,table_variance.md,per_patient.csv,consensus_per_patient.csv}`
   (≈936 Ko) et un contrôle de plus (`check_en_v10.py` C11) exige que chaque nombre du §5.6
   soit présent dans `stats.json` et que les signatures de la run obsolète (0,7815 / 0,8230 /
   65,9 / 719 / 684 / +4,15 pp) soient **absentes** des manuscrits.
4. `papers/paper4/CADRAGE.md` cite les mêmes chiffres périmés comme cible à battre : à
   réaligner sur 0,8103 → 0,8257 / +4,28 pp / −17,2 mm (chantier papier 4, gelé — correction
   de citation seulement, pas de relance).

## 5. Inventaire v9 mesuré (pour la tâche 4)

`v9_inventory.json` (généré ce jour) : archive re-téléchargée depuis
`https://zenodo.org/api/records/21168405/files/brats-moe-distmap-fusion-1.zip/content`,
13 251 876 o, md5 `7e85761d10312ee9d8448ef435c2f686` **identique au md5 déclaré par Zenodo**,
76 entrées dont 70 fichiers (17 705 333 o décompressés), racine
`brats-moe-distmap-fusion-1-main/` — c'est l'export du dépôt GitHub supplément. Aucun des
fichiers `analysis/`, `data/`, `scripts/` (19 scripts) de ce bundle n'existe plus dans
l'espace de travail BRATS (mesuré par `find` sur la Tour) : **l'archive Zenodo v9 et son
supplément GitHub en sont les seules copies**, donc le staging v10 doit partir de l'archive
v9 et n'y substituer que les fichiers réellement révisés.

## 6. Complément de mesure du 2026-09-17 — pourquoi les deux runs diffèrent

Le §2 laissait entendre que la run obsolète diffère surtout par sa complétude (5 lignes
manquantes sur 4320, 108 sur 2160). La comparaison **cas par cas** des deux
`per_patient.csv` et `consensus_per_patient.csv` dit autre chose, et c'est elle qui fonde
la restauration :

| Mesure (clés communes aux deux runs) | Valeur |
|---|---|
| clés communes | 4315 (main) · 2052 (consensus) |
| `legacy_dice` différent | 558 clés, médiane \|Δ\| = **0,00001**, 553/558 dans le sens courant > obsolète |
| `lw_dice` différent | 458 clés, médiane \|Δ\| = **0,4465**, 455/458 dans le sens courant > obsolète |
| `num_fp` différent | 337 clés, **336/337** avec obsolète > courant (dont 278 exactement « 1 faux positif → 0 ») |

Signature sans ambiguïté : le Dice volumétrique bouge à peine (retrait de quelques voxels)
pendant que le Dice lesion-wise bondit et que le comptage de faux positifs lésionnaires
disparaît. C'est exactement l'effet du retrait des amas parasites (`clean_small_components`,
seuils officiels WT 1000 / TC 250 / ET 500 voxels, `src/brats_eval/decoding.py`) —
c'est-à-dire le protocole que le v9 énonce (« sur des prédictions vérifiées exemptes de
fragments résiduels ») et que le §5.1/§5.3 du même manuscrit appliquent. La run obsolète est
la même évaluation **sans** ce nettoyage : c'est pour cela que sa baseline lesion-wise vaut
0,7815 au lieu de 0,8103, et que le paragraphe « Ce recadrage est délibéré » du v9 la
décrivait comme une version antérieure artefactée.

Corroboration temporelle : les prédictions évaluées n'ont pas été réécrites entre les deux
runs (NIfTI de validation Baseline du 2026-06-09 02h48-02h52, consensus_DB du 2026-06-12
11h32-11h48) et le fork local du scoreur (`external/BraTS-2023-Metrics/metrics.py`) date du
2026-06-08 10h02 — la différence ne vient donc ni des volumes ni du code de scoring, mais du
régime de pré-traitement appliqué aux prédictions avant évaluation.

Conséquence pour la v10 : la restauration du §5.6 sur la run courante est un **retour au
régime publié et au protocole officiel du manuscrit**, pas une nouvelle mesure. Deux
corrections d'arrondi accompagnent le retour aux valeurs de l'artefact (p Wilcoxon Legacy
Dice ET 0,64 → 0,63 et Legacy Dice TC tableau B 0,57 → 0,56, l'artefact donnant 0,6349 et
0,5647), et la borne « \|Δ\| < 1,4 pp et < 1,4 mm » du v9, fausse sur ET LW HD95 (+1,89 mm),
est remplacée par les bornes mesurées « < 0,6 pp sur LW Dice et < 1,9 mm sur LW HD95 ».
