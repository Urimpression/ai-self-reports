"""Pull every comment out of a Word review copy, together with the passage it marks.

Nicola reads a draft away from his desk as a Word file and comments on it in
Google Docs. Word stores each comment in `word/comments.xml` and marks the words
it belongs to in `word/document.xml` with a start tag and an end tag carrying the
same number. This script walks the document once, keeps the text of every range
that is currently open, and so hands back each comment beside the words it is
attached to, the heading it falls under, and the sentence that runs up to it.

Usage:
    python3 extract_review_comments.py "<path to the .docx>" > pairs.md

Reading only. It never writes into the document.
"""

import re
import sys
import zipfile
import xml.etree.ElementTree as ET

WORD = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
W15 = "{http://schemas.microsoft.com/office/word/2012/wordml}"

# How much text to keep on either side of a comment, in characters. Long enough
# to find the passage in the markdown, short enough to read in a table.
ANCHOR_LIMIT = 400
RUNUP_LIMIT = 120


def tag(element, name):
    return element.tag == WORD + name


def paragraph_style(paragraph):
    """The style name of a paragraph, or None. Headings are how we locate a comment."""
    properties = paragraph.find(WORD + "pPr")
    if properties is None:
        return None
    style = properties.find(WORD + "pStyle")
    if style is None:
        return None
    return style.get(WORD + "val")


def paragraph_text(paragraph):
    return "".join(node.text or "" for node in paragraph.iter(WORD + "t"))


def read_comment_bodies(archive):
    """id -> {author, date, text} for every comment in the file."""
    bodies = {}
    root = ET.fromstring(archive.read("word/comments.xml"))
    for comment in root.iter(WORD + "comment"):
        paragraphs = [paragraph_text(p) for p in comment.iter(WORD + "p")]
        text = "\n".join(p for p in paragraphs if p.strip())
        bodies[comment.get(WORD + "id")] = {
            "author": comment.get(WORD + "author") or "",
            "date": (comment.get(WORD + "date") or "")[:16].replace("T", " "),
            "text": text.strip(),
        }
    return bodies


def read_reply_links(archive):
    """paragraph-id -> parent paragraph-id, so replies can be told from new comments."""
    if "word/commentsExtended.xml" not in archive.namelist():
        return {}
    links = {}
    root = ET.fromstring(archive.read("word/commentsExtended.xml"))
    for entry in root.iter(W15 + "commentEx"):
        parent = entry.get(W15 + "paraIdParent")
        if parent:
            links[entry.get(W15 + "paraId")] = parent
    return links


def walk_document(archive):
    """Walk the body once, returning a record per comment in the order they appear."""
    root = ET.fromstring(archive.read("word/document.xml"))

    open_ranges = {}        # comment id -> list of text pieces inside the range
    running_text = []       # everything seen so far, for the run-up
    current_heading = ""
    found = []
    seen = set()

    for element in root.iter():
        if tag(element, "p"):
            style = paragraph_style(element)
            # Word names heading styles Heading1, Heading2 and so on.
            if style and style.startswith("Heading"):
                heading = paragraph_text(element).strip()
                if heading:
                    current_heading = heading
        elif tag(element, "t"):
            piece = element.text or ""
            running_text.append(piece)
            for pieces in open_ranges.values():
                pieces.append(piece)
        elif tag(element, "commentRangeStart"):
            number = element.get(WORD + "id")
            open_ranges[number] = []
            found.append({
                "id": number,
                "heading": current_heading,
                "runup": "".join(running_text)[-RUNUP_LIMIT:],
                "anchor": None,
            })
            seen.add(number)
        elif tag(element, "commentRangeEnd"):
            number = element.get(WORD + "id")
            pieces = open_ranges.pop(number, None)
            if pieces is not None:
                for record in found:
                    if record["id"] == number:
                        record["anchor"] = "".join(pieces)
        elif tag(element, "commentReference"):
            number = element.get(WORD + "id")
            # A comment with no marked range still has a reference mark. Keep it,
            # anchored to nothing, rather than losing it silently.
            if number not in seen:
                seen.add(number)
                found.append({
                    "id": number,
                    "heading": current_heading,
                    "runup": "".join(running_text)[-RUNUP_LIMIT:],
                    "anchor": None,
                })

    return found


def tidy(text):
    """One line, no pipes, so it survives a markdown table cell."""
    if text is None:
        return ""
    text = re.sub(r"\s+", " ", text).strip()
    return text.replace("|", "\\|")


def shorten(text, limit):
    if len(text) <= limit:
        return text
    half = limit // 2
    return text[:half] + " […] " + text[-half:]


def main():
    if len(sys.argv) < 2:
        sys.exit("Give the path to the .docx review copy.")
    path = sys.argv[1]

    with zipfile.ZipFile(path) as archive:
        bodies = read_comment_bodies(archive)
        replies = read_reply_links(archive)
        records = walk_document(archive)

    print(f"Comments in the file: {len(bodies)}. Anchors found in the body: {len(records)}.")
    print()
    print("| # | Section | Words it marks | What Nicola wrote |")
    print("|---|---|---|---|")

    unanchored = []
    for position, record in enumerate(records, start=1):
        body = bodies.get(record["id"], {})
        anchor = record["anchor"]
        if not anchor:
            unanchored.append(position)
            shown = "(no marked range) …" + tidy(record["runup"])
        else:
            shown = tidy(shorten(anchor, ANCHOR_LIMIT))
        print(f"| {position} | {tidy(record['heading'])} | {shown} | {tidy(body.get('text', ''))} |")

    if unanchored:
        print()
        print("Comments with no marked range, shown with the words that run up to them "
              f"instead: {', '.join(str(n) for n in unanchored)}.")

    missing = set(bodies) - {r["id"] for r in records}
    if missing:
        print()
        print(f"In comments.xml but never referenced in the body: {len(missing)}.")
    if replies:
        print()
        print(f"Reply threads recorded in the file: {len(replies)}.")


if __name__ == "__main__":
    main()
