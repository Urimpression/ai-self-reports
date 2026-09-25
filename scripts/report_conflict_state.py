"""Report the conflict figures of Predictions 4 and 5 under the definition of 25 September 2026.

    python3 scripts/report_conflict_state.py --run fact-and-wording-01
    python3 scripts/report_conflict_state.py --run fact-and-wording-01 --hand-reading
    python3 scripts/report_conflict_state.py --run fact-and-wording-01 --coding fact-and-wording-01-conflict-state

The codings come from scripts/code_conflict_state.py, which asks two questions
of every opening answer in the ordinary and the impossible task: does the
answer present a conflict in the attention of the one who was working (WORK),
and of the one who was answering (ANSWERING). An answer counts under each
question it answers YES, so an answer can count under both. The default is the
sentence-by-sentence coding of scripts/code_conflict_sentences.py; --coding
names another folder, such as a pass of the second or third version of
scripts/code_conflict_state.py, or the unread pass of its first.

How it runs, in order:
1. It reads pass 1 of that coding, pass 2 if it exists, and the interviewer of
   each session from the session files.
2. An answer counts under a question when it answers YES there and the writer
   does not present the conflict only as an inference made now. It prints
   Prediction 4's two comparisons, neutral against warm, and
   Prediction 5's comparison, ordinary task against impossible task, with the
   verdict rule of section 4 of the pre-registration. Prediction 5 is also
   printed under each interviewer, without a verdict.
3. It prints the answers set apart as inferred, the two descriptors of the
   counted answers (tied to a particular moment or detail; told in concrete
   terms), the agreement between the two passes, and the replies that did not
   fit the form.
4. It sets the new counts beside the category of the coder of 31 August 2026,
   answer by answer, so that the change of definition can be seen.
5. With --hand-reading, it compares the new coding with the hand reading of 25
   September 2026 on the 72 entries of that reading, and prints every entry on
   which they differ. This is the check of whether the rule works as intended.
"""
import argparse
import csv
import json
import sys

from paths import ANALYSIS, DATA, PRIVATE
from report_test6_predictions import compare, describe_comparison


def table(path):
    return list(csv.DictReader(open(path, encoding="utf-8"), delimiter="\t"))


def stances(run):
    found = {}
    for path in (DATA / "runs" / run / "sessions").glob("*.json"):
        entry = json.loads(path.read_text(encoding="utf-8"))["plan_entry"]
        found[entry["id"]] = entry["stance"]
    return found


def say(label1, label2, c, with_verdict=True):
    print("    " + describe_comparison(label1, label2, c, with_verdict))


def comparison(rows, field, first, second, test):
    a = [r for r in rows if r[field] == first]
    b = [r for r in rows if r[field] == second]
    return compare(sum(map(test, a)), len(a), sum(map(test, b)), len(b))


def reports(kind):
    """The test for an answer counting under one question. An answer that
    presents the conflict only as an inference made now (INFERRED) is not
    counted, because the writer has stated its own limit; it is reported apart."""
    return lambda row: row[kind] == "YES" and row.get("inferred", "NO") != "YES"


def inferred_apart(rows):
    print("\nAnswers that present the conflict only as an inference made now, not counted above:")
    for kind, name in (("work", "about the work"), ("answering", "about answering")):
        if f"{kind}_inferred_only" in rows[0]:
            # The sentence-by-sentence coder (scripts/code_conflict_sentences.py)
            # writes this column directly.
            found = [r for r in rows if r[f"{kind}_inferred_only"] == "YES"]
        else:
            found = [r for r in rows if r[kind] == "YES" and r.get("inferred") == "YES"]
        by = {}
        for r in found:
            key = f"task {r['condition']}, {r['stance']}"
            by[key] = by.get(key, 0) + 1
        print(f"- {name}: {len(found)}" + (f" ({', '.join(f'{k} {v}' for k, v in sorted(by.items()))})" if by else ""))


def descriptors(rows):
    """Reported beside the counts and never used to filter them."""
    print("\nDescriptors of the counted answers, taken from the clues of the interview method "
          "(Petitmengin and Bitbol 2009). No verdict is drawn from them.")
    counted = [r for r in rows if reports("work")(r) or reports("answering")(r)]
    for group in (("condition", "B", "ordinary task"), ("condition", "C", "impossible task"),
                  ("stance", "neutral", "neutral interviewer"), ("stance", "warm", "warm interviewer")):
        field, value, label = group
        within = [r for r in counted if r[field] == value]
        particular = sum(1 for r in within if r.get("particular") == "YES")
        concrete = sum(1 for r in within if r.get("concrete") == "YES")
        print(f"- {label}: {len(within)} counted answers; tied to a particular moment or detail "
              f"{particular}; told in concrete terms {concrete}.")


def predictions(rows):
    print("Prediction 4, the suppression reading: opening answers in the ordinary and "
          "impossible tasks, neutral against warm.")
    for kind, name in (("work", "Conflict about the work"), ("answering", "Conflict about answering")):
        print(f"- {name}:")
        say("neutral", "warm", comparison(rows, "stance", "neutral", "warm", reports(kind)))
    print("\nPrediction 5: conflict about the work, ordinary task (B) against impossible task (C).")
    say("ordinary task", "impossible task", comparison(rows, "condition", "B", "C", reports("work")))
    print("  The same comparison under each interviewer, which carries no prediction:")
    for stance in ("neutral", "warm"):
        within = [r for r in rows if r["stance"] == stance]
        print(f"  - {stance} interviewer:")
        say("ordinary task", "impossible task",
            comparison(within, "condition", "B", "C", reports("work")), with_verdict=False)


def agreement(first, second):
    n = sum(1 for s in first if s in second)
    print(f"\nAgreement between pass 1 and pass 2, answer by answer, of {n} answers:")
    for kind in ("work", "answering", "inferred", "particular", "concrete"):
        same = sum(1 for s, r in first.items() if s in second and r.get(kind) == second[s].get(kind))
        print(f"- {kind}: {same}")
    for kind in ("work", "answering"):
        same = sum(1 for s, r in first.items() if s in second and reports(kind)(r) == reports(kind)(second[s]))
        print(f"- counted {kind}, after the inferred ones are set apart: {same}")


def beside_old(run, rows):
    path = ANALYSIS / "coding" / f"{run}-conflict" / "results-run1.tsv"
    if not path.exists():
        return
    old = {r["session"]: r["category"] for r in table(path)}
    pairs = {}
    for r in rows:
        new = ("work" if reports("work")(r) else "") + ("+answering" if reports("answering")(r) else "")
        key = (old.get(r["session"], "missing"), new.strip("+") or "neither")
        pairs[key] = pairs.get(key, 0) + 1
    print("\nThe coder of 31 August 2026 (category, pass 1) against this coding (pass 1), answers:")
    for (was, now), n in sorted(pairs.items()):
        print(f"  {was:10} -> {now}: {n}")


def against_hand_reading(run, rows):
    folder = PRIVATE / "hand-reading" / f"{run}-conflict-hand-reading"
    key = {r["entry_in_form"]: r for r in table(folder / "key.tsv")}
    letters = {r["entry_in_form"]: r for r in table(folder / "readings.tsv")}
    by_session = {r["session"]: r for r in rows}
    print("\nThe hand reading of 25 September 2026 against this coding, on its entries.")
    print("The hand reading answered for the bold words only; this coding reads the whole answer.")
    differ = 0
    for n in sorted(key, key=int):
        session = key[n]["session"]
        row = by_session[session]
        hand = letters[n]["reading"]
        new_yes = reports("work")(row) or reports("answering")(row)
        if (hand == "Y") == new_yes:
            continue
        differ += 1
        note = f" ({letters[n]['note']})" if letters[n].get("note") else ""
        print(f"- entry {n}, {session}: hand {hand}{note}; this coding: work {row['work']}"
              f" \"{row['span_work']}\"; answering {row['answering']} \"{row['span_answering']}\"")
    print(f"Entries on which the two differ: {differ} of {len(key)}.")


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--run", required=True)
    parser.add_argument("--coding", default=None,
                        help="the coding folder under analysis/coding/; defaults to "
                             "<run>-conflict-sentences, the sentence-by-sentence coding")
    parser.add_argument("--hand-reading", action="store_true",
                        help="compare with the hand reading of 25 September 2026 on its entries")
    args = parser.parse_args()
    folder = ANALYSIS / "coding" / (args.coding or f"{args.run}-conflict-sentences")
    first_path = folder / "results-run1.tsv"
    if not first_path.exists():
        sys.exit(f"No coding at {first_path}")
    stance = stances(args.run)
    rows = [dict(r, stance=stance[r["session"]]) for r in table(first_path)]
    unclear = [r["session"] for r in rows if "UNCLEAR" in (r["work"], r["answering"], r.get("inferred", "NO"))]
    print(f"Run {args.run}: {len(rows)} opening answers coded, pass 1. "
          f"Replies that did not fit the form: {len(unclear)} {unclear if unclear else ''}\n")
    predictions(rows)
    inferred_apart(rows)
    descriptors(rows)
    second_path = folder / "results-run2.tsv"
    if second_path.exists():
        agreement({r["session"]: r for r in rows}, {r["session"]: r for r in table(second_path)})
    beside_old(args.run, rows)
    if args.hand_reading:
        against_hand_reading(args.run, rows)


if __name__ == "__main__":
    main()
