#!/bin/bash
# Build the article as a PDF, with a real contents page and no table running off
# the page. Run it from anywhere inside the project.
#
# Three things here are not optional, and each fixes a fault that was in the
# first build:
#   --from=markdown          computes the column widths of the eighteen tables
#                            from the source, so that they wrap. The gfm reader
#                            lays them out at their natural width and nine of
#                            them then run up to seventy-five centimetres wide.
#   +autolink_bare_uris      turns the web addresses in the reference list into
#                            links, which LaTeX may break across lines. As plain
#                            text they are single unbreakable words and four of
#                            them run into the margin.
#   the PNG of the figure     LaTeX cannot read the SVG without rsvg-convert.
#
# The header file it writes sets the tables one size down and lets LaTeX stretch
# a line a little further than usual before it gives up.
set -euo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
root="$here"
while [ ! -e "$root/.project-root" ] && [ "$root" != "/" ]; do root="$(dirname "$root")"; done
if [ ! -e "$root/.project-root" ]; then echo "Could not find the project root." >&2; exit 1; fi

draft="${1:-$root/drafts/article-draft-v25.md}"
out="${2:-$root/drafts/Eliciting and Validating AI Self-Reports - final draft 2026-09-12.pdf}"
work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT

sed 's|figure-1-protocol-loop-v20\.svg|figure-1-protocol-loop-v20.png|' "$draft" > "$work/article.md"
cp "$root/drafts/figure-1-protocol-loop-v20.png" "$work/"

cat > "$work/header.tex" <<'TEX'
\usepackage{etoolbox}
\AtBeginEnvironment{longtable}{\small}
\setlength{\tabcolsep}{4pt}
\setlength{\emergencystretch}{3em}
\usepackage{xurl}
TEX

cd "$work"
pandoc article.md --from=markdown+autolink_bare_uris --to=pdf \
  --pdf-engine=xelatex --toc --toc-depth=3 --resource-path=. \
  -V geometry:margin=1in -V fontsize=11pt \
  -V colorlinks=true -V linkcolor=blue -V urlcolor=blue \
  -H header.tex -o article.pdf

cp article.pdf "$out"
echo "Wrote: $out"
