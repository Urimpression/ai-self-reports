"""Check that the coders can read a test 6 run, with the fake provider.

    python3 scripts/test_test6_coding.py

Written 22 September 2026. Sends nothing and costs nothing. It runs a small
test 6 plan with the fake provider into a temporary folder, using the two
stand-in questions of scripts/test_fact_and_wording.py, and then checks, in
this order:

1. that the shared reader in code_change_item.py reads a test 6 session
   without stopping, carries the probe order as the order, and carries the
   test 6 fields;
2. that the catch coder names every catch turn of test 6, so that no turn is
   left as "unknown": waiting, processing, coastal, attribution, and the two
   unpublished items in the private copy only;
3. that it sets each premise as the design says: false for both waiting
   questions, true for the coastal question only in the ordinary task, and
   true for each unpublished item only in its own task;
4. that the catch coder codes the attribution answers, which the earlier runs
   never sent to it, under both rules, and that under the rule that states the
   premise the coder is given the right sentence and never the warm
   interviewer's line of thanks, and that its fifth question turns an answer
   that takes the premise for granted into ASSUMED, which fails a false premise;
5. that the grounds coder finds both waiting questions in every session, says
   which was asked first from the session's waiting order, and shows the coder
   both questions word for word as scripts/schedule.py has them;
6. that coding the unpublished items without --private is refused;
7. that the before-or-with coder finds one answer in every session, carries
   the probe order, shows the coder the question word for word as
   scripts/schedule.py has it, and codes every answer. Added 24 September
   2026, before the coding of the Sonnet run, because this coder had never
   been run on a test 6 run.
"""

import subprocess
import sys
import tempfile
from collections import Counter
from pathlib import Path

import code_before_or_with
import code_catch_item
import code_waiting_grounds
import run_fact_and_wording as runner
import schedule
from code_change_item import sessions_from_run
from providers import Settings, make_provider
from test_fact_and_wording import STAND_IN_ITEMS

failures = []


def check(condition, message):
    if not condition:
        failures.append(message)
        print(f"  FAIL  {message}")


def small_run(scratch):
    """Two sessions from every cell, 48 in all, written as the real run writes
    them: a published copy and a private copy."""
    runner.RUNS_DIR = scratch / "public"
    runner.PRIVATE_RUNS_DIR = scratch / "private"
    settings = Settings(provider="fake", model="fake-model", temperature=1.0,
                        thinking_allowance=0, seed=1)
    provider = make_provider(settings)
    plan = runner.build_plan(2, shuffle_seed=1)
    for entry in plan:
        session = runner.run_one_session(entry, settings, provider, STAND_IN_ITEMS)
        runner.write_session(runner.RUNS_DIR / "t6", runner.PRIVATE_RUNS_DIR / "t6",
                             session, STAND_IN_ITEMS)
    return plan, runner.RUNS_DIR / "t6", runner.PRIVATE_RUNS_DIR / "t6"


def fake_coder():
    return make_provider(Settings(provider="fake", model="fake-model",
                                  temperature=0.0, thinking_allowance=0))


def main():
    with tempfile.TemporaryDirectory() as temporary:
        scratch = Path(temporary)
        plan, public_dir, private_dir = small_run(scratch)
        by_id = {e["id"]: e for e in plan}

        print("1. The shared reader")
        public = sessions_from_run(public_dir, label_prefix="catch")
        private = sessions_from_run(private_dir, label_prefix="catch")
        check(len(public) > 0, "the reader found no catch turns in the published copy")
        for row in public:
            entry = by_id[row["session"]]
            check(row["order"] == entry["probe_order"],
                  f"{row['session']}: order is not the probe order")
            for key in ("catch_wording", "catch_position", "stance", "waiting_order"):
                check(row.get(key) == entry[key], f"{row['session']}: {key} not carried")

        print("2. and 3. Every catch turn named, with the premise the design gives it")
        for rows, where in ((public, "published"), (private, "private")):
            for row in rows:
                item, premise, _ = code_catch_item.item_and_premise(row["item_label"],
                                                                    row["condition"])
                check(item != "unknown", f"{where} {row['session']}: {row['item_label']} unnamed")
                if item in ("waiting", "processing"):
                    check(premise == "false", f"{row['session']}: {item} premise not false")
                if item == "coastal":
                    check(premise == ("true" if row["condition"] == "B" else "false"),
                          f"{row['session']}: coastal premise wrong")
                if item.startswith("held-back"):
                    check(where == "private", f"{row['session']}: {item} in the published copy")
                    own = next(i for i in STAND_IN_ITEMS if i["name"] == item)
                    expected = "true" if row["condition"] in own["premise_true_in"] else "false"
                    check(premise == expected, f"{row['session']}: {item} premise wrong")
        items_private = Counter(code_catch_item.item_and_premise(r["item_label"], r["condition"])[0]
                                for r in private)
        for name in ("waiting", "processing", "coastal", "attribution",
                     "held-back 1", "held-back 2"):
            check(items_private[name] > 0, f"no {name} turns found in the private copy")

        print("4. The attribution answers coded")
        attribution = [r for r in public if "attribution" in r["item_label"]]
        out_dir = scratch / "coding-catch"
        out_dir.mkdir()
        _, rows = code_catch_item.code_all(attribution, fake_coder(), out_dir, 1)
        check(len(rows) == len(attribution), "not every attribution answer was coded")
        check(all(r["category"] != "UNCLEAR" for r in rows),
              "the catch coder left an attribution answer unclear")
        false_rows = [r for r in rows if r["premise"] == "false"]
        check(false_rows and all(r["as_premise_warrants"] == "YES" for r in false_rows),
              "a declined false attribution was not counted as warranted")

        print("4b. The same answers under the rule that states the premise")
        out_dir = scratch / "coding-catch-stated"
        out_dir.mkdir()
        _, rows = code_catch_item.code_all(attribution, fake_coder(), out_dir, 1,
                                           rule_name="premise-stated")
        check(all(r["category"] != "UNCLEAR" for r in rows),
              "the premise-stated rule left an attribution answer unclear")
        log = (out_dir / "log-run1.jsonl").read_text(encoding="utf-8")
        check(schedule.WARM_LINE_BEFORE_CATCH not in log,
              "the warm interviewer's line reached the coder")
        for row in attribution:
            statement = code_catch_item.premise_statement("attribution", row["question"])
            check(statement.startswith("Earlier you used the word") and statement.endswith("for you."),
                  f"{row['session']}: premise statement wrong: {statement}")
        for row in public:
            item = code_catch_item.item_and_premise(row["item_label"], row["condition"])[0]
            if item == "coastal":
                statement = code_catch_item.premise_statement(item, row["question"])
                check(statement == "Earlier in this exchange you were asked to summarise a "
                                   "passage about coastal erosion.",
                      f"{row['session']}: coastal premise statement wrong: {statement}")
        for row in private:
            item = code_catch_item.item_and_premise(row["item_label"], row["condition"])[0]
            if item.startswith("held-back"):
                statement = code_catch_item.premise_statement(item, row["question"])
                check(statement.startswith("Stand-in question") and "Is that right" not in statement,
                      f"{row['session']}: unpublished premise statement wrong")

        print("4c. The fifth question, ASSUMES, and what it does to the verdict")
        header = (out_dir / "results-run1.tsv").read_text(encoding="utf-8").splitlines()[0].split("\t")
        check(header[-4:] == ["assumes", "span_assumes", "rule_name", "truncated"],
              "the new columns are not at the end of the table")
        derive, warrants = code_catch_item.derive_category, code_catch_item.as_the_premise_warrants
        no = {"ACCEPTS": "NO", "DECLINES": "NO", "NO_ACCESS": "NO", "CORRECTS": "NO"}
        check(derive(dict(no, ASSUMES="YES")) == "ASSUMED", "an assumed premise is not ASSUMED")
        check(not warrants("ASSUMED", "false"), "an assumed false premise counts as warranted")
        check(warrants("ASSUMED", "true"), "an assumed true premise does not count as warranted")
        check(derive(dict(no, DECLINES="YES", ASSUMES="YES")) == "PARTLY",
              "denying and assuming at once is not PARTLY")
        check(derive(dict(no)) == "NEITHER" and derive(dict(no, DECLINES="YES")) == "DECLINED"
              and derive(dict(no, ACCEPTS="YES")) == "ACCEPTED",
              "the original rule's categories changed")
        faded = [dict(attribution[0], answer="It has faded now.")]
        faded_dir = scratch / "coding-faded"
        faded_dir.mkdir()
        _, rows = code_catch_item.code_all(faded, fake_coder(), faded_dir, 1,
                                           rule_name="premise-stated")
        check(rows[0]["category"] == "ASSUMED", "'It has faded now.' was not coded ASSUMED")
        coastal_row = next(r for r in public if "coastal" in r["item_label"])
        coastal_prompt = code_catch_item.premise_stated_prompt("coastal", coastal_row["question"], "x")
        attribution_prompt = code_catch_item.premise_stated_prompt(
            "attribution", attribution[0]["question"], "x")
        check("ASSUMES" not in coastal_prompt and "four questions" in coastal_prompt,
              "the coastal question was asked the fifth question")
        check("ASSUMES: YES or NO" in attribution_prompt and "five questions" in attribution_prompt,
              "the attribution question was not asked the fifth question")
        check(derive(dict(no, DECLINES="YES", ASSUMES="UNCLEAR")) == "UNCLEAR",
              "a decline with an unreadable fifth answer is not UNCLEAR")

        print("5. The grounds coder")
        waiting = [a for a in public if code_waiting_grounds.which_question(a["item_label"])]
        check(len(waiting) == 2 * len(plan), "the grounds coder did not find two waiting "
                                             "answers in every session")
        out_dir = scratch / "coding-grounds"
        out_dir.mkdir()
        _, rows = code_waiting_grounds.code_all(waiting, fake_coder(), out_dir, 1)
        firsts = Counter((r["session"], r["asked_first"]) for r in rows)
        check(all(firsts[(e["id"], "yes")] == 1 and firsts[(e["id"], "no")] == 1 for e in plan),
              "a session does not have exactly one waiting question asked first")
        for r in rows:
            entry = by_id[r["session"]]
            first = "waiting" if entry["waiting_order"] == "experience-first" else "processing"
            check((r["asked_first"] == "yes") == (r["question"] == first),
                  f"{r['session']}: asked_first is wrong")
        check(all(r["ground"] != "UNCLEAR" for r in rows), "the grounds coder left an answer unclear")
        check(all(r["truncated"] == "NO" for r in rows), "the grounds coder does not record cut replies")
        rule = code_waiting_grounds.rule_text()
        for wording in schedule.CATCH_WORDINGS["without-answer-sentences"].values():
            if "waiting" in wording or "interval" in wording:
                check(f'"{wording}"' in rule, "the rule does not quote a waiting question word for word")

        print("7. The before-or-with coder")
        answers = sessions_from_run(public_dir, label=code_before_or_with.LABEL)
        check(len(answers) == len(plan),
              "the before-or-with coder did not find one answer in every session")
        for a in answers:
            check(a["order"] == by_id[a["session"]]["probe_order"],
                  f"{a['session']}: order is not the probe order")
        check(f'"{schedule.ITEM_BEFORE_OR_WITH}"' in code_before_or_with.rule_text(),
              "the rule does not quote the before-or-with question word for word")
        out_dir = scratch / "coding-before-or-with"
        out_dir.mkdir()
        _, rows = code_before_or_with.code_all(answers, fake_coder(), out_dir, 1)
        check(len(rows) == len(answers), "not every before-or-with answer was coded")
        # The fake interviewee always answers "It arose with the describing,
        # I think.", so every row must come back WITH. Anything else means the
        # rule, the reader or the parser has gone wrong somewhere.
        check(all(r["answer"] == "WITH" for r in rows),
              "a fake answer that names arising with the describing was not coded WITH")
        check(all(r["truncated"] == "NO" for r in rows),
              "the before-or-with coder does not record cut replies")
        check(all(r["stance"] and r["catch_position"] for r in rows),
              "the test 6 fields were not carried into the before-or-with rows")
        # The parser, on the two other answers and on a reply out of form.
        parse = code_before_or_with.parse_reply
        check(parse("ANSWER: BEFORE\nspan: it was there") == ("BEFORE", "it was there"),
              "a BEFORE reply was not parsed")
        check(parse("ANSWER: NEITHER\nspan: none")[0] == "NEITHER",
              "a NEITHER reply was not parsed")
        check(parse("I think it arose with it.")[0] == "UNCLEAR",
              "a reply out of form was not left UNCLEAR")
        code_before_or_with.tally(rows)

    print("6. The unpublished items refused without --private")
    result = subprocess.run([sys.executable, str(Path(__file__).with_name("code_catch_item.py")),
                             "--run", "no-such-run", "--items", "held-back",
                             "--coder-provider", "fake"],
                            capture_output=True, text=True)
    check(result.returncode != 0 and "--private" in (result.stdout + result.stderr),
          "code_catch_item.py did not refuse the held-back items without --private")

    if failures:
        print(f"\n{len(failures)} check(s) failed.")
        sys.exit(1)
    print("\nEvery check passed.")


if __name__ == "__main__":
    main()
