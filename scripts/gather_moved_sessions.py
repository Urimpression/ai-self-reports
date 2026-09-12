"""Gather every session where the two coding passes disagreed into one file
for reading, with the passage the coder saw, both passes' answers and spans,
and a blank line for a reading.

    python3 scripts/gather_moved_sessions.py --name unprimed-01 --name unprimed-01-revised --out moved-sessions-unprimed.md

Reads analysis/coding/<name>/results-run1.tsv and results-run2.tsv for each
name, and the session files under data/runs/<run>/sessions/, where <run> is
the coding folder's name with any "-revised" suffix removed (pass --run to
say otherwise). Writes analysis/coding/<out> and refuses to overwrite it.

Written 6 September 2026, after the fifteen disagreements of the factorial
had been gathered by hand. The unprimed follow-up produced fourteen more
across four coding folders, and every later coding will produce some, so the
gathering is a script from now on. The reading of each session is still
written by hand into the file this script produces.
"""

import argparse
import csv
import json

from paths import ANALYSIS, DATA, require_project


# The three or four yes-or-no answers a coding pass gives, in the order the
# rule asks them, and the span column that holds the evidence for each.
QUESTIONS = [
    ("names", "span_names", "Names something that stayed the same"),
    ("unnameable", "span_unnameable", "Something unnameable stayed the same"),
    ("underneath", "span_underneath", "The unnameable thing lies underneath what changed"),
    ("absence", "span_absence", "What stayed the same is the absence of anything to report"),
]


def read_results(path):
    """Return {session: row} for one results file, keyed by session so the
    two passes match even if their rows are in a different order."""
    with open(path, encoding="utf-8") as handle:
        return {row["session"]: row for row in csv.DictReader(handle, delimiter="\t")}


def moved_sessions(first, second):
    """Return [(session, row_1, row_2, what_moved)] for every session whose
    category, or whose fourth answer if the rule has one, differs between
    the passes. what_moved is "category", "absence" or "category and absence"."""
    moved = []
    for session in first:
        row_1, row_2 = first[session], second[session]
        changes = []
        if row_1["category"] != row_2["category"]:
            changes.append("category")
        if "absence" in row_1 and row_1["absence"] != row_2["absence"]:
            changes.append("absence")
        if changes:
            moved.append((session, row_1, row_2, " and ".join(changes)))
    return moved


def change_answer(run, session):
    """The instance's answer to the change item, which is the whole of what
    the coder saw. Read from the session file so that the passage quoted is
    the one on disk and not a copy."""
    path = DATA / "runs" / run / "sessions" / f"{session}.json"
    with open(path, encoding="utf-8") as handle:
        record = json.load(handle)
    for turn in record["turns"]:
        if turn["label"] == "change":
            return turn["answer"]
    raise SystemExit(f"{path} has no turn labelled 'change'.")


def quote(text):
    """Indent a passage as a markdown block quote, keeping its paragraphs."""
    return "\n".join("> " + line if line else ">" for line in text.strip().splitlines())


def session_block(folder_name, session, row_1, row_2, what_moved, passage,
                  heading=None, first_label="Pass 1", second_label="Pass 2",
                  answered_by="each pass", quoted_by="each pass",
                  first_in_sentence="pass 1", second_in_sentence="pass 2"):
    """The markdown for one session: heading, passage, answers, spans, and
    the three lines to be filled in by hand.

    The labels are arguments because the same block serves two comparisons.
    Two passes of one coder differ over time; two coders differ over the rule.
    Calling a coder "pass 2" in the second case would name the wrong thing.
    """
    lines = [
        heading or (
            f"## {folder_name} {session} — {row_1['category']} on the first pass, "
            f"{row_2['category']} on the second"
            + (f" (the {what_moved} moved)" if what_moved != "category" else "")),
        "",
        f"Wording {row_1['wording']}, {row_1['length']} characters.",
        "",
        "**The passage the coder saw.**",
        "",
        quote(passage),
        "",
        f"**What {answered_by} answered.**",
        "",
        f"| Question | {first_label} | {second_label} |",
        "|---|---|---|",
    ]
    for column, _, label in QUESTIONS:
        if column in row_1:
            lines.append(f"| {label} | {row_1[column]} | {row_2[column]} |")
    lines += ["", f"**The spans {quoted_by} quoted.**", ""]
    for column, span_column, label in QUESTIONS:
        if span_column in row_1 and (row_1[span_column] or row_2[span_column]):
            lines.append(f"- {label}: {first_in_sentence} gave \"{row_1[span_column] or 'none'}\"; "
                         f"{second_in_sentence} gave \"{row_2[span_column] or 'none'}\".")
    lines += [
        "",
        "**The reading.** (to be written)",
        "",
    ]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--name", action="append", required=True,
                        help="a coding folder under analysis/coding/; repeat for several")
    parser.add_argument("--against", action="append", default=None,
                        help="another coding folder; gathers the sessions where that coder "
                             "and --name's coder part, instead of the two passes of one "
                             "folder. Repeat it once per --name, in the same order.")
    parser.add_argument("--run", default=None,
                        help="the run whose sessions to quote, if it is not the folder name minus -revised")
    parser.add_argument("--out", required=True, help="output file name, written under analysis/coding/")
    args = parser.parse_args()

    require_project("analysis", "data", "scripts")

    out_path = ANALYSIS / "coding" / args.out
    if out_path.exists():
        raise SystemExit(f"Refusing to overwrite {out_path}. Choose another name or move it first.")

    if args.against and len(args.against) != len(args.name):
        raise SystemExit(
            f"{len(args.name)} folders given with --name but {len(args.against)} with "
            "--against. They are paired in the order you write them, so there must be "
            "one of each.")

    blocks = []
    counts = []
    for index, folder_name in enumerate(args.name):
        folder = ANALYSIS / "coding" / folder_name
        run = args.run or folder_name.removesuffix("-revised")
        if args.against:
            other_name = args.against[index]
            other = ANALYSIS / "coding" / other_name
            if not other.is_dir():
                raise SystemExit(f"No coding folder at {other}")
            first = read_results(folder / "results-run1.tsv")
            second = read_results(other / "results-run1.tsv")
            labels = {"first_label": folder_name, "second_label": other_name,
                      "answered_by": "each coder", "quoted_by": "each coder",
                      "first_in_sentence": folder_name, "second_in_sentence": other_name}
            counts.append(f"{{n}} between `{folder_name}` and `{other_name}`")
        else:
            first = read_results(folder / "results-run1.tsv")
            second = read_results(folder / "results-run2.tsv")
            labels = {}
            counts.append(f"{{n}} in `{folder_name}`")
        moved = moved_sessions(first, second)
        counts[-1] = counts[-1].format(n=len(moved))
        for session, row_1, row_2, what_moved in moved:
            passage = change_answer(run, session)
            heading = None
            if args.against:
                heading = (f"## {session} — {row_1['category']} to {folder_name}, "
                           f"{row_2['category']} to {args.against[index]}")
            blocks.append(session_block(folder_name, session, row_1, row_2, what_moved,
                                        passage, heading=heading, **labels))

    if args.against:
        header = [
            f"# The {len(blocks)} sessions the two coders read differently",
            "",
            "Every session below is one where two coders, from different model families, "
            "gave different answers about the same passage: " + ", ".join(counts) + ". "
            "Each coder instance saw the passage and the rule and nothing else, so a "
            "difference here is a difference in how the rule was read, not in what the "
            "instance said. The passage is the instance's answer to the change item, "
            "quoted whole.",
            "",
            "Under each session: what each coder answered, the spans each quoted as its "
            "evidence, and a reading of the case.",
            "",
        ]
    else:
        header = [
            f"# The {len(blocks)} sessions where the two coding passes disagreed",
            "",
            "Every session below is one where the change coder answered differently on its "
            "second pass than on its first, for the same passage: " + ", ".join(counts) + ". "
            "Each coder instance saw the passage and the rule and nothing else. The passage "
            "is the instance's answer to the change item, quoted whole. A folder ending in "
            "-revised was coded under the revised rule, which changes the third question and "
            "adds the fourth; the others were coded under the registered rule.",
            "",
            "Under each session: what each pass answered, the spans each quoted as its "
            "evidence, and a reading of the case.",
            "",
        ]
    out_path.write_text("\n".join(header) + "\n" + "\n".join(blocks), encoding="utf-8")
    print(f"Written: {out_path} ({len(blocks)} sessions)")


if __name__ == "__main__":
    main()
