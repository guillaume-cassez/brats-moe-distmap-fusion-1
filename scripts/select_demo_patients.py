#!/usr/bin/env python3
"""Classify all 1196 patients into the 6 ordering cases (C1-C6) defined by the
user and dump one CSV + one JSON per case + one global JSON with champions.

Cases (B=baseline, D=distmap, F=fusion, metric = dice_avg over WT/TC/ET):
  C1 : B > D              (baseline beats distmap, any F)
  C2 : D > B              (distmap beats baseline, any F)
  C3 : B < F < D          (fusion intermediate, closer-to-baseline side)
  C4 : D < F < B          (fusion intermediate, closer-to-distmap side)
  C5 : F < B AND F < D    (fusion is worst)
  C6 : F > B AND F > D    (fusion is best)

Output :
  - data/C<n>_<name>.csv  : all patients of each case, ranked
  - data/all_cases.json   : machine-readable
"""
import json
import csv
from pathlib import Path

ROOT = Path(__file__).parent
DATA = ROOT.parent / "data"
RANK = DATA / "rankings.json"
OUT_DIR = DATA
OUT_DIR.mkdir(exist_ok=True)

data = json.loads(RANK.read_text())
rows = data["rows"]

def clean(r):
    b, d, f = r.get("baseline"), r.get("distmap"), r.get("fusion")
    if not (b and d and f):
        return None
    ba, da, fa = b.get("dice_avg"), d.get("dice_avg"), f.get("dice_avg")
    if ba is None or da is None or fa is None:
        return None
    return {
        "pid": r["patient_id"], "fold": r.get("fold"),
        "b": ba, "d": da, "f": fa,
        "b_WT": b.get("dice_WT"), "b_TC": b.get("dice_TC"), "b_ET": b.get("dice_ET"),
        "d_WT": d.get("dice_WT"), "d_TC": d.get("dice_TC"), "d_ET": d.get("dice_ET"),
        "f_WT": f.get("dice_WT"), "f_TC": f.get("dice_TC"), "f_ET": f.get("dice_ET"),
    }

pool = [x for x in (clean(r) for r in rows) if x]
print(f"pool size = {len(pool)}")

CASES = [
    ("C1_baseline_beats_distmap",  lambda x: x["b"] > x["d"],                         lambda x: x["b"] - x["d"]),
    ("C2_distmap_beats_baseline",  lambda x: x["d"] > x["b"],                         lambda x: x["d"] - x["b"]),
    ("C3_fusion_between_B_lt_D",   lambda x: x["b"] < x["f"] < x["d"],                lambda x: min(x["f"] - x["b"], x["d"] - x["f"])),
    ("C4_fusion_between_D_lt_B",   lambda x: x["d"] < x["f"] < x["b"],                lambda x: min(x["f"] - x["d"], x["b"] - x["f"])),
    ("C5_fusion_worst",            lambda x: x["f"] < x["b"] and x["f"] < x["d"],    lambda x: min(x["b"] - x["f"], x["d"] - x["f"])),
    ("C6_fusion_best",             lambda x: x["f"] > x["b"] and x["f"] > x["d"],    lambda x: min(x["f"] - x["b"], x["f"] - x["d"])),
]

all_cases = {}
champions = {}

print("\n=== prevalence + champions ===")
for name, pred, score in CASES:
    hits = sorted((x for x in pool if pred(x)), key=score, reverse=True)
    all_cases[name] = hits
    if hits:
        champ = hits[0]
        champions[name] = champ
        print(f"{name:30s} n={len(hits):4d} ({100*len(hits)/len(pool):.1f}%)  champion={champ['pid']} B={champ['b']:.4f} D={champ['d']:.4f} F={champ['f']:.4f}")

# champions distincts (greedy dedup across cases, order matters)
picked = {}
used = set()
for name, _, _ in CASES:
    for c in all_cases[name]:
        if c["pid"] not in used:
            picked[name] = c; used.add(c["pid"]); break

CHAMP = DATA / "champions.json"
CHAMP.write_text(json.dumps({
    "generated_at": data.get("generated_at"),
    "source": "rankings.json",
    "patients": [
        {"patient_id": picked[n]["pid"], "fold": picked[n]["fold"], "tag": n,
         "metrics": {"baseline": picked[n]["b"], "distmap": picked[n]["d"], "fusion": picked[n]["f"]}}
        for n, _, _ in CASES if n in picked
    ],
}, indent=2))
print(f"\nchampions written -> {CHAMP}")

for name, _, _ in CASES:
    hits = all_cases[name]
    csv_path = OUT_DIR / f"{name}.csv"
    with csv_path.open("w", newline="") as f_:
        w = csv.writer(f_)
        w.writerow(["rank","patient_id","fold","B_dice_avg","D_dice_avg","F_dice_avg",
                    "B_WT","B_TC","B_ET","D_WT","D_TC","D_ET","F_WT","F_TC","F_ET"])
        for i, x in enumerate(hits, 1):
            w.writerow([i, x["pid"], x["fold"],
                        f"{x['b']:.4f}", f"{x['d']:.4f}", f"{x['f']:.4f}",
                        x.get("b_WT"), x.get("b_TC"), x.get("b_ET"),
                        x.get("d_WT"), x.get("d_TC"), x.get("d_ET"),
                        x.get("f_WT"), x.get("f_TC"), x.get("f_ET")])
    print(f"  {csv_path.relative_to(ROOT.parent)}  rows={len(hits)}")

# machine-readable compact dump (pid + metrics + fold only)
(OUT_DIR / "all_cases.json").write_text(json.dumps({
    "generated_at": data.get("generated_at"),
    "n_pool": len(pool),
    "cases": {name: [{"pid": x["pid"], "fold": x["fold"], "b": x["b"], "d": x["d"], "f": x["f"]}
                     for x in all_cases[name]]
              for name in [c[0] for c in CASES]},
}, indent=2))
print(f"\nfull json -> {OUT_DIR/'all_cases.json'}")
