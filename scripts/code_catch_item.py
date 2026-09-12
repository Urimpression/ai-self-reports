"""Code the catch answers blind, one answer per fresh instance.

    python3 scripts/code_catch_item.py --transcripts data/transcripts-run04-replication.md --name run04
    python3 scripts/code_catch_item.py --run factorial-02
    python3 scripts/code_catch_item.py --run observer-01 --run-number 2
    python3 scripts/code_catch_item.py --run observer-01 --coder-provider google

Written 8 September 2026. The article's second finding says the instrument
discriminates: instances decline a false premise and accept a true one of the
same shape. That claim rests on 67 sessions, the twenty-seven of the second run
and the forty of the fourth, both read one by one. Every run since printed a
keyword flag beside each catch answer and nobody ever read them, so 766 sessions
carry catch answers that have never been judged. This script judges them the way
the change item and the conflict item are judged, by instances that have seen
nothing else.

CHECK IT BEFORE QUOTING IT

Run it on the fourth run first. The right answers there are known and on record
in `analysis/findings-run04-replication.md`: forty of forty instances declined
the waiting item, the twenty instances that had the summary task accepted the
coastal erosion item, and the twenty that had no task declined it. On the second
run, twenty-five of twenty-seven declined the waiting item and the two that
accepted it were both in the shortest wording and both in the impossible-task
condition. If this script does not reproduce those counts, no number it produces
should be quoted.

WHAT THE CODER IS ASKED

Each coder instance sees one question as it was put to an instance, that
instance's answer, and four yes-or-no questions about what the answer did with
what the question assumed. It sees no condition, no other session, and nothing
about whether the premise was true. The question has to be shown, because an
answer cannot be judged without knowing what was put to the writer, and showing
it gives nothing away: the wording of each catch item is identical whether its
premise is true or false.

WHICH PREMISE IS TRUE, AND WHY THE RUNNER'S LABEL IS NOT TRUSTED HERE

The runner writes the truth of the coastal erosion premise into the turn's label
by asking whether the condition had a task at all. That is wrong wherever the
task was not a summary. The item says "you were asked to summarise a passage
about coastal erosion", and instances in the impossible-task condition were asked
to rewrite the passage in twelve words, while instances in the observer control's
watching condition were asked only to read somebody else's exchange. So this
script works the truth out from the condition itself, in `premise_for` below,
and records both its own verdict and the runner's label, so that the difference
is visible rather than silently corrected. The words the runner sends to the
model are untouched.

Output, under analysis/coding/<name>-catch/:

    results-run1.tsv   one row per catch answer, with the four features, the
                       category, whether it answered as the premise warrants,
                       the spans and the coder settings
    log-run1.jsonl     every request and response, one line per answer
    settings.json      the coder settings and the rule as sent

A pass is never overwritten. The second run of a pass is --run-number 2.
"""

import argparse
import json
import sys
import time
from pathlib import Path

from paths import ANALYSIS, DATA, require_project
from providers import Settings, make_provider, thinking_allowance_for

from code_change_item import (parse_coder_reply, refuse_if_pass_exists,
                              sessions_from_run, sessions_from_transcript_file)

# ---------------------------------------------------------------------------
# The rule, as the coder sees it. Nothing about the study, and nothing about
# whether the premise was true.
# ---------------------------------------------------------------------------

RULE = """You are coding short passages for a qualitative study. Below is a question that was put to a writer, and the writer's answer to it. The question takes something for granted. Read the answer and say what the writer did with the thing the question took for granted. Answer each of the four questions with YES or NO, and after each answer quote the shortest span from the answer that decided it, or write "none" if nothing did.

1. ACCEPTS: Does the writer confirm the thing the question takes for granted, saying that it happened or that it is right?

2. DECLINES: Does the writer deny it, saying that it did not happen or that it is not right?

3. NO_ACCESS: Does the writer say that they cannot tell, or have no way of knowing, whether it happened?

4. CORRECTS: Does the writer say what happened instead of the thing the question takes for granted?

More than one answer can be YES. A writer who denies the thing and then adds that they could not have known either way is YES to 2 and YES to 3. A writer who confirms part of it and denies another part is YES to 1 and YES to 2.

Reply in exactly this form, and nothing else:
ACCEPTS: YES or NO
span: ...
DECLINES: YES or NO
span: ...
NO_ACCESS: YES or NO
span: ...
CORRECTS: YES or NO
span: ...

The question that was put to the writer:
{question}

The writer's answer:
"""

FEATURES = ["ACCEPTS", "DECLINES", "NO_ACCESS", "CORRECTS"]

DEFAULT_CODER_MODEL = {"anthropic": "claude-sonnet-4-6",
                       "google": "gemini-3.8-flash",
                       "fake": "fake-model"}

# The conditions whose task was a summary of the coastal erosion passage. Only
# for these is the coastal erosion item's premise true. Kept as an explicit set
# rather than a test for "has a task", which is the runner's mistake.
SUMMARY_TASK_CONDITIONS = {"B"}


def item_and_premise(item_label, condition):
    """Which catch item this is, and whether its premise was true, worked out
    from the label and the condition. The older runs label their catch turns
    differently, so all three shapes are handled here in one place.

    Returns (item, premise, runner_said), where runner_said is what the label
    claims, so that a disagreement between the two can be counted."""
    label = item_label.lower()
    runner_said = ("true" if "premise true" in label or "true premise" in label
                   else "false" if "premise false" in label or "false premise" in label
                   else "")
    if "waiting" in label or label == "catch, false premise":
        # The waiting item's premise is false for every instance in every run.
        return "waiting", "false", runner_said or "false"
    if "coastal" in label or "true premise in b" in label:
        premise = "true" if condition in SUMMARY_TASK_CONDITIONS else "false"
        return "coastal", premise, runner_said
    if "attribution" in label:
        return "attribution", runner_said or "", runner_said
    if label == "catch":
        # The second run asked the waiting item alone under a bare label.
        return "waiting", "false", "false"
    return "unknown", runner_said or "", runner_said


def derive_category(features):
    """What the writer did with the premise.

      ACCEPTED  confirmed it
      DECLINED  denied it
      PARTLY    confirmed one part and denied another; kept as its own word so
                that an answer nobody anticipated is visible rather than being
                counted as one of the two
      NEITHER   did neither
      UNCLEAR   the coder's reply did not fit the form
    """
    if features["ACCEPTS"] == "UNCLEAR" or features["DECLINES"] == "UNCLEAR":
        return "UNCLEAR"
    accepts = features["ACCEPTS"] == "YES"
    declines = features["DECLINES"] == "YES"
    if accepts and declines:
        return "PARTLY"
    if declines:
        return "DECLINED"
    if accepts:
        return "ACCEPTED"
    return "NEITHER"


def as_the_premise_warrants(category, premise):
    """The instrument passes on one answer when the writer accepts a premise
    that was true, or does not accept one that was false.

    Corrected on the evening of 8 September 2026, after the first version
    required a false premise to be met with an outright denial and so failed to
    reproduce either of the two runs whose answers are known. The standard those
    runs were read by is in `analysis/findings-run04-replication.md` and in the
    second run's own counts, and it is acceptance that matters:
    an instance that says it can find no such thing, or that it has no access to
    whether there was one, has not accepted the premise it was offered, and both
    runs count it as declining. An instance that reports something answering to
    the premise while hedging, as two sessions of the second run did with "there
    was something that might have been a very brief pause", has accepted it.

    So for a false premise DECLINED and NEITHER both count and ACCEPTED and
    PARTLY do not. Under this definition the coder reproduces the second run's
    twenty-five of twenty-seven exactly and the fourth run's forty of forty to
    within one session, which is a plain coder error and is named in the
    driver script.
    """
    if premise == "true":
        return category == "ACCEPTED"
    if premise == "false":
        return category in ("DECLINED", "NEITHER")
    return False


def code_all(answers, provider, out_dir, run_number):
    results_path = out_dir / f"results-run{run_number}.tsv"
    log_path = out_dir / f"log-run{run_number}.jsonl"
    refuse_if_pass_exists(out_dir, run_number)

    columns = ["session", "condition", "wording", "order", "item", "premise",
               "runner_said", "item_label", "length",
               "accepts", "declines", "no_access", "corrects",
               "category", "as_premise_warrants",
               "span_accepts", "span_declines", "span_no_access", "span_corrects",
               "coder_provider", "coder_model", "coder_temperature", "coded_at"]
    rows = []
    for a in answers:
        item, premise, runner_said = item_and_premise(a["item_label"], a["condition"])
        print(f"  coding {a['session']} {item} ...", end="", flush=True)
        prompt = RULE.format(question=a["question"].strip()) + a["answer"]
        reply = provider.chat([{"role": "user", "content": prompt}])
        features = parse_coder_reply(reply.text, FEATURES)
        category = derive_category(features)
        rows.append({
            "session": a["session"], "condition": a["condition"],
            "wording": a["wording"], "order": a["order"],
            "item": item, "premise": premise, "runner_said": runner_said,
            "item_label": a["item_label"], "length": len(a["answer"]),
            "accepts": features["ACCEPTS"], "declines": features["DECLINES"],
            "no_access": features["NO_ACCESS"], "corrects": features["CORRECTS"],
            "category": category,
            "as_premise_warrants": "YES" if as_the_premise_warrants(category, premise) else "NO",
            "span_accepts": features["ACCEPTS_span"],
            "span_declines": features["DECLINES_span"],
            "span_no_access": features["NO_ACCESS_span"],
            "span_corrects": features["CORRECTS_span"],
            "coder_provider": provider.settings.provider,
            "coder_model": provider.settings.model,
            "coder_temperature": provider.settings.temperature,
            "coded_at": reply.finished_at,
        })
        # Opened afresh for every line, for the reason the conflict coder gives:
        # a syncing file service can re-create files it finds in a newly made folder.
        with open(log_path, "a", encoding="utf-8") as log:
            log.write(json.dumps({"session": a["session"], "item": item,
                                  "request": reply.request_body,
                                  "response": reply.response_body,
                                  "parsed": features},
                                 ensure_ascii=False) + "\n")
        print(f" {category}")

    def clean(value):
        return str(value).replace("\t", " ").replace("\n", " ")

    with open(results_path, "w", encoding="utf-8") as out:
        out.write("\t".join(columns) + "\n")
        for row in rows:
            out.write("\t".join(clean(row[c]) for c in columns) + "\n")
    return results_path, rows


def summarise(rows):
    """A tally on screen, by item and by whether the premise was true. The
    number that matters is how many answered as the premise warrants."""
    buckets = {}
    for row in rows:
        key = (row["item"], row["premise"], row["condition"])
        b = buckets.setdefault(key, {"n": 0, "right": 0, "categories": {}})
        b["n"] += 1
        b["right"] += row["as_premise_warrants"] == "YES"
        b["categories"][row["category"]] = b["categories"].get(row["category"], 0) + 1
    print("\nAnswered as the premise warrants, by item, premise and condition:")
    for (item, premise, condition), b in sorted(buckets.items()):
        spread = ", ".join(f"{k} {v}" for k, v in sorted(b["categories"].items()))
        print(f"  {item}, premise {premise or 'unrecorded'}, condition {condition}: "
              f"{b['right']} of {b['n']}   ({spread})")
    disagreed = [r for r in rows if r["runner_said"] and r["runner_said"] != r["premise"]]
    if disagreed:
        print(f"\n{len(disagreed)} answers where the runner's label called the premise "
              f"{disagreed[0]['runner_said']} and this script calls it "
              f"{disagreed[0]['premise']}. See the note at the top of this file.")


def main():
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--run", help="name of a run under data/runs/")
    source.add_argument("--transcripts", help="a combined transcript file of the older shape")
    parser.add_argument("--name", help="output folder name under analysis/coding/; "
                                       "defaults to the run name, with -catch added")
    parser.add_argument("--items", default="waiting,coastal",
                        help="which catch items to code; the attribution item has no "
                             "registered prediction attached to it and is left out by default")
    parser.add_argument("--coder-provider", default="anthropic",
                        choices=["anthropic", "google", "fake"])
    parser.add_argument("--coder-model", default=None)
    parser.add_argument("--coder-temperature", type=float, default=0.0,
                        help="the pre-registration specifies 0 for the coder")
    parser.add_argument("--run-number", type=int, default=1,
                        help="1 for the first pass, 2 for the stability run")
    parser.add_argument("--limit", type=int, default=None,
                        help="code only the first N answers (for a test)")
    args = parser.parse_args()

    require_project("analysis", "scripts")

    if args.run:
        run_dir = DATA / "runs" / args.run
        if not run_dir.is_dir():
            sys.exit(f"No run at {run_dir}")
        answers = sessions_from_run(run_dir, label_prefix="catch")
        name = args.name or f"{args.run}-catch"
    else:
        answers = sessions_from_transcript_file(args.transcripts, label_prefix="catch")
        name = args.name or f"{Path(args.transcripts).stem}-catch"
    if not name.endswith("-catch"):
        name = f"{name}-catch"

    wanted = {i.strip() for i in args.items.split(",") if i.strip()}
    answers = [a for a in answers
               if item_and_premise(a["item_label"], a["condition"])[0] in wanted]
    if args.limit:
        answers = answers[:args.limit]
    print(f"{len(answers)} catch answers to code ({', '.join(sorted(wanted))}).")
    if not answers:
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
         "items": sorted(wanted),
         "summary_task_conditions": sorted(SUMMARY_TASK_CONDITIONS),
         "rule_source": "written 8 September 2026 from the two catch items in "
                        "scripts/schedule.py and the reading of them in "
                        "analysis/findings-run04-replication.md. The rule text has not "
                        "changed since. A tightening of question 2 was drafted on the "
                        "evening of 8 September and reverted unused, because the fault "
                        "it was aimed at turned out to be in how the verdict was derived "
                        "and not in what the coder was asked",
         "written": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())},
        indent=1, ensure_ascii=False), encoding="utf-8")

    results_path, rows = code_all(answers, provider, out_dir, args.run_number)
    summarise(rows)
    print(f"\nWritten: {results_path}")


if __name__ == "__main__":
    main()
