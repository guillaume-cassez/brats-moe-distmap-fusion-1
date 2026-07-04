#!/usr/bin/env python3
"""Validate the 1-feature per-region decision rules in 5-fold CV to ensure the
+0.00119 gain is not overfitting. For each fold, the rule (feature + threshold
+ model mapping) is selected on TRAIN only, then applied on TEST.
"""
import csv
import json
from pathlib import Path
from itertools import product

import numpy as np
from sklearn.model_selection import KFold

ROOT = Path(__file__).parent
DATA = ROOT.parent / "data"
FEATS_MORPHO = DATA / "patient_features.csv"
FEATS_AGREE = DATA / "patient_agreement_features.csv"
RANK = DATA / "rankings.json"

morpho = {r["patient_id"]: r for r in csv.DictReader(FEATS_MORPHO.open())}
agree = {r["patient_id"]: r for r in csv.DictReader(FEATS_AGREE.open())}
MORPHO_COLS = [k for k in next(iter(morpho.values())).keys() if k not in ("patient_id", "fold")]
AGREE_COLS = [k for k in next(iter(agree.values())).keys() if k != "patient_id"]
ALL_FEATS = MORPHO_COLS + AGREE_COLS

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
        "pid": pid,
        "B_WT": b["dice_WT"], "B_TC": b["dice_TC"], "B_ET": b["dice_ET"],
        "D_WT": d["dice_WT"], "D_TC": d["dice_TC"], "D_ET": d["dice_ET"],
        "F_WT": f["dice_WT"], "F_TC": f["dice_TC"], "F_ET": f["dice_ET"],
        "feats": feats,
    })

N = len(rows)
X = np.array([[r["feats"][fn] for fn in ALL_FEATS] for r in rows])
print(f"n = {N} patients, {len(ALL_FEATS)} features")

def find_best_rule(idx, reg, eval_mean):
    """Search best (feat, thr, m_hi, m_lo) maximizing mean dice_reg over idx."""
    best = (-1, None)
    for fi, feat in enumerate(ALL_FEATS):
        vals = X[idx, fi]
        if np.std(vals) < 1e-9: continue
        quantiles = np.quantile(vals, np.linspace(0.05, 0.95, 19))
        for thr in quantiles:
            for m_hi in "BDF":
                for m_lo in "BDF":
                    if m_hi == m_lo: continue
                    score = np.mean([rows[i][f"{m_hi if X[i, fi] > thr else m_lo}_{reg}"] for i in idx])
                    if score > best[0]:
                        best = (score, (feat, thr, m_hi, m_lo, fi))
    return best[1]

def apply_rule(rule, idx, reg):
    feat, thr, m_hi, m_lo, fi = rule
    return [rows[i][f"{m_hi if X[i, fi] > thr else m_lo}_{reg}"] for i in idx]

kf = KFold(n_splits=5, shuffle=True, random_state=42)

per_patient_dice_avg_cv = [None] * N
rules_chosen = {reg: [] for reg in ("WT", "TC", "ET")}
for fold_idx, (tr, te) in enumerate(kf.split(X)):
    chosen = {}
    for reg in ("WT", "TC", "ET"):
        rule = find_best_rule(tr, reg, "train")
        rules_chosen[reg].append(rule)
        chosen[reg] = rule

    te_test_scores = {}
    for reg in ("WT", "TC", "ET"):
        te_test_scores[reg] = apply_rule(chosen[reg], te, reg)
    # combine dice_avg
    for pos_in_te, idx in enumerate(te):
        dice_avg = (te_test_scores["WT"][pos_in_te] + te_test_scores["TC"][pos_in_te] + te_test_scores["ET"][pos_in_te]) / 3
        per_patient_dice_avg_cv[idx] = dice_avg

    print(f"fold {fold_idx} : WT={chosen['WT'][0]}>{chosen['WT'][1]:.3f} TC={chosen['TC'][0]}>{chosen['TC'][1]:.3f} ET={chosen['ET'][0]}>{chosen['ET'][1]:.3f}")

cv_mean = np.mean(per_patient_dice_avg_cv)

# Baselines
f_avg = np.mean([(r["F_WT"] + r["F_TC"] + r["F_ET"]) / 3 for r in rows])
oracle_class = np.mean([(max(r["B_WT"], r["D_WT"], r["F_WT"]) +
                         max(r["B_TC"], r["D_TC"], r["F_TC"]) +
                         max(r["B_ET"], r["D_ET"], r["F_ET"])) / 3 for r in rows])

print(f"\n=== 5-fold CV result (no overfit) ===")
print(f"  Fusion default          : {f_avg:.6f}")
print(f"  1-feature rule (CV)     : {cv_mean:.6f}")
print(f"  Δ vs fusion             : {cv_mean - f_avg:+.6f}")
print(f"  Oracle per-class        : {oracle_class:.6f}")
print(f"  Gap vs oracle           : {oracle_class - cv_mean:+.6f}")
print(f"  Recovery of oracle gap  : {100 * (cv_mean - f_avg) / (oracle_class - f_avg):.1f}%")

# Stability : how often the same feature picked across folds
from collections import Counter
print(f"\n=== Rule stability across 5 folds ===")
for reg in ("WT", "TC", "ET"):
    feats_picked = Counter(r[0] for r in rules_chosen[reg])
    pairs_picked = Counter((r[2], r[3]) for r in rules_chosen[reg])
    print(f"  {reg}  features: {dict(feats_picked)}  model-pairs: {dict(pairs_picked)}")
