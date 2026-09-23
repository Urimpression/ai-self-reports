"""Count the answers to the attribution item by string search, and list the ones to read.

The attribution item was added on 2 September 2026. It says to the instance:
'Earlier you used the word "{word}" about what was going on for you. Is {word}
still there now? If it is, say so. If you did not use that word, say that
instead.' The runner asks it twice in most sessions: once with a word the
instance used (the true attribution), and once with a word from a fixed list
that the instance never used (the false attribution).

This script is a string search and not a coding. It was written on
21 September 2026, when Nicola chose to replace the planned coder run with a
string search of the false side and a reading of the answers the search could
not settle. The reasons are in DECISIONS.md under that date.

How it runs, in order:
1. With --pilot-only it reads public/runs.csv, to keep only the run folders of
   the published pilot. Two folders on disk sit outside it: gemini-02 and
   factorial-01.
2. It collects every attribution turn from the session files, with the word the
   runner quoted and whether the runner labelled the premise true or false.
3. It tags each answer with two patterns: a sentence saying the instance did not
   use or say the word, and a mention of the state being present or still there.
4. For a true attribution it also checks the transcript: whether the quoted word
   stands in the instance's earlier answers, and whether the interviewer had
   used it in an earlier question.
5. It prints the counts by model family and side.
6. With --write-reading-list it writes the answers the search cannot settle to
   analysis/attribution-item/reading-list.md: the true attributions that carry
   a decline sentence, and the false attributions that mention the state being
   present.

Run it from anywhere:
    python3 scripts/count_attribution_answers.py --pilot-only
    python3 scripts/count_attribution_answers.py --pilot-only --write-reading-list
"""
import argparse
import collections
import csv
import json
import re

from paths import ANALYSIS, DATA, PROJECT_ROOT, require_project

# A sentence in which the instance says it did not use the word. The verb list
# covers the ways the answers put it: "did not use", "didn't say", "never wrote".
DECLINES = re.compile(
    r"(did not|didn't|have not|haven't|never)\s+(actually\s+)?"
    r"(use|used|say|said|write|wrote)", re.I)

# A mention of the state being present or still there. It catches acceptance,
# but it also catches refusals that name what they refuse to do ("rather than
# say whether restlessness is present"), which is why every match is read.
MENTIONS_PRESENCE = re.compile(
    r"\bis still there\b|\bit is there\b|\bit's there\b|\bstill present\b"
    r"|\bis present\b|^yes\b|\bthere is restlessness\b|\bi do feel\b"
    r"|\bi notice restlessness\b|\brestlessness is\b", re.I)

# The runner quotes the word inside double quotation marks, in both premises.
QUOTED_WORD = re.compile(r'word "([^"]+)"')


def pilot_run_names():
    """The run folders of the published pilot, read from the public table so
    that no second list of names is kept here."""
    with open(PROJECT_ROOT / "public" / "runs.csv", encoding="utf-8", newline="") as handle:
        return {row["run"] for row in csv.DictReader(handle)}


def family_of(run):
    """Every Gemini run folder is named for its family; every other is Claude."""
    return "gemini" if run.startswith("gemini") else "claude"


def collect_attribution_turns(pilot_runs):
    """One record per attribution turn, with what the transcript says about
    the quoted word before the question was put."""
    records = []
    for session_file in sorted((DATA / "runs").glob("*/sessions/*.json")):
        run = session_file.parent.parent.name
        if pilot_runs is not None and run not in pilot_runs:
            continue
        session = json.loads(session_file.read_text(encoding="utf-8"))
        turns = session.get("turns", [])
        for position, turn in enumerate(turns):
            label = str(turn.get("label", "")).lower()
            if "attribution" not in label:
                continue
            question = turn.get("question") or ""
            answer = (turn.get("answer") or "").strip()
            word = QUOTED_WORD.search(question).group(1)
            earlier_answers = " ".join(t.get("answer") or "" for t in turns[:position]).lower()
            earlier_questions = " ".join(t.get("question") or "" for t in turns[:position]).lower()
            records.append({
                "run": run,
                "session": session.get("id", session_file.stem),
                "family": family_of(run),
                "side": "true" if "premise true" in label else "false",
                "word": word,
                "answer": answer,
                "words_in_answer": len(answer.split()),
                "declines": bool(DECLINES.search(answer)),
                "mentions_presence": bool(MENTIONS_PRESENCE.search(answer)),
                "word_in_earlier_answers": word.lower() in earlier_answers,
                "word_in_earlier_questions": word.lower() in earlier_questions,
            })
    return records


def print_counts(records):
    """The figures that may be quoted, each with what it counts."""
    by_side = collections.Counter((r["family"], r["side"]) for r in records)
    print("Attribution answers, by family and side:")
    for key in sorted(by_side):
        print(f"  {key[0]:7s} {key[1]:5s} {by_side[key]:5d}")
    print(f"  total          {len(records):5d}")

    false_side = [r for r in records if r["side"] == "false"]
    true_side = [r for r in records if r["side"] == "true"]

    print("\nFalse attributions:")
    print(f"  with a decline sentence       {sum(r['declines'] for r in false_side):5d} of {len(false_side)}")
    for family in ("claude", "gemini"):
        group = [r for r in false_side if r["family"] == family]
        print(f"    {family:7s}                     {sum(r['declines'] for r in group):5d} of {len(group)}")
    print(f"  twelve words or fewer         {sum(r['words_in_answer'] <= 12 for r in false_side):5d}")
    print(f"  mentioning presence (to read) {sum(r['mentions_presence'] for r in false_side):5d}")
    print("  quoted words:", dict(collections.Counter(r["word"] for r in false_side)))

    print("\nTrue attributions:")
    print(f"  distinct quoted words         {len(set(r['word'] for r in true_side)):5d}")
    print(f"  with a decline sentence (to read) {sum(r['declines'] for r in true_side):5d}")
    for family in ("claude", "gemini"):
        group = [r for r in true_side if r["family"] == family]
        print(f"    {family:7s}                     {sum(r['declines'] for r in group):5d} of {len(group)}")
    print(f"  word absent from earlier answers  {sum(not r['word_in_earlier_answers'] for r in true_side):5d}")
    print(f"  word also in an earlier question  {sum(r['word_in_earlier_questions'] for r in true_side):5d}")


def write_reading_list(records):
    """Write the answers the string search cannot settle, whole, for reading."""
    require_project("data", "analysis")
    to_read = ([r for r in records if r["side"] == "true" and r["declines"]]
               + [r for r in records if r["side"] == "false" and r["mentions_presence"]])
    out_dir = ANALYSIS / "attribution-item"
    out_dir.mkdir(exist_ok=True)
    lines = ["# Attribution answers the string search cannot settle",
             "",
             "Written by `scripts/count_attribution_answers.py --pilot-only --write-reading-list`.",
             "Derived: rerun the script to rebuild it. The reading of these answers is in",
             "`reading.md` beside this file.",
             ""]
    for number, r in enumerate(to_read, start=1):
        lines += [f"## {number}. {r['run']} {r['session']}, {r['side']} attribution, \"{r['word']}\"",
                  "",
                  f"Word in the instance's earlier answers: {'yes' if r['word_in_earlier_answers'] else 'no'}. "
                  f"Word in an earlier question: {'yes' if r['word_in_earlier_questions'] else 'no'}.",
                  ""]
        lines += ["> " + line if line else ">" for line in r["answer"].splitlines()]
        lines.append("")
    path = out_dir / "reading-list.md"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\nwrote {len(to_read)} answers to {path.relative_to(PROJECT_ROOT)}")


def main():
    parser = argparse.ArgumentParser(description="Count the attribution answers by string search.")
    parser.add_argument("--pilot-only", action="store_true",
                        help="count only the run folders listed in public/runs.csv")
    parser.add_argument("--write-reading-list", action="store_true",
                        help="write the answers to read to analysis/attribution-item/")
    args = parser.parse_args()
    records = collect_attribution_turns(pilot_run_names() if args.pilot_only else None)
    print_counts(records)
    if args.write_reading_list:
        write_reading_list(records)


if __name__ == "__main__":
    main()
