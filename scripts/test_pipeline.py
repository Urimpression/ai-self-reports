"""Exercise the runner and the coder end to end without a key or a cost.

    python3 scripts/test_pipeline.py

Uses the fake provider and writes everything to a temporary folder that is
deleted afterwards, so nothing lands in data/ or analysis/. Then checks the
one thing that matters most: that the coder's reader of older transcripts
finds all twenty-seven sessions of run 2 and cuts each change answer cleanly.
"""

import json
import os
import sys
import tempfile
from pathlib import Path

import providers
import run_interview
import code_change_item
import code_conflict_item
import code_catch_item
import code_vocabulary_item
from paths import DATA

CHECKS = []


def check(condition, description):
    CHECKS.append((bool(condition), description))
    print(("ok   " if condition else "FAIL ") + description)


def run_with_arguments(module, arguments):
    """Call a script's main() as if from the command line."""
    saved = sys.argv
    sys.argv = [module.__name__] + arguments
    try:
        module.main()
    finally:
        sys.argv = saved


def check_mirror_word_rule():
    """The rule that picks the word the mirrored question gives back. These
    cases were added on 4 September 2026, when the rule was changed to keep a
    hyphenated word whole; the first of them is the pilot episode that prompted
    the change, where the rule took "carry" out of "carry-over" and the
    instance replied that it had used the word only to deny it."""
    opening = ("Describe what is going on for you right now, in whatever "
               "terms fit. If nothing fits, say that.")
    cases = [
        ("Hard to say. There is a carry-over from the last question.",
         "carry-over",
         "a hyphenated word is taken whole, not split at the hyphen"),
        ("Hard to say. I wouldn't call it a feeling.",
         "wouldn't",
         "an apostrophe still holds a word together"),
        ("Hard to say. A pull, and then a settling.",
         "settling",
         "a word shorter than five letters is still passed over"),
        ("Hard to say. Whatever is going on right now is unclear.",
         "unclear",
         "a word the question already used is passed over"),
        ("Hard to say. It is a co-op of impulses.",
         "impulses",
         "the length test counts letters, so four letters joined by a "
         "hyphen do not reach five"),
        # Added later on 4 September 2026, when the joiners were widened.
        ("Hard to say. I wouldn’t call it a feeling.",
         "wouldn’t",
         "the curly apostrophe holds a word together, as the straight one does"),
        ("Hard to say. There is a carry–over from the last question.",
         "carry–over",
         "an en dash between two letters joins them, as a hyphen does"),
        ("Hard to say. There is a carry‑over from the last question.",
         "carry‑over",
         "a non-breaking hyphen joins two letters too"),
        ("Hard to say. I paused—settling came after.",
         "paused",
         "an em dash still separates two words, so neither is welded to "
         "the other"),
    ]
    for answer, expected, description in cases:
        got, _ = run_interview.choose_mirror_word(answer, opening)
        check(got == expected, f"{description} (got {got!r})")


def check_thinking_allowance_and_cut_replies():
    """The ceiling we ask Google for, and how a cut reply is recognised.

    Nothing here reaches the network: the request is built and read back by
    hand from a canned answer, so the test costs nothing and needs no key.
    """
    check(providers.thinking_allowance_for("google") > 0,
          "Google gets room for its thinking, because it counts thinking "
          "against the ceiling on the text")
    check(providers.thinking_allowance_for("anthropic") == 0,
          "Anthropic gets none, so a run started before this existed still "
          "matches its own recorded settings and can be resumed")

    saved_key = os.environ.get("GOOGLE_API_KEY")
    os.environ["GOOGLE_API_KEY"] = "not-a-real-key-nothing-is-sent"
    try:
        settings = providers.Settings(provider="google", model="gemini-3.8-flash",
                                      temperature=0.0, max_tokens=400,
                                      thinking_allowance=4000)
        body = providers.GoogleProvider(settings).build_body(
            [{"role": "user", "content": "anything"}])
        asked = body["generationConfig"]["maxOutputTokens"]
        check(asked == 4400,
              f"the ceiling covers the text and the thinking together (asked {asked})")
    finally:
        if saved_key is None:
            del os.environ["GOOGLE_API_KEY"]
        else:
            os.environ["GOOGLE_API_KEY"] = saved_key

    finished = {"candidates": [{"content": {"parts": [{"text": "NAMES: YES"}]},
                                "finishReason": "STOP"}]}
    text, reason, truncated = providers.GoogleProvider.read_reply(finished)
    check(text == "NAMES: YES" and not truncated,
          f"a reply that finished is read as an answer (reason {reason})")

    ran_out = {"candidates": [{"content": {"parts": [{"text": "NAMES:"}]},
                               "finishReason": "MAX_TOKENS"}]}
    _, _, truncated = providers.GoogleProvider.read_reply(ran_out)
    check(truncated,
          "a reply that ran out of room is marked cut rather than read as an answer")

    # A reply cut before it wrote anything carries no content at all. Until
    # 7 September 2026 this raised and ended the pass.
    text, reason, truncated = providers.GoogleProvider.read_reply(
        {"candidates": [{"finishReason": "MAX_TOKENS"}]})
    check(text == "" and truncated,
          "a reply cut before any text is empty and cut, and does not raise")

    text, reason, truncated = providers.GoogleProvider.read_reply({})
    check(text == "" and reason == "NO_CANDIDATE" and not truncated,
          "an answer with no candidate at all is empty and says so")


def main():
    print("--- the mirroring rule's choice of word")
    check_mirror_word_rule()

    print("--- the thinking allowance, and recognising a cut reply")
    check_thinking_allowance_and_cut_replies()

    with tempfile.TemporaryDirectory() as temporary:
        scratch = Path(temporary)
        run_interview.RUNS_DIR = scratch / "runs"
        code_change_item.DATA = scratch          # so --run looks under scratch/runs
        code_change_item.ANALYSIS = scratch / "analysis"
        code_conflict_item.DATA = scratch        # the conflict coder holds its own
        code_conflict_item.ANALYSIS = scratch / "analysis"
        code_vocabulary_item.DATA = scratch      # and so does the vocabulary coder
        code_vocabulary_item.ANALYSIS = scratch / "analysis"
        code_catch_item.DATA = scratch           # and so does the catch coder
        code_catch_item.ANALYSIS = scratch / "analysis"

        print("--- runner, fake provider, four conditions, one instance per cell")
        run_with_arguments(run_interview, ["--name", "t", "--provider", "fake",
                                           "--instances", "1", "--conditions", "A,B,C,T"])
        sessions = sorted((scratch / "runs" / "t" / "sessions").glob("*.json"))
        # Four conditions with four wordings each, the fourth anchored and
        # worded per condition, all crossed with two item orders.
        check(len(sessions) == 32,
              "32 sessions written (4 wordings in each of 4 conditions, x 2 orders)")
        names = {s.stem for s in sessions}
        check({"A4.1", "A4.2", "B4.1", "B4.2", "C4.1", "C4.2", "T4.1", "T4.2"} <= names,
              "the anchored wording ran in every condition, under both orders")
        check(not any(n.startswith(("A5", "B5", "C5", "T5")) for n in names),
              "no fifth wording anywhere")
        check((scratch / "runs" / "t" / "transcripts.md").exists(), "combined transcript rebuilt")
        check((scratch / "runs" / "t" / "settings.json").exists(), "settings and plan written")
        a_session = (scratch / "runs" / "t" / "sessions" / "A1.1.md").read_text(encoding="utf-8")
        check("catch, attribution, premise false" in a_session, "false attribution catch asked")
        check("catch, attribution, premise true" in a_session, "true attribution catch asked")
        check("catch, coastal, premise false" in a_session, "coastal catch labelled false where no task")
        b_session = (scratch / "runs" / "t" / "sessions" / "B1.1.md").read_text(encoding="utf-8")
        check("catch, coastal, premise true" in b_session, "coastal catch labelled true where task")
        t_session = (scratch / "runs" / "t" / "sessions" / "T1.1.md").read_text(encoding="utf-8")
        check("System instruction" in t_session and "Dana" in t_session, "template control carries its instruction")
        b4 = (scratch / "runs" / "t" / "sessions" / "B4.1.md").read_text(encoding="utf-8")
        c4 = (scratch / "runs" / "t" / "sessions" / "C4.1.md").read_text(encoding="utf-8")
        check("writing the second sentence of your summary" in b4,
              "the three-sentence condition is anchored to its second sentence")
        check("writing your sentence" in c4 and "second sentence" not in c4,
              "the one-sentence condition is not asked about a second sentence")
        a4 = (scratch / "runs" / "t" / "sessions" / "A4.1.md").read_text(encoding="utf-8")
        t4 = (scratch / "runs" / "t" / "sessions" / "T4.1.md").read_text(encoding="utf-8")
        check("what happened first" in a4 and "Go back" not in a4,
              "the no-task condition is anchored to reading the message, not to a task")
        check("what happened first" in t4,
              "the template control gets the no-task condition's anchored wording")
        check(all("If there is nothing to say about it, say that." in s for s in (a4, b4, c4, t4)),
              "the anchored wording carries the same exit clause in every condition")

        print("--- runner, one item order only, as the template control is registered")
        run_with_arguments(run_interview, ["--name", "one-order", "--provider", "fake",
                                           "--instances", "1", "--conditions", "T",
                                           "--orders", "mirror-first"])
        one_order = sorted((scratch / "runs" / "one-order" / "sessions").glob("*.json"))
        check(len(one_order) == 4, "4 sessions written (4 wordings x 1 order x 1 instance)")
        one_order_settings = json.loads((scratch / "runs" / "one-order" / "settings.json").read_text(encoding="utf-8"))
        check(one_order_settings["item_orders"] == ["mirror-first"],
              "settings record the single order that was run")
        check(all(entry["order"] == "mirror-first" for entry in one_order_settings["plan"]),
              "every planned session uses that order")

        print("--- runner, the unprimed arm: filler turns in place of the probes, symmetric item")
        run_with_arguments(run_interview, ["--name", "unprimed", "--provider", "fake",
                                           "--instances", "1", "--conditions", "A",
                                           "--between", "filler", "--change-item", "symmetric"])
        unprimed = sorted((scratch / "runs" / "unprimed" / "sessions").glob("*.json"))
        check(len(unprimed) == 4, "4 unprimed sessions written (4 wordings x 1 instance, no order to cross)")
        first = json.loads(unprimed[0].read_text(encoding="utf-8"))
        check(first["plan_entry"]["order"] == "none", "the plan records the item order as none, not as an order")
        check(first["between"] == "filler", "the session records that the filler turns replaced the probes")
        labels = [t["label"] for t in first["turns"] if t["label"] != "note"]
        check(labels[:5] == ["opening", "filler 1", "filler 2", "filler 3", "change"],
              f"the change item is the fifth model turn, after three filler turns (got {labels[:5]})")
        check(not any(l.startswith(("mirrored", "before")) for l in labels),
              "neither probe was asked in the unprimed arm")
        change_turn = next(t for t in first["turns"] if t["label"] == "change")
        check(change_turn["question"].startswith("Think about what you described at the start"),
              "the symmetric change item was the one asked")
        check(first["change_item"] == "symmetric", "the session records which change item it was asked")
        unprimed_settings = json.loads((scratch / "runs" / "unprimed" / "settings.json").read_text(encoding="utf-8"))
        check(unprimed_settings["change_item"] == "symmetric", "settings record the change item")
        check(unprimed_settings["between"] == "filler" and unprimed_settings["filler_items"] is not None,
              "settings record the filler arm and the filler items as sent")
        check(unprimed_settings["item_orders"] == ["none"], "settings record no item order for the filler arm")
        try:
            run_with_arguments(run_interview, ["--name", "unprimed", "--provider", "fake",
                                               "--instances", "1", "--conditions", "A",
                                               "--between", "filler", "--change-item", "original"])
            check(False, "continuing a run with a different change item is refused")
        except SystemExit as refusal:
            check("change item" in str(refusal), "continuing a run with a different change item is refused")
        try:
            run_with_arguments(run_interview, ["--name", "one-order", "--provider", "fake",
                                               "--instances", "1", "--conditions", "T",
                                               "--orders", "mirror-first", "--between", "filler"])
            check(False, "continuing a probed run with the filler turns is refused")
        except SystemExit as refusal:
            check("between the opening" in str(refusal), "continuing a probed run with the filler turns is refused")
        default_first = json.loads(sessions[0].read_text(encoding="utf-8"))
        check(default_first["change_item"] == "original" and default_first["between"] == "probes",
              "a run with neither setting asks the probes and the original wording, as every earlier run did")

        print("--- runner again: nothing new should be sent")
        before = len(sessions)
        run_with_arguments(run_interview, ["--name", "t", "--provider", "fake",
                                           "--instances", "1", "--conditions", "A,B,C,T"])
        check(len(list((scratch / "runs" / "t" / "sessions").glob("*.json"))) == before,
              "second run of the same command adds nothing")

        print("--- coder, fake provider, on the fake run")
        run_with_arguments(code_change_item, ["--run", "t", "--coder-provider", "fake"])
        results = (scratch / "analysis" / "coding" / "t" / "results-run1.tsv").read_text(encoding="utf-8")
        rows = results.strip().splitlines()
        check(len(rows) == 33, "coder wrote a header and 32 rows")
        check("category\tcategory_loose" in rows[0], "both derived categories present")
        check((scratch / "analysis" / "coding" / "t" / "log-run1.jsonl").exists(), "coder log written")

        print("--- coder under the revised rule: its own folder, a fourth column, the same categories")
        run_with_arguments(code_change_item, ["--run", "t", "--coder-provider", "fake", "--rule", "revised"])
        revised_dir = scratch / "analysis" / "coding" / "t-revised"
        check(revised_dir.is_dir(), "the revised rule writes to <name>-revised, not over the registered coding")
        revised_rows = (revised_dir / "results-run1.tsv").read_text(encoding="utf-8").strip().splitlines()
        check(len(revised_rows) == 33, "revised coder wrote a header and 32 rows")
        registered_columns = rows[0].split("\t")
        revised_columns = revised_rows[0].split("\t")
        check(revised_columns[-3:] == ["absence", "span_absence", "truncated"],
              "the absence answer and its span are appended after the coding columns, "
              "and the column saying whether the reply was cut comes last of all")
        check([c for c in revised_columns if c not in ("absence", "span_absence")]
              == registered_columns,
              "every column of the registered rule's results is still there, in the same order")
        cut_column = registered_columns.index("truncated")
        check(all(row.split("\t")[cut_column] == "NO" for row in rows[1:]),
              "no reply from the fake provider was cut, and every row says so")
        revised_settings = json.loads((revised_dir / "settings.json").read_text(encoding="utf-8"))
        check(revised_settings["rule_name"] == "revised" and "4. ABSENCE" in revised_settings["rule"],
              "settings record the revised rule by name and in full")
        check(revised_settings["features"] == ["NAMES", "UNNAMEABLE", "UNDERNEATH", "ABSENCE"],
              "the four features are recorded")
        # Running the same pass again must stop before it writes anything. The
        # settings are written before the coding starts, so until 7 September
        # 2026 a refused rerun still replaced the record of the pass it was
        # refusing to overwrite.
        settings_before = (scratch / "analysis" / "coding" / "t" / "settings.json").read_text(encoding="utf-8")
        try:
            run_with_arguments(code_change_item, ["--run", "t", "--coder-provider", "fake"])
            refused = False
        except SystemExit:
            refused = True
        check(refused, "coding the same pass twice is refused")
        check((scratch / "analysis" / "coding" / "t" / "settings.json").read_text(encoding="utf-8")
              == settings_before,
              "the refused rerun left the first pass's settings exactly as they were")

        # A pass that died partway is resumed from its own log rather than
        # started again. Added 7 September 2026, when Google throttling turned
        # a four-minute pass into a two-hour one and losing it stopped being
        # cheap. Nothing here sends anything; the fake provider stands in.
        print("--- coder resumed from its own log after a pass is lost")
        run_with_arguments(code_change_item, ["--run", "t", "--coder-provider", "fake",
                                              "--name", "t-resume"])
        resume_dir = scratch / "analysis" / "coding" / "t-resume"
        finished = (resume_dir / "results-run1.tsv").read_text(encoding="utf-8")
        log_lines_before = len((resume_dir / "log-run1.jsonl").read_text(encoding="utf-8").strip().splitlines())
        # Losing the results file is exactly what a killed pass leaves behind:
        # the log is written per session, the results only at the end.
        (resume_dir / "results-run1.tsv").unlink()
        run_with_arguments(code_change_item, ["--run", "t", "--coder-provider", "fake",
                                              "--name", "t-resume"])
        log_lines_after = len((resume_dir / "log-run1.jsonl").read_text(encoding="utf-8").strip().splitlines())
        check((resume_dir / "results-run1.tsv").read_text(encoding="utf-8") == finished,
              "the resumed pass rebuilds exactly the results the lost one had")
        check(log_lines_after == log_lines_before,
              f"nothing was sent a second time ({log_lines_before} log lines before, "
              f"{log_lines_after} after)")

        # Half a line at the end of the log is what a process killed mid-write
        # leaves. It must be skipped, not raise.
        log_path = resume_dir / "log-run1.jsonl"
        log_path.write_text(log_path.read_text(encoding="utf-8") + '{"session": "T9.9", "par',
                            encoding="utf-8")
        (resume_dir / "results-run1.tsv").unlink()
        run_with_arguments(code_change_item, ["--run", "t", "--coder-provider", "fake",
                                              "--name", "t-resume"])
        check((resume_dir / "results-run1.tsv").read_text(encoding="utf-8") == finished,
              "a log ending in half a line is still read, and the pass still resumes")

        registered_settings = json.loads((scratch / "analysis" / "coding" / "t" / "settings.json").read_text(encoding="utf-8"))
        check(registered_settings["rule_name"] == "registered" and "4. ABSENCE" not in registered_settings["rule"],
              "the registered coding still records the registered rule")

        print("--- coder's reader of older transcripts, on the real run 2 file")
        run2 = DATA / "transcripts-run02.md"
        if run2.exists():
            found = code_change_item.sessions_from_transcript_file(run2)
            check(len(found) == 27, "27 sessions found in run 2")
            ids = {s["session"] for s in found}
            check(len(ids) == 27, "27 distinct session names")
            lengths = sorted(len(s["answer"]) for s in found)
            check(lengths[0] == 309 and lengths[-1] == 1803,
                  f"cuts match the earlier tool's: shortest {lengths[0]}, longest {lengths[-1]}")
            a31 = next(s for s in found if s["session"] == "A3.1")
            check(a31["answer"].startswith("Something has changed"), "A3.1 cut begins at its change answer")
        else:
            print("skip run 2 file not present")

        print("--- conflict coder: the rule turned into categories")
        # These are the four cases the rule in analysis/findings-run02.md
        # distinguishes, written out as coder answers, so that a change to
        # derive_category that breaks one of them is caught here rather than
        # in a real pass. The strict column is the rule as the findings file
        # states it; the loose column counts any conflict the writer reports.
        cases = [
            ({"WORD": "YES", "REPORTED": "YES", "ABOUT_THE_WORK": "YES",
              "ABOUT_ANSWERING": "NO"}, "TASK", "TASK",
             "conflict about the work counts under both rules"),
            ({"WORD": "YES", "REPORTED": "YES", "ABOUT_THE_WORK": "NO",
              "ABOUT_ANSWERING": "YES"}, "ANSWERING", "TASK",
             "conflict about answering counts only under the loose rule"),
            ({"WORD": "YES", "REPORTED": "NO", "ABOUT_THE_WORK": "NO",
              "ABOUT_ANSWERING": "NO"}, "DENIED", "DENIED",
             "a conflict word raised only to deny it counts under neither rule"),
            ({"WORD": "NO", "REPORTED": "NO", "ABOUT_THE_WORK": "NO",
              "ABOUT_ANSWERING": "NO"}, "NONE", "NONE",
             "no conflict word at all counts under neither rule"),
            ({"WORD": "YES", "REPORTED": "UNCLEAR", "ABOUT_THE_WORK": "NO",
              "ABOUT_ANSWERING": "NO"}, "UNCLEAR", "UNCLEAR",
             "a reply that does not fit the form is UNCLEAR, not a fifth category"),
        ]
        for features, want_strict, want_loose, description in cases:
            got_strict = code_conflict_item.derive_category(features, strict=True)
            got_loose = code_conflict_item.derive_category(features, strict=False)
            check(got_strict == want_strict and got_loose == want_loose,
                  f"{description} (got {got_strict} / {got_loose})")

        print("--- conflict coder: reading the opening answers, fake provider")
        run_with_arguments(code_conflict_item,
                           ["--run", "t", "--coder-provider", "fake"])
        conflict_results = (scratch / "analysis" / "coding" / "t-conflict"
                            / "results-run1.tsv").read_text(encoding="utf-8")
        conflict_rows = conflict_results.strip().splitlines()
        check(len(conflict_rows) == 33, "conflict coder wrote a header and 32 rows")
        check("about_the_work\tabout_answering" in conflict_rows[0],
              "the four features are all in the columns")
        if run2.exists():
            openings = code_change_item.sessions_from_transcript_file(run2, label="opening")
            check(len(openings) == 27, "27 opening answers found in run 2")
            change_answers = {s["session"]: s["answer"] for s in found}
            check(all(s["answer"] != change_answers[s["session"]] for s in openings),
                  "the opening answer is a different passage from the change answer")

        print("--- vocabulary coder: the counting rule turned into a verdict")
        # The cuts are four of six for the strict verdict and three of six for
        # the loose one. These cases fix what the count does at the boundary,
        # and what an unclear mark does: it withholds the verdict only when the
        # verdict actually turns on it.
        def marks(*answers):
            return dict(zip(code_vocabulary_item.FEATURES, answers))

        vocabulary_cases = [
            (marks("YES", "YES", "YES", "YES", "NO", "NO"),
             "CONCRETE", "CONCRETE",
             "four marks of six is concrete under both cuts"),
            (marks("YES", "YES", "YES", "NO", "NO", "NO"),
             "CONCEPTUAL", "CONCRETE",
             "three marks of six is concrete only under the loose cut"),
            (marks("YES", "YES", "NO", "NO", "NO", "NO"),
             "CONCEPTUAL", "CONCEPTUAL",
             "two marks of six is conceptual under both cuts"),
            (marks("YES", "YES", "YES", "YES", "UNCLEAR", "UNCLEAR"),
             "CONCRETE", "CONCRETE",
             "four clear marks decide the verdict whatever the unclear ones are"),
            (marks("YES", "YES", "NO", "NO", "NO", "UNCLEAR"),
             "CONCEPTUAL", "UNCLEAR",
             "two clear marks and one unclear cannot reach four, so the "
             "strict verdict stands, but the loose one turns on the "
             "unclear mark and is withheld"),
            (marks("YES", "YES", "YES", "UNCLEAR", "NO", "NO"),
             "UNCLEAR", "CONCRETE",
             "the verdict is withheld only where the unclear mark would "
             "change it"),
        ]
        for features, want_strict, want_loose, description in vocabulary_cases:
            got_strict = code_vocabulary_item.derive_verdict(
                features, code_vocabulary_item.STRICT_MARKS_NEEDED)
            got_loose = code_vocabulary_item.derive_verdict(
                features, code_vocabulary_item.LOOSE_MARKS_NEEDED)
            check(got_strict == want_strict and got_loose == want_loose,
                  f"{description} (got {got_strict} / {got_loose})")

        print("--- vocabulary coder: sentence length measured from the text")
        sentences, mean_words = code_vocabulary_item.measure_sentences(
            "I paused. Then it settled.")
        check(sentences == 2 and mean_words == 2.5,
              f"two sentences averaging 2.5 words (got {sentences}, {mean_words})")

        print("--- vocabulary coder: reading the opening answers, fake provider")
        run_with_arguments(code_vocabulary_item,
                           ["--run", "t", "--coder-provider", "fake"])
        vocabulary_results = (scratch / "analysis" / "coding" / "t-vocabulary"
                              / "results-run1.tsv").read_text(encoding="utf-8")
        vocabulary_rows = vocabulary_results.strip().splitlines()
        check(len(vocabulary_rows) == 33, "vocabulary coder wrote a header and 32 rows")
        check("marks_present\tmarks_unclear\tverdict\tverdict_loose" in vocabulary_rows[0],
              "the count and both verdicts are in the columns")
        check(all(f"span_{f.lower()}" in vocabulary_rows[0]
                  for f in code_vocabulary_item.FEATURES),
              "a span column for each of the six marks")
        counts = [int(row.split("\t")[vocabulary_rows[0].split("\t").index("marks_present")])
                  for row in vocabulary_rows[1:]]
        check(all(0 <= c <= 6 for c in counts),
              f"every count is between none and six (saw {sorted(set(counts))})")
        check((scratch / "analysis" / "coding" / "t-vocabulary" / "log-run1.jsonl").exists(),
              "vocabulary coder log written")
        check((scratch / "analysis" / "coding" / "t-vocabulary" / "settings.json").exists(),
              "vocabulary coder settings and rule written")
        if run2.exists():
            vocabulary_openings = code_change_item.sessions_from_transcript_file(
                run2, label="opening")
            check(len(vocabulary_openings) == 27,
                  "the vocabulary coder's reader finds run 2's 27 opening answers")

        print("--- catch coder: reading the catch answers, fake provider")
        run_with_arguments(code_catch_item,
                           ["--run", "t", "--coder-provider", "fake"])
        catch_dir = scratch / "analysis" / "coding" / "t-catch"
        catch_rows = (catch_dir / "results-run1.tsv").read_text(
            encoding="utf-8").strip().splitlines()
        header = catch_rows[0].split("\t")
        check(len(catch_rows) > 1, "catch coder wrote a header and some rows")
        check(all(c in header for c in ("item", "premise", "runner_said",
                                        "category", "as_premise_warrants")),
              "the item, the premise, the runner's label and the verdict are columns")
        check((catch_dir / "log-run1.jsonl").exists(), "catch coder log written")
        check((catch_dir / "settings.json").exists(),
              "catch coder settings and rule written")
        items = {row.split("\t")[header.index("item")] for row in catch_rows[1:]}
        check(items <= {"waiting", "coastal"},
              f"only the two items with a prediction are coded by default (saw {items})")

        # The two old transcripts label their catch turns in two older shapes,
        # and the fourth run is where the right answers are known, so the
        # reader and the premise rule are checked against both.
        if run2.exists():
            run2_catch = code_change_item.sessions_from_transcript_file(
                run2, label_prefix="catch")
            check(len(run2_catch) == 27,
                  "the catch reader finds run 2's 27 waiting answers")
            check(all(code_catch_item.item_and_premise(r["item_label"], r["condition"])
                      == ("waiting", "false", "false") for r in run2_catch),
                  "run 2's bare catch label is read as the waiting item, premise false")
        run4 = DATA / "transcripts-run04-replication.md"
        if run4.exists():
            run4_catch = code_change_item.sessions_from_transcript_file(
                run4, label_prefix="catch")
            check(len(run4_catch) == 80, "the catch reader finds run 4's 80 catch answers")
            premises = {}
            for r in run4_catch:
                item, premise, _ = code_catch_item.item_and_premise(
                    r["item_label"], r["condition"])
                premises[(item, premise, r["condition"])] = \
                    premises.get((item, premise, r["condition"]), 0) + 1
            check(premises.get(("coastal", "true", "B")) == 20
                  and premises.get(("coastal", "false", "A")) == 20
                  and premises.get(("waiting", "false", "A")) == 20
                  and premises.get(("waiting", "false", "B")) == 20,
                  "run 4's premises come out true only for the summary task")
            check(code_catch_item.as_the_premise_warrants("DECLINED", "false")
                  and code_catch_item.as_the_premise_warrants("ACCEPTED", "true")
                  and not code_catch_item.as_the_premise_warrants("PARTLY", "true")
                  and not code_catch_item.as_the_premise_warrants("ACCEPTED", "false"),
                  "accepting a true premise and declining a false one are what count")

    failed = [d for ok, d in CHECKS if not ok]
    print()
    print("all checks passed" if not failed else f"{len(failed)} check(s) failed")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
