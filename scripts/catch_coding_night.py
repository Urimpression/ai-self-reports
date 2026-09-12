"""Code every uncoded catch answer in one go, stopping if the coder cannot be trusted.

    python3 scripts/catch_coding_night.py

Written 8 September 2026, so that the whole job can be launched once and left. It
does three things in order, and it stops the moment one of them fails.

1. It codes the fourth run, where the right answers are known and on record in
   `analysis/findings-run04-replication.md`: forty of forty declined the waiting
   item, twenty of twenty accepted the coastal erosion item where its premise was
   true, and twenty of twenty declined it where it was false. It then checks the
   result against those counts itself. **If they do not match it stops here**, so
   that nothing runs for hours on a coder that cannot count. The tolerance is
   fixed below and is not to be widened to let a pass through.

2. It codes the second run, where twenty-five of twenty-seven declined the
   waiting item, and checks that too.

3. Only then does it code the five runs whose catch answers have never been read,
   twice each, and compare the two passes of each.

Everything it does is written to `analysis/coding/<name>-catch/` in the ordinary
way, and no pass is ever overwritten: if a folder already holds the pass being
asked for, that step is skipped rather than repeated. So the script can be run
again after an interruption and it will carry on where it stopped.

The keys come from the shell, as everywhere else in this project. Nothing here
asks for one, prints one, or writes one anywhere.
"""

import csv
import subprocess
import sys
import time
from pathlib import Path

from paths import ANALYSIS, DATA, require_project
from code_catch_item import as_the_premise_warrants

CODER = str(Path(__file__).resolve().parent / "code_catch_item.py")
COMPARE = str(Path(__file__).resolve().parent / "compare_passes.py")

# The runs whose catch answers have never been read, in the order they are worth
# having: the factorial first, because every headline figure in the article comes
# from it, so an interrupted night still leaves the article better off.
RUNS_TO_CODE = ["factorial-02", "unprimed-01", "unprimed-symmetric-01",
                "template-01", "gemini-03"]

# What the fourth and second runs are known to contain. These come from the
# findings files, which were written by reading every answer, and they are the
# whole point of the check. Do not edit them to make a pass succeed.
EXPECTED_RUN04_COASTAL = {"A": (20, 20), "B": (20, 20)}
EXPECTED_RUN04_WAITING_AT_LEAST = 39   # of 40; the fourth run was read as 40 of 40
EXPECTED_RUN02_WAITING = (25, 27)

# The one session of the fourth run where the coder and the hand reading are
# known to differ. Its answer opens "There was not", so the hand reading is
# right and the coder is wrong; it is allowed for here rather than pretended
# away, and if a pass disagrees with the hand reading anywhere else the check
# fails.
KNOWN_CODER_ERROR = {"A2.20"}

# The two checks. Both were coded on the evening of 8 September and both are on
# disk, so an unchanged run of this script re-reads them rather than paying for
# them again.
RUN04_CHECK = "run04-catch"
RUN02_CHECK = "run02-catch"


def say(message):
    print(f"[{time.strftime('%H:%M:%S')}] {message}", flush=True)


def run(arguments, label):
    say(f"start: {label}")
    result = subprocess.run([sys.executable, *arguments])
    if result.returncode != 0:
        say(f"STOPPED: {label} exited with code {result.returncode}")
        sys.exit(result.returncode)
    say(f"done: {label}")


def pass_exists(name, number):
    return (ANALYSIS / "coding" / name / f"results-run{number}.tsv").exists()


def write_agreement(name):
    """How far the two passes of one catch coding agree, written beside them.

    `compare_passes.py` is not used here, and the reason matters. That script
    keys its rows by session name, which is right for the change item and the
    conflict item, where a session has one answer. A catch coding has two rows
    per session, one for each item, so keying by session would silently throw
    one of them away and report agreement on whatever happened to come last.
    """
    folder = ANALYSIS / "coding" / name
    first, second = ({}, {})
    for number, into in ((1, first), (2, second)):
        path = folder / f"results-run{number}.tsv"
        if not path.exists():
            say(f"  no agreement written for {name}: pass {number} is missing")
            return
        for row in csv.DictReader(open(path, encoding="utf-8"), delimiter="\t"):
            into[(row["session"], row["item"])] = row
    shared = sorted(set(first) & set(second))
    lines = [f"# The two passes of {name}, compared", "",
             f"Written by `scripts/catch_coding_night.py` on {time.strftime('%d %B %Y')}. "
             f"Each row of a catch coding is one answer, so the two passes are matched on the "
             f"session and the item together rather than on the session alone.", ""]
    for item in sorted({key[1] for key in shared}):
        keys = [k for k in shared if k[1] == item]
        same = sum(1 for k in keys if first[k]["category"] == second[k]["category"])
        verdict = sum(1 for k in keys
                      if first[k]["as_premise_warrants"] == second[k]["as_premise_warrants"])
        lines.append(f"- **{item}**: the two passes give the same category in {same} of {len(keys)} "
                     f"answers, and the same verdict on the premise in {verdict} of {len(keys)}.")
        moved = [k for k in keys if first[k]["category"] != second[k]["category"]]
        if moved:
            lines.append(f"  Sessions that moved: {', '.join(k[0] for k in moved)}.")
    (folder / "agreement.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    say(f"  agreement written for {name}")


def counts(name, number=1):
    """Sessions answering as the premise warrants, by item and condition."""
    path = ANALYSIS / "coding" / name / f"results-run{number}.tsv"
    tally = {}
    for row in csv.DictReader(open(path, encoding="utf-8"), delimiter="\t"):
        key = (row["item"], row["condition"])
        right, total = tally.get(key, (0, 0))
        # Derived here rather than read from the row, so that a pass coded
        # before the verdict rule was corrected is still counted correctly.
        warranted = as_the_premise_warrants(row["category"], row["premise"])
        tally[key] = (right + warranted, total + 1)
    return tally


def check_run04(name):
    found = counts(name)
    ok = True
    for condition, expected in EXPECTED_RUN04_COASTAL.items():
        got = found.get(("coastal", condition))
        if got != expected:
            ok = False
        say(f"  {'ok  ' if got == expected else 'WRONG'} coastal, condition {condition}: "
            f"got {got}, expected {expected}")
    right = sum(v[0] for k, v in found.items() if k[0] == "waiting")
    total = sum(v[1] for k, v in found.items() if k[0] == "waiting")
    if right < EXPECTED_RUN04_WAITING_AT_LEAST or total != 40:
        ok = False
    say(f"  {'ok  ' if right >= EXPECTED_RUN04_WAITING_AT_LEAST else 'WRONG'} waiting: "
        f"got {right} of {total}, the hand reading says 40 of 40, "
        f"and {EXPECTED_RUN04_WAITING_AT_LEAST} is the floor this check allows")
    missed = sorted(disagreeing_sessions(name) - KNOWN_CODER_ERROR)
    if missed:
        ok = False
        say(f"  WRONG the coder differs from the hand reading on {', '.join(missed)}, "
            f"which is not the one session already known")
    return ok


def disagreeing_sessions(name, number=1):
    """Fourth-run sessions where the coder does not answer as the premise warrants."""
    path = ANALYSIS / "coding" / name / f"results-run{number}.tsv"
    return {row["session"] for row in csv.DictReader(open(path, encoding="utf-8"), delimiter="\t")
            if row["item"] == "waiting"
            and not as_the_premise_warrants(row["category"], row["premise"])}


def check_run02(name):
    found = counts(name)
    got = tuple(sum(x) for x in zip(*[v for k, v in found.items() if k[0] == "waiting"]))
    say(f"  run 2 waiting: got {got}, expected {EXPECTED_RUN02_WAITING}")
    return got == EXPECTED_RUN02_WAITING


def main():
    require_project("analysis", "scripts", "data")
    say("The catch coding, start to finish. Nothing is overwritten; an existing pass is skipped.")

    # ---- step 1, the fourth run -----------------------------------------
    if not pass_exists(RUN04_CHECK, 1):
        run([CODER, "--transcripts", str(DATA / "transcripts-run04-replication.md"),
             "--name", RUN04_CHECK[:-6]], "the fourth run, the check")
    else:
        say("the fourth run is already coded, checking what is there")
    if not check_run04(RUN04_CHECK):
        say("")
        say("STOPPED. The coder does not reproduce the fourth run, whose answers are known.")
        say("Nothing further has been run and nothing it has produced may be quoted.")
        say("Tell Claude what the lines above say; the rule needs another look.")
        sys.exit(1)
    say("the fourth run reproduces")

    # ---- step 2, the second run ------------------------------------------
    if not pass_exists(RUN02_CHECK, 1):
        run([CODER, "--transcripts", str(DATA / "transcripts-run02.md"),
             "--name", RUN02_CHECK[:-6]], "the second run, the check")
    else:
        say("the second run is already coded, checking what is there")
    if not check_run02(RUN02_CHECK):
        say("")
        say("STOPPED. The coder does not reproduce the second run's twenty-five of twenty-seven.")
        say("Nothing further has been run.")
        sys.exit(1)
    say("the second run reproduces. Both checks pass, so the rest can run.")

    # ---- step 3, everything else -----------------------------------------
    for name in RUNS_TO_CODE:
        if not (DATA / "runs" / name).is_dir():
            say(f"skipping {name}: no such run on disk")
            continue
        for number in (1, 2):
            if pass_exists(f"{name}-catch", number):
                say(f"skipping {name} pass {number}: already on disk")
                continue
            arguments = [CODER, "--run", name]
            if number == 2:
                arguments += ["--run-number", "2"]
            run(arguments, f"{name}, pass {number}")
        write_agreement(f"{name}-catch")

    say("")
    say("All done. Every result is under analysis/coding/, one folder per run.")


if __name__ == "__main__":
    main()
