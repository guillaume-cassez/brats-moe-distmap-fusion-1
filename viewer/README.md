# 3D interactive viewer

The companion 3D viewer is **hosted on Cloudflare Pages** and embedded directly on the paper landing page. It is not reproduced in this repository because the precomputed meshes (≈ 80 GB on disk) are larger than a Git repository should hold.

## Where to use it

- **Paper landing page** (recommended) : [guillaume-cassez.fr/brats/paper1/](https://guillaume-cassez.fr/brats/paper1/) — the viewer is embedded in an `<iframe>` next to the results tables.
- **Standalone viewer** : [guillaume-cassez.fr/brats/](https://guillaume-cassez.fr/brats/) — full-screen, all 1196 patients, all four segmentations (GT / Baseline / DistMap / Fusion).
- **Per-patient ranking table** : [guillaume-cassez.fr/brats/ranking/](https://guillaume-cassez.fr/brats/ranking/) — sort and filter the 1196 patients by Dice and HD95 of each model.

## The six thesis-demo patients

Six patients are pinned at the top of the Patient dropdown (optgroup "★ Démo thèse" / "★ Thesis demo"). Each one illustrates one of the six model-ordering cases C1–C6 discussed in the paper:

| Pin | Patient | Case description |
|---|---|---|
| ★ | `01437-000` | C2 — DistMap rescues Baseline |
| ★ | `00048-001` | C1 — DistMap hallucinates, Baseline dominates |
| ★ | `00540-000` | C6 — Fusion clean synergy |
| ★ | `01530-000` | C5 — Fusion deletes a legitimate CC |
| ★ | `01428-000` | C3 — Fusion baseline-side |
| ★ | `00017-001` | C4 — Fusion distmap-side |

## Viewer source

The viewer is built with Next.js 13 (App Router) + Three.js + @react-three/fiber. The source lives in the separate private viewer monorepo of the project and is exported to static HTML for Cloudflare Pages. An open-source release of the viewer is under consideration.
