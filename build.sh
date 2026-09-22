#!/usr/bin/env bash
# Build paper.pdf and paper_fr.pdf from the Markdown sources (self-contained recipe).
#
# Engine: pandoc -> XeLaTeX, US letter, 1.7 cm margins, table of contents — the recipe
# reverse-engineered from the published v9 PDF metadata and kept stable since.
#
# Two headers, identical to the recipe verified on the source repository
# (scripts/build_paper_pdf.py):
#   header.tex        unicode -> LaTeX glyph map + \needspace (the revised manuscripts
#                     carry 12 \needspace blocks and unicode superscript p-values)
#   header_tables.tex horizontal table compaction + anti-split guards, applied to BOTH
#                     languages: the EN v10 carries the same wide official-metric tables
# Both headers together are the recipe that PRODUCED the shipped PDFs, and it is guarded:
# v10/verif_recette_bundle.py recompiles from these sources and compares page counts +
# extracted-text sha256 against the shipped PDFs (measured 2026-09-22: identical for both
# languages; the EN deposited PDF is built with `--tables-naturelles --compact-tables`).
# Without them pandoc dies on \needspace or silently drops glyphs/table guards.
#
# Requires: pandoc, TeX Live with xelatex + texlive-latex-extra (needspace, etoolbox),
#           fonts-liberation (Liberation Serif).
set -euo pipefail
cd "$(dirname "$0")"
# Le template pandoc charge lmodern.sty ; le poste n'a plus le paquet Debian lm. Le repo
# source porte un shim dans papers/_assets/texmf — le bundle embarque le même, et
# build.sh l'expose via TEXMFHOME (l'éventuel TEXMFHOME de l'utilisateur garde sa place).
export TEXMFHOME="$PWD/texmf${TEXMFHOME:+:$TEXMFHOME}"
# --columns 100000 : largeur de colonnes NATURELLE pour toutes les tables pipe.
# Pandoc bascule une table en « poids relatifs » (minipages) dès qu'une ligne de
# la source dépasse --columns (72 par défaut) et, sur des séparateurs uniformes
# |---|---|, répartit alors la largeur À PARTS ÉGALES : le tableau « Region /
# class » (§5.3) se retrouvait avec 6 colonnes de 0.14 \columnwidth, son en-tête
# coupé sur 3 lignes et 2 sauts de lignes inutiles, alors qu'il tient au naturel
# en 355.5 pt sur les 475.2 pt de texte. Sans cette option, build.sh ne reproduit
# PAS le PDF déposé. Les 12 tableaux de ce dépôt ont été mesurés (scripts/
# table_layout.py, sonde XeLaTeX sur Liberation Serif) : tous tiennent à largeur
# naturelle, donc ce mode donne zéro saut de ligne et aucun débordement.
OPTS=(--pdf-engine=xelatex --toc --columns 100000
      -V geometry:left=0.95in,right=0.95in,top=1in,bottom=1in
      -V mainfont="Liberation Serif" -V monofont="Latin Modern Mono"
      --include-in-header=header.tex --include-in-header=header_tables.tex)
pandoc paper.md    -o paper.pdf    "${OPTS[@]}"
pandoc paper_fr.md -o paper_fr.pdf "${OPTS[@]}"
echo "built: paper.pdf  paper_fr.pdf"
