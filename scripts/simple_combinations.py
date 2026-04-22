#!/usr/bin/env python3
"""Exhaustive test of all 27 fixed per-region rules :
  for each region (WT, TC, ET), pick one of {B, D, F} → 3^3 = 27 combinations.
Also: one-feature decision rules (1-deep decision tree) per region to see if
a hard rule on a single feature can approach oracle.
"""
import csv
import json
from pathlib import Path
from itertools import product
from collections import Counter

import numpy as np

ROOT = Path(__file__).parent
FEATS_MORPHO = ROOT / "cases_out" / "patient_features.csv"
FEATS_AGREE = ROOT / "cases_out" / "patient_agreement_features.csv"
RANK = Path("/tmp/rankings.json")

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
print(f"n = {len(rows)} patients")

# ---- 1. All 27 fixed-rule combinations ----
results = []
for WT, TC, ET in product("BDF", repeat=3):
    vals = [(r[f"{WT}_WT"] + r[f"{TC}_TC"] + r[f"{ET}_ET"]) / 3 for r in rows]
    results.append((f"{WT}/{TC}/{ET}", float(np.mean(vals))))
results.sort(key=lambda x: -x[1])

print(f"\n=== All 27 fixed per-region rules (WT/TC/ET model assignment) ===")
for name, mean in results:
    flag = ""
    if name == "F/F/F": flag = " <- fusion default"
    if name == "B/B/B": flag = " <- baseline only"
    if name == "D/D/D": flag = " <- distmap only"
    print(f"  {name:10s} mean Dice = {mean:.6f}{flag}")

# Fusion default reference
f_avg = next(v for n, v in results if n == "F/F/F")
print(f"\nBest fixed rule vs fusion default : {results[0][1] - f_avg:+.6f}")

# ---- 2. Majority-vote per-voxel (cheap since we have all 3 segs on tower).
#        But that's a different animal — skip: would need re-loading NIfTIs.
#        Here focus on what's cheap : thresholded decision rules on features. ----

# Per-region : for each feature, find the best threshold that decides between
# the top-2 models for that region (usually B and D for WT/ET, and F for TC).
# Decision rule : if feat > thr -> use model_high, else use model_low
#                 else pick the "default fixed" model.

print(f"\n=== Per-region 1-feature rules (search best single-feature threshold) ===")
for reg in ("WT", "TC", "ET"):
    # Try every feature × threshold at deciles
    best_dice = -1
    best_rule = None
    for feat in ALL_FEATS:
        vals = np.array([r["feats"][feat] for r in rows])
        if np.std(vals) < 1e-9: continue
        quantiles = np.quantile(vals, np.linspace(0.05, 0.95, 19))
        for thr in quantiles:
            # try all 6 pairs of (model_above, model_below)
            for m_hi in "BDF":
                for m_lo in "BDF":
                    if m_hi == m_lo: continue
                    picks = [m_hi if v > thr else m_lo for v in vals]
                    region_vals = [r[f"{p}_{reg}"] for r, p in zip(rows, picks)]
                    # Plus keep other regions default = F
                    full = [(region_vals[i] + rows[i]["F_TC" if reg != "TC" else "F_WT"] + rows[i]["F_ET" if reg != "ET" else "F_WT"]) / 3
                            for i in range(len(rows))]
                    # That's wrong, let's just compute the mean of the region-only dice
                    mean_reg = np.mean(region_vals)
                    # Compare to best_reg_mean_F (fusion for that region)
                    if mean_reg > best_dice:
                        best_dice = mean_reg
                        best_rule = (feat, thr, m_hi, m_lo)
    f_reg_default = np.mean([r[f"F_{reg}"] for r in rows])
    o_reg = np.mean([max(r[f"B_{reg}"], r[f"D_{reg}"], r[f"F_{reg}"]) for r in rows])
    print(f"  {reg}: best 1-feature rule dice_reg = {best_dice:.6f} (feature={best_rule[0]}, thr={best_rule[1]:.3f}, >thr→{best_rule[2]} else {best_rule[3]})")
    print(f"     fusion default for {reg} = {f_reg_default:.6f}   oracle for {reg} = {o_reg:.6f}   rule gain = {best_dice - f_reg_default:+.6f}")

# ---- 3. Combined : apply the best 1-feature rule per region, use fusion elsewhere ----
# Recompute the best 1-feature rule more carefully with tracked picks, then
# compute patient-level Dice avg using the 3 per-region rules together.

best_rules = {}
for reg in ("WT", "TC", "ET"):
    best_dice = -1; best_rule = None; best_picks = None
    for feat in ALL_FEATS:
        vals = np.array([r["feats"][feat] for r in rows])
        if np.std(vals) < 1e-9: continue
        quantiles = np.quantile(vals, np.linspace(0.05, 0.95, 19))
        for thr in quantiles:
            for m_hi in "BDF":
                for m_lo in "BDF":
                    if m_hi == m_lo: continue
                    picks = [m_hi if v > thr else m_lo for v in vals]
                    region_vals = [r[f"{p}_{reg}"] for r, p in zip(rows, picks)]
                    mean_reg = np.mean(region_vals)
                    if mean_reg > best_dice:
                        best_dice = mean_reg; best_rule = (feat, thr, m_hi, m_lo); best_picks = picks
    best_rules[reg] = (best_rule, best_picks)

# Combined
combined = []
for i, r in enumerate(rows):
    s = 0
    for reg in ("WT", "TC", "ET"):
        p = best_rules[reg][1][i]
        s += r[f"{p}_{reg}"]
    combined.append(s / 3)
combined_mean = np.mean(combined)

print(f"\n=== Combined : apply best 1-feature rule per region ===")
print(f"  mean Dice avg = {combined_mean:.6f}")
print(f"  vs fusion default = {combined_mean - f_avg:+.6f}")
print(f"  vs oracle per-class = {combined_mean - np.mean([(max(r['B_WT'],r['D_WT'],r['F_WT']) + max(r['B_TC'],r['D_TC'],r['F_TC']) + max(r['B_ET'],r['D_ET'],r['F_ET']))/3 for r in rows]):+.6f}")
