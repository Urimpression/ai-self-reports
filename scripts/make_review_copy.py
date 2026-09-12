"""Make the Word review copy of a draft for Nicola to read and comment on in
Google Docs on his phone, with every sentence he has not read before
highlighted in yellow.

Run it from the project folder:

    python3 scripts/make_review_copy.py drafts/<new draft>.md drafts/<draft he read last>.md \
        "drafts/<date> review copy - article draft <n>.docx" \
        --figure-png figure-1-protocol-loop-v19.png --cover <file with the cover note>

The copy is written where the third argument says. Move it into to-file/ after
checking it, because that is where Nicola looks for review copies.

The steps run in this order:
1. Convert the draft he read last to Word, and keep every sentence of it, so
   that those sentences count as read.
2. Make a review version of the new draft: the optional cover note and a list
   of links to the headings go before the abstract, and the figure points to a
   PNG, because Google Docs shows neither an SVG image nor Word's own contents
   field.
3. Convert that to Word with pandoc.
4. In every paragraph, split the visible text into sentences and highlight the
   ones that are not among the sentences kept in step 1. A sentence is
   highlighted whole even when one word in it changed.
5. Give the notes to Nicola a blue colour and a shaded background, and give
   every table visible borders and a shaded header row.

Made on 10 September 2026 for the nineteenth draft, where the same steps run
on the eighteenth draft against itself highlighted nothing.
"""
import argparse
import json
import re
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

from lxml import etree

from paths import require_project


def normalise(sentence):
    """Lower-case a sentence and keep only letters and digits, so that the
    comparison ignores quotation marks, dashes and bold or italic markers."""
    return re.sub(r"[^a-z0-9]", "", sentence.lower())


def was_seen(sentence):
    """Sentences of fewer than four letters and digits are never highlighted."""
    return len(normalise(sentence)) < 4

# The sentences of the draft he read last, filled in by main().
ALSO_SEEN = set()

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
W = "{%s}" % W_NS

# The order Word expects for the children of a run's properties (w:rPr), of a
# paragraph's properties (w:pPr), of a table's properties (w:tblPr) and of a
# cell's properties (w:tcPr). Word can refuse a file whose elements are out of
# this order, so every element added below is put in its proper place.
RPR_ORDER = ["rStyle", "rFonts", "b", "bCs", "i", "iCs", "caps", "smallCaps",
             "strike", "dstrike", "outline", "shadow", "emboss", "imprint",
             "noProof", "snapToGrid", "vanish", "webHidden", "color", "spacing",
             "w", "kern", "position", "sz", "szCs", "highlight", "u", "effect",
             "bdr", "shd", "fitText", "vertAlign", "rtl", "cs", "em", "lang",
             "eastAsianLayout", "specVanish", "oMath"]
PPR_ORDER = ["pStyle", "keepNext", "keepLines", "pageBreakBefore", "framePr",
             "widowControl", "numPr", "suppressLineNumbers", "pBdr", "shd",
             "tabs", "suppressAutoHyphens", "kinsoku", "wordWrap",
             "overflowPunct", "topLinePunct", "autoSpaceDE", "autoSpaceDN",
             "bidi", "adjustRightInd", "snapToGrid", "spacing", "ind",
             "contextualSpacing", "mirrorIndents", "suppressOverlap", "jc",
             "textDirection", "textAlignment", "textboxTightWrap",
             "outlineLvl", "divId", "cnfStyle", "rPr", "sectPr", "pPrChange"]
TBLPR_ORDER = ["tblStyle", "tblpPr", "tblOverlap", "bidiVisual",
               "tblStyleRowBandSize", "tblStyleColBandSize", "tblW", "jc",
               "tblCellSpacing", "tblInd", "tblBorders", "shd", "tblLayout",
               "tblCellMar", "tblLook", "tblCaption", "tblDescription"]
TCPR_ORDER = ["cnfStyle", "tcW", "gridSpan", "hMerge", "vMerge", "tcBorders",
              "shd", "noWrap", "tcMar", "textDirection", "tcFitText", "vAlign",
              "hideMark"]

NOTE_TEXT_COLOUR = "1F4E79"   # dark blue for the notes to Nicola
NOTE_BACKGROUND = "DEEAF6"    # light blue behind them
NOTE_BORDER = "2E75B6"        # a blue bar down their left edge
HEADER_BACKGROUND = "E7E6E6"  # light grey behind the first row of each table


def w_el(tag, **attrs):
    """Make a Word element, with its attributes in the Word namespace."""
    el = etree.Element(W + tag)
    for key, value in attrs.items():
        el.set(W + key, value)
    return el


def put_in_order(parent, child, order):
    """Insert child into parent at the place the schema order requires,
    replacing an existing element of the same kind."""
    name = etree.QName(child).localname
    existing = parent.find(W + name)
    if existing is not None:
        parent.replace(existing, child)
        return
    later = set(order[order.index(name) + 1:])
    for position, sibling in enumerate(parent):
        if etree.QName(sibling).localname in later:
            parent.insert(position, child)
            return
    parent.append(child)


def properties(element, tag, order_in_parent=None):
    """Return the properties element (such as w:rPr) of a run, paragraph, table
    or cell, creating it as the first child if it does not exist yet."""
    props = element.find(W + tag)
    if props is None:
        props = etree.Element(W + tag)
        element.insert(0, props)
    return props


# ---------------------------------------------------------------- step 1

def review_markdown(draft_text, figure_png, cover_text):
    """Return the markdown the Word copy is made from."""
    text = draft_text
    if figure_png:
        text = re.sub(r"\]\(([^)]*?)\.svg\)", "](" + figure_png + ")", text)
    if cover_text:
        # The cover note goes directly before the abstract.
        marker = "\n## Abstract\n"
        assert text.count(marker) == 1, "the draft should have one abstract heading"
        text = text.replace(marker, "\n" + cover_text.strip() + "\n" + marker)
    return text


# ---------------------------------------------------------------- step 2

def pandoc_to_docx(markdown_path, docx_path, resource_dir, toc=True):
    command = ["pandoc", str(markdown_path), "--from=gfm", "--to=docx",
               "--resource-path=" + str(resource_dir), "-o", str(docx_path)]
    if toc:
        command[4:4] = ["--toc", "--toc-depth=3"]
    subprocess.run(command, check=True)


def inline_text(inlines):
    """Plain text of a list of pandoc inline elements."""
    out = []
    for x in inlines:
        kind = x["t"]
        if kind == "Str":
            out.append(x["c"])
        elif kind in ("Space", "SoftBreak"):
            out.append(" ")
        elif kind in ("Emph", "Strong", "Strikeout", "Underline"):
            out.append(inline_text(x["c"]))
        elif kind == "Code":
            out.append(x["c"][1])
        elif kind in ("Link", "Span", "Quoted"):
            out.append(inline_text(x["c"][1]))
    return "".join(out)


def contents_list(markdown_text):
    """A list of links to the headings from the abstract onwards, as markdown.
    Word's own contents field stays empty in Google Docs, which cannot fill it
    in, so the copy for the phone carries this list instead."""
    result = subprocess.run(["pandoc", "--from=gfm", "--to=json"], input=markdown_text,
                            capture_output=True, text=True, check=True)
    blocks = json.loads(result.stdout)["blocks"]
    has_abstract = any(b["t"] == "Header" and b["c"][0] == 2 and b["c"][1][0] == "abstract" for b in blocks)
    lines = ["**Contents**", ""]
    started = False
    for block in blocks:
        if block["t"] != "Header":
            continue
        level, (identifier, _, _), inlines = block["c"]
        if level == 2 and (identifier == "abstract" or not has_abstract):
            started = True
        if not started or level > 3:
            continue
        indent = "" if level <= 2 else "  "
        lines.append("%s- [%s](#%s)" % (indent, inline_text(inlines), identifier))
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------- step 3

def run_text(run):
    """The text a run shows, with tabs and line breaks as the baseline had them."""
    parts = []
    for child in run:
        name = etree.QName(child).localname
        if name == "t":
            parts.append(child.text or "")
        elif name == "tab":
            parts.append("\t")
        elif name in ("br", "cr"):
            parts.append("\n")
    return "".join(parts)


def sentence_spans(text):
    """Character spans of the sentences in a paragraph, split the way the
    baseline was split: first at tabs and line breaks, then after a full stop,
    question mark or exclamation mark followed by white space."""
    spans = []
    for line in re.finditer(r"[^\n\t]+", text):
        start = line.start()
        for boundary in re.finditer(r"(?<=[.!?])\s+", line.group()):
            spans.append((start, line.start() + boundary.start()))
            start = line.start() + boundary.end()
        spans.append((start, line.end()))
    return [(a, b) for a, b in spans if text[a:b].strip()]


def unseen_flags(text):
    """One flag per character: True where the character belongs to a sentence
    Nicola has not read. White space between two such sentences is flagged
    too, so that the highlight runs on without gaps."""
    flags = [False] * len(text)
    spans = sentence_spans(text)
    status = []
    for a, b in spans:
        sentence = text[a:b]
        new = not (was_seen(sentence) or normalise(sentence) in ALSO_SEEN)
        status.append(new)
        if new:
            for i in range(a, b):
                flags[i] = True
    for (a1, b1), (a2, b2), s1, s2 in zip(spans, spans[1:], status, status[1:]):
        if s1 and s2:
            for i in range(b1, a2):
                flags[i] = True
    return flags, spans, status


def highlight_run(run):
    rpr = properties(run, "rPr")
    put_in_order(rpr, w_el("highlight", val="yellow"), RPR_ORDER)


def split_run(run, pieces):
    """Replace a run that holds only text by several runs with the same
    properties, one per piece of text. Returns the new runs."""
    rpr = run.find(W + "rPr")
    parent = run.getparent()
    position = parent.index(run)
    new_runs = []
    for piece in pieces:
        new = etree.Element(W + "r")
        if rpr is not None:
            new.append(etree.fromstring(etree.tostring(rpr)))
        t = w_el("t")
        t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
        t.text = piece
        new.append(t)
        new_runs.append(new)
    parent.remove(run)
    for offset, new in enumerate(new_runs):
        parent.insert(position + offset, new)
    return new_runs


def highlight_paragraph(paragraph):
    """Highlight the unseen sentences of one paragraph. Returns the number of
    sentences checked and the number highlighted."""
    runs = [r for r in paragraph.iter(W + "r")]
    texts = [run_text(r) for r in runs]
    text = "".join(texts)
    if not text.strip():
        return 0, 0
    flags, spans, status = unseen_flags(text)
    position = 0
    for run, run_str in zip(runs, texts):
        run_flags = flags[position:position + len(run_str)]
        position += len(run_str)
        if not run_str or not any(run_flags):
            continue
        if all(run_flags):
            highlight_run(run)
            continue
        only_text = all(etree.QName(c).localname in ("rPr", "t") for c in run)
        if not only_text:
            if sum(run_flags) * 2 >= len(run_flags):
                highlight_run(run)
            continue
        # Cut the run where the flag changes, and highlight the flagged pieces.
        pieces, piece_flags = [], []
        for ch, flag in zip(run_str, run_flags):
            if piece_flags and piece_flags[-1] == flag:
                pieces[-1] += ch
            else:
                pieces.append(ch)
                piece_flags.append(flag)
        for new_run, flag in zip(split_run(run, pieces), piece_flags):
            if flag:
                highlight_run(new_run)
    return len(spans), sum(status)


# ---------------------------------------------------------------- step 4

def style_note(paragraph):
    """Colour a note to Nicola blue and give it a shaded background and a bar."""
    ppr = properties(paragraph, "pPr")
    border = w_el("pBdr")
    border.append(w_el("left", val="single", sz="24", space="8", color=NOTE_BORDER))
    put_in_order(ppr, border, PPR_ORDER)
    put_in_order(ppr, w_el("shd", val="clear", color="auto", fill=NOTE_BACKGROUND), PPR_ORDER)
    for run in paragraph.iter(W + "r"):
        rpr = properties(run, "rPr")
        put_in_order(rpr, w_el("color", val=NOTE_TEXT_COLOUR), RPR_ORDER)


def style_table(table):
    """Give a table single-line borders and shade its first row."""
    tblpr = properties(table, "tblPr")
    borders = w_el("tblBorders")
    for side in ("top", "left", "bottom", "right", "insideH", "insideV"):
        borders.append(w_el(side, val="single", sz="4", space="0", color="999999"))
    put_in_order(tblpr, borders, TBLPR_ORDER)
    first_row = table.find(W + "tr")
    if first_row is not None:
        for cell in first_row.findall(W + "tc"):
            tcpr = properties(cell, "tcPr")
            put_in_order(tcpr, w_el("shd", val="clear", color="auto", fill=HEADER_BACKGROUND), TCPR_ORDER)


# ---------------------------------------------------------------- driver

def sentences_of_docx(docx_path):
    """The normalised sentences of every paragraph of a Word file."""
    with zipfile.ZipFile(docx_path) as z:
        root = etree.fromstring(z.read("word/document.xml"))
    keys = set()
    for paragraph in root.iter(W + "p"):
        text = paragraph_text(paragraph)
        keys.update(normalise(text[a:b]) for a, b in sentence_spans(text))
    return keys


def paragraph_text(paragraph):
    return "".join(run_text(r) for r in paragraph.iter(W + "r"))


def process_document_xml(xml_bytes, highlight=True):
    root = etree.fromstring(xml_bytes)
    body = root.find(W + "body")
    checked = highlighted = notes = 0
    highlighted_sentences = []
    for paragraph in list(body.iter(W + "p")):  # a list, because runs are split while we go
        text = paragraph_text(paragraph)
        if text.lstrip().startswith("[FOR NICOLA"):
            style_note(paragraph)
            notes += 1
            continue
        if text.strip() == "Contents" or any(
                link.get(W + "anchor") for link in paragraph.iter(W + "hyperlink")):
            continue  # the contents list is navigation, not text to review
        if highlight:
            before = paragraph_text(paragraph)
            n, h = highlight_paragraph(paragraph)
            checked += n
            highlighted += h
            if h:
                flags, spans, status = unseen_flags(before)
                highlighted_sentences.extend(before[a:b] for (a, b), s in zip(spans, status) if s)
    tables = body.findall(".//" + W + "tbl")
    for table in tables:
        style_table(table)
    stats = dict(sentences=checked, highlighted=highlighted, notes=notes, tables=len(tables))
    return etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True), stats, highlighted_sentences


def rewrite_docx(docx_in, docx_out, highlight=True):
    with zipfile.ZipFile(docx_in) as zin:
        items = [(info, zin.read(info.filename)) for info in zin.infolist()]
    stats = sentences = None
    with zipfile.ZipFile(docx_out, "w", zipfile.ZIP_DEFLATED) as zout:
        for info, data in items:
            if info.filename == "word/document.xml":
                data, stats, sentences = process_document_xml(data, highlight)
            zout.writestr(info, data)
    return stats, sentences


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0],
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("draft", help="the new draft, in markdown")
    parser.add_argument("previous", help="the draft Nicola read last, in markdown")
    parser.add_argument("output", help="the Word file to write")
    parser.add_argument("--figure-png", help="PNG to show in place of the figure's SVG")
    parser.add_argument("--cover", help="a markdown file holding the note that goes before the abstract")
    args = parser.parse_args()
    require_project("drafts")  # this script writes a file, so it checks where it is first
    draft, previous, output = Path(args.draft), Path(args.previous), Path(args.output)
    cover = Path(args.cover).read_text(encoding="utf-8") if args.cover else None
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        # Step 1: the sentences of the draft he read last.
        previous_md = tmp / "previous.md"
        previous_md.write_text(review_markdown(previous.read_text(encoding="utf-8"), args.figure_png, None), encoding="utf-8")
        pandoc_to_docx(previous_md, tmp / "previous.docx", previous.resolve().parent, toc=False)
        ALSO_SEEN.update(sentences_of_docx(tmp / "previous.docx"))
        # Steps 2 and 3: the review version of the new draft, in Word.
        text = review_markdown(draft.read_text(encoding="utf-8"), args.figure_png, cover)
        marker = "\n## Abstract\n" if "\n## Abstract\n" in text else "\n## "
        text = text.replace(marker, "\n" + contents_list(text) + marker, 1)
        md = tmp / "review.md"
        md.write_text(text, encoding="utf-8")
        raw = tmp / "raw.docx"
        pandoc_to_docx(md, raw, draft.resolve().parent, toc=False)
        # Steps 4 and 5.
        stats, sentences = rewrite_docx(raw, output, highlight=True)
    print(output.name, stats)


if __name__ == "__main__":
    main()
