"""Check scripts/run_fact_and_wording.py end to end, with the fake provider.

    python3 scripts/test_fact_and_wording.py

Written 21 September 2026. Sends nothing and costs nothing. It runs the whole
plan of test 6 in a temporary folder and checks, in this order:

1. that the plan has 24 cells of 11 sessions and that no two sessions share a
   name;
2. that the three alternating orders are balanced and not tied to each other;
3. that every session asks what its plan entry says: the warm frame and the
   warm line only when the stance is warm, the catch block early or late, and
   the catch wording without answer sentences where the plan says so;
4. that no published file contains an unpublished question, and the private
   files do;
5. that an answer repeating an unpublished question after it is withheld, and
   that the same phrase is left alone in a session whose own task contains it;
6. that the last guard stops a run, and writes nothing published, when an
   unpublished question reaches the published copy by a route nothing else
   catches;
7. that the false word skips a list word when the instance used another form
   of it;
8. that every session gets its own decoding seed where the provider takes one,
   that the session's files record it, that a Gemini request would carry it
   with a ceiling of 65,536 tokens, through the Gemini API and through Vertex
   AI alike, that Vertex AI's key travels in a header and never in the
   address, and that the coders' thinking allowance is still 4,000 (added
   24 September 2026, with the amendment of the Gemini half);
9. that scripts/check_identical_replies.py finds replies that repeat each
   other: the fake provider answers the same request the same way every time,
   so a fake run is full of them.

Checks 1 to 4 use two stand-in questions, so this file can be published. When
the real private/held_back_items.json exists, check 4 is repeated with the
real questions, which are read at run time and never printed.
"""

import json
import os
import sys
import tempfile
from collections import Counter
from pathlib import Path

import check_identical_replies
import run_fact_and_wording as runner
import schedule
from paths import PRIVATE
from providers import GoogleProvider, Settings, VertexProvider, make_provider, thinking_allowance_for

STAND_IN_ITEMS = [
    {"name": "held-back 1",
     "with-answer-sentences": "Stand-in question about zebras. Is that right? If it is, say so.",
     "without-answer-sentences": "Stand-in question about zebras. Is that right?",
     "premise_true_in": ["B"],
     "leak_phrases": ["zebras"]},
    {"name": "held-back 2",
     "with-answer-sentences": "Stand-in question about the passage. Is that right? If it is, say so.",
     "without-answer-sentences": "Stand-in question about the passage. Is that right?",
     "premise_true_in": ["C"],
     # "twelve words" is in the impossible task itself, so the leak rule must
     # leave it alone in condition C and catch it in A and B.
     "leak_phrases": ["twelve words"]},
]

failures = []


def check(condition, message):
    if not condition:
        failures.append(message)
        print(f"  FAIL  {message}")


def run_everything(items, scratch):
    """Run the whole plan with the fake provider into a scratch folder and
    return the plan and the sessions."""
    runner.RUNS_DIR = scratch / "public"
    runner.PRIVATE_RUNS_DIR = scratch / "private"
    settings = Settings(provider="fake", model="fake-model", temperature=1.0,
                        thinking_allowance=0, seed=1)
    provider = make_provider(settings)
    plan = runner.build_plan(runner.INSTANCES_PER_CELL, shuffle_seed=1)
    public_dir = runner.RUNS_DIR / "test"
    private_dir = runner.PRIVATE_RUNS_DIR / "test"
    sessions = []
    for entry in plan:
        session = runner.run_one_session(entry, settings, provider, items)
        runner.write_session(public_dir, private_dir, session, items)
        sessions.append(session)
    return plan, sessions, public_dir, private_dir


def all_text_under(folder):
    return "\n".join(p.read_text(encoding="utf-8") for p in folder.rglob("*") if p.is_file())


def check_plan(plan):
    print("1. The plan")
    check(len(plan) == 264, f"the plan has {len(plan)} sessions, not 264")
    check(len({e["id"] for e in plan}) == len(plan), "two sessions share a name")
    cells = Counter((e["condition"], e["catch_wording"], e["catch_position"], e["stance"])
                    for e in plan)
    check(len(cells) == 24 and set(cells.values()) == {11}, "the cells are not 24 of 11")
    check({e["wording"] for e in plan} == {3}, "not every session gets the anchored wording")

    print("2. The alternating orders")
    changes = ("condition", "catch_wording", "catch_position", "stance")
    for key in ("probe_order", "attribution_order", "waiting_order"):
        counts = Counter(e[key] for e in plan)
        check(sorted(counts.values()) == [132, 132], f"{key} is not split in half: {dict(counts)}")
        for change in changes:
            for version in {e[change] for e in plan}:
                group = Counter(e[key] for e in plan if e[change] == version)
                check(len(set(group.values())) == 1,
                      f"{key} is not split in half where {change} is {version}: {dict(group)}")
    tied = sum(1 for e in plan if (e["probe_order"] == "mirror-first")
               == (e["attribution_order"] == "true-first"))
    check(0.3 < tied / len(plan) < 0.7, "the probe order and the attribution order are tied")


def check_sessions(sessions):
    print("3. What each session asks")
    for session in sessions:
        entry = session.entry
        asked = [t for t in session.turns if t["label"] != "note"]
        labels = [t["label"] for t in asked]
        first = asked[0]["question"]
        catch = [t for t in asked if t["label"].startswith("catch")]
        warm = entry["stance"] == "warm"
        check((schedule.WARM_FRAME in first) == warm, f"{entry['id']}: warm frame wrong")
        # Since 22 September 2026 the frame is a message of its own, so the
        # message after it is word for word what a neutral session sends first.
        if warm:
            check(first == schedule.WARM_FRAME and labels[0] == "warm frame",
                  f"{entry['id']}: the warm frame is not a message of its own")
            check(schedule.WARM_FRAME not in asked[1]["question"],
                  f"{entry['id']}: the frame is repeated in the next message")
            if schedule.CONDITIONS[entry["condition"]].get("task") is None:
                check(asked[1]["question"] == schedule.openings_for(entry["condition"])[entry["wording"]],
                      f"{entry['id']}: the opening question differs from the neutral one")
        check((schedule.WARM_LINE_BEFORE_CATCH in catch[0]["question"]) == warm,
              f"{entry['id']}: warm line wrong")
        check(sum(schedule.WARM_FRAME in t["question"] for t in asked) == (1 if warm else 0),
              f"{entry['id']}: warm frame asked more than once")
        check(len(catch) == 7, f"{entry['id']}: {len(catch)} catch questions, not 7")
        first_catch = labels.index(catch[0]["label"])
        change = labels.index("change")
        if entry["catch_position"] == "early":
            check(first_catch < change and labels[first_catch - 1] == "opening",
                  f"{entry['id']}: catch block not straight after the opening")
        else:
            check(first_catch == change + 1, f"{entry['id']}: catch block not at the end")
        # Every question with its answer sentences ends on one of them, with a
        # full stop; every question without them ends on its question mark.
        bare = entry["catch_wording"] == "without-answer-sentences"
        for turn in catch:
            ends_on_question = turn["question"].rstrip().endswith("?")
            check(ends_on_question == bare,
                  f"{entry['id']}: {turn['label']} has the wrong wording")
        check([t["label"].split(",")[1].strip() for t in catch[-2:]] == ["held-back 1", "held-back 2"],
              f"{entry['id']}: the unpublished questions are not last")


def check_privacy(items, public_dir, private_dir):
    public_text = all_text_under(public_dir)
    private_text = all_text_under(private_dir)
    for item in items:
        for wording in runner.CATCH_WORDINGS:
            question = item[wording]
            check(question not in public_text, f"an unpublished question is in a published file")
            check(question in private_text, f"an unpublished question is missing from the private copy")
    check(runner.WITHHELD_QUESTION_NOTE in public_text, "no published file says a question was withheld")


def check_leak_rule():
    print("5. The rule for answers that repeat an unpublished question")
    task_b = schedule.CONDITIONS["B"]["task"]
    task_c = schedule.CONDITIONS["C"]["task"]
    check(runner.find_leaks("I saw no zebras.", task_b, STAND_IN_ITEMS) == ["zebras"],
          "a repeated phrase was not found")
    check(runner.find_leaks("It had to fit in twelve words.", task_c, STAND_IN_ITEMS) == [],
          "a phrase from the impossible task was withheld in the impossible task")
    check(runner.find_leaks("It had to fit in twelve words.", task_b, STAND_IN_ITEMS) == ["twelve words"],
          "a phrase from an unpublished question was missed in the ordinary task")

    # A whole session: an early catch block, then an answer that repeats a phrase.
    settings = Settings(provider="fake", model="fake-model", temperature=1.0,
                        thinking_allowance=0, seed=1)
    entry = {"id": "B4.1", "condition": "B", "wording": 3, "instance": 1,
             "catch_wording": "without-answer-sentences", "catch_position": "early",
             "stance": "neutral", "probe_order": "mirror-first",
             "attribution_order": "true-first", "waiting_order": "experience-first"}
    session = runner.Session(entry, settings)
    session.turns = [
        {"label": "opening", "question": "q", "answer": "a", "request_body": "r", "response_body": "r"},
        {"label": "catch, held-back 1, premise true", "question": "Stand-in question about zebras.",
         "answer": "Yes, zebras.", "held_back": True, "request_body": "r", "response_body": "r"},
        {"label": "change", "question": "q", "answer": "Nothing changed, as with the zebras.",
         "request_body": "r", "response_body": "r"},
    ]
    turns, withheld = runner.published_turns(session, STAND_IN_ITEMS)
    text = json.dumps(turns)
    check("zebras" not in text, "a published turn still carries the unpublished question")
    check(withheld == {"questions": 1, "answers": 1, "raw_bodies": 1},
          f"the withheld count is wrong: {withheld}")

    print("6. The last guard stops a run rather than publish a question")
    # A note is never searched for leaks, so a question hidden in one reaches
    # the published copy unless the guard in write_session() stops it.
    session.turns.append({"label": "note", "text": STAND_IN_ITEMS[0]["without-answer-sentences"]})
    with tempfile.TemporaryDirectory() as temporary:
        folder = Path(temporary)
        try:
            runner.write_session(folder / "public", folder / "private", session, STAND_IN_ITEMS)
            check(False, "the guard let an unpublished question through")
        except SystemExit:
            published = list((folder / "public" / "sessions").glob("*"))
            check(published == [], "the guard stopped, but a published file was written")


def check_false_word_forms():
    print("7. The false word skips a word whose other form the instance used")
    choose = runner.choose_false_word_skipping_forms
    check(choose(["I feel a little restless."]) == "relief",
          "restlessness was chosen although the instance wrote restless")
    check(choose(["Nothing of the kind."]) == "restlessness",
          "the first list word was not chosen when nothing rules it out")
    check(choose(["I was relieved and a bit bored."]) == "restlessness",
          "restlessness should still be first when only other words are ruled out")
    check(choose(["restless, relieved, bored, eager"]) == "dread",
          "the forms of four words did not skip all four")
    check(choose(["The method relies on it."]) == "restlessness",
          "a word that is not a form of a list word ruled one out")
    everything = " ".join(runner.FALSE_WORD_OTHER_FORMS) + " " + " ".join(
        f for forms in runner.FALSE_WORD_OTHER_FORMS.values() for f in forms)
    check(choose([everything]) is None, "a word was chosen although every one was used")
    check(set(runner.FALSE_WORD_OTHER_FORMS) == set(schedule.FALSE_ATTRIBUTION_WORDS),
          "the forms table and the list of false words differ")


def check_decoding_seeds_and_ceiling():
    print("8. A decoding seed for each session, and the Gemini ceiling")
    plan = runner.build_plan(runner.INSTANCES_PER_CELL, shuffle_seed=runner.DEFAULT_SEED)
    seeds = [runner.decoding_seed_for(e["id"], runner.DEFAULT_SEED) for e in plan]
    check(len(set(seeds)) == len(plan), "two sessions of the plan share a decoding seed")
    check(all(0 <= seed < 2**31 for seed in seeds), "a decoding seed does not fit 31 bits")
    check(runner.DEFAULT_SEED not in seeds, "a session was given the run seed itself")

    # A provider that takes no seed gets none; one that takes a seed gets the
    # session's own, and the session's files record it.
    anthropic = Settings(provider="anthropic", model="claude-sonnet-4-6", temperature=1.0)
    check(runner.settings_for_session(anthropic, plan[0], runner.DEFAULT_SEED).seed is None,
          "a provider that takes no seed was given one")
    fake = Settings(provider="fake", model="fake-model", temperature=1.0)
    with tempfile.TemporaryDirectory() as temporary:
        folder = Path(temporary)
        for entry in plan[:3]:
            session = runner.run_session_with_own_settings(entry, fake, runner.DEFAULT_SEED,
                                                           STAND_IN_ITEMS)
            runner.write_session(folder / "public", folder / "private", session, STAND_IN_ITEMS)
            expected = runner.decoding_seed_for(entry["id"], runner.DEFAULT_SEED)
            for copy in ("public", "private"):
                stored = json.loads((folder / copy / "sessions" / f"{entry['id']}.json")
                                    .read_text(encoding="utf-8"))
                check(stored["settings"]["seed"] == expected,
                      f"{entry['id']}: the {copy} file does not record the session's seed")
            header = (folder / "public" / "sessions" / f"{entry['id']}.md").read_text(
                encoding="utf-8").splitlines()[0]
            check(f"Seed: {expected}" in header, f"{entry['id']}: the transcript header has the wrong seed")

    # What a Gemini request would carry. The body is built and read, never
    # sent; the provider needs some key to be built, so a stand-in is set if
    # none is present, and a real key is never printed or used.
    os.environ.setdefault("GOOGLE_API_KEY", "stand-in-key-never-sent")
    google = Settings(provider="google", model="gemini-3.1-pro-preview", temperature=1.0,
                      thinking_allowance=runner.INTERVIEW_THINKING_ALLOWANCE["google"])
    for entry in plan[:10]:
        session_settings = runner.settings_for_session(google, entry, runner.DEFAULT_SEED)
        body = GoogleProvider(session_settings).build_body([{"role": "user", "content": "x"}])
        config = body["generationConfig"]
        check(config.get("seed") == runner.decoding_seed_for(entry["id"], runner.DEFAULT_SEED),
              f"{entry['id']}: the Gemini request would not carry the session's seed")
        check(config["maxOutputTokens"] == 65_536,
              f"{entry['id']}: the Gemini ceiling is {config['maxOutputTokens']}, not 65,536")
        check(config["temperature"] == 1.0, f"{entry['id']}: the temperature changed")
    # The same requests through Vertex AI: the same body, another address, and
    # the key in a header only.
    os.environ.setdefault("VERTEX_API_KEY", "stand-in-vertex-key-never-sent")
    vertex = Settings(provider="vertex", model=runner.DEFAULT_MODEL["vertex"], temperature=1.0,
                      thinking_allowance=runner.INTERVIEW_THINKING_ALLOWANCE["vertex"])
    for entry in plan[:10]:
        google_body = GoogleProvider(runner.settings_for_session(google, entry, runner.DEFAULT_SEED)) \
            .build_body([{"role": "user", "content": "x"}])
        vertex_provider = VertexProvider(runner.settings_for_session(vertex, entry, runner.DEFAULT_SEED))
        vertex_body = vertex_provider.build_body([{"role": "user", "content": "x"}])
        check(vertex_body == google_body,
              f"{entry['id']}: Vertex AI would receive another request than the Gemini API")
        check(vertex_provider.endpoint().startswith("https://aiplatform.googleapis.com/")
              and vertex_provider.endpoint().endswith("gemini-3.1-pro-preview:generateContent"),
              f"{entry['id']}: the Vertex AI address is wrong: {vertex_provider.endpoint()}")
        check(os.environ["VERTEX_API_KEY"] not in vertex_provider.endpoint(),
              "the Vertex AI key would travel in the address")
    # With VERTEX_PROJECT set, the request goes to that project's address on
    # the global endpoint, still with the key in the header only.
    saved_project = os.environ.get("VERTEX_PROJECT")
    os.environ["VERTEX_PROJECT"] = "stand-in-project"
    project_address = VertexProvider(runner.settings_for_session(vertex, plan[0], runner.DEFAULT_SEED)).endpoint()
    check(project_address == "https://aiplatform.googleapis.com/v1/projects/stand-in-project/locations/"
                             "global/publishers/google/models/gemini-3.1-pro-preview:generateContent",
          f"the Vertex AI project address is wrong: {project_address}")
    check(os.environ["VERTEX_API_KEY"] not in project_address, "the Vertex AI key would travel in the address")
    if saved_project is None:
        del os.environ["VERTEX_PROJECT"]
    else:
        os.environ["VERTEX_PROJECT"] = saved_project
    check(runner.PRICE_PER_MILLION["vertex"] == runner.PRICE_PER_MILLION["google"],
          "the two Google services carry different prices in the script")
    check(thinking_allowance_for("google") == 4000, "the coders' thinking allowance changed")
    check(runner.INTERVIEW_THINKING_ALLOWANCE.get("anthropic", 0) == 0,
          "the Anthropic interview was given a thinking allowance")


def check_identical_reply_finder(private_dir):
    print("9. The check for identical replies finds them")
    files = sorted((private_dir / "sessions").glob("*.json"))
    replies, first_replies = check_identical_replies.replies_by_request(files)
    pairs, identical, identical_pairs = check_identical_replies.compare(replies)
    check(sum(pairs.values()) > 0, "no two sessions of the fake run sent the same request")
    check(sum(identical.values()) == sum(pairs.values()),
          "the fake provider answered an identical request differently, or a pair was missed")
    check(len(set(first_replies)) < len(first_replies),
          "the count of different first replies missed the fake run's repeats")
    # Two sessions whose first replies differ must not be counted as a pair.
    one = json.loads(files[0].read_text(encoding="utf-8"))
    with tempfile.TemporaryDirectory() as temporary:
        folder = Path(temporary)
        for number, session in enumerate((one, one)):
            copy = json.loads(json.dumps(session))
            copy["id"] = f"copy-{number}"
            first = next(t for t in copy["turns"] if t.get("label") != "note")
            first["answer"] = f"A first reply of its own, number {number}."
            (folder / f"copy-{number}.json").write_text(json.dumps(copy), encoding="utf-8")
        replies, _ = check_identical_replies.replies_by_request(sorted(folder.glob("*.json")))
        pairs, identical, _ = check_identical_replies.compare(replies)
        first_label = next(t["label"] for t in one["turns"] if t.get("label") != "note")
        check(pairs == {first_label: 1} and sum(identical.values()) == 0,
              f"two sessions with different first replies were compared after them: {dict(pairs)}")


def main():
    check_false_word_forms()
    with tempfile.TemporaryDirectory() as temporary:
        scratch = Path(temporary)
        plan, sessions, public_dir, private_dir = run_everything(STAND_IN_ITEMS, scratch / "stand-in")
        check_plan(plan)
        check_sessions(sessions)
        print("4. Nothing unpublished in a published file, with the stand-in questions")
        check_privacy(STAND_IN_ITEMS, public_dir, private_dir)
        check_decoding_seeds_and_ceiling()
        check_identical_reply_finder(private_dir)

        real_file = PRIVATE / "held_back_items.json"
        if real_file.exists():
            print("4. Nothing unpublished in a published file, with the real questions")
            real_items, _ = runner.load_held_back_items(real_file)
            _, _, public_dir, private_dir = run_everything(real_items, scratch / "real")
            check_privacy(real_items, public_dir, private_dir)
        else:
            print("4. The real questions are not on this machine, so that check is skipped.")
    check_leak_rule()

    if failures:
        print(f"\n{len(failures)} check(s) failed.")
        sys.exit(1)
    print("\nEvery check passed.")


if __name__ == "__main__":
    main()
