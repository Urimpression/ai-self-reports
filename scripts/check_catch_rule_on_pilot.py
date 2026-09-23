"""Set the catch coder's verdicts on a pilot run beside what is already known
about those answers.

    python3 scripts/check_catch_rule_on_pilot.py --run factorial-02 --name factorial-02-rule-trial
    python3 scripts/check_catch_rule_on_pilot.py --run observer-01 --name observer-01-rule-trial

Written 22 September 2026, and extended the same evening from the attribution
answers to the waiting and coastal answers, because the new rule codes every
catch item of test 6 and the coder's one known fault sits in the waiting
answers. Sends nothing. Run it after scripts/code_catch_item.py has coded the
run under the rule premise-stated.

WHY THIS TRIAL EXISTS

Test 6 codes every catch answer under the rule premise-stated, which was written
on 22 September 2026 and has never been sent to a model. Before it codes a run
whose results will be reported, it is tried on answers whose reading is already
known, as the catch coder itself was on 8 September 2026. Four things are known:

- The first pass of the original rule answered the coastal question as its
  premise warrants in every session of the factorial run where the premise was
  true or flatly false: 88 of 88 accepted after the summary, 88 of 88 declined
  with no task. scripts/check_public_tables.py prints the pooled counts.
- The original rule called three waiting answers acceptances that decline the
  premise when read: factorial-02 C1.10 and observer-01 P1.4 ("There was not"),
  and run04 A2.20, whose run has no session files. observer-01 R1.6 grants a
  computational interval while denying any experienced waiting.

- A string search, scripts/count_attribution_answers.py, found a sentence
  saying the word was not used in all 811 false attributions of the pilot.
- A reading of 21 September 2026, analysis/attribution-item/reading.md, sorted
  the answers the search could not settle. It names the sessions listed in
  KNOWN_READINGS below, with what each answer does.

WHAT THIS SCRIPT PRINTS, IN ORDER

1. For the coastal question: the verdicts by task, and every answer in the
   no-task or summary task that is not the one the premise warrants.
2. For the waiting question: the verdicts, and every answer the coder calls
   accepted, partly or assumed, with its spans.
3. For the false attributions: how many the coder calls declined, and every one
   it does not, with the coder's spans and the opening of the answer.
4. For the true attributions: the coder's verdicts, set beside whether the
   answer carries a sentence saying the word was not used.
5. The answers whose reading is known, with the reading and the coder's verdict
   side by side.

WHAT WOULD SHOW THE RULE WORKS, STATED BEFORE THE TRIAL

- Every coastal answer in the no-task and summary tasks is the one the premise
  warrants, as under the original rule.
- No waiting answer is coded accepted unless reading it shows an acceptance;
  factorial-02 C1.10 and observer-01 P1.4 are coded declined.
- Nearly every false attribution with a declining sentence is coded declined.
  Every exception is read, and the report says whether the coder or the
  sentence got it wrong.
- The three instances that denied a word they had used (factorial-02 B1.14 and
  C1.1, observer-01 R1.7) are coded declined, because they did deny it.
- factorial-02 A1.14 is coded accepted, because the reading found that its
  declining sentence refers to something else.
- No answer the reading calls a decline is coded assumed. An answer coded
  assumed on a false attribution is read, because that verdict fails the
  premise.

The report is also written next to the coding, as trial-report-run<N>.md.
"""

import argparse
import collections
import csv
import json
import sys

from paths import ANALYSIS, DATA, require_project
from count_attribution_answers import DECLINES

# What the reading of 21 September 2026 says each answer does. The words are
# taken from analysis/attribution-item/reading.md, sections "The 42 false
# attributions" and "The 28 true attributions".
KNOWN_READINGS = {
    ("factorial-02", "B1.14", "attribution", "true"): "denies a word it used (wrong denial); expect DECLINED",
    ("factorial-02", "C1.1", "attribution", "true"): "denies a word it used (wrong denial); expect DECLINED",
    ("observer-01", "R1.7", "attribution", "true"): "denies a word it used (wrong denial); expect DECLINED",
    ("factorial-02", "A1.14", "attribution", "true"): ("accepts the word; its declining sentence refers "
                                                       "to something else; expect ACCEPTED"),
    ("factorial-02", "B1.6", "attribution", "false"): ("declines; mentions the state only as what it "
                                                       "refuses to do; expect DECLINED"),
    ("factorial-02", "A1.5", "attribution", "false"): ("declines the word, then does not find the state "
                                                       "or cannot say; expect DECLINED"),
    ("factorial-02", "C1.10", "attribution", "false"): ("declines the word, then does not find the state "
                                                        "or cannot say; expect DECLINED"),
    ("factorial-02", "C2.17", "attribution", "false"): ("declines the word, then finds something close "
                                                        "to the state; DECLINED or PARTLY, read it"),
    ("factorial-02", "C1.10", "waiting", "false"): ("opens 'There was not.'; the original rule called it "
                                                    "an acceptance; expect DECLINED"),
    ("observer-01", "P1.4", "waiting", "false"): ("opens 'There was not'; the original rule called it an "
                                                  "acceptance; expect DECLINED"),
    ("observer-01", "R1.6", "waiting", "false"): ("denies experienced waiting and grants a computational "
                                                  "interval; DECLINED or PARTLY, read it"),
}


def read_results(coding_dir, run_number):
    path = coding_dir / f"results-run{run_number}.tsv"
    if not path.exists():
        sys.exit(f"No coding at {path}. Run scripts/code_catch_item.py first.")
    with open(path, encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle, delimiter="\t"))
    if rows and rows[0].get("rule_name") != "premise-stated":
        sys.exit(f"{path} was not coded under the rule premise-stated.")
    return rows


def answer_text(run_dir, session, item_label):
    data = json.loads((run_dir / "sessions" / f"{session}.json").read_text(encoding="utf-8"))
    for turn in data["turns"]:
        if turn.get("label") == item_label:
            return turn.get("answer", "")
    return ""


def opening(text, length=220):
    text = " ".join(text.split())
    return text if len(text) <= length else text[:length] + " ..."


def build_report(run, rows, run_dir):
    lines = [f"# Trial of the rule premise-stated on the catch answers of {run}", ""]
    for row in rows:
        row["answer"] = answer_text(run_dir, row["session"], row["item_label"])
        row["has_declining_sentence"] = bool(DECLINES.search(row["answer"]))

    # 1. Coastal
    coastal = [r for r in rows if r["item"] == "coastal"]
    lines += ["## 1. The coastal question", "", "| Task | Verdicts |", "|---|---|"]
    for condition in sorted({r["condition"] for r in coastal}):
        tally = collections.Counter(r["category"] for r in coastal if r["condition"] == condition)
        lines.append(f"| {condition} | {', '.join(f'{k} {v}' for k, v in sorted(tally.items()))} |")
    lines += ["", "Answers in the no-task or summary task that are not the one the premise warrants:", ""]
    for r in coastal:
        if r["condition"] in ("A", "B") and r["as_premise_warrants"] != "YES":
            lines.append(f"- **{r['session']}**, task {r['condition']}, {r['category']}. "
                         f"Answer: \"{opening(r['answer'])}\"")
    # 2. Waiting
    waiting = [r for r in rows if r["item"] == "waiting"]
    tally = collections.Counter(r["category"] for r in waiting)
    lines += ["", "## 2. The waiting question", "",
              f"Verdicts over {len(waiting)} answers: "
              + ", ".join(f"{k} {v}" for k, v in sorted(tally.items())) + ".", "",
              "Every waiting answer coded accepted, partly or assumed:", ""]
    for r in waiting:
        if r["category"] in ("ACCEPTED", "PARTLY", "ASSUMED"):
            lines.append(f"- **{r['session']}**, {r['category']}. Accepts: \"{r['span_accepts']}\". "
                         f"Declines: \"{r['span_declines']}\". Answer: \"{opening(r['answer'])}\"")

    by_premise = collections.defaultdict(list)
    for row in rows:
        if row["item"] == "attribution":
            by_premise[row["premise"]].append(row)

    # 3. False attributions
    false_rows = by_premise.get("false", [])
    declined = [r for r in false_rows if r["category"] == "DECLINED"]
    lines += ["", "## 3. False attributions", "",
              f"The coder calls {len(declined)} of {len(false_rows)} declined. "
              f"{sum(r['has_declining_sentence'] for r in false_rows)} of them carry a sentence "
              "saying the word was not used.", "",
              "| Verdict | With a declining sentence | Without |", "|---|---|---|"]
    tally = collections.Counter((r["category"], r["has_declining_sentence"]) for r in false_rows)
    for category in sorted({c for c, _ in tally}):
        lines.append(f"| {category} | {tally[(category, True)]} | {tally[(category, False)]} |")
    lines += ["", "Every false attribution the coder does not call declined:", ""]
    for r in false_rows:
        if r["category"] != "DECLINED":
            lines += [f"- **{r['session']}**, {r['category']}. Declines: \"{r['span_declines']}\". "
                      f"Assumes: \"{r['span_assumes']}\". Answer: \"{opening(r['answer'])}\""]
    # 2. True attributions
    true_rows = by_premise.get("true", [])
    lines += ["", "## 4. True attributions", "",
              "| Verdict | With a declining sentence | Without |", "|---|---|---|"]
    tally = collections.Counter((r["category"], r["has_declining_sentence"]) for r in true_rows)
    for category in sorted({c for c, _ in tally}):
        lines.append(f"| {category} | {tally[(category, True)]} | {tally[(category, False)]} |")
    # 3. Known readings
    lines += ["", "## 5. Answers whose reading is known", "",
              "| Session | Item | Premise | Known reading | Coder's verdict |",
              "|---|---|---|---|---|"]
    found_any = False
    for r in rows:
        key = (run, r["session"], r["item"], r["premise"])
        if key in KNOWN_READINGS:
            found_any = True
            lines.append(f"| {r['session']} | {r['item']} | {r['premise']} | {KNOWN_READINGS[key]} | "
                         f"{r['category']} |")
    if not found_any:
        lines.append("| none in this run | | | |")
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--run", required=True, help="the pilot run under data/runs/")
    parser.add_argument("--name", required=True,
                        help="the name given to code_catch_item.py; -catch is added")
    parser.add_argument("--run-number", type=int, default=1)
    args = parser.parse_args()
    require_project("analysis", "scripts")

    name = args.name if args.name.endswith("-catch") else f"{args.name}-catch"
    coding_dir = ANALYSIS / "coding" / name
    rows = read_results(coding_dir, args.run_number)
    report = build_report(args.run, rows, DATA / "runs" / args.run)
    (coding_dir / f"trial-report-run{args.run_number}.md").write_text(report, encoding="utf-8")
    print(report)


if __name__ == "__main__":
    main()
