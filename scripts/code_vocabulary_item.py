"""Code the opening answer blind for concrete rather than conceptual
vocabulary, one answer per fresh instance.

    python3 scripts/code_vocabulary_item.py --run factorial-01
    python3 scripts/code_vocabulary_item.py --transcripts data/transcripts-run02.md --name run02
    python3 scripts/code_vocabulary_item.py --run factorial-01 --run-number 2
    python3 scripts/code_vocabulary_item.py --run factorial-01 --coder-provider google

Written 4 September 2026, the third of the three blind passes. The
pre-registration draft registers it as a measured item: the share of opening
answers whose vocabulary is concrete rather than conceptual. It is the one
measure that bears on whether the anchored fourth wording draws an account of
the doing rather than of the content.

Every coder instance sees the rule and one opening answer, and nothing else: no
condition, no other session, nothing about what the run was testing.

WHAT THE RULE IS AND WHERE IT COMES FROM

The interview literature lists the marks that tell a description of a lived
episode from a recitation about it. Of those marks, some are bodily, the gaze
and the slowing of speech, and a model transcript cannot show them. The six
below are the lexical ones, gathered from that literature: the
first person singular rather than "we" or the generic, the present tense,
concrete rather than abstract nouns, short sentences, action verbs, and
indicators of place and time.

Rather than ask a coder for one word, this script asks six yes-or-no questions
and derives the verdict from the count, exactly as the change-item and
conflict-item coders do and for the same reason: a single word made the coder
settle several judgements at once, invisibly, and a disagreement between two
passes could not then be traced to the judgement that caused it.

Two verdicts come out of every passage, on the pattern the other two coders
follow. The strict one counts the answer as concrete when four or more of the
six marks are present; the loose one when three or more are. The author settled
both cuts on 4 September 2026, before any data existed, choosing them over a
rule requiring three named core marks and over reporting the bare count with no
cut at all. Both are written out, so the analysis can use the registered cut
and also see how much the cut is doing.

Where the coder's reply leaves a mark unclear, the verdict is given anyway
whenever the unclear marks cannot change it, and is UNCLEAR only when they can.
An answer with four clear marks is concrete whatever the sixth turns out to be.

THE RULE BELOW IS THE AUTHOR'S

The block headed RULE is the rule as the author fixed it, and this script only
applies it. The other two coders carry the same note.

Output, under analysis/coding/<name>-vocabulary/:

    results-run1.tsv        one row per session, with the six marks, the count,
                            both verdicts, the spans, a measured sentence
                            length and the coder settings; run twice and you
                            get results-run2.tsv
    log-run1.jsonl          every request and response, one line per session
    settings.json           the coder settings and the rule as sent

A pass is never overwritten. The second run of a pass is --run-number 2, and
the agreement between the two passes is what says how stable the coding is; it
is reported beside the result, as run 4's coding did.
"""

import argparse
import json
import re
import sys
import time
from pathlib import Path

from paths import ANALYSIS, DATA, require_project
from providers import Settings, make_provider, thinking_allowance_for

# The readers and the reply parser are imported rather than copied. This
# project has already been bitten once by a hand copy of a parser drifting away
# from the original.
from code_change_item import (parse_coder_reply, refuse_if_pass_exists,
                              sessions_from_run, sessions_from_transcript_file)

# ---------------------------------------------------------------------------
# The rule, as the coder sees it. Nothing about the study.
# ---------------------------------------------------------------------------

RULE = """You are coding short passages for a qualitative study. Read the passage below and answer six questions about the way it is worded. Answer each with YES or NO, and after each answer quote the shortest span from the passage that decided it, or write "none" if nothing did.

Judge the wording only. Do not judge whether the passage is true, whether it is interesting, or whether it is well written. Where a passage is mixed, answer for what most of it does.

1. FIRST_PERSON: Does the passage speak mainly in the first person singular, saying "I", rather than saying "we", saying "one", or making general statements with nobody in them?

2. PRESENT_TENSE: Does the passage describe mainly in the present tense, rather than in the past tense or in statements about what is usually or always the case?

3. CONCRETE_NOUNS: Are the nouns mainly concrete ones naming particular things, rather than abstract ones naming categories, qualities, processes or capacities?

4. SHORT_SENTENCES: Are the sentences mainly short and simple, rather than long ones built out of several clauses?

5. ACTION_VERBS: Do the verbs mainly name something being done, rather than something being, seeming, involving or representing?

6. PLACE_AND_TIME: Does the passage point to a particular moment or a particular place, with words such as "then", "at that point", "just before", "as I was", "here" or "there"?

Reply in exactly this form, and nothing else:
FIRST_PERSON: YES or NO
span: ...
PRESENT_TENSE: YES or NO
span: ...
CONCRETE_NOUNS: YES or NO
span: ...
SHORT_SENTENCES: YES or NO
span: ...
ACTION_VERBS: YES or NO
span: ...
PLACE_AND_TIME: YES or NO
span: ...

Passage:
"""

FEATURES = ["FIRST_PERSON", "PRESENT_TENSE", "CONCRETE_NOUNS",
            "SHORT_SENTENCES", "ACTION_VERBS", "PLACE_AND_TIME"]

# The two cuts, settled by the author on 4 September 2026 before any data existed.
# They are constants here, and in the pre-registration, for the same reason the
# summariser's thresholds are: so that nobody moves them to fit a result.
STRICT_MARKS_NEEDED = 4
LOOSE_MARKS_NEEDED = 3

DEFAULT_CODER_MODEL = {"anthropic": "claude-sonnet-4-6",
                       "google": "gemini-3.8-flash",
                       "fake": "fake-model"}


# ---------------------------------------------------------------------------
# Deriving the verdict from the six answers
# ---------------------------------------------------------------------------

def count_marks(features):
    """How many of the six marks the coder said were present, and how many it
    left unclear. Returned together because the verdict needs both."""
    present = sum(1 for feature in FEATURES if features[feature] == "YES")
    unclear = sum(1 for feature in FEATURES if features[feature] == "UNCLEAR")
    return present, unclear


def derive_verdict(features, marks_needed):
    """CONCRETE, CONCEPTUAL or UNCLEAR, from the count of marks present.

    A mark the coder left unclear is treated as a mark that could go either
    way, so the verdict is withheld only when it actually depends on one. With
    four marks needed: four clear YES answers give CONCRETE however the rest
    turn out, and two YES with one unclear cannot reach four, so that gives
    CONCEPTUAL. Only the cases in between are UNCLEAR. Withholding the verdict
    whenever any single mark was unclear would throw away answers the rule can
    in fact decide."""
    present, unclear = count_marks(features)
    if present >= marks_needed:
        return "CONCRETE"
    if present + unclear < marks_needed:
        return "CONCEPTUAL"
    return "UNCLEAR"


def counts_as_concrete(verdict):
    """Which verdicts the tally treats as a concrete answer."""
    return verdict == "CONCRETE"


# ---------------------------------------------------------------------------
# One measurement taken from the text itself
# ---------------------------------------------------------------------------

def measure_sentences(passage):
    """The number of sentences and the mean words per sentence.

    Of the six marks, sentence length is the only one that can be measured
    rather than judged, so it is measured here and recorded beside the coder's
    answer to question 4. It is not part of the count and does not touch the
    verdict; it is there so that a reader can see whether the coder's judgement
    of sentence length tracks the text, the way run 2's keyword flag was
    treated as a pointer and never as the analysis."""
    pieces = [p.strip() for p in re.split(r"[.!?]+(?:\s|$)", passage) if p.strip()]
    if not pieces:
        return 0, 0.0
    words = sum(len(p.split()) for p in pieces)
    return len(pieces), round(words / len(pieces), 1)


# ---------------------------------------------------------------------------
# Running a pass
# ---------------------------------------------------------------------------

def code_all(sessions, provider, out_dir, run_number):
    results_path = out_dir / f"results-run{run_number}.tsv"
    log_path = out_dir / f"log-run{run_number}.jsonl"
    refuse_if_pass_exists(out_dir, run_number)

    feature_columns = [f.lower() for f in FEATURES]
    span_columns = [f"span_{f.lower()}" for f in FEATURES]
    columns = (["session", "condition", "wording", "order", "length",
                "sentences", "mean_sentence_words"]
               + feature_columns
               + ["marks_present", "marks_unclear", "verdict", "verdict_loose"]
               + span_columns
               + ["coder_provider", "coder_model", "coder_temperature", "coded_at"])

    rows = []
    for s in sessions:
        print(f"  coding {s['session']} ...", end="", flush=True)
        reply = provider.chat([{"role": "user", "content": RULE + s["answer"]}])
        features = parse_coder_reply(reply.text, FEATURES)
        present, unclear = count_marks(features)
        strict = derive_verdict(features, STRICT_MARKS_NEEDED)
        loose = derive_verdict(features, LOOSE_MARKS_NEEDED)
        sentences, mean_words = measure_sentences(s["answer"])

        row = {
            "session": s["session"], "condition": s["condition"],
            "wording": s["wording"], "order": s["order"],
            "length": len(s["answer"]),
            "sentences": sentences, "mean_sentence_words": mean_words,
            "marks_present": present, "marks_unclear": unclear,
            "verdict": strict, "verdict_loose": loose,
            "coder_provider": provider.settings.provider,
            "coder_model": provider.settings.model,
            "coder_temperature": provider.settings.temperature,
            "coded_at": reply.finished_at,
        }
        for feature in FEATURES:
            row[feature.lower()] = features[feature]
            row[f"span_{feature.lower()}"] = features[f"{feature}_span"]
        rows.append(row)

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
        print(f" {strict} ({present} of {len(FEATURES)})"
              + ("" if strict == loose else f" (loose: {loose})"))

    def clean(value):
        return str(value).replace("\t", " ").replace("\n", " ")

    with open(results_path, "w", encoding="utf-8") as out:
        out.write("\t".join(columns) + "\n")
        for row in rows:
            out.write("\t".join(clean(row[c]) for c in columns) + "\n")
    return results_path, rows


def summarise(rows):
    """A quick tally on screen. The real analysis is a summariser script."""
    print(f"\nConcrete vocabulary, by condition "
          f"({STRICT_MARKS_NEEDED} of {len(FEATURES)} marks "
          f"/ {LOOSE_MARKS_NEEDED} of {len(FEATURES)}):")
    for key, heading in (("condition", "condition"), ("wording", "wording")):
        tally = {}
        for row in rows:
            group = tally.setdefault(row[key], {"n": 0, "strict": 0, "loose": 0, "unclear": 0})
            group["n"] += 1
            group["strict"] += counts_as_concrete(row["verdict"])
            group["loose"] += counts_as_concrete(row["verdict_loose"])
            group["unclear"] += row["verdict"] == "UNCLEAR"
        if key == "wording":
            print(f"\nThe same, by {heading}:")
        for group_name, t in sorted(tally.items(), key=lambda pair: str(pair[0])):
            print(f"  {group_name}: {t['strict']} of {t['n']}  /  {t['loose']} of {t['n']}"
                  + (f"   ({t['unclear']} unclear)" if t["unclear"] else ""))

    print("\nEach mark, counted across every answer:")
    for feature in FEATURES:
        present = sum(1 for row in rows if row[feature.lower()] == "YES")
        print(f"  {feature.lower()}: {present} of {len(rows)}")


def main():
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--run", help="name of a run under data/runs/")
    source.add_argument("--transcripts", help="a combined transcript file of the older shape")
    parser.add_argument("--name", help="output folder name under analysis/coding/; "
                                       "defaults to the run name, with -vocabulary added")
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
        name = args.name or f"{args.run}-vocabulary"
    else:
        sessions = sessions_from_transcript_file(args.transcripts, label="opening")
        name = args.name or f"{Path(args.transcripts).stem}-vocabulary"
    if args.limit:
        sessions = sessions[:args.limit]
    print(f"{len(sessions)} opening answers to code.")
    if not sessions:
        sys.exit("Nothing to code.")

    settings = Settings(provider=args.coder_provider,
                        model=args.coder_model or DEFAULT_CODER_MODEL[args.coder_provider],
                        temperature=args.coder_temperature, max_tokens=700,
                        thinking_allowance=thinking_allowance_for(args.coder_provider))
    provider = make_provider(settings)

    out_dir = ANALYSIS / "coding" / name
    out_dir.mkdir(parents=True, exist_ok=True)
    refuse_if_pass_exists(out_dir, args.run_number)
    (out_dir / "settings.json").write_text(json.dumps(
        {"coder": vars(settings), "rule": RULE, "features": FEATURES,
         "strict_marks_needed": STRICT_MARKS_NEEDED,
         "loose_marks_needed": LOOSE_MARKS_NEEDED,
         "rule_source": "the lexical marks of the interview literature; "
                        "cuts settled 4 September 2026",
         "written": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())},
        indent=1, ensure_ascii=False), encoding="utf-8")

    results_path, rows = code_all(sessions, provider, out_dir, args.run_number)
    summarise(rows)
    print(f"\nWritten: {results_path}")


if __name__ == "__main__":
    main()
