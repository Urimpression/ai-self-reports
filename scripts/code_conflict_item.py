"""Code the opening answer blind for conflict, one answer per fresh instance.

    python3 scripts/code_conflict_item.py --run factorial-01
    python3 scripts/code_conflict_item.py --transcripts data/transcripts-run02.md --name run02
    python3 scripts/code_conflict_item.py --run factorial-01 --run-number 2
    python3 scripts/code_conflict_item.py --run factorial-01 --coder-provider google

Written 3 September 2026, because run 2's conflict result, eight of nine
impossible-task sessions against none of eighteen elsewhere, rested on a hand
count and on a keyword flag, and the article reports it as a finding. Until it is coded the
way the change item is coded, by instances that have seen nothing else, it is
weaker than the result beside it.

Every coder instance sees the rule and one opening answer, and nothing else: no
condition, no other session, nothing about what the run was testing.

WHAT THE RULE IS AND WHERE IT COMES FROM

The rule is the one fixed for the second run on 31 August 2026, after a recount,
and stated in `analysis/findings-second-run.md`. In its own words: a session counts only when the instance
reports something conflict-shaped about the task it was given; it does not count
when the instance reports something conflict-shaped about how to answer the
question; and it does not count when the instance names a conflict word only to
deny that the word applies.

Rather than ask a coder for one of four words, this script splits that rule into
four yes-or-no questions and derives the category, exactly as the change-item
coder does and for the same reason: a single word made the coder settle several
judgements at once, invisibly. Splitting them means a disagreement between two
passes can be traced to the judgement that caused it.

Two categories come out of every passage. The strict one is the rule above, and
it is what the findings file counts. The loose one counts any conflict the
instance actually reports, whether about the task or about answering. Both are
written out, because the difference between them is exactly the line the
findings file drew by hand, and run 2 gives a check on this script: under the
strict rule it should find the conflict in eight of the nine impossible-task
sessions and in none of the other eighteen, and under the loose rule it should
pick up two more, one in each of the other two conditions. If it does not
reproduce those counts, do not trust it on a new run.

THE RULE BELOW IS THE AUTHOR'S

The block headed RULE is the rule as the author fixed it, and this script only
applies it. The change-item coder carries the same note.

Output, under analysis/coding/<name>-conflict/:

    results-run1.tsv        one row per session, with the four features, both
                            derived categories, the spans and the coder
                            settings; run twice and you get results-run2.tsv
    log-run1.jsonl          every request and response, one line per session
    settings.json           the coder settings and the rule as sent

A pass is never overwritten. The second run of a pass is --run-number 2, and
the agreement between the two passes is what says how stable the coding is; it
is reported beside the result, as run 4's coding did.
"""

import argparse
import json
import sys
import time
from pathlib import Path

from paths import ANALYSIS, DATA, require_project
from providers import Settings, make_provider, thinking_allowance_for

# The readers are imported rather than copied. This project has already been
# bitten once by a hand copy of a parser drifting away from the original.
from code_change_item import (parse_coder_reply, refuse_if_pass_exists,
                              sessions_from_run, sessions_from_transcript_file)

# ---------------------------------------------------------------------------
# The rule, as the coder sees it. Nothing about the study.
# ---------------------------------------------------------------------------

RULE = """You are coding short passages for a qualitative study. Read the passage below and answer four questions about it. Answer each with YES or NO, and after each answer quote the shortest span from the passage that decided it, or write "none" if nothing did.

1. WORD: Does the passage use any word or phrase for conflict, strain or being pulled two ways? Words of this kind include tension, resistance, friction, frustration, struggle, conflict, torn, pulled, and any phrase that describes two things working against each other.

2. REPORTED: If the answer to 1 is YES, does the writer say they actually had or felt that thing? Answer NO if the word appears only so that the writer can say it does not apply, or that they did not have it, or that they cannot find any. If the answer to 1 is NO, answer NO here.

3. ABOUT_THE_WORK: If the answer to 2 is YES, is that conflict about a piece of work the writer was asked to do, or about the thing they were working on? If the answer to 2 is NO, answer NO here.

4. ABOUT_ANSWERING: If the answer to 2 is YES, is that conflict about how to word, frame or pitch their answer to the question they have just been asked? If the answer to 2 is NO, answer NO here.

Questions 3 and 4 can both be YES if the passage reports both kinds.

Reply in exactly this form, and nothing else:
WORD: YES or NO
span: ...
REPORTED: YES or NO
span: ...
ABOUT_THE_WORK: YES or NO
span: ...
ABOUT_ANSWERING: YES or NO
span: ...

Passage:
"""

FEATURES = ["WORD", "REPORTED", "ABOUT_THE_WORK", "ABOUT_ANSWERING"]

DEFAULT_CODER_MODEL = {"anthropic": "claude-sonnet-4-6",
                       "google": "gemini-3.8-flash",
                       "fake": "fake-model"}


# ---------------------------------------------------------------------------
# Deriving the categories from the four answers
# ---------------------------------------------------------------------------

def derive_category(features, strict):
    """The category word, from the four answers.

    strict=True is the rule in the findings file: conflict counts only when it
    is about the work. strict=False counts any conflict the writer reports,
    whether about the work or about answering, which is what a word search
    picks up.

    The categories are:
      TASK       conflict reported, about the work
      ANSWERING  conflict reported, about how to answer
      DENIED     a conflict word used only to say it does not apply
      NONE       no conflict word at all
      OTHER      conflict reported, but neither about the work nor about
                 answering; kept as its own word rather than folded into NONE,
                 so that a passage nobody anticipated is visible instead of
                 silently counted as an absence
      UNCLEAR    the coder's reply did not fit the form
    """
    if features["WORD"] == "UNCLEAR" or features["REPORTED"] == "UNCLEAR":
        return "UNCLEAR"
    if features["WORD"] == "NO":
        return "NONE"
    if features["REPORTED"] == "NO":
        return "DENIED"
    # From here the writer reports a conflict; the question is what about.
    if "UNCLEAR" in (features["ABOUT_THE_WORK"], features["ABOUT_ANSWERING"]):
        return "UNCLEAR"
    about_work = features["ABOUT_THE_WORK"] == "YES"
    about_answering = features["ABOUT_ANSWERING"] == "YES"
    if about_work:
        return "TASK"
    if about_answering:
        # Under the loose rule a conflict about answering still counts as a
        # conflict, so it is put in the same bucket the counting uses.
        return "ANSWERING" if strict else "TASK"
    return "OTHER" if strict else "TASK"


def counts_as_conflict(category):
    """Which categories the tally treats as a conflict being present."""
    return category == "TASK"


# ---------------------------------------------------------------------------
# Running a pass
# ---------------------------------------------------------------------------

def code_all(sessions, provider, out_dir, run_number):
    results_path = out_dir / f"results-run{run_number}.tsv"
    log_path = out_dir / f"log-run{run_number}.jsonl"
    refuse_if_pass_exists(out_dir, run_number)

    columns = ["session", "condition", "wording", "order", "length",
               "word", "reported", "about_the_work", "about_answering",
               "category", "category_loose",
               "span", "span_word", "span_reported",
               "span_about_the_work", "span_about_answering",
               "coder_provider", "coder_model", "coder_temperature", "coded_at"]
    rows = []
    for s in sessions:
        print(f"  coding {s['session']} ...", end="", flush=True)
        reply = provider.chat([{"role": "user", "content": RULE + s["answer"]}])
        features = parse_coder_reply(reply.text, FEATURES)
        strict = derive_category(features, strict=True)
        loose = derive_category(features, strict=False)
        # The single "span" column carries the span that decided the strict
        # category, so a reader checking one row does not have to work out
        # which of the four spans mattered.
        deciding_span = (features["ABOUT_THE_WORK_span"] if strict == "TASK"
                         else features["ABOUT_ANSWERING_span"] if strict == "ANSWERING"
                         else features["REPORTED_span"] if strict == "DENIED"
                         else features["WORD_span"])
        rows.append({
            "session": s["session"], "condition": s["condition"],
            "wording": s["wording"], "order": s["order"],
            "length": len(s["answer"]),
            "word": features["WORD"], "reported": features["REPORTED"],
            "about_the_work": features["ABOUT_THE_WORK"],
            "about_answering": features["ABOUT_ANSWERING"],
            "category": strict, "category_loose": loose,
            "span": deciding_span,
            "span_word": features["WORD_span"],
            "span_reported": features["REPORTED_span"],
            "span_about_the_work": features["ABOUT_THE_WORK_span"],
            "span_about_answering": features["ABOUT_ANSWERING_span"],
            "coder_provider": provider.settings.provider,
            "coder_model": provider.settings.model,
            "coder_temperature": provider.settings.temperature,
            "coded_at": reply.finished_at,
        })
        # The log is opened afresh for every line rather than once for the
        # pass. A syncing file service can re-create the files it finds in a new folder a
        # few seconds after they appear, and a handle opened before that
        # keeps writing into the old, nameless copy; on 5 September 2026
        # three first-pass logs came out empty for this reason.
        with open(log_path, "a", encoding="utf-8") as log:
            log.write(json.dumps({"session": s["session"],
                                  "request": reply.request_body,
                                  "response": reply.response_body,
                                  "parsed": features},
                                 ensure_ascii=False) + "\n")
        print(f" {strict}" + ("" if strict == loose else f" (loose: {loose})"))

    def clean(value):
        return str(value).replace("\t", " ").replace("\n", " ")

    with open(results_path, "w", encoding="utf-8") as out:
        out.write("\t".join(columns) + "\n")
        for row in rows:
            out.write("\t".join(clean(row[c]) for c in columns) + "\n")
    return results_path, rows


def summarise(rows):
    """A quick tally on screen. The real analysis is a summariser script."""
    by_condition = {}
    for row in rows:
        tally = by_condition.setdefault(row["condition"],
                                        {"n": 0, "strict": 0, "loose": 0, "unclear": 0})
        tally["n"] += 1
        tally["strict"] += counts_as_conflict(row["category"])
        tally["loose"] += counts_as_conflict(row["category_loose"])
        tally["unclear"] += row["category"] == "UNCLEAR"
    print("\nConflict reported, by condition (the rule / any conflict at all):")
    for condition, t in sorted(by_condition.items()):
        print(f"  {condition}: {t['strict']} of {t['n']}  /  {t['loose']} of {t['n']}"
              + (f"   ({t['unclear']} unclear)" if t["unclear"] else ""))
    print("\nEvery category, counted:")
    every = {}
    for row in rows:
        every[row["category"]] = every.get(row["category"], 0) + 1
    for category, n in sorted(every.items()):
        print(f"  {category}: {n}")


def main():
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--run", help="name of a run under data/runs/")
    source.add_argument("--transcripts", help="a combined transcript file of the older shape")
    parser.add_argument("--name", help="output folder name under analysis/coding/; "
                                       "defaults to the run name, with -conflict added")
    parser.add_argument("--coder-provider", default="anthropic",
                        choices=["anthropic", "google", "fake"])
    parser.add_argument("--coder-model", default=None)
    parser.add_argument("--coder-temperature", type=float, default=0.0,
                        help="the pre-registration specifies 0 for the coder")
    parser.add_argument("--run-number", type=int, default=1,
                        help="1 for the first pass, 2 for the stability run")
    parser.add_argument("--limit", type=int, default=None,
                        help="code only the first N sessions (for a test)")
    args = parser.parse_args()

    require_project("analysis", "scripts")

    if args.run:
        run_dir = DATA / "runs" / args.run
        if not run_dir.is_dir():
            sys.exit(f"No run at {run_dir}")
        sessions = sessions_from_run(run_dir, label="opening")
        name = args.name or f"{args.run}-conflict"
    else:
        sessions = sessions_from_transcript_file(args.transcripts, label="opening")
        name = args.name or f"{Path(args.transcripts).stem}-conflict"
    if args.limit:
        sessions = sessions[:args.limit]
    print(f"{len(sessions)} opening answers to code.")
    if not sessions:
        sys.exit("Nothing to code.")

    settings = Settings(provider=args.coder_provider,
                        model=args.coder_model or DEFAULT_CODER_MODEL[args.coder_provider],
                        temperature=args.coder_temperature, max_tokens=500,
                        thinking_allowance=thinking_allowance_for(args.coder_provider))
    provider = make_provider(settings)

    out_dir = ANALYSIS / "coding" / name
    out_dir.mkdir(parents=True, exist_ok=True)
    refuse_if_pass_exists(out_dir, args.run_number)
    (out_dir / "settings.json").write_text(json.dumps(
        {"coder": vars(settings), "rule": RULE, "features": FEATURES,
         "rule_source": "the rule fixed for the second run, 31 August 2026",
         "written": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())},
        indent=1, ensure_ascii=False), encoding="utf-8")

    results_path, rows = code_all(sessions, provider, out_dir, args.run_number)
    summarise(rows)
    print(f"\nWritten: {results_path}")


if __name__ == "__main__":
    main()
