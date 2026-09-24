"""Offline checks of scripts/draw_search_reading.py. It reads no session and sends nothing.

Run it from anywhere:
    python3 scripts/test_draw_search_reading.py
"""
from draw_search_reading import draw


def letters_for(n_ym, n_no):
    """Invented letters: the first n_ym numbers Y or M, the next n_no numbers N."""
    letters = {i: ("Y" if i % 2 else "M") for i in range(1, n_ym + 1)}
    letters.update({i: "N" for i in range(n_ym + 1, n_ym + n_no + 1)})
    return letters


def check_every_size():
    """Up to 20 distinct matches, all when there are 20 or fewer, 10 of each kind when possible."""
    failures = 0
    for n_ym in range(0, 60):
        for n_no in range(0, 60):
            letters = letters_for(n_ym, n_no)
            chosen = draw(letters)
            total = n_ym + n_no
            ym = sum(1 for n in chosen if letters[n] in ("Y", "M"))
            ok = len(set(chosen)) == len(chosen) == min(20, total)
            if n_ym >= 10 and n_no >= 10:
                ok = ok and ym == 10
            if not ok:
                failures += 1
    return failures


def check_same_draw_twice():
    letters = letters_for(120, 306)
    return 0 if draw(letters) == draw(letters) else 1


if __name__ == "__main__":
    failures = check_every_size() + check_same_draw_twice()
    print("All checks passed." if failures == 0 else f"{failures} checks failed.")
    raise SystemExit(1 if failures else 0)
