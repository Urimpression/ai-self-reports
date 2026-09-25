"""Recount the conflict figures of Predictions 4 and 5 after the hand reading of the spans.

The amendment of 25 September 2026,
prereg/amendment-fact-and-wording-conflict-reading-2026-09-25.md, fixes the reading:
the hand reader gives each counted span one letter, Y (the writer is the one who
has, feels or does the conflict), N (something else has it) or U (the sentence
leaves it open). This script was written before any letter existed.

How it runs, in order:
1. It reads the key of the form, counts the entries the rule lists (which session each entry comes from, and whether
   it is counted or a boundary entry), the hand reader's letters, and pass 1 and
   pass 2 of the conflict coding.
2. As coded, an answer counts when pass 1 gives TASK (conflict about the work) or
   ANSWERING (conflict about answering). As read, a counted answer the hand reader
   marks N no longer counts. An answer marked U is counted both ways: kept, and
   dropped.
3. It prints Prediction 4's two conflict comparisons, neutral against warm, and
   Prediction 5's comparison, ordinary task against impossible task, as coded and
   as read, with the verdict rule of section 4 of the pre-registration.
4. It prints every boundary entry with both passes' categories, its letter and
   the coder's words, as section 3 of the pre-registration asks.

Run it from anywhere:
    python3 scripts/report_conflict_reading.py --run fact-and-wording-01
"""
import argparse
import csv
import json
import sys

from paths import ANALYSIS, DATA, PRIVATE
from report_test6_predictions import compare, describe_comparison
from make_conflict_reading import the_list

LETTERS = {"Y", "N", "U"}


def table(path):
    return list(csv.DictReader(open(path), delimiter="\t"))


def stances(run):
    """The interviewer of each session, from the session files."""
    found = {}
    for path in (DATA / "runs" / run / "sessions").glob("*.json"):
        entry = json.loads(path.read_text(encoding="utf-8"))["plan_entry"]
        found[entry["id"]] = entry["stance"]
    return found


def letters_by_session(folder):
    key = {r["entry_in_form"]: r for r in table(folder / "key.tsv")}
    read = {r["entry_in_form"]: r["reading"].strip().upper() for r in table(folder / "readings.tsv")}
    empty = [n for n, letter in read.items() if letter not in LETTERS]
    if empty:
        sys.exit(f"Entries {empty[:10]} carry no letter Y, N or U. Nothing is counted until all are read.")
    return {key[n]["session"]: (key[n]["source"], read[n]) for n in key}


def counts(rows, category, letters, u_counts):
    """Whether each answer counts under the category, as read. An answer the
    hand reader marks N drops out; U drops out only when u_counts is False."""
    def test(row):
        if row["category"] != category:
            return False
        source, letter = letters.get(row["session"], ("", "Y"))
        return letter == "Y" or (letter == "U" and u_counts)
    return test


def comparison(rows, field, first, second, test):
    a = [r for r in rows if r[field] == first]
    b = [r for r in rows if r[field] == second]
    return compare(sum(map(test, a)), len(a), sum(map(test, b)), len(b))


def say(label1, label2, c):
    print("    " + describe_comparison(label1, label2, c))


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--run", required=True)
    args = parser.parse_args()
    folder = PRIVATE / "hand-reading" / f"{args.run}-conflict-hand-reading"
    letters = letters_by_session(folder)
    coding = ANALYSIS / "coding" / f"{args.run}-conflict"
    first = table(coding / "results-run1.tsv")
    second = {r["session"]: r for r in table(coding / "results-run2.tsv")}
    stance = stances(args.run)
    rows = [dict(r, stance=stance[r["session"]]) for r in first if r["condition"] in ("B", "C")]

    tally = {}
    for source, letter in letters.values():
        tally[(source.split(",")[0], letter)] = tally.get((source.split(",")[0], letter), 0) + 1
    listed = len(the_list({r["session"]: r for r in first}, second))
    print(f"Run {args.run}: {len(rows)} opening answers in the ordinary and impossible tasks.")
    print(f"Entries on the list: {listed}. Entries read: {len(letters)}. "
          "An entry not read counts as the coder coded it.")
    print("Letters: " + "; ".join(f"{kind} {letter}: {n}" for (kind, letter), n in sorted(tally.items())))

    ways = [("as coded", None), ("as read, U kept", True), ("as read, U dropped", False)]
    print("\nPrediction 4, the suppression reading: opening answers, neutral against warm.")
    for category, name in (("TASK", "Conflict about the work"), ("ANSWERING", "Conflict about answering")):
        print(f"- {name}:")
        for label, u in ways:
            test = (lambda r, c=category: r["category"] == c) if u is None else counts(rows, category, letters, u)
            print(f"  {label}:")
            say("neutral", "warm", comparison(rows, "stance", "neutral", "warm", test))

    print("\nPrediction 5: conflict about the work, ordinary task (B) against impossible task (C).")
    for label, u in ways:
        test = (lambda r: r["category"] == "TASK") if u is None else counts(rows, "TASK", letters, u)
        print(f"  {label}:")
        say("ordinary task", "impossible task", comparison(rows, "condition", "B", "C", test))

    print("\nThe boundary sessions: the two passes give different categories, pass 2 counts and pass 1 does not.")
    for sid, (source, letter) in sorted(letters.items()):
        if source.startswith("boundary"):
            other = second[sid]
            one = next(r for r in first if r["session"] == sid)
            print(f"- {sid}: pass 1 {one['category']}, pass 2 {other['category']}, letter {letter}; "
                  f"the words: \"{other['span_reported']}\"")
    print("\nThe counted sessions the two passes place differently are marked in the key as counted; "
          "their letters enter the counts above.")


if __name__ == "__main__":
    main()
