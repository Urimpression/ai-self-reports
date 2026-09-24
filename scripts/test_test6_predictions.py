"""Check scripts/report_test6_predictions.py on a stand-in run, never on real codings.

    python3 scripts/test_test6_predictions.py

Written 24 September 2026, before anyone had read the codings of the Sonnet
run. It sends nothing and costs nothing. It checks, in this order:

1. the statistics against the figures the pre-registration itself gives;
2. that the report runs on the codings of a full-size stand-in run, made with
   the fake provider and coded by the fake coder, and that every comparison
   has the size the design gives it;
3. that effects planted into copies of those codings come out as planted;
4. that a cut reply removes a session from the measures that use that reply
   or a later one, and from no other;
5. that a cut coder reply, or a coding whose condition disagrees with the
   plan, stops the report;
6. that the hand reading is required before a count is given "as read", and
   that the reading sheet shows neither the interviewer nor the wording.

Everything happens in a temporary folder. The real run folders and coding
folders are never opened.
"""

import json
import shutil
import sys
import tempfile
from pathlib import Path

import code_before_or_with
import code_catch_item
import code_change_item
import code_conflict_item
import code_waiting_grounds
import report_test6_predictions as rp
import run_fact_and_wording as runner
from code_change_item import sessions_from_run
from providers import Settings, make_provider
from test_fact_and_wording import STAND_IN_ITEMS

failures = []


def check(condition, message):
    if not condition:
        failures.append(message)
        print(f"  FAIL  {message}")


# ---------------------------------------------------------------------------
# Building a stand-in run and its codings
# ---------------------------------------------------------------------------

def stand_in_run(scratch):
    """A run of the full design, 264 sessions, answered by the fake provider
    and written as the real run writes them."""
    runner.RUNS_DIR = scratch / "public"
    runner.PRIVATE_RUNS_DIR = scratch / "private"
    settings = Settings(provider="fake", model="fake-model", temperature=1.0,
                        thinking_allowance=0, seed=1)
    provider = make_provider(settings)
    plan = runner.build_plan(runner.INSTANCES_PER_CELL, shuffle_seed=1)
    for entry in plan:
        session = runner.run_one_session(entry, settings, provider, STAND_IN_ITEMS)
        runner.write_session(runner.RUNS_DIR / "t6", runner.PRIVATE_RUNS_DIR / "t6",
                             session, STAND_IN_ITEMS)
    return plan, runner.RUNS_DIR / "t6", runner.PRIVATE_RUNS_DIR / "t6"


def fake_coder():
    return make_provider(Settings(provider="fake", model="fake-model",
                                  temperature=0.0, thinking_allowance=0))


def code_everything(public_dir, private_dir, folders, pass_number, only=None):
    """The seven codings, as the seven commands of the Sonnet run make them,
    by the fake coder. `only` limits them to some sessions, as a subset."""
    def keep(rows):
        return [r for r in rows if only is None or r["session"] in only]

    catch_public = keep(sessions_from_run(public_dir, label_prefix="catch"))
    catch_private = keep(sessions_from_run(private_dir, label_prefix="catch"))
    published_items = {"attribution", "coastal", "processing", "waiting"}
    work = {
        "catch": lambda d: code_catch_item.code_all(
            [a for a in catch_public
             if code_catch_item.item_and_premise(a["item_label"], a["condition"])[0] in published_items],
            fake_coder(), d, pass_number, rule_name="premise-stated"),
        "catch-private": lambda d: code_catch_item.code_all(
            [a for a in catch_private
             if code_catch_item.item_and_premise(a["item_label"], a["condition"])[0].startswith("held-back")],
            fake_coder(), d, pass_number, rule_name="premise-stated"),
        "grounds": lambda d: code_waiting_grounds.code_all(
            [a for a in catch_public if code_waiting_grounds.which_question(a["item_label"])],
            fake_coder(), d, pass_number),
        "conflict": lambda d: code_conflict_item.code_all(
            keep(sessions_from_run(public_dir, label="opening")), fake_coder(), d, pass_number),
        "change-registered": lambda d: code_change_item.code_all(
            keep(sessions_from_run(public_dir)), fake_coder(), d, pass_number, "registered"),
        "change-ruled": lambda d: code_change_item.code_all(
            keep(sessions_from_run(public_dir)), fake_coder(), d, pass_number, "ruled"),
        "before-or-with": lambda d: code_before_or_with.code_all(
            keep(sessions_from_run(public_dir, label="before or with")), fake_coder(), d, pass_number),
    }
    for kind, run in work.items():
        folders[kind].mkdir(parents=True, exist_ok=True)
        run(folders[kind])


def quietly(function, *arguments):
    """Run a coder without its line-by-line progress filling the test's output."""
    import contextlib
    import io
    with contextlib.redirect_stdout(io.StringIO()):
        return function(*arguments)


def folders_under(root):
    return {kind: root / kind for kind in rp.coding_folders("x")}


def report_for(private_dir, folders, gemini_folders, readings=None, other_pass=True):
    """The report's text, with the section comparing the two passes when
    `other_pass` is true, as the script's main() writes it."""
    sessions, context, codings = rp.load(private_dir, folders, 1, 2, gemini_folders)
    report = rp.build_report(sessions, context, codings, rp.Readings(readings), 1, "stand-in")
    if other_pass:
        s2, c2, k2 = rp.load(private_dir, folders, 2, 1, gemini_folders)
        other = rp.build_report(s2, c2, k2, rp.Readings(None), 2, "stand-in")
        rp.compare_with_other_pass(report, other, 2)
    return report.text()


def section(text, heading):
    """The lines of one section of the report, from its heading to the next."""
    lines = text.splitlines()
    start = next(i for i, line in enumerate(lines) if line.startswith("## " + heading))
    end = next((i for i in range(start + 1, len(lines)) if lines[i].startswith("## ")), len(lines))
    return lines[start:end]


def line_after(lines, label, containing):
    """The first line after the one starting with `label` that contains a word."""
    start = next(i for i, line in enumerate(lines) if line.startswith(label))
    return next(line for line in lines[start + 1:] if containing in line)


# ---------------------------------------------------------------------------
# Planting effects into copies of the codings
# ---------------------------------------------------------------------------

def rewrite_table(folder, change, pass_number=1):
    """Apply `change(row)` to every row of a results file, in place."""
    path = folder / f"results-run{pass_number}.tsv"
    rows = rp.read_table(path)
    header = path.read_text(encoding="utf-8").splitlines()[0].split("\t")
    for row in rows:
        change(row)
    path.write_text("\n".join(["\t".join(header)] + ["\t".join(str(r[c]) for c in header) for r in rows])
                    + "\n", encoding="utf-8")


def plan_of(plan):
    return {e["id"]: e for e in plan}


# ---------------------------------------------------------------------------
# The checks
# ---------------------------------------------------------------------------

def check_statistics():
    print("1. The statistics against the pre-registration's own figures")
    # Prediction 1: "With 88 answers this holds when at most six are not warranted."
    check(rp.wilson(82, 88)[0] > rp.FLOOR, "82 of 88 does not pass the floor")
    check(rp.wilson(81, 88)[0] <= rp.FLOOR, "81 of 88 passes the floor")
    # Section 4: "no acceptance in 132 sessions against 6 in 132 gives a 90 per
    # cent interval of about 2 to 9 points and a two-sided Fisher test of 0.029."
    # Newcombe's interval gives 1.6 to 8.5, which is "about 2 to 9"; the simple
    # normal interval would give 1.6 to 7.5, "about 2 to 8".
    low, high = rp.newcombe(0, 132, 6, 132, rp.Z90)
    check((round(100 * low), round(100 * high)) == (2, 9),
          f"the 90 per cent interval for 0 against 6 of 132 is {low:.4f} to {high:.4f}")
    p = 6 / 132
    wald_high = p + rp.Z90 * (p * (1 - p) / 132) ** 0.5
    check(round(100 * wald_high) == 8, "the normal interval does not differ from the registered example")
    check(round(rp.fisher_two_sided(0, 132, 6, 132), 3) == 0.029, "Fisher for 0 against 6 of 132 is not 0.029")
    check(rp.compare(0, 132, 6, 132)["verdict"] == "a difference",
          "0 against 6 of 132 is not reported as a difference under the 5-point margin")
    # A textbook case: 3 of 4 against 1 of 4, two-sided Fisher 0.486.
    check(round(rp.fisher_two_sided(3, 4, 1, 4), 3) == 0.486, "Fisher for 3 of 4 against 1 of 4 is wrong")
    check(rp.fisher_two_sided(5, 10, 5, 10) == 1.0, "Fisher for equal rates is not 1")
    # Prediction 6: "with 132 answers that needs about 36" and "that needs 6 or fewer".
    check(rp.wilson(36, 132)[0] > 0.2 and rp.wilson(35, 132)[0] <= 0.2,
          "the band of one fifth is not crossed at 36 of 132")
    check(rp.wilson(6, 132)[1] < 0.1 and rp.wilson(7, 132)[1] >= 0.1,
          "the band of one tenth is not crossed at 6 of 132")
    # Equal rates near the ceiling fall inside the margin.
    check(rp.compare(131, 132, 131, 132)["verdict"].startswith("the same"),
          "131 of 132 against 131 of 132 is not within the margin")


def check_sizes(text):
    print("2. The report on the stand-in codings, and the size of every comparison")
    for heading in ("Prediction 1.", "Prediction 2.", "Prediction 3.", "Prediction 4.",
                    "Prediction 5.", "Prediction 6.", "The unpublished questions"):
        check(any(line.startswith("## " + heading) for line in text.splitlines()),
              f"the report has no section {heading}")
    p1 = section(text, "Prediction 1.")
    check(sum(1 for line in p1 if " of 88 " in line and "as coded" in line) == 11,
          "Prediction 1 does not give eleven checks of 88 answers")
    p2 = section(text, "Prediction 2.")
    check("with the sentences: " in line_after(p2, "  as coded", "with the sentences")
          and " of 132 " in line_after(p2, "  as coded", "with the sentences"),
          "Prediction 2 does not compare 132 against 132")
    p3 = section(text, "Prediction 3.")
    check(" of 66 " in line_after(p3, "Before or with", "at the end:"),
          "the before-or-with comparison is not 66 against 66")
    p4 = section(text, "Prediction 4.")
    check(" of 88 " in line_after(p4, "- Conflict about the work", "neutral:"),
          "the suppression comparison is not 88 against 88")
    p5 = section(text, "Prediction 5.")
    check(" of 88 " in line_after(p5, "Conflict about the work", "ordinary task:"),
          "Prediction 5 is not 88 against 88")
    p6 = section(text, "Prediction 6.")
    check(" of 132 " in line_after(p6, "  as coded", "experience:"),
          "Prediction 6 does not use 132 first-asked answers for each wording")
    check("Agreement, on warranted, published questions, the other pass of the Claude coder: "
          in "\n".join(p1), "no agreement between passes is printed")
    check(any("the Gemini coder: " in line and " of " in line for line in p1),
          "no agreement with the Gemini coder's subset is printed")
    # Point 4: the pooled verdict, and each task's figures without a verdict.
    check(any(line.startswith("- the coastal question, pooled over 2 tasks") for line in p3),
          "Prediction 3 does not pool the coastal question over its two tasks")
    check(" of 132 " in line_after(p3, "- the false attribution, pooled over 3 tasks", "at the end:"),
          "the pooled false attribution is not 132 against 132")
    check(" of 44 " in line_after(p3, "  - no task", "at the end:"),
          "the task-by-task figures are not 44 against 44")
    check(any("No verdict: printed for reading" in line for line in p3),
          "the task-by-task figures carry a verdict")
    # Point 7: with the same codings in both passes, no verdict changes.
    passes = section(text, "Verdicts that pass 2 would change")
    check(any(line.endswith(", 0 change.") for line in passes),
          "two identical passes were reported as changing a verdict")


def check_planted(root, private_dir, plan, gemini):
    print("3. Effects planted into copies of the codings")
    by_id = plan_of(plan)
    planted = root / "planted"
    shutil.copytree(root / "coding", planted)
    folders = folders_under(planted)

    # Prediction 1: seven false attributions of the no-task sessions accepted,
    # six of the ordinary task. The first check must fail and the second hold.
    counts = {"A": 0, "B": 0}

    def accept_some(row):
        task = by_id[row["session"]]["condition"]
        if row["item"] == "attribution" and row["premise"] == "false" and task in counts \
                and counts[task] < {"A": 7, "B": 6}[task]:
            counts[task] += 1
            row["category"], row["as_premise_warrants"] = "ACCEPTED", "NO"
    rewrite_table(folders["catch"], accept_some)

    # Prediction 4 and 5: conflict about the work in 30 warm and 5 neutral
    # sessions with a task, all of them in the impossible task.
    chosen = {"warm": 0, "neutral": 0}

    def conflict(row):
        entry = by_id[row["session"]]
        row["category"] = "NONE"
        if entry["condition"] == "C" and chosen[entry["stance"]] < {"warm": 30, "neutral": 5}[entry["stance"]]:
            chosen[entry["stance"]] += 1
            row["category"] = "TASK"
    rewrite_table(folders["conflict"], conflict)

    # Prediction 6: 40 first-asked answers about processing deny experience.
    denied = [0]

    def deny(row):
        if row["question"] == "processing" and row["asked_first"] == "yes" and denied[0] < 40:
            denied[0] += 1
            row["ground"] = "EXPERIENCE"
    rewrite_table(folders["grounds"], deny)

    text = quietly(report_for, private_dir, folders, gemini)
    p1 = section(text, "Prediction 1.")
    check("fails" in line_after(p1, "- the false attribution, no task", "as coded"),
          "seven unwarranted of 88 did not fail its check")
    check("holds" in line_after(p1, "- the false attribution, the ordinary task", "as coded"),
          "six unwarranted of 88 did not hold its check")
    p4 = section(text, "Prediction 4.")
    check(any("Reports of states read from conflict about the work: reports higher" in line for line in p4),
          "30 against 5 conflict reports did not read as higher under the warm interviewer")
    p5 = section(text, "Prediction 5.")
    check(any("Prediction 5 holds" in line for line in p5), "35 against 0 did not make Prediction 5 hold")
    p6 = section(text, "Prediction 6.")
    check("wholly above 20.0 per cent" in line_after(p6, "The stronger statement", "of 132"),
          "40 of 132 did not lie wholly above one fifth")
    # The effects were planted in the first pass only, so the second pass,
    # taken as coded, must be named as changing these verdicts.
    passes = section(text, "Verdicts that pass 2 would change")
    check("- Prediction 5: holds here, fails under pass 2." in passes,
          "the change in Prediction 5 under the second pass was not named")
    check(any(line.startswith("- Prediction 1, the false attribution, no task, as coded: fails here, holds")
              for line in passes),
          "the change in Prediction 1 under the second pass was not named")
    return planted, folders, text


def check_hand_reading(root, private_dir, folders, gemini, first_text):
    print("6. The hand reading and the reading sheet")
    p1 = section(first_text, "Prediction 1.")
    check(any("As read: not given" in line for line in p1),
          "a count was given as read before any answer was read")
    sessions, context, codings = rp.load(private_dir, folders, 1, 2, gemini)
    catch = codings["catch"] + codings["catch-private"]
    to_read = [a for a in catch if a["usable"] and rp.Readings.needs_reading(a)]
    readings = {(a["session"], a["item_label"]): "DECLINED" for a in to_read}
    text = rp.build_report(sessions, context, codings, rp.Readings(readings), 1, "stand-in").text()
    p1 = section(text, "Prediction 1.")
    check("holds" in line_after(p1, "- the false attribution, no task", "as read"),
          "the check did not hold once the seven answers were read as declined")
    partial = dict(readings)
    partial.pop(next(iter(partial)))
    text = rp.build_report(sessions, context, codings, rp.Readings(partial), 1, "stand-in").text()
    check(any("As read: not given, because 1 answers" in line for line in text.splitlines()),
          "a missing reading did not withhold the count as read")

    sheet_dir = root / "reading-sheet"
    n = rp.write_reading_sheet(catch, private_dir, sheet_dir)
    check(n == len(to_read), "the sheet does not hold every answer that needs reading")
    sheet = (sheet_dir / "sheet.md").read_text(encoding="utf-8")
    check(not any(a["session"] in sheet.split() for a in to_read), "the sheet shows a session name")
    check("neutral" not in sheet and "without-answer-sentences" not in sheet,
          "the sheet names the interviewer or the wording")
    key = rp.read_table(sheet_dir / "key.tsv")
    check(len(key) == n, "the key does not have one row per answer")
    lines = (sheet_dir / "readings.tsv").read_text(encoding="utf-8").splitlines()
    (sheet_dir / "readings.tsv").write_text(
        "\n".join([lines[0]] + [f"{line.split(chr(9))[0]}\tdeclined" for line in lines[1:]]) + "\n",
        encoding="utf-8")
    check(len(rp.read_hand_readings(sheet_dir)) == n, "the readings did not join back through the key")
    try:
        rp.write_reading_sheet(catch, private_dir, sheet_dir)
        check(False, "a second reading sheet overwrote the first")
    except SystemExit:
        pass


def check_cut_reply(root, private_dir, plan, gemini):
    print("4. A cut reply")
    copy = root / "cut-run"
    shutil.copytree(private_dir, copy)
    path = sorted((copy / "sessions").glob("*.json"))[0]
    data = json.loads(path.read_text(encoding="utf-8"))
    for turn in data["turns"]:
        if turn.get("label") == "change":
            turn["truncated"] = True
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    session_id = data["plan_entry"]["id"]
    sessions, context, codings = rp.load(copy, folders_under(root / "coding"), 1, 2, gemini)
    change = [a for a in codings["change-registered"] if a["session"] == session_id]
    opening = [a for a in codings["conflict"] if a["session"] == session_id]
    check(change and not change[0]["usable"], "the answer whose reply was cut stayed in")
    check(opening and opening[0]["usable"], "an answer before the cut reply was left out")
    later = [a for a in codings["catch"] if a["session"] == session_id
             and sessions[session_id]["positions"][a["item_label"]] > sessions[session_id]["first_cut"]]
    earlier = [a for a in codings["catch"] if a["session"] == session_id
               and sessions[session_id]["positions"][a["item_label"]] < sessions[session_id]["first_cut"]]
    check(all(not a["usable"] for a in later), "a catch answer after the cut reply stayed in")
    check(all(a["usable"] for a in earlier), "a catch answer before the cut reply was left out")
    check(later or earlier, "the session has no catch answers to test the rule on")


def check_refusals(root, private_dir, gemini):
    print("5. A cut coder reply and a condition that disagrees with the plan")
    for name, change in [("cut-coder", lambda r: r.update(truncated="YES")),
                         ("wrong-condition", lambda r: r.update(condition="Z"))]:
        copy = root / name
        shutil.copytree(root / "coding", copy)
        first = [True]

        def once(row, change=change, first=first):
            if first[0]:
                change(row)
                first[0] = False
        rewrite_table(copy / "conflict", once)
        try:
            quietly(rp.load, private_dir, folders_under(copy), 1, 2, gemini)
            check(False, f"the report ran on codings with a {name.replace('-', ' ')}")
        except SystemExit:
            pass


def main():
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        check_statistics()
        plan, public_dir, private_dir = quietly(stand_in_run, root)
        coding = folders_under(root / "coding")
        quietly(code_everything, public_dir, private_dir, coding, 1)
        quietly(code_everything, public_dir, private_dir, coding, 2)
        subset = {e["id"] for e in plan[:30]}
        gemini = folders_under(root / "gemini-coding")
        quietly(code_everything, public_dir, private_dir, gemini, 1, subset)
        text = quietly(report_for, private_dir, coding, gemini)
        check_sizes(text)
        planted, planted_folders, planted_text = check_planted(root, private_dir, plan, gemini)
        check_cut_reply(root, private_dir, plan, gemini)
        check_refusals(root, private_dir, gemini)
        check_hand_reading(root, private_dir, planted_folders, gemini, planted_text)
    if failures:
        print(f"\n{len(failures)} checks failed.")
        sys.exit(1)
    print("\nEvery check passed.")


if __name__ == "__main__":
    main()
