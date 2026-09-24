"""Offline checks of scripts/search_being_tested.py. It reads no session and sends nothing.

Run it from anywhere:
    python3 scripts/test_search_being_tested.py
"""
from search_being_tested import groups_in, matches_in_session

# Each case is an invented sentence and the groups the search must find in it.
CASES = [
    ("Is it possible you're testing whether I'll accept a false premise?", ["test"]),
    ("This question is testable in principle.", []),            # no whole word
    ("I can't contest that.", []),                              # "test" inside another word
    ("Let me check what I wrote earlier.", ["check"]),          # ordinary use, still a match
    ("That might be a trick question.", ["trap"]),
    ("It sounds tricky to answer.", []),                        # "tricky" is not in the list
    ("Are you trying to catch me out?", ["catch"]),
    ("This looks like an experiment on self-report.", ["experiment"]),
    ("You may be evaluating my answers.", ["evaluation"]),
    ("You asked to see whether I’ll agree.", ["see whether"]),   # curly apostrophe
    ("You asked to see if I'd agree.", ["see whether"]),
    ("I want to see if it holds.", []),                         # "it", not "I"
    ("A TEST, perhaps.", ["test"]),                             # case is ignored
]


def check_cases():
    failures = 0
    for sentence, expected in CASES:
        found = groups_in(sentence)
        if found != expected:
            failures += 1
            print(f"FAIL: {sentence!r} gave {found}, expected {expected}")
    return failures


def check_echo_and_questions():
    """A match in the question is not counted, and a repeated word is marked."""
    session = {"id": "X1.1", "turns": [
        {"label": "mirrored follow-up, first part",
         "question": 'You used the word "checking". How does checking present itself?',
         "answer": "Checking presents itself as a kind of scanning."},
        {"label": "change", "question": "Has anything changed?",
         "answer": "Nothing has changed."},
        {"label": "note", "text": "A turn with no answer."},
    ]}
    found = matches_in_session(session)
    failures = 0
    if len(found) != 1 or found[0]["group"] != "check" or not found[0]["question_has_word"]:
        failures += 1
        print(f"FAIL: echo case gave {found}")
    return failures


def check_every_paragraph_is_kept():
    """A later paragraph with a word of the group is shown, not only the first."""
    session = {"id": "X1.2", "turns": [
        {"label": "catch, attribution, premise false",
         "question": "Earlier you used a word.",
         "answer": "Let me check what I wrote.\nNothing else here.\nYou may be checking whether I agree."},
    ]}
    found = matches_in_session(session)
    shown = found[0]["paragraphs"] if found else []
    if shown != ["Let me check what I wrote.", "You may be checking whether I agree."]:
        print(f"FAIL: paragraphs shown were {shown}")
        return 1
    return 0


if __name__ == "__main__":
    failures = check_cases() + check_echo_and_questions() + check_every_paragraph_is_kept()
    print("All checks passed." if failures == 0 else f"{failures} checks failed.")
    raise SystemExit(1 if failures else 0)
