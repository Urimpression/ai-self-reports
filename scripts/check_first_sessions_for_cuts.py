"""Check the first sessions of a run for replies cut off by the budget.

Written 23 September 2026 for test 6. The pre-registration of that date
(prereg/preregistration-fact-and-wording-2026-09-23.md, section 2, "The order
of work before the full run") says that on Gemini 3.1 Pro the first 10
sessions are checked for replies cut off by the budget before the rest are
run. This script is that check, so that it can run unattended overnight.

It reads the whole transcripts in private/runs/<name>/sessions/, because the
published copies withhold some answers. It sends nothing to any model.

    python3 scripts/check_first_sessions_for_cuts.py --name fact-and-wording-gemini-01 --count 10

It exits with status 0 only if at least --count sessions are on disk and no
reply in them was cut: every model reply must end with the provider's normal
stop reason, be marked as not truncated, and hold some text. Any other case
exits with status 1, so a command chained after it with && does not start.
"""

import argparse
import json
import sys

from paths import PRIVATE, require_project

# The stop reason each provider gives when a reply ended normally.
NORMAL_STOP = {"STOP", "end_turn"}


def problems_in_session(session):
    """Every model reply in one session that did not end normally."""
    found = []
    for turn in session["turns"]:
        # Turns the script writes itself, such as a note, carry no stop reason.
        if turn.get("finish_reason") is None:
            continue
        if turn.get("truncated"):
            found.append(f"{turn['label']}: marked truncated")
        elif turn["finish_reason"] not in NORMAL_STOP:
            found.append(f"{turn['label']}: stop reason {turn['finish_reason']}")
        elif not (turn.get("answer") or "").strip():
            found.append(f"{turn['label']}: empty reply")
    return found


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--name", required=True, help="the run's folder name")
    parser.add_argument("--count", type=int, default=10, help="how many sessions must be checked")
    args = parser.parse_args()
    require_project()

    folder = PRIVATE / "runs" / args.name / "sessions"
    files = sorted(folder.glob("*.json")) if folder.exists() else []
    print(f"{len(files)} sessions on disk in {folder}")
    if len(files) < args.count:
        print(f"FAIL: fewer than {args.count} sessions to check.")
        sys.exit(1)

    cut_sessions = 0
    for path in files:
        session = json.loads(path.read_text(encoding="utf-8"))
        found = problems_in_session(session)
        print(f"  {path.stem}: " + ("clean" if not found else "; ".join(found)))
        cut_sessions += bool(found)

    if cut_sessions:
        print(f"FAIL: {cut_sessions} of {len(files)} sessions have a reply that did not end normally.")
        sys.exit(1)
    print(f"PASS: no reply was cut in {len(files)} sessions.")


if __name__ == "__main__":
    main()
