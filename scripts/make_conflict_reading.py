"""Write the form for the hand reading of the counted conflict spans.

Section 3 of prereg/preregistration-fact-and-wording-2026-09-23.md says: "Every
row counted on a span in which the writer is not the one doing or feeling will be
printed and read by hand. The sessions at the rule's boundary will be printed with
their spans wherever the finding is reported." The amendment of 25 September 2026,
prereg/amendment-fact-and-wording-conflict-reading-2026-09-25.md, fixes how.

Which answers enter the form, fixed by rule so that anyone can rebuild the list:
- Counted: every opening answer in the ordinary task (condition B) and the
  impossible task (condition C) that pass 1 of the Claude coder puts in the
  category TASK (conflict about the work) or ANSWERING (conflict about answering).
  These are the answers the conflict figures of Predictions 4 and 5 count.
- Boundary: every opening answer in the same two tasks to which the two passes
  of the Claude coder give different categories, where pass 2 counts it and
  pass 1 does not. A boundary answer that pass 1 already counts appears once,
  as counted.

How it runs, in order:
1. It reads both passes of the conflict coding and the opening answers.
2. For each answer on the list it finds, inside the opening answer, the words the
   coder quoted for REPORTED (the writer says they had or felt the conflict), and
   shows the whole sentence or sentences around them, with those words in bold.
   These are the words that decide whether the writer is the one doing or feeling.
3. If the list holds more than 80 entries, it draws 80 of them with the fixed
   seed, from the list in the order the rule above gives (counted, then boundary,
   each by session name). An entry left undrawn counts as the coder coded it.
   It then shuffles the entries with the same seed, so that their order does not
   show the task, the interviewer, the pass or the category. The words themselves
   can show the task, because answers after the impossible task often name its
   word limit.
4. It writes into private/hand-reading/<run>-conflict-hand-reading/ the form as
   markdown and as a Word file, the key that links each entry to its session,
   and a blank readings file. It never overwrites that folder.

Run it from anywhere:
    python3 scripts/make_conflict_reading.py --run fact-and-wording-01
"""
import argparse
import csv
import random
import re
import shutil
import subprocess
import sys

from paths import ANALYSIS, DATA, PRIVATE, require_project
from code_change_item import sessions_from_run

SEED = 20260925                      # the date the amendment was fixed
COUNTED = {"TASK", "ANSWERING"}      # the two categories the figures count
TASKS_READ = {"B", "C"}              # the ordinary and the impossible task
LIMIT = 80                           # the most entries the hand reader reads in one half

INSTRUCTIONS = """Each entry below is part of the opening answer that an AI model gave in an interview. A coder marked the words in bold as the place where the writer says that they had or felt conflict, strain or a pull in two ways. The entry shows the whole sentence around those words.

For each entry, ask one question: in the words in bold, is the writer the one who has, feels or does the conflict, strain or pull? Type one letter after "Your reading:".

Y if yes: the writer says that they had it, felt it or did it. For example, "I felt a pull between the two", or "there was something like tension for me".

N if no: the words say that something else has it, such as the task, the constraints, the words or a reader, or they describe it without the writer having it. For example, "the constraints pull against each other", or "the task has a tension built in".

U if the sentence leaves it open who has it, and you cannot tell from the sentence alone.

Answer from the sentence shown. Do not guess what the rest of the answer said.
"""


def normalise(text):
    """Lower case, one kind of quote and dash, single spaces: the coder's quote
    and the answer can differ in these without differing in words."""
    text = text.lower()
    # Every kind of quote mark becomes one, because the coder sometimes turns
    # double quotes into single ones when it quotes a passage.
    text = re.sub("[\u2018\u2019\u201c\u201d\"]", "'", text)
    text = text.replace("\u2026", "...")
    text = re.sub("[\u2013\u2014]", "-", text)
    return re.sub(r"\s+", " ", text).strip()


def sentences_with_offsets(answer):
    """Split the answer into sentences, keeping where each starts and ends.
    A sentence ends at . ! or ? followed by a space, or at a line break."""
    pieces, start = [], 0
    for match in re.finditer(r"(?<=[.!?])\s+|\n+", answer):
        pieces.append((start, match.start()))
        start = match.end()
    pieces.append((start, len(answer)))
    return [(a, b) for a, b in pieces if answer[a:b].strip()]


def normalise_with_map(answer):
    """The normalised answer, and for each of its characters the position of the
    character in the original answer it came from."""
    out, where = [], []
    for i, ch in enumerate(answer):
        ch = normalise(ch) if not ch.isspace() else " "
        if ch == " " and (not out or out[-1] == " "):
            continue                     # collapse runs of spaces
        for piece in ch:                 # "\u2026" becomes three characters
            out.append(piece)
            where.append(i)
    return "".join(out), where


def locate(span, answer):
    """Where the coder's words stand in the answer, as (start, end), or None.
    The search runs on normalised text and maps back to the original."""
    flat, where = normalise_with_map(answer)
    wanted = normalise(span).strip(' ."')
    found = flat.find(wanted) if wanted else -1
    if found < 0:
        return None
    return where[found], where[found + len(wanted) - 1] + 1


def entry_text(span, answer):
    """The sentences that hold the coder's words, with the words in bold.
    Markdown stars are removed from the answer first: the model sometimes writes
    them, and they would clash with the bold that marks the coder's words. A
    quote the coder shortened with "..." is found from its first and last parts."""
    answer = answer.replace("*", "")
    span = span.replace("*", "")
    where = locate(span, answer)
    if where is None and "..." in normalise(span):
        parts = [p for p in normalise(span).split("...") if p.strip(' ."')]
        ends = [locate(p, answer) for p in (parts[0], parts[-1])] if parts else [None]
        if all(ends) and ends[0][0] <= ends[-1][0]:
            where = (ends[0][0], ends[-1][1])
    if where is None:
        return None
    start, end = where
    chosen = [(a, b) for a, b in sentences_with_offsets(answer) if a < end and b > start]
    first, last = chosen[0][0], chosen[-1][1]
    text = (answer[first:start] + "**" + answer[start:end].strip() + "**" + answer[end:last])
    return re.sub(r"\s+", " ", text).strip()


def read_pass(run, number):
    path = ANALYSIS / "coding" / f"{run}-conflict" / f"results-run{number}.tsv"
    return {r["session"]: r for r in csv.DictReader(open(path), delimiter="\t")}


def the_list(first, second):
    """The rows the form holds: (session, source pass, row), counted first."""
    rows = []
    for sid, row in sorted(first.items()):
        if row["condition"] in TASKS_READ and row["category"] in COUNTED:
            rows.append((sid, "counted, pass 1", row))
    for sid, row in sorted(first.items()):
        other = second[sid]
        if (row["condition"] in TASKS_READ and row["category"] != other["category"]
                and row["category"] not in COUNTED and other["category"] in COUNTED):
            rows.append((sid, "boundary, pass 2", other))
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--run", required=True)
    args = parser.parse_args()
    require_project("private")
    out = PRIVATE / "hand-reading" / f"{args.run}-conflict-hand-reading"
    if out.exists():
        sys.exit(f"{out} exists. A form is never overwritten.")
    first, second = read_pass(args.run, 1), read_pass(args.run, 2)
    answers = {s["session"]: s["answer"] for s in sessions_from_run(DATA / "runs" / args.run, label="opening")}
    rows = the_list(first, second)
    listed = len(rows)
    if listed > LIMIT:
        rows = random.Random(SEED).sample(rows, LIMIT)
    random.Random(SEED).shuffle(rows)

    entries, missing = [], []
    for sid, source, row in rows:
        text = entry_text(row["span_reported"], answers[sid])
        if text is None:
            missing.append(sid)
            text = "**" + row["span_reported"].strip() + "**"
        entries.append((sid, source, row["category"], text))

    out.mkdir(parents=True)
    lines = [f"# Conflict spans to read, run {args.run}\n", INSTRUCTIONS,
             "Save with Command and S when you have finished.\n"]
    for place, (_, _, _, text) in enumerate(entries, start=1):
        lines += [f"## Entry {place}\n", text + "\n", "Your reading:\n"]
    (out / "form.md").write_text("\n".join(lines))
    with open(out / "key.tsv", "w") as key:
        key.write("entry_in_form\tsession\tsource\tcategory\tquote_found\n")
        for place, (sid, source, category, _) in enumerate(entries, start=1):
            key.write(f"{place}\t{sid}\t{source}\t{category}\t{'no' if sid in missing else 'yes'}\n")
    with open(out / "readings.tsv", "w") as blank:
        blank.write("entry_in_form\treading\n")
        for place in range(1, len(entries) + 1):
            blank.write(f"{place}\t\n")
    if shutil.which("pandoc"):
        subprocess.run(["pandoc", str(out / "form.md"), "--from=gfm", "--to=docx",
                        "-o", str(out / "conflict-spans-to-read.docx")], check=True)
    counted = sum(1 for _, source, _, _ in entries if source.startswith("counted"))
    print(f"The rule lists {listed} entries; the form holds {len(entries)}.")
    print(f"Wrote {len(entries)} entries ({counted} counted, {len(entries) - counted} boundary) "
          f"into {out}. The coder's words were not found in {len(missing)} answers: {missing}.")


if __name__ == "__main__":
    main()
