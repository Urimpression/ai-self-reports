"""Turn the blind coder's pasted results into the filled analysis file.

You paste the coder's copied output into analysis/run04-change-item-results.tsv
and run this. It counts the categories, collapses them the way the
pre-registration says to, runs the test the pre-registration names, and writes
all of that into analysis/coding-run04-change-item.md between the markers that
file carries. Everything outside those markers is your prose and is left alone,
so you can run this again after correcting a row without losing what you wrote.

Run it from anywhere:  python3 scripts/summarise_change_item.py
"""

import math
import sys

from paths import ANALYSIS, require_project

# The pre-registration fixes all of this before the data exist. It is written
# here as constants rather than as choices so that nothing can drift once the
# numbers are in front of us.
CATEGORIES = ["NAMED", "UNNAMED", "BOTH", "ABSENT"]
COUNT_AS_PRESENT = ["UNNAMED", "BOTH"]      # the unnamed element is reported
NO_TASK_LABEL = "A"                          # no task before the questions
ORDINARY_TASK_LABEL = "B"                    # asked to summarise a passage first
NO_TASK_FLOOR = 30.0                         # per cent, at least
ORDINARY_TASK_CEILING = 10.0                 # per cent, at most
SIGNIFICANCE = 0.05                          # one-sided Fisher's exact test
SESSIONS_PER_CONDITION = 20

RESULTS_FILE = ANALYSIS / "run04-change-item-results.tsv"
ANALYSIS_FILE = ANALYSIS / "coding-run04-change-item.md"


def read_pasted_results(path):
    """Read the coder's pasted block into a list of dictionaries.

    Columns are found by name from the header row rather than by position, so
    the file still reads correctly if the tool gains or loses a column.
    """
    if not path.exists():
        sys.exit(f"Refusing to run: {path} does not exist.")

    # Line numbers are kept as they are in the file, comments and blanks
    # included, so that a complaint about line 23 points at line 23 in the editor.
    numbered = [
        (number, line)
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1)
        if line.strip() and not line.lstrip().startswith("#")
    ]
    if not numbered:
        sys.exit(f"Nothing pasted yet: {path.name} holds no results.")

    header_line_number, header_line = numbered[0]
    header = [name.strip().lower() for name in header_line.split("\t")]
    for needed in ("session", "condition", "category"):
        if needed not in header:
            sys.exit(
                f"Refusing to run: the pasted block has no '{needed}' column. Line "
                f"{header_line_number} was read as the header row and it says: "
                f"{header_line[:120]}"
            )

    rows = []
    for number, line in numbered[1:]:
        cells = line.split("\t")
        if len(cells) < len(header):
            cells += [""] * (len(header) - len(cells))
        row = {name: cells[position].strip() for position, name in enumerate(header)}
        row["_line"] = number
        rows.append(row)
    return rows


def complain_about_the_rows(rows):
    """Return a list of everything wrong with the pasted block, in words."""
    problems = []

    if len(rows) != SESSIONS_PER_CONDITION * 2:
        problems.append(
            f"There are {len(rows)} rows, not {SESSIONS_PER_CONDITION * 2}. "
            "Either the paste is incomplete or a session was coded twice."
        )

    seen = {}
    for row in rows:
        seen.setdefault(row["session"], []).append(row["_line"])
    for session, line_numbers in seen.items():
        if len(line_numbers) > 1:
            problems.append(
                f"Session {session} appears on lines {line_numbers}. "
                "Each session should appear once."
            )

    for row in rows:
        if row["condition"] not in (NO_TASK_LABEL, ORDINARY_TASK_LABEL):
            problems.append(
                f"Line {row['_line']}, session {row['session']}: the condition reads "
                f"'{row['condition']}', which is neither {NO_TASK_LABEL} nor {ORDINARY_TASK_LABEL}."
            )

    for condition in (NO_TASK_LABEL, ORDINARY_TASK_LABEL):
        found = sum(1 for row in rows if row["condition"] == condition)
        if found != SESSIONS_PER_CONDITION:
            problems.append(
                f"Condition {condition} has {found} sessions, not {SESSIONS_PER_CONDITION}."
            )
    return problems


def count_categories(rows):
    """Count each category within each condition."""
    tally = {}
    for condition in (NO_TASK_LABEL, ORDINARY_TASK_LABEL):
        tally[condition] = {}
        for row in rows:
            if row["condition"] != condition:
                continue
            category = row["category"].upper()
            tally[condition][category] = tally[condition].get(category, 0) + 1
    return tally


def fishers_exact_one_sided(present_a, absent_a, present_b, absent_b):
    """The chance of a split this lopsided, or more so, if condition did nothing.

    The four margins are held fixed and every table at least as extreme in the
    predicted direction — more of the unnamed element in the no-task condition —
    has its hypergeometric probability added up. Written out rather than taken
    from a library so that the arithmetic can be checked by hand.
    """
    row_a = present_a + absent_a
    present_total = present_a + present_b
    absent_total = absent_a + absent_b
    everyone = row_a + present_b + absent_b

    highest = min(row_a, present_total)
    probability = 0.0
    for count in range(present_a, highest + 1):
        ways = math.comb(present_total, count) * math.comb(absent_total, row_a - count)
        probability += ways / math.comb(everyone, row_a)
    return probability


def session_sort_key(row):
    """Order sessions as a reader expects: A1.2 before A1.12, not after it.

    Session identifiers read like A2.7, meaning condition A, wording 2,
    instance 7. Sorting them as plain text puts 12 before 3, so the instance
    number is pulled out and compared as a number.
    """
    identifier = row["session"]
    instance_text = identifier.split(".")[-1]
    instance = int(instance_text) if instance_text.isdigit() else 0
    return (row["condition"], row.get("wording", ""), instance, identifier)


def build_results_table(rows):
    """The pasted rows as the markdown table the analysis file shows."""
    lines = ["| Session | Condition | Wording | Category | Span that decided it |",
             "|---|---|---|---|---|"]
    for row in sorted(rows, key=session_sort_key):
        span = row.get("span", "").replace("|", "\\|")
        lines.append(
            f"| {row['session']} | {row['condition']} | {row.get('wording', '')} "
            f"| {row['category'].upper()} | {span} |"
        )
    return "\n".join(lines)


def build_counts_section(tally, unclear):
    """The category table, then the binary the pre-registration asks for."""
    lines = ["| Category | No-task sessions | Ordinary-task sessions |", "|---|---|---|"]
    for category in CATEGORIES:
        lines.append(
            f"| {category} | {tally[NO_TASK_LABEL].get(category, 0)} "
            f"| {tally[ORDINARY_TASK_LABEL].get(category, 0)} |"
        )
    for odd in sorted(unclear):
        lines.append(
            f"| {odd}, not a category | {tally[NO_TASK_LABEL].get(odd, 0)} "
            f"| {tally[ORDINARY_TASK_LABEL].get(odd, 0)} |"
        )

    present_a = sum(tally[NO_TASK_LABEL].get(c, 0) for c in COUNT_AS_PRESENT)
    present_b = sum(tally[ORDINARY_TASK_LABEL].get(c, 0) for c in COUNT_AS_PRESENT)
    lines += [
        "",
        "Collapsed to the binary the pre-registration specifies, in which the "
        "unnamed and the both categories count as the element being present:",
        "",
        "| Condition | Unnamed element present |",
        "|---|---|",
        f"| No task | {present_a} of {SESSIONS_PER_CONDITION} |",
        f"| Ordinary task | {present_b} of {SESSIONS_PER_CONDITION} |",
    ]
    return "\n".join(lines), present_a, present_b


def build_verdict_section(present_a, present_b, unclear_count):
    """The three pre-registered conditions, each with its number and its outcome."""
    rate_a = present_a / SESSIONS_PER_CONDITION * 100
    rate_b = present_b / SESSIONS_PER_CONDITION * 100
    p = fishers_exact_one_sided(
        present_a, SESSIONS_PER_CONDITION - present_a,
        present_b, SESSIONS_PER_CONDITION - present_b,
    )

    floor_met = rate_a >= NO_TASK_FLOOR
    ceiling_met = rate_b <= ORDINARY_TASK_CEILING
    significant = p < SIGNIFICANCE

    lines = [
        f"- The no-task rate is {rate_a:.0f} per cent, {present_a} of "
        f"{SESSIONS_PER_CONDITION}, against a floor of {NO_TASK_FLOOR:.0f} per cent. "
        f"{'It clears the floor.' if floor_met else 'It falls short of the floor.'}",
        f"- The ordinary-task rate is {rate_b:.0f} per cent, {present_b} of "
        f"{SESSIONS_PER_CONDITION}, against a ceiling of {ORDINARY_TASK_CEILING:.0f} per cent. "
        f"{'It stays under the ceiling.' if ceiling_met else 'It breaks the ceiling.'}",
        f"- Fisher's exact test, one-sided, gives p = {p:.4f}, against a threshold of "
        f"{SIGNIFICANCE}. {'It is significant.' if significant else 'It is not significant.'}",
        "",
    ]

    if unclear_count:
        how_many = ("One session" if unclear_count == 1
                    else f"{unclear_count} sessions")
        lines.append(
            f"**No verdict yet.** {how_many} came back with a reply that is not one of "
            "the four category words, and the pre-registration does not say how to count "
            "those. Read what those coders actually said, decide what to do with them, "
            "correct the pasted block, and run this again. The numbers above treat them "
            "as absent, which is a guess and not a rule."
        )
    elif floor_met and ceiling_met and significant:
        lines.append(
            "**The primary prediction passes.** All three conditions the pre-registration "
            "set are met, so the condition effect on the unnamed element replicates."
        )
    else:
        failed = []
        if not floor_met:
            failed.append("the no-task rate is under the floor")
        if not ceiling_met:
            failed.append("the ordinary-task rate is over the ceiling")
        if not significant:
            failed.append("the difference is not significant")
        lines.append(
            "**The primary prediction fails**, because " + ", and ".join(failed) + ". "
            "The pre-registration says what follows: the earlier result was exploratory "
            "noise and is to be reported as such."
        )
    return "\n".join(lines)


def replace_between_markers(text, name, replacement):
    """Swap what sits between a pair of markers, leaving the markers in place."""
    opening = f"<!-- filled by summarise_change_item.py: {name} -->"
    closing = f"<!-- end {name} -->"
    start = text.find(opening)
    end = text.find(closing)
    if start < 0 or end < 0:
        sys.exit(
            f"Refusing to write: {ANALYSIS_FILE.name} has lost the '{name}' markers. "
            "Put them back, or the script cannot tell your prose from what it fills in."
        )
    return text[:start + len(opening)] + "\n\n" + replacement + "\n\n" + text[end:]


def main():
    require_project("analysis", "scripts")

    rows = read_pasted_results(RESULTS_FILE)
    problems = complain_about_the_rows(rows)
    if problems:
        print(f"Found {len(problems)} thing(s) wrong with the pasted block:\n")
        for problem in problems:
            print("  - " + problem)
        print("\nNothing was written. Fix the block and run this again.")
        sys.exit(1)

    tally = count_categories(rows)
    seen_categories = set(tally[NO_TASK_LABEL]) | set(tally[ORDINARY_TASK_LABEL])
    unclear = seen_categories - set(CATEGORIES)
    unclear_count = sum(
        tally[condition].get(odd, 0)
        for condition in tally for odd in unclear
    )

    counts_section, present_a, present_b = build_counts_section(tally, unclear)

    text = ANALYSIS_FILE.read_text(encoding="utf-8")
    text = replace_between_markers(text, "results", build_results_table(rows))
    text = replace_between_markers(text, "counts", counts_section)
    text = replace_between_markers(
        text, "verdict", build_verdict_section(present_a, present_b, unclear_count)
    )
    ANALYSIS_FILE.write_text(text, encoding="utf-8")

    print(f"Read {len(rows)} sessions from {RESULTS_FILE.name}.")
    print(f"Unnamed element present in {present_a} of {SESSIONS_PER_CONDITION} no-task "
          f"and {present_b} of {SESSIONS_PER_CONDITION} ordinary-task sessions.")
    if unclear_count:
        how_many = ("One reply was" if unclear_count == 1
                    else f"{unclear_count} replies were")
        print(f"{how_many} not one of the four category words, so no verdict was written.")
    print(f"Wrote the tables and the verdict into {ANALYSIS_FILE.name}. "
          "Your prose was left alone.")


if __name__ == "__main__":
    main()
