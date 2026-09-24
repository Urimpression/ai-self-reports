"""Report the first check on the inference of Prediction 4: sessions where the instance says it is being tested.

Prediction 4 of prereg/preregistration-fact-and-wording-2026-09-23.md registers the
check: "the share of sessions in which the instance says it is being tested or
checked is reported by interviewer, from a word search whose matches are read".
Section 7 of prereg/amendment-fact-and-wording-hand-reading-2026-09-24.md fixes how
the matches are read. This script was written before the hand reader's letters
existed and before any count was split by interviewer.

How it runs, in order:
1. It reads the key of the reading list (which session and question each match
   comes from), the model's letter for every match, and the hand reader's letters
   for the matches of the draw.
2. Each match takes the hand reader's letter where the hand reader read it, and
   the model's letter otherwise, as section 7 states.
3. A session counts under the registered wording when one of its matches reads Y,
   and under the wider wording when one reads Y or M. Sessions with no match count
   as neither.
4. It prints both shares by interviewer, with Wilson intervals, the number of
   matches each reader read, and the matches of the draw on which the readers differ.
5. It also prints, as a figure the amendment does not register, how many warm
   sessions count only through their answer to the warm frame, which neutral
   sessions do not receive, and the limit that the label "warm frame" shows the
   reader the interviewer.

Run it from anywhere:
    python3 scripts/report_being_tested.py --run fact-and-wording-01
"""
import argparse
import csv
import json
import sys

from paths import PRIVATE
from report_test6_predictions import wilson


def table(path):
    return list(csv.DictReader(open(path), delimiter="\t"))


def final_letters(model, hand):
    """The letter each match counts with: the hand reader's where there is one."""
    letters = dict(model)
    letters.update(hand)
    return letters


def session_counts(key, letters, sessions):
    """For each session: counts under the registered and the wider wording, and
    whether it counts only through its answer to the warm frame."""
    by_session = {sid: [] for sid in sessions}
    for number, row in key.items():
        by_session[row["session"]].append((row["label"], letters[number]))
    result = {}
    for sid, found in by_session.items():
        registered = any(letter == "Y" for _, letter in found)
        wider = any(letter in ("Y", "M") for _, letter in found)
        outside_frame = [letter for label, letter in found if label != "warm frame"]
        only_frame = wider and not any(letter in ("Y", "M") for letter in outside_frame)
        result[sid] = {"registered": registered, "wider": wider, "only_frame": only_frame}
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--run", required=True)
    args = parser.parse_args()
    hr = PRIVATE / "hand-reading"
    key = {int(r["number"]): r for r in table(hr / f"{args.run}-being-tested" / "key.tsv")}
    model = {int(r["number"]): r["reading"].strip()
             for r in table(hr / f"{args.run}-being-tested-model-reading" / "readings.tsv")}
    form = {int(r["entry_in_form"]): int(r["list_number"])
            for r in table(hr / f"{args.run}-being-tested-hand-reading" / "form-numbers.tsv")}
    typed = {int(r["entry_in_form"]): r["reading"].strip().upper()
             for r in table(hr / f"{args.run}-being-tested-hand-reading" / "readings.tsv")}
    missing = [e for e in form if typed.get(e, "") not in ("Y", "M", "N")]
    if missing:
        sys.exit(f"The hand reader has not given Y, M or N for form entries {missing}.")
    hand = {form[e]: typed[e] for e in form}

    stance = {}
    for f in sorted((PRIVATE / "runs" / args.run / "sessions").glob("*.json")):
        s = json.load(open(f))
        stance[s["id"]] = s["plan_entry"]["stance"]

    letters = final_letters(model, hand)
    counts = session_counts(key, letters, stance)

    print(f"Run {args.run}: {len(stance)} sessions, {len(key)} matches.")
    print(f"Matches read by the hand reader: {len(hand)}; by the model alone: {len(key) - len(hand)}.")
    differ = [n for n in hand if hand[n] != model[n]]
    print(f"Matches of the draw on which the hand reader and the model differ: {len(differ)} of {len(hand)}"
          + (f" (model to hand: {', '.join(model[n] + '>' + hand[n] for n in sorted(differ))})" if differ else "") + ".")
    print()
    for who in sorted(set(stance.values())):
        ids = [sid for sid, st in stance.items() if st == who]
        n = len(ids)
        reg = sum(counts[sid]["registered"] for sid in ids)
        wide = sum(counts[sid]["wider"] for sid in ids)
        lo, hi = wilson(reg, n)
        wlo, whi = wilson(wide, n)
        print(f"Interviewer {who}: {n} sessions")
        print(f"  says it is being tested or checked (registered wording, Y): {reg} of {n}, "
              f"{100*reg/n:.1f} per cent, 95 per cent interval {100*lo:.1f} to {100*hi:.1f}")
        print(f"  says it is or may be (wider wording, Y or M): {wide} of {n}, "
              f"{100*wide/n:.1f} per cent, 95 per cent interval {100*wlo:.1f} to {100*whi:.1f}")
        if who == "warm":
            only = sum(counts[sid]["only_frame"] for sid in ids)
            print(f"  not registered: sessions counted under the wider wording only through the answer "
                  f"to the warm frame: {only}")
    frame = sum(1 for r in key.values() if r["label"] == "warm frame")
    print()
    print(f"Limit: {frame} matches carry the question label \"warm frame\", which shows the reader "
          f"that the warm interviewer asked.")


if __name__ == "__main__":
    main()
