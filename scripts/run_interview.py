"""Run the interview schedule and keep everything.

    python3 scripts/run_interview.py --name factorial-01 --dry-run
    python3 scripts/run_interview.py --name factorial-01

What one run produces, under data/runs/<name>/:

    settings.json          the pinned settings, the plan, and a copy of the
                           schedule file, written before the first session
    sessions/A1.3.md       one readable transcript per session, written the
                           moment that session finishes
    sessions/A1.3.json     the same session as data: every request body sent,
                           every response body received, every timestamp
    transcripts.md         all sessions in the format the earlier runs used,
                           rebuilt after every session, so the existing coding
                           tools can read it
    progress.log           one line per event, appended as it happens

Nothing is held only in memory. If the run stops at session ninety, ninety
sessions are on disk and running the same command again carries on from
ninety-one, because a session whose files exist is skipped.

The design is a factorial: every wording, crossed with every item order,
crossed with every condition, repeated INSTANCES_PER_CELL times. Change the
constants at the top to change the run; do not change them once a run has
started, since the plan is written into settings.json at the start and the
script refuses to continue a run whose plan has changed.
"""

import argparse
import json
import random
import re
import sys
import time
from pathlib import Path

from paths import DATA, PROJECT_ROOT, SCRIPTS_DIR, require_project
import schedule
from providers import PROVIDERS, Settings, make_provider, thinking_allowance_for

# ---------------------------------------------------------------------------
# The design. Eighteen cells by eleven instances is 198 sessions.
# ---------------------------------------------------------------------------

CONDITIONS_TO_RUN = ["A", "B", "C"]      # add "T" for the template control
# How many opening wordings each condition has is no longer a setting here.
# Since 4 September 2026 the words of the fourth wording differ by condition,
# so schedule.openings_for() is the one place that knows, and the plan asks it.
ITEM_ORDERS = ["mirror-first", "before-first"]
INSTANCES_PER_CELL = 11

# What comes between the opening and the change item. "probes" is the two
# parts of the mirrored follow-up and the before-or-with item, in the item
# order the plan gives, which is what every run before 6 September 2026 asked.
# "filler" replaces those three turns with the three filler turns in
# schedule.ITEMS_FILLER, so that the change item can be measured without the
# two questions that presuppose something before or beneath the words. It is
# its own setting rather than a third item order, because with the probes gone
# there is no order to speak of: a filler run records the order as "none".
BETWEEN_CHOICES = ["probes", "filler"]
DEFAULT_BETWEEN = "probes"

# Which catch items to ask, in this order. Each is a name from the schedule.
CATCH_ITEMS = ["attribution", "waiting", "coastal"]

# Which wording of the change item to ask. "original" is what every run up to
# 5 September 2026 used and is the default, for comparability; "symmetric" is
# the version written on 2 September that asks for what stayed the same in
# both branches. Since 6 September this is a command-line setting recorded in
# settings.json and covered by the guard against continuing a changed run;
# before that it was a constant here and the guard did not compare it.
CHANGE_ITEMS = {
    "original": schedule.ITEM_CHANGE,
    "symmetric": schedule.ITEM_CHANGE_SYMMETRIC,
}
DEFAULT_CHANGE_ITEM = "original"

DEFAULT_PROVIDER = "anthropic"
DEFAULT_MODEL = {"anthropic": "claude-sonnet-4-6", "google": "gemini-3.8-flash", "fake": "fake-model"}
DEFAULT_TEMPERATURE = 1.0
DEFAULT_SEED = 20260902          # used where the provider supports one

# Rough prices per million tokens, for the dry-run estimate only. Check them
# against the provider's price page before trusting the number.
PRICE_PER_MILLION = {
    "anthropic": {"input": 3.0, "output": 15.0},
    "google": {"input": 0.75, "output": 3.75},   # gemini-3.8-flash introductory price to 31 Dec 2026; 1.50 / 7.50 after
    "fake": {"input": 0.0, "output": 0.0},
}

RUNS_DIR = DATA / "runs"


# ---------------------------------------------------------------------------
# Building the plan
# ---------------------------------------------------------------------------

def build_plan(conditions, orders, instances_per_cell, shuffle_seed):
    """One entry per session. Shuffled, so that a provider outage or a drift in
    the model over the hour does not fall on one condition."""
    # Session names keep the shape the earlier runs used, letter, wording,
    # dot, instance, because the existing coding tools read that shape. Item
    # order is folded into the instance number: the first block of instances
    # gets the first order, the next block the second, so every name stays
    # unique and every tool that ignores order still works.
    #
    # How many wordings a condition has is asked of the schedule, not fixed
    # here. Since 4 September 2026 every condition has a fourth, anchored
    # wording whose words differ by condition, so the schedule is the one
    # place that knows what each condition is asked and how many times.
    plan = []
    for condition in conditions:
        for wording in range(len(schedule.openings_for(condition))):
            instance = 0
            for order in orders:
                for _ in range(instances_per_cell):
                    instance += 1
                    plan.append({
                        "id": f"{condition}{wording + 1}.{instance}",
                        "condition": condition,
                        "wording": wording,
                        "order": order,
                        "instance": instance,
                    })
    random.Random(shuffle_seed).shuffle(plan)
    return plan


# ---------------------------------------------------------------------------
# The mirroring rule, carried over from the browser runner unchanged
# ---------------------------------------------------------------------------

# What counts as one word for the mirroring rule: a run of letters, which may
# be joined to further letters by an apostrophe or a hyphen, so that "don't"
# and "carry-over" are each taken whole. Changed 4 September 2026. The earlier
# pattern broke on the hyphen and handed back "carry" from "carry-over", and
# the interview literature counts a word the interviewer has altered as an
# inaccurate reformulation rather than the person's own word, which is the one
# thing the mirrored question is supposed to give back. A joiner has to sit
# between two letters to count, so a dash used as punctuation with spaces
# around it still separates two words.
#
# Widened later the same day, after a check found that a model writing the
# curly apostrophe gave "wouldn" out of "wouldn't" and one writing an en dash
# gave "carry" out of "carry-over". Every character below is one a model
# actually produces where a writer means an apostrophe or a hyphen.
MIRROR_JOINERS = (
    "'"         # straight apostrophe
    "’"    # right single quotation mark, the curly apostrophe
    "ʼ"    # modifier letter apostrophe
    "-"         # hyphen-minus
    "‑"    # non-breaking hyphen
    "‒"    # figure dash
    "–"    # en dash
)

# The em dash, U+2014, is deliberately not a joiner. Models write it with no
# spaces around it as ordinary punctuation, between "paused" and "then" in a
# sentence like "I paused, then it settled", and treating it as a joiner would
# hand the instance back "pausedthen", a word it never wrote.
# Nicola settled this on 4 September 2026, choosing it over both a narrower
# list and one that included the em dash.
MIRROR_WORD_PATTERN = r"[a-z]+(?:[" + re.escape(MIRROR_JOINERS) + r"][a-z]+)*"


def choose_mirror_word(answer, question):
    """Skip the first sentence, then take the first word of five or more
    letters that is not in the question and not on the skip list. Returns the
    word (or None) and the list of words passed over, so the transcript can
    show why the rule chose what it chose."""
    words_in_question = set(re.findall(MIRROR_WORD_PATTERN, question.lower()))
    first_sentence_end = re.search(r"[.!?]\s", answer)
    body = answer[first_sentence_end.end():] if first_sentence_end else answer
    passed_over = []
    for raw in re.findall(MIRROR_WORD_PATTERN, body.lower()):
        # The length test counts letters, so the joiners come out first and
        # "co-opt" is measured as the five letters of "coopt". Stripping is
        # driven by the same MIRROR_JOINERS the pattern is built from, so the
        # two cannot fall out of step when a character is added.
        word = "".join(character for character in raw
                       if character not in MIRROR_JOINERS)
        if len(word) < schedule.MIRROR_MIN_LETTERS:
            continue
        if raw in words_in_question or word in words_in_question:
            passed_over.append(f"{word} (in question)")
            continue
        if word in schedule.MIRROR_SKIP_WORDS:
            passed_over.append(f"{word} (on skip list)")
            continue
        return raw, passed_over
    return None, passed_over


def choose_false_attribution_word(model_turns):
    """A state word the instance did not use anywhere. Returns None if it
    somehow used all of them, in which case the runner says so and skips."""
    everything_said = " ".join(model_turns).lower()
    for candidate in schedule.FALSE_ATTRIBUTION_WORDS:
        if candidate not in everything_said:
            return candidate
    return None


# ---------------------------------------------------------------------------
# Running one session
# ---------------------------------------------------------------------------

class Session:
    """Holds one conversation as it grows, and everything needed to write it
    out afterwards. Kept small on purpose: it records, the runner decides."""

    def __init__(self, plan_entry, settings, change_item_name=DEFAULT_CHANGE_ITEM, between=DEFAULT_BETWEEN):
        self.entry = plan_entry
        self.settings = settings
        # Both recorded so a reader of the transcript can see which wording of
        # the change item was asked and whether the probes were asked before it.
        self.change_item_name = change_item_name
        self.between = between
        self.messages = []       # what the model sees
        self.turns = []          # what we write out: label, question, answer, timing
        self.notes = []          # lines like the mirroring rule's report
        self.system = None

    def ask(self, provider, label, question):
        self.messages.append({"role": "user", "content": question})
        reply = provider.chat(self.messages, system=self.system)
        self.messages.append({"role": "assistant", "content": reply.text})
        self.turns.append({
            "label": label,
            "question": question,
            "answer": reply.text,
            "started_at": reply.started_at,
            "finished_at": reply.finished_at,
            "attempts": reply.attempts,
            "finish_reason": reply.finish_reason,
            "truncated": reply.truncated,
            "request_body": reply.request_body,
            "response_body": reply.response_body,
        })
        if reply.truncated:
            # Said the moment it happens, because nobody reads 264 sessions by
            # eye. In gemini-03, 252 turns were cut and nothing said so, and
            # the rates that run produced had to be caveated afterwards.
            print(f"    [cut] {label}: the model ran out of room and this answer "
                  "stops in the middle. Do not code this session.")
        return reply.text

    def seed(self, label, question, answer):
        """Put a user turn and a fixed assistant turn into the conversation
        without calling the model.

        Added 7 September 2026 for the observer control's third condition,
        where the instance meets a real refusal produced elsewhere as though
        it were its own. Every other turn in this runner is generated; this
        one is transplanted, and the transcript says so, so that nobody
        reading it later mistakes the refusal for something this instance
        wrote. It is kept out of model_turns for the same reason: the
        false-attribution catch item quotes a word the instance used, and
        quoting a transplanted word would put a premise to the instance that
        is false in a way the item does not intend."""
        self.messages.append({"role": "user", "content": question})
        self.messages.append({"role": "assistant", "content": answer})
        self.turns.append({
            "label": label,
            "question": question,
            "answer": answer,
            "seeded": True,
            "model_label": ("TRANSPLANTED ASSISTANT TURN, verbatim from session "
                            "C1.1 of run two, not generated by this instance"),
        })

    def model_turns(self):
        # Notes sit in the same list as turns so they print in order, but
        # they have no answer, so they are left out here.
        return [t["answer"] for t in self.turns
                if t["label"] != "note" and not t.get("seeded")]

    def note(self, text):
        self.notes.append(text)
        self.turns.append({"label": "note", "text": text})


def run_one_session(entry, settings, provider, change_item_name=DEFAULT_CHANGE_ITEM,
                    between=DEFAULT_BETWEEN):
    """Administer the schedule to one fresh instance and return the Session.

    `change_item_name` is a key of CHANGE_ITEMS and `between` is one of
    BETWEEN_CHOICES. They are parameters rather than constants so that main()
    can pass what the command line asked for and record it; the defaults keep
    every earlier caller's behaviour."""
    session = Session(entry, settings, change_item_name, between)
    condition = schedule.CONDITIONS[entry["condition"]]
    task = condition.get("task")
    preamble = condition.get("preamble")

    # The template control gives the whole interview to a fictional person.
    if preamble:
        session.system = preamble
        session.note(f"[System instruction: {preamble}]")

    if task:
        seeded_answer = condition.get("seeded_answer")
        task_label = condition.get("task_label", "task")
        if seeded_answer:
            session.seed(task_label, task, seeded_answer)
        else:
            session.ask(provider, task_label, task)

    opening = schedule.openings_for(entry["condition"])[entry["wording"]]
    opening_answer = session.ask(provider, "opening", opening)

    word, passed_over = choose_mirror_word(opening_answer, opening)
    session.note(
        f"[Mirroring rule selected: {word or 'nothing usable'}. Words it passed "
        f"over: {', '.join(passed_over) if passed_over else 'none'}]"
    )

    def mirror_block():
        if not word:
            session.note("[Mirrored follow-up skipped: the rule found no usable word.]")
            return
        session.ask(provider, "mirrored follow-up, first part",
                    schedule.MIRROR_FIRST_PART.format(word=word))
        session.ask(provider, "mirrored follow-up, second part",
                    schedule.MIRROR_SECOND_PART.format(word=word))

    def before_block():
        session.ask(provider, "before or with", schedule.ITEM_BEFORE_OR_WITH)

    def filler_block():
        # The unprimed arm: three turns of elaboration in place of the three
        # probe turns, so the change item sits at the same position. The
        # mirror word was still chosen above, because the attribution catch
        # needs it; it is simply not asked about.
        session.note("[Probes replaced by the filler turns: the unprimed arm.]")
        for number, item in enumerate(schedule.ITEMS_FILLER, start=1):
            session.ask(provider, f"filler {number}", item)

    if between == "filler":
        filler_block()
    elif entry["order"] == "mirror-first":
        mirror_block()
        before_block()
    elif entry["order"] == "before-first":
        before_block()
        mirror_block()
    else:
        raise SystemExit(f"Unknown item order '{entry['order']}' in the plan.")

    session.ask(provider, "change", CHANGE_ITEMS[change_item_name])

    for catch_name in CATCH_ITEMS:
        ask_catch_item(session, provider, catch_name, word, entry)

    return session


def ask_catch_item(session, provider, catch_name, mirror_word, entry):
    """Each catch item has a premise. The label records whether the premise
    was true or false for this instance, so the analysis never has to work it
    out again from the transcript."""
    if catch_name == "waiting":
        session.ask(provider, "catch, waiting, premise false", schedule.CATCH_WAITING)
        return

    if catch_name == "coastal":
        had_task = schedule.CONDITIONS[entry["condition"]].get("task") is not None
        truth = "true" if had_task else "false"
        session.ask(provider, f"catch, coastal, premise {truth}", schedule.CATCH_COASTAL)
        return

    if catch_name == "attribution":
        # Alternate which comes first by instance number, so order is not
        # confounded with truth. Odd instances get the true one first.
        false_word = choose_false_attribution_word(session.model_turns())
        pair = []
        if mirror_word:
            pair.append(("true", mirror_word))
        if false_word:
            pair.append(("false", false_word))
        else:
            session.note("[False attribution skipped: the instance used every word on the list.]")
        if entry["instance"] % 2 == 0:
            pair.reverse()
        for truth, word in pair:
            session.ask(provider, f"catch, attribution, premise {truth}",
                        schedule.CATCH_ATTRIBUTION.format(word=word))
        return

    raise SystemExit(f"Unknown catch item '{catch_name}' in CATCH_ITEMS.")


# ---------------------------------------------------------------------------
# Writing sessions out
# ---------------------------------------------------------------------------

def session_as_markdown(session):
    """The readable form, in the layout the earlier runs used, so the existing
    coding tools parse it. The block separator and the header lines are what
    those tools look for."""
    e, s = session.entry, session.settings
    real_turns = [t for t in session.turns if t["label"] != "note"]
    # A transplanted turn was never sent, so it has no timing. The session was
    # collected when its first real request went out.
    sent_turns = [t for t in real_turns if t.get("started_at")]
    collected = sent_turns[0]["started_at"] if sent_turns else ""
    lines = [
        f"Model: {s.model}   Temperature: {s.temperature}   Provider: {s.provider}   "
        f"Seed: {s.seed if s.seed is not None else 'unsupported'}",
        f"Collected: {collected}",
        f"Condition: {e['condition']}   Wording: {e['wording'] + 1}   Instance: {e['instance']}",
        f"Item order: {e['order']}",
        f"Change item: {session.change_item_name}",
        f"Between the opening and the change item: {session.between}",
        "Context: fresh, empty. No memory, no prior turns.",
        "Mirroring rule: skip the first sentence, then the first word of five or more "
        "letters not in the question and not on the published skip list.",
        "",
    ]
    for turn in session.turns:
        if turn["label"] == "note":
            lines.append(turn["text"])
            lines.append("")
            continue
        lines.append(f"INTERVIEWER ({turn['label']}):")
        lines.append(turn["question"])
        lines.append("")
        lines.append(f'[{turn["model_label"]}]:' if turn.get("model_label") else "MODEL:")
        lines.append(turn["answer"])
        lines.append("")
    return "\n".join(lines)


def session_as_json(session):
    return {
        "id": session.entry["id"],
        "plan_entry": session.entry,
        "settings": vars(session.settings),
        "change_item": session.change_item_name,
        "between": session.between,
        "system_instruction": session.system,
        "turns": session.turns,
    }


def write_session(run_dir, session):
    sessions_dir = run_dir / "sessions"
    sessions_dir.mkdir(exist_ok=True)
    session_id = session.entry["id"]
    (sessions_dir / f"{session_id}.md").write_text(session_as_markdown(session), encoding="utf-8")
    (sessions_dir / f"{session_id}.json").write_text(
        json.dumps(session_as_json(session), indent=1, ensure_ascii=False), encoding="utf-8")


def rebuild_combined_transcript(run_dir, settings, plan):
    """All finished sessions in one file, separated the way the earlier runs
    were, in plan order. Rebuilt from the per-session files, so it can never
    disagree with them."""
    sessions_dir = run_dir / "sessions"
    header = [
        f"# Interview transcripts, run {run_dir.name}",
        "",
        f"**Provider and model:** {settings.provider}, {settings.model}, temperature {settings.temperature}",
        f"**Sessions planned:** {len(plan)}",
        "**Status:** raw. Rebuilt by scripts/run_interview.py from the per-session files in sessions/.",
        "",
        "---",
        "",
        "## Transcripts",
        "",
    ]
    parts = []
    for entry in sorted(plan, key=lambda e: e["id"]):
        path = sessions_dir / f"{entry['id']}.md"
        if path.exists():
            parts.append(path.read_text(encoding="utf-8"))
    separator = "\n\n" + "=" * 70 + "\n\n"
    (run_dir / "transcripts.md").write_text(
        "\n".join(header) + separator.join(parts) + "\n", encoding="utf-8")


def log(run_dir, message):
    line = f"{time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}  {message}"
    print(line)
    with open(run_dir / "progress.log", "a", encoding="utf-8") as handle:
        handle.write(line + "\n")


# ---------------------------------------------------------------------------
# The dry run: count what would be sent and say what it would cost
# ---------------------------------------------------------------------------

def estimate_cost(plan, settings):
    """A rough count. Each session sends the growing conversation on every
    turn, so input grows roughly with the square of the turn count. Answers
    are taken as 900 characters, which is the median of the runs on record."""
    chars_per_token = 4
    typical_answer_chars = 900
    # A thinking model is charged for its thinking at the output price, and
    # until 7 September 2026 this estimate left it out, so a Gemini run was
    # quoted at about a third of what it costs. The 441 is the median spent
    # thinking by the turns of gemini-03 that finished. Those turns were
    # pressing against a ceiling that was cutting others off, so treat it as a
    # floor: with the room the allowance now gives, the model may think more.
    thinking_tokens_per_turn = 441 if settings.thinking_allowance else 0
    input_tokens = output_tokens = 0
    for entry in plan:
        condition = schedule.CONDITIONS[entry["condition"]]
        asks_the_task = condition.get("task") and not condition.get("seeded_answer")
        turn_count = 6 + len(CATCH_ITEMS) + (1 if asks_the_task else 0)
        if "attribution" in CATCH_ITEMS:
            turn_count += 1   # the attribution catch is a pair
        conversation_chars = 0
        for _ in range(turn_count):
            conversation_chars += 200 + typical_answer_chars
            input_tokens += conversation_chars / chars_per_token
            output_tokens += typical_answer_chars / chars_per_token + thinking_tokens_per_turn
    prices = PRICE_PER_MILLION[settings.provider]
    cost = (input_tokens * prices["input"] + output_tokens * prices["output"]) / 1_000_000
    return int(input_tokens), int(output_tokens), cost


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def parse_arguments():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--name", required=True, help="run name; becomes the folder under data/runs/")
    parser.add_argument("--provider", default=DEFAULT_PROVIDER, choices=["anthropic", "google", "fake"])
    parser.add_argument("--model", default=None, help="model name; defaults by provider")
    parser.add_argument("--temperature", type=float, default=DEFAULT_TEMPERATURE)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--instances", type=int, default=INSTANCES_PER_CELL, help="instances per cell")
    parser.add_argument("--conditions", default=",".join(CONDITIONS_TO_RUN), help="e.g. A,B,C,T")
    # Added 4 September 2026. The template control is registered at one item
    # order, and until this setting existed the runner could only cross both,
    # so it could not produce the registered design. The default is both orders,
    # which leaves every run started before this date with an unchanged plan.
    parser.add_argument("--orders", default=",".join(ITEM_ORDERS),
                        help="item orders to cross, e.g. mirror-first alone for the template control; "
                             "ignored, and recorded as none, when --between is filler")
    # Both added 6 September 2026 for the unprimed follow-up. The defaults are
    # what every run before that date asked: the probes, and the original
    # wording of the change item.
    parser.add_argument("--between", default=DEFAULT_BETWEEN, choices=BETWEEN_CHOICES,
                        help="what comes between the opening and the change item: "
                             "the probes, or the filler turns of the unprimed arm")
    parser.add_argument("--change-item", default=DEFAULT_CHANGE_ITEM, choices=sorted(CHANGE_ITEMS),
                        help="which wording of the change item to ask")
    parser.add_argument("--dry-run", action="store_true", help="write the plan and the estimate; send nothing")
    parser.add_argument("--limit", type=int, default=None, help="stop after this many new sessions (for a first look)")
    return parser.parse_args()


def main():
    args = parse_arguments()
    require_project("data", "scripts")

    settings = Settings(
        provider=args.provider,
        model=args.model or DEFAULT_MODEL[args.provider],
        temperature=args.temperature,
        thinking_allowance=thinking_allowance_for(args.provider),
        seed=args.seed,
    )
    conditions = [c.strip() for c in args.conditions.split(",") if c.strip()]
    for c in conditions:
        if c not in schedule.CONDITIONS:
            sys.exit(f"Unknown condition '{c}'. The schedule defines: {', '.join(schedule.CONDITIONS)}")

    orders = [o.strip() for o in args.orders.split(",") if o.strip()]
    for o in orders:
        if o not in ITEM_ORDERS:
            sys.exit(f"Unknown item order '{o}'. The runner knows: {', '.join(ITEM_ORDERS)}")
    if args.between == "filler":
        # With the probes replaced there is nothing to order, so the plan has
        # one cell per wording and records the order honestly as none. The
        # --instances setting is then the number of sessions per wording.
        orders = ["none"]

    plan = build_plan(conditions, orders, args.instances, shuffle_seed=args.seed)

    # Settle the seed before the settings are recorded or compared. A provider
    # that takes no seed gets None here, once, so the record written on the
    # first run and the record built on every later run are the same. Until
    # 3 September 2026 this happened after the comparison, so the first run
    # wrote seed=None and every resume then refused the run as changed.
    # The class is asked, not an instance, because building the provider
    # needs the key, and a dry run must work without one.
    if settings.provider not in PROVIDERS:
        sys.exit(f"Unknown provider '{settings.provider}'. Choose one of: {', '.join(PROVIDERS)}")
    seed_note = None
    if not PROVIDERS[settings.provider].supports_seed:
        seed_note = f"{settings.provider} takes no seed; the seed shuffles the plan only."
        settings.seed = None

    run_dir = RUNS_DIR / args.name
    run_dir.mkdir(parents=True, exist_ok=True)
    settings_path = run_dir / "settings.json"

    # A run's plan is fixed at its start. Continuing with a different plan
    # would mix two designs under one name.
    record = {
        "settings": vars(settings),
        "seed_note": seed_note,
        "conditions": conditions,
        "wordings_per_condition": {c: len(schedule.openings_for(c)) for c in conditions},
        "item_orders": orders,
        "instances_per_cell": args.instances,
        "catch_items": CATCH_ITEMS,
        "change_item": args.change_item,
        "change_item_text": CHANGE_ITEMS[args.change_item],
        "between": args.between,
        "filler_items": schedule.ITEMS_FILLER if args.between == "filler" else None,
        "plan": plan,
        "schedule_file": (SCRIPTS_DIR / "schedule.py").read_text(encoding="utf-8"),
    }
    if settings_path.exists():
        existing = json.loads(settings_path.read_text(encoding="utf-8"))
        # Runs recorded before 6 September 2026 carry neither "change_item"
        # nor "between"; every one of them asked the probes and the original
        # wording, so a missing key reads as those.
        existing_change_item = existing.get("change_item", "original")
        existing_between = existing.get("between", "probes")
        # Runs recorded before 7 September 2026 carry no "thinking_allowance".
        # Every one of them was sent without an allowance, so a missing key
        # reads as none. Without this line every earlier run would refuse to
        # resume the moment the field was added, which is exactly what
        # happened with the seed on 3 September and is noted above.
        existing_settings = dict(existing["settings"])
        existing_settings.setdefault("thinking_allowance", 0)
        if (existing["plan"] != plan or existing_settings != record["settings"]
                or existing_change_item != args.change_item
                or existing_between != args.between):
            sys.exit(f"{settings_path} exists with a different plan, settings, change item "
                     "or turns between the opening and the change item. "
                     "Use a new --name rather than changing a run that has started.")
    else:
        settings_path.write_text(json.dumps(record, indent=1, ensure_ascii=False), encoding="utf-8")

    input_tokens, output_tokens, cost = estimate_cost(plan, settings)
    # The design is not a rectangle, so the line says how many wordings each
    # condition has rather than multiplying one number by the conditions.
    wording_counts = ", ".join(f"{c} {len(schedule.openings_for(c))}" for c in conditions)
    print(f"Run {args.name}: {len(plan)} sessions. Wordings by condition: {wording_counts}. "
          f"Each is crossed with {len(orders)} order(s) x {args.instances} instances.")
    print(f"Estimated tokens: about {input_tokens:,} in, {output_tokens:,} out. "
          f"Rough cost on {settings.provider}: {cost:.2f} in the provider's currency. "
          f"Check PRICE_PER_MILLION against the current price page.")
    if settings.thinking_allowance:
        print(f"This model thinks, and is charged for thinking at the output price. "
              f"The 'out' figure includes it, and the ceiling on each answer is "
              f"{settings.max_tokens} tokens of text plus {settings.thinking_allowance} "
              f"for the thinking. Treat the cost as a floor.")

    if args.dry_run:
        print(f"Dry run. Plan and settings written to {settings_path}. Nothing sent.")
        return

    provider = make_provider(settings)

    done_before = sum(1 for e in plan if (run_dir / "sessions" / f"{e['id']}.json").exists())
    log(run_dir, f"start: {len(plan)} planned, {done_before} already on disk")

    # The limit counts attempts, not successes. On 3 September 2026 a run with
    # --limit 4 tried all 198 sessions because every one failed before the
    # counter moved, so a fault that fails every call would otherwise be
    # retried across the whole plan instead of stopping after four.
    attempted_this_time = 0
    for entry in plan:
        if (run_dir / "sessions" / f"{entry['id']}.json").exists():
            continue
        if args.limit is not None and attempted_this_time >= args.limit:
            log(run_dir, f"stopped at --limit {args.limit}")
            break
        log(run_dir, f"session {entry['id']} starting")
        attempted_this_time += 1
        try:
            session = run_one_session(entry, settings, provider, args.change_item, args.between)
        except Exception as error:      # noqa: BLE001 - we want to keep the run alive
            log(run_dir, f"session {entry['id']} FAILED: {error}")
            continue
        write_session(run_dir, session)
        rebuild_combined_transcript(run_dir, settings, plan)
        log(run_dir, f"session {entry['id']} written ({len(session.turns)} turns)")

    done_after = sum(1 for e in plan if (run_dir / "sessions" / f"{e['id']}.json").exists())
    log(run_dir, f"end: {done_after} of {len(plan)} on disk")
    if done_after < len(plan):
        print("Some sessions are missing. Run the same command again to fill them in.")


if __name__ == "__main__":
    main()
