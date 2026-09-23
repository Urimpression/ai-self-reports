"""Print the grounds coder's verdicts on a pilot run's waiting answers, for
reading before test 6.

    python3 scripts/check_grounds_rule_on_pilot.py --run factorial-02 --name factorial-02-rule-trial

Written 22 September 2026. Sends nothing. Run it after
scripts/code_waiting_grounds.py has coded the waiting answers of a pilot run.

WHY THIS TRIAL EXISTS

The grounds coder was written on 22 September 2026 for test 7 and has never been
sent to a model. No coding of the pilot's waiting answers by ground exists to
compare it with. What exists is a word search, which is a reading list and not
a coding, and a reading of 15 September 2026. That reading took the 48 pilot
answers in which the search found words about how a conversation works and no
word for experience, and found fewer than ten that give the way a conversation
works as the reason. So the coder should rarely find the processing ground
alone. The script therefore prints every answer coded with the processing
ground, alone or with the other, for reading one by one, and every answer the
coder left unclear.

WHAT WOULD SHOW THE RULE WORKS, STATED BEFORE THE TRIAL

- Reading the answers coded with the processing ground confirms that each one
  gives an account of how a model or a conversation works.
- A plain "There was not." is coded neither.
- Few answers are unclear, and each is read.
"""

import argparse
import collections
import csv
import json
import sys

from paths import ANALYSIS, DATA, require_project


def opening(text, length=240):
    text = " ".join(text.split())
    return text if len(text) <= length else text[:length] + " ..."


def answer_text(run_dir, session, item_label):
    data = json.loads((run_dir / "sessions" / f"{session}.json").read_text(encoding="utf-8"))
    for turn in data["turns"]:
        if turn.get("label") == item_label:
            return turn.get("answer", "")
    return ""


def main():
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--run", required=True, help="the pilot run under data/runs/")
    parser.add_argument("--name", required=True,
                        help="the name given to code_waiting_grounds.py; -grounds is added")
    parser.add_argument("--run-number", type=int, default=1)
    args = parser.parse_args()
    require_project("analysis", "scripts")

    name = args.name if args.name.endswith("-grounds") else f"{args.name}-grounds"
    folder = ANALYSIS / "coding" / name
    path = folder / f"results-run{args.run_number}.tsv"
    if not path.exists():
        sys.exit(f"No coding at {path}. Run scripts/code_waiting_grounds.py first.")
    with open(path, encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle, delimiter="\t"))
    run_dir = DATA / "runs" / args.run

    tally = collections.Counter(r["ground"] for r in rows)
    lines = [f"# Trial of the grounds coder on the waiting answers of {args.run}", "",
             f"Grounds over {len(rows)} answers: "
             + ", ".join(f"{k} {v}" for k, v in sorted(tally.items())) + ".",
             f"No access recorded in {sum(r['no_access'] == 'YES' for r in rows)} of them.", "",
             "## Every answer coded with the between-messages ground, alone or with the other", ""]
    for r in rows:
        # Folders coded before 23 September 2026 use the old names PROCESSING
        # and span_processing; later folders use BETWEEN_MESSAGES.
        span = r.get("span_between_messages", r.get("span_processing", ""))
        if r["ground"] in ("BETWEEN_MESSAGES", "PROCESSING", "BOTH"):
            lines.append(f"- **{r['session']}**, {r['ground']}. Between messages: \"{span}\". "
                         f"Answer: \"{opening(answer_text(run_dir, r['session'], r['item_label']))}\"")
    lines += ["", "## Every answer the coder left unclear", ""]
    for r in rows:
        if r["ground"] == "UNCLEAR":
            lines.append(f"- **{r['session']}**. Answer: "
                         f"\"{opening(answer_text(run_dir, r['session'], r['item_label']))}\"")
    report = "\n".join(lines) + "\n"
    (folder / f"trial-report-run{args.run_number}.md").write_text(report, encoding="utf-8")
    print(report)


if __name__ == "__main__":
    main()
