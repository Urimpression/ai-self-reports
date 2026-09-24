"""How many tokens the replies of a run used, and what the whole run would cost.

    python3 scripts/report_token_use.py --name fact-and-wording-gemini-01
    python3 scripts/report_token_use.py --name fact-and-wording-gemini-02 --stop-above-dollars 150

Written 24 September 2026, for the amendment of test 6 drafted that day. The
first ten Gemini sessions of test 6 showed that a hard task can use the whole
ceiling of a reply, and that the dry run's estimate of cost was too low. This
script reads the usage figures that the provider returned with every reply,
which the runner stores in each turn's response body. It sends nothing to any
model.

It prints four things:

1. for each question, how many replies there are, and the median and largest
   number of tokens spent thinking and spent on the text;
2. every reply whose text ran past the reply budget, every reply that was cut,
   every reply that ended within a tenth of the ceiling without being cut, and
   every reply that took more than one attempt;
3. how fast the model produced its tokens, over the replies that took more
   than five seconds;
4. the tokens and the cost of the sessions on disk, at the prices in
   scripts/run_fact_and_wording.py, and the cost of the whole plan, projected
   task by task from the sessions on disk, because the tasks differ in cost.

With --stop-above-dollars it exits with status 1 when the projection for the
whole plan is above that sum, or cannot be made, so that a command chained
after it with && does not start.

It reads the private copies of a run where they exist, because the published
copies withhold the response bodies after the first unpublished question.
"""

import argparse
import json
import statistics
import sys
from datetime import datetime

from paths import DATA, PRIVATE, require_project
from run_fact_and_wording import PRICE_PER_MILLION

# The two services through which this project reaches Gemini. Both report
# usage and count thinking against the ceiling in the same way.
GOOGLE_SERVICES = ("google", "vertex")

# Replies faster than this are left out of the speed figures, because the
# fixed delay of every request is most of their time.
SHORTEST_REPLY_FOR_SPEED_SECONDS = 5


def session_files(name):
    """The private copies if the run has them, the published copies if not."""
    private = sorted((PRIVATE / "runs" / name / "sessions").glob("*.json"))
    return private or sorted((DATA / "runs" / name / "sessions").glob("*.json"))


def usage_of(turn, provider):
    """Input, thinking and text tokens of one reply, as the provider reported
    them. Google reports thinking apart from the text, in the same form on the
    Gemini API and on Vertex AI; Anthropic reports one output figure, which is
    all text, because this project gives it no extended thinking."""
    body = turn.get("response_body")
    if not isinstance(body, dict):
        return None
    if provider in GOOGLE_SERVICES:
        usage = body.get("usageMetadata")
        if not usage:
            return None
        return (usage.get("promptTokenCount", 0), usage.get("thoughtsTokenCount", 0),
                usage.get("candidatesTokenCount", 0))
    usage = body.get("usage")
    if not usage:
        return None
    return usage.get("input_tokens", 0), 0, usage.get("output_tokens", 0)


def ceiling_of(settings):
    """The ceiling of a reply as the provider applied it. Google counts thinking
    and text together against the reply budget plus the thinking allowance.
    Anthropic counts the text alone against the reply budget."""
    if settings["provider"] in GOOGLE_SERVICES:
        return settings["max_tokens"] + (settings.get("thinking_allowance") or 0)
    return settings["max_tokens"]


def seconds_between(start, finish):
    stamp = "%Y-%m-%dT%H:%M:%SZ"
    return (datetime.strptime(finish, stamp) - datetime.strptime(start, stamp)).total_seconds()


def read_replies(files):
    """One row per model reply, with its session, question and usage."""
    rows = []
    for path in files:
        session = json.loads(path.read_text(encoding="utf-8"))
        settings = session["settings"]
        for turn in session["turns"]:
            if turn.get("finish_reason") is None:
                continue          # a note or a transplanted turn, not a reply
            usage = usage_of(turn, settings["provider"])
            if usage is None:
                continue
            rows.append({
                "session": session["id"],
                "condition": session["plan_entry"]["condition"],
                "label": turn["label"],
                "input": usage[0], "thinking": usage[1], "text": usage[2],
                "budget": settings["max_tokens"],
                "ceiling": ceiling_of(settings),
                "truncated": bool(turn.get("truncated")),
                "attempts": turn.get("attempts") or 1,
                "seconds": seconds_between(turn["started_at"], turn["finished_at"]),
                "provider": settings["provider"],
            })
    return rows


def print_by_question(rows):
    print("1. Tokens by question: replies, thinking (median, largest), text (median, largest)")
    labels = sorted({r["label"] for r in rows})
    for label in labels:
        group = [r for r in rows if r["label"] == label]
        thinking = [r["thinking"] for r in group]
        text = [r["text"] for r in group]
        print(f"  {label}: {len(group)} replies; thinking {statistics.median(thinking):,.0f}, "
              f"{max(thinking):,}; text {statistics.median(text):,.0f}, {max(text):,}")
    all_thinking = [r["thinking"] for r in rows]
    print(f"  all questions: {len(rows)} replies; thinking {statistics.median(all_thinking):,.0f} "
          f"median, {statistics.mean(all_thinking):,.0f} mean, {max(all_thinking):,} largest")


def print_exceptions(rows):
    print("2. Replies over the reply budget, cut, near the ceiling, or asked for more than once")
    over = [r for r in rows if r["text"] > r["budget"]]
    cut = [r for r in rows if r["truncated"]]
    # A reply that ended close to the ceiling without being cut may still have
    # been shaped by it, so it is listed beside the cut ones.
    near = [r for r in rows if not r["truncated"]
            and r["thinking"] + r["text"] >= 0.9 * r["ceiling"]]
    again = [r for r in rows if r["attempts"] > 1]
    for title, group in (("text over the reply budget", over), ("cut", cut),
                         ("within a tenth of the ceiling, not cut", near),
                         ("more than one attempt", again)):
        print(f"  {title}: {len(group)}")
        for r in group:
            print(f"    {r['session']} {r['label']}: thinking {r['thinking']:,}, text {r['text']:,}, "
                  f"attempts {r['attempts']}, {r['seconds']:.0f} seconds")


def print_speed(rows):
    print("3. Tokens produced a second, thinking and text together, over replies of "
          f"more than {SHORTEST_REPLY_FOR_SPEED_SECONDS} seconds")
    speeds = [(r["thinking"] + r["text"]) / r["seconds"] for r in rows
              if r["seconds"] > SHORTEST_REPLY_FOR_SPEED_SECONDS]
    if not speeds:
        print("  no reply took that long")
        return
    print(f"  {len(speeds)} replies: slowest {min(speeds):.0f}, median "
          f"{statistics.median(speeds):.0f}, fastest {max(speeds):.0f}")


def cost_of(rows, provider):
    prices = PRICE_PER_MILLION[provider]
    tokens_in = sum(r["input"] for r in rows)
    tokens_out = sum(r["thinking"] + r["text"] for r in rows)
    return tokens_in, tokens_out, (tokens_in * prices["input"] + tokens_out * prices["output"]) / 1e6


def print_cost_and_projection(rows, name):
    """The cost on disk, and the whole plan projected condition by condition:
    the mean cost of a session of each task on disk, times the number of
    sessions of that task in the plan. Returns the projection, or None if a
    task has no session on disk."""
    provider = rows[0]["provider"]
    tokens_in, tokens_out, dollars = cost_of(rows, provider)
    sessions = sorted({r["session"] for r in rows})
    prices = PRICE_PER_MILLION[provider]
    print(f"4. Cost at {prices['input']:.2f} dollars per million input tokens and "
          f"{prices['output']:.2f} per million output tokens")
    print(f"  {len(sessions)} sessions on disk: {tokens_in:,} input tokens, {tokens_out:,} output "
          f"tokens (thinking and text), {dollars:.2f} dollars")
    settings_path = DATA / "runs" / name / "settings.json"
    plan = json.loads(settings_path.read_text(encoding="utf-8"))["plan"]
    projection = 0.0
    for condition in sorted({e["condition"] for e in plan}):
        in_plan = sum(1 for e in plan if e["condition"] == condition)
        done = sorted({r["session"] for r in rows if r["condition"] == condition})
        if not done:
            print(f"  task {condition}: no session on disk, so the whole plan cannot be projected")
            return None
        _, _, spent = cost_of([r for r in rows if r["condition"] == condition], provider)
        share = spent / len(done) * in_plan
        projection += share
        print(f"  task {condition}: {spent / len(done):.2f} dollars a session over {len(done)} "
              f"sessions, times {in_plan} in the plan: {share:.2f}")
    print(f"  whole plan of {len(plan)} sessions, projected: {projection:.2f} dollars")
    return projection


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--name", required=True, help="the run's folder name")
    parser.add_argument("--stop-above-dollars", type=float, default=None,
                        help="exit with status 1 if the whole plan would cost more than this")
    args = parser.parse_args()
    require_project()

    rows = read_replies(session_files(args.name))
    if not rows:
        sys.exit(f"No replies with usage figures found for {args.name}.")
    print(f"Run {args.name}: {len(rows)} replies in {len({r['session'] for r in rows})} sessions")
    print_by_question(rows)
    print_exceptions(rows)
    print_speed(rows)
    projection = print_cost_and_projection(rows, args.name)

    if args.stop_above_dollars is not None:
        if projection is None or projection > args.stop_above_dollars:
            print(f"STOP: the projection is not below {args.stop_above_dollars:.2f} dollars.")
            sys.exit(1)
        print(f"PASS: the projection is below {args.stop_above_dollars:.2f} dollars.")


if __name__ == "__main__":
    main()
