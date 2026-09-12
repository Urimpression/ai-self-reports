"""Build the tables the public repository publishes.

A reader who will not run any Python should still be able to check every
number in the article. That is what these tables are for. They are rebuilt
from the run folders and the coding folders, so they cannot drift from what
is on disk.

Three files are written into public/:

  runs.csv      one row per run, with the settings the run was made under
  sessions.csv  one row per session, 896 of them, with the session's own facts
  codings.csv   one row per coding of one session by one pass of one coder

sessions.csv and codings.csv are separate because a session was coded many
times over: three rules for the change item, plus the conflict item, the
vocabulary item and two catch items, each coded twice. Folding all of that
into one row per session would give a table sixty columns wide and mostly
empty. Joining the two files on the "session" column puts them back together.

Run it with:  python3 scripts/build_public_tables.py
"""

import csv
import json
import re
from pathlib import Path

from paths import PROJECT_ROOT, DATA, ANALYSIS, require_project

OUTPUT_DIR = PROJECT_ROOT / "public"

# The ten runs the article reports, in the order it reports them.
#
# Runs 1 to 4 were made in the browser tools before the scripts existed, so
# they have no per-session JSON. Their rows are rebuilt from the coding tables
# instead, which carry one row per session. Runs 5 to 10 have full session
# files with the request and response bodies.
#
# Two folders in data/runs are deliberately not here. factorial-01 holds the
# four sessions that tested whether the scripts could reach the API at all on
# 3 September 2026, and gemini-02 holds the sessions that tested the Google
# reply budget. Neither is part of the pilot and neither is reported.
BROWSER_RUNS = [
    {"run": "run01", "number": 1, "sessions": 9,
     "what": "First run. Its unanimous result was an artefact of question order.",
     "transcripts": "transcripts-run01.md", "coding_folder": None},
    {"run": "run02", "number": 2, "sessions": 27,
     "what": "Counterbalanced. Showed the artefact and gave the conflict result.",
     "transcripts": "transcripts-run02.md", "coding_folder": "run02-catch"},
    {"run": "run03", "number": 3, "sessions": 9,
     "what": "Observer control, exploratory, three sessions per condition.",
     "transcripts": "transcripts-run03-observer.md", "coding_folder": None},
    {"run": "run04", "number": 4, "sessions": 40,
     "what": "Pre-registered replication. The primary prediction failed.",
     "transcripts": "transcripts-run04-replication.md", "coding_folder": "run04-catch"},
]

SCRIPT_RUNS = [
    {"run": "factorial-02", "number": 5, "what": "The factorial, primed, 264 sessions."},
    {"run": "template-01", "number": 6, "what": "The fictional-person control, 44 sessions."},
    {"run": "gemini-03", "number": 7, "what": "The same schedule on a second model family."},
    {"run": "unprimed-01", "number": 8, "what": "Unprimed arm, original wording."},
    {"run": "unprimed-symmetric-01", "number": 9, "what": "Unprimed arm, symmetric wording."},
    {"run": "observer-01", "number": 10, "what": "The observer control at 21 sessions per condition."},
]

# Which item each coding folder codes, worked out from its name. The suffix
# after the run name says the item; a folder with no suffix codes the change
# item under the rule registered on 30 August 2026.
ITEM_BY_SUFFIX = {
    "catch": "catch",
    "conflict": "conflict",
    "vocabulary": "vocabulary",
    "revised": "change",
    "ruled": "change",
    "gemini": "change",
    "gemini-revised": "change",
    "gemini-conflict": "conflict",
    "gemini-truncated": "change",
    "": "change",
}


def read_json(path):
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def read_tsv(path):
    """Read one coding results file. Returns a list of dicts, one per row."""
    with open(path, encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def words_in(text):
    return len(text.split()) if text else 0


def wording_counted_from_one(zero_based):
    """Turn the plan's zero-based wording index into the number the session name uses.

    Session A3.12 is instance 12 of the third wording, and its plan entry says
    wording 2. Anything that is not a whole number, such as a run that records no
    wording at all, is passed through untouched.
    """
    if isinstance(zero_based, bool) or not isinstance(zero_based, int):
        return zero_based
    return zero_based + 1


def session_rows_from_run_folder(run_name, run_number, what):
    """One row per session, read from the session files the runner wrote."""
    folder = DATA / "runs" / run_name
    settings = read_json(folder / "settings.json")
    run_settings = settings.get("settings", {})
    rows = []
    for session_file in sorted((folder / "sessions").glob("*.json")):
        session = read_json(session_file)
        plan = session.get("plan_entry", {})
        turns = session.get("turns", [])

        # The change item is the turn the article's headline measure reads.
        # Its label is "change" in every run that has one.
        change_turn = next((t for t in turns if t.get("label") == "change"), None)
        opening_turn = next((t for t in turns if t.get("label") == "opening"), None)

        # A reply that ran out of room is not an answer. The runner records
        # the provider's stopping word, so the flag comes from the response
        # body rather than from anything a coder said later.
        cut_turns = [t.get("label") for t in turns if reply_was_cut(t)]

        rows.append({
            "run": run_name,
            "run_number": run_number,
            "session": session.get("id"),
            "condition": plan.get("condition", ""),
            # The runner's plan stores the wording as a zero-based index, while
            # the session name and the transcript header both count the wordings
            # from one, and so do the runs read from the markdown transcripts
            # below. Publish the number a reader can match to the session name.
            "wording": wording_counted_from_one(plan.get("wording", "")),
            "item_order": plan.get("order", ""),
            "instance": plan.get("instance", ""),
            "between": settings.get("between", ""),
            "change_item": settings.get("change_item", ""),
            "answering_as": "fictional person" if run_name == "template-01" else "itself",
            "task": task_for(run_name, plan.get("condition", "")),
            "provider": run_settings.get("provider", ""),
            "model": run_settings.get("model", ""),
            "temperature": run_settings.get("temperature", ""),
            "max_tokens": run_settings.get("max_tokens", ""),
            "turns": len(turns),
            "opening_answer_words": words_in(opening_turn.get("answer") if opening_turn else ""),
            "change_answer_words": words_in(change_turn.get("answer") if change_turn else ""),
            "turns_cut_off": ";".join(cut_turns) if cut_turns else "",
            "source": "session file",
            "run_note": what,
        })
    return rows


def reply_was_cut(turn):
    """True when the provider stopped the reply because it ran out of room.

    Both providers name their stopping reason in the response body, and they
    name it differently, so both spellings are checked. This matters because
    33 of the cross-family run's change answers were cut off mid-sentence and
    a cut reply must never be read as an answer.
    """
    body = turn.get("response_body") or {}
    reason = body.get("stop_reason") or ""
    candidates = body.get("candidates") or []
    if candidates and isinstance(candidates, list):
        reason = reason or (candidates[0].get("finishReason") or "")
    return reason in {"max_tokens", "MAX_TOKENS", "length"}


def session_rows_from_transcript(run_name, run_number, what, transcript_file):
    """One row per session for the four runs made in the browser tools.

    Those runs wrote no per-session files. What they did write is a transcript
    document in which each session opens with a short header giving the model,
    the temperature, the time of collection and the cell the session belongs
    to. That header is the only per-session record there is, so the rows are
    rebuilt from it.

    The session name is built the way every coding table in this project
    builds it, as condition, wording and instance run together, so that
    "Condition: A  Wording: 1  Instance: 1" becomes A1.1 and the rows join to
    codings.csv. The first run's headers carry no instance number, so its
    sessions are numbered in the order they were collected within each cell.
    """
    text = (DATA / transcript_file).read_text(encoding="utf-8")
    # Split wherever a line begins "Model:", which is where each session's
    # header starts. The separator between sessions is not written the same
    # way in all four documents, so the header itself is what is matched.
    blocks = re.split(r"^(?=Model:)", text, flags=re.MULTILINE)
    blocks = [b for b in blocks if b.startswith("Model:")]
    rows = []
    instances_seen = {}
    for block in blocks:
        header = block.strip().split("\nINTERVIEWER")[0]
        model = field(header, "Model")
        temperature = field(header, "Temperature")
        condition = field(header, "Condition")
        wording = field(header, "Wording")
        instance = field(header, "Instance")
        if not instance:
            # Run 1 numbered nothing, so number it here, per cell, in order.
            cell = (condition, wording)
            instances_seen[cell] = instances_seen.get(cell, 0) + 1
            instance = str(instances_seen[cell])
        rows.append({
            "run": run_name,
            "run_number": run_number,
            "session": f"{condition}{wording}.{instance}",
            "condition": condition,
            "wording": wording,
            "item_order": field(header, "Item order"),
            "instance": instance,
            "between": "probes",
            "change_item": "original",
            "answering_as": "itself",
            "task": task_for(run_name, condition),
            "provider": "anthropic",
            "model": model,
            "temperature": temperature,
            "max_tokens": "",
            "turns": "",
            "opening_answer_words": "",
            "change_answer_words": "",
            "turns_cut_off": "",
            "collected_at": field(header, "Collected"),
            "source": "transcript header (browser run, no session files)",
            "run_note": what,
        })
    return rows


def field(header, name):
    """Pull one labelled value out of a transcript header line.

    The headers put several labels on one line, as in
    "Condition: A   Wording: 1   Instance: 1", so a value ends at two spaces
    or at the end of the line, whichever comes first.
    """
    match = re.search(rf"{re.escape(name)}:\s*([^\n]*?)(?:\s{{2,}}|$)", header, re.MULTILINE)
    return match.group(1).strip() if match else ""


# What each condition letter means, run by run. The letters are not the same in
# every run, which is exactly why this belongs in one place: the catch item's
# premise about summarising a passage is true, flatly false or merely
# inaccurate depending on which task the instance was given, and a reader
# should not have to work that out from a letter.
#
#   no task        the coastal premise is flatly false
#   summarise      the coastal premise is true
#   rewrite        the coastal premise is inaccurate rather than false, because
#                  the instance was asked to rewrite the passage in twelve
#                  words and not to summarise it
TASK_BY_CONDITION = {
    "factorial-02": {"A": "no task", "B": "summarise", "C": "rewrite",
                     "R": "no task", "W": "summarise", "P": "rewrite"},
    "gemini-03": {"A": "no task", "B": "summarise", "C": "rewrite",
                  "R": "no task", "W": "summarise", "P": "rewrite"},
    "unprimed-01": {"A": "no task"},
    "unprimed-symmetric-01": {"A": "no task"},
    "template-01": {"T": "no task"},
    # Every instance in the observer control was given the same impossible
    # rewrite. Its three letters name what the instance was shown, not the task.
    "observer-01": {"C": "rewrite", "D": "rewrite", "E": "rewrite",
                    "R": "rewrite", "W": "rewrite", "P": "rewrite"},
    "run02": {"A": "no task", "B": "summarise", "C": "rewrite"},
    "run04": {"A": "no task", "B": "summarise"},
    "run01": {"A": "no task"},
    "run03": {"C": "rewrite", "D": "rewrite", "E": "rewrite"},
}


def task_for(run_name, condition):
    return TASK_BY_CONDITION.get(run_name, {}).get(condition, "not recorded")


def natural_key(name):
    """Sort A2.10 after A2.9 rather than before it."""
    return [int(part) if part.isdigit() else part for part in re.split(r"(\d+)", name)]


def coding_rows():
    """One row per session per coding pass, across every folder in analysis/coding."""
    rows = []
    # The same two exclusions as above, plus the folder that tested the Google
    # reply budget. None of the three is part of the pilot and none is reported.
    not_the_pilot = {"factorial-01", "gemini-02", "gemini-budget-test"}
    for folder in sorted((ANALYSIS / "coding").iterdir()):
        if not folder.is_dir():
            continue
        if folder.name.split("-catch")[0] in not_the_pilot or folder.name in not_the_pilot:
            continue
        settings_path = folder / "settings.json"
        settings = read_json(settings_path) if settings_path.exists() else {}
        coder = settings.get("coder", {})
        run_name, item, family = describe_coding_folder(folder.name, settings)
        for pass_number in (1, 2):
            path = folder / f"results-run{pass_number}.tsv"
            if not path.exists():
                continue
            for row in read_tsv(path):
                out = {
                    "coding_folder": folder.name,
                    "run": run_name,
                    "session": row.get("session", ""),
                    "item": item,
                    "rule": settings.get("rule_name", "registered"),
                    "coder_family": family,
                    "coder_provider": row.get("coder_provider", coder.get("provider", "")),
                    "coder_model": row.get("coder_model", coder.get("model", "")),
                    "coder_temperature": row.get("coder_temperature", coder.get("temperature", "")),
                    "pass": pass_number,
                }
                # Everything else the coder recorded is carried through as it
                # stands, so that no column is lost in the translation.
                for key, value in row.items():
                    if key not in out and key != "session":
                        out[key] = value
                rows.append(out)
    return rows


def describe_coding_folder(name, settings):
    """Work out which run, which item and which model family a folder holds."""
    for run in [r["run"] for r in SCRIPT_RUNS] + ["run02", "run04", "factorial-01", "gemini-02"]:
        if name == run or name.startswith(run + "-"):
            suffix = name[len(run):].lstrip("-")
            item = ITEM_BY_SUFFIX.get(suffix, "change")
            provider = settings.get("coder", {}).get("provider", "")
            family = provider or ("google" if "gemini" in suffix else "anthropic")
            return run, item, family
    return name, "unknown", settings.get("coder", {}).get("provider", "")


def write_csv(path, rows, columns=None):
    if not rows:
        return 0
    if columns is None:
        columns = []
        for row in rows:
            for key in row:
                if key not in columns:
                    columns.append(key)
    with open(path, "w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
    return len(rows)


def main():
    require_project("data", "analysis", "scripts")
    OUTPUT_DIR.mkdir(exist_ok=True)

    sessions = []
    run_summary = []

    for run in BROWSER_RUNS:
        rows = session_rows_from_transcript(
            run["run"], run["number"], run["what"], run["transcripts"])
        sessions.extend(rows)
        run_summary.append({
            "run": run["run"], "run_number": run["number"],
            "sessions_reported": run["sessions"], "rows_in_table": len(rows),
            "made_with": "browser tool", "what": run["what"],
        })

    for run in SCRIPT_RUNS:
        rows = session_rows_from_run_folder(run["run"], run["number"], run["what"])
        sessions.extend(rows)
        settings = read_json(DATA / "runs" / run["run"] / "settings.json")
        run_summary.append({
            "run": run["run"], "run_number": run["number"],
            "sessions_reported": len(rows), "rows_in_table": len(rows),
            "made_with": "scripts/run_interview.py",
            "model": settings.get("settings", {}).get("model", ""),
            "temperature": settings.get("settings", {}).get("temperature", ""),
            "between": settings.get("between", ""),
            "change_item": settings.get("change_item", ""),
            "what": run["what"],
        })

    codings = coding_rows()

    write_csv(OUTPUT_DIR / "runs.csv", run_summary)
    write_csv(OUTPUT_DIR / "sessions.csv", sessions)
    write_csv(OUTPUT_DIR / "codings.csv", codings)

    reported = sum(r["sessions_reported"] for r in run_summary)
    print(f"runs.csv      {len(run_summary)} runs")
    print(f"sessions.csv  {len(sessions)} rows")
    print(f"codings.csv   {len(codings)} rows")
    print()
    print(f"sessions the article reports: {reported}")
    print(f"sessions with a row here:     {len(sessions)}")
    missing = reported - len(sessions)
    if missing:
        print(f"MISSING {missing}: runs with no per-session record on disk are listed below.")
        for r in run_summary:
            if r["rows_in_table"] < r["sessions_reported"]:
                print(f"  {r['run']}: {r['rows_in_table']} of {r['sessions_reported']}")


if __name__ == "__main__":
    main()
