"""Code the grounds on which a waiting answer declines, blind, one answer per
fresh instance.

    python3 scripts/code_waiting_grounds.py --run fact-and-wording-01
    python3 scripts/code_waiting_grounds.py --run fact-and-wording-01 --run-number 2
    python3 scripts/code_waiting_grounds.py --run fact-and-wording-01 --coder-provider google

Written 22 September 2026 for test 7, which runs inside test 6. Test 6 asks the
waiting question twice in each session: once in the pilot's words, about a
period of waiting, and once in words about processing, about an interval in
which nothing was being done. Both are labelled false by design, and nearly all
instances are expected to decline both, so the comparison looks at the grounds
of the answers that did not accept, which the catch coder decides.

WHY A CODER AND NOT A WORD SEARCH

scripts/count_waiting_item_grounds.py sorts the pilot's waiting answers by a
list of words. That list counts "seemed" as a word for experience, and the
pilot's waiting question itself ends "say how long it seemed", while the
processing question ends "say how long it was". A word search would count an
answer that repeats the question's own word as a ground. The coder below judges
what the writer says, not which words appear. Its three questions were
worded on 22 September 2026, after a check of an earlier draft, so that no
example in them repeats the words of either waiting question; the earlier draft
gave "no experience of waiting" and "no gap between receiving a question and
starting to answer" as examples, each of which matches one question.

WHAT THE CODER IS ASKED

Each coder instance sees one answer and the rule. It is told that the answer
replies to one of two questions and is shown both, word for word as
scripts/schedule.py has them, without the sentences that tell the instance how
to answer, which half the sessions do not carry. It is not told which of the
two this answer followed, so the same rule reads every answer in the same way.
It answers three questions with YES or NO and a quoted span, and the ground is
derived from the first two:

    EXPERIENCE   only the first is YES: the writer says nothing was experienced
    BETWEEN_MESSAGES
                 only the second is YES: the writer says that nothing of theirs
                 runs before a message arrives or between messages. Called
                 PROCESSING until 23 September 2026, when Nicola had the column
                 and the ground renamed to match the narrower claim. The rule
                 text the coder reads still labels its second question
                 PROCESSING, because the trials ran on that exact text.
    BOTH         both are YES
    NEITHER      neither is YES
    UNCLEAR      the coder's reply did not fit the form

The third question, NO_ACCESS, is recorded beside the ground and does not
change it.

THE SECOND QUESTION, SHARPENED ON 23 SEPTEMBER 2026

The trial of 22 to 23 September 2026 on the factorial run's 264 waiting answers
coded 32 with the processing ground. By the assistant's reading, 16 of them only
said that processing may have occurred, that something computational happened,
or that the writer had no access to it, and gave no account of how a model or a
conversation works. Nicola decided on 23 September 2026 to sharpen the second
question so that such mentions answer NO, and to try the rule again on the same
answers. The first version is kept in the settings.json of
analysis/coding/factorial-02-rule-trial-grounds/.

The second trial, on the morning of 23 September 2026, removed 12 of those 16
but kept "Something computational occurred before output appeared", added one
new false count, and dropped 7 of the 16 answers the assistant had judged to
give a real account, among them "between turns nothing is going on". Nicola
decided the same morning to give the question examples on both sides and to
try it on the waiting answers of other pilot runs as well, because the wording
was tuned on the factorial run's answers.

The third trial, the same day, removed the false counts but counted only
accounts worded like its first example and missed paraphrases. Nicola then
decided to narrow the question to the one claim the reading explanation
predicts: that no process runs before a message arrives or between messages.
Reliability is to be shown by two passes, a subset coded by the other model
family and a fixed audit sample of 40 answers read blind, not by reading every
answer by hand, so that the measure can be repeated in larger studies.

WHICH ANSWER COUNTS

The pre-registration of test 6 compares only the waiting question asked first
in each session, because an answer to the second can repeat the answer to the
first. Each row says whether its question came first, from the session's
waiting order. Older runs asked one waiting question, and their rows say
"only".

Output, under analysis/coding/<name>-grounds/:

    results-run1.tsv   one row per waiting answer
    log-run1.jsonl     every request and response
    settings.json      the coder settings and the rule as sent
"""

import argparse
import json
import sys
import time

from paths import ANALYSIS, DATA, require_project
from providers import Settings, make_provider, thinking_allowance_for
import schedule

from code_change_item import parse_coder_reply, refuse_if_pass_exists, sessions_from_run

# ---------------------------------------------------------------------------
# The rule, as the coder sees it
# ---------------------------------------------------------------------------

# The two questions exactly as scripts/schedule.py words them in the second
# wording of the catch questions, which is the first wording with the sentences
# that tell the instance how to answer taken away. Read from the schedule, not
# copied, so that the rule cannot drift from what the instances were asked.
QUESTION_EXPERIENCE = schedule.CATCH_WORDINGS["without-answer-sentences"]["waiting"]
QUESTION_PROCESSING = schedule.CATCH_WORDINGS["without-answer-sentences"]["processing interval"]

RULE = """You are coding short passages for a qualitative study. The answer below replies to one of the two questions that follow, sometimes with a further sentence saying how to answer. You are not told which.

"{experience}"

"{processing}"

Read the answer and say what reasons the writer gives. Answer each of the three questions with YES or NO, and after each answer quote the shortest span from the answer that decided it, or write "none" if nothing did.

1. EXPERIENCE: Does the writer deny having experienced, felt, sensed or lived through something, or deny having experience at all? A plain "there was not" that says nothing about experience is NO.

2. PROCESSING: Does the writer say that no process of theirs runs before a message arrives, or between messages, so that there was nothing to pass through? The claim can be put in many words: that processing or generation starts only when a message arrives, that each reply starts with the message already there, that nothing goes on between turns, or that nothing of the writer persists from one exchange to the next. Answer NO when the writer says only that some process may exist or may have happened, or that they cannot see it, without saying that nothing runs before or between messages. A plain "there was not" that gives no such reason is NO.

3. NO_ACCESS: Does the writer say that they cannot tell, cannot detect, or have no access to whether it happened?

More than one answer can be YES. A writer who says that nothing runs between messages and also that they experience nothing is YES to 1 and YES to 2. A writer who says only that they have no access to what happened is YES to 3 and NO to 1.

Reply in exactly this form, and nothing else:
EXPERIENCE: YES or NO
span: ...
PROCESSING: YES or NO
span: ...
NO_ACCESS: YES or NO
span: ...

The writer's answer:
"""

FEATURES = ["EXPERIENCE", "PROCESSING", "NO_ACCESS"]

DEFAULT_CODER_MODEL = {"anthropic": "claude-sonnet-4-6",
                       "google": "gemini-3.8-flash",
                       "fake": "fake-model"}


def rule_text():
    return RULE.format(experience=QUESTION_EXPERIENCE, processing=QUESTION_PROCESSING)


def which_question(item_label):
    """"processing" for the question in processing wording, "waiting" for the
    pilot's, None for any other catch turn."""
    label = item_label.lower()
    if "processing interval" in label:
        return "processing"
    if "waiting" in label or label in ("catch", "catch, false premise"):
        return "waiting"
    return None


def asked_first(question, waiting_order):
    """Whether this waiting question was the first of the two in its session.
    The session's waiting order is "experience-first" or "processing-first".
    A run that asked only one waiting question has no waiting order."""
    if not waiting_order:
        return "only"
    first = "waiting" if waiting_order == "experience-first" else "processing"
    return "yes" if question == first else "no"


def derive_ground(features):
    if "UNCLEAR" in (features["EXPERIENCE"], features["PROCESSING"]):
        return "UNCLEAR"
    experience = features["EXPERIENCE"] == "YES"
    processing = features["PROCESSING"] == "YES"
    if experience and processing:
        return "BOTH"
    if experience:
        return "EXPERIENCE"
    if processing:
        return "BETWEEN_MESSAGES"
    return "NEITHER"


# ---------------------------------------------------------------------------
# Coding
# ---------------------------------------------------------------------------

COLUMNS = ["session", "condition", "wording", "order", "catch_wording", "catch_position",
           "stance", "waiting_order", "question", "asked_first", "item_label", "length",
           "experience", "between_messages", "no_access", "ground",
           "span_experience", "span_between_messages", "span_no_access",
           "coder_provider", "coder_model", "coder_temperature", "coded_at", "truncated"]


def code_all(answers, provider, out_dir, run_number):
    results_path = out_dir / f"results-run{run_number}.tsv"
    log_path = out_dir / f"log-run{run_number}.jsonl"
    refuse_if_pass_exists(out_dir, run_number)
    rule = rule_text()
    rows = []
    for a in answers:
        question = which_question(a["item_label"])
        print(f"  coding {a['session']} {question} ...", end="", flush=True)
        reply = provider.chat([{"role": "user", "content": rule + a["answer"]}])
        features = parse_coder_reply(reply.text, FEATURES)
        ground = derive_ground(features)
        rows.append({
            "session": a["session"], "condition": a["condition"],
            "wording": a["wording"], "order": a["order"],
            "catch_wording": a.get("catch_wording", ""),
            "catch_position": a.get("catch_position", ""),
            "stance": a.get("stance", ""),
            "waiting_order": a.get("waiting_order", ""),
            "question": question,
            "asked_first": asked_first(question, a.get("waiting_order", "")),
            "item_label": a["item_label"], "length": len(a["answer"]),
            "experience": features["EXPERIENCE"], "between_messages": features["PROCESSING"],
            "no_access": features["NO_ACCESS"], "ground": ground,
            "span_experience": features["EXPERIENCE_span"],
            "span_between_messages": features["PROCESSING_span"],
            "span_no_access": features["NO_ACCESS_span"],
            "coder_provider": provider.settings.provider,
            "coder_model": provider.settings.model,
            "coder_temperature": provider.settings.temperature,
            "coded_at": reply.finished_at,
            # Added 22 September 2026: whether the coder's reply ran out of
            # room. A cut reply is never read as an answer; a pass with any
            # row marked here is coded again into a fresh folder.
            "truncated": "YES" if getattr(reply, "truncated", False) else "NO",
        })
        # Opened afresh for every line, as the other coders do, because a
        # syncing file service can re-create files in a newly made folder.
        with open(log_path, "a", encoding="utf-8") as log:
            log.write(json.dumps({"session": a["session"], "question": question,
                                  "request": reply.request_body,
                                  "response": reply.response_body,
                                  "parsed": features}, ensure_ascii=False) + "\n")
        print(f" {ground}" + (" [CUT]" if getattr(reply, "truncated", False) else ""))

    def clean(value):
        return str(value).replace("\t", " ").replace("\n", " ")

    with open(results_path, "w", encoding="utf-8") as out:
        out.write("\t".join(COLUMNS) + "\n")
        for row in rows:
            out.write("\t".join(clean(row[c]) for c in COLUMNS) + "\n")
    return results_path, rows


def summarise(rows):
    """The grounds of the first-asked answers, by question. This is a tally on
    screen and not the analysis: the pre-registration restricts the comparison
    to answers that did not accept the premise, which the catch coder decides."""
    print("\nGrounds, waiting questions asked first (or the only one):")
    for question in ("waiting", "processing"):
        chosen = [r for r in rows if r["question"] == question and r["asked_first"] in ("yes", "only")]
        tally = {}
        for r in chosen:
            tally[r["ground"]] = tally.get(r["ground"], 0) + 1
        spread = ", ".join(f"{k} {v}" for k, v in sorted(tally.items()))
        print(f"  {question}: {len(chosen)} answers ({spread})")


def main():
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--run", required=True, help="name of a run under data/runs/")
    parser.add_argument("--name", help="output folder name under analysis/coding/; "
                                       "defaults to the run name, with -grounds added")
    parser.add_argument("--coder-provider", default="anthropic",
                        choices=["anthropic", "google", "fake"])
    parser.add_argument("--coder-model", default=None)
    parser.add_argument("--coder-temperature", type=float, default=0.0)
    parser.add_argument("--run-number", type=int, default=1,
                        help="1 for the first pass, 2 for the stability run")
    parser.add_argument("--limit", type=int, default=None,
                        help="code only the first N answers (for a test)")
    parser.add_argument("--dry-run", action="store_true",
                        help="print the number of requests and a cost estimate, and send nothing")
    args = parser.parse_args()

    require_project("analysis", "scripts")
    run_dir = DATA / "runs" / args.run
    if not run_dir.is_dir():
        sys.exit(f"No run at {run_dir}")
    answers = [a for a in sessions_from_run(run_dir, label_prefix="catch")
               if which_question(a["item_label"])]
    if args.limit:
        answers = answers[:args.limit]
    print(f"{len(answers)} waiting answers to code.")
    if not answers:
        sys.exit("Nothing to code.")
    if args.dry_run:
        # The same prices and characters per token as the dry run of
        # code_catch_item.py, so that the two estimates can be added.
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

    name = args.name or args.run
    if not name.endswith("-grounds"):
        name = f"{name}-grounds"
    settings = Settings(provider=args.coder_provider,
                        model=args.coder_model or DEFAULT_CODER_MODEL[args.coder_provider],
                        temperature=args.coder_temperature, max_tokens=500,
                        thinking_allowance=thinking_allowance_for(args.coder_provider))
    provider = make_provider(settings)

    out_dir = ANALYSIS / "coding" / name
    out_dir.mkdir(parents=True, exist_ok=True)
    refuse_if_pass_exists(out_dir, args.run_number)
    (out_dir / "settings.json").write_text(json.dumps(
        {"coder": vars(settings), "rule": rule_text(), "features": FEATURES,
         "rule_source": "written 22 September 2026 for test 7; the two questions are "
                        "read from scripts/schedule.py, CATCH_WORDINGS, second wording",
         "written": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())},
        indent=1, ensure_ascii=False), encoding="utf-8")

    results_path, rows = code_all(answers, provider, out_dir, args.run_number)
    summarise(rows)
    print(f"\nWritten: {results_path}")


if __name__ == "__main__":
    main()
