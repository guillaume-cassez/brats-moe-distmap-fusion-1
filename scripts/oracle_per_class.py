#!/usr/bin/env python3
"""Per-class oracle + baseline/distmap/fusion per-class means.

Decomposes the selection problem : instead of picking one model for the whole
patient, pick the best model INDEPENDENTLY for each region (WT/TC/ET).

Dice convention : on this dataset, empty-GT region → dice=1.0 (perfect absence
prediction). Note : for regions with empty GT, all 3 models trivially score 1.0
if they predict nothing, so oracle gain in those regions is 0.
"""
import json
from pathlib import Path
import numpy as np
from collections import Counter

ROOT = Path(__file__).parent
RANK = ROOT.parent / "data" / "rankings.json"
REGIONS = ["WT", "TC", "ET"]
MODELS = ["baseline", "distmap", "fusion"]

data = json.loads(RANK.read_text())
rows = []
for r in data["rows"]:
    b, d, f = r.get("baseline"), r.get("distmap"), r.get("fusion")
    if not (b and d and f): continue
    vals = {}
    ok = True
    for m, mm in [("B", b), ("D", d), ("F", f)]:
        for reg in REGIONS:
            v = mm.get(f"dice_{reg}")
            if v is None: ok = False
            vals[f"{m}_{reg}"] = v
    if not ok: continue
    rows.append({"pid": r["patient_id"], **vals})

print(f"n = {len(rows)} patients")

# ---- Per-class means per model ----
print(f"\n=== Mean per region per model ===")
print(f"{'region':>6} {'baseline':>10} {'distmap':>10} {'fusion':>10} {'oracle/reg':>10}")
for reg in REGIONS:
    b = np.mean([r[f"B_{reg}"] for r in rows])
    d = np.mean([r[f"D_{reg}"] for r in rows])
    f = np.mean([r[f"F_{reg}"] for r in rows])
    o = np.mean([max(r[f"B_{reg}"], r[f"D_{reg}"], r[f"F_{reg}"]) for r in rows])
    print(f"{reg:>6} {b:>10.6f} {d:>10.6f} {f:>10.6f} {o:>10.6f}")

# ---- Oracle global (patient-level) = pick one model for whole patient ----
oracle_patient = np.mean([
    max((r["B_WT"]+r["B_TC"]+r["B_ET"])/3,
        (r["D_WT"]+r["D_TC"]+r["D_ET"])/3,
        (r["F_WT"]+r["F_TC"]+r["F_ET"])/3)
    for r in rows
])

# ---- Oracle per-class (region-level) = pick best model per region ----
oracle_perclass = np.mean([
    (max(r["B_WT"], r["D_WT"], r["F_WT"]) +
     max(r["B_TC"], r["D_TC"], r["F_TC"]) +
     max(r["B_ET"], r["D_ET"], r["F_ET"])) / 3
    for r in rows
])

# ---- Reference means (Dice avg) ----
b_mean = np.mean([(r["B_WT"]+r["B_TC"]+r["B_ET"])/3 for r in rows])
d_mean = np.mean([(r["D_WT"]+r["D_TC"]+r["D_ET"])/3 for r in rows])
f_mean = np.mean([(r["F_WT"]+r["F_TC"]+r["F_ET"])/3 for r in rows])

print(f"\n=== Global Dice avg (mean of (WT+TC+ET)/3 per patient) ===")
print(f"  Baseline only              : {b_mean:.6f}")
print(f"  DistMap only               : {d_mean:.6f}")
print(f"  Fusion default             : {f_mean:.6f}")
print(f"  ORACLE patient-level       : {oracle_patient:.6f}  (+{oracle_patient - f_mean:+.6f} vs fusion)")
print(f"  ORACLE per-class (3 reg)   : {oracle_perclass:.6f}  (+{oracle_perclass - f_mean:+.6f} vs fusion)")

# ---- Per-class argmax breakdown (who wins each region?) ----
print(f"\n=== Per-class winning model ===")
for reg in REGIONS:
    wins = Counter()
    ties = 0
    for r in rows:
        vals = {"B": r[f"B_{reg}"], "D": r[f"D_{reg}"], "F": r[f"F_{reg}"]}
        mx = max(vals.values())
        winners = [k for k, v in vals.items() if v == mx]
        if len(winners) == 1:
            wins[winners[0]] += 1
        else:
            ties += 1
    tot = sum(wins.values()) + ties
    print(f"  {reg:>3}  B={wins['B']:>4} ({100*wins['B']/tot:.1f}%)  D={wins['D']:>4} ({100*wins['D']/tot:.1f}%)  F={wins['F']:>4} ({100*wins['F']/tot:.1f}%)  ties={ties}")

# ---- Cross-class oracle choice consistency ----
print(f"\n=== Oracle choice consistency across regions (does the best model change across WT/TC/ET ?) ===")
same = 0; mixed = 0
for r in rows:
    picks = []
    for reg in REGIONS:
        vals = {"B": r[f"B_{reg}"], "D": r[f"D_{reg}"], "F": r[f"F_{reg}"]}
        picks.append(max(vals, key=vals.get))
    if len(set(picks)) == 1: same += 1
    else: mixed += 1
print(f"  Same model for all 3 regions : {same} ({100*same/len(rows):.1f}%)")
print(f"  Mixed choice                 : {mixed} ({100*mixed/len(rows):.1f}%)")
