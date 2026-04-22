#!/usr/bin/env python3
"""Per-region meta-selector : for each patient and each region (WT/TC/ET),
train a classifier to predict argmax(B, D, F). Combine the 3 picks into a
per-patient Dice avg and compare to default fusion + oracle.

Features : 20 morpho (patient_features.csv) + 11 agreement (patient_agreement_features.csv) = 31.
"""
import csv
import json
from pathlib import Path
from collections import Counter

import numpy as np
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import KFold

ROOT = Path(__file__).parent
FEATS_MORPHO = ROOT / "cases_out" / "patient_features.csv"
FEATS_AGREE = ROOT / "cases_out" / "patient_agreement_features.csv"
RANK = Path("/tmp/rankings.json")
OUT = ROOT / "analysis_out" / "meta_selector_perregion.txt"

# ---- Load features ----
morpho = {r["patient_id"]: r for r in csv.DictReader(FEATS_MORPHO.open())}
agree = {r["patient_id"]: r for r in csv.DictReader(FEATS_AGREE.open())}
MORPHO_COLS = [k for k in next(iter(morpho.values())).keys() if k not in ("patient_id", "fold")]
AGREE_COLS = [k for k in next(iter(agree.values())).keys() if k != "patient_id"]
ALL_FEATS = MORPHO_COLS + AGREE_COLS
print(f"morpho cols: {len(MORPHO_COLS)}  agree cols: {len(AGREE_COLS)}  total: {len(ALL_FEATS)}")

# ---- Load rankings ----
data = json.loads(RANK.read_text())
rows = []
for r in data["rows"]:
    pid = r["patient_id"]
    if pid not in morpho or pid not in agree: continue
    b, d, f = r.get("baseline"), r.get("distmap"), r.get("fusion")
    if not (b and d and f): continue
    if any(b.get(f"dice_{reg}") is None or d.get(f"dice_{reg}") is None or f.get(f"dice_{reg}") is None
           for reg in ("WT","TC","ET")): continue
    feats = {}
    for c in MORPHO_COLS: feats[c] = float(morpho[pid][c] or 0)
    for c in AGREE_COLS: feats[c] = float(agree[pid][c] or 0)
    rows.append({
        "pid": pid, "fold": r.get("fold", "0"),
        "B_WT": b["dice_WT"], "B_TC": b["dice_TC"], "B_ET": b["dice_ET"],
        "D_WT": d["dice_WT"], "D_TC": d["dice_TC"], "D_ET": d["dice_ET"],
        "F_WT": f["dice_WT"], "F_TC": f["dice_TC"], "F_ET": f["dice_ET"],
        "feats": feats,
    })
print(f"n = {len(rows)} patients")

X = np.array([[r["feats"][fn] for fn in ALL_FEATS] for r in rows])
REGIONS = ["WT", "TC", "ET"]

report = []
def log(s=""): report.append(s); print(s)

# Reference means
b_avg = np.mean([(r["B_WT"] + r["B_TC"] + r["B_ET"]) / 3 for r in rows])
d_avg = np.mean([(r["D_WT"] + r["D_TC"] + r["D_ET"]) / 3 for r in rows])
f_avg = np.mean([(r["F_WT"] + r["F_TC"] + r["F_ET"]) / 3 for r in rows])
oracle_patient = np.mean([max((r["B_WT"]+r["B_TC"]+r["B_ET"])/3,
                               (r["D_WT"]+r["D_TC"]+r["D_ET"])/3,
                               (r["F_WT"]+r["F_TC"]+r["F_ET"])/3) for r in rows])
oracle_class = np.mean([(max(r["B_WT"], r["D_WT"], r["F_WT"]) +
                         max(r["B_TC"], r["D_TC"], r["F_TC"]) +
                         max(r["B_ET"], r["D_ET"], r["F_ET"])) / 3 for r in rows])

log(f"=== References (Dice avg, n={len(rows)}) ===")
log(f"  Baseline only         : {b_avg:.6f}")
log(f"  DistMap only          : {d_avg:.6f}")
log(f"  Fusion default        : {f_avg:.6f}")
log(f"  Oracle patient-level  : {oracle_patient:.6f}  (+{oracle_patient - f_avg:+.6f})")
log(f"  Oracle per-class      : {oracle_class:.6f}  (+{oracle_class - f_avg:+.6f})")

# ---- Per-region meta-classifier (3 models, one per region) ----
def run_classifier_family(X, rows, clf_factory, name):
    picks_per_region = {reg: [None] * len(rows) for reg in REGIONS}
    accs = {}
    kf = KFold(n_splits=5, shuffle=True, random_state=42)
    for reg in REGIONS:
        y = np.array([["B", "D", "F"][int(np.argmax([r[f"B_{reg}"], r[f"D_{reg}"], r[f"F_{reg}"]]))] for r in rows])
        correct = 0
        for tr, te in kf.split(X):
            clf = clf_factory()
            clf.fit(X[tr], y[tr])
            preds = clf.predict(X[te])
            for idx, p in zip(te, preds):
                picks_per_region[reg][idx] = p
            correct += int((preds == y[te]).sum())
        accs[reg] = correct / len(rows)

    # Combine per-patient
    scores = []
    pick_counter = Counter()
    for i, r in enumerate(rows):
        total = 0
        for reg in REGIONS:
            p = picks_per_region[reg][i]
            pick_counter[f"{reg}_{p}"] += 1
            total += r[f"{p}_{reg}"]
        scores.append(total / 3)
    mean = np.mean(scores)
    log(f"\n=== {name} (5-fold CV, per-region) ===")
    log(f"  mean Dice avg         : {mean:.6f}")
    log(f"  vs fusion default     : {mean - f_avg:+.6f}")
    log(f"  vs oracle per-class   : {mean - oracle_class:+.6f}")
    log(f"  argmax accuracy per region : " + ", ".join(f"{reg}={accs[reg]:.3f}" for reg in REGIONS))
    log(f"  pick distribution     : WT: B={pick_counter['WT_B']} D={pick_counter['WT_D']} F={pick_counter['WT_F']}  "
        f"TC: B={pick_counter['TC_B']} D={pick_counter['TC_D']} F={pick_counter['TC_F']}  "
        f"ET: B={pick_counter['ET_B']} D={pick_counter['ET_D']} F={pick_counter['ET_F']}")
    return mean

# Try multiple classifiers
run_classifier_family(
    X, rows,
    lambda: RandomForestClassifier(n_estimators=400, min_samples_leaf=3, class_weight="balanced", random_state=0, n_jobs=-1),
    "META-RF (31 features)"
)

# LR with standardization
def make_lr():
    from sklearn.pipeline import Pipeline
    return Pipeline([("s", StandardScaler()), ("l", LogisticRegression(max_iter=2000, class_weight="balanced", random_state=0))])

run_classifier_family(X, rows, make_lr, "META-LR (31 features)")

run_classifier_family(
    X, rows,
    lambda: GradientBoostingClassifier(n_estimators=300, max_depth=3, random_state=0),
    "META-GBM (31 features)"
)

# Ablation : morpho only (20), agreement only (11)
X_morpho = np.array([[r["feats"][fn] for fn in MORPHO_COLS] for r in rows])
X_agree = np.array([[r["feats"][fn] for fn in AGREE_COLS] for r in rows])
run_classifier_family(
    X_morpho, rows,
    lambda: RandomForestClassifier(n_estimators=400, min_samples_leaf=3, class_weight="balanced", random_state=0, n_jobs=-1),
    "META-RF (20 morpho only)"
)
run_classifier_family(
    X_agree, rows,
    lambda: RandomForestClassifier(n_estimators=400, min_samples_leaf=3, class_weight="balanced", random_state=0, n_jobs=-1),
    "META-RF (11 agreement only)"
)

# ---- Feature importance on full data (per region) ----
log(f"\n=== RF feature importance per region (trained on all data) ===")
for reg in REGIONS:
    y = np.array([["B", "D", "F"][int(np.argmax([r[f"B_{reg}"], r[f"D_{reg}"], r[f"F_{reg}"]]))] for r in rows])
    clf = RandomForestClassifier(n_estimators=400, min_samples_leaf=3, class_weight="balanced", random_state=0, n_jobs=-1)
    clf.fit(X, y)
    imp = sorted(zip(ALL_FEATS, clf.feature_importances_), key=lambda kv: -kv[1])
    log(f"\n  -- {reg} top 10 --")
    for fn, i in imp[:10]:
        log(f"    {fn:32s} {i:.4f}")

OUT.parent.mkdir(exist_ok=True)
OUT.write_text("\n".join(report))
print(f"\nwritten -> {OUT}")
