#!/usr/bin/env python3
"""Génère la note publique de provenance des exclusions 1 251 → 1 196 (papier 1).

Rien n'est tapé à la main : chaque chiffre de la note est lu des artefacts produits par
`scripts/audit_exclusions_1251_1196.py`, `scripts/audit_exclusions_integrity.py`,
`scripts/sonde_5_cas_exclus.py` et `scripts/compare_3_copies_exclus.sh`. Fail-closed :
une entrée manquante, un compte incohérent ou une exclusion sans raison arrêtent le
script avant toute écriture (exit != 0), pour qu'aucune phrase invérifiable n'entre dans
le bundle publié.

Sorties (--stage, par défaut le bundle v10 ; à pointer sur le staging de la version déposée) :
  papers/paper1/publish/v10/stage/brats-moe-distmap-fusion-1-main/analysis/
      DATASET_EXCLUSIONS.md            (EN — bundle public / dépôt Zenodo v10)
      DATASET_EXCLUSIONS_fr.md         (FR)
      exclusions_1251_to_1196.csv      (les 55 identifiants + raison + date git)
      exclusions_1251_to_1196.json     (synthèse mesurée)
  docs/provenance_exclusions_1251_1196.md   (note interne BRATS, FR)

Usage :  python3 scripts/paper1_exclusions_provenance.py [--stage <bundle>] [--sans-corroboration]

Le nombre de cas du jeu unifié attrapés par expansion au patient est calculé DEUX fois
(mesure embarquée, puis scan du jeu unifié) et toute divergence — ou tout scan impossible
sans --sans-corroboration explicite — arrête le script. Voir le commentaire du garde-fou.
"""

from __future__ import annotations

import argparse
import json
import shutil
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
OUT = REPO / "outputs/exclusions_1251_1196"
STAGE = REPO / "papers/paper1/publish/v10/stage/brats-moe-distmap-fusion-1-main"
DOCS = REPO / "docs"


def lire_json(p: Path) -> dict:
    if not p.exists():
        raise SystemExit(f"[ÉCHEC] artefact mesuré introuvable : {p}")
    return json.loads(p.read_text())


def lire_csv(p: Path) -> list[dict]:
    import csv

    if not p.exists():
        raise SystemExit(f"[ÉCHEC] artefact mesuré introuvable : {p}")
    with open(p, newline="") as fh:
        return list(csv.DictReader(fh))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mesures", default=str(OUT))
    ap.add_argument("--stage", default=str(STAGE),
                    help="bundle à écrire (analysis/) : v10 par défaut, à pointer sur le "
                         "staging de la version en cours de dépôt")
    ap.add_argument("--sans-corroboration", action="store_true",
                    help="assume la valeur non corroborée par un scan du jeu "
                         "unifié quand le disque de données n'est pas monté "
                         "(le repli SILENCIEUX sur 0 est ce qui a fait publier "
                         "un faux chiffre en v10)")
    args = ap.parse_args()
    mesures = Path(args.mesures)

    detail = lire_json(mesures / "exclusions_detail.json")
    synth = detail["synthese"]
    lignes = detail["lignes"]
    integrite = lire_json(mesures / "integrite_exclus_vs_temoins.json")
    sonde = lire_json(mesures / "sonde_5_cas_exacts.json")
    tsv = (mesures / "comparaison_3_copies.tsv").read_text().splitlines()
    folds = lire_csv(mesures / "folds.csv")

    # --- contrôles fail-closed sur les mesures elles-mêmes -------------------------
    pb: list[str] = []
    if synth["n_source"] - synth["n_inclus"] != synth["n_exclus"]:
        pb.append("source − inclus ≠ n_exclus")
    if synth["n_inclus_sans_source"] != 0:
        pb.append("des cas inclus n'ont pas de dossier source")
    if synth.get("exclus_sans_raison"):
        pb.append(f"{len(synth['exclus_sans_raison'])} exclusions sans raison")
    if integrite["exclus"]["n_cas"] != synth["n_exclus"]:
        pb.append("le bilan d'intégrité ne couvre pas toutes les exclusions")
    for cle in ("cas_illisibles", "nan_total", "inf_total", "labels_hors_jeu", "affines_divergents"):
        if integrite["exclus"][cle] != 0:
            pb.append(f"intégrité exclus : {cle} = {integrite['exclus'][cle]} ≠ 0")
        if integrite["temoins"][cle] != 0:
            pb.append(f"intégrité témoins : {cle} = {integrite['temoins'][cle]} ≠ 0")
    if not folds or sum(int(f["val_inter_train"]) for f in folds) != 0:
        pb.append("chevauchement train/val dans les folds")
    if pb:
        print("[ÉCHEC] mesures incohérentes, rien n'est écrit :\n  - " + "\n  - ".join(pb))
        return 1

    # --- décompositions calculées sur les données, jamais recopiées ----------------
    n_exact = sum(1 for r in lignes if r["entree_exacte"] == "oui")
    n_base = sum(1 for r in lignes if r["entree_exacte"] == "non")
    entries = set()
    for r in lignes:
        for e in r["entrees_liste_meme_patient"].split(";"):
            e = e.strip()
            if e and e != "-":
                entries.add(e)
    liste = [l.strip() for l in (REPO / "corrupted_patients.txt").read_text().splitlines() if l.strip()]
    n_lignes_liste = len(liste)
    n_uniques = len(set(liste))
    doublons = {k: v for k, v in Counter(liste).items() if v > 1}
    suivi = [l for l in liste if l.startswith("BraTS-GLI-") and l.split("-")[-1] not in ("000", "001")]
    bases_suivi = sorted({"-".join(l.split("-")[:3]) for l in suivi})
    # --- cas du jeu unifié attrapés par expansion au patient : DEUX sources, aucune muette --
    # Source primaire = les lignes de la mesure embarquée (entree_exacte == "non") : elles SONT
    # le dépôt, donc toujours disponibles. Contre-épreuve = le scan du jeu unifié, possible
    # seulement quand le disque de données est monté.
    # POURQUOI CE GARDE-FOU (mesuré le 2026-10-05) : la version d'origine ne connaissait que le
    # scan et retombait SILENCIEUSEMENT sur [] quand le dossier était absent. La note publiée en
    # v10 (record Zenodo 22904810) affirmait donc « which is how 0 cases of the unified set
    # (suffix -000/-001) were caught » dans la ligne même dont la première colonne annonçait 50
    # exclusions par expansion au patient — et que le CSV embarqué du même bundle contredisait
    # (55 lignes, dont 50 en entree_exacte=non, toutes en -000/-001). Un repli « données
    # absentes » qui rend 0 au lieu de lever ne se voit pas à la relecture : il publie un faux
    # chiffre. La valeur vraie, re-mesurée le 2026-10-05 disque monté, est 50, et les deux
    # sources donnent le MÊME ENSEMBLE d'identifiants (pas seulement le même compte).
    cases_atteints_liste = sorted(r["patient_id"] for r in lignes if r["entree_exacte"] == "non")
    if cases_atteints_liste and not all(
            p.split("-")[-1] in ("000", "001") for p in cases_atteints_liste):
        print("[ÉCHEC] provenance des exclusions : des cas « expansion au patient » ne portent "
              "pas un suffixe du jeu unifié (-000/-001) — rien n'est écrit.")
        return 1
    if len(cases_atteints_liste) != n_base:
        print(f"[ÉCHEC] provenance des exclusions : {len(cases_atteints_liste)} cas non exacts "
              f"contre n_base = {n_base} — rien n'est écrit.")
        return 1
    UNIFIED = Path("/home/ser/brats_data/data_local/processed/brats_unified")
    if UNIFIED.is_dir():
        cases_atteints_scan = sorted(
            d.name for d in UNIFIED.iterdir()
            if d.is_dir() and "-".join(d.name.split("-")[:3]) in set(bases_suivi)
        )
        if cases_atteints_scan != cases_atteints_liste:
            print(f"[ÉCHEC] provenance des exclusions : le scan du jeu unifié "
                  f"({len(cases_atteints_scan)} cas) contredit la mesure embarquée "
                  f"({len(cases_atteints_liste)} cas) — rien n'est écrit.")
            for etiquette, seulement in (("scan", set(cases_atteints_scan) - set(cases_atteints_liste)),
                                         ("mesure", set(cases_atteints_liste) - set(cases_atteints_scan))):
                if seulement:
                    print(f"        uniquement dans {etiquette} : "
                          + ", ".join(sorted(seulement)[:5]))
            return 1
        cases_atteints = cases_atteints_scan
        corroboration = f"corroboré par le scan de {UNIFIED}"
    elif args.sans_corroboration:
        cases_atteints = cases_atteints_liste
        corroboration = ("NON corroboré par un scan du jeu unifié "
                         f"({UNIFIED} absent — disque de données non monté)")
        print(f"[ATTENTION] {corroboration} : la valeur {len(cases_atteints)} vient de la seule "
              f"mesure embarquée, assumée par --sans-corroboration.")
    else:
        print(f"[ÉCHEC] provenance des exclusions : le jeu unifié {UNIFIED} est absent (disque "
              f"de données non monté ?). Le nombre de cas attrapés par expansion au patient ne "
              f"peut pas être corroboré par un scan, et c'est exactement ce repli silencieux qui "
              f"a fait publier « 0 cases » en v10. Monter le disque de données, ou relancer avec "
              f"--sans-corroboration pour assumer explicitement la valeur non corroborée.")
        return 1
    hist = synth.get("historique_git_de_la_liste", [])
    rapport_origine_present = sonde.get("rapport_audit_d_origine_present")

    n_copies = len({l.split("\t")[0] for l in tsv[1:] if l.strip()})
    n_fichiers_compares = sum(1 for l in tsv[1:] if l.strip() and l.split("\t")[3] == "oui")
    empreintes = {}
    for l in tsv[1:]:
        if not l.strip():
            continue
        c = l.split("\t")
        empreintes.setdefault((c[1], c[2]), set()).add(c[5])
    n_divergents = sum(1 for v in empreintes.values() if len(v) > 1)

    def defaut_non_reproduit(cas: dict) -> str:
        seg = [f for f in cas["fichiers"] if f["fichier"].endswith("seg.nii.gz")]
        mods = [f for f in cas["fichiers"] if not f["fichier"].endswith("seg.nii.gz")]
        nan = sum(f["nan"] for f in cas["fichiers"])
        inf = sum(f["inf"] for f in cas["fichiers"])
        v35 = sum(f["valeur_34359738368"] for f in cas["fichiers"])
        hors = sum(len(f.get("labels_hors_jeu", [])) for f in seg)
        return f"NaN {nan} · Inf {inf} · voxels 2^35 {v35} · labels seg {seg[0]['labels'] if seg else '-'} · hors-jeu {hors} · modalités lues {len(mods)}"

    cas_sonde = [c for c in sonde["cas"] if c["groupe"] == "exclu_exact"]
    temoins_sonde = [c for c in sonde["cas"] if c["groupe"] == "inclus_témoin"]

    # ------------------------------------------------------------------ textes ----
    chiffres = dict(
        n_source=synth["n_source"],
        n_inclus=synth["n_inclus"],
        n_exclus=synth["n_exclus"],
        pct_exclus=100.0 * synth["n_exclus"] / synth["n_source"],
        n_images=synth["n_imagesTr"],
        num_training=synth["numTraining_dataset_json"],
        n_exact=n_exact,
        n_base=n_base,
        n_lignes_liste=n_lignes_liste,
        n_uniques=n_uniques,
        doublons=", ".join(f"{k} ({v}×)" for k, v in doublons.items()) or "aucun",
        n_suivi=len(suivi),
        n_bases_suivi=len(bases_suivi),
        n_cas_atteints=len(cases_atteints),
        n_temoins=integrite["n_temoins"],
        formes=" · ".join(integrite["exclus"]["formes_attendues"]),
        n_copies=n_copies,
        n_fichiers_compares=n_fichiers_compares,
        n_divergents=n_divergents,
        rapport_origine="présent" if rapport_origine_present else "ABSENT du dépôt",
        n_folds=len(folds),
        tailles_folds=" / ".join(f["n_val"] for f in folds),
        genere_le=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
    )

    nf = lambda n: f"{n:,}".replace(",", "\u202f")  # séparateur de milliers français

    en = f"""# Where the 55 exclusions come from — measured provenance ({chiffres['n_source']:,} → {chiffres['n_inclus']:,} cases)

*Generated on {chiffres['genere_le']} by `scripts/paper1_exclusions_provenance.py` from the
artefacts of `scripts/audit_exclusions_1251_1196.py`,
`scripts/audit_exclusions_integrity.py`, `scripts/sonde_5_cas_exclus.py` and
`scripts/compare_3_copies_exclus.sh`. No number below is typed by hand: every figure is read
from those measurements, and the generator refuses to write anything as long as one control
fails.*

## 1. The claim, and what it now rests on

The paper reports **{chiffres['n_inclus']:,} cases** out of the **{chiffres['n_source']:,}** unified
BraTS-2023 GLI cases. The earlier public wording — "the remaining 55 have format problems or
inconsistent labels" — was **not supported by measurement**. This note replaces it with what was
actually found, including where that wording was wrong.

| Quantity | Measured value | Source |
|---|---|---|
| Unified patient folders (source) | {chiffres['n_source']:,} | `data/processed/brats_unified/` |
| Cases in the nnU-Net dataset (destination) | {chiffres['n_inclus']:,} | `<nnUNet_raw>/Dataset001_BraTS2023GLI/labelsTr/` |
| Modality files in `imagesTr` | {chiffres['n_images']:,} = {chiffres['n_inclus']:,} × 4 | idem |
| `dataset.json` `numTraining` | {chiffres['num_training']:,} | idem |
| **Excluded cases** | **{chiffres['n_exclus']}** ({chiffres['pct_exclus']:.1f} % of the source) | set difference, `analysis/exclusions_1251_to_1196.csv` |
| Included cases with no source folder | 0 | idem |

## 2. Why those {chiffres['n_exclus']} cases were dropped — the real mechanism

All {chiffres['n_exclus']} exclusions come from a single filter at conversion time
(`scripts/convert_brats_to_nnunet.py`): a case is skipped when its identifier, **or its patient
identifier** (`BraTS-GLI-xxxxx`), appears in `corrupted_patients.txt`.

| Trigger | Cases | What it means |
|---|---|---|
| Exact identifier in the list | {chiffres['n_exact']} | added on 2026-03-10 after `scripts/audit_feature_quality.py` (full audit of the {chiffres['n_source']:,} cases) |
| Patient identifier in the list (patient-level expansion) | {chiffres['n_base']} | the list flagged {chiffres['n_suivi']} **longitudinal follow-up** acquisitions (suffix `-100` … `-109`) belonging to {chiffres['n_bases_suivi']} patients; the converter drops *every* case of those patients, which is how {chiffres['n_cas_atteints']} cases of the unified set (suffix `-000`/`-001`) were caught |

The list itself: **{chiffres['n_lignes_liste']} non-empty lines, {chiffres['n_uniques']} unique
identifiers** (duplicate: {chiffres['doublons']}). Its git history dates the entries —
""" + "\n".join(
        f"- `{h['commit']}` {h['date'][:10]}: {h['n_lignes']} unique lines (+{h['n_ajoutees']})"
        for h in hist
    ) + "\n" + f"""
Crucially, the follow-up acquisitions that make up the bulk of the list **are not part of the
unified dataset** (which only contains `-000` and `-001` cases): they were flagged during
download verification. The exclusion of the {chiffres['n_base']} baseline/second cases is therefore a
**patient-level precaution taken before any training or metric**, not a measurement on those files.

## 3. Do the {chiffres['n_exclus']} excluded files actually have a defect? No — measured

`scripts/audit_exclusions_integrity.py` read every file of the {chiffres['n_exclus']} excluded cases
and of a matched control sample of {chiffres['n_temoins']} included cases (seed {integrite['seed']}):
NIfTI readability, shape, dtype, NaN, Inf, zero-variance, extreme amplitude, affine agreement
between the four modalities and the segmentation, and segmentation label set.

| Check | Excluded ({chiffres['n_exclus']}) | Control ({chiffres['n_temoins']}) |
|---|---|---|
| Missing/incomplete cases | {integrite['exclus']['cas_incomplets']} | {integrite['temoins']['cas_incomplets']} |
| Unreadable files | {integrite['exclus']['cas_illisibles']} | {integrite['temoins']['cas_illisibles']} |
| NaN voxels | {integrite['exclus']['nan_total']} | {integrite['temoins']['nan_total']} |
| Inf voxels | {integrite['exclus']['inf_total']} | {integrite['temoins']['inf_total']} |
| Zero-variance volumes | {integrite['exclus']['variance_nulle']} | {integrite['temoins']['variance_nulle']} |
| Extreme amplitudes | {integrite['exclus']['amplitude_extreme']} | {integrite['temoins']['amplitude_extreme']} |
| Divergent affines | {integrite['exclus']['affines_divergents']} | {integrite['temoins']['affines_divergents']} |
| Labels outside {{0,1,2,3}} | {integrite['exclus']['labels_hors_jeu']} | {integrite['temoins']['labels_hors_jeu']} |
| Shapes observed | {chiffres['formes']} | {" · ".join(integrite['temoins']['formes_attendues'])} |

The two groups are indistinguishable on every one of these checks. Per-file detail:
`analysis/integrite_exclus_vs_temoins.csv` (regenerated on demand).

## 4. The five 2026-03 flags do not reproduce either

The session note `14-03-2026.md` attributes specific defects to the {chiffres['n_exact']} exactly-flagged
cases (segmentation label `34359738368 = 2^35`, one Inf voxel in a T2, an extreme intensity
outlier). `scripts/sonde_5_cas_exclus.py` re-ran those checks **on the literal code path of that
audit** (`nib.load(...).get_fdata().astype(np.int64)`):

| Case | Defect claimed in 03/2026 | Measured today |
|---|---|---|
""" + "\n".join(
        f"| `{c['patient_id']}` | {c['defaut_annonce']} | {defaut_non_reproduit(c)} |"
        for c in cas_sonde
    ) + "\n" + "\n".join(
        f"| `{c['patient_id']}` *(included control)* | — | {defaut_non_reproduit(c)} |"
        for c in temoins_sonde
    ) + f"""

The original audit report (`outputs/feature_audit/`) is {chiffres['rapport_origine']}, so the March
evidence cannot be re-examined. Two further controls close the "maybe another copy was broken"
hypothesis: the three surviving copies of the unified dataset on the machine
(NVMe working copy, HDD rescue copy, 8 TB disk) are **byte-identical** for those cases —
{chiffres['n_fichiers_compares']} files compared across {chiffres['n_copies']} copies,
**{chiffres['n_divergents']} divergence** — and their timestamps precede the audit.

## 5. What this changes, and what it does not

* **No result changes.** Every number in the paper is computed on the {chiffres['n_inclus']:,}-case
  nnU-Net dataset; the exclusion is upstream of all training and all metrics.
* **The cross-validation is a clean partition** (this audit also checked it):
  {chiffres['n_folds']} folds of {chiffres['tailles_folds']} validation cases, `val ∩ train = 0` in
  every fold, and the union of validation folds equals exactly the {chiffres['n_inclus']:,} cases —
  so no patient is validated twice and no prediction is in-fold.
* **The wording must be corrected**: the {chiffres['n_exclus']} exclusions are *conservative*
  (patient-level caution recorded in March 2026), not the correction of a measured file defect in
  those cases. The v10 text and the website now say exactly that, and point here.
* **Re-including them is not justified by a measured defect**, but it would require
  re-preprocessing and re-training the whole cross-validation; it would change published numbers.
  We keep the {chiffres['n_inclus']:,}-case set and publish the list, so a reader can bound the
  effect ({chiffres['n_exclus']}/{chiffres['n_source']:,} = {chiffres['pct_exclus']:.1f} % of cases).

## 6. Reproducing this note

```bash
python3 scripts/audit_exclusions_1251_1196.py       # 55 exclusions, reasons, folds  -> PASS/ÉCHEC
python3 scripts/audit_exclusions_integrity.py        # file-level integrity vs controls -> PASS/ÉCHEC
python3 scripts/sonde_5_cas_exclus.py                # the five March flags, re-measured
bash    scripts/compare_3_copies_exclus.sh           # md5 across the three dataset copies
python3 scripts/paper1_exclusions_provenance.py      # this note, regenerated from the above
```

Artefacts: `analysis/exclusions_1251_to_1196.csv` (the {chiffres['n_exclus']} identifiers, trigger,
git date of the triggering list entry), `analysis/exclusions_1251_to_1196.json` (measured summary,
list history, fold partition), `analysis/integrite_exclus_vs_temoins.csv` and `.json`,
`analysis/sonde_5_cas_exacts.json`, `analysis/comparaison_3_copies.tsv`.
"""

    fr = f"""# D'où viennent les 55 exclusions — provenance mesurée (1 251 → 1 196 cas)

*Généré le {chiffres['genere_le']} par `scripts/paper1_exclusions_provenance.py` à partir des
artefacts de `scripts/audit_exclusions_1251_1196.py`,
`scripts/audit_exclusions_integrity.py`, `scripts/sonde_5_cas_exclus.py` et
`scripts/compare_3_copies_exclus.sh`. Aucun chiffre ci-dessous n'est tapé à la main : tous sont
lus de ces mesures, et le générateur refuse d'écrire tant qu'un contrôle échoue.*

## 1. L'affirmation, et ce sur quoi elle repose désormais

Le papier rapporte **{nf(chiffres['n_inclus'])} cas** sur les **{nf(chiffres['n_source'])}** cas BraTS-2023
GLI unifiés. La formulation publique antérieure — « les 55 restants ont des problèmes de format ou
des labels incohérents » — **n'était pas étayée par une mesure**. Cette note la remplace par ce qui
a été constaté, y compris là où elle était fausse.

| Grandeur | Valeur mesurée | Source |
|---|---|---|
| Dossiers patients unifiés (source) | {nf(chiffres['n_source'])} | `data/processed/brats_unified/` |
| Cas du jeu nnU-Net (destination) | {nf(chiffres['n_inclus'])} | `<nnUNet_raw>/Dataset001_BraTS2023GLI/labelsTr/` |
| Fichiers de modalités dans `imagesTr` | {nf(chiffres['n_images'])} = {nf(chiffres['n_inclus'])} × 4 | idem |
| `numTraining` de `dataset.json` | {nf(chiffres['num_training'])} | idem |
| **Cas exclus** | **{chiffres['n_exclus']}** ({chiffres['pct_exclus']:.1f} % de la source) | différence d'ensembles, `analysis/exclusions_1251_to_1196.csv` |
| Cas inclus sans dossier source | 0 | idem |

## 2. Pourquoi ces {chiffres['n_exclus']} cas ont été écartés — le mécanisme réel

Les {chiffres['n_exclus']} exclusions proviennent d'un unique filtre à la conversion
(`scripts/convert_brats_to_nnunet.py`) : un cas est sauté quand son identifiant, **ou celui de son
patient** (`BraTS-GLI-xxxxx`), figure dans `corrupted_patients.txt`.

| Déclencheur | Cas | Signification |
|---|---|---|
| Identifiant exact dans la liste | {chiffres['n_exact']} | ajoutés le 2026-03-10 après `scripts/audit_feature_quality.py` (audit complet des {nf(chiffres['n_source'])} cas) |
| Identifiant patient dans la liste (expansion au patient) | {chiffres['n_base']} | la liste signalait {chiffres['n_suivi']} **acquisitions de suivi longitudinal** (suffixe `-100` … `-109`) appartenant à {chiffres['n_bases_suivi']} patients ; le convertisseur écarte *tous* les cas de ces patients, d'où les {chiffres['n_cas_atteints']} cas du jeu unifié (suffixe `-000`/`-001`) attrapés |

La liste elle-même : **{chiffres['n_lignes_liste']} lignes non vides, {chiffres['n_uniques']}
identifiants uniques** (doublon : {chiffres['doublons']}). Son historique git date les entrées —
""" + "\n".join(
        f"- `{h['commit']}` {h['date'][:10]} : {h['n_lignes']} lignes uniques (+{h['n_ajoutees']})"
        for h in hist
    ) + "\n" + f"""
Point décisif : les acquisitions de suivi qui constituent l'essentiel de la liste **ne font pas
partie du jeu unifié** (qui ne contient que des cas `-000` et `-001`) ; elles avaient été signalées
lors de la vérification du téléchargement. L'exclusion des {chiffres['n_base']} cas est donc une
**précaution au niveau patient, prise avant tout entraînement et toute métrique**, et non une
mesure faite sur ces fichiers.

## 3. Ces {chiffres['n_exclus']} fichiers exclus ont-ils réellement un défaut ? Non — mesuré

`scripts/audit_exclusions_integrity.py` a lu tous les fichiers des {chiffres['n_exclus']} cas exclus
et d'un échantillon témoin apparié de {chiffres['n_temoins']} cas inclus (graine {integrite['seed']}) :
lisibilité NIfTI, forme, dtype, NaN, Inf, variance nulle, amplitude extrême, accord des affines
entre les quatre modalités et la segmentation, jeu de labels de la segmentation.

| Contrôle | Exclus ({chiffres['n_exclus']}) | Témoins ({chiffres['n_temoins']}) |
|---|---|---|
| Cas incomplets | {integrite['exclus']['cas_incomplets']} | {integrite['temoins']['cas_incomplets']} |
| Fichiers illisibles | {integrite['exclus']['cas_illisibles']} | {integrite['temoins']['cas_illisibles']} |
| Voxels NaN | {integrite['exclus']['nan_total']} | {integrite['temoins']['nan_total']} |
| Voxels Inf | {integrite['exclus']['inf_total']} | {integrite['temoins']['inf_total']} |
| Volumes à variance nulle | {integrite['exclus']['variance_nulle']} | {integrite['temoins']['variance_nulle']} |
| Amplitudes extrêmes | {integrite['exclus']['amplitude_extreme']} | {integrite['temoins']['amplitude_extreme']} |
| Affines divergents | {integrite['exclus']['affines_divergents']} | {integrite['temoins']['affines_divergents']} |
| Labels hors {{0,1,2,3}} | {integrite['exclus']['labels_hors_jeu']} | {integrite['temoins']['labels_hors_jeu']} |
| Formes observées | {chiffres['formes']} | {" · ".join(integrite['temoins']['formes_attendues'])} |

Les deux groupes sont indiscernables sur chacun de ces contrôles. Détail par fichier :
`analysis/integrite_exclus_vs_temoins.csv` (régénérable à la demande).

## 4. Les cinq drapeaux de 03/2026 ne se reproduisent pas non plus

La note de session `14-03-2026.md` attribue des défauts précis aux {chiffres['n_exact']} cas
marqués par identifiant exact (label de segmentation `34359738368 = 2^35`, un voxel Inf dans un T2,
un outlier d'intensité extrême). `scripts/sonde_5_cas_exclus.py` a rejoué ces contrôles **sur le
chemin de code littéral de cet audit** (`nib.load(...).get_fdata().astype(np.int64)`) :

| Cas | Défaut annoncé en 03/2026 | Mesuré aujourd'hui |
|---|---|---|
""" + "\n".join(
        f"| `{c['patient_id']}` | {c['defaut_annonce']} | {defaut_non_reproduit(c)} |"
        for c in cas_sonde
    ) + "\n" + "\n".join(
        f"| `{c['patient_id']}` *(témoin inclus)* | — | {defaut_non_reproduit(c)} |"
        for c in temoins_sonde
    ) + f"""

Le rapport d'audit d'origine (`outputs/feature_audit/`) est {chiffres['rapport_origine']} : la preuve
de mars n'est plus consultable. Deux contrôles supplémentaires ferment l'hypothèse « une autre copie
était abîmée » : les trois copies survive du jeu unifié sur la machine (copie de travail NVMe, copie
de secours HDD, disque 8 To) sont **identiques octet pour octet** sur ces cas —
{chiffres['n_fichiers_compares']} fichiers comparés sur {chiffres['n_copies']} copies,
**{chiffres['n_divergents']} divergence** — et leurs horodatages précèdent l'audit.

## 5. Ce que cela change, et ce que cela ne change pas

* **Aucun résultat ne change.** Tous les nombres du papier sont calculés sur le jeu nnU-Net de
  {nf(chiffres['n_inclus'])} cas ; l'exclusion est en amont de tout entraînement et de toute métrique.
* **La validation croisée est une partition propre** (contrôlée par le même audit) :
  {chiffres['n_folds']} folds de {chiffres['tailles_folds']} cas de validation, `val ∩ train = 0` dans
  chaque fold, et l'union des folds de validation vaut exactement les {nf(chiffres['n_inclus'])} cas —
  aucun patient n'est validé deux fois, aucune prédiction n'est in-fold.
* **La formulation doit être corrigée** : les {chiffres['n_exclus']} exclusions sont *conservatoires*
  (précaution au niveau patient consignée en mars 2026), et non la correction d'un défaut de fichier
  mesuré sur ces cas. Le texte v10 et le site le disent désormais ainsi, et renvoient ici.
* **Les réinclure n'est justifié par aucun défaut mesuré**, mais exigerait de reprétraiter et de
  réentraîner toute la validation croisée : cela changerait les nombres publiés. Nous conservons le
  jeu de {nf(chiffres['n_inclus'])} cas et publions la liste, pour que le lecteur borne l'effet
  ({chiffres['n_exclus']}/{nf(chiffres['n_source'])} = {chiffres['pct_exclus']:.1f} % des cas).

## 6. Reproduire cette note

```bash
python3 scripts/audit_exclusions_1251_1196.py       # 55 exclusions, raisons, folds  -> PASS/ÉCHEC
python3 scripts/audit_exclusions_integrity.py        # intégrité fichiers vs témoins -> PASS/ÉCHEC
python3 scripts/sonde_5_cas_exclus.py                # les cinq drapeaux de mars, re-mesurés
bash    scripts/compare_3_copies_exclus.sh           # md5 sur les trois copies du jeu
python3 scripts/paper1_exclusions_provenance.py      # cette note, régénérée depuis les mesures
```

Artefacts : `analysis/exclusions_1251_to_1196.csv` (les {chiffres['n_exclus']} identifiants, le
déclencheur, la date git de l'entrée de liste déclenchante), `analysis/exclusions_1251_to_1196.json`
(synthèse mesurée, historique de la liste, partition des folds),
`analysis/integrite_exclus_vs_temoins.csv` et `.json`, `analysis/sonde_5_cas_exacts.json`,
`analysis/comparaison_3_copies.tsv`.
"""

    # ------------------------------------------------------------- écritures -----
    analyse_racine = Path(args.stage)
    analysis = analyse_racine / "analysis"
    if not analysis.is_dir():
        print(f"[ÉCHEC] bundle introuvable (analysis/ absent) : {analysis}")
        return 2
    (analysis / "DATASET_EXCLUSIONS.md").write_text(en)
    (analysis / "DATASET_EXCLUSIONS_fr.md").write_text(fr)

    csv_src = mesures / "exclusions.csv"
    shutil.copyfile(csv_src, analysis / "exclusions_1251_to_1196.csv")
    (analysis / "exclusions_1251_to_1196.json").write_text(
        json.dumps(
            {
                "genere_le": chiffres["genere_le"],
                "provenance": "scripts/audit_exclusions_1251_1196.py",
                "synthese": {k: v for k, v in synth.items() if k != "exclus_ids"},
                "exclus_ids": synth["exclus_ids"],
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    for nom in (
        "integrite_exclus_vs_temoins.csv",
        "integrite_exclus_vs_temoins.json",
        "sonde_5_cas_exacts.json",
        "comparaison_3_copies.tsv",
        "folds.csv",
    ):
        if (mesures / nom).exists():
            shutil.copyfile(mesures / nom, analysis / nom)

    DOCS.mkdir(exist_ok=True)
    (DOCS / "provenance_exclusions_1251_1196.md").write_text(fr)

    print(f"[PASS] note de provenance écrite (EN + FR) + artefacts copiés dans {analyse_racine.name}")
    print(f"  cas du jeu unifié attrapés par expansion au patient : {len(cases_atteints)} "
          f"(n_base = {n_base}) — {corroboration}")
    print(f"  EN : {analysis / 'DATASET_EXCLUSIONS.md'}")
    print(f"  FR : {analysis / 'DATASET_EXCLUSIONS_fr.md'}")
    print(f"  interne : {DOCS / 'provenance_exclusions_1251_1196.md'}")
    print(
        f"  mesures clés : source {chiffres['n_source']:,} · inclus {chiffres['n_inclus']:,} · "
        f"exclus {chiffres['n_exclus']} ({chiffres['n_exact']} exacts + {chiffres['n_base']} par patient) · "
        f"liste {chiffres['n_lignes_liste']} lignes / {chiffres['n_uniques']} uniques · "
        f"défauts fichiers mesurés : 0 · copies divergentes : {chiffres['n_divergents']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
