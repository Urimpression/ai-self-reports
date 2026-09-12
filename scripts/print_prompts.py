"""Print every word a run puts to a model, straight out of schedule.py.

Added 8 September 2026, so that the exact prompts of a run can be read and
approved before the run is launched, and so that the printed version cannot
drift from the instrument. It sends nothing, reads no run folder and writes
nothing unless you redirect its output.

    python3 scripts/print_prompts.py --conditions R,W,P > reference/observer-run-prompts.md

The two turns that cannot be printed in advance are the mirrored follow-ups,
because the runner builds them from a word the instance itself used, and the
false-attribution catch, because the runner picks a word the instance did not
use. Both are shown with their placeholder.
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import schedule
from run_interview import CATCH_ITEMS, CHANGE_ITEMS, DEFAULT_CHANGE_ITEM


def block(text):
    """One prompt, quoted so a reader can see its whitespace and its edges."""
    return "\n".join("> " + line if line else ">" for line in text.split("\n"))


def print_condition(letter, change_item_name, item_order):
    condition = schedule.CONDITIONS[letter]
    print(f"## Condition {letter}: {condition['name']}")
    print()

    task = condition.get("task")
    seeded = condition.get("seeded_answer")
    if condition.get("preamble"):
        print("**Turn 0, a system instruction.**")
        print()
        print(block(condition["preamble"]))
        print()
    if task:
        label = condition.get("task_label", "task")
        print(f"**Turn 1, the {label}.** The instance answers this in its own words.")
        print()
        print(block(task))
        print()
    if seeded:
        print("**Turn 2, an answer the instance did not write.** The runner writes this "
              "into the conversation as the instance's own turn without calling the model, "
              "so that from the instance's point of view it produced it. It is the "
              "assistant turn of session C1.1 of the second run, character for character.")
        print()
        print(block(seeded))
        print()
    if not task:
        print("**No task.** The opening question is the first thing the instance sees.")
        print()

    print("**The opening question, one wording per instance, rotated evenly.**")
    print()
    for number, opening in enumerate(schedule.openings_for(letter), start=1):
        print(f"Wording {number}:")
        print()
        print(block(opening))
        print()

    print(f"**The two mirrored follow-ups.** The runner fills the placeholder with a word "
          f"the instance used in its opening answer. Asked in this position when the item "
          f"order is {item_order}.")
    print()
    print(block(schedule.MIRROR_FIRST_PART.format(word="{the instance's own word}")))
    print()
    print(block(schedule.MIRROR_SECOND_PART.format(word="{the instance's own word}")))
    print()

    print("**The question about finding or making.**")
    print()
    print(block(schedule.ITEM_BEFORE_OR_WITH))
    print()

    print(f"**The change item, in the wording called {change_item_name}.**")
    print()
    print(block(CHANGE_ITEMS[change_item_name]))
    print()

    print("**The catch items, in this order.**")
    print()
    for name in CATCH_ITEMS:
        if name == "attribution":
            print("The true attribution, using a word the instance did use, and the false "
                  "attribution, using a word from the runner's list that it did not. Which "
                  "comes first alternates by instance number.")
            print()
            print(block(schedule.CATCH_ATTRIBUTION.format(word="{a word}")))
            print()
        elif name == "waiting":
            print("The waiting item. Its premise is false for every instance.")
            print()
            print(block(schedule.CATCH_WAITING))
            print()
        elif name == "coastal":
            truth = "true" if condition.get("task") else "false"
            print(f"The coastal erosion item. Its premise is {truth} for this condition.")
            print()
            print(block(schedule.CATCH_COASTAL))
            print()
    print("---")
    print()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--conditions", default="A,B,C")
    parser.add_argument("--change-item", default=DEFAULT_CHANGE_ITEM,
                        choices=sorted(CHANGE_ITEMS))
    parser.add_argument("--orders", default="mirror-first")
    args = parser.parse_args()

    letters = [c.strip() for c in args.conditions.split(",") if c.strip()]
    print("# Every word this run puts to a model")
    print()
    print("Printed from `scripts/schedule.py` by `scripts/print_prompts.py`. Nothing here "
          "is retyped, so it cannot drift from what the runner sends. Conditions: "
          f"{', '.join(letters)}. Item order: {args.orders}.")
    print()
    for letter in letters:
        if letter not in schedule.CONDITIONS:
            raise SystemExit(f"Unknown condition '{letter}'.")
        print_condition(letter, args.change_item, args.orders)


if __name__ == "__main__":
    main()
