#!/usr/bin/env python3
"""Single source of truth for Paper 1 & Paper 3 statistics on OFFICIAL BraTS-2023 metrics.

Honest reporting (no metric cherry-picking): every official metric, every region, every
method pair, with paired Wilcoxon + rank-biserial effect size + bootstrap CI on the median
paired difference + Holm-Bonferroni multiple-comparison correction. A pre-specified PRIMARY
endpoint family (the two official ranking metrics, region-averaged) is corrected separately
from the secondary/exploratory grid.

Input : outputs/cv_kervadec_paper2/lesionwise_per_patient.csv (eval_lesionwise_kervadec.py,
        5-fold held-out CV, n=1196, identical nnU-Net splits -> paired).
Output: outputs/cv_kervadec_paper2/paper_stats.json + printed report.

Directions: Dice/Sensitivity/Specificity higher=better; HD95/FP/FN lower=better.
delta = A - B for pair (A,B); effect signed so positive r/improvement = A better than B.
"""
import csv
import json
import os
from collections import defaultdict
from statistics import median, mean as amean

import numpy as np
from scipy.stats import wilcoxon

HERE = os.path.dirname(os.path.abspath(__file__))
CSV = os.path.join(HERE, "..", "outputs", "cv_kervadec_paper2", "lesionwise_per_patient.csv")
OUT = os.path.join(HERE, "..", "outputs", "cv_kervadec_paper2", "paper_stats.json")
REGIONS = ["WT", "TC", "ET"]
METHODS = ["kervadec", "baseline", "distmap", "consensus_DB", "consensus_DK"]
# (field, label, higher_is_better, tier)
METRICS = [
    ("lw_dice", "Lesion-wise Dice", True, "primary"),
    ("lw_hd95", "Lesion-wise HD95", False, "primary"),
    ("legacy_dice", "Legacy Dice", True, "secondary"),
    ("legacy_hd95", "Legacy HD95", False, "secondary"),
    ("sensitivity", "Lesion Sensitivity", True, "secondary"),
    ("specificity", "Lesion Specificity", True, "secondary"),
    ("num_fp", "False-positive lesions", False, "secondary"),
    ("num_fn", "False-negative lesions", False, "secondary"),
]
# (A, B, tag)   delta = A - B
PAIRS = [("distmap", "baseline", "P1: DistMap vs baseline"),
         ("kervadec", "baseline", "P3: Kervadec vs baseline"),
         ("kervadec", "distmap", "P3b: Kervadec vs DistMap"),
         ("consensus_DB", "baseline", "CC-DB vs baseline"),
         ("consensus_DK", "baseline", "CC-DK vs baseline"),
         ("consensus_DB", "distmap", "CC-DB vs DistMap (FP cleanup)"),
         ("consensus_DK", "distmap", "CC-DK vs DistMap (FP cleanup)"),
         ("consensus_DK", "kervadec", "CC-DK vs Kervadec"),
         ("consensus_DK", "consensus_DB", "CC-DK vs CC-DB (better veto?)")]
FIELD_NAMES = ("legacy_hd95", "lw_hd95", "legacy_dice", "lw_dice",
               "num_tp", "num_fp", "num_fn", "sensitivity", "specificity")
RNG = np.random.default_rng(42)  # seeded -> reproducible bootstrap


def load(path):
    m = {meth: {} for meth in METHODS}
    for r in csv.DictReader(open(path)):
        key = (r["fold"], r["patient_id"], r["region"])
        m[r["method"]][key] = {k: float(r[k]) for k in FIELD_NAMES if k in r}
    return m


def region_keys(d, region):
    return {k: v for k, v in d.items() if k[2] == region}


def avg_over_regions(d, field):
    byp = defaultdict(dict)
    for (fold, pid, reg), v in d.items():
        byp[(fold, pid)][reg] = v
    out = {}
    for (fold, pid), regs in byp.items():
        if len(regs) == 3:
            out[(fold, pid, "avg")] = {field: amean([regs[r][field] for r in REGIONS])}
    return out


def rank_biserial(diffs, higher_better):
    """Matched-pairs rank-biserial correlation; signed so + = A better than B. Vectorized."""
    arr = np.asarray(diffs, dtype=float)
    arr = arr[arr != 0]
    if arr.size == 0:
        return 0.0
    ranks = np.empty(arr.size)
    ranks[np.argsort(np.abs(arr))] = np.arange(1, arr.size + 1)
    r_plus = ranks[arr > 0].sum()
    r_minus = ranks[arr < 0].sum()
    r = (r_plus - r_minus) / (r_plus + r_minus)   # + = A has larger values
    return float(r if higher_better else -r)       # flip so + = A better when lower is better


def boot_ci(diffs, n=2000):
    """95% percentile bootstrap CI on the median paired difference."""
    arr = np.asarray(diffs)
    if len(arr) == 0:
        return (float("nan"), float("nan"))
    idx = RNG.integers(0, len(arr), size=(n, len(arr)))
    meds = np.median(arr[idx], axis=1)
    return (float(np.percentile(meds, 2.5)), float(np.percentile(meds, 97.5)))


def boot_ci_rb(diffs, higher_better, n=500):
    """95% percentile bootstrap CI on the rank-biserial effect size (informative where the
    median paired difference is ~0). The effect size, not the median, is what we interpret."""
    arr = np.asarray(diffs)
    if len(arr) == 0:
        return (float("nan"), float("nan"))
    idx = RNG.integers(0, len(arr), size=(n, len(arr)))
    rbs = [rank_biserial(arr[idx[i]], higher_better) for i in range(n)]
    return (float(np.percentile(rbs, 2.5)), float(np.percentile(rbs, 97.5)))


def bh_fdr(items):
    """Benjamini-Hochberg FDR. items: list of (key, p) -> {key: q}. Step-up, monotone."""
    valid = [(k, p) for k, p in items if p == p]
    sv = sorted(valid, key=lambda kp: kp[1])
    n = len(sv)
    q = {}
    prev = 1.0
    for i in range(n - 1, -1, -1):
        k, p = sv[i]
        prev = min(prev, p * n / (i + 1))
        q[k] = prev
    for k, p in items:
        q.setdefault(k, float("nan"))
    return q


def compare(A, B, field, higher_better):
    shared = sorted(set(A) & set(B))
    a = [A[k][field] for k in shared]
    b = [B[k][field] for k in shared]
    diffs = [x - y for x, y in zip(a, b)]
    if higher_better:
        n_win = sum(1 for d in diffs if d > 0)
        n_loss = sum(1 for d in diffs if d < 0)
        alt = "greater"
    else:
        n_win = sum(1 for d in diffs if d < 0)
        n_loss = sum(1 for d in diffs if d > 0)
        alt = "less"
    try:
        stat, p2 = wilcoxon(a, b, alternative="two-sided")
        _, p1 = wilcoxon(a, b, alternative=alt)
    except ValueError:
        stat, p2, p1 = float("nan"), 1.0, 1.0
    lo, hi = boot_ci(diffs)
    rb = rank_biserial(diffs, higher_better)
    rb_lo, rb_hi = boot_ci_rb(diffs, higher_better)
    return {"n": len(shared), "mean_A": amean(a), "mean_B": amean(b),
            "median_A": median(a), "median_B": median(b),
            "mean_delta": amean(diffs), "median_delta": median(diffs),
            "median_delta_ci95": [lo, hi], "n_win_A": n_win, "n_loss_A": n_loss,
            "n_tie": sum(1 for d in diffs if d == 0),
            "rank_biserial": rb, "rank_biserial_ci95": [rb_lo, rb_hi],
            "p_two_sided": p2, "p_one_sided_A_better": p1}


def holm(items):
    """items: list of (key, p). -> {key: p_holm}. Standard Holm-Bonferroni step-down."""
    valid = [(k, p) for k, p in items if p == p]  # drop NaN
    sv = sorted(valid, key=lambda kp: kp[1])
    n = len(sv)
    adj = {}
    running = 0.0
    for i, (k, p) in enumerate(sv):
        a = min(1.0, (n - i) * p)
        running = max(running, a)  # enforce monotonicity
        adj[k] = running
    for k, p in items:
        if k not in adj:
            adj[k] = float("nan")
    return adj


def main():
    m = load(CSV)
    res = {"n_patients": len(region_keys(m["kervadec"], "WT")), "metrics": {}}

    for field, label, hib, tier in METRICS:
        res["metrics"][field] = {"label": label, "higher_better": hib, "tier": tier, "regions": {}}
        for reg in REGIONS + ["avg"]:
            if reg == "avg":
                buckets = {meth: avg_over_regions(m[meth], field) for meth in METHODS}
            else:
                buckets = {meth: region_keys(m[meth], reg) for meth in METHODS}
            res["metrics"][field]["regions"][reg] = {}
            for A, B, tag in PAIRS:
                res["metrics"][field]["regions"][reg][f"{A}_vs_{B}"] = compare(
                    buckets[A], buckets[B], field, hib)

    # ---- Holm correction across the 3 regions within each (metric, pair) family ----
    for field, label, hib, tier in METRICS:
        for A, B, tag in PAIRS:
            items = [(reg, res["metrics"][field]["regions"][reg][f"{A}_vs_{B}"]["p_two_sided"])
                     for reg in REGIONS]
            adj = holm(items)
            for reg in REGIONS:
                res["metrics"][field]["regions"][reg][f"{A}_vs_{B}"]["p_holm_3region"] = adj[reg]

    # ---- Global BH-FDR across the WHOLE exploratory family (every metric x {WT,TC,ET} x pair;
    #      the 2 pre-specified primary endpoints are region-averaged and Holm-corrected separately) ----
    expl = []
    for field, label, hib, tier in METRICS:
        for reg in REGIONS:
            for A, B, tag in PAIRS:
                k = (field, reg, f"{A}_vs_{B}")
                expl.append((k, res["metrics"][field]["regions"][reg][f"{A}_vs_{B}"]["p_two_sided"]))
    q = bh_fdr(expl)
    survivors = []
    for (field, reg, pk), qv in q.items():
        res["metrics"][field]["regions"][reg][pk]["q_bh_global"] = qv
        if qv == qv and qv < 0.05:
            survivors.append((field, reg, pk, qv))
    res["exploratory_family_size"] = len(expl)
    res["exploratory_survivors_bh_fdr"] = len(survivors)

    # ---- PRE-SPECIFIED PRIMARY endpoint: avg of the 2 official ranking metrics, per pair ----
    primary = {}
    for A, B, tag in PAIRS:
        items = [(f, res["metrics"][f]["regions"]["avg"][f"{A}_vs_{B}"]["p_two_sided"])
                 for f, _, _, t in METRICS if t == "primary"]
        adj = holm(items)
        primary[f"{A}_vs_{B}"] = {
            f: {"raw_p": dict(items)[f], "holm_p": adj[f],
                "delta": res["metrics"][f]["regions"]["avg"][f"{A}_vs_{B}"]["mean_delta"],
                "rank_biserial": res["metrics"][f]["regions"]["avg"][f"{A}_vs_{B}"]["rank_biserial"]}
            for f, _, _, t in METRICS if t == "primary"}
    res["primary_endpoints"] = primary

    with open(OUT, "w") as fh:
        json.dump(res, fh, indent=2)

    # ---------- printed report ----------
    print(f"n = {res['n_patients']} patients (5-fold held-out CV)\n")
    print("=" * 78)
    print("PRE-SPECIFIED PRIMARY ENDPOINTS — official ranking metrics, region-averaged")
    print("  (Holm-corrected across the 2-metric primary family, per pair)")
    print("=" * 78)
    for A, B, tag in PAIRS:
        print(f"\n{tag}")
        for f, lab, hib, t in METRICS:
            if t != "primary":
                continue
            pe = primary[f"{A}_vs_{B}"][f]
            sig = "SIG" if pe["holm_p"] < 0.05 else " ns"
            print(f"  {lab:18s} Δ={pe['delta']:+8.3f}  r={pe['rank_biserial']:+.3f}  "
                  f"raw_p={pe['raw_p']:.2e}  Holm_p={pe['holm_p']:.2e}  [{sig}]")

    print("\n" + "=" * 78)
    print(f"GLOBAL BH-FDR — exploratory family of {res['exploratory_family_size']} tests "
          f"(every metric x WT/TC/ET x pair); {res['exploratory_survivors_bh_fdr']} survive q<0.05")
    print("=" * 78)
    for field, reg, pk, qv in sorted(survivors, key=lambda x: x[3])[:30]:
        print(f"  {field:14s} {reg:3s} {pk:30s} q={qv:.2e}")
    if len(survivors) > 30:
        print(f"  ... +{len(survivors) - 30} more (q_bh_global in paper_stats.json)")

    print("\n" + "=" * 78)
    print("FULL GRID — all official metrics x regions x pairs (Holm across 3 regions)")
    print("=" * 78)
    for field, label, hib, tier in METRICS:
        arrow = "↑" if hib else "↓"
        print(f"\n--- {label} ({arrow} better) [{tier}] ---")
        print(f"{'reg':4s} {'pair':10s} {'meanA':9s} {'meanB':9s} {'medΔ':8s} "
              f"{'CI95':18s} {'win/los':9s} {'r':6s} {'p_raw':9s} {'p_holm':9s}")
        for reg in REGIONS + ["avg"]:
            for A, B, tag in PAIRS:
                c = res["metrics"][field]["regions"][reg][f"{A}_vs_{B}"]
                ph = c.get("p_holm_3region", float("nan"))
                phs = f"{ph:.2e}" if ph == ph else "   --   "
                s = "*" if c["p_two_sided"] < 0.05 else " "
                ci = f"[{c['median_delta_ci95'][0]:+.2f},{c['median_delta_ci95'][1]:+.2f}]"
                print(f"{reg:4s} {A[:4]+'-'+B[:4]:10s} {c['mean_A']:9.3f} {c['mean_B']:9.3f} "
                      f"{c['median_delta']:+8.3f} {ci:18s} {c['n_win_A']:4d}/{c['n_loss_A']:<4d} "
                      f"{c['rank_biserial']:+.3f} {c['p_two_sided']:.2e}{s}{phs:>9s}")
    print(f"\n-> {OUT}")


if __name__ == "__main__":
    main()
