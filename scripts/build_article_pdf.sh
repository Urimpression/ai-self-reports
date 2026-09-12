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

# The contents run onto a second page, and without a break the title block would
# start halfway down it. This puts the article itself on a fresh page.
printf '\\clearpage\n\n' > "$work/article.md"
# Two changes to the figure's line. The PNG replaces the SVG, which LaTeX cannot
# read. And the text in square brackets is emptied, because LaTeX prints it as a
# caption of its own under the picture and the article already writes the caption
# in the paragraph below, so the PDF was showing it twice. Word does not print it,
# which is why this was invisible until the first PDF was built.
# The vocabulary table is five lines long and was being split across two pages,
# with its header repeated, away from the heading that introduces it.
sed -e 's|^!\[[^]]*\](figure-1-protocol-loop-v20\.svg)|![](figure-1-protocol-loop-v20.png)|' \
    -e 's|^### The vocabulary item$|\\needspace{14\\baselineskip}\n\n### The vocabulary item|' \
    "$draft" >> "$work/article.md"
cp "$root/drafts/figure-1-protocol-loop-v20.png" "$work/"

cat > "$work/header.tex" <<'TEX'
\usepackage{etoolbox}
\AtBeginEnvironment{longtable}{\small}
\setlength{\tabcolsep}{4pt}
\setlength{\emergencystretch}{3em}
\usepackage{xurl}
% The contents ran four lines onto a second page, which left that page almost
% empty. Setting it one size down and taking the paragraph spacing out of it
% brings it onto a single page without dropping any heading from it.
\pretocmd{\tableofcontents}{\begingroup\small\setlength{\parskip}{0pt}}{}{}
\apptocmd{\tableofcontents}{\endgroup}{}{}
% Lets a heading demand a minimum amount of room below it, so that a short table
% is not torn across a page break away from the heading that introduces it.
\usepackage{needspace}
% Record the title and the author in the PDF's own properties, which is what a
% preprint server and a reference manager read. This prints nothing on the page.
% It runs at the start of the document rather than in the preamble, so that it
% works whichever order pandoc's template loads hyperref in.
\AtBeginDocument{\hypersetup{%
  pdftitle={Eliciting and Validating AI Self-Reports: A Phenomenologically Grounded Protocol},%
  pdfauthor={Nicola Spano},%
  pdfsubject={A protocol for eliciting self-reports from language models and judging them, with a pilot of ten runs and 896 sessions}}}
TEX

cd "$work"
pandoc article.md --from=markdown+autolink_bare_uris --to=pdf \
  --pdf-engine=xelatex --toc --toc-depth=3 --resource-path=. \
  -V geometry:margin=1in -V fontsize=11pt \
  -V colorlinks=true -V linkcolor=blue -V urlcolor=blue \
  -H header.tex -o article.pdf

cp article.pdf "$out"
echo "Wrote: $out"
