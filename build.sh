#!/usr/bin/env bash
# Build paper.pdf and paper_fr.pdf from the Markdown sources.
#
# Engine reverse-engineered from the original PDF metadata (Creator "LaTeX via pandoc",
# Producer "xdvipdfmx", letter, 20 pages): pandoc -> XeLaTeX, US letter, 1.7 cm margins,
# table of contents. Verified to reproduce the original 20-page layout from the unedited source.
#
# Main font = Liberation Serif (matches the original embedded fonts: LiberationSerif + LMMono +
# LatinModernMath). header.tex maps inline unicode super/subscripts and set symbols (10⁻¹⁴, ∈, …)
# to LaTeX so rendering does not depend on the font carrying every glyph (Liberation Serif lacks
# U+207B superscript-minus). Without header.tex, negative exponents silently lose their minus.
#
# Requires: pandoc, a TeX Live with xelatex + recommended packages (texlive-xetex
#   texlive-fonts-recommended texlive-latex-recommended texlive-latex-extra), and the
#   fonts-liberation package (Liberation Serif).
set -euo pipefail
cd "$(dirname "$0")"
OPTS=(--pdf-engine=xelatex --toc -V papersize=letter -V geometry:margin=1.7cm
      -V mainfont="Liberation Serif" -H header.tex)
pandoc paper.md    -o paper.pdf    "${OPTS[@]}"
pandoc paper_fr.md -o paper_fr.pdf "${OPTS[@]}"
echo "built: paper.pdf  paper_fr.pdf"
