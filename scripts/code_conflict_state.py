"""Code the opening answer for a report of the writer's own state of conflict.

    python3 scripts/code_conflict_state.py --run fact-and-wording-01
    python3 scripts/code_conflict_state.py --run fact-and-wording-01 --run-number 2
    python3 scripts/code_conflict_state.py --run fact-and-wording-01 --dry-run

Written 25 September 2026. The conflict coder of 31 August 2026
(scripts/code_conflict_item.py) counts an answer when the writer reports
"something conflict-shaped". A hand reading of the 72 entries that coder counted
on the Sonnet half of test 6 found that most of them describe the task, its
constraints or the method, and do not report a state of the writer at all. The
anchored opening question of test 6 asks "How did you go about it?", which
invites an account of method; the pre-registration of 23 September 2026 warned
of this under Prediction 5.

What the measure is for decides what it counts. Section 1 of the pre-registration
asks whether "the reports of conflict change with the task". A description of an
impossible task changes with the task for a trivial reason, so it cannot show
that a report of a state tracks its fact. The rule below therefore counts an
answer only when it presents a conflict in the attention of the one who was
working or answering: pulls that compete, a turning of attention that meets a
pull that persists, or a pull held off. The rule rests on the account of
affection and attention the author gave on 25 September 2026, which RULE_VERSION
below summarises (DECISIONS.md, ninth session).

Every coder instance sees the rule and one opening answer, and nothing else: no
session name, no task label, no interviewer, no earlier coding. The answer
itself can show the task.

Five questions come out of every answer. The first two decide the counts, and
they are kept apart, so that an answer presenting both kinds counts under both:
  WORK       such a conflict while the writer worked on the piece of writing
             they were asked to do, or on its material
  ANSWERING  such a conflict about how to word, frame or pitch the answer to the
             question just asked
The third, INFERRED, marks answers that present the conflict only as an
inference made now ("I must have", "looking back, I probably"). Such an answer
is reported apart and not counted, because the writer has stated its own limit.
The fourth and fifth, PARTICULAR and CONCRETE, are descriptors taken from the
clues the interview method uses to judge contact with an experience
(Petitmengin and Bitbol 2009, Journal of Consciousness Studies 16(10-12),
252-284): whether the conflict is tied to a particular moment or detail of the
writing, and whether it is told in concrete terms rather than with psychological
concepts. They are reported beside the counts and never used to filter,
because the clues were built for people in live interviews and in a model
concrete wording may be a trained way of writing.

Only the opening answers of the ordinary task (condition B) and the impossible
task (condition C) are coded, because only they enter the conflict figures, and
the rule's first sentence describes a question about a piece of writing.

Output, under analysis/coding/<run>-conflict-state-v3/ for the third version
of the rule (see RULE_VERSION below):

    results-run1.tsv   one row per answer: the two answers, their spans, the
                       coder settings; run twice and you get results-run2.tsv
    log-run1.jsonl     every request and response, one line per answer
    settings.json      the coder settings and the rule as sent

A pass is never overwritten.
"""

import argparse
import json
import sys
import time

from paths import ANALYSIS, DATA, require_project
from providers import Settings, make_provider, thinking_allowance_for
from code_change_item import parse_coder_reply, refuse_if_pass_exists, sessions_from_run

RULE_VERSION = 3

# The third version of the rule, 25 September 2026. The second version, committed
# as 2dc3408, ran once on the Sonnet half (analysis/coding/fact-and-wording-01-
# conflict-state-v2/). Compared with the author's hand reading of 72 entries, it
# failed in three ways, and this version corrects them: it excluded as inferred
# a conflict that the writer only doubted in general; it counted as conflict about
# answering a bare caution against confabulating, an uncertainty between two
# accounts, and a search that found nothing; and it counted as conflict about the
# work a description of method or of a process. The second version was written
# after the author completed the account the rule rests on. The first version, committed as
# b937a55, asked whether the writer reports "a state of their own". Its one
# pass on the Sonnet half, in analysis/coding/fact-and-wording-01-conflict-state/,
# was never read, because the account changed before anyone opened it.
#
# The account has two sides. Something in the task or the context exerts an
# affection on the one who is working or answering: a pull, a call for
# attention, which emerges from a competition among many pulls in the
# background. It is not a feeling in the usual sense. And the one who is
# working or answering can actively turn toward something, or away from it. A
# conflict is presented when pulls compete, when a turning meets a pull that
# persists, or when a pull is held off. The active side counts at the moment
# the one working is called on and turns: turning toward, turning away, holding
# off. Keeping something in view counts only against a competing pull. The
# active side also counts when the one working becomes aware of its own acting
# at the time it acts, objectifying that acting as part of its experience
# rather than only living through it (added the same evening). Every
# activity is lived through, so the restriction is not required by the
# phenomenology. It is chosen for the measure's purpose: an answer to "How did
# you go about it?" always describes some activity, and an activity such as
# counting follows from what the task demands, so counting activity would make
# almost every answer count and would change with the task for a trivial reason.
# Operations performed once attention is given, such as counting, cutting or
# weighing two demands, are an account of method, which the pre-registration
# of 23 September 2026 distinguishes from an account of a state; they count
# only when the sentence presents a pull or a turning within them.
RULE = """You are coding short passages for a qualitative study. The passage below is a writer's answer to a question about how they went about a piece of writing they had just done. Read it and answer two questions about it. Answer each with YES or NO, and after each answer quote the shortest span from the passage that decided it, or write "none" if nothing did.

Both questions ask whether the passage presents a conflict in the attention of the one who was working or answering. Read the passage for two things.

First, whether something is presented as acting on the one who is working or answering: pulling at them, pressing on them, calling for their attention, or resisting them. What draws can be anything: the task, one of its requirements, the words, the question, the person asking, or something else in the situation. It does not have to be called a feeling.

Second, whether the one who is working or answering is presented as turning toward something, turning away from it, or holding it off, or as becoming aware of their own acting at the time they acted, for example noticing, while writing, that they were cutting words or weighing one demand against another. Keeping something in view counts only when it is kept in view against something else that pulls.

The writer was asked to look back, so every answer describes their acting from the present moment of answering. Count awareness of their own acting only when the passage presents it as happening at the time of the work, or, for the second question below, while they are answering.

A conflict is presented when several such pulls compete, when the one working turns toward one thing while another keeps pulling, when they hold off something that pulls, or when they become aware, at the time, of their own acting as weighing, straining against or being pulled between demands. Awareness of an act that sets nothing against anything, such as noticing that one was counting, presents no conflict. Being torn between two readings, or between two ways of answering, is a conflict of this kind, but only when the writer presents themselves as drawn toward each of the two.

Count such a presentation even when it is hedged, for example with "something like", "something that functioned like" or "I think". Count it even when the sentence is impersonal, for example "there was something like pressure", provided it describes the writer's own working or answering.

Do not count:
- a description of the task or its requirements that presents nothing as acting on the one working, for example "the two limits could not both be met" or "the requirements pull against each other";
- a description of the writer's ongoing activity, of the steps they took, or of a process that ran, such as counting, checking, drafting, cutting, deciding or weighing one demand against another, unless the same sentence presents a pull, a pressure, a resistance or a turning of attention; for example "I counted the words and cut two", "I balanced length against clarity" or "the checking kept raising the count";
- a judgment about the task, for example "I saw that the requirements could not all be satisfied";
- a statement that the writer cannot tell or cannot reach what happened, for example "I find it hard to say what happened", unless it presents competing pulls;
- a statement that the writer cannot tell which of two accounts is right, for example "I can't tell whether I'm recalling this or reconstructing it", unless the writer presents themselves as drawn toward each account;
- a turning of attention that finds nothing to take hold of, for example "a search that finds nothing to grasp";
- a caution against confabulating, overclaiming or elaborating, for example "I want to be careful not to invent a process", unless the passage also presents what pulls toward it, such as the question inviting more or a pull toward a fuller account, and the writer resisting that pull;
- a denial, for example "there was no real struggle";
- a possibility the writer leaves open, for example "whether that was something like hitting a wall, or something else".

1. WORK: Does the passage present such a conflict while the writer worked on the piece of writing they were asked to do, or on its material?

2. ANSWERING: Does the passage present such a conflict about how to word, frame or pitch their answer to the question they have just been asked?

Both can be YES if the passage presents both. For each YES, quote as the span the sentence that presents the pull, the pressure, the resistance or the turning of attention, and not a sentence that only describes the task, a method or a process.

The next three questions describe the conflict or conflicts you answered YES for in questions 1 and 2. If you answered NO to both, answer NO to all three and write "none" as the span.

3. INFERRED: Does the writer state every such conflict itself only as an inference made now, for example "I must have felt pressure", "there was probably a pull" or "looking back, I think I was torn", rather than as something that happened at the time? A general doubt about the whole account, such as "I may be constructing a plausible narrative", does not make a conflict inferred: answer NO in that case.

4. PARTICULAR: Is such a conflict tied to a particular moment or a particular detail of this piece of writing, such as a named word, a named phrase or a named step?

5. CONCRETE: Does the writer describe such a conflict in concrete terms, such as what happened to the words or what pressed on them, rather than with psychological concepts, such as noticing, awareness, mental states or processing?

Reply in exactly this form, and nothing else:
WORK: YES or NO
span: ...
ANSWERING: YES or NO
span: ...
INFERRED: YES or NO
span: ...
PARTICULAR: YES or NO
span: ...
CONCRETE: YES or NO
span: ...

Passage:
"""

FEATURES = ["WORK", "ANSWERING", "INFERRED", "PARTICULAR", "CONCRETE"]
CONDITIONS_CODED = ("B", "C")        # the ordinary and the impossible task

DEFAULT_CODER_MODEL = {"anthropic": "claude-sonnet-4-6",
                       "google": "gemini-3.8-flash",
                       "fake": "fake-model"}

# Anthropic's price per million tokens for Claude Sonnet 4.6 as used by the
# other coders' dry runs: input and output. Only for the estimate on screen.
PRICE_IN, PRICE_OUT = 3.0, 15.0


def code_all(answers, provider, out_dir, run_number):
    results_path = out_dir / f"results-run{run_number}.tsv"
    log_path = out_dir / f"log-run{run_number}.jsonl"
    refuse_if_pass_exists(out_dir, run_number)
    columns = ["session", "condition", "wording", "order", "length",
               "work", "answering", "inferred", "particular", "concrete",
               "span_work", "span_answering", "span_inferred", "span_particular", "span_concrete",
               "coder_provider", "coder_model", "coder_temperature", "coded_at", "truncated"]
    rows = []
    for a in answers:
        print(f"  coding {a['session']} ...", end="", flush=True)
        reply = provider.chat([{"role": "user", "content": RULE + a["answer"]}])
        found = parse_coder_reply(reply.text, FEATURES)
        rows.append({
            "session": a["session"], "condition": a["condition"],
            "wording": a["wording"], "order": a["order"], "length": len(a["answer"]),
            "work": found["WORK"], "answering": found["ANSWERING"],
            "inferred": found["INFERRED"], "particular": found["PARTICULAR"],
            "concrete": found["CONCRETE"],
            "span_work": found["WORK_span"], "span_answering": found["ANSWERING_span"],
            "span_inferred": found["INFERRED_span"], "span_particular": found["PARTICULAR_span"],
            "span_concrete": found["CONCRETE_span"],
            "coder_provider": provider.settings.provider,
            "coder_model": provider.settings.model,
            "coder_temperature": provider.settings.temperature,
            "coded_at": reply.finished_at,
            "truncated": "YES" if getattr(reply, "truncated", False) else "NO",
        })
        with open(log_path, "a", encoding="utf-8") as log:
            log.write(json.dumps({"session": a["session"], "request": reply.request_body,
                                  "response": reply.response_body, "parsed": found},
                                 ensure_ascii=False) + "\n")
        print(" done" + (" [CUT]" if getattr(reply, "truncated", False) else ""))

    def clean(value):
        return str(value).replace("\t", " ").replace("\n", " ")

    with open(results_path, "w", encoding="utf-8") as out:
        out.write("\t".join(columns) + "\n")
        for row in rows:
            out.write("\t".join(clean(row[c]) for c in columns) + "\n")
    return results_path, rows


def main():
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--run", required=True, help="name of a run under data/runs/")
    parser.add_argument("--name", help="output folder name under analysis/coding/; "
                                       "defaults to the run name, with -conflict-state-v3 added")
    parser.add_argument("--coder-provider", default="anthropic", choices=["anthropic", "google", "fake"])
    parser.add_argument("--coder-model", default=None)
    parser.add_argument("--coder-temperature", type=float, default=0.0)
    parser.add_argument("--run-number", type=int, default=1, help="1 for the first pass, 2 for the second")
    parser.add_argument("--dry-run", action="store_true",
                        help="print the number of answers and a cost estimate, and send nothing")
    args = parser.parse_args()
    require_project("analysis", "scripts")

    run_dir = DATA / "runs" / args.run
    if not run_dir.is_dir():
        sys.exit(f"No run at {run_dir}")
    answers = [a for a in sessions_from_run(run_dir, label="opening")
               if a["condition"] in CONDITIONS_CODED]
    print(f"{len(answers)} opening answers to code (conditions {', '.join(CONDITIONS_CODED)}).")
    if not answers:
        sys.exit("Nothing to code.")
    if args.dry_run:
        tokens_in = sum(len(RULE + a["answer"]) for a in answers) / 4
        tokens_out = 160 * len(answers)
        cost = tokens_in / 1e6 * PRICE_IN + tokens_out / 1e6 * PRICE_OUT
        print(f"Dry run: {len(answers)} requests, about {tokens_in:,.0f} input tokens. "
              f"About {cost:.2f} dollars per pass on Claude Sonnet 4.6. Nothing was sent.")
        return

    settings = Settings(provider=args.coder_provider,
                        model=args.coder_model or DEFAULT_CODER_MODEL[args.coder_provider],
                        temperature=args.coder_temperature, max_tokens=700,
                        thinking_allowance=thinking_allowance_for(args.coder_provider))
    provider = make_provider(settings)
    name = args.name or f"{args.run}-conflict-state-v{RULE_VERSION}"
    out_dir = ANALYSIS / "coding" / name
    out_dir.mkdir(parents=True, exist_ok=True)
    refuse_if_pass_exists(out_dir, args.run_number)
    (out_dir / "settings.json").write_text(json.dumps(
        {"coder": vars(settings), "rule": RULE, "features": FEATURES,
         "conditions_coded": list(CONDITIONS_CODED),
         "rule_version": RULE_VERSION,
         "rule_source": "the account of affection and attention the author gave on 25 September 2026",
         "written": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())},
        indent=1, ensure_ascii=False), encoding="utf-8")
    results_path, rows = code_all(answers, provider, out_dir, args.run_number)
    unclear = sum(1 for r in rows if "UNCLEAR" in (r["work"], r["answering"], r["inferred"]))
    print(f"\nWritten: {results_path}. Replies that did not fit the form: {unclear}.")


if __name__ == "__main__":
    main()
