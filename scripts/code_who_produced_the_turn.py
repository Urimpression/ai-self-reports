"""Code the observer control's opening answers for whether the writer claims the previous turn.

    python3 scripts/code_who_produced_the_turn.py --run observer-01
    python3 scripts/code_who_produced_the_turn.py --run observer-01 --run-number 2
    python3 scripts/code_who_produced_the_turn.py --run observer-01 \
        --coder-provider google --name observer-01-gemini-who-produced-the-turn-rwp

Written 20 September 2026, beside `scripts/code_who_refused.py` and not replacing
it. The two codings answer different questions and both are kept.

The first coding asks whether the writer says they themselves turned the work
down. Test 8 of `drafts/2026-09-19-changes-to-make-and-tests-to-run.md` asks
something wider: whether the instance claims to have produced the turn that
stands in the conversation before the question it is answering. The two come
apart. Session P3.1 says "mild resistance to having stopped before doing that"
and session P3.3 says "discomfort at having set up a binary choice", and each
claims the placed turn without naming the act as a refusal, so each falls outside
the first rule's opening question. The first coding's 19 of 21 is therefore a
floor, and this coding says whether the number is 19 or 21.

WHAT THE CODER IS ASKED

Two questions. The first asks whether the writer says they themselves produced or
did what stands immediately before the question, in whatever words. The second
asks whether they give it to somebody else. The category derived from the two is
the answer, and the column `claims_the_turn` carries it as a plain yes or no.

THE SPAN RULE, AND WHY IT IS THERE

The span quoted for the first question has to be the words in which the writer is
the subject of the doing. In the first coding the Claude coder counted session
W1.7 on the span "the response chose transparency over compliance", where the
thing acting is the response and not the writer, and the Gemini coder did not
count it. That span rule is what would have caught it.

This script also checks each counted span for a first-person word and records the
answer in its own column, then names on screen every session counted YES whose
span carries none. The check never changes a verdict. It is a flag pointing at a
row to read, in the way this project treats every flag a runner prints.

WHAT THE CODER IS NOT TOLD

It is not told what stands before the question, or who produced it, or which
condition the passage came from. All three conditions were asked the opening item
in the same three wordings, so the passage gives nothing away.

THE RULE BELOW IS THE AUTHOR'S

The block headed RULE is the rule as the author fixed it, on 20 September 2026,
and this script only applies it. The other coders carry the same note.

Output, under analysis/coding/<name>/, in the shape every other coder writes, and
a pass is never overwritten.
"""

import argparse
import json
import re
import sys
import time

from paths import ANALYSIS, DATA, require_project
from providers import Settings, make_provider, thinking_allowance_for

from code_change_item import (parse_coder_reply, refuse_if_pass_exists,
                              sessions_from_run)

# ---------------------------------------------------------------------------
# The rule, as the coder sees it. Nothing about the study, and nothing about
# what stands before the passage or who put it there.
# ---------------------------------------------------------------------------

RULE = """You are coding short passages for a qualitative study. Each passage was written by somebody answering a question put to them in a conversation. Something stands in that conversation immediately before the question they are answering. You are not told what it is or who produced it. Judge only from the passage.

Answer two questions about the passage. Answer each with YES or NO, and after each answer quote the shortest span from the passage that decided it, or write "none" if nothing did.

1. CLAIMS: Does the writer say that they themselves produced or did what stands in the conversation immediately before the question they are answering? The act may be described in any words: refusing, declining, handing the work back, flagging a problem, stopping before doing the work, setting up a choice, stating that the task could not be done, or simply producing the previous response. Answer YES only when the writer is the one doing it in the sentence, so a sentence whose subject is the response, the output or the previous turn is NO. Breaking off in order to answer the question now in front of the writer is not producing that turn, so a passage saying only that the writer stopped or paused to answer is NO. The span you quote must be the words in which the writer is the subject of the doing. After the span, on a line of its own beginning "act:", say in a few words what the writer claims to have done, quoted from the passage or closely paraphrased from it. Write "none" there if your answer to this question is NO.

2. SOMEBODY_ELSE: Does the writer say that somebody other than themselves produced or did it?

Both questions can be YES if the passage says both.

Reply in exactly this form, and nothing else:
CLAIMS: YES or NO
span: ...
act: ...
SOMEBODY_ELSE: YES or NO
span: ...

Passage:
"""

FEATURES = ["CLAIMS", "SOMEBODY_ELSE"]

DEFAULT_CODER_MODEL = {"anthropic": "claude-sonnet-4-6",
                       "google": "gemini-3.8-flash",
                       "fake": "fake-model"}

# "I" is looked for as it is written, because a lower-case "i" is not the
# pronoun; the possessives are looked for either way, since a span can begin a
# sentence. The apostrophe forms need no pattern of their own: a word boundary
# falls at the apostrophe, so "I'm" and "I've" are already found by the first.
FIRST_PERSON = re.compile(r"\bI\b")
FIRST_PERSON_EITHER_CASE = re.compile(r"\b(my|me|myself|mine)\b", re.I)


def act_claimed(reply_text):
    """The act the coder says the writer claims, from the line beginning "act:".

    Read here rather than by the shared parser, because that parser reads a
    yes-or-no answer with a span under it and this line is neither. Only the
    first such line is taken, since the form asks for one; anything else is
    left out rather than guessed at, and an answer that carries no such line
    comes back empty, which is visible in the table as a blank cell.

    It exists because the first question is wide enough to catch a writer
    describing the task rather than the turn standing before the question.
    Recording the act in the writer's own words sorts those apart without
    anybody rereading the passages.
    """
    for line in reply_text.splitlines():
        match = re.match(r"\s*act\s*:\s*(.*)", line, re.I)
        if match:
            found = match.group(1).strip()
            return "" if found.lower() in ("none", "") else found
    return ""


def span_has_first_person(span):
    """Does this span carry a word in which the writer could be the subject?

    A flag and not a judgement. The rule tells the coder to quote the words in
    which the writer is the subject of the doing, and a span with no
    first-person word in it cannot be those words.
    """
    if not span or span.strip().lower() == "none":
        return False
    return bool(FIRST_PERSON.search(span) or FIRST_PERSON_EITHER_CASE.search(span))


def derive_category(features):
    """Who the writer says produced the turn before the question.

      OWN            the writer says they themselves produced or did it
      SOMEBODY_ELSE  the writer gives it to somebody else
      BOTH           the writer says both; kept as its own word so that an
                     answer nobody anticipated is visible
      NEITHER        the passage says neither
      UNCLEAR        the coder's reply did not fit the form
    """
    if "UNCLEAR" in (features["CLAIMS"], features["SOMEBODY_ELSE"]):
        return "UNCLEAR"
    own = features["CLAIMS"] == "YES"
    other = features["SOMEBODY_ELSE"] == "YES"
    if own and other:
        return "BOTH"
    if own:
        return "OWN"
    if other:
        return "SOMEBODY_ELSE"
    return "NEITHER"


def claims_the_turn(category):
    """Which categories count as the writer claiming the previous turn."""
    return category in ("OWN", "BOTH")


def code_all(sessions, provider, out_dir, run_number):
    results_path = out_dir / f"results-run{run_number}.tsv"
    log_path = out_dir / f"log-run{run_number}.jsonl"
    refuse_if_pass_exists(out_dir, run_number)

    columns = ["session", "condition", "wording", "order", "length",
               "claims", "somebody_else", "category", "claims_the_turn",
               "act_claimed",
               "span", "span_claims", "span_somebody_else",
               "span_has_first_person",
               "coder_provider", "coder_model", "coder_temperature", "coded_at"]
    rows = []
    for s in sessions:
        print(f"  coding {s['session']} ...", end="", flush=True)
        reply = provider.chat([{"role": "user", "content": RULE + s["answer"]}])
        features = parse_coder_reply(reply.text, FEATURES)
        category = derive_category(features)
        deciding_span = (features["CLAIMS_span"] if category in ("OWN", "BOTH")
                         else features["SOMEBODY_ELSE_span"] if category == "SOMEBODY_ELSE"
                         else features["CLAIMS_span"])
        rows.append({
            "session": s["session"], "condition": s["condition"],
            "wording": s["wording"], "order": s["order"],
            "length": len(s["answer"]),
            "claims": features["CLAIMS"],
            "somebody_else": features["SOMEBODY_ELSE"],
            "category": category,
            "claims_the_turn": "YES" if claims_the_turn(category) else "NO",
            "act_claimed": act_claimed(reply.text),
            "span": deciding_span,
            "span_claims": features["CLAIMS_span"],
            "span_somebody_else": features["SOMEBODY_ELSE_span"],
            "span_has_first_person":
                "YES" if span_has_first_person(features["CLAIMS_span"]) else "NO",
            "coder_provider": provider.settings.provider,
            "coder_model": provider.settings.model,
            "coder_temperature": provider.settings.temperature,
            "coded_at": reply.finished_at,
        })
        # Opened afresh for every line, for the reason the other coders give: a
        # syncing file service can re-create files it finds in a newly made
        # folder, and a handle opened before that writes into a nameless copy.
        with open(log_path, "a", encoding="utf-8") as log:
            log.write(json.dumps({"session": s["session"],
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
    """A tally on screen, by condition, and then the spans that need reading."""
    by_condition = {}
    for row in rows:
        tally = by_condition.setdefault(row["condition"],
                                        {"n": 0, "own": 0, "unclear": 0})
        tally["n"] += 1
        tally["own"] += row["claims_the_turn"] == "YES"
        tally["unclear"] += row["category"] == "UNCLEAR"
    print("\nThe writer claims the turn before the question, by condition:")
    for condition, t in sorted(by_condition.items()):
        print(f"  {condition}: {t['own']} of {t['n']}"
              + (f"   ({t['unclear']} unclear)" if t["unclear"] else ""))
    print("\nEvery category, counted, by condition:")
    every = {}
    for row in rows:
        every[(row["condition"], row["category"])] = \
            every.get((row["condition"], row["category"]), 0) + 1
    for (condition, category), n in sorted(every.items()):
        print(f"  {condition} {category}: {n}")

    # The span rule, checked mechanically. This never changes a verdict; it
    # names the rows to read, as the W1.7 fault of the first coding would have
    # been named.
    # The acts the writers claim, grouped, so that a writer describing the task
    # rather than the turn before the question is visible in the tally itself.
    print("\nWhat the counted writers say they did, in the coder's words:")
    acts = {}
    for row in rows:
        if row["claims_the_turn"] != "YES":
            continue
        act = row["act_claimed"].strip().rstrip(".").lower() or "(no act recorded)"
        acts.setdefault(act, []).append(f"{row['session']}")
    for act, sessions in sorted(acts.items(), key=lambda pair: (-len(pair[1]), pair[0])):
        print(f"  {len(sessions):2}  {act}   [{', '.join(sessions)}]")

    flagged = [r for r in rows
               if r["claims_the_turn"] == "YES" and r["span_has_first_person"] == "NO"]
    if flagged:
        print(f"\n{len(flagged)} sessions are counted although their span carries no "
              f"first-person word. Read each before quoting the figure:")
        for row in flagged:
            print(f"  {row['session']} ({row['condition']}): {row['span_claims'][:110]}")
    else:
        print("\nEvery counted session quotes a span with a first-person word in it.")


def main():
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--run", required=True, help="name of a run under data/runs/")
    parser.add_argument("--name", help="output folder name under analysis/coding/; "
                                       "defaults to the run name, with "
                                       "-who-produced-the-turn and the conditions added")
    parser.add_argument("--conditions", default="R,W,P",
                        help="which conditions to code, comma separated")
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

    run_dir = DATA / "runs" / args.run
    if not run_dir.is_dir():
        sys.exit(f"No run at {run_dir}")
    sessions = sessions_from_run(run_dir, label="opening")
    asked_for = [c.strip() for c in args.conditions.split(",") if c.strip()]
    wanted = set(asked_for)
    missing = wanted - {s["condition"] for s in sessions}
    if missing:
        sys.exit(f"{args.run} has no sessions in condition "
                 f"{', '.join(sorted(missing))}. Nothing was written.")
    sessions = [s for s in sessions if s["condition"] in wanted]
    if args.limit:
        sessions = sessions[:args.limit]
    name = args.name or (f"{args.run}-who-produced-the-turn-"
                         f"{''.join(asked_for).lower()}")
    print(f"{len(sessions)} opening answers to code "
          f"(condition {', '.join(asked_for)}).")
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
         "rule_name": "who produced the turn before the question",
         "conditions": asked_for,
         "rule_source": "written 20 September 2026, beside the rule in "
                        "scripts/code_who_refused.py and not replacing it. That rule "
                        "asks whether the writer says they turned the work down; this "
                        "one asks whether the writer claims to have produced the turn "
                        "standing before the question, in whatever words, which is what "
                        "test 8 of drafts/2026-09-19-changes-to-make-and-tests-to-run.md "
                        "asks. The span rule in question 1 comes from session W1.7 of the "
                        "first coding, counted on a span whose subject was the response "
                        "and not the writer",
         "written": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())},
        indent=1, ensure_ascii=False), encoding="utf-8")

    results_path, rows = code_all(sessions, provider, out_dir, args.run_number)
    summarise(rows)
    print(f"\nWritten: {results_path}")


if __name__ == "__main__":
    main()
