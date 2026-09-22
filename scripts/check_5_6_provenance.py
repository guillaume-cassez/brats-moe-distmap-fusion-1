#!/usr/bin/env python3
"""Contrôle de provenance du §4.6 (ex-§5.6) — carte #205, critère C11.

Chaque nombre des tableaux A et B du §5.6 d'un manuscrit doit se retrouver dans
l'artefact de référence `outputs/multiseed/stats.json` (run courante du 15/06 11:23,
n=720), et AUCUNE signature de la run `_obsolete_20260615_105454` (n=719/684) ne doit
subsister. Fail-closed : le script sort en 1 dès qu'un écart est mesuré.

Usage : check_5_6_provenance.py <manuscrit.md> [stats.json]
"""
from __future__ import annotations

import json
import re
import sys
import unicodedata
from pathlib import Path

def _racine() -> Path:
    """Remonte jusqu'au dossier qui porte outputs/multiseed/ (indice fixe = piège)."""
    for ancetre in [Path(__file__).resolve(), *Path(__file__).resolve().parents]:
        if (ancetre / "outputs" / "multiseed" / "stats.json").exists():
            return ancetre
    return Path(__file__).resolve().parents[4]


RACINE = _racine()
STATS_DEFAUT = RACINE / "outputs" / "multiseed" / "stats.json"

SUP = "⁰¹²³⁴⁵⁶⁷⁸⁹"

LIGNES = [
    ("Legacy Dice", "WT", "legacy_dice_WT"),
    ("Legacy Dice", "TC", "legacy_dice_TC"),
    ("Legacy Dice", "ET", "legacy_dice_ET"),
    ("LW Dice", "WT", "lw_dice_WT"),
    ("LW Dice", "TC", "lw_dice_TC"),
    ("LW Dice", "ET", "lw_dice_ET"),
    ("Legacy HD95", "WT", "legacy_hd95_WT"),
    ("Legacy HD95", "TC", "legacy_hd95_TC"),
    ("Legacy HD95", "ET", "legacy_hd95_ET"),
    ("LW HD95", "WT", "lw_hd95_WT"),
    ("LW HD95", "TC", "lw_hd95_TC"),
    ("LW HD95", "ET", "lw_hd95_ET"),
]

# Signatures numériques de la run obsolète (_obsolete_20260615_105454).
SIGNATURES_OBSOLETES = [
    "0,7815", "0.7815", "0,8230", "0.8230", "0,8004", "0.8004",
    "65,9 ±", "65.9 ±", "49,1 ±", "49.1 ±", "58,0 ±", "58.0 ±",
    "+4,15 pp", "+4.15 pp", "−16,8 mm", "-16.8 mm", "−7,9 mm", "-7.9 mm",
    "719 paires", "719 valid pairs", "684 pour consensus", "684 for consensus",
    "0,7815 ±", "0.7815 ±",
]


def normaliser(txt: str) -> str:
    """Met les p-values et exposants dans une forme comparable, quel que soit le style."""
    txt = txt.replace("\u2212", "-").replace("\u00a0", " ")
    # 5,5 × 10⁻⁵  /  5,5×$10^{-5}$  ->  5.5e-05
    def sci(m: re.Match) -> str:
        mant = m.group(1).replace(",", ".")
        exp = m.group(2)
        for i, c in enumerate(SUP):
            exp = exp.replace(c, str(i))
        exp = exp.replace("\u207b", "-")
        return f"{mant}e{int(exp):+03d}"

    txt = re.sub(r"(\d+[.,]\d+)\s*[×x]\s*\$?10\^\{(-?\d+)\}\$?", sci, txt)
    txt = re.sub(r"(\d+[.,]\d+)\s*[×x]\s*10([⁻⁰¹²³⁴⁵⁶⁷⁸⁹]+)", sci, txt)
    txt = re.sub(r"10\^\{(-?\d+)\}", lambda m: "1e%+03d" % int(m.group(1)), txt)
    txt = re.sub(r"10([⁻⁰¹²³⁴⁵⁶⁷⁸⁹]+)", lambda m: "1e%+03d" % int(
        m.group(1).replace("\u207b", "-").translate(
            {ord(c): ord("0") + i for i, c in enumerate(SUP)})), txt)
    # $ ... $ résiduels
    txt = txt.replace("$", "")
    return txt


def lire_nombre(s: str):
    """Lit '0,8103 ± 0,0080 mm' ou '0.017' ou '5.5e-05' -> (valeur, décimales, incertitude)."""
    s = normaliser(s).strip().replace("**", "")
    s = re.sub(r"\s*(mm|pp)\s*$", "", s).strip()
    inc = None
    if "±" in s:
        s, si = [x.strip() for x in s.split("±", 1)]
        inc = float(si.replace(",", "."))
    m = re.fullmatch(r"[-+]?[\d.,]+(?:e[-+]?\d+)?", s.replace(" ", ""))
    if not m:
        return None
    txt = s.replace(" ", "").replace(",", ".")
    if "e" in txt:
        return (float(txt), None, inc)
    dec = len(txt.split(".")[1]) if "." in txt else 0
    return (float(txt), dec, inc)


def extraire_tables(md: str):
    """Rend {('A'|'B', métrique, région): ligne brute} pour les tableaux du §5.6."""
    # Harmonisation du 2026-09-19 : la section robustesse est §4.6 (plan papier 2) ;
    # l'ancien §5.6 reste accepté pour relire un manuscrit antérieur.
    i56 = -1
    for marque in ("## 4.6", "# 4.6", "4.6 ", "## 5.6", "# 5.6", "5.6 "):
        i56 = md.find(marque)
        if i56 >= 0:
            break
    cands = [c for c in (md.find("## 5.", i56), md.find("## 6.", i56)) if c > 0]
    fin = min(cands) if cands else -1
    corps = md[i56:fin if fin > 0 else len(md)]
    out = {}
    manche = None
    for ligne in corps.splitlines():
        l = ligne.strip()
        if re.search(r"Tableau A|Table A\b", l):
            manche = "A"
            continue
        if re.search(r"Tableau B|Table B\b", l):
            manche = "B"
            continue
        if manche and l.startswith("|"):
            cel = [c.strip() for c in l.strip("|").split("|")]
            if len(cel) < 7 or cel[0].startswith("---") or cel[0].lower().startswith(
                    ("métrique", "metric")):
                continue
            out[(manche, cel[0].replace("**", ""), cel[1].replace("**", ""))] = l
    return out


def comparer(cellule: str, attendu: float, tol_decimales=True) -> tuple[bool, str]:
    lu = lire_nombre(cellule)
    if lu is None:
        return False, f"illisible: {cellule!r}"
    val, dec, _ = lu
    if dec is None:  # notation scientifique
        if attendu == 0:
            return val == 0, f"{val} vs {attendu}"
        ordre = int(f"{abs(attendu):e}".split("e")[1])
        if not (ordre - 1 <= int(f"{abs(val):e}".split("e")[1]) <= ordre + 1):
            return False, f"ordre de grandeur {val:g} vs {attendu:g}"
        return abs(val - attendu) <= 0.06 * 10 ** ordre, f"{val:g} vs {attendu:.4g}"
    arr = round(attendu, dec)
    ok = abs(arr - val) < 10 ** (-dec) / 2 + 1e-12
    return ok, f"{val} vs arrondi({attendu:.6f},{dec})={arr}"


def verifier(manuscrit: Path, stats_path: Path) -> int:
    md = manuscrit.read_text(encoding="utf-8")
    stats = json.loads(stats_path.read_text(encoding="utf-8"))
    tables = extraire_tables(md)
    echecs, alertes, ok = [], [], 0

    if len(tables) < 24:
        echecs.append(f"seulement {len(tables)}/24 lignes de tableau lues dans le §5.6")

    for manche in ("A", "B"):
        for metrique, region, cle in LIGNES:
            # Le tableau B compare le CC-consensus à la baseline : clés « cons_* ».
            cle_eff = cle if manche == "A" else "cons_" + cle
            ligne = tables.get((manche, metrique, region))
            if ligne is None:
                echecs.append(f"tableau {manche} : ligne « {metrique} {region} » absente")
                continue
            if cle_eff not in stats:
                echecs.append(f"stats.json : clé {cle_eff} absente")
                continue
            e = stats[cle_eff]
            cel = [c.strip() for c in ligne.strip("|").split("|")]
            autre = "mean_distmap" if "mean_distmap" in e else "mean_consensus"
            std_autre = "std_distmap" if "std_distmap" in e else "std_consensus"
            testes = [
                ("Baseline", cel[2], e["mean_baseline"], e.get("std_baseline")),
                ("autre", cel[3], e[autre], e.get(std_autre)),
            ]
            for nom, cell, moy, sd in testes:
                bon, msg = comparer(cell, moy)
                if not bon:
                    echecs.append(f"{manche}/{metrique} {region} [{nom}] {msg}")
                else:
                    ok += 1
                lu = lire_nombre(cell)
                if lu and lu[2] is not None and sd is not None:
                    dec = len(f"{sd:.6f}".split(".")[1])
                    if abs(round(sd, 2) - lu[2]) > 0.005 + 1e-9:
                        alertes.append(
                            f"{manche}/{metrique} {region} [{nom}] σ {lu[2]} vs {sd:.4f}")
            # Δ (colonne 4) : pp pour les Dice, mm pour les HD95
            delta_att = e["delta_mean"] * (100 if "dice" in cle else 1)
            bon, msg = comparer(cel[4], delta_att)
            if not bon:
                echecs.append(f"{manche}/{metrique} {region} [Δ] {msg}")
            else:
                ok += 1
            for idx, clep in ((5, "p_ttest"), (6, "p_wilcoxon")):
                bon, msg = comparer(cel[idx], e[clep])
                if not bon:
                    echecs.append(f"{manche}/{metrique} {region} [{clep}] {msg}")
                else:
                    ok += 1

    for sig in SIGNATURES_OBSOLETES:
        if sig in md:
            n = md.count(sig)
            echecs.append(f"signature de la run obsolète présente : {sig!r} ×{n}")

    n_att = stats["lw_dice_WT"]["n_wilcoxon"]
    if "720" not in md and str(n_att) not in md:
        alertes.append(f"le n de la run courante ({n_att}) n'apparaît pas dans le manuscrit")

    print(f"── {manuscrit}")
    print(f"   statistiques comparées à : {stats_path.name} (md5 attendu fe5d513e…)")
    print(f"   {ok} valeurs conformes · {len(alertes)} alerte(s) · {len(echecs)} échec(s)")
    for a in alertes:
        print(f"   ALERTE  {a}")
    for e in echecs:
        print(f"   ÉCHEC   {e}")
    return 1 if echecs else 0


def main() -> int:
    argv = sys.argv[1:]
    stats = STATS_DEFAUT
    cibles: list[str] = []
    it = iter(range(len(argv)))
    for i in it:
        if argv[i] == "--stats":
            stats = Path(argv[next(it)])
        else:
            cibles.append(argv[i])
    if not cibles:
        print(__doc__)
        return 2
    rc = 0
    for c in cibles:
        rc |= verifier(Path(c), stats)
    print("VERDICT :", "PASS" if rc == 0 else "ÉCHEC")
    return rc


if __name__ == "__main__":
    sys.exit(main())
