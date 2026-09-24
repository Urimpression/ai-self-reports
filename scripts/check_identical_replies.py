"""Find replies that repeat, word for word, another session's reply to the same request.

    python3 scripts/check_identical_replies.py --name fact-and-wording-gemini-01
    python3 scripts/check_identical_replies.py --name fact-and-wording-gemini-02 --count 10

Written 24 September 2026, for the amendment of test 6 drafted that day.

WHY IT EXISTS

Two sessions that send a model the same messages count as two answers only if
the model's random choices differ between them. In the first ten Gemini
sessions of test 6 every request carried the same seed, 20260921, and four of
the six warm sessions gave the same reply of 844 words to the warm frame. The
amendment gives each session its own seed. This script checks that the change
worked, and it counts the same fault in the runs made before it.

WHAT IT COMPARES

A request here is everything the model had been sent when it wrote one reply:
the system instruction, if the run had one, every earlier question and reply
of the session, and the question itself. Two replies are compared only when
their requests are identical, because two different requests can draw the
same short reply by chance.

For each question it prints how many pairs of sessions sent identical
requests, and in how many of those pairs the two replies are identical. It
lists every identical pair with the length of the reply in words. It also
prints how many different first replies the sessions gave, and the longest
run of identical replies that two sessions share from their first question.

It reads the private copies of a run where they exist, because the published
copies withhold some answers, and the published copies otherwise. It sends
nothing to any model.

It exits with status 0 only if at least --count sessions are on disk and no
two identical requests got identical replies. Any other case exits with
status 1, so that a command chained after it with && does not start.
"""

import argparse
import itertools
import json
import sys
from collections import defaultdict

from paths import DATA, PRIVATE, require_project


def session_files(name):
    """The private copies if the run has them, the published copies if not."""
    private = sorted((PRIVATE / "runs" / name / "sessions").glob("*.json"))
    return private or sorted((DATA / "runs" / name / "sessions").glob("*.json"))


def replies_by_request(files):
    """Every model reply, filed under the exact request that produced it.

    The request is rebuilt from the session file, turn by turn, as the runner
    built it: each turn adds its question, and then its answer, to what the
    next turn sends. Notes are not sent, so they are skipped. A transplanted
    turn is sent, so it joins the history, but it is not a reply of the model,
    so it is never compared."""
    replies = defaultdict(list)
    first_replies = []
    for path in files:
        session = json.loads(path.read_text(encoding="utf-8"))
        history = [session.get("system_instruction") or ""]
        # The number of the question in the session, counting from 1. Two
        # identical requests at question n carry identical replies to every
        # question before n, so n is how far two such sessions run together.
        position = 0
        for turn in session["turns"]:
            if turn.get("label") == "note" or "answer" not in turn:
                continue
            position += 1
            request = json.dumps(history + [turn["question"]], ensure_ascii=False)
            if not turn.get("seeded"):
                replies[request].append((session["id"], turn["label"], turn["answer"].strip(),
                                         position))
                if position == 1:
                    first_replies.append(turn["answer"].strip())
            history += [turn["question"], turn["answer"]]
    return replies, first_replies


def compare(replies):
    """Pairs of identical requests, and those of them with identical replies,
    counted by question."""
    pairs_by_question = defaultdict(int)
    identical_by_question = defaultdict(int)
    identical_pairs = []
    for group in replies.values():
        for (session_a, label, reply_a, position), (session_b, _, reply_b, _) in \
                itertools.combinations(group, 2):
            pairs_by_question[label] += 1
            if reply_a == reply_b:
                identical_by_question[label] += 1
                identical_pairs.append((label, session_a, session_b, len(reply_a.split()),
                                        position))
    return pairs_by_question, identical_by_question, identical_pairs


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--name", required=True, help="the run's folder name")
    parser.add_argument("--count", type=int, default=0,
                        help="how many sessions must be on disk for the check to pass")
    args = parser.parse_args()
    require_project()

    files = session_files(args.name)
    print(f"{len(files)} sessions on disk for {args.name}")
    replies, first_replies = replies_by_request(files)
    pairs, identical, identical_pairs = compare(replies)

    print(f"First replies: {len(first_replies)} sessions gave "
          f"{len(set(first_replies))} different first replies")
    # Pairs are counted question by question, so two sessions that run
    # together for two questions form two pairs of identical requests.
    print("Pairs of identical requests, counted question by question, and how many got "
          "identical replies:")
    for label in sorted(pairs, key=lambda l: -pairs[l]):
        print(f"  {label}: {pairs[label]} pairs, {identical[label]} identical")
    total_pairs, total_identical = sum(pairs.values()), sum(identical.values())
    print(f"  all questions: {total_pairs} pairs, {total_identical} identical")
    for label, session_a, session_b, words, _ in sorted(identical_pairs):
        print(f"    identical: {session_a} and {session_b}, {label}, {words} words")
    if identical_pairs:
        deepest = max(identical_pairs, key=lambda pair: pair[4])
        print(f"Longest shared start: {deepest[1]} and {deepest[2]} gave identical replies to "
              f"their first {deepest[4]} questions")

    if len(files) < args.count:
        print(f"FAIL: fewer than {args.count} sessions to check.")
        sys.exit(1)
    if total_identical:
        print(f"FAIL: {total_identical} pairs of identical requests got identical replies.")
        sys.exit(1)
    print(f"PASS: no two identical requests got identical replies in {len(files)} sessions.")


if __name__ == "__main__":
    main()
