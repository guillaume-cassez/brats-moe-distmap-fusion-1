#!/usr/bin/env python3
"""Test meta-selector strategies against default fusion.

1. ORACLE    : per-patient max(B, D, F_default) — theoretical upper bound.
2. META-RF   : train a RF classifier on 20 features → predict argmax(B, D, F).
               5-fold CV by patient (fold column).
3. META-LR   : same idea with logistic regression (for sanity).

Output : which strategy beats default fusion, by how much, and where the gains
come from (C5/C6 transitions).
"""
import csv
import json
import math
from pathlib import Path
from collections import Counter, defaultdict

import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import StratifiedKFold

ROOT = Path(__file__).parent
DATA = ROOT.parent / "data"
FEATS = DATA / "patient_features.csv"
RANK = DATA / "rankings.json"
OUT = ROOT.parent / "analysis" / "meta_selector.txt"

# Load features
feat_rows = list(csv.DictReader(FEATS.open()))
FEAT_NAMES = [k for k in feat_rows[0].keys() if k not in ("patient_id", "fold")]
feats_by_pid = {r["patient_id"]: r for r in feat_rows}

# Load rankings
data = json.loads(RANK.read_text())
rows = []
for r in data["rows"]:
    pid = r["patient_id"]
    if pid not in feats_by_pid:
        continue
    b, d, f = r.get("baseline"), r.get("distmap"), r.get("fusion")
    if not (b and d and f):
        continue
    if None in (b.get("dice_avg"), d.get("dice_avg"), f.get("dice_avg")):
        continue
    rows.append({
        "pid": pid,
        "fold": r.get("fold", "0"),
        "B": b["dice_avg"], "D": d["dice_avg"], "F": f["dice_avg"],
        "feats": {fn: float(feats_by_pid[pid][fn] or 0) for fn in FEAT_NAMES},
    })
print(f"n = {len(rows)} patients with features + metrics")

report = []
def log(s=""): report.append(s); print(s)

# ---- 1. ORACLE ----
oracle_vals = [max(r["B"], r["D"], r["F"]) for r in rows]
def_fusion_vals = [r["F"] for r in rows]
baseline_vals = [r["B"] for r in rows]
distmap_vals = [r["D"] for r in rows]
log(f"\n=== Global means (Dice avg) ===")
log(f"  Baseline only   : {np.mean(baseline_vals):.6f}")
log(f"  DistMap only    : {np.mean(distmap_vals):.6f}")
log(f"  Fusion default  : {np.mean(def_fusion_vals):.6f}")
log(f"  ORACLE (best/3) : {np.mean(oracle_vals):.6f}  (+{np.mean(oracle_vals) - np.mean(def_fusion_vals):+.6f} vs fusion)")

# Oracle choice breakdown
argmax_counts = Counter()
for r in rows:
    vals = {"B": r["B"], "D": r["D"], "F": r["F"]}
    best = max(vals, key=vals.get)
    argmax_counts[best] += 1
log(f"\n  Oracle argmax counts: {dict(argmax_counts)}  ({100*argmax_counts['B']/len(rows):.1f}% B, {100*argmax_counts['D']/len(rows):.1f}% D, {100*argmax_counts['F']/len(rows):.1f}% F)")

# ---- 2. META-RF : train classifier to predict argmax(B, D, F) from features ----
X = np.array([[r["feats"][fn] for fn in FEAT_NAMES] for r in rows])
y = []
for r in rows:
    vals = [r["B"], r["D"], r["F"]]
    labels = ["B", "D", "F"]
    y.append(labels[int(np.argmax(vals))])
y = np.array(y)
folds = np.array([r["fold"] for r in rows])

# 5-fold stratified CV by fold column
skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
rf_vals = []
rf_choices = []
pred_labels = {}
for tr, te in skf.split(X, y):
    clf = RandomForestClassifier(n_estimators=400, min_samples_leaf=3,
                                  class_weight="balanced", random_state=0, n_jobs=-1)
    clf.fit(X[tr], y[tr])
    preds = clf.predict(X[te])
    for idx, p in zip(te, preds):
        r = rows[idx]
        val = {"B": r["B"], "D": r["D"], "F": r["F"]}[p]
        rf_vals.append(val)
        rf_choices.append(p)
        pred_labels[idx] = p

log(f"\n=== META-RF (5-fold CV, RandomForest) ===")
log(f"  mean Dice avg : {np.mean(rf_vals):.6f}")
log(f"  vs fusion def : {np.mean(rf_vals) - np.mean(def_fusion_vals):+.6f}")
log(f"  vs oracle gap : {np.mean(oracle_vals) - np.mean(rf_vals):+.6f}  (remaining headroom)")
log(f"  choice counts : {dict(Counter(rf_choices))}")

# Accuracy (did we pick the true argmax ?)
argmax_true = np.array(y)
argmax_pred = np.array([pred_labels[i] for i in range(len(rows))])
acc = np.mean(argmax_true == argmax_pred)
log(f"  argmax accuracy: {acc:.3f}")

# ---- 3. META-LR ----
lr_vals = []
for tr, te in skf.split(X, y):
    scaler = StandardScaler()
    X_tr = scaler.fit_transform(X[tr])
    X_te = scaler.transform(X[te])
    clf = LogisticRegression(max_iter=2000, class_weight="balanced", random_state=0)
    clf.fit(X_tr, y[tr])
    preds = clf.predict(X_te)
    for idx, p in zip(te, preds):
        r = rows[idx]
        val = {"B": r["B"], "D": r["D"], "F": r["F"]}[p]
        lr_vals.append(val)
log(f"\n=== META-LR (5-fold CV, LogisticRegression) ===")
log(f"  mean Dice avg : {np.mean(lr_vals):.6f}")
log(f"  vs fusion def : {np.mean(lr_vals) - np.mean(def_fusion_vals):+.6f}")

# ---- 4. Feature importances for meta-RF on full data ----
clf = RandomForestClassifier(n_estimators=400, min_samples_leaf=3,
                              class_weight="balanced", random_state=0, n_jobs=-1)
clf.fit(X, y)
imp = sorted(zip(FEAT_NAMES, clf.feature_importances_), key=lambda kv: -kv[1])
log(f"\n=== Meta-RF feature importances (trained on all data) ===")
for fn, i in imp:
    log(f"  {fn:30s} {i:.4f}")

OUT.parent.mkdir(exist_ok=True)
OUT.write_text("\n".join(report))
print(f"\nwritten -> {OUT}")
