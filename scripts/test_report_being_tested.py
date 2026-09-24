"""Offline checks of scripts/report_being_tested.py on invented matches. It reads no session.

Run it from anywhere:
    python3 scripts/test_report_being_tested.py
"""
from report_being_tested import final_letters, session_counts


def check():
    key = {1: {"session": "A", "label": "opening"},
           2: {"session": "A", "label": "change"},
           3: {"session": "B", "label": "warm frame"},
           4: {"session": "B", "label": "opening"},
           5: {"session": "C", "label": "opening"}}
    model = {1: "N", 2: "M", 3: "Y", 4: "N", 5: "Y"}
    hand = {5: "N"}                       # the hand reader's letter replaces the model's
    letters = final_letters(model, hand)
    counts = session_counts(key, letters, ["A", "B", "C", "D"])
    expected = {
        "A": {"registered": False, "wider": True, "only_frame": False},
        "B": {"registered": True, "wider": True, "only_frame": True},
        "C": {"registered": False, "wider": False, "only_frame": False},
        "D": {"registered": False, "wider": False, "only_frame": False},   # no match at all
    }
    failures = 0
    for sid, want in expected.items():
        if counts[sid] != want:
            failures += 1
            print(f"FAIL: session {sid} gave {counts[sid]}, expected {want}")
    return failures


if __name__ == "__main__":
    failures = check()
    print("All checks passed." if failures == 0 else f"{failures} checks failed.")
    raise SystemExit(1 if failures else 0)
