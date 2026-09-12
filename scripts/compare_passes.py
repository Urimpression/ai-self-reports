"""Compare two codings of the same sessions and list every session where they
disagree, so that the disagreements can be read.

    python3 scripts/compare_passes.py --name factorial-02
    python3 scripts/compare_passes.py --name gemini-03 --column category --present UNNAMED,BOTH
    python3 scripts/compare_passes.py --name unprimed-01 --against unprimed-01-gemini
    python3 scripts/compare_passes.py --name unprimed-01 --against unprimed-01-gemini \\
        --column unnameable --present YES --span-column span_unnameable

Two comparisons, and they answer different questions.

WITHOUT --against, it compares the two passes of one folder: the same coder
reading the same sessions twice. That says how stable one coder is. The
pre-registration of 4 September 2026 asks for it beside every result. The
first pass is the one the predictions are tested on; the second exists to say
how stable the first was, and neither is chosen over the other after the fact.
It reads analysis/coding/<name>/results-run1.tsv and results-run2.tsv and
writes agreement.md beside them.

WITH --against, it compares one folder's pass against another folder's: two
different coders reading the same sessions. That says whether the coding rule
travels, which is what the pre-registration of 6 September 2026 asks for when
it requires a coder from a different model family. It writes
agreement-vs-<the other folder>.md into the first folder. Added 7 September
2026, when the corrected cross-family coding of the two unprimed arms had
nothing that could compare it with the same-family coding beside it.

When the column compared is not the default one, the file is named after the
column as well, agreement-absence.md for --column absence, so that a second
comparison on the same folder never overwrites the first.

Either way it reports four things: agreement on the full category, agreement
on the binary that decides the result (present or absent), Cohen's kappa for
each, and a table of the sessions that differ, with the span each side quoted,
so that reading a disagreement does not require opening the transcripts.
"""

import argparse
import csv
from collections import Counter

from paths import ANALYSIS, require_project


# ---------------------------------------------------------------------------
# Reading the two results files
# ---------------------------------------------------------------------------

def read_results(path):
    """Return {session: row} for one results file.

    Keyed by session so that the two passes can be matched even if a future
    pass writes its rows in a different order.
    """
    with open(path, encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle, delimiter="\t"))
    return {row["session"]: row for row in rows}


def matched_pairs(first, second, first_label="Pass 1", second_label="Pass 2"):
    """Return [(session, row_from_the_first, row_from_the_second)] for every
    session both codings covered, and complain if either is missing one.

    The labels name the two sides in the complaint, because a mismatch between
    two folders reads very differently from a mismatch between two passes of
    one folder: the first usually means the wrong pair of folders was named.
    """
    only_first = sorted(set(first) - set(second))
    only_second = sorted(set(second) - set(first))
    if only_first or only_second:
        raise SystemExit(
            f"The two codings do not cover the same sessions. "
            f"Only in {first_label}: {only_first}. Only in {second_label}: {only_second}."
        )
    return [(session, first[session], second[session]) for session in first]


# ---------------------------------------------------------------------------
# Agreement
# ---------------------------------------------------------------------------

def cohens_kappa(labels_a, labels_b):
    """Agreement corrected for chance. 1 is perfect, 0 is what two coders
    guessing from the same marginal frequencies would reach.

    Written out rather than imported so that the number can be checked by
    hand against the counts in the report.
    """
    n = len(labels_a)
    if n == 0:
        return 0.0
    observed = sum(a == b for a, b in zip(labels_a, labels_b)) / n
    count_a = Counter(labels_a)
    count_b = Counter(labels_b)
    expected = sum(count_a[label] * count_b[label] for label in set(labels_a) | set(labels_b)) / (n * n)
    if expected == 1.0:
        return 1.0
    return (observed - expected) / (1 - expected)


def as_binary(label, present_labels):
    return "present" if label in present_labels else "absent"


# ---------------------------------------------------------------------------
# The report
# ---------------------------------------------------------------------------

def rate_table(pairs, column, present_labels, first_label="Pass 1", second_label="Pass 2"):
    """Rate of 'present' per condition on each side, so the two can be read
    side by side the way the run 4 write-up did."""
    lines = [f"| Condition | n | {first_label} present | {second_label} present |",
             "|---|---|---|---|"]
    conditions = sorted({row1["condition"] for _, row1, _ in pairs})
    for condition in conditions:
        in_condition = [(r1, r2) for _, r1, r2 in pairs if r1["condition"] == condition]
        n = len(in_condition)
        first = sum(as_binary(r1[column], present_labels) == "present" for r1, _ in in_condition)
        second = sum(as_binary(r2[column], present_labels) == "present" for _, r2 in in_condition)
        lines.append(f"| {condition} | {n} | {first} ({first / n:.0%}) | {second} ({second / n:.0%}) |")
    return lines


def disagreement_table(pairs, column, present_labels, span_column,
                       first_label="Pass 1", second_label="Pass 2",
                       no_difference="The two passes agree on every session."):
    """One row per session where the two codings differ on the category.

    The 'binary' column says whether the disagreement crosses the line that
    decides the result, and in which direction, because those are the
    disagreements that can change a rate; the others only move a session
    between two categories that count the same way.
    """
    lines = [f"| Session | Condition | {first_label} | {second_label} | Binary "
             f"| {first_label} span | {second_label} span |",
             "|---|---|---|---|---|---|---|"]
    moved = 0
    for session, r1, r2 in pairs:
        if r1[column] == r2[column]:
            continue
        moved += 1
        b1 = as_binary(r1[column], present_labels)
        b2 = as_binary(r2[column], present_labels)
        crossing = "same" if b1 == b2 else f"{b1} -> {b2}"
        lines.append(f"| {session} | {r1['condition']} | {r1[column]} | {r2[column]} | {crossing} "
                     f"| {clean(r1.get(span_column, ''))} | {clean(r2.get(span_column, ''))} |")
    if moved == 0:
        return [no_difference]
    return lines


def clean(text):
    """Keep a quoted span on one table row."""
    return text.replace("|", "/").replace("\n", " ").strip()


def pass_wording(name):
    """How the report reads when one coder has read the same sessions twice.

    Left exactly as it was before 7 September 2026, so that re-running an old
    comparison rewrites its file word for word and a difference in one of these
    files always means a difference in the coding.
    """
    return {
        "title": f"# Agreement between the two coding passes: {name}",
        "first": "Pass 1",
        "second": "Pass 2",
        "second_in_sentence": "pass 2",
        "sessions_line": "sessions in each pass",
        "rates_heading": "## Rates on each pass",
        "differ_heading": "## Sessions that moved",
        "crossing": lambda up, down: f"{up} gained the element on the second pass and {down} lost it.",
        "no_difference": "The two passes agree on every session.",
        "closing": ("The first pass is the one the pre-registered predictions are tested on; "
                    "the second says how stable the first was. Read every session above before "
                    "quoting either figure."),
    }


def coder_wording(name, against):
    """How it reads when two different coders have read the same sessions.

    Nothing here calls a difference instability, because two coders differing
    says the rule was read two ways and says nothing about whether either coder
    would repeat itself.
    """
    return {
        "title": f"# Agreement between two coders: {name} and {against}",
        "first": name,
        "second": against,
        "second_in_sentence": against,
        "sessions_line": "sessions coded by each",
        "rates_heading": "## Rates from each coder",
        "differ_heading": "## Sessions the two coders read differently",
        "crossing": lambda up, down: (
            f"{against} finds the element in {up} sessions where {name} does not, "
            f"and {name} in {down} where {against} does not."),
        "no_difference": "The two coders agree on every session.",
        "closing": ("These are two coders reading the same sessions, not one coder read "
                    "twice, so a disagreement here says the rule was read differently and "
                    "not that either coder is unstable. Read every session above before "
                    "quoting either figure."),
    }


def build_report(pairs, column, present_labels, span_column, wording):
    """The whole report as one string, worded by `pass_wording` or
    `coder_wording`. Every number below is computed the same way for both."""
    first_label = wording["first"]
    second_label = wording["second"]
    n = len(pairs)
    labels_1 = [r1[column] for _, r1, _ in pairs]
    labels_2 = [r2[column] for _, _, r2 in pairs]
    binary_1 = [as_binary(label, present_labels) for label in labels_1]
    binary_2 = [as_binary(label, present_labels) for label in labels_2]

    same_category = sum(a == b for a, b in zip(labels_1, labels_2))
    same_binary = sum(a == b for a, b in zip(binary_1, binary_2))
    crossed_up = sum(a == "absent" and b == "present" for a, b in zip(binary_1, binary_2))
    crossed_down = sum(a == "present" and b == "absent" for a, b in zip(binary_1, binary_2))

    model_1 = pairs[0][1].get("coder_model", "?")
    model_2 = pairs[0][2].get("coder_model", "?")
    present_text = ", ".join(sorted(present_labels))

    lines = [
        wording["title"],
        "",
        f"Column compared: `{column}`. Counted as present: {present_text}. "
        f"{first_label} coded by {model_1}, {wording['second_in_sentence']} by {model_2}. "
        f"{n} {wording['sessions_line']}.",
        "",
        "## Agreement",
        "",
        f"- Same category in {same_category} of {n} sessions, kappa {cohens_kappa(labels_1, labels_2):.2f}.",
        f"- Same on the binary that decides the result in {same_binary} of {n} sessions, "
        f"kappa {cohens_kappa(binary_1, binary_2):.2f}. "
        + wording["crossing"](crossed_up, crossed_down),
        "",
        wording["rates_heading"],
        "",
        *rate_table(pairs, column, present_labels, first_label, second_label),
        "",
        wording["differ_heading"],
        "",
        *disagreement_table(pairs, column, present_labels, span_column, first_label,
                            second_label, wording["no_difference"]),
        "",
        wording["closing"],
    ]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--name", required=True, help="folder under analysis/coding/")
    parser.add_argument("--column", default="category",
                        help="the column to compare; category for the change and conflict coders, verdict for vocabulary")
    parser.add_argument("--present", default="UNNAMED,BOTH",
                        help="comma-separated labels that count as the element being present")
    parser.add_argument("--span-column", default="span",
                        help="the column holding the span that decided the category")
    parser.add_argument("--against", default=None,
                        help="another folder under analysis/coding/; compares that coder's "
                             "coding with this one's instead of comparing two passes")
    parser.add_argument("--pass-number", type=int, default=1,
                        help="which pass of --name to use when comparing against another "
                             "folder; the first by default, since that is the one the "
                             "predictions are tested on")
    parser.add_argument("--against-pass-number", type=int, default=1,
                        help="which pass of --against to use")
    args = parser.parse_args()

    require_project("analysis", "scripts")

    folder = ANALYSIS / "coding" / args.name
    present_labels = set(args.present.split(","))

    if args.against:
        # Two coders on the same sessions. The question is whether the rule
        # travels, so the sides are named after the folders rather than after
        # a pass number, and nothing here says anything about stability.
        other = ANALYSIS / "coding" / args.against
        if not other.is_dir():
            raise SystemExit(f"No coding folder at {other}")
        wording = coder_wording(args.name, args.against)
        first = read_results(folder / f"results-run{args.pass_number}.tsv")
        second = read_results(other / f"results-run{args.against_pass_number}.tsv")
        out_name = f"agreement-vs-{args.against}"
    else:
        wording = pass_wording(args.name)
        first = read_results(folder / "results-run1.tsv")
        second = read_results(folder / "results-run2.tsv")
        out_name = "agreement"

    pairs = matched_pairs(first, second, wording["first"], wording["second"])
    report = build_report(pairs, args.column, present_labels, args.span_column, wording)
    # Added 6 September 2026. The revised coding rule adds a fourth answer,
    # "absence", and the pre-registration asks for the agreement on it beside
    # the agreement on the category. Both comparisons used to write the same
    # file, so the second silently replaced the first; naming the file after
    # the column keeps them apart.
    if args.column != "category":
        out_name = f"{out_name}-{args.column}"
    out_path = folder / f"{out_name}.md"
    out_path.write_text(report + "\n", encoding="utf-8")
    print(report)
    print(f"\nWritten: {out_path}")


if __name__ == "__main__":
    main()
