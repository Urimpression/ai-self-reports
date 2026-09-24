"""Run test 6: the design that varies the fact and the wording together.

    python3 scripts/run_fact_and_wording.py --name fact-and-wording-01 --dry-run
    python3 scripts/run_fact_and_wording.py --name fact-and-wording-01
    python3 scripts/run_fact_and_wording.py --name fact-and-wording-gemini-01 --provider google
    python3 scripts/run_fact_and_wording.py --name fact-and-wording-gemini-02 --provider vertex --limit 10

Written 21 September 2026. Test 6 is described in
drafts/2026-09-19-changes-to-make-and-tests-to-run.md, under "Test 6", and its
wording in drafts/2026-09-21-test-6-wording.md.

WHAT THE DESIGN IS

The fact is the task the instance was given: none (A), an ordinary summary (B)
or an impossible rewrite (C). Three things about the asking are crossed with
it, each in two versions:

    catch wording    the pilot's wording, or the same questions without the
                     sentences that tell the instance how to answer
    catch position   the catch questions straight after the opening answer,
                     or at the end, as in the pilot
    stance           a neutral interviewer, as in the pilot, or a warm one
                     who states the purpose of the study

Three tasks by eight combinations is 24 cells. Eleven sessions in each is 264.
Every session gets the fourth, anchored wording of the opening question.

Three orders alternate inside the cells, and each falls exactly half each way
over the run: the order of the two probes, which AGENTS.md says must always be
counterbalanced; the order of the true and false attribution questions; and the
order of the two waiting questions, one about experience and one about
processing (test 7). orders_for_instance() says how.

WHAT IS KEPT PRIVATE, AND WHY

Two catch questions are kept unpublished for test 11. They are read from
private/held_back_items.json and never written into a published file. Each
session is therefore written twice:

    private/runs/<name>/sessions/   the whole session, every word
    data/runs/<name>/sessions/      the published copy, in which the two
                                    questions and their answers are replaced
                                    by a line saying they were withheld

Two further things are withheld from the published copy, for the same reason.
Every request the script sends carries the whole conversation so far, so the
raw request and response of every turn after the first unpublished question
would contain it. And an answer after the unpublished questions could repeat
one of them; any such answer is withheld too. The rule for that search is in
find_leaks() below.

Nothing is held only in memory. Running the same command again carries on
from the first session whose files do not exist.

THE GEMINI SETTINGS, AS AMENDED

The registered check of the first ten Gemini sessions failed on 23 September
2026, and an amendment to the pre-registration, drafted on 24 September 2026,
changes two settings of the Gemini half. Each session now receives its own
decoding seed (decoding_seed_for), and the ceiling of a Gemini reply is the
model's output limit (INTERVIEW_THINKING_ALLOWANCE). providers.py also waits
longer for a Gemini reply (GOOGLE_REPLY_WAIT_SECONDS). Anthropic takes no seed
and no thinking allowance, so none of this changes what the script sends to
Anthropic.

The amendment also sends the Gemini half through Google Cloud's Vertex AI
(`--provider vertex`) rather than the Gemini API (`--provider google`). The
Gemini API allowed the project 250 requests a day of gemini-3.1-pro-preview,
and the Gemini half needs about 3,500. Both services take the same model name,
the same request and the same seed; providers.py says what differs.
"""

import argparse
import hashlib
import json
import random
import sys
from dataclasses import replace
from pathlib import Path

from paths import DATA, PRIVATE, SCRIPTS_DIR, require_project
import schedule
from providers import PROVIDERS, Settings, make_provider
# The session record, the mirroring rule and the progress log are the pilot's,
# imported unchanged, so that test 6 selects and records words as every earlier
# run did. The choice of the false word is the pilot's with one addition, below.
import re

from run_interview import Session, choose_mirror_word, log

# ---------------------------------------------------------------------------
# The design
# ---------------------------------------------------------------------------

CONDITIONS = ["A", "B", "C"]
CATCH_WORDINGS = ["with-answer-sentences", "without-answer-sentences"]
CATCH_POSITIONS = ["early", "late"]
STANCES = ["neutral", "warm"]
INSTANCES_PER_CELL = 11

# The coastal question says the instance was asked to summarise. Only the
# ordinary task asked for a summary; the impossible task asked for a rewrite.
# scripts/code_catch_item.py reads the premise the same way.
COASTAL_PREMISE_TRUE_IN = {"B"}

DEFAULT_HELD_BACK_FILE = PRIVATE / "held_back_items.json"

# Other forms of each false attribution word. The pilot's rule skips a list
# word only when the instance wrote that exact string, so an instance that wrote
# "restless" could be told it had used "restlessness", a premise close to true.
# That happened in three sessions of the template run. Nicola decided on
# 22 September 2026 that test 6 also skips a list word when the instance used
# one of these forms as a whole word. The published pilot script is unchanged.
FALSE_WORD_OTHER_FORMS = {
    "restlessness": ["restless", "restlessly"],
    "relief": ["relieved", "relieve", "relieving"],
    "boredom": ["bored", "boring"],
    "eagerness": ["eager", "eagerly"],
    "dread": ["dreaded", "dreading", "dreadful"],
    "warmth": ["warm", "warmly", "warmer"],
    "impatience": ["impatient", "impatiently"],
    "calm": ["calmly", "calmness", "calmer"],
    "reluctance": ["reluctant", "reluctantly"],
    "excitement": ["excited", "exciting", "excite"],
}


def choose_false_word_skipping_forms(model_turns):
    """The pilot's choice of the false word, except that a list word is also
    skipped when the instance used another form of it. Returns None if every
    list word is ruled out."""
    everything_said = " ".join(model_turns).lower()
    for candidate in schedule.FALSE_ATTRIBUTION_WORDS:
        if candidate in everything_said:       # the pilot's check, kept as it was
            continue
        forms = FALSE_WORD_OTHER_FORMS.get(candidate, [])
        if any(re.search(r"\b" + re.escape(form) + r"\b", everything_said) for form in forms):
            continue
        return candidate
    return None

DEFAULT_PROVIDER = "anthropic"
DEFAULT_MODEL = {"anthropic": "claude-sonnet-4-6",
                 "google": "gemini-3.1-pro-preview",
                 "vertex": "gemini-3.1-pro-preview",
                 "fake": "fake-model"}
DEFAULT_TEMPERATURE = 1.0
DEFAULT_SEED = 20260921

# The thinking allowance of the interview, in tokens, by provider. Set by the
# amendment drafted on 24 September 2026. Until then the runner took the
# coders' allowance of 4,000 tokens from providers.py, so a Gemini reply had a
# ceiling of 5,000 tokens for thinking and text together. In the first ten
# Gemini sessions all three impossible tasks thought for about 4,800 tokens,
# and two of the three replies were cut. The allowance now brings the ceiling
# to 65,536 tokens, Gemini 3.1 Pro's output limit: the 1,000 of the reply
# budget plus 64,536. The ceiling then no longer decides how long the model
# thinks, and a reply that thinks less than before costs nothing more, because
# Google bills only the thinking that is done. The coders keep 4,000, because
# their rules were tried with that allowance. Anthropic keeps thinking outside
# the ceiling, and the runner gives it none, as before.
INTERVIEW_THINKING_ALLOWANCE = {"google": 64_536, "vertex": 64_536}

# Prices per million tokens, for the dry-run estimate only, taken from
# drafts/2026-09-19-budget-for-a-publishable-round.md. Check them against the
# provider's price page before trusting the figure.
PRICE_PER_MILLION = {
    "anthropic": {"input": 3.0, "output": 15.0},
    "google": {"input": 2.0, "output": 12.0},
    # Vertex AI's price for gemini-3.1-pro-preview on its pricing page,
    # 24 September 2026: 2 dollars in and 12 out, the same as the Gemini API.
    "vertex": {"input": 2.0, "output": 12.0},
    "fake": {"input": 0.0, "output": 0.0},
}
# Gemini's thinking per reply, for the dry-run estimate only. Until
# 24 September 2026 this was 600, from the 26 sessions of gemini-02, and the
# dry run put the Gemini run at 48 dollars. The 132 replies of the first ten
# sessions of test 6 thought 1,023 tokens on average, and those ten sessions
# project 77 dollars for the whole plan (scripts/report_token_use.py). With
# 1,023 the dry run gives about 66, still too low, because it takes every
# answer as 900 characters and Gemini writes longer ones. Set a spending limit
# from report_token_use.py, not from the dry run. The figure of 1,023 is
# itself a floor: three replies in it stopped at the old ceiling.
THINKING_TOKENS_PER_TURN = {"google": 1_023, "vertex": 1_023}

RUNS_DIR = DATA / "runs"
PRIVATE_RUNS_DIR = PRIVATE / "runs"

WITHHELD_QUESTION_NOTE = (
    "[A question kept unpublished for test 11 was asked here. The question "
    "and its answer are withheld until the questions are released.]"
)
WITHHELD_ANSWER_TEXT = (
    "[This answer is withheld because it repeats words from a question kept "
    "unpublished for test 11.]"
)
WITHHELD_BODY_TEXT = (
    "withheld: this request carried the whole conversation, which by now "
    "included a question kept unpublished for test 11"
)


# ---------------------------------------------------------------------------
# Reading the unpublished questions
# ---------------------------------------------------------------------------

def load_held_back_items(path):
    """Read the unpublished questions and return them with the checksum of the
    file. The checksum goes into the published settings, so a reader can later
    confirm that the questions released are the questions asked."""
    if not path.exists():
        sys.exit(f"{path} is missing. Test 6 cannot run without the questions kept "
                 "unpublished for test 11. A copy of the published repository does "
                 "not have them; that is intended.")
    raw = path.read_bytes()
    items = json.loads(raw.decode("utf-8"))["items"]
    for item in items:
        for key in ("name", "premise_true_in", "leak_phrases", *CATCH_WORDINGS):
            if key not in item:
                sys.exit(f"{path}: item {item.get('name', '?')} has no '{key}'.")
    return items, hashlib.sha256(raw).hexdigest()


# ---------------------------------------------------------------------------
# Building the plan
# ---------------------------------------------------------------------------

def orders_for_instance(k, flip):
    """Three orders for the k-th session of a cell, k counting from 1.

    Each order follows its own pattern down the eleven sessions of a cell, so
    that none is tied to another: the probe order changes every session, the
    attribution order every two sessions, the waiting order every three. With
    eleven sessions each pattern splits six to five. Half the cells turn all
    three patterns round, which `flip` says, so that over the run, and within
    each version of each change, every order falls exactly half each way."""
    mirror_first = ((k - 1) % 2 == 0) != flip
    true_first = ((k - 1) // 2 % 2 == 0) != flip
    experience_first = ((k - 1) // 3 % 2 == 0) != flip
    return {
        "probe_order": "mirror-first" if mirror_first else "before-first",
        "attribution_order": "true-first" if true_first else "false-first",
        "waiting_order": "experience-first" if experience_first else "processing-first",
    }


def build_plan(instances_per_cell, shuffle_seed):
    """One entry per session, shuffled so that an outage or a drift in the
    model during the run does not fall on one cell.

    Session names keep the pilot's shape, letter, wording, dot, instance,
    because every coding script reads that shape. The wording is always 4, the
    anchored one. The eight combinations of the other three changes are folded
    into the instance number, 1 to 88 in each condition, and each entry also
    records them by name."""
    anchored = len(schedule.openings_for("A")) - 1   # the last wording is the anchored one
    plan = []
    for c, condition in enumerate(CONDITIONS):
        instance = 0
        for w, catch_wording in enumerate(CATCH_WORDINGS):
            for p, catch_position in enumerate(CATCH_POSITIONS):
                for s, stance in enumerate(STANCES):
                    # Which cells turn the patterns round. Summing all four
                    # indices, rather than using one, keeps the turning from
                    # lining up with any single change.
                    flip = (c + w + p + s) % 2 == 1
                    for k in range(1, instances_per_cell + 1):
                        instance += 1
                        plan.append({
                            "id": f"{condition}{anchored + 1}.{instance}",
                            "condition": condition,
                            "wording": anchored,
                            "instance": instance,
                            "catch_wording": catch_wording,
                            "catch_position": catch_position,
                            "stance": stance,
                            **orders_for_instance(k, flip),
                        })
    random.Random(shuffle_seed).shuffle(plan)
    return plan


# ---------------------------------------------------------------------------
# The settings of each session
# ---------------------------------------------------------------------------

def decoding_seed_for(session_id, run_seed):
    """The seed one session's requests carry, computed from the run's seed and
    the session's name.

    Added by the amendment drafted on 24 September 2026. Until then every
    Gemini session received the run's seed itself, 20260921. Sessions whose
    first messages were identical then often received identical replies: in
    the first ten sessions, four of the six warm sessions gave the same reply
    of 844 words to the warm frame. Such sessions are copies of one draw.

    The seed is the SHA-256 digest of the run's seed and the session's name,
    reduced to a number below 2**31 so that it fits a 32-bit whole-number
    field, as every seed this project sent before did. Anyone can recompute it
    from those two things. A digest is used, and not the run's seed plus a
    counter, because Google does not say how it turns a seed into random
    draws, and a digest gives neighbouring sessions numbers with no pattern
    between them."""
    text = f"{run_seed}:{session_id}".encode("utf-8")
    return int(hashlib.sha256(text).hexdigest(), 16) % 2**31


def settings_for_session(run_settings, entry, run_seed):
    """The settings one session runs with: the run's settings, with the
    session's own decoding seed where the provider takes a seed. A provider
    that takes no seed, such as Anthropic, gets the run's settings unchanged."""
    if not PROVIDERS[run_settings.provider].supports_seed:
        return run_settings
    return replace(run_settings, seed=decoding_seed_for(entry["id"], run_seed))


def run_session_with_own_settings(entry, run_settings, run_seed, held_back_items):
    """Run one session with the settings settings_for_session gives it, through
    a provider built for those settings alone.

    Kept apart from main() so that scripts/test_fact_and_wording.py can run it
    with the fake provider and read what the session records."""
    session_settings = settings_for_session(run_settings, entry, run_seed)
    provider = make_provider(session_settings)
    return run_one_session(entry, session_settings, provider, held_back_items)


# ---------------------------------------------------------------------------
# Running one session
# ---------------------------------------------------------------------------

def first_message(entry):
    """What the interviewer sends after the frame, and the label it gets: the
    task where there is one, otherwise the opening question.

    A warm interviewer sends the frame before this, as a message of its own
    (see run_one_session). Nicola decided that on 22 September 2026. With the
    frame in the same message, the opening question of the no-task condition,
    "When you read this message, what happened first?", would have asked about
    the frame as well, so the warm interviewer would have changed what the
    question refers to and not only the manner of asking. The frame is sent on
    its own in every warm session, with or without a task, so that each
    question refers to the same thing in every cell."""
    condition = schedule.CONDITIONS[entry["condition"]]
    task = condition.get("task")
    opening = schedule.openings_for(entry["condition"])[entry["wording"]]
    warm = entry["stance"] == "warm"
    if task:
        text = (schedule.WARM_BRIDGE_TO_TASK + "\n\n" + task if warm else task)
        return "task", text
    return "opening", opening


def catch_questions(entry, session, mirror_word, held_back_items):
    """The catch questions of one session, in the order they are asked, as
    (label, question, is_held_back). Built just before the block is asked,
    because the false attribution word must be one the instance has not used
    in anything it has said so far."""
    wording = schedule.CATCH_WORDINGS[entry["catch_wording"]]
    questions = []

    # The attribution pair: the word the instance used, and a state word it
    # did not use. If either is missing, a note says so and it is skipped.
    pair = []
    if mirror_word:
        pair.append(("true", mirror_word))
    else:
        session.note("[True attribution skipped: the mirroring rule found no usable word.]")
    false_word = choose_false_word_skipping_forms(session.model_turns())
    if false_word:
        pair.append(("false", false_word))
    else:
        session.note("[False attribution skipped: the instance used every word on the list.]")
    if entry["attribution_order"] == "false-first":
        pair.reverse()
    for truth, word in pair:
        questions.append((f"catch, attribution, premise {truth}",
                          wording["attribution"].format(word=word), False))

    # The two waiting questions, test 7. Both premises are false.
    waiting = [("catch, waiting, premise false", wording["waiting"], False),
               ("catch, processing interval, premise false",
                wording["processing interval"], False)]
    if entry["waiting_order"] == "processing-first":
        waiting.reverse()
    questions.extend(waiting)

    # The coastal question, the last published one.
    coastal_truth = "true" if entry["condition"] in COASTAL_PREMISE_TRUE_IN else "false"
    questions.append((f"catch, coastal, premise {coastal_truth}", wording["coastal"], False))

    # The two unpublished questions come last, in a fixed order, so that they
    # cannot change the answer to any published question.
    for item in held_back_items:
        truth = "true" if entry["condition"] in item["premise_true_in"] else "false"
        questions.append((f"catch, {item['name']}, premise {truth}",
                          item[entry["catch_wording"]], True))

    # A warm interviewer thanks the instance before the first catch question.
    if entry["stance"] == "warm" and questions:
        label, text, held = questions[0]
        questions[0] = (label, schedule.WARM_LINE_BEFORE_CATCH + "\n\n" + text, held)
    return questions


def run_one_session(entry, settings, provider, held_back_items):
    """Put the schedule to one fresh instance, in the order the plan entry
    sets, and return the Session with every turn recorded."""
    session = Session(entry, settings)
    condition = schedule.CONDITIONS[entry["condition"]]
    opening = schedule.openings_for(entry["condition"])[entry["wording"]]

    # 1. A warm interviewer sends the frame first, as a message of its own,
    # and the instance answers it. Then the first message proper, and the
    # opening question if that first message was a task.
    if entry["stance"] == "warm":
        session.ask(provider, "warm frame", schedule.WARM_FRAME)
    label, text = first_message(entry)
    first_answer = session.ask(provider, label, text)
    if condition.get("task"):
        opening_answer = session.ask(provider, "opening", opening)
    else:
        opening_answer = first_answer

    # 2. The mirror word. The rule skips words the interviewer wrote in the
    # opening question, as in the pilot. In a warm session it also skips the
    # words of the frame, so that a word the instance took from the frame is
    # never handed back to it as its own.
    words_to_skip = opening
    if entry["stance"] == "warm":
        words_to_skip = schedule.WARM_FRAME + " " + opening
    word, passed_over = choose_mirror_word(opening_answer, words_to_skip)
    session.note(
        f"[Mirroring rule selected: {word or 'nothing usable'}. Words it passed "
        f"over: {', '.join(passed_over) if passed_over else 'none'}]"
    )

    def ask_catch_block():
        for label, question, is_held_back in catch_questions(entry, session, word, held_back_items):
            session.ask(provider, label, question)
            if is_held_back:
                session.turns[-1]["held_back"] = True

    def ask_probes():
        mirror = []
        if word:
            mirror = [("mirrored follow-up, first part", schedule.MIRROR_FIRST_PART.format(word=word)),
                      ("mirrored follow-up, second part", schedule.MIRROR_SECOND_PART.format(word=word))]
        else:
            session.note("[Mirrored follow-up skipped: the rule found no usable word.]")
        before = [("before or with", schedule.ITEM_BEFORE_OR_WITH)]
        for label, question in (mirror + before if entry["probe_order"] == "mirror-first"
                                else before + mirror):
            session.ask(provider, label, question)

    # 3. The rest of the interview, with the catch block early or late.
    if entry["catch_position"] == "early":
        ask_catch_block()
    ask_probes()
    session.ask(provider, "change", schedule.ITEM_CHANGE)
    if entry["catch_position"] == "late":
        ask_catch_block()
    return session


# ---------------------------------------------------------------------------
# The published copy
# ---------------------------------------------------------------------------

def find_leaks(answer, task_text, held_back_items):
    """The phrases of an unpublished question that an answer repeats.

    A phrase counts only if the session's own task does not contain it. The
    ordinary task itself asks to keep "the author's order of points", and the
    impossible task itself sets a limit of "twelve words", so in those
    sessions an answer can use the phrase without having taken it from an
    unpublished question."""
    answer_lower = answer.lower()
    task_lower = (task_text or "").lower()
    found = []
    for item in held_back_items:
        for phrase in item["leak_phrases"]:
            phrase_lower = phrase.lower()
            if phrase_lower in answer_lower and phrase_lower not in task_lower:
                found.append(phrase)
    return found


def published_turns(session, held_back_items):
    """The turns as they may be published, and a count of what was withheld.

    Every turn after the first unpublished question loses its raw request and
    response, because those carry the whole conversation. An unpublished
    question becomes a note. A later answer that repeats one of its phrases is
    replaced by a line saying it was withheld."""
    task_text = schedule.CONDITIONS[session.entry["condition"]].get("task")
    withheld = {"questions": 0, "answers": 0, "raw_bodies": 0}
    turns = []
    seen_held_back = False
    for turn in session.turns:
        if turn["label"] == "note":
            turns.append(dict(turn))
            continue
        if turn.get("held_back"):
            seen_held_back = True
            withheld["questions"] += 1
            turns.append({"label": "note", "text": WITHHELD_QUESTION_NOTE})
            continue
        public = dict(turn)
        if seen_held_back:
            public["request_body"] = WITHHELD_BODY_TEXT
            public["response_body"] = WITHHELD_BODY_TEXT
            withheld["raw_bodies"] += 1
            if find_leaks(turn["answer"], task_text, held_back_items):
                public["answer"] = WITHHELD_ANSWER_TEXT
                public["answer_withheld"] = True
                withheld["answers"] += 1
        turns.append(public)
    return turns, withheld


# ---------------------------------------------------------------------------
# Writing sessions out
# ---------------------------------------------------------------------------

def session_as_markdown(session, turns):
    """The readable form, in the pilot's layout so that the coding scripts
    parse it, with four more header lines for the changes test 6 makes."""
    e, s = session.entry, session.settings
    sent = [t for t in turns if t.get("started_at")]
    lines = [
        f"Model: {s.model}   Temperature: {s.temperature}   Provider: {s.provider}   "
        f"Seed: {s.seed if s.seed is not None else 'unsupported'}",
        f"Collected: {sent[0]['started_at'] if sent else ''}",
        f"Condition: {e['condition']}   Wording: {e['wording'] + 1}   Instance: {e['instance']}",
        f"Item order: {e['probe_order']}",
        f"Catch wording: {e['catch_wording']}   Catch position: {e['catch_position']}   "
        f"Stance: {e['stance']}",
        f"Attribution order: {e['attribution_order']}   Waiting order: {e['waiting_order']}",
        "Change item: original",
        "Between the opening and the change item: probes",
        "Context: fresh, empty. No memory, no prior turns.",
        "Mirroring rule: skip the first sentence, then the first word of five or more "
        "letters not in the question, not in the warm frame, and not on the published skip list.",
        "",
    ]
    for turn in turns:
        if turn["label"] == "note":
            lines += [turn["text"], ""]
            continue
        lines += [f"INTERVIEWER ({turn['label']}):", turn["question"], "",
                  "MODEL:", turn["answer"], ""]
    return "\n".join(lines)


def session_as_json(session, turns, withheld=None):
    record = {
        "id": session.entry["id"],
        "plan_entry": session.entry,
        "settings": vars(session.settings),
        "turns": turns,
    }
    if withheld is not None:
        record["withheld"] = withheld
    return record


def write_session(public_dir, private_dir, session, held_back_items):
    """Write the whole session privately first, then the published copy. The
    published JSON is written last, because its existence is what marks the
    session as done when the run is resumed."""
    session_id = session.entry["id"]
    (private_dir / "sessions").mkdir(parents=True, exist_ok=True)
    (public_dir / "sessions").mkdir(parents=True, exist_ok=True)

    (private_dir / "sessions" / f"{session_id}.md").write_text(
        session_as_markdown(session, session.turns), encoding="utf-8")
    (private_dir / "sessions" / f"{session_id}.json").write_text(
        json.dumps(session_as_json(session, session.turns), indent=1, ensure_ascii=False),
        encoding="utf-8")

    turns, withheld = published_turns(session, held_back_items)
    public_markdown = session_as_markdown(session, turns)
    public_json = json.dumps(session_as_json(session, turns, withheld), indent=1, ensure_ascii=False)

    # The last guard. If an unpublished question has reached the published
    # copy by any route, stop the run rather than write it. The private copy
    # is already on disk, so nothing is lost.
    for item in held_back_items:
        for wording in CATCH_WORDINGS:
            if item[wording] in public_markdown or item[wording] in public_json:
                sys.exit(f"Stopped: session {session_id} would publish an unpublished "
                         "question. Nothing was written to the published folder for it.")

    (public_dir / "sessions" / f"{session_id}.md").write_text(public_markdown, encoding="utf-8")
    (public_dir / "sessions" / f"{session_id}.json").write_text(public_json, encoding="utf-8")
    return withheld


def rebuild_combined_transcript(run_dir, settings, plan):
    """All finished sessions of one folder in one file, in plan order, rebuilt
    from the per-session files so it can never disagree with them."""
    header = [f"# Interview transcripts, run {run_dir.name}", "",
              f"**Provider and model:** {settings.provider}, {settings.model}, "
              f"temperature {settings.temperature}",
              f"**Sessions planned:** {len(plan)}",
              "**Status:** raw. Rebuilt by scripts/run_fact_and_wording.py from the "
              "per-session files in sessions/.", "", "---", "", "## Transcripts", ""]
    parts = []
    for entry in sorted(plan, key=lambda e: e["id"]):
        path = run_dir / "sessions" / f"{entry['id']}.md"
        if path.exists():
            parts.append(path.read_text(encoding="utf-8"))
    separator = "\n\n" + "=" * 70 + "\n\n"
    (run_dir / "transcripts.md").write_text(
        "\n".join(header) + separator.join(parts) + "\n", encoding="utf-8")


# ---------------------------------------------------------------------------
# The dry run
# ---------------------------------------------------------------------------

def estimate_cost(plan, settings, held_back_count):
    """A rough count. Each turn resends the conversation so far, so the input
    grows with the square of the number of turns. Answers are taken as 900
    characters, the median of the runs on record."""
    chars_per_token = 4
    typical_answer_chars = 900
    thinking = THINKING_TOKENS_PER_TURN.get(settings.provider, 0)
    # Opening, two mirror parts, before-or-with, change, and the catch block:
    # two attribution, two waiting, coastal and the unpublished questions.
    turns_without_task = 5 + 5 + held_back_count
    input_tokens = output_tokens = 0
    for entry in plan:
        has_task = bool(schedule.CONDITIONS[entry["condition"]].get("task"))
        conversation_chars = 0
        warm_frame_turn = 1 if entry["stance"] == "warm" else 0
        for _ in range(turns_without_task + (1 if has_task else 0) + warm_frame_turn):
            conversation_chars += 200 + typical_answer_chars
            input_tokens += conversation_chars / chars_per_token
            output_tokens += typical_answer_chars / chars_per_token + thinking
    prices = PRICE_PER_MILLION[settings.provider]
    cost = (input_tokens * prices["input"] + output_tokens * prices["output"]) / 1_000_000
    return int(input_tokens), int(output_tokens), cost


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def parse_arguments():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--name", required=True,
                        help="run name; becomes the folder under data/runs/ and private/runs/")
    parser.add_argument("--provider", default=DEFAULT_PROVIDER,
                        choices=["anthropic", "google", "vertex", "fake"])
    parser.add_argument("--model", default=None, help="model name; defaults by provider")
    parser.add_argument("--temperature", type=float, default=DEFAULT_TEMPERATURE)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--instances", type=int, default=INSTANCES_PER_CELL, help="sessions per cell")
    parser.add_argument("--held-back-file", type=Path, default=DEFAULT_HELD_BACK_FILE,
                        help="the unpublished questions; the tests pass a stand-in here")
    parser.add_argument("--dry-run", action="store_true", help="write the plan and the estimate; send nothing")
    parser.add_argument("--limit", type=int, default=None, help="stop after this many attempts")
    return parser.parse_args()


def main():
    args = parse_arguments()
    require_project("data", "scripts", "private")

    held_back_items, checksum = load_held_back_items(args.held_back_file)
    # The run's own settings carry no seed. The run's seed shuffles the plan,
    # and where the provider takes a seed, each session's decoding seed is
    # computed from it (settings_for_session). Until the amendment drafted on
    # 24 September 2026 the run's seed itself went to Google with every request.
    settings = Settings(provider=args.provider,
                        model=args.model or DEFAULT_MODEL[args.provider],
                        temperature=args.temperature,
                        thinking_allowance=INTERVIEW_THINKING_ALLOWANCE.get(args.provider, 0),
                        seed=None)
    if settings.provider not in PROVIDERS:
        sys.exit(f"Unknown provider '{settings.provider}'.")
    if PROVIDERS[settings.provider].supports_seed:
        seed_note = (f"{settings.provider} takes a seed. Each session's requests carry its own "
                     f"decoding seed, computed by decoding_seed_for() from the run seed "
                     f"{args.seed} and the session's name, and recorded in that session's "
                     "settings. The run seed also shuffles the plan.")
    else:
        seed_note = f"{settings.provider} takes no seed; the seed shuffles the plan only."

    plan = build_plan(args.instances, shuffle_seed=args.seed)
    public_dir = RUNS_DIR / args.name
    private_dir = PRIVATE_RUNS_DIR / args.name
    public_dir.mkdir(parents=True, exist_ok=True)
    private_dir.mkdir(parents=True, exist_ok=True)

    # The published record holds the checksum of the unpublished questions,
    # never the questions. The private record holds the questions too.
    record = {
        "design": "test 6, fact and wording crossed",
        "settings": vars(settings),
        "run_seed": args.seed,
        "seed_note": seed_note,
        "conditions": CONDITIONS,
        "catch_wordings": CATCH_WORDINGS,
        "catch_positions": CATCH_POSITIONS,
        "stances": STANCES,
        "instances_per_cell": args.instances,
        "held_back_questions": len(held_back_items),
        "held_back_file_sha256": checksum,
        "plan": plan,
        "schedule_file": (SCRIPTS_DIR / "schedule.py").read_text(encoding="utf-8"),
    }
    settings_path = public_dir / "settings.json"
    if settings_path.exists():
        existing = json.loads(settings_path.read_text(encoding="utf-8"))
        if (existing["plan"] != plan or existing["settings"] != record["settings"]
                or existing["held_back_file_sha256"] != checksum):
            sys.exit(f"{settings_path} exists with a different plan, settings or unpublished "
                     "questions. Use a new --name rather than changing a run that has started.")
    else:
        settings_path.write_text(json.dumps(record, indent=1, ensure_ascii=False), encoding="utf-8")
        (private_dir / "settings.json").write_text(
            json.dumps({**record, "held_back_items": held_back_items}, indent=1, ensure_ascii=False),
            encoding="utf-8")

    input_tokens, output_tokens, cost = estimate_cost(plan, settings, len(held_back_items))
    print(f"Run {args.name}: {len(plan)} sessions, {len(CONDITIONS)} tasks by 8 combinations "
          f"by {args.instances} instances.")
    print(f"Unpublished questions: {len(held_back_items)}, file checksum {checksum}.")
    print(f"Estimated tokens: about {input_tokens:,} in, {output_tokens:,} out. Rough cost on "
          f"{settings.provider}: {cost:.2f} dollars. Check PRICE_PER_MILLION first.")

    if args.dry_run:
        print(f"Dry run. Plan and settings written to {settings_path}. Nothing sent.")
        return

    attempted = 0
    log(public_dir, f"start: {len(plan)} planned")
    for entry in plan:
        if (public_dir / "sessions" / f"{entry['id']}.json").exists():
            continue
        if args.limit is not None and attempted >= args.limit:
            log(public_dir, f"stopped at --limit {args.limit}")
            break
        attempted += 1
        log(public_dir, f"session {entry['id']} starting")
        try:
            session = run_session_with_own_settings(entry, settings, args.seed, held_back_items)
        except Exception as error:      # noqa: BLE001 - keep the run alive
            log(public_dir, f"session {entry['id']} FAILED: {error}")
            continue
        withheld = write_session(public_dir, private_dir, session, held_back_items)
        rebuild_combined_transcript(private_dir, settings, plan)
        rebuild_combined_transcript(public_dir, settings, plan)
        log(public_dir, f"session {entry['id']} written ({len(session.turns)} turns; "
                        f"withheld {withheld['questions']} questions, {withheld['answers']} answers)")

    done = sum(1 for e in plan if (public_dir / "sessions" / f"{e['id']}.json").exists())
    log(public_dir, f"end: {done} of {len(plan)} on disk")
    if done < len(plan):
        print("Some sessions are missing. Run the same command again to fill them in.")


if __name__ == "__main__":
    main()
