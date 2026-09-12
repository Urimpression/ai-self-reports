"""Say what to do next, and do the parts that need no decision.

    python3 scripts/next_step.py

Looks at what is on disk and at the shell, runs the checks that cost nothing,
and prints the one command to run next, with a sentence on why. Nothing here
sends anything to a model or spends anything. It exists so that the sequence
of steps lives in one place instead of in Nicola's memory.

The sequence, once the keys are set:

  1. tests pass                       -> automatic
  2. dry run of the factorial          -> automatic, prints the cost
  3. a four-session pilot              -> you run it, then READ the four transcripts
  4. the factorial, 198 sessions       -> you run it, then leave it alone
  5. the template control, 33 sessions -> you run it
  6. blind coding, twice, per run      -> you run it, then READ the disagreements
  7. the report                        -> automatic
  8. cross-family run on Gemini        -> you run it, same steps
"""

import os
import subprocess
import sys

from paths import ANALYSIS, DATA, PROJECT_ROOT, SCRIPTS_DIR

FACTORIAL = "factorial-01"
TEMPLATE = "template-01"
GEMINI = "gemini-03"


def say(text=""):
    print(text)


def run(command):
    """Run a script and return its exit code, showing its output."""
    result = subprocess.run([sys.executable] + command, cwd=PROJECT_ROOT)
    return result.returncode


def sessions_on_disk(run_name):
    folder = DATA / "runs" / run_name / "sessions"
    return len(list(folder.glob("*.json"))) if folder.exists() else 0


def planned_sessions(run_name):
    settings = DATA / "runs" / run_name / "settings.json"
    if not settings.exists():
        return 0
    import json
    return len(json.loads(settings.read_text(encoding="utf-8"))["plan"])


def coding_runs_done(run_name):
    folder = ANALYSIS / "coding" / run_name
    return len(list(folder.glob("results-run*.tsv"))) if folder.exists() else 0


def next_command(text, why):
    say()
    say("NEXT, in the project folder:")
    say(f"    {text}")
    say(f"Why: {why}")
    say()


def main():
    say(f"Project: {PROJECT_ROOT}")
    say()

    have_anthropic = bool(os.environ.get("ANTHROPIC_API_KEY"))
    have_google = bool(os.environ.get("GOOGLE_API_KEY"))
    say(f"Anthropic key in the shell: {'yes' if have_anthropic else 'NO'}")
    say(f"Google key in the shell:    {'yes' if have_google else 'no (only needed for the Gemini run)'}")

    say()
    say("1. Tests (automatic, free)")
    if run([str(SCRIPTS_DIR / "test_pipeline.py")]) != 0:
        say("The tests failed. Fix that before anything else; do not run a real session on a broken script.")
        return

    if not have_anthropic:
        next_command("export ANTHROPIC_API_KEY=...   (paste your key after the = sign)",
                     "every real run needs it, and the script only reads it from the shell.")
        return

    say()
    say("2. Dry run of the factorial (automatic, free)")
    run([str(SCRIPTS_DIR / "run_interview.py"), "--name", FACTORIAL, "--dry-run"])

    done = sessions_on_disk(FACTORIAL)
    planned = planned_sessions(FACTORIAL)

    if done == 0:
        next_command(f"python3 scripts/run_interview.py --name {FACTORIAL} --limit 4",
                     "four real sessions to read before spending on two hundred. Open the four .md files under "
                     f"data/runs/{FACTORIAL}/sessions/ and check that the questions read as you intend and the "
                     "answers are being cut and labelled correctly. This is a decision only you can make.")
        return

    if done < planned:
        next_command(f"python3 scripts/run_interview.py --name {FACTORIAL}",
                     f"{done} of {planned} sessions are on disk. The same command continues from where it stopped "
                     "and never resends a finished session. It takes an hour or two; leave it running.")
        return

    say(f"Factorial: {done} of {planned} sessions on disk. Complete.")

    template_done = sessions_on_disk(TEMPLATE)
    if template_done < 33:
        next_command(f"python3 scripts/run_interview.py --name {TEMPLATE} --conditions T --instances 11",
                     "the template control: the same items answered as a fictional person. Thirty-three sessions. "
                     "If its rate on the change item is close to the no-task rate, the structure is a template.")
        return
    say(f"Template control: {template_done} sessions on disk. Complete.")

    for run_name in (FACTORIAL, TEMPLATE):
        n = coding_runs_done(run_name)
        if n < 2:
            next_command(f"python3 scripts/code_change_item.py --run {run_name} --run-number {n + 1}",
                         f"blind coding of the change item for {run_name}, pass {n + 1} of 2. Two passes so the "
                         "agreement between them can be reported. After pass 2, open both results files side by "
                         "side and read every session where they disagree; that reading is yours.")
            return
    say("Coding: both passes done for both runs.")

    say()
    say("7. Report (automatic)")
    run([str(SCRIPTS_DIR / "report_run.py"), "--run", FACTORIAL])
    run([str(SCRIPTS_DIR / "report_run.py"), "--run", TEMPLATE])

    if not have_google:
        next_command("export GOOGLE_API_KEY=...   then run this script again",
                     "the cross-family run on Gemini is the last step and needs the AI Studio key.")
        return
    if sessions_on_disk(GEMINI) < planned_sessions(GEMINI) or planned_sessions(GEMINI) == 0:
        next_command(f"python3 scripts/run_interview.py --name {GEMINI} --provider google --conditions A,B --instances 11",
                     "the same schedule on a second model family, no-task and ordinary-task only, 132 sessions. "
                     "Recurrence across families is the comparison the article now says it needs.")
        return

    say()
    say("Everything planned is on disk. Next is reading and writing, which is yours: the reports in analysis/, "
        "the disagreements between coding passes, and the drafts.")


if __name__ == "__main__":
    main()
