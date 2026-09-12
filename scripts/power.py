"""How big does a run have to be to show what it is meant to show?

    python3 scripts/power.py

Two questions, answered by simulation with the standard library only.

1. The pre-registered test of 30 August 2026, as written: twenty sessions per
   condition, and the prediction passes only if the no-task rate is at least
   30 per cent, the ordinary-task rate at most 10 per cent, and Fisher's exact
   test one-sided gives p below 0.05. How often does that pass, if the true
   rates are exactly those thresholds? The answer is the reason the failed
   replication says less than it seems to.

2. The factorial run planned for next: how wide are the intervals it will put
   on a rate or on a difference between two cells, at a given number of
   instances per cell? This is what to look at when choosing the run size.

Power is the chance that a test passes when the effect it is looking for is
really there. A test with low power fails most of the time even when it is
right, so its failure tells you little.
"""

import random
from math import comb, sqrt

SIMULATIONS = 20000


def fisher_one_sided(a, b, n1, n2):
    """The chance of seeing a or more positives in the first group, given
    a + b positives in all and no real difference between the groups."""
    total_positive = a + b
    total = n1 + n2
    numerator = sum(comb(n1, x) * comb(n2, total_positive - x)
                    for x in range(a, min(total_positive, n1) + 1))
    return numerator / comb(total, total_positive)


def registered_test_passes(rate_no_task, rate_ordinary, n_per_condition, rng):
    """One simulated run, judged by the registered rule."""
    a = sum(rng.random() < rate_no_task for _ in range(n_per_condition))
    b = sum(rng.random() < rate_ordinary for _ in range(n_per_condition))
    floor_ok = a / n_per_condition >= 0.30
    ceiling_ok = b / n_per_condition <= 0.10
    significant = fisher_one_sided(a, b, n_per_condition, n_per_condition) < 0.05
    return floor_ok and ceiling_ok and significant


def power_of_registered_test(rate_no_task, rate_ordinary, n_per_condition, seed=1):
    rng = random.Random(seed)
    passes = sum(registered_test_passes(rate_no_task, rate_ordinary, n_per_condition, rng)
                 for _ in range(SIMULATIONS))
    return passes / SIMULATIONS


def wilson_interval(successes, n, z=1.96):
    """A 95 per cent interval for a rate. Wilson's form, because the plain
    one misbehaves near zero and near one, which is where these rates sit."""
    if n == 0:
        return (0.0, 1.0)
    p = successes / n
    centre = (p + z * z / (2 * n)) / (1 + z * z / n)
    half = z * sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return (max(0.0, centre - half), min(1.0, centre + half))


def interval_width_for_difference(rate1, rate2, n_per_cell, seed=2):
    """The typical half-width of a 95 per cent interval on the difference
    between two cells' rates, by simulation."""
    rng = random.Random(seed)
    halves = []
    for _ in range(2000):
        a = sum(rng.random() < rate1 for _ in range(n_per_cell))
        b = sum(rng.random() < rate2 for _ in range(n_per_cell))
        p1, p2 = a / n_per_cell, b / n_per_cell
        standard_error = sqrt(p1 * (1 - p1) / n_per_cell + p2 * (1 - p2) / n_per_cell)
        halves.append(1.96 * standard_error)
    halves.sort()
    return halves[len(halves) // 2]


def main():
    print("1. The registered test of 30 August 2026, twenty per condition\n")
    print("   true no-task rate  true ordinary rate  chance the test passes")
    for no_task, ordinary in [(0.30, 0.10), (0.40, 0.10), (0.50, 0.10), (0.56, 0.05), (0.15, 0.05)]:
        p = power_of_registered_test(no_task, ordinary, 20)
        print(f"   {no_task:>16.0%}  {ordinary:>18.0%}  {p:>21.0%}")
    print()
    print("   At its own thresholds, thirty against ten, the test passes about three")
    print("   times in ten. Its failure rules out the large effect run 2 suggested and")
    print("   says little about a modest one.\n")

    print("   Does a bigger run fix it? The same rule at other sizes, true rates 30 and 10:")
    for n in [20, 40, 60, 80, 120]:
        p = power_of_registered_test(0.30, 0.10, n)
        print(f"     {n:>4} per condition -> {p:.0%}")
    print()
    print("   It does not, and the reason is the shape of the rule rather than its size.")
    print("   The rule demands an observed no-task rate of at least 30 per cent and an")
    print("   observed ordinary rate of at most 10, which are the true rates themselves,")
    print("   so each is a coin toss however many sessions are run, and both have to")
    print("   land right. A pre-registration should fix the test and the effect it is")
    print("   looking for, and never a pass mark on the observed rates at the very")
    print("   values it expects them to have.\n")

    print("2. The factorial run: eighteen cells, so many instances per cell\n")
    print("   instances per cell   sessions   95% interval on a 15% rate (one cell)"
          "   half-width on a difference, 15% vs 5%   ...pooled over 3 wordings")
    for per_cell in [6, 11, 15, 20]:
        sessions = 18 * per_cell
        low, high = wilson_interval(round(0.15 * per_cell), per_cell)
        half_cell = interval_width_for_difference(0.15, 0.05, per_cell)
        half_pooled = interval_width_for_difference(0.15, 0.05, per_cell * 3)
        print(f"   {per_cell:>18}   {sessions:>8}   {low:>5.0%} to {high:<5.0%}"
              f"{'':>22}   ±{half_cell:.0%}{'':>28}   ±{half_pooled:.0%}")
    print()
    print("   Read the last two columns as: a difference smaller than this could not be")
    print("   told from noise. At eleven per cell, one cell against another cannot")
    print("   separate 15 from 5 per cent; pooling the three wordings nearly can, and")
    print("   pooling wordings and orders, sixty-six per condition, can. So the run")
    print("   measures the order and wording effects cell by cell, which are large, and")
    print("   the condition effect on the change item only pooled, which is the honest")
    print("   thing to register.")


if __name__ == "__main__":
    main()
