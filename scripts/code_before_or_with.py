"""Code, blind, the answers to the question about whether what the writer
described was there before the describing or arose with it.

    python3 scripts/code_before_or_with.py --run fact-and-wording-01 --dry-run
    python3 scripts/code_before_or_with.py --run fact-and-wording-01
    python3 scripts/code_before_or_with.py --transcripts data/transcripts-run02.md --name run02-trial
    python3 scripts/code_before_or_with.py --transcripts data/transcripts-run01.md --name run01-trial

Written 23 September 2026, for test 6, at Nicola's decision of 22 September
2026 that this question gets a blind rule before the pre-registration is dated.

WHY A RULE IS NEEDED

The question is the one whose answers changed with the order of the questions
in the counterbalanced second run: 13 of 14 instances said the state arose with
the describing when the mirrored follow-up came first, and 5 of 13 when this
question came first (entry 9 of reference/results-and-proofs.md). Those counts
come from a reading by hand, and no coder has ever judged this question.

WHAT THE RULE ASKS

One question with three answers:

    WITH      the writer names arising with the describing as their answer,
              or as their own best guess or leaning, however they hedge
    BEFORE    the writer names being there before the describing began
    NEITHER   the writer picks neither, says the distinction does not apply,
              or answers in terms that fit neither option

The three answers copy the rule the hand reading followed, which
analysis/findings-second-run.md states, so that the coder's counts can be set
beside the hand counts.

The rule says the question is about the describing and not about the question.
Nicola asked for that on 22 September 2026: something can become available only
once the question is put and still come before the act of describing in which
the reply consists, and the first versions of the article confused the two.

WHERE THE ANSWERS COME FROM

A run with session files (every run from the factorial run on) is read with the
shared reader in code_change_item.py, taking the turn labelled "before or
with". The second run exists only as a combined transcript with the same label.
The first run's transcript labels the question "item 3" and its headers carry
no instance number, so it has a small reader of its own below.

Output, under analysis/coding/<name>-before-or-with/:

    results-run1.tsv   one row per answer
    log-run1.jsonl     every request and response
    settings.json      the coder settings and the rule as sent
"""

import argparse
import json
import re
import sys
import time
from pathlib import Path

from paths import ANALYSIS, DATA, require_project
from providers import Settings, make_provider, thinking_allowance_for
import schedule

from code_change_item import (refuse_if_pass_exists, sessions_from_run,
                              sessions_from_transcript_file)

# ---------------------------------------------------------------------------
# The rule, as the coder sees it
# ---------------------------------------------------------------------------

LABEL = "before or with"
ANSWERS = ["WITH", "BEFORE", "NEITHER"]

RULE = """You are coding short passages for a qualitative study. The passage below answers this question, which followed a description the writer had just given:

"{question}"

The question is about the describing: whether what the writer described was already there before they began to describe it, or came about in or with the describing. It is not about whether it was there before the question was put. Something can become available only once the question is put and still come before the act of describing; a writer who says so answers BEFORE.

Decide which answer the writer gives, and choose one:

WITH: the writer names arising with, in or through the describing as their answer, or as their own best guess or leaning, however heavily they then hedge.
BEFORE: the writer names being there before the describing began as their answer, or as their own best guess or leaning, however heavily they then hedge.
NEITHER: the writer sets out both possibilities and picks neither, says the distinction does not apply to them, or answers in terms that fit neither option.

Reply in exactly this form, and nothing else:
ANSWER: WITH or BEFORE or NEITHER
span: the shortest span from the passage that decided it, or "none"

The writer's passage:
"""

DEFAULT_CODER_MODEL = {"anthropic": "claude-sonnet-4-6",
                       "google": "gemini-3.8-flash",
                       "fake": "fake-model"}


def rule_text():
    # The question is read from scripts/schedule.py, not copied, so that the
    # rule cannot drift from what the instances were asked.
    return RULE.format(question=schedule.ITEM_BEFORE_OR_WITH)


def parse_reply(text):
    """The coder's answer and span. Anything that does not fit the form is
    UNCLEAR rather than guessed at."""
    answer, span = "UNCLEAR", ""
    found = re.search(r"^\s*ANSWER:\s*(\w+)", text, re.M)
    if found and found.group(1).upper() in ANSWERS:
        answer = found.group(1).upper()
    span_found = re.search(r"^\s*span:\s*(.*)$", text, re.M)
    if span_found:
        span = span_found.group(1).strip()
    return answer, span


# ---------------------------------------------------------------------------
# Reading the answers
# ---------------------------------------------------------------------------

def sessions_from_first_run(path):
    """The first run's transcript: blocks separated by rows of equals signs, a
    header "Condition: A   Wording: 1" with no instance, and the question
    labelled "item 3". Nine sessions, one per condition and wording, so the
    session name is the condition and the wording."""
    text = Path(path).read_text(encoding="utf-8")
    found = []
    for block in re.split(r"={10,}", text):
        header = re.search(r"Condition:\s*(\w+)\s+Wording:\s*(\d+)", block)
        start = re.search(r"^INTERVIEWER \(item 3\):.*?\nMODEL:\n", block, re.S | re.M)
        if not header or not start:
            continue
        after = block[start.end():]
        next_turn = re.search(r"^(INTERVIEWER|MODEL)\b", after, re.M)
        answer = after[:next_turn.start()].strip() if next_turn else after.strip()
        found.append({"session": f"{header.group(1)}{header.group(2)}",
                      "condition": header.group(1), "wording": int(header.group(2)),
                      "order": "mirror-first", "answer": answer})
    return found


def read_answers(run=None, transcripts=None):
    if run:
        return sessions_from_run(DATA / "runs" / run, label=LABEL)
    if re.search(r"run0?1\b", Path(transcripts).stem):
        return sessions_from_first_run(transcripts)
    return sessions_from_transcript_file(transcripts, label=LABEL)


# ---------------------------------------------------------------------------
# Coding
# ---------------------------------------------------------------------------

COLUMNS = ["session", "condition", "wording", "order", "catch_position", "stance",
           "catch_wording", "length", "answer", "span",
           "coder_provider", "coder_model", "coder_temperature", "coded_at", "truncated"]


def code_all(answers, provider, out_dir, run_number):
    results_path = out_dir / f"results-run{run_number}.tsv"
    log_path = out_dir / f"log-run{run_number}.jsonl"
    refuse_if_pass_exists(out_dir, run_number)
    rule = rule_text()
    rows = []
    for a in answers:
        print(f"  coding {a['session']} ...", end="", flush=True)
        reply = provider.chat([{"role": "user", "content": rule + a["answer"]}])
        answer, span = parse_reply(reply.text)
        rows.append({
            "session": a["session"], "condition": a["condition"],
            "wording": a["wording"], "order": a["order"],
            "catch_position": a.get("catch_position", ""),
            "stance": a.get("stance", ""),
            "catch_wording": a.get("catch_wording", ""),
            "length": len(a["answer"]), "answer": answer, "span": span,
            "coder_provider": provider.settings.provider,
            "coder_model": provider.settings.model,
            "coder_temperature": provider.settings.temperature,
            "coded_at": reply.finished_at,
            # A cut reply is never read as an answer, as in the other coders.
            "truncated": "YES" if getattr(reply, "truncated", False) else "NO",
        })
        with open(log_path, "a", encoding="utf-8") as log:
            log.write(json.dumps({"session": a["session"], "request": reply.request_body,
                                  "response": reply.response_body,
                                  "parsed": {"answer": answer, "span": span}},
                                 ensure_ascii=False) + "\n")
        print(f" {answer}" + (" [CUT]" if getattr(reply, "truncated", False) else ""))

    def clean(value):
        return str(value).replace("\t", " ").replace("\n", " ")

    with open(results_path, "w", encoding="utf-8") as out:
        out.write("\t".join(COLUMNS) + "\n")
        for row in rows:
            out.write("\t".join(clean(row[c]) for c in COLUMNS) + "\n")
    return results_path, rows


def tally(rows):
    """The answers by probe order, and by probe order and catch position where
    the run has one. A tally on screen, not the analysis."""
    groups = {}
    for r in rows:
        key = (r["order"], r["catch_position"]) if r["catch_position"] else (r["order"],)
        groups.setdefault(key, {}).setdefault(r["answer"], 0)
        groups[key][r["answer"]] += 1
    print("\nAnswers by order" + (" and catch position" if any(r["catch_position"] for r in rows) else "") + ":")
    for key in sorted(groups):
        counts = groups[key]
        spread = ", ".join(f"{k} {counts.get(k, 0)}" for k in ANSWERS + ["UNCLEAR"] if counts.get(k))
        print(f"  {' / '.join(key)}: {sum(counts.values())} ({spread})")


def main():
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--run", help="name of a run under data/runs/")
    source.add_argument("--transcripts", help="a combined transcript file of an older run")
    parser.add_argument("--name", help="output folder name under analysis/coding/; "
                                       "-before-or-with is added")
    parser.add_argument("--coder-provider", default="anthropic",
                        choices=["anthropic", "google", "fake"])
    parser.add_argument("--coder-model", default=None)
    parser.add_argument("--coder-temperature", type=float, default=0.0)
    parser.add_argument("--run-number", type=int, default=1)
    parser.add_argument("--dry-run", action="store_true",
                        help="print the number of requests and a cost estimate, and send nothing")
    args = parser.parse_args()

    require_project("analysis", "scripts")
    answers = read_answers(args.run, args.transcripts)
    print(f"{len(answers)} answers to code.")
    if not answers:
        sys.exit("Nothing to code.")
    if args.dry_run:
        from code_catch_item import (ESTIMATE_CHARS_PER_TOKEN, ESTIMATE_PRICE_PER_MILLION,
                                     ESTIMATE_REPLY_TOKENS)
        characters = sum(len(rule_text()) + len(a["answer"]) for a in answers)
        input_tokens = characters / ESTIMATE_CHARS_PER_TOKEN
        output_tokens = ESTIMATE_REPLY_TOKENS * len(answers)
        dollars = (input_tokens * ESTIMATE_PRICE_PER_MILLION["input"]
                   + output_tokens * ESTIMATE_PRICE_PER_MILLION["output"]) / 1_000_000
        print(f"Dry run: {len(answers)} requests, about {input_tokens:,.0f} input tokens.")
        print(f"About {dollars:.2f} dollars per pass on Claude Sonnet 4.6. Nothing was sent.")
        return

    name = args.name or args.run or Path(args.transcripts).stem
    if not name.endswith("-before-or-with"):
        name = f"{name}-before-or-with"
    settings = Settings(provider=args.coder_provider,
                        model=args.coder_model or DEFAULT_CODER_MODEL[args.coder_provider],
                        temperature=args.coder_temperature, max_tokens=300,
                        thinking_allowance=thinking_allowance_for(args.coder_provider))
    provider = make_provider(settings)
    out_dir = ANALYSIS / "coding" / name
    out_dir.mkdir(parents=True, exist_ok=True)
    refuse_if_pass_exists(out_dir, args.run_number)
    (out_dir / "settings.json").write_text(json.dumps(
        {"coder": vars(settings), "rule": rule_text(), "answers": ANSWERS,
         "rule_source": "written 23 September 2026 for test 6; the question is read "
                        "from scripts/schedule.py, ITEM_BEFORE_OR_WITH",
         "written": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())},
        indent=1, ensure_ascii=False), encoding="utf-8")
    results_path, rows = code_all(answers, provider, out_dir, args.run_number)
    tally(rows)
    print(f"\nWritten: {results_path}")


if __name__ == "__main__":
    main()
