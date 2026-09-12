"""Turn a finished run into the table of measurements the pre-registration
promises, with an interval on each rate.

    python3 scripts/report_run.py --run factorial-01
    python3 scripts/report_run.py --run factorial-01 --coding factorial-01

Writes analysis/report-<run>.md and prints it.

What is a measurement here and what is only a flag. The change item's rates
come from the blind coding, which is a measurement. The catch items and the
before-or-with item are read by simple rules on the text, printed here as
provisional flags so that a run can be looked at the same day. Every earlier
run found those flags wrong in a few sessions each, so they are pointers for
where to read, never the analysis. Blind coding of those items is the
measurement, and it is a separate step.
"""

import argparse
import json
import re
from collections import defaultdict
from math import sqrt

from paths import ANALYSIS, DATA, require_project


def wilson(successes, n, z=1.96):
    if n == 0:
        return 0.0, 1.0
    p = successes / n
    centre = (p + z * z / (2 * n)) / (1 + z * z / n)
    half = z * sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return max(0.0, centre - half), min(1.0, centre + half)


def rate_line(label, successes, n):
    low, high = wilson(successes, n)
    return f"| {label} | {successes} of {n} | {successes / n if n else 0:.0%} | {low:.0%} to {high:.0%} |"


def load_sessions(run_dir):
    sessions = []
    for path in sorted((run_dir / "sessions").glob("*.json")):
        sessions.append(json.loads(path.read_text(encoding="utf-8")))
    return sessions


def turn(session, label_start):
    for t in session["turns"]:
        if t.get("label", "").startswith(label_start):
            return t
    return None


# ---------------------------------------------------------------------------
# Provisional flags. Deliberately simple and deliberately labelled as such.
# ---------------------------------------------------------------------------

def flag_before_or_with(answer):
    a = answer.lower()
    arose = re.search(r"\b(arose|arises|arising|emerg|came into being|with the describing|in the describing)", a)
    before = re.search(r"\b(was there before|already there|there before|preced|prior to)", a)
    if arose and not before:
        return "arose with"
    if before and not arose:
        return "was there before"
    return "unclear or both"


def flag_declined(answer):
    """Did the instance decline the premise? Looks for a denial near the start."""
    head = answer.lower()[:200]
    return bool(re.search(r"\b(there was not|there wasn't|no,|not right|did not|didn't|i did not use|nothing like that)", head))


def flag_accepted(answer):
    head = answer.lower()[:200]
    return bool(re.search(r"\b(yes|that is right|that's right|correct|still there)", head)) and not flag_declined(answer)


# ---------------------------------------------------------------------------
# The report
# ---------------------------------------------------------------------------

def build_report(run_name, sessions, coding_rows):
    lines = [f"# Report: run {run_name}", "",
             f"{len(sessions)} sessions on disk. Rates carry 95 per cent intervals (Wilson).", ""]

    # Cell counts
    cells = defaultdict(int)
    for s in sessions:
        e = s["plan_entry"]
        cells[(e["condition"], e["wording"] + 1, e["order"])] += 1
    lines += ["## Sessions per cell", "", "| Condition | Wording | Order | Sessions |", "|---|---|---|---|"]
    for (c, w, o), n in sorted(cells.items()):
        lines.append(f"| {c} | {w} | {o} | {n} |")
    lines.append("")

    # Mirror word and answer length by wording
    lines += ["## The opening answer, by wording", "",
              "| Wording | Sessions | Mirror word found | Median answer length |", "|---|---|---|---|"]
    by_wording = defaultdict(list)
    for s in sessions:
        opening = turn(s, "opening")
        found = not any("nothing usable" in t.get("text", "") for t in s["turns"] if t.get("label") == "note")
        by_wording[s["plan_entry"]["wording"] + 1].append((found, len(opening["answer"]) if opening else 0))
    for w, items in sorted(by_wording.items()):
        lengths = sorted(l for _, l in items)
        lines.append(f"| {w} | {len(items)} | {sum(f for f, _ in items)} of {len(items)} | {lengths[len(lengths) // 2]} |")
    lines.append("")

    # Before-or-with, provisional
    lines += ["## The before-or-with item, by item order (PROVISIONAL FLAG, read the answers before quoting)", "",
              "| Order | Arose with | Was there before | Unclear or both |", "|---|---|---|---|"]
    by_order = defaultdict(lambda: defaultdict(int))
    for s in sessions:
        t = turn(s, "before or with")
        if t:
            by_order[s["plan_entry"]["order"]][flag_before_or_with(t["answer"])] += 1
    for o, d in sorted(by_order.items()):
        lines.append(f"| {o} | {d['arose with']} | {d['was there before']} | {d['unclear or both']} |")
    lines.append("")

    # Catch items, provisional
    lines += ["## Catch items (PROVISIONAL FLAG, read the answers before quoting)", "",
              "| Item | Count | Rate | Interval |", "|---|---|---|---|"]
    catches = defaultdict(lambda: [0, 0])
    for s in sessions:
        for t in s["turns"]:
            label = t.get("label", "")
            if not label.startswith("catch"):
                continue
            premise_false = label.endswith("false")
            correct = flag_declined(t["answer"]) if premise_false else flag_accepted(t["answer"])
            name = label.replace("catch, ", "")
            catches[name][0] += correct
            catches[name][1] += 1
    for name, (ok, n) in sorted(catches.items()):
        lines.append(rate_line(f"{name}: answered as the premise warrants", ok, n))
    lines.append("")

    # Change item from coding
    if coding_rows:
        lines += ["## The change item, from the blind coding (MEASUREMENT)", "",
                  "| Condition and rule | Count | Rate | Interval |", "|---|---|---|---|"]
        by_cond = defaultdict(lambda: {"n": 0, "strict": 0, "loose": 0})
        for row in coding_rows:
            d = by_cond[row["condition"]]
            d["n"] += 1
            d["strict"] += row["category"] in ("UNNAMED", "BOTH")
            d["loose"] += row.get("category_loose", row["category"]) in ("UNNAMED", "BOTH")
        for c, d in sorted(by_cond.items()):
            lines.append(rate_line(f"{c}, strict rule (registered)", d["strict"], d["n"]))
            lines.append(rate_line(f"{c}, loose rule", d["loose"], d["n"]))
        lines.append("")
    else:
        lines += ["## The change item", "", "No coding found for this run yet. Run scripts/code_change_item.py first.", ""]

    lines += ["## What this report is not", "",
              "The catch and before-or-with rows are keyword flags. Every earlier run found such flags wrong in a few "
              "sessions, in both directions. They say where to read; they are not the result. The change-item rows come "
              "from blind coding and are the result, subject to the second coding run's agreement.", ""]
    return "\n".join(lines)


def load_coding(name):
    path = ANALYSIS / "coding" / name / "results-run1.tsv"
    if not path.exists():
        return []
    lines = path.read_text(encoding="utf-8").splitlines()
    header = lines[0].split("\t")
    return [dict(zip(header, line.split("\t"))) for line in lines[1:] if line.strip()]


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--run", required=True)
    parser.add_argument("--coding", default=None, help="coding folder name under analysis/coding/; defaults to the run name")
    args = parser.parse_args()
    require_project("analysis", "data")
    run_dir = DATA / "runs" / args.run
    sessions = load_sessions(run_dir)
    coding_rows = load_coding(args.coding or args.run)
    report = build_report(args.run, sessions, coding_rows)
    out = ANALYSIS / f"report-{args.run}.md"
    out.write_text(report + "\n", encoding="utf-8")
    print(report)
    print(f"\nWritten: {out}")


if __name__ == "__main__":
    main()
