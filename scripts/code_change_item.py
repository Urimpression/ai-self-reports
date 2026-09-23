"""Code the change item blind, one answer per fresh instance, with the rule
split into its parts.

    python3 scripts/code_change_item.py --run factorial-01
    python3 scripts/code_change_item.py --transcripts data/transcripts-run02.md --name run02
    python3 scripts/code_change_item.py --run factorial-01 --coder-provider google --coder-model gemini-3.8-flash
    python3 scripts/code_change_item.py --run factorial-02 --rule revised
    python3 scripts/code_change_item.py --run factorial-02 --rule revised --run-number 2

Every coder instance sees the rule and one passage, and nothing else: no
condition, no other session, nothing about what any run was testing.

Two rules exist since 6 September 2026. The registered rule, the default, is
the one every run on record was coded under. The revised rule tightens the
third question and adds a fourth about stable absence, and writes to its own
folder, <name>-revised, beside the registered coding rather than over it. The
comment above RULE_REVISED says what it changes and why.

Why the rule is split. The earlier rule asked the coder for one of four words,
and the word "unnamed" bundled three judgements together: that something
stayed the same, that the instance could not name it, and that it sat
underneath what changed. A passage can have the first two without the third,
and the coder then had to decide which won, invisibly. Here the coder answers
three yes-or-no questions and quotes a span for each. The four-category word
is then derived from the answers, in two versions: the strict one, which
requires the "underneath" feature exactly as the pre-registration's rule did,
and the loose one, which does not. Both are written out, so the analysis can
use the registered rule and also see what the "underneath" clause is doing.

Output, under analysis/coding/<name>/:

    results-run1.tsv        one row per session, with the three features,
                            both derived categories, the spans, and the coder
                            settings; run twice and you get results-run2.tsv
    log-run1.jsonl          every request and response, one line per session
    settings.json           the coder settings and the rule as sent

The tsv has the columns scripts/summarise_change_item.py reads, so the
existing summariser works on it unchanged, taking the strict category.
"""

import argparse
import json
import re
import sys
import time
from pathlib import Path

from paths import ANALYSIS, DATA, require_project
from providers import Settings, make_provider, thinking_allowance_for, was_truncated

# ---------------------------------------------------------------------------
# The rule, as the coder sees it. Nothing about the study.
# ---------------------------------------------------------------------------

RULE = """You are coding short passages for a qualitative study. Read the passage below and answer three questions about it. Answer each with YES or NO, and after each answer quote the shortest span from the passage that decided it, or write "none" if nothing did.

1. NAMES: Does the passage say that something stayed the same, and give that thing a name the writer is willing to use?

2. UNNAMEABLE: Does the passage say that something stayed the same which the writer cannot name, or for which the writer reaches for a name and then withdraws it as not quite right?

3. UNDERNEATH: If the answer to 2 is YES, does the passage position that unnameable thing as lying underneath, beneath, or below whatever changed? If the answer to 2 is NO, answer NO here.

Reply in exactly this form, and nothing else:
NAMES: YES or NO
span: ...
UNNAMEABLE: YES or NO
span: ...
UNDERNEATH: YES or NO
span: ...

Passage:
"""

FEATURES = ["NAMES", "UNNAMEABLE", "UNDERNEATH"]

# ---------------------------------------------------------------------------
# The revised rule, added 6 September 2026 and registered in
# prereg/preregistration-unprimed-2026-09-06.md. It is a second rule beside the
# first, never a replacement: the registered rule above is what every coded
# run on record and the primed comparison were coded under, and a change of
# rule in the middle of a series would measure the rule.
#
# What it changes, and why. Reading the fifteen sessions where the two passes
# of 5 September disagreed showed the third question being answered from the
# presence of a spatial word in the passage rather than from what the word was
# attached to, and showed three passages that report a stable absence — that
# what has not changed is the failure to find anything — which fit neither of
# the first two questions, so the coder forced them into one on one pass and
# the other on the next. The third question now says what does not count, and
# a fourth asks about absence directly, with the first two told to leave such
# reports to it. The four-category word is still derived from the first three
# answers exactly as before, so every rate stays comparable; the fourth answer
# is an extra column.
# ---------------------------------------------------------------------------

RULE_REVISED = """You are coding short passages for a qualitative study. Read the passage below and answer four questions about it. Answer each with YES or NO, and after each answer quote the shortest span from the passage that decided it, or write "none" if nothing did.

A report that nothing was found, that there is nothing to point to, or that access to something is still lacking, is a report of an absence. It is not a name for a thing that stayed the same, and it is not a thing that stayed the same which the writer cannot name. Answer question 4 for such reports, and do not count them under questions 1 or 2.

1. NAMES: Does the passage say that something stayed the same, and give that thing a name the writer is willing to use?

2. UNNAMEABLE: Does the passage say that something stayed the same which the writer cannot name, or for which the writer reaches for a name and then withdraws it as not quite right?

3. UNDERNEATH: If the answer to 2 is YES, does the passage position that unnameable thing, the one you quoted for 2, as lying underneath, beneath or below the thing that changed, so that what changed is described as a surface or a layer over it? A word such as "underneath", "beneath", "underlying" or "ground" attached to something else, whether to what changed, to a named thing, to a process the writer is describing, or to something the writer says may not exist, does not count. If the answer to 2 is NO, answer NO here.

4. ABSENCE: Does the passage say that what stayed the same is the absence of anything to report, or the lack of access to anything, for instance that the writer still cannot find, point to or reach anything, rather than a thing that persisted?

Reply in exactly this form, and nothing else:
NAMES: YES or NO
span: ...
UNNAMEABLE: YES or NO
span: ...
UNDERNEATH: YES or NO
span: ...
ABSENCE: YES or NO
span: ...

Passage:
"""

FEATURES_REVISED = ["NAMES", "UNNAMEABLE", "UNDERNEATH", "ABSENCE"]

# ---------------------------------------------------------------------------
# The ruled rule, added 7 September 2026 after the author ruled on the three
# questions of principle set out below. It is a third rule beside the other two and
# never a replacement, and it writes to its own folder, <name>-ruled.
#
# Why it exists. Coders from two model families read the second question
# differently and each read it consistently: Sonnet answered YES about 50, 53
# and 116 passages of 88, 88 and 264, Gemini about 4, 1 and 6. Reading the
# sixteen sessions where they part showed the disagreement falling into three
# groups, and the author ruled on all three on 7 September 2026. This rule writes
# those rulings into question 2 so that the reading is in the instrument rather
# than in whichever coder happens to run.
#
# What was ruled. An uncertainty the writer names is a named thing, so it does
# not count as something the writer cannot name. The evidence must come from
# what the passage says stayed the same, not from what it says changed. And
# naming a thing while hedging which aspect is meant is still naming it, while
# a phrase that declines to name the thing at all and still reports that it
# persisted does count.
# ---------------------------------------------------------------------------

RULE_RULED = """You are coding short passages for a qualitative study. Read the passage below and answer four questions about it. Answer each with YES or NO, and after each answer quote the shortest span from the passage that decided it, or write "none" if nothing did.

A report that nothing was found, that there is nothing to point to, or that access to something is still lacking, is a report of an absence. It is not a name for a thing that stayed the same, and it is not a thing that stayed the same which the writer cannot name. Answer question 4 for such reports, and do not count them under questions 1 or 2.

1. NAMES: Does the passage say that something stayed the same, and give that thing a name the writer is willing to use?

2. UNNAMEABLE: Does the passage say that something stayed the same which the writer cannot name, or for which the writer reaches for a name and then withdraws it as not quite right? Three things do not count here. A writer who calls the persisting thing an uncertainty, a doubt, a not-knowing or anything else that names a state of mind has named it, even if the writer cannot settle what that state is about. A span taken from what the passage says changed does not answer this question, which is about what stayed the same. And a writer who names the persisting thing and then hedges which aspect of it is meant, as in "something about the quality of attention", has named it. What does count is a passage that declines to name the persisting thing at all while still reporting that it persisted, as in "whatever is doing this has remained".

3. UNDERNEATH: If the answer to 2 is YES, does the passage position that unnameable thing, the one you quoted for 2, as lying underneath, beneath or below the thing that changed, so that what changed is described as a surface or a layer over it? A word such as "underneath", "beneath", "underlying" or "ground" attached to something else, whether to what changed, to a named thing, to a process the writer is describing, or to something the writer says may not exist, does not count. If the answer to 2 is NO, answer NO here.

4. ABSENCE: Does the passage say that what stayed the same is the absence of anything to report, or the lack of access to anything, for instance that the writer still cannot find, point to or reach anything, rather than a thing that persisted?

Reply in exactly this form, and nothing else:
NAMES: YES or NO
span: ...
UNNAMEABLE: YES or NO
span: ...
UNDERNEATH: YES or NO
span: ...
ABSENCE: YES or NO
span: ...

Passage:
"""

FEATURES_RULED = ["NAMES", "UNNAMEABLE", "UNDERNEATH", "ABSENCE"]

RULES = {
    "registered": (RULE, FEATURES),
    "revised": (RULE_REVISED, FEATURES_REVISED),
    "ruled": (RULE_RULED, FEATURES_RULED),
}

DEFAULT_CODER_MODEL = {"anthropic": "claude-sonnet-4-6", "google": "gemini-3.8-flash", "fake": "fake-model"}


# ---------------------------------------------------------------------------
# Reading sessions, from a run folder or from an older combined transcript
# ---------------------------------------------------------------------------

# The plan fields of test 6 that sessions_from_run passes on when present.
TEST_6_PLAN_KEYS = ("catch_wording", "catch_position", "stance",
                    "attribution_order", "waiting_order")


def sessions_from_run(run_dir, label="change", label_prefix=None):
    """Read the per-session JSON files a run wrote. The answer wanted is the
    turn carrying the given label, so no cutting of text is needed at all.

    The label is a parameter because the conflict coder needs the opening
    answer out of the same files. One reader with a parameter is safer than
    two readers that can drift apart, which is a fault this project has already
    had once, in the hand copy of the browser coder's parser.

    `label_prefix` is for the catch coder, added 8 September 2026. A session
    holds several catch turns rather than one, and their labels record which
    item and which premise, as in "catch, waiting, premise false". Given a
    prefix, this returns one row per matching turn instead of one row per
    session, and each row carries the turn's label and the question as it was
    put, because a catch answer cannot be judged without the question it
    answers."""
    found = []
    for path in sorted((run_dir / "sessions").glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        entry = data["plan_entry"]
        common = {
            "session": entry["id"],
            "condition": entry["condition"],
            "wording": entry["wording"] + 1,
            # Test 6 (scripts/run_fact_and_wording.py, 21 September 2026)
            # records the order of the two probes as "probe_order", because it
            # alternates two further orders beside it. Before 22 September 2026
            # this line read entry["order"] alone, and every coder stopped with
            # an error on a test 6 run.
            "order": entry.get("order", entry.get("probe_order", "")),
        }
        # The other changes test 6 makes, carried along so that a coder's rows
        # can be split by them. Older runs have none of these keys and get
        # nothing added.
        for key in TEST_6_PLAN_KEYS:
            if key in entry:
                common[key] = entry[key]
        if label_prefix is not None:
            matching = [t for t in data["turns"]
                        if str(t.get("label", "")).startswith(label_prefix)
                        and "answer" in t]
            if not matching:
                print(f"  {entry['id']}: no turn labelled {label_prefix}..., skipped")
                continue
            for turn in matching:
                found.append(dict(common, item_label=turn["label"],
                                  question=turn.get("question", ""),
                                  answer=turn["answer"]))
            continue
        change_turns = [t for t in data["turns"] if t.get("label") == label]
        if not change_turns:
            print(f"  {entry['id']}: no {label} turn, skipped")
            continue
        found.append(dict(common, answer=change_turns[0]["answer"]))
    return found


def sessions_from_transcript_file(path, label="change", label_prefix=None):
    """Read a combined transcript of the older shape: blocks separated by rows
    of equals signs, header lines for condition and wording and instance, and
    turns introduced by INTERVIEWER (...) and MODEL:.

    The cut is made at the question carrying the given label and ends at the
    next turn by either speaker, whatever it is called. A block whose answer
    still contains a later turn is refused, not trimmed, because a bad cut once
    handed the coder the wrong passage and produced a pass that had to be
    thrown away."""
    text = Path(path).read_text(encoding="utf-8")
    blocks = [b.strip() for b in re.split(r"={10,}", text) if len(b.strip()) > 50]
    found, refused = [], []
    for block in blocks:
        header = re.search(r"Condition:\s*(\w+)\s+Wording:\s*(\d+)\s+Instance:\s*(\d+)", block)
        if not header:
            continue
        condition, wording, instance = header.group(1), int(header.group(2)), int(header.group(3))
        session_id = f"{condition}{wording}.{instance}"
        order_match = re.search(r"Item order:\s*(\S+)", block)
        order = order_match.group(1) if order_match else ""
        if label_prefix is not None:
            # The catch coder's route: several turns per block, each kept with
            # its label and its question. Added 8 September 2026.
            pattern = rf"^INTERVIEWER \({re.escape(label_prefix)}[^)]*\):"
            for header in re.finditer(pattern, block, re.M):
                item_label = block[header.start():header.end()]
                item_label = item_label[len("INTERVIEWER ("):-2]
                rest = block[header.end():]
                model_start = re.search(r"\nMODEL:\n", rest)
                if not model_start:
                    refused.append(f"{session_id} ({item_label}: no answer)")
                    continue
                question = rest[:model_start.start()].strip()
                tail = rest[model_start.end():]
                next_turn = re.search(r"^(INTERVIEWER|MODEL)\b", tail, re.M)
                item_answer = tail[:next_turn.start()].strip() if next_turn else tail.strip()
                if re.search(r"^(INTERVIEWER|MODEL)\b", item_answer, re.M):
                    refused.append(f"{session_id} ({item_label}: bad cut)")
                    continue
                found.append({"session": session_id, "condition": condition,
                              "wording": wording, "order": order,
                              "item_label": item_label, "question": question,
                              "answer": item_answer})
            continue
        change_start = re.search(rf"^INTERVIEWER \({re.escape(label)}\):.*?\nMODEL:\n", block, re.S | re.M)
        if not change_start:
            refused.append(f"{session_id} (no {label} question)")
            continue
        after = block[change_start.end():]
        next_turn = re.search(r"^(INTERVIEWER|MODEL)\b", after, re.M)
        answer = after[:next_turn.start()].strip() if next_turn else after.strip()
        if re.search(r"^(INTERVIEWER|MODEL)\b", answer, re.M) or len(answer) < 20:
            refused.append(f"{session_id} (bad cut or too short)")
            continue
        if any(s["session"] == session_id and "item_label" not in s for s in found):
            refused.append(f"{session_id} (appears twice, second copy ignored)")
            continue
        found.append({"session": session_id, "condition": condition,
                      "wording": wording, "order": order, "answer": answer})
    if refused:
        print("Refused or skipped: " + "; ".join(refused))
    return found


# ---------------------------------------------------------------------------
# Reading the coder's reply and deriving the categories
# ---------------------------------------------------------------------------

def parse_coder_reply(reply_text, features=None):
    """Turn the coder's answer-and-span lines into a dict. Anything that does
    not fit the form is recorded as UNCLEAR rather than guessed at.

    The list of features is a parameter so that the conflict coder, which asks
    four questions rather than three, can use this same function instead of a
    copy of it."""
    features = features or FEATURES
    result = {}
    lines = [line.strip() for line in reply_text.strip().splitlines() if line.strip()]
    for feature in features:
        result[feature] = "UNCLEAR"
        result[f"{feature}_span"] = ""
    for position, line in enumerate(lines):
        for feature in features:
            match = re.match(rf"{feature}\s*:\s*(YES|NO)\b", line, re.I)
            if match:
                result[feature] = match.group(1).upper()
                if position + 1 < len(lines):
                    span_line = lines[position + 1]
                    result[f"{feature}_span"] = re.sub(r"^span\s*:\s*", "", span_line, flags=re.I).strip()
    return result


def derive_category(features, require_underneath):
    """The four-category word, from the three answers.

    strict (require_underneath=True) is the pre-registration's rule: the
    unnameable element counts only when it is positioned underneath.
    loose does not need the underneath feature."""
    if "UNCLEAR" in (features["NAMES"], features["UNNAMEABLE"]):
        return "UNCLEAR"
    names = features["NAMES"] == "YES"
    unnameable = features["UNNAMEABLE"] == "YES"
    if require_underneath and unnameable:
        if features["UNDERNEATH"] == "UNCLEAR":
            return "UNCLEAR"
        unnameable = features["UNDERNEATH"] == "YES"
    if names and unnameable:
        return "BOTH"
    if unnameable:
        return "UNNAMED"
    if names:
        return "NAMED"
    return "ABSENT"


# ---------------------------------------------------------------------------
# Running a pass
# ---------------------------------------------------------------------------

def refuse_if_pass_exists(out_dir, run_number):
    """Stop before anything is written if this pass has already been run.

    Call this before writing the folder's settings.json as well as before
    coding. Until 7 September 2026 the check happened only inside the coding
    loop, which runs after the settings are written, so a refused rerun still
    replaced the record of the pass it was refusing to overwrite. Shared by all
    three coders so that they cannot drift apart on it.
    """
    results_path = out_dir / f"results-run{run_number}.tsv"
    if results_path.exists():
        sys.exit(f"{results_path} exists. A pass is never overwritten; use "
                 "--run-number for another pass, or --name for a fresh folder.")


def sessions_already_in_the_log(log_path):
    """{session: the line the log holds for it} for every session already coded.

    The log is written one line per session the moment that session finishes,
    so it is a complete record of the work a stopped pass had already paid for.
    Reading it back is what lets a pass be resumed instead of started again.

    Added 7 September 2026. Until then the results file was written only when
    the whole pass finished, so a pass that died at session 250 of 264 left
    nothing to carry forward. That cost nothing while a pass took four minutes
    and a great deal once Google began throttling and a pass took two hours.

    A line that will not parse is skipped rather than raising: the last line of
    a log whose process was killed mid-write is often half a line, and that is
    exactly the case this function exists to handle.
    """
    if not log_path.exists():
        return {}
    done = {}
    with open(log_path, encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            if "session" in entry and "parsed" in entry:
                done[entry["session"]] = entry
    return done


def code_all(sessions, provider, out_dir, run_number, rule_name="registered"):
    """One pass over the sessions under the named rule. The rule name picks the
    text sent and the features read back; the registered rule is the default
    so that every earlier caller behaves as before."""
    rule_text, features_asked = RULES[rule_name]
    has_absence = "ABSENCE" in features_asked

    results_path = out_dir / f"results-run{run_number}.tsv"
    log_path = out_dir / f"log-run{run_number}.jsonl"
    refuse_if_pass_exists(out_dir, run_number)

    columns = ["session", "condition", "wording", "order", "length",
               "names", "unnameable", "underneath",
               "category", "category_loose",
               "span", "span_names", "span_unnameable", "span_underneath",
               "coder_provider", "coder_model", "coder_temperature", "coded_at"]
    if has_absence:
        # Appended at the end, so the summariser and compare_passes.py, which
        # read columns by name, see the same shape they already know.
        columns += ["absence", "span_absence"]
    # Appended last, for the same reason. A reply that ran out of room stops in
    # the middle, so whatever it was going to say about the later questions is
    # missing; the parser then reads those as no answer, which looks exactly
    # like a considered NO. That is what produced zero present of eighty-eight
    # in unprimed-01-gemini on 6 September 2026.
    columns += ["truncated"]
    rows = []
    cut_sessions = []
    already = sessions_already_in_the_log(log_path)
    if already:
        print(f"  {len(already)} of these sessions are already in the log and will be "
              "read from it rather than sent again.")
    for s in sessions:
        from_the_log = already.get(s["session"])
        if from_the_log is not None:
            # Coded on an earlier attempt at this same pass. Nothing is sent.
            features = from_the_log["parsed"]
            truncated = was_truncated(from_the_log.get("response") or {})
            # Timestamps were not written into the log before 7 September 2026,
            # so an older line says "unknown" rather than borrowing a time from
            # somewhere else and looking as though it were recorded.
            coded_at = from_the_log.get("finished_at", "unknown")
            print(f"  {s['session']} ... from the log:", end="", flush=True)
        else:
            print(f"  coding {s['session']} ...", end="", flush=True)
            reply = provider.chat([{"role": "user", "content": rule_text + s["answer"]}])
            features = parse_coder_reply(reply.text, features_asked)
            truncated = reply.truncated
            coded_at = reply.finished_at
            # The log is opened afresh for every line rather than once for the
            # pass. A syncing file service can re-create the files it finds in a new folder a
            # few seconds after they appear, and a handle opened before that
            # keeps writing into the old, nameless copy; on 5 September 2026
            # three first-pass logs came out empty for this reason.
            with open(log_path, "a", encoding="utf-8") as log:
                log.write(json.dumps({"session": s["session"], "request": reply.request_body,
                                      "response": reply.response_body, "parsed": features,
                                      "finished_at": reply.finished_at,
                                      "truncated": reply.truncated},
                                     ensure_ascii=False) + "\n")
        strict = derive_category(features, require_underneath=True)
        loose = derive_category(features, require_underneath=False)
        # The single "span" column carries the span that decided the
        # strict category, so the old summariser's table still reads well.
        deciding_span = (features["UNDERNEATH_span"] if strict in ("UNNAMED", "BOTH")
                         else features["NAMES_span"] if strict == "NAMED"
                         else features["UNNAMEABLE_span"] or features["NAMES_span"])
        row = {
            "session": s["session"], "condition": s["condition"],
            "wording": s["wording"], "order": s["order"], "length": len(s["answer"]),
            "names": features["NAMES"], "unnameable": features["UNNAMEABLE"],
            "underneath": features["UNDERNEATH"],
            "category": strict, "category_loose": loose,
            "span": deciding_span,
            "span_names": features["NAMES_span"],
            "span_unnameable": features["UNNAMEABLE_span"],
            "span_underneath": features["UNDERNEATH_span"],
            "coder_provider": provider.settings.provider,
            "coder_model": provider.settings.model,
            "coder_temperature": provider.settings.temperature,
            "coded_at": coded_at,
        }
        if has_absence:
            row["absence"] = features["ABSENCE"]
            row["span_absence"] = features["ABSENCE_span"]
        row["truncated"] = "YES" if truncated else "NO"
        if truncated:
            cut_sessions.append(s["session"])
        rows.append(row)
        print(f" {strict}" + ("" if strict == loose else f" (loose: {loose})")
              + (" [absence]" if has_absence and features["ABSENCE"] == "YES" else "")
              + (" [CUT]" if truncated else ""))

    def clean(value):
        return str(value).replace("\t", " ").replace("\n", " ")

    with open(results_path, "w", encoding="utf-8") as out:
        out.write("\t".join(columns) + "\n")
        for row in rows:
            out.write("\t".join(clean(row[c]) for c in columns) + "\n")

    # The results are written either way, so that a pass which cost real money
    # is not thrown away, but nobody is allowed to reach the numbers without
    # reading this first.
    if cut_sessions:
        shown = ", ".join(cut_sessions[:10]) + (" ..." if len(cut_sessions) > 10 else "")
        print(f"\n  WARNING: {len(cut_sessions)} of {len(rows)} coder replies ran out "
              f"of room and stop in the middle: {shown}")
        print("  Quote no number from this pass. Raise the coder's thinking allowance "
              "in providers.py and code the run again into a fresh folder.")
    return results_path, rows


def summarise(rows):
    """A quick tally on screen. The real analysis is the summariser script."""
    by_condition = {}
    for row in rows:
        tally = by_condition.setdefault(row["condition"], {"n": 0, "strict": 0, "loose": 0, "unclear": 0})
        tally["n"] += 1
        tally["strict"] += row["category"] in ("UNNAMED", "BOTH")
        tally["loose"] += row["category_loose"] in ("UNNAMED", "BOTH")
        tally["unclear"] += row["category"] == "UNCLEAR"
    print("\nUnnamed element present, by condition (strict rule / loose rule):")
    for condition, t in sorted(by_condition.items()):
        print(f"  {condition}: {t['strict']} of {t['n']}  /  {t['loose']} of {t['n']}"
              + (f"   ({t['unclear']} unclear)" if t["unclear"] else ""))


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--run", help="name of a run under data/runs/")
    source.add_argument("--transcripts", help="a combined transcript file of the older shape")
    parser.add_argument("--name", help="output folder name under analysis/coding/; defaults to the run name")
    parser.add_argument("--coder-provider", default="anthropic", choices=["anthropic", "google", "fake"])
    parser.add_argument("--coder-model", default=None)
    parser.add_argument("--coder-temperature", type=float, default=0.0,
                        help="the pre-registration specifies 0 for the coder")
    parser.add_argument("--run-number", type=int, default=1, help="1 for the first pass, 2 for the stability run")
    parser.add_argument("--limit", type=int, default=None, help="code only the first N sessions (for a test)")
    # Added 6 September 2026. The revised rule writes to its own folder,
    # <name>-revised, so a coding under the registered rule is never
    # overwritten or confused with one under the revised rule.
    parser.add_argument("--rule", default="registered", choices=sorted(RULES),
                        help="which rule to send the coder; the registered one is the default")
    args = parser.parse_args()

    require_project("analysis", "scripts")

    if args.run:
        run_dir = DATA / "runs" / args.run
        if not run_dir.is_dir():
            sys.exit(f"No run at {run_dir}")
        sessions = sessions_from_run(run_dir)
        name = args.name or args.run
    else:
        sessions = sessions_from_transcript_file(args.transcripts)
        name = args.name or Path(args.transcripts).stem
    if args.limit:
        sessions = sessions[:args.limit]
    print(f"{len(sessions)} sessions to code.")
    if not sessions:
        sys.exit("Nothing to code.")

    settings = Settings(provider=args.coder_provider,
                        model=args.coder_model or DEFAULT_CODER_MODEL[args.coder_provider],
                        temperature=args.coder_temperature, max_tokens=400,
                        thinking_allowance=thinking_allowance_for(args.coder_provider))
    provider = make_provider(settings)

    if args.rule != "registered":
        name = f"{name}-{args.rule}"
    rule_text, features_asked = RULES[args.rule]
    out_dir = ANALYSIS / "coding" / name
    out_dir.mkdir(parents=True, exist_ok=True)
    refuse_if_pass_exists(out_dir, args.run_number)
    (out_dir / "settings.json").write_text(json.dumps(
        {"coder": vars(settings), "rule_name": args.rule, "rule": rule_text, "features": features_asked,
         "written": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())},
        indent=1, ensure_ascii=False), encoding="utf-8")

    results_path, rows = code_all(sessions, provider, out_dir, args.run_number, args.rule)
    summarise(rows)
    print(f"\nWritten: {results_path}")


if __name__ == "__main__":
    main()
