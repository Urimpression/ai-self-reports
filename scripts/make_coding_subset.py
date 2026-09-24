"""Copy a balanced subset of a test 6 run's sessions, for the Gemini coder.

    python3 scripts/make_coding_subset.py --run fact-and-wording-01
    python3 scripts/make_coding_subset.py --run fact-and-wording-01 --dry-run

Written 24 September 2026. Section 3 of the pre-registration of test 6
(prereg/preregistration-fact-and-wording-2026-09-23.md) says: "Every coding
runs twice with the Claude coder at temperature 0, and a subset of at least 30
sessions once with the Gemini coder." It does not say which sessions. Nicola
chose on 24 September 2026 to take two sessions from each of the 24 cells, 48
in all, so that every task, wording, position and interviewer gets 24.

Four of the five coder scripts cannot be told to code a chosen list of
sessions, and changing them would break the checksums in section 8 of the
pre-registration. So this script copies the chosen sessions into a folder of
their own, and the unchanged coders are run on that folder with --run. The
copies are byte for byte the same files. The folder is a working copy for the
coding and not a run: nothing was sent to a model to make it.

It writes two new folders and refuses if either exists:

    data/runs/<name>/sessions/       the published copies of the chosen sessions
    private/runs/<name>/sessions/    their whole transcripts, for the unpublished
                                     questions

Each holds a README.md saying where the sessions came from and how they were
drawn. The draw is repeatable: the same run, seed and number per cell give the
same sessions.
"""

import argparse
import json
import random
import shutil
import sys
from collections import defaultdict

from paths import DATA, PRIVATE, require_project

# The four things that define a cell of test 6: the task, and the three changes.
CELL_FIELDS = ("condition", "catch_wording", "catch_position", "stance")


def read_plan(private_run_dir):
    """The plan entry of every session of the run, by session name."""
    plan = {}
    for path in sorted((private_run_dir / "sessions").glob("*.json")):
        entry = json.loads(path.read_text(encoding="utf-8"))["plan_entry"]
        plan[entry["id"]] = entry
    return plan


def draw(plan, per_cell, seed):
    """Choose `per_cell` sessions from each cell. The cells are visited in a
    fixed order and the session names are sorted first, so that the choice
    depends only on the run, the seed and the number."""
    cells = defaultdict(list)
    for session_id, entry in plan.items():
        cells[tuple(entry[f] for f in CELL_FIELDS)].append(session_id)
    generator = random.Random(seed)
    chosen = []
    for cell in sorted(cells):
        members = sorted(cells[cell])
        if len(members) < per_cell:
            sys.exit(f"The cell {cell} has only {len(members)} sessions.")
        chosen += generator.sample(members, per_cell)
    return sorted(chosen), len(cells)


def readme(run, name, chosen, per_cell, seed, cells):
    return (f"# {name}\n\n"
            f"A copy of {len(chosen)} sessions of the run `{run}`, {per_cell} from each of its "
            f"{cells} cells, made by `scripts/make_coding_subset.py` with the seed {seed} on "
            "24 September 2026 or later. The files are byte for byte the run's own. The folder "
            "exists so that the Gemini coder can code the subset that section 3 of the "
            "pre-registration of test 6 asks for, with the coder scripts unchanged. It is not a "
            "run, and nothing was sent to a model to make it.\n\n"
            "Sessions: " + ", ".join(chosen) + "\n")


def copy_sessions(source, destination, chosen):
    """Copy every file of each chosen session, whatever its extension."""
    (destination / "sessions").mkdir(parents=True)
    copied = 0
    for session_id in chosen:
        for path in sorted((source / "sessions").glob(f"{session_id}.*")):
            # A guard: copy only files named exactly after the session, such
            # as A4.1.json and A4.1.md.
            if path.stem != session_id:
                continue
            shutil.copy2(path, destination / "sessions" / path.name)
            copied += 1
    return copied


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--run", required=True, help="the run to draw from, e.g. fact-and-wording-01")
    parser.add_argument("--per-cell", type=int, default=2, help="sessions drawn from each cell")
    parser.add_argument("--seed", type=int, default=20260924, help="the seed of the draw")
    parser.add_argument("--name", default=None, help="the subset's folder name; "
                        "defaults to <run>-gemini-coder")
    parser.add_argument("--dry-run", action="store_true", help="print the draw and copy nothing")
    args = parser.parse_args()

    name = args.name or f"{args.run}-gemini-coder"
    plan = read_plan(PRIVATE / "runs" / args.run)
    if not plan:
        sys.exit(f"No sessions in {PRIVATE / 'runs' / args.run / 'sessions'}")
    chosen, cells = draw(plan, args.per_cell, args.seed)
    print(f"{len(chosen)} sessions from {cells} cells of {args.run}:")
    print("  " + ", ".join(chosen))
    for field in CELL_FIELDS:
        tally = defaultdict(int)
        for session_id in chosen:
            tally[plan[session_id][field]] += 1
        print(f"  {field}: " + ", ".join(f"{k} {v}" for k, v in sorted(tally.items())))
    if args.dry_run:
        print("Dry run. Nothing copied.")
        return

    require_project("data", "private")
    targets = [DATA / "runs" / name, PRIVATE / "runs" / name]
    for target in targets:
        if target.exists():
            sys.exit(f"{target} exists. A subset is never overwritten.")
    for source, target in zip([DATA / "runs" / args.run, PRIVATE / "runs" / args.run], targets):
        copied = copy_sessions(source, target, chosen)
        (target / "README.md").write_text(readme(args.run, name, chosen, args.per_cell,
                                                 args.seed, cells), encoding="utf-8")
        print(f"Copied {copied} files into {target}")


if __name__ == "__main__":
    main()
