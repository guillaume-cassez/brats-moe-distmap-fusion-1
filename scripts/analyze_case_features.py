#!/usr/bin/env python3
"""Join patient_features.csv + all_cases.json → which features discriminate the
6 model-ordering cases (C1-C6).

Analysis:
  1. For each feature, per-case median + IQR.
  2. Pairwise Mann-Whitney U between specific case-pairs of interest:
       C1 vs C2 (baseline > distmap   vs   distmap > baseline)
       C5 vs C6 (fusion worst         vs   fusion best)
       C5 vs C3 (fusion worst         vs   fusion between B<D)
       C5 vs C4 (fusion worst         vs   fusion between D<B)
  3. Random-forest importance (6-class classification) — global ranking.
  4. Compact report (top-K features) + CSV export.
"""
import csv
import json
import math
from pathlib import Path
from collections import defaultdict

import numpy as np
from scipy.stats import mannwhitneyu

FEATS_CSV = Path("/tmp/patient_features.csv")
CASES_JSON = Path(__file__).parent / "cases_out" / "all_cases.json"
OUT_DIR = Path(__file__).parent / "analysis_out"
OUT_DIR.mkdir(exist_ok=True)

# Load features
rows = list(csv.DictReader(FEATS_CSV.open()))
print(f"features: {len(rows)} patients")

# Load cases
cases_data = json.loads(CASES_JSON.read_text())
case_of = {}  # pid -> list of case names
for cname, plist in cases_data["cases"].items():
    for p in plist:
        case_of.setdefault(p["pid"], []).append(cname)

FEATURE_NAMES = [k for k in rows[0].keys() if k not in ("patient_id", "fold")]
print(f"features: {len(FEATURE_NAMES)}")

# Build feature arrays, per-case lists
per_case = defaultdict(list)   # case_name -> list of dicts {feat: val}
for r in rows:
    pid = r["patient_id"]
    feats = {k: float(r[k]) if r[k] not in ("", None) else 0.0 for k in FEATURE_NAMES}
    for cname in case_of.get(pid, []):
        per_case[cname].append(feats)

for cname, arr in per_case.items():
    print(f"  {cname:30s} n={len(arr)}")

# ---- 1. Per-case median (1 ligne par feature) ----
stats_rows = []
for feat in FEATURE_NAMES:
    row = {"feature": feat}
    for cname in sorted(per_case):
        vals = [x[feat] for x in per_case[cname]]
        if vals:
            row[f"{cname}_median"] = f"{np.median(vals):.3f}"
            row[f"{cname}_iqr"] = f"{np.subtract(*np.percentile(vals, [75, 25])):.3f}"
    stats_rows.append(row)

# ---- 2. Mann-Whitney U pour paires clés ----
PAIRS = [
    ("C1_baseline_beats_distmap", "C2_distmap_beats_baseline", "Baseline gagne vs DistMap gagne"),
    ("C5_fusion_worst", "C6_fusion_best", "Fusion casse vs Fusion synergie"),
    ("C5_fusion_worst", "C3_fusion_between_B_lt_D", "Fusion casse vs Fusion intermédiaire (B<D)"),
    ("C5_fusion_worst", "C4_fusion_between_D_lt_B", "Fusion casse vs Fusion intermédiaire (D<B)"),
    ("C6_fusion_best", "C3_fusion_between_B_lt_D", "Fusion gagne vs Fusion intermédiaire (B<D)"),
]

mw_table = []  # rows : pair_label, feature, median_a, median_b, p-value, direction
for ca, cb, label in PAIRS:
    a = per_case[ca]; b = per_case[cb]
    if not a or not b:
        continue
    for feat in FEATURE_NAMES:
        va = np.array([x[feat] for x in a])
        vb = np.array([x[feat] for x in b])
        # Skip degenerate features (same values)
        if np.std(va) < 1e-9 and np.std(vb) < 1e-9:
            continue
        try:
            u, p = mannwhitneyu(va, vb, alternative="two-sided")
        except Exception:
            continue
        mw_table.append({
            "pair": label, "ca": ca, "cb": cb, "feature": feat,
            "median_a": float(np.median(va)), "median_b": float(np.median(vb)),
            "mean_a": float(np.mean(va)), "mean_b": float(np.mean(vb)),
            "p_value": float(p),
            "direction": ">" if np.median(va) > np.median(vb) else ("<" if np.median(va) < np.median(vb) else "="),
        })

# Sort by p-value ascending per pair
mw_table.sort(key=lambda r: (r["pair"], r["p_value"]))

# Write full CSV
with (OUT_DIR / "mann_whitney.csv").open("w", newline="") as fout:
    w = csv.DictWriter(fout, fieldnames=["pair","ca","cb","feature","median_a","median_b","mean_a","mean_b","direction","p_value"])
    w.writeheader()
    for r in mw_table:
        w.writerow(r)

# ---- 3. Random-forest importance (multi-class) ----
try:
    from sklearn.ensemble import RandomForestClassifier
    SK = True
except Exception:
    SK = False
    print("[warn] sklearn not available, skipping RF importance")

rf_importance_BD = []
rf_importance_FUSION = []
if SK:
    from collections import Counter
    # Analysis A: binary B>D vs D>B (orthogonal to fusion)
    X, y = [], []
    for r in rows:
        pid = r["patient_id"]
        labels = set(case_of.get(pid, []))
        if "C1_baseline_beats_distmap" in labels:
            y.append("C1_B>D")
        elif "C2_distmap_beats_baseline" in labels:
            y.append("C2_D>B")
        else:
            continue
        X.append([float(r[f]) for f in FEATURE_NAMES])
    X = np.array(X); y = np.array(y)
    print(f"\n=== RF-A [B vs D ordering] n={len(X)} {dict(Counter(y))} ===")
    clf = RandomForestClassifier(n_estimators=500, min_samples_leaf=5,
                                  class_weight="balanced", random_state=0, n_jobs=-1)
    clf.fit(X, y)
    rf_importance_BD = sorted(zip(FEATURE_NAMES, clf.feature_importances_), key=lambda kv: kv[1], reverse=True)
    for f, imp in rf_importance_BD:
        print(f"  {f:30s} {imp:.4f}")
    with (OUT_DIR / "rf_importance_BvD.csv").open("w", newline="") as fout:
        w = csv.writer(fout); w.writerow(["feature", "importance"])
        for f, imp in rf_importance_BD: w.writerow([f, f"{imp:.6f}"])

    # Analysis B: 4-class fusion position (C3/C4/C5/C6)
    FUSION_CASES = {"C3_fusion_between_B_lt_D", "C4_fusion_between_D_lt_B",
                    "C5_fusion_worst", "C6_fusion_best"}
    X, y = [], []
    for r in rows:
        pid = r["patient_id"]
        labels = set(case_of.get(pid, [])) & FUSION_CASES
        if not labels:
            continue
        X.append([float(r[f]) for f in FEATURE_NAMES])
        y.append(sorted(labels)[0])  # unique: a patient is in exactly one of C3-C6
    X = np.array(X); y = np.array(y)
    print(f"\n=== RF-B [Fusion position 4-class] n={len(X)} {dict(Counter(y))} ===")
    clf = RandomForestClassifier(n_estimators=500, min_samples_leaf=5,
                                  class_weight="balanced", random_state=0, n_jobs=-1)
    clf.fit(X, y)
    rf_importance_FUSION = sorted(zip(FEATURE_NAMES, clf.feature_importances_), key=lambda kv: kv[1], reverse=True)
    for f, imp in rf_importance_FUSION:
        print(f"  {f:30s} {imp:.4f}")
    with (OUT_DIR / "rf_importance_fusion4.csv").open("w", newline="") as fout:
        w = csv.writer(fout); w.writerow(["feature", "importance"])
        for f, imp in rf_importance_FUSION: w.writerow([f, f"{imp:.6f}"])

# ---- 4. Report: top discriminants per pair ----
print("\n=== Top discriminants (Mann-Whitney p < 0.01) ===")
for ca, cb, label in PAIRS:
    subset = [r for r in mw_table if r["ca"] == ca and r["cb"] == cb and r["p_value"] < 0.01]
    subset.sort(key=lambda r: r["p_value"])
    print(f"\n### {label}  (n_{ca}={len(per_case[ca])}, n_{cb}={len(per_case[cb])})")
    for r in subset[:8]:
        print(f"  {r['feature']:30s}  med[{ca[:5]}]={r['median_a']:10.3f}  {r['direction']}  med[{cb[:5]}]={r['median_b']:10.3f}   p={r['p_value']:.2e}")

# per-case medians table → CSV
with (OUT_DIR / "per_case_stats.csv").open("w", newline="") as fout:
    keys = list(stats_rows[0].keys())
    w = csv.DictWriter(fout, fieldnames=keys)
    w.writeheader()
    for r in stats_rows:
        w.writerow(r)

print(f"\noutputs written -> {OUT_DIR}/")
