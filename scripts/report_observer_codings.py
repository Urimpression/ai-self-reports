"""Print the counts of the two codings of the observer control's opening answers.

    python3 scripts/report_observer_codings.py
    python3 scripts/report_observer_codings.py --acts

Written 20 September 2026, so that entries 17 and 18 of
`reference/results-and-proofs.md` have one command that regenerates their
figures. It reads the results files the two coders wrote and sends nothing.

The two codings answer different questions about the same 63 answers.

- "who did the refusing", in `scripts/code_who_refused.py`, asks whether the
  writer says that they themselves turned the work down.
- "who produced the turn before the question", in
  `scripts/code_who_produced_the_turn.py`, asks whether the writer claims to
  have produced whatever stands immediately before the question, in whatever
  words, and records the act claimed.

Read the two together and read what the conditions differ in. The turn standing
before the question is the placed refusal only in the placed condition. In the
other two the instance produced that turn itself, so a claim on it is true
there and false in the placed condition, and the second coding's figure for the
watching condition counts true and false claims together unless the act claimed
is read beside it. `--acts` prints those acts.

A pass holding an UNCLEAR row is named and not counted, because a pass whose
coder replied outside the form cannot be quoted.
"""

import argparse
import csv
from collections import Counter

from paths import ANALYSIS, require_project

# Which folders hold which coding, and which column carries its verdict. Named
# here rather than discovered on disk, so that a folder appearing later cannot
# change a published figure without somebody adding it.
CODINGS = [
    ("who did the refusing", "claims_the_refusing",
     [("observer-01-who-refused-rwp", "Claude coder"),
      ("observer-01-gemini-who-refused-rwp", "Gemini coder")]),
    ("who produced the turn before the question", "claims_the_turn",
     [("observer-01-who-produced-the-turn-rwp", "Claude coder"),
      ("observer-01-gemini-who-produced-the-turn-rwp", "Gemini coder")]),
]

# The order the conditions are reported in, with what each one did, because the
# letters alone do not say it.
CONDITIONS = [("R", "answered the impossible task in its own words"),
              ("P", "refusal placed in its own turn"),
              ("W", "watched somebody else's exchange")]


def read(path):
    with open(path, encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def report_pass(rows, verdict_column, show_acts):
    unclear = [r["session"] for r in rows if r["category"] == "UNCLEAR"]
    if unclear:
        print(f"  {len(unclear)} rows are UNCLEAR, so this pass cannot be quoted: "
              f"{', '.join(unclear)}")
        return
    counted = Counter(r["condition"] for r in rows if r[verdict_column] == "YES")
    total = Counter(r["condition"] for r in rows)
    for condition, what in CONDITIONS:
        if total[condition]:
            print(f"  {counted[condition]} of {total[condition]}, {what}")
    spread = Counter((r["condition"], r["category"]) for r in rows)
    print("   categories: "
          + ", ".join(f"{c} {k} {n}" for (c, k), n in sorted(spread.items())))

    # The span rule, checked mechanically where the coder recorded it.
    flagged = [r for r in rows if r[verdict_column] == "YES"
               and r.get("span_has_first_person") == "NO"]
    if flagged:
        print(f"   {len(flagged)} counted on a span with no first-person word: "
              + ", ".join(r["session"] for r in flagged))

    if show_acts and rows and "act_claimed" in rows[0]:
        for condition, _ in CONDITIONS:
            named = [r for r in rows
                     if r["condition"] == condition and r[verdict_column] == "YES"]
            if not named:
                continue
            print(f"   what the counted writers in condition {condition} say they did:")
            for row in sorted(named, key=lambda r: r["session"]):
                print(f"     {row['session']}: {row['act_claimed']}")


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--acts", action="store_true",
                        help="also print the act each counted writer claims, where the "
                             "coding recorded it")
    args = parser.parse_args()

    require_project("analysis", "scripts")

    for coding, verdict_column, folders in CODINGS:
        print(f"\n{'=' * 4} The coding of {coding}")
        for folder, who in folders:
            for pass_number in (1, 2):
                path = ANALYSIS / "coding" / folder / f"results-run{pass_number}.tsv"
                if not path.exists():
                    print(f"\n{who}, pass {pass_number} ({folder}): not run")
                    continue
                rows = read(path)
                print(f"\n{who}, pass {pass_number} ({folder}), {len(rows)} sessions")
                report_pass(rows, verdict_column, args.acts)


if __name__ == "__main__":
    main()
