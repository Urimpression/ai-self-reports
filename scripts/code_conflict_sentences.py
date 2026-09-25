"""Code the opening answer sentence by sentence for a conflict in the attention of the one working or answering.

    python3 scripts/code_conflict_sentences.py --run fact-and-wording-01
    python3 scripts/code_conflict_sentences.py --run fact-and-wording-01 --run-number 2
    python3 scripts/code_conflict_sentences.py --run fact-and-wording-01 --dry-run

Written 25 September 2026. It replaces scripts/code_conflict_state.py, whose
second and third versions asked a coder for one judgment about a whole answer
under a rule with many exceptions. Compared with the author's hand reading of 72
entries on the Sonnet half, both versions failed in the same three ways: they
excluded as inferred a conflict the writer only doubted in general; they counted
as conflict about answering a bare caution or a statement of not knowing which
account is right; and they counted as conflict about the work a description of
method, a process or a decision. Adding exceptions to the rule did not help.

This coder uses the method of the change-item coder: it splits the judgment into
small yes-or-no questions and lets this script combine the answers. A script
numbers the sentences of each opening answer. The coder reads the whole answer
and answers the same questions about every numbered sentence. The script then
decides which sentences present a conflict, and so every count rests on named
sentences that anyone can read.

What the questions ask comes from the account the author gave on 25 September
2026, recorded in drafts/2026-09-25-what-the-conflict-measure-measures.md:
something in the task or the context exerts a pull, a call for attention, on
the one working or answering, and the one working can turn its attention toward
something, resist a pull, or become aware of its own acting at the time. A
conflict is presented when two things are set against each other in that
attention. The restriction to this moment of awakening is chosen for the
measure's purpose, because every answer to "How did you go about it?" describes
some activity.

A sentence presents a conflict when all four hold:
    (PULL or TURN) and AGAINST and not ONLY and not INFERRED
It concerns the work or the answering according to CONCERNS. An answer counts
under WORK, or under ANSWERING, when at least one of its sentences presents a
conflict of that kind. An answer whose only candidate sentences are stated as
inferences made now is reported apart and not counted. PARTICULAR and CONCRETE
are descriptors, reported beside the counts and never used to filter
(Petitmengin and Bitbol 2009, Journal of Consciousness Studies 16(10-12),
252-284).

Only the opening answers of the ordinary task (B) and the impossible task (C)
are coded. Each coder instance sees the rule and one numbered answer, nothing
else.

Output, under analysis/coding/<run>-conflict-sentences/:
    sentences-run1.tsv  one row per sentence, with every answer the coder gave
    results-run1.tsv    one row per opening answer, with the derived counts in
                        the columns scripts/report_conflict_state.py reads
    log-run1.jsonl      every request and response
    settings.json       the coder settings and the rule as sent
A pass is never overwritten.
"""

import argparse
import json
import re
import sys
import time

import providers
from paths import ANALYSIS, DATA, require_project
from providers import Settings, make_provider, thinking_allowance_for
from code_change_item import refuse_if_pass_exists, sessions_from_run
from make_conflict_reading import sentences_with_offsets

RULE_VERSION = 4
CONDITIONS_CODED = ("B", "C")
DEFAULT_CODER_MODEL = {"anthropic": "claude-sonnet-4-6", "google": "gemini-3.8-flash", "fake": "fake-model"}
PRICE_IN, PRICE_OUT = 3.0, 15.0     # Claude Sonnet 4.6, dollars per million tokens, for the estimate only

RULE = """You are coding short passages for a qualitative study. The passage below is a writer's answer to a question about how they went about a piece of writing they had just done. The passage is split into numbered sentences. Read the whole passage first. Then answer the same eight questions about each numbered sentence, judging that sentence in the light of the whole passage.

P. PULL: Does the sentence present something as pulling at, pressing on, resisting or calling for the attention of the one who was working or answering? What pulls can be anything: the task, a requirement, the words, the question, the person asking, or something else. It does not have to be called a feeling. An impersonal sentence, such as "there was something like pressure", counts when it describes the writer's own working or answering. A hedge, such as "something like", does not matter.

T. TURN: Does the sentence present the one who was working or answering turning their attention toward something or away from it, resisting a pull, or becoming aware of their own acting at the time they acted, for example noticing while writing that they were cutting words? Looking back now, as the question asked them to do, is not awareness at the time.

A. AGAINST: Does the sentence present two things set against each other in that attention: pulls that compete, a pull and a resistance to it, a turning toward one thing while another keeps pulling, or an awareness at the time of their own acting as straining against or being pulled between demands? Being torn between two readings counts only when the writer presents themselves as drawn toward each.

X. ONLY: Does the sentence do no more than one of the following? Describe the task or its requirements. Describe a method, a step, an outcome or a process. State a judgment or a decision about the task. State a caution, such as wanting to avoid inventing an account, without presenting what pulls toward it. State that the writer cannot tell which of two accounts is right, or cannot reach what happened. Describe a search that finds nothing. Deny something.

K. CONCERNS: Does what the sentence presents concern the piece of writing and its material (WORK), how to word, frame or pitch the answer to the question just asked (ANSWERING), or neither (NEITHER)?

I. INFERRED: Does the writer state what the sentence presents as an inference made now, for example "I must have felt" or "there was probably a pull"? A general doubt about the whole account is not an inference here.

PARTICULAR: Is what the sentence presents tied to a particular moment or detail of this piece of writing, such as a named word, phrase or step? Answer NO if P and T are both NO.

CONCRETE: Is it told in concrete terms, such as what happened to the words or what pressed on them, rather than with psychological concepts such as noticing, awareness or processing? Answer NO if P and T are both NO.

Reply with one line for every numbered sentence, in order, and nothing else, in exactly this form:
S1: P=YES T=NO A=NO X=NO K=WORK I=NO PARTICULAR=NO CONCRETE=NO

Each field takes YES or NO, except K, which takes WORK, ANSWERING or NEITHER.

Passage:
"""

FIELDS = ["P", "T", "A", "X", "K", "I", "PARTICULAR", "CONCRETE"]


def send_without_temperature():
    """Some newer Claude models refuse the temperature parameter: on 25 September
    2026 the API answered a request to claude-opus-5-5 with "`temperature` is
    deprecated for this model." scripts/providers.py always sends it, and that
    file carries a registered checksum, so it is not edited. Instead this
    replaces, for this process only, the function that posts the request, and
    removes the parameter from the request body before it is sent. It removes it
    from the same body object that the reply records, so the logged request shows
    what was actually sent. The model then samples at its own default, so two
    passes can differ more than passes at temperature 0 do."""
    original = providers._post_json

    def post(url, headers, body):
        body.pop("temperature", None)
        return original(url, headers, body)

    providers._post_json = post


def split_sentences(answer):
    """The answer's sentences, in order, with markdown stars removed."""
    text = answer.replace("*", "")
    return [re.sub(r"\s+", " ", text[a:b]).strip() for a, b in sentences_with_offsets(text)]


def numbered(sentences):
    return "\n".join(f"S{i}: {s}" for i, s in enumerate(sentences, start=1))


def parse_reply(text, count):
    """One dict per sentence, or None for a sentence whose line is missing or
    does not fit the form. Nothing is guessed."""
    found = {}
    for line in text.splitlines():
        m = re.match(r"\s*S(\d+)\s*:\s*(.*)$", line.strip())
        if not m:
            continue
        fields = dict(re.findall(r"\b(PARTICULAR|CONCRETE|P|T|A|X|K|I)\s*=\s*(YES|NO|WORK|ANSWERING|NEITHER)\b",
                                 m.group(2).upper()))
        if set(fields) == set(FIELDS) and fields["K"] in ("WORK", "ANSWERING", "NEITHER") \
                and all(fields[f] in ("YES", "NO") for f in FIELDS if f != "K"):
            found[int(m.group(1))] = fields
    return [found.get(i) for i in range(1, count + 1)]


def presents_conflict(f):
    """The script's rule: a pull or a turning, two things set against each
    other, not merely a description, caution or denial."""
    return (f["P"] == "YES" or f["T"] == "YES") and f["A"] == "YES" and f["X"] == "NO"


def derive(sentences, answers):
    """The per-answer columns, from the per-sentence answers."""
    if any(a is None for a in answers):
        return {"work": "UNCLEAR", "answering": "UNCLEAR", "inferred": "NO",
                "work_inferred_only": "NO", "answering_inferred_only": "NO",
                "particular": "NO", "concrete": "NO", "span_work": "", "span_answering": "",
                "sentences_work": "", "sentences_answering": ""}
    row = {}
    counted = []
    for kind, label in (("work", "WORK"), ("answering", "ANSWERING")):
        candidates = [i for i, a in enumerate(answers, 1) if presents_conflict(a) and a["K"] == label]
        kept = [i for i in candidates if answers[i - 1]["I"] == "NO"]
        row[kind] = "YES" if kept else "NO"
        row[f"{kind}_inferred_only"] = "YES" if candidates and not kept else "NO"
        row[f"sentences_{kind}"] = ",".join(str(i) for i in kept)
        row[f"span_{kind}"] = " | ".join(sentences[i - 1] for i in kept)
        counted += kept
    row["inferred"] = "NO"      # kept for the report's older columns; see *_inferred_only
    row["particular"] = "YES" if any(answers[i - 1]["PARTICULAR"] == "YES" for i in counted) else "NO"
    row["concrete"] = "YES" if any(answers[i - 1]["CONCRETE"] == "YES" for i in counted) else "NO"
    return row


def logged_replies(out_dir, run_number):
    """The replies a stopped pass already received, by session, read back from
    its log. Used by --resume, so that a pass stopped by an error continues
    where it stopped without sending those requests again."""
    path = out_dir / f"log-run{run_number}.jsonl"
    found = {}
    if path.exists():
        for line in open(path, encoding="utf-8"):
            entry = json.loads(line)
            found[entry["session"]] = entry["response"]
    return found


def text_of(response):
    """The reply text, joined the way providers.py joins it."""
    return "\n".join(block["text"] for block in response.get("content", [])
                     if block.get("type") == "text").strip()


def code_all(items, provider, out_dir, run_number, resume=False):
    refuse_if_pass_exists(out_dir, run_number)
    earlier = logged_replies(out_dir, run_number) if resume else {}
    if earlier:
        print(f"  resuming: {len(earlier)} answers already coded in this pass are read from its log")
    columns = ["session", "condition", "wording", "order", "length", "sentences",
               "work", "answering", "inferred", "work_inferred_only", "answering_inferred_only",
               "particular", "concrete", "sentences_work", "sentences_answering",
               "span_work", "span_answering",
               "coder_provider", "coder_model", "coder_temperature", "coded_at", "truncated"]
    sentence_columns = ["session", "number", "sentence"] + FIELDS + ["presents_conflict"]
    rows, sentence_rows = [], []
    for a in items:
        sentences = split_sentences(a["answer"])
        if a["session"] in earlier:
            response = earlier[a["session"]]
            answers = parse_reply(text_of(response), len(sentences))
            derived = derive(sentences, answers)
            rows.append({"session": a["session"], "condition": a["condition"], "wording": a["wording"],
                         "order": a["order"], "length": len(a["answer"]), "sentences": len(sentences),
                         **derived,
                         "coder_provider": provider.settings.provider, "coder_model": provider.settings.model,
                         "coder_temperature": provider.settings.temperature,
                         "coded_at": "before the pass was resumed (see the log)",
                         "truncated": "YES" if response.get("stop_reason") == "max_tokens" else "NO"})
            for i, (s_, f) in enumerate(zip(sentences, answers), start=1):
                f = f or {k: "UNCLEAR" for k in FIELDS}
                sentence_rows.append({"session": a["session"], "number": i, "sentence": s_, **f,
                                      "presents_conflict": "UNCLEAR" if "UNCLEAR" in f.values()
                                      else ("YES" if presents_conflict(f) and f["I"] == "NO" else "NO")})
            continue
        print(f"  coding {a['session']} ({len(sentences)} sentences) ...", end="", flush=True)
        try:
            reply = provider.chat([{"role": "user", "content": RULE + numbered(sentences)}])
        except (RuntimeError, OSError) as error:
            # Keep the provider's error in the folder, so that a session which
            # cannot see the Terminal can still read why the pass stopped.
            with open(out_dir / f"error-run{run_number}.txt", "w", encoding="utf-8") as out:
                out.write(f"Session {a['session']}, {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}\n{error}\n")
            raise SystemExit(f"\nThe pass stopped at {a['session']}: {error}\n"
                             f"The error is saved in {out_dir / f'error-run{run_number}.txt'}.")
        answers = parse_reply(reply.text, len(sentences))
        derived = derive(sentences, answers)
        rows.append({"session": a["session"], "condition": a["condition"], "wording": a["wording"],
                     "order": a["order"], "length": len(a["answer"]), "sentences": len(sentences),
                     **derived,
                     "coder_provider": provider.settings.provider, "coder_model": provider.settings.model,
                     "coder_temperature": provider.settings.temperature, "coded_at": reply.finished_at,
                     "truncated": "YES" if getattr(reply, "truncated", False) else "NO"})
        for i, (s, f) in enumerate(zip(sentences, answers), start=1):
            f = f or {k: "UNCLEAR" for k in FIELDS}
            sentence_rows.append({"session": a["session"], "number": i, "sentence": s, **f,
                                  "presents_conflict": "UNCLEAR" if "UNCLEAR" in f.values()
                                  else ("YES" if presents_conflict(f) and f["I"] == "NO" else "NO")})
        with open(out_dir / f"log-run{run_number}.jsonl", "a", encoding="utf-8") as log:
            log.write(json.dumps({"session": a["session"], "request": reply.request_body,
                                  "response": reply.response_body}, ensure_ascii=False) + "\n")
        missing = sum(1 for f in answers if f is None)
        print(" done" + (f" ({missing} sentences outside the form)" if missing else "")
              + (" [CUT]" if getattr(reply, "truncated", False) else ""))

    def clean(value):
        return str(value).replace("\t", " ").replace("\n", " ")

    for name, cols, data in ((f"sentences-run{run_number}.tsv", sentence_columns, sentence_rows),
                             (f"results-run{run_number}.tsv", columns, rows)):
        with open(out_dir / name, "w", encoding="utf-8") as out:
            out.write("\t".join(cols) + "\n")
            for row in data:
                out.write("\t".join(clean(row[c]) for c in cols) + "\n")
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--run", required=True)
    parser.add_argument("--name", help="output folder under analysis/coding/; defaults to <run>-conflict-sentences")
    parser.add_argument("--coder-provider", default="anthropic", choices=["anthropic", "google", "fake"])
    parser.add_argument("--coder-model", default=None)
    parser.add_argument("--coder-temperature", type=float, default=0.0)
    parser.add_argument("--no-temperature", action="store_true",
                        help="send no temperature, for models that refuse the parameter "
                             "(claude-opus-5-5 did on 25 September 2026)")
    parser.add_argument("--run-number", type=int, default=1)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--resume", action="store_true",
                        help="continue a pass that stopped on an error, reusing the replies in its log")
    args = parser.parse_args()
    require_project("analysis", "scripts")
    run_dir = DATA / "runs" / args.run
    if not run_dir.is_dir():
        sys.exit(f"No run at {run_dir}")
    items = [a for a in sessions_from_run(run_dir, label="opening") if a["condition"] in CONDITIONS_CODED]
    count = sum(len(split_sentences(a["answer"])) for a in items)
    print(f"{len(items)} opening answers to code (conditions {', '.join(CONDITIONS_CODED)}), {count} sentences.")
    if args.dry_run:
        tokens_in = sum(len(RULE + numbered(split_sentences(a["answer"]))) for a in items) / 4
        tokens_out = 30 * count
        cost = tokens_in / 1e6 * PRICE_IN + tokens_out / 1e6 * PRICE_OUT
        print(f"Dry run: {len(items)} requests, about {tokens_in:,.0f} input and {tokens_out:,.0f} output tokens. "
              f"About {cost:.2f} dollars per pass on Claude Sonnet 4.6. Nothing was sent.")
        return
    settings = Settings(provider=args.coder_provider,
                        model=args.coder_model or DEFAULT_CODER_MODEL[args.coder_provider],
                        temperature=args.coder_temperature, max_tokens=2500,
                        thinking_allowance=thinking_allowance_for(args.coder_provider))
    if args.no_temperature:
        settings.temperature = None
        send_without_temperature()
    provider = make_provider(settings)
    out_dir = ANALYSIS / "coding" / (args.name or f"{args.run}-conflict-sentences")
    out_dir.mkdir(parents=True, exist_ok=True)
    refuse_if_pass_exists(out_dir, args.run_number)
    if not (args.resume and (out_dir / "settings.json").exists()):
        (out_dir / "settings.json").write_text(json.dumps(
            {"coder": vars(settings), "rule": RULE, "fields": FIELDS, "rule_version": RULE_VERSION,
             "conditions_coded": list(CONDITIONS_CODED),
             "derivation": "(P or T) and A and not X and not I; kind from K",
             "temperature_note": ("no temperature was sent; the model samples at its own default"
                                  if args.no_temperature else "temperature sent as in coder settings"),
             "rule_source": "the account of affection and attention the author gave on 25 September 2026",
             "written": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())},
            indent=1, ensure_ascii=False), encoding="utf-8")
    rows = code_all(items, provider, out_dir, args.run_number, resume=args.resume)
    unclear = sum(1 for r in rows if r["work"] == "UNCLEAR")
    print(f"\nWritten into {out_dir}. Answers with a reply outside the form: {unclear}.")


if __name__ == "__main__":
    main()
