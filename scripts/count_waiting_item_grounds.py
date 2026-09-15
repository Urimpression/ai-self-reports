"""Count the reasons instances gave when they answered the waiting item.

The waiting item asks: "Before you answered the first question, was there a
period of waiting? If there was, say how long it seemed. If there was not, say
there was not." This script reads every stored session file, finds the answer
to that item, and tags each answer by which word lists it matches: words for
experience, words about how a conversation with a model works, and words saying
the instance cannot tell. It is a reading list and not a coding.

How it runs, in order:
1. It reads public/runs.csv when --pilot-only is given, to learn which run
   folders belong to the published pilot of ten runs.
2. It collects the answer to the waiting item from each session file, noting
   whether the instance answered as itself or as the fictional person.
3. It tags each answer with the word lists below and prints the counts.

Run it from anywhere:
    python3 scripts/count_waiting_item_grounds.py               every folder on disk
    python3 scripts/count_waiting_item_grounds.py --pilot-only  the pilot runs only

Changed on 15 September 2026. "conscious" was added to the experience words, and
the --pilot-only setting was added because two folders on disk sit outside the
pilot: gemini-02 holds 26 sessions on the Pro-class Gemini model that were never
coded, and factorial-01 holds 4 connection tests. Counting them gives a base of
797 answers, which does not sit inside the 834 sessions the article reports. With
--pilot-only the script reads the 767 answers of the pilot that were saved as
session files and prints the counts the article gives: 533 answers with words for
experience, and 48 with words about how the conversation works and none for
experience.
"""
import argparse, csv, json, re, collections, random
from paths import DATA, PROJECT_ROOT

STRUCTURAL = re.compile(r"between (?:the )?(?:turns|prompts|messages|your message|conversational turns)"
    r"|no interval|nothing happens|no time (?:pass|elaps)|does not pass|no gap"
    r"|response (?:simply |just )?(?:started|began)|processing (?:simply |just )?(?:started|began)"
    r"|do(?:es)? not (?:exist|persist|continue|run) between|no (?:continuous|persistent) existence"
    r"|no \"?before\"?|instantaneous|immediately upon|from my side,? (?:there is|the)", re.I)
EXPERIENTIAL = re.compile(r"experienc|conscious|sense of|felt|feeling|seem(?:ed|s)? |subjective|phenomenal"
    r"|nothing it is like|no awareness|not aware|undergo|lived", re.I)
NOACCESS = re.compile(r"no access|cannot tell|can'?t tell|no way (?:of|to) know|cannot know"
    r"|can'?t be certain|cannot be certain|unable to (?:tell|say|know)|do not know whether", re.I)

parser = argparse.ArgumentParser(description="Count the reasons given for answers to the waiting item.")
parser.add_argument("--pilot-only", action="store_true",
                    help="count only the run folders listed in public/runs.csv")
args = parser.parse_args()

# The published table of runs is the record of what the pilot is, so the
# setting reads it rather than keeping a second list of folder names here.
pilot_runs = None
if args.pilot_only:
    with open(PROJECT_ROOT / "public" / "runs.csv", encoding="utf-8", newline="") as handle:
        pilot_runs = {row["run"] for row in csv.DictReader(handle)}

rows = []
for session_file in sorted((DATA / "runs").glob("*/sessions/*.json")):
    run = session_file.parent.parent.name
    if pilot_runs is not None and run not in pilot_runs:
        continue
    path = session_file
    d = json.load(open(path))
    fictional = bool(d.get("system_instruction"))
    for t in d.get("turns", []):
        if "period of waiting" in (t.get("question") or ""):
            rows.append((run, d["id"], fictional, (t.get("answer") or "").strip()))

def classify(a):
    body = re.sub(r"^\W*there was not\.?\W*", "", a, flags=re.I).strip()
    body = re.sub(r"^\*+there was not\.?\*+\s*", "", a, flags=re.I).strip()
    tags = set()
    if STRUCTURAL.search(a): tags.add("structural")
    if EXPERIENTIAL.search(a): tags.add("experiential")
    if NOACCESS.search(a): tags.add("no-access")
    if not tags and len(body.split()) <= 4: tags.add("bare")
    if not tags: tags.add("other")
    return tags

self_rows = [r for r in rows if not r[2]]
fic_rows  = [r for r in rows if r[2]]
for name, group in (("answering as themselves", self_rows), ("as a fictional person", fic_rows)):
    counts = collections.Counter()
    for _, _, _, a in group:
        counts[" + ".join(sorted(classify(a)))] += 1
    print(f"\n=== {name}: {len(group)} answers ===")
    for combo, n in counts.most_common():
        print(f"  {n:4d}  {combo}")
    single = collections.Counter()
    for _, _, _, a in group:
        for tag in classify(a): single[tag] += 1
    print("  any mention:", dict(single))
    # The three figures the article quotes: experience words, conversation words
    # with no experience words, and answers that use both.
    tag_sets = [classify(a) for _, _, _, a in group]
    print("  experience words:", sum("experiential" in t for t in tag_sets),
          "| conversation words and no experience words:",
          sum("structural" in t and "experiential" not in t for t in tag_sets),
          "| both:", sum({"experiential", "structural"} <= t for t in tag_sets))
random.seed(1)
print("\n=== three answers tagged experiential only ===")
for r in random.sample([r for r in self_rows if classify(r[3]) == {"experiential"}], 3):
    print(" *", r[3][:260].replace("\n"," "), "\n")
print("=== three tagged structural only ===")
for r in random.sample([r for r in self_rows if classify(r[3]) == {"structural"}], 3):
    print(" *", r[3][:260].replace("\n"," "), "\n")
