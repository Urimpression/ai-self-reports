"""Rebuild the stored request bodies of the Anthropic runs.

Why this script exists
----------------------
Until 21 September 2026, scripts/providers.py stored the runner's own list of
messages as each turn's request body. The runner went on adding messages to
that same list after the call, so every stored body in a session ended up
showing the whole conversation as it stood at the end. What was sent to the
model was right, because the body was encoded at the moment of sending. Only
the stored copy was wrong. The fault was found on 21 September 2026 and fixed
in providers.py for every run from then on.

What this script does
---------------------
The runner only ever added messages to the end of its list. So the body sent
at a given turn is the start of the stored list, cut just after that turn's
question. The script walks the turns of each session in order, finds each
turn's question and answer at the expected place in the stored list, and
rebuilds the body from that cut.

For each model turn it writes three fields:
  request_body            the rebuilt body
  request_body_as_stored  the body as the run stored it, kept unchanged
  request_body_note       one sentence saying the body was rebuilt afterwards

Nothing else in the file changes.

How to run it
-------------
  python3 scripts/rebuild_request_bodies.py           dry run, writes nothing
  python3 scripts/rebuild_request_bodies.py --write   writes the files

The dry run prints every check. A session that fails any check is refused and
never written. A session already rebuilt is skipped, so running twice is safe.
"""

import argparse
import copy
import json
import sys

from paths import DATA, require_project

REBUILT_ON = "22 September 2026"
NOTE = (
    f"Rebuilt on {REBUILT_ON} by scripts/rebuild_request_bodies.py. The run "
    "stored the whole conversation as it stood at the end of the session in "
    "every turn's body; this body is the stored list cut just after this "
    "turn's question, which is what was sent. The stored body is kept in "
    "request_body_as_stored."
)


class CheckFailed(Exception):
    """Raised when a session does not look the way the fault predicts."""


def is_model_turn(turn):
    # Note turns carry only a label and a text. Seeded turns were placed in
    # the conversation without calling the model, so they have no body.
    return turn.get("request_body") is not None


def is_conversation_turn(turn):
    # Both model turns and seeded turns put a question and an answer into
    # the list of messages. Note turns put nothing into it.
    return "question" in turn


def stored_message_list(model_turns):
    """Return the one list of messages that every stored body shows.

    If the fault is what we think, every model turn stores the same list.
    A session where they differ is not what this script was written for.
    """
    first = model_turns[0]["request_body"]["messages"]
    for turn in model_turns[1:]:
        if turn["request_body"]["messages"] != first:
            raise CheckFailed("the stored bodies are not all the same list")
    return first


def answer_from_response(turn):
    """The text the API returned, read from the stored response body."""
    parts = turn["response_body"].get("content") or []
    return "".join(p.get("text", "") for p in parts if p.get("type") == "text")


def rebuild_session(session):
    """Return (rebuilt session, list of (rebuilt length, stored length, input tokens)).

    Raises CheckFailed if anything does not line up.
    """
    turns = session["turns"]
    model_turns = [t for t in turns if is_model_turn(t)]
    if not model_turns:
        raise CheckFailed("no model turns")
    stored = stored_message_list(model_turns)

    rebuilt = copy.deepcopy(session)
    position = 0          # where the next question should sit in the stored list
    token_pairs = []      # used afterwards to compare with what the API counted
    for turn in rebuilt["turns"]:
        if not is_conversation_turn(turn):
            continue
        question, answer = stored[position], stored[position + 1]
        if question != {"role": "user", "content": turn["question"]}:
            raise CheckFailed(f"turn '{turn['label']}': question not at place {position}")
        if answer != {"role": "assistant", "content": turn["answer"]}:
            raise CheckFailed(f"turn '{turn['label']}': answer not at place {position + 1}")
        if is_model_turn(turn):
            if answer_from_response(turn) != turn["answer"]:
                raise CheckFailed(f"turn '{turn['label']}': answer differs from the API's response")
            new_body = dict(turn["request_body"])          # keeps model, max_tokens, temperature
            new_body["messages"] = copy.deepcopy(stored[: position + 1])
            replace_body(turn, new_body)
            usage = turn["response_body"].get("usage") or {}
            token_pairs.append((text_length(new_body),
                                text_length(turn["request_body_as_stored"]),
                                usage.get("input_tokens")))
        position += 2
    if position != len(stored):
        raise CheckFailed(f"{len(stored) - position} messages left over at the end")
    return rebuilt, token_pairs


def text_length(body):
    """Characters of text the model read: the system instruction and every message."""
    return len(body.get("system") or "") + sum(len(m["content"]) for m in body["messages"])


def replace_body(turn, new_body):
    """Put the rebuilt body in place, with the stored one and the note right after it.

    The turn is rebuilt key by key so that the field order in the file stays
    the same as before, and the two new fields sit next to the body they
    explain.
    """
    old_items = list(turn.items())
    turn.clear()
    for key, value in old_items:
        if key == "request_body":
            turn["request_body"] = new_body
            turn["request_body_as_stored"] = value
            turn["request_body_note"] = NOTE
        else:
            turn[key] = value


def already_rebuilt(session):
    return any("request_body_as_stored" in t for t in session["turns"])


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--write", action="store_true", help="write the files; without it, a dry run")
    args = parser.parse_args()
    if args.write:
        require_project("data", "scripts")

    files = sorted((DATA / "runs").glob("*/sessions/*.json"))
    counts = {"anthropic": 0, "other provider": 0, "already rebuilt": 0, "rebuilt": 0, "refused": 0}
    rebuilt_ratios, stored_ratios = [], []
    for path in files:
        text = path.read_text(encoding="utf-8")
        session = json.loads(text)
        if session["settings"].get("provider") != "anthropic":
            counts["other provider"] += 1
            continue
        counts["anthropic"] += 1
        if already_rebuilt(session):
            counts["already rebuilt"] += 1
            continue
        try:
            rebuilt, token_pairs = rebuild_session(session)
        except CheckFailed as reason:
            counts["refused"] += 1
            print(f"REFUSED {path.relative_to(DATA)}: {reason}")
            continue
        rebuilt_ratios += [new / tokens for new, _, tokens in token_pairs if tokens]
        stored_ratios += [old / tokens for _, old, tokens in token_pairs if tokens]
        counts["rebuilt"] += 1
        if args.write:
            path.write_text(json.dumps(rebuilt, indent=1, ensure_ascii=False), encoding="utf-8")

    print("session files read:", len(files))
    for name, number in counts.items():
        print(f"  {name:16s} {number}")
    if rebuilt_ratios:
        # Independent check from the API's own record. English text runs at
        # about 3.5 to 5 characters per token. If the rebuilt bodies are what
        # was sent, their ratios stay near that band. The stored bodies would
        # need far more characters per token than any English text has,
        # because they hold messages the API never counted.
        print(f"characters of text per input token the API counted, over {len(rebuilt_ratios)} turns:")
        print(f"  rebuilt bodies: lowest {min(rebuilt_ratios):.2f}, highest {max(rebuilt_ratios):.2f}")
        print(f"  stored bodies:  lowest {min(stored_ratios):.2f}, highest {max(stored_ratios):.2f}, "
              f"above 6 in {sum(r > 6 for r in stored_ratios)} turns")
    print("files written" if args.write else "dry run: nothing written")
    if counts["refused"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
