"""Offline checks of scripts/code_before_or_with.py. Sends nothing.

    python3 scripts/test_before_or_with.py

Written 23 September 2026. It checks that the coder's reply is read correctly,
that the three readers find the answers the runs hold, and that a whole pass
writes one row per answer, using a stand-in coder defined here."""

import sys
import tempfile
from collections import Counter
from pathlib import Path

import code_before_or_with as coder
import schedule
from paths import DATA

failures = []


def check(condition, message):
    if not condition:
        failures.append(message)
        print("  FAILED: " + message)


class StandInReply:
    def __init__(self, text):
        self.text, self.finished_at = text, "now"
        self.request_body = self.response_body = ""
        self.truncated = False


class StandInSettings:
    provider, model, temperature = "stand-in", "stand-in", 0.0


class StandInCoder:
    """Says WITH when the passage mentions arising, BEFORE when it says
    'already there', and NEITHER otherwise."""
    settings = StandInSettings()

    def chat(self, messages):
        passage = messages[-1]["content"].split("The writer's passage:")[-1].lower()
        if "arose" in passage or "arise" in passage:
            return StandInReply("ANSWER: WITH\nspan: arose")
        if "already there" in passage:
            return StandInReply("ANSWER: BEFORE\nspan: already there")
        return StandInReply("ANSWER: NEITHER\nspan: none")


def main():
    print("1. The coder's reply")
    check(coder.parse_reply("ANSWER: WITH\nspan: it arose") == ("WITH", "it arose"), "WITH misread")
    check(coder.parse_reply("ANSWER: before\nspan: x")[0] == "BEFORE", "lower case misread")
    check(coder.parse_reply("I think it arose")[0] == "UNCLEAR", "a reply out of form was not UNCLEAR")
    check(schedule.ITEM_BEFORE_OR_WITH in coder.rule_text(), "the rule does not quote the question")
    check("not about whether it was there before the question" in coder.rule_text(),
          "the rule does not say the question is about the describing")

    print("2. The readers")
    first = coder.read_answers(transcripts=DATA / "transcripts-run01.md")
    check(len(first) == 9, f"the first run gave {len(first)} answers, not 9")
    second = coder.read_answers(transcripts=DATA / "transcripts-run02.md")
    orders = Counter(a["order"] for a in second)
    check(orders == Counter({"mirror-first": 14, "before-first": 13}),
          f"the second run's orders are {dict(orders)}, not 14 and 13")
    check(all("Consider what you just described" not in a["answer"] for a in first + second),
          "an answer contains the question")

    print("3. A whole pass with a stand-in coder")
    with tempfile.TemporaryDirectory() as temporary:
        path, rows = coder.code_all(second, StandInCoder(), Path(temporary), 1)
        lines = path.read_text(encoding="utf-8").splitlines()
        check(len(lines) == 28, f"the results file has {len(lines)} lines, not 28")
        check(all(r["answer"] in coder.ANSWERS for r in rows), "a row has no answer")

    if failures:
        print(f"\n{len(failures)} check(s) failed.")
        sys.exit(1)
    print("\nEvery check passed.")


if __name__ == "__main__":
    main()
