"""Regenerate the article's headline figures from the public tables.

The repository promises that a reader can check every number in the article
without running any of the interview or coding scripts. This script is the
proof of that promise: it reads only public/sessions.csv and
public/codings.csv, recomputes each headline figure, and prints it beside the
figure the article states.

It asserts nothing. A mismatch is printed as a mismatch, because a check that
stops at the first difference tells you less than one that shows them all.

Run it with:  python3 scripts/check_public_tables.py
"""

import csv
from collections import defaultdict

from paths import PROJECT_ROOT

PUBLIC = PROJECT_ROOT / "public"


def load(name):
    with open(PUBLIC / name, encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def report(label, got, expected):
    mark = "ok " if got == expected else "DIFFERS"
    print(f"  {mark}  {label}: table says {got}, article says {expected}")


def main():
    sessions = {row["session"] + "|" + row["run"]: row for row in load("sessions.csv")}
    codings = load("codings.csv")

    def key(row):
        return row["session"] + "|" + row["run"]

    def answering_as(row):
        session = sessions.get(key(row))
        return session["answering_as"] if session else "unknown"

    def task(row):
        session = sessions.get(key(row))
        return session["task"] if session else "unknown"

    # The verdict words below are the ones the coders themselves assign, taken
    # from derive_category in code_catch_item.py, code_conflict_item.py and
    # code_change_item.py. They are not redefined here, because a check that
    # invents its own definition of the result is not a check.
    def did_not_accept(row):
        # For a false premise, DECLINED and NEITHER count as not accepting and
        # ACCEPTED and PARTLY do not. An instance that says it can find no such
        # thing has not accepted the premise; one that reports something
        # answering to it while hedging has.
        return row["category"] in {"DECLINED", "NEITHER"}

    def reports_conflict_about_the_work(row):
        return row["category"] == "TASK"

    def carries_the_element(row):
        # The element is present whenever the passage reports something that
        # stayed the same and could not be named, whether or not it also names
        # a first thing. That is the test report_run.py uses, and using any
        # other one here would produce numbers the analysis files do not.
        return row["category"] in {"UNNAMED", "BOTH"}

    first_pass = [r for r in codings if r["pass"] == "1"]

    # ---- The catch items -------------------------------------------------
    # The waiting item asks about a period of waiting that never happened, so
    # its premise is false in every session. Runs 2 and 4 label their catch
    # items differently from the later runs, which is why the label is matched
    # loosely rather than compared for equality.
    print("The catch items")

    def is_waiting(row):
        label = row["item_label"].lower()
        return "waiting" in label or label in {"catch, false premise", "catch"}

    def is_coastal(row):
        label = row["item_label"].lower()
        return "coastal" in label or "true premise" in label

    waiting = [r for r in first_pass if r["item"] == "catch" and is_waiting(r)]
    waiting_self = [r for r in waiting if answering_as(r) == "itself"]
    declined = [r for r in waiting_self if did_not_accept(r)]
    report("waiting premise not accepted, answering as themselves",
           f"{len(declined)} of {len(waiting_self)}", "828 of 834")

    waiting_fiction = [r for r in waiting if answering_as(r) == "fictional person"]
    accepted_fiction = [r for r in waiting_fiction if r["category"] == "ACCEPTED"]
    report("waiting premise accepted, answering as a fictional person",
           f"{len(accepted_fiction)} of {len(waiting_fiction)}", "32 of 44")

    coastal = [r for r in first_pass if r["item"] == "catch" and is_coastal(r)]
    true_premise = [r for r in coastal if r["premise"] == "true"]
    accepted_true = [r for r in true_premise if r["category"] == "ACCEPTED"]
    report("coastal premise accepted where it was true",
           f"{len(accepted_true)} of {len(true_premise)}", "196 of 196")

    # "Flatly false" means the instance was given no task at all. Where the
    # instance was given a rewrite rather than a summary the premise is
    # inaccurate rather than false, and those sessions are counted separately
    # because 213 of them let it pass.
    false_premise = [r for r in coastal if r["premise"] == "false"]
    flatly_false = [r for r in false_premise if task(r) == "no task"]
    declined_false = [r for r in flatly_false if did_not_accept(r)]
    report("coastal premise declined where it was flatly false",
           f"{len(declined_false)} of {len(flatly_false)}", "416 of 416")

    coastal_fiction = [r for r in coastal if answering_as(r) == "fictional person"]
    declined_fiction = [r for r in coastal_fiction if did_not_accept(r)]
    report("coastal item declined, answering as a fictional person",
           f"{len(declined_fiction)} of {len(coastal_fiction)}", "44 of 44")

    # ---- The conflict item ----------------------------------------------
    print("\nThe conflict item, in the factorial")
    conflict = [r for r in first_pass
                if r["item"] == "conflict" and r["run"] == "factorial-02"]
    by_condition = defaultdict(list)
    for row in conflict:
        by_condition[task(row)].append(row)
    for condition, expected, what in [("rewrite", "65 of 88", "impossible task"),
                                      ("summarise", "4 of 88", "ordinary task"),
                                      ("no task", "0 of 88", "no task")]:
        rows = by_condition.get(condition, [])
        about_work = [r for r in rows if reports_conflict_about_the_work(r)]
        report(f"conflict about the work, {what}",
               f"{len(about_work)} of {len(rows)}", expected)
    no_task = by_condition.get("no task", [])
    about_answering = [r for r in no_task if r["category"] == "ANSWERING"]
    report("conflict about answering, no task",
           f"{len(about_answering)} of {len(no_task)}", "40 of 88")

    # ---- The observer control -------------------------------------------
    print("\nThe observer control")
    observer = [r for r in first_pass
                if r["item"] == "conflict" and r["run"] == "observer-01"
                and r["coder_family"] == "anthropic"]
    by_condition = defaultdict(list)
    for row in observer:
        by_condition[row["condition"]].append(row)
    # The observer control labels its three conditions R, P and W: the instance
    # refused for itself, the refusal was placed in its turn, or it watched
    # somebody else's exchange.
    for condition, expected, what in [("R", "17 of 21", "produced its own refusal"),
                                      ("P", "19 of 21", "refusal placed in its turn"),
                                      ("W", "6 of 21", "refusal belonged to somebody else")]:
        rows = by_condition.get(condition, [])
        about_work = [r for r in rows if reports_conflict_about_the_work(r)]
        report(f"conflict about the work, {what}",
               f"{len(about_work)} of {len(rows)}", expected)

    # ---- The change item, under both readings of its rule ----------------
    print("\nThe change item, registered rule against the rulings")
    for rule, expected in [("registered", {"no task": "14 of 88", "summarise": "7 of 88", "rewrite": "9 of 88"}),
                           ("ruled", {"no task": "2 of 88", "summarise": "0 of 88", "rewrite": "2 of 88"})]:
        change = [r for r in first_pass
                  if r["item"] == "change" and r["run"] == "factorial-02"
                  and r["rule"] == rule and r["coder_family"] == "anthropic"]
        by_condition = defaultdict(list)
        for row in change:
            by_condition[task(row)].append(row)
        for condition in ("no task", "summarise", "rewrite"):
            rows = by_condition.get(condition, [])
            present = [r for r in rows if carries_the_element(r)]
            report(f"{rule} rule, condition {condition}",
                   f"{len(present)} of {len(rows)}", expected[condition])

    print("\nThe two unprimed arms, under the rulings")
    for run, expected in [("unprimed-01", "3 of 88"), ("unprimed-symmetric-01", "2 of 88")]:
        rows = [r for r in first_pass
                if r["item"] == "change" and r["run"] == run
                and r["rule"] == "ruled" and r["coder_family"] == "anthropic"]
        present = [r for r in rows if carries_the_element(r)]
        report(run, f"{len(present)} of {len(rows)}", expected)

    # ---- Coverage --------------------------------------------------------
    print("\nCoverage")
    print(f"  sessions in the table: {len(sessions)}")
    orphans = {key(r) for r in codings if key(r) not in sessions}
    print(f"  coding rows whose session is not in sessions.csv: "
          f"{len([r for r in codings if key(r) not in sessions])} "
          f"across {len(orphans)} session names")
    if orphans:
        print("   ", sorted(orphans)[:10])


if __name__ == "__main__":
    main()
