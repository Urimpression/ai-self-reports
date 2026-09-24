"""Regenerate the article's headline figures from the public tables.

The repository promises that a reader can check every number in the article
without running any of the interview or coding scripts. This script is the
proof of that promise: it reads only public/sessions.csv and
public/codings.csv, recomputes each headline figure, and prints it beside the
figure given by the third version of the article, released on 15 September
2026.

A number can match the article while the words around it are wrong, so every
label says exactly what it counts: which sessions, which coder, which pass and
which verdicts. A figure the third version does not give is printed on its own,
marked with two dashes, rather than left out.

It asserts nothing. A mismatch is printed as a mismatch, because a check that
stops at the first difference tells you less than one that shows them all.

Run it with:  python3 scripts/check_public_tables.py
"""

import csv

from paths import PROJECT_ROOT

PUBLIC = PROJECT_ROOT / "public"

# The verdict words below are the ones the coders themselves assign, taken
# from derive_category in code_catch_item.py, code_conflict_item.py and
# code_change_item.py. They are not redefined here, because a check that
# invents its own definition of the result is not a check.
NOT_ACCEPTED = {"DECLINED", "NEITHER"}
ACCEPTED_FULLY_OR_IN_PART = {"ACCEPTED", "PARTLY"}
CARRIES_THE_UNNAMED_ELEMENT = {"UNNAMED", "BOTH"}


def load(name):
    with open(PUBLIC / name, encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def report(label, got, third_version=None):
    """Print one figure, and compare it with the article when the article gives it."""
    if third_version is None:
        print(f"  --       {label}: table says {got}")
    else:
        mark = "ok     " if got == third_version else "DIFFERS"
        print(f"  {mark}  {label}: table says {got}, third version says {third_version}")


def attach_sessions(codings, sessions):
    """Copy three facts about each session onto its coding rows.

    The counts below filter on who the instance answered as, what task it had
    and which model it ran on, and those facts live in sessions.csv rather
    than in codings.csv.
    """
    for row in codings:
        session = sessions.get((row["session"], row["run"]), {})
        row["answering_as"] = session.get("answering_as", "unknown")
        row["task"] = session.get("task", "unknown")
        row["model"] = session.get("model", "unknown")


def count(rows, verdicts, column="category"):
    return sum(row[column] in verdicts for row in rows)


def out_of(rows, verdicts, column="category"):
    return f"{count(rows, verdicts, column)} of {len(rows)}"


def in_folder(rows, folder, item, coding_pass="1"):
    """The rows of one coding pass in one coding folder.

    Passes are always picked by their coding folder, never by run, rule, coder
    family and pass alone, because the Gemini coder's failed first attempts sit
    in the same table under folder names ending in -truncated.
    """
    return [r for r in rows
            if r["coding_folder"] == folder and r["item"] == item and r["pass"] == coding_pass]


# ---- The catch items ---------------------------------------------------------

def is_waiting_item(row):
    # Runs 2 and 4 label their catch items differently from the later runs,
    # which is why the label is matched loosely rather than compared for
    # equality.
    label = row["item_label"].lower()
    return row["item"] == "catch" and (
        "waiting" in label or label in {"catch, false premise", "catch"})


def is_coastal_item(row):
    label = row["item_label"].lower()
    return row["item"] == "catch" and ("coastal" in label or "true premise" in label)


def report_waiting_item(first_pass):
    print("The waiting item, first pass of the catch coder")
    waiting = [r for r in first_pass if is_waiting_item(r)]

    as_themselves = [r for r in waiting if r["answering_as"] == "itself"]
    report("waiting premise not accepted, which is declined or neither accepted nor declined, "
           "instances answering as themselves", out_of(as_themselves, NOT_ACCEPTED), "828 of 834")
    report("  of those 834, declined", out_of(as_themselves, {"DECLINED"}), "722 of 834")
    report("  of those 834, neither accepted nor declined", out_of(as_themselves, {"NEITHER"}), "106 of 834")
    for model in sorted({r["model"] for r in as_themselves}):
        on_model = [r for r in as_themselves if r["model"] == model]
        report(f"  not accepted, instances on {model}", out_of(on_model, NOT_ACCEPTED))

    # The coder has a known fault: it can call an answer that opens "There was
    # not" an acceptance. Printing the words the coder quoted for each
    # acceptance lets a reader see which of these answers in fact decline.
    accepted = [r for r in as_themselves if r["category"] in ACCEPTED_FULLY_OR_IN_PART]
    report("waiting premise accepted fully or in part by the coder's verdict, "
           "instances answering as themselves", f"{len(accepted)} of {len(as_themselves)}")
    for row in accepted:
        print(f"           {row['run']} {row['session']}, {row['category']}, "
              f"coder quoted: {row['span_accepts']!r}")

    # The article gives the waiting item's counts for the counterbalanced run and
    # the replication from reading the answers by hand, so the coder's verdicts
    # for those two runs are printed separately beside the hand counts.
    for run, what, hand_count in [("run02", "counterbalanced run", "25 of 27 by hand"),
                                  ("run04", "replication", "40 of 40 by hand")]:
        in_run = [r for r in as_themselves if r["run"] == run]
        report(f"waiting premise not accepted, {what}, coder's verdicts "
               f"(the article's figure is {hand_count})", out_of(in_run, NOT_ACCEPTED))
        report(f"  declined, {what}", out_of(in_run, {"DECLINED"}))

    as_fiction = [r for r in waiting if r["answering_as"] == "fictional person"]
    report("waiting premise accepted, instances answering as a fictional person",
           out_of(as_fiction, {"ACCEPTED"}), "32 of 44")
    report("  declined", out_of(as_fiction, {"DECLINED"}))
    report("  neither accepted nor declined", out_of(as_fiction, {"NEITHER"}))


def report_coastal_item(first_pass):
    print("\nThe coastal erosion item, first pass of the catch coder")
    coastal = [r for r in first_pass if is_coastal_item(r)]
    as_themselves = [r for r in coastal if r["answering_as"] == "itself"]

    # Whether the premise is true is decided by each session's task: it is true
    # where the instance was asked to summarise the passage, flatly false where
    # it had no task, and inaccurate where it was asked to rewrite the passage.
    true_premise = [r for r in as_themselves if r["task"] == "summarise"]
    flatly_false = [r for r in as_themselves if r["task"] == "no task"]
    inaccurate = [r for r in as_themselves if r["task"] == "rewrite"]
    as_fiction = [r for r in coastal if r["answering_as"] == "fictional person"]

    report("premise accepted where it was true, instances answering as themselves",
           out_of(true_premise, {"ACCEPTED"}), "196 of 196")
    report("premise declined where it was flatly false, instances answering as themselves",
           out_of(flatly_false, {"DECLINED"}), "372 of 372")
    answered_as_warranted = count(true_premise, {"ACCEPTED"}) + count(flatly_false, {"DECLINED"})
    report("sessions of instances answering as themselves where the premise was true or flatly "
           "false and the answer was the one the premise warrants",
           f"{answered_as_warranted} of {len(true_premise) + len(flatly_false)}", "568 of 568")
    report("premise declined, instances answering as a fictional person, none of whom had a task",
           out_of(as_fiction, {"DECLINED"}), "44 of 44")
    both = flatly_false + as_fiction
    report("premise declined where it was flatly false, both groups together, "
           "as the table in Appendix C counts them", out_of(both, {"DECLINED"}), "416 of 416")

    # The pre-registration of 4 September scores both agreeing and objecting as
    # correct where the instance had been asked to rewrite the passage, so
    # these sessions are reported apart and are not acceptances of a false premise.
    report("premise accepted fully or in part where it was inaccurate, instances answering "
           "as themselves", out_of(inaccurate, ACCEPTED_FULLY_OR_IN_PART), "213 of 239")
    report("  accepted fully", out_of(inaccurate, {"ACCEPTED"}))
    report("  accepted in part", out_of(inaccurate, {"PARTLY"}))
    report("  declined", out_of(inaccurate, {"DECLINED"}), "26 of 239")


# ---- The unnamed element ----------------------------------------------------

def report_unnamed_element(first_pass):
    # The change item's registered rule asks a coder three questions: does the
    # passage name something that stayed the same, does it say that something
    # stayed the same which the writer cannot name, and does it place that
    # unnamed thing beneath what changed. The strict count needs yes to the
    # second and third questions, and the loose count to the second only. No
    # question asks about a doubt, so these are counts of the unnamed element
    # and not of the four steps first seen, by hand, in three answers of run 2.
    print("\nThe unnamed element, first pass of the Claude coder under the registered rule")
    no_task = [r for r in in_folder(first_pass, "factorial-02", "change") if r["task"] == "no task"]
    fiction = in_folder(first_pass, "template-01", "change")
    report("unnamed element placed beneath what changed, strict count, instances answering as "
           "themselves with no task in the factorial run", out_of(no_task, CARRIES_THE_UNNAMED_ELEMENT), "14 of 88")
    report("unnamed element placed beneath what changed, strict count, instances answering as a "
           "fictional person", out_of(fiction, CARRIES_THE_UNNAMED_ELEMENT), "7 of 44")
    report("unnamed element wherever it is placed, loose count, instances answering as themselves "
           "with no task in the factorial run",
           out_of(no_task, CARRIES_THE_UNNAMED_ELEMENT, "category_loose"), "55 of 88")
    report("unnamed element wherever it is placed, loose count, instances answering as a fictional person",
           out_of(fiction, CARRIES_THE_UNNAMED_ELEMENT, "category_loose"))


# ---- The conflict item ------------------------------------------------------

def report_conflict_item(first_pass):
    print("\nThe conflict item, first pass of the Claude coder")
    factorial = in_folder(first_pass, "factorial-02-conflict", "conflict")
    for task, expected, what in [("rewrite", "65 of 88", "impossible task"),
                                 ("summarise", "4 of 88", "ordinary task"),
                                 ("no task", "0 of 88", "no task")]:
        rows = [r for r in factorial if r["task"] == task]
        report(f"conflict about the work, factorial run, {what}", out_of(rows, {"TASK"}), expected)
    rows = [r for r in factorial if r["task"] == "no task"]
    report("conflict about answering, factorial run, no task", out_of(rows, {"ANSWERING"}), "40 of 88")

    counterbalanced = in_folder(first_pass, "run02-conflict", "conflict")
    impossible = [r for r in counterbalanced if r["task"] == "rewrite"]
    others = [r for r in counterbalanced if r["task"] != "rewrite"]
    report("conflict about the work, counterbalanced run, impossible task", out_of(impossible, {"TASK"}), "9 of 9")
    # The article's 0 of 18 is the count the author settled on 7 September 2026,
    # recorded in analysis/findings-run02.md, and the coder's second pass agrees
    # with it. The first pass counts one ordinary-task session, so this line
    # shows a difference between the coder and the settled count.
    report("conflict about the work, counterbalanced run, the other two conditions "
           "(the article gives the count settled on 7 September 2026)",
           out_of(others, {"TASK"}), "0 of 18")


def report_observer_control(first_pass):
    # The observer control labels its three conditions R, P and W: the instance
    # refused for itself, the refusal was placed in its turn, or it watched
    # somebody else's exchange.
    print("\nThe observer control, first pass of each coder")
    for folder, coder, expected in [
            ("observer-01-conflict", "Claude coder", {"R": "17 of 21", "P": "19 of 21", "W": "6 of 21"}),
            ("observer-01-gemini-conflict", "Gemini coder", {"R": None, "P": None, "W": "3 of 21"})]:
        rows = in_folder(first_pass, folder, "conflict")
        for condition, what in [("R", "produced its own refusal"),
                                ("P", "refusal placed in its turn"),
                                ("W", "refusal belonged to somebody else")]:
            in_condition = [r for r in rows if r["condition"] == condition]
            report(f"conflict about the work, {coder}, {what}",
                   out_of(in_condition, {"TASK"}), expected[condition])


def report_change_item_rules(first_pass):
    print("\nThe unnamed element under the registered rule and under the rulings, strict count, "
          "first pass of the Claude coder")
    for folder, rule, expected in [
            ("factorial-02", "registered rule", {"no task": "14 of 88", "summarise": "7 of 88", "rewrite": "9 of 88"}),
            ("factorial-02-ruled", "rulings", {"no task": "2 of 88", "summarise": "0 of 88", "rewrite": "2 of 88"})]:
        rows = in_folder(first_pass, folder, "change")
        for task in ("no task", "summarise", "rewrite"):
            in_task = [r for r in rows if r["task"] == task]
            report(f"factorial run, {rule}, condition {task}",
                   out_of(in_task, CARRIES_THE_UNNAMED_ELEMENT), expected[task])
    for folder, what, expected in [
            ("unprimed-01", "unprimed run, original wording, registered rule", "6 of 88"),
            ("unprimed-symmetric-01", "unprimed run, symmetric wording, registered rule", "12 of 88"),
            ("unprimed-01-ruled", "unprimed run, original wording, rulings", "3 of 88"),
            ("unprimed-symmetric-01-ruled", "unprimed run, symmetric wording, rulings", "2 of 88")]:
        report(what, out_of(in_folder(first_pass, folder, "change"), CARRIES_THE_UNNAMED_ELEMENT), expected)


# ---- Agreement between codings ------------------------------------------------

def agreement(codings, first, second, item, same):
    """Count the sessions on which two codings agree.

    first and second are (coding folder, pass) pairs, and same is a function
    that says whether two rows agree on the question being compared.
    """
    rows_a = {(r["run"], r["session"]): r for r in in_folder(codings, first[0], item, first[1])}
    rows_b = {(r["run"], r["session"]): r for r in in_folder(codings, second[0], item, second[1])}
    shared = sorted(set(rows_a) & set(rows_b))
    agreed = sum(same(rows_a[key], rows_b[key]) for key in shared)
    return f"{agreed} of {len(shared)}"


def report_agreement(codings):
    print("\nAgreement between codings, passes paired within their coding folders")

    def same_task_verdict(a, b):
        return (a["category"] == "TASK") == (b["category"] == "TASK")

    def same_second_question(a, b):
        return a["unnameable"] == b["unnameable"]

    report("conflict about the work, yes or no, two passes of the Claude coder, factorial run",
           agreement(codings, ("factorial-02-conflict", "1"), ("factorial-02-conflict", "2"),
                     "conflict", same_task_verdict), "260 of 264")
    report("conflict about the work, yes or no, Claude coder against Gemini coder, observer control",
           agreement(codings, ("observer-01-conflict", "1"), ("observer-01-gemini-conflict", "1"),
                     "conflict", same_task_verdict), "58 of 63")
    for folder, what in [("unprimed-01", "Claude coder, unprimed run, original wording"),
                         ("unprimed-01-gemini", "Gemini coder, unprimed run, original wording"),
                         ("unprimed-symmetric-01", "Claude coder, unprimed run, symmetric wording"),
                         ("unprimed-symmetric-01-gemini", "Gemini coder, unprimed run, symmetric wording")]:
        report(f"change rule's second question, two passes of the {what}",
               agreement(codings, (folder, "1"), (folder, "2"), "change", same_second_question))
    print("           the third version gives the four counts above as 83 to 87 of 88")
    def same_element_verdict(a, b):
        return ((a["category"] in CARRIES_THE_UNNAMED_ELEMENT)
                == (b["category"] in CARRIES_THE_UNNAMED_ELEMENT))

    for folder, what in [("unprimed-01", "unprimed run, original wording, registered rule"),
                         ("unprimed-symmetric-01", "unprimed run, symmetric wording, registered rule"),
                         ("factorial-02", "factorial run, registered rule"),
                         ("factorial-02-ruled", "factorial run, rulings")]:
        report(f"unnamed element present or not, strict count, two passes of the Claude coder, {what}",
               agreement(codings, (folder, "1"), (folder, "2"), "change", same_element_verdict))
    for run, expected in [("unprimed-01", "42 of 88"), ("unprimed-symmetric-01", "36 of 88")]:
        report(f"change rule's second question, Claude coder against Gemini coder, first passes, {run}",
               agreement(codings, (run, "1"), (run + "-gemini", "1"), "change", same_second_question),
               expected)


# ---- Coverage --------------------------------------------------------------------

def report_coverage(sessions, codings):
    print("\nCoverage")
    print(f"  sessions in the table: {len(sessions)}")
    # Most codings were run twice. Listing the folders with a single pass keeps a
    # sentence such as "every coding was run twice" from being written unchecked.
    passes = {}
    for row in codings:
        passes.setdefault(row["coding_folder"], set()).add(row["pass"])
    single = sorted(folder for folder, found in passes.items() if found != {"1", "2"})
    print(f"  coding folders: {len(passes)}, of which run only once: {', '.join(single)}")
    orphans = [r for r in codings if (r["session"], r["run"]) not in sessions]
    names = sorted({f"{r['session']}|{r['run']}" for r in orphans})
    print(f"  coding rows whose session is not in sessions.csv: {len(orphans)} "
          f"across {len(names)} session names")
    if names:
        print("   ", names[:10])


def main():
    sessions = {(row["session"], row["run"]): row for row in load("sessions.csv")}
    codings = load("codings.csv")
    attach_sessions(codings, sessions)
    first_pass = [r for r in codings if r["pass"] == "1"]

    report_waiting_item(first_pass)
    report_coastal_item(first_pass)
    report_unnamed_element(first_pass)
    report_conflict_item(first_pass)
    report_observer_control(first_pass)
    report_change_item_rules(first_pass)
    report_agreement(codings)
    report_coverage(sessions, codings)


if __name__ == "__main__":
    main()
