#!/usr/bin/env python3
"""Analyze sweep.csv (adaptive fusion thresholds) :
  1. Global mean Dice avg per threshold
  2. Per-case reclassification : for each original C3/C4/C5/C6 patient, does
     the adaptive fusion move them to a better case ?
  3. Top 10 patients most improved by adaptive rule
"""
import csv
from pathlib import Path
import numpy as np
from collections import Counter

SWEEP = Path("/tmp/sweep.csv")
OUT = Path(__file__).parent / "analysis_out" / "adaptive_fusion_summary.txt"
OUT.parent.mkdir(exist_ok=True)

rows = list(csv.DictReader(SWEEP.open()))
THRS = [20, 50, 100, 200, 500, 10**9]

report = []
def log(s=""): report.append(s); print(s)

log(f"n_patients = {len(rows)}")

# 1. Global mean per threshold
log("\n=== Mean Dice avg over all patients ===")
for thr in THRS:
    col = f"f{thr}_avg"
    vals = [float(r[col]) for r in rows if r[col]]
    log(f"  thr={thr:>12}  mean={np.mean(vals):.6f}  median={np.median(vals):.6f}  n={len(vals)}")

# Reference : baseline & distmap global mean (sanity)
b_mean = float(np.mean([float(r["b_avg"]) for r in rows]))
d_mean = float(np.mean([float(r["d_avg"]) for r in rows]))
log(f"\n  baseline mean = {b_mean:.6f}")
log(f"  distmap  mean = {d_mean:.6f}")
default_mean = np.mean([float(r["f1000000000_avg"]) for r in rows])

# 2. Case classification per threshold (uses current thr as F, B and D unchanged)
def classify(b, d, f):
    if b < f < d: return "C3"
    if d < f < b: return "C4"
    if f < b and f < d: return "C5"
    if f > b and f > d: return "C6"
    return "tie"

def orig_case(b, d, f):
    return classify(b, d, f)

log("\n=== Case distribution per threshold ===")
log(f"{'thr':>12}  {'C3':>5} {'C4':>5} {'C5':>5} {'C6':>5} {'tie':>5}")
for thr in THRS:
    cases = [classify(float(r["b_avg"]), float(r["d_avg"]), float(r[f"f{thr}_avg"])) for r in rows]
    c = Counter(cases)
    log(f"  thr={thr:>8}  {c.get('C3',0):>5} {c.get('C4',0):>5} {c.get('C5',0):>5} {c.get('C6',0):>5} {c.get('tie',0):>5}")

# 3. Transition matrix C5(default rule) → case(at thr=200)
log("\n=== Transitions from default C5 (thr=inf) to adaptive cases ===")
for target_thr in [20, 50, 100, 200, 500]:
    tm = Counter()
    n_C5_default = 0
    for r in rows:
        b = float(r["b_avg"]); d = float(r["d_avg"])
        f_default = float(r["f1000000000_avg"])
        if classify(b, d, f_default) != "C5":
            continue
        n_C5_default += 1
        f_new = float(r[f"f{target_thr}_avg"])
        tm[classify(b, d, f_new)] += 1
    log(f"  thr={target_thr:>5}  (n_C5_default={n_C5_default})")
    for k, n in sorted(tm.items(), key=lambda kv: -kv[1]):
        pct = 100 * n / n_C5_default if n_C5_default else 0
        log(f"     -> {k:<4} {n:>4} ({pct:.1f}%)")

# 4. Transitions from C6(default) — to confirm we don't break winners
log("\n=== Transitions from default C6 (thr=inf) ===")
for target_thr in [20, 50, 100, 200, 500]:
    tm = Counter()
    n_C6 = 0
    for r in rows:
        b = float(r["b_avg"]); d = float(r["d_avg"])
        f_default = float(r["f1000000000_avg"])
        if classify(b, d, f_default) != "C6":
            continue
        n_C6 += 1
        f_new = float(r[f"f{target_thr}_avg"])
        tm[classify(b, d, f_new)] += 1
    log(f"  thr={target_thr:>5}  (n_C6_default={n_C6})")
    for k, n in sorted(tm.items(), key=lambda kv: -kv[1]):
        pct = 100 * n / n_C6 if n_C6 else 0
        log(f"     -> {k:<4} {n:>4} ({pct:.1f}%)")

# 5. Top 10 most improved by thr=200 vs default
log("\n=== Top 10 most improved by thr=200 vs default fusion ===")
delta_rows = []
for r in rows:
    d200 = float(r["f200_avg"]); dinf = float(r["f1000000000_avg"])
    delta_rows.append((r["pid"], r["fold"], float(r["b_avg"]), float(r["d_avg"]), dinf, d200, d200 - dinf))
delta_rows.sort(key=lambda x: -x[6])
log(f"  {'pid':<22} {'fold':>4} {'B':>7} {'D':>7} {'F_inf':>7} {'F_200':>7} {'Δ':>8}")
for x in delta_rows[:10]:
    log(f"  {x[0]:<22} {x[1]:>4} {x[2]:>7.4f} {x[3]:>7.4f} {x[4]:>7.4f} {x[5]:>7.4f} {x[6]:>+8.4f}")

log("\n=== Top 10 most damaged by thr=200 (if any) ===")
delta_rows.sort(key=lambda x: x[6])
for x in delta_rows[:10]:
    if x[6] < 0:
        log(f"  {x[0]:<22} {x[1]:>4} {x[2]:>7.4f} {x[3]:>7.4f} {x[4]:>7.4f} {x[5]:>7.4f} {x[6]:>+8.4f}")

OUT.write_text("\n".join(report))
print(f"\nwritten -> {OUT}")
