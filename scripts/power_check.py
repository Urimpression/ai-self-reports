"""An exact check on the power figures that `power.py` produces by simulation.

    python3 scripts/power_check.py

Written 3 September 2026, because the decisions log recorded that the power
figures came from a simulation and should be checked by a second method before
they went into a draft.

`power.py` answers its first question by drawing twenty thousand imaginary runs
and counting how many of them the registered rule passes. That is a good answer
but an approximate one: run it with a different seed and the figure moves by a
percentage point or so. The rule can also be evaluated exactly, because there
are only twenty-one possible counts in each condition and so only four hundred
and forty-one possible runs. This script walks all of them, works out how likely
each one is, and adds up the probability of the ones the rule passes.

If the exact figure and the simulated figure agree to within the simulation's
own noise, both are believable and the number can go into a draft. If they
disagree, one of the two is wrong and the disagreement says so before a reader
finds it.

Nothing here sends anything anywhere and nothing is written to disk.
"""

from math import comb

# `power.py` holds the rule and the Fisher calculation. Importing them rather
# than copying them means this script checks that code, not a second version of
# it that could drift away from what the runs actually used.
from power import fisher_one_sided, power_of_registered_test

REGISTERED_FLOOR = 0.30      # the no-task rate the pre-registration demanded
REGISTERED_CEILING = 0.10    # the ordinary-task rate it allowed at most
SIGNIFICANCE = 0.05


def binomial_probability(k, n, rate):
    """The chance of exactly k positives in n independent sessions."""
    return comb(n, k) * rate ** k * (1 - rate) ** (n - k)


def exact_power_of_registered_test(rate_no_task, rate_ordinary, n_per_condition):
    """The chance the registered rule passes, worked out by enumeration.

    Every possible run is a pair of counts: how many of the no-task sessions
    carried the element, and how many of the ordinary-task ones did. The two
    conditions are independent, so the chance of a particular pair is the
    product of the two binomial probabilities. Add up the pairs the rule
    passes and you have the power, with no sampling and no seed.
    """
    total = 0.0
    for a in range(n_per_condition + 1):
        probability_a = binomial_probability(a, n_per_condition, rate_no_task)
        if a / n_per_condition < REGISTERED_FLOOR:
            continue  # the floor already fails, whatever the other condition does
        for b in range(n_per_condition + 1):
            if b / n_per_condition > REGISTERED_CEILING:
                continue
            if fisher_one_sided(a, b, n_per_condition, n_per_condition) >= SIGNIFICANCE:
                continue
            total += probability_a * binomial_probability(b, n_per_condition, rate_ordinary)
    return total


def check_fisher_against_a_hand_worked_case():
    """One case worked out by hand, to check the Fisher function itself.

    Take two groups of two sessions with two positives in all. Under the null
    the two positives are spread over the four sessions in comb(4, 2) = 6
    equally likely ways. Both landing in the first group happens in exactly one
    of those, so the one-sided p for a = 2 is 1/6.
    """
    expected = 1 / 6
    got = fisher_one_sided(2, 0, 2, 2)
    return abs(got - expected) < 1e-12, got, expected


def main():
    ok, got, expected = check_fisher_against_a_hand_worked_case()
    print("Fisher's exact test, checked against a case worked out by hand")
    print(f"  two of two against none of two: {got:.6f}, should be {expected:.6f}"
          f"  {'ok' if ok else 'WRONG'}\n")

    print("The registered test of 30 August 2026, twenty sessions per condition\n")
    print("  true no-task  true ordinary   exact     by simulation   difference")
    rows = [(0.30, 0.10), (0.40, 0.10), (0.50, 0.10), (0.56, 0.05), (0.15, 0.05)]
    worst = 0.0
    for no_task, ordinary in rows:
        exact = exact_power_of_registered_test(no_task, ordinary, 20)
        simulated = power_of_registered_test(no_task, ordinary, 20)
        gap = abs(exact - simulated)
        worst = max(worst, gap)
        print(f"  {no_task:>11.0%}  {ordinary:>13.0%}   {exact:>6.1%}   {simulated:>13.1%}"
              f"   {gap:>10.1%}")

    print()
    # Twenty thousand draws put a rough limit of about 0.7 of a percentage point
    # on how far a simulated proportion near 0.3 should stray, so anything under
    # one point is the simulation's own noise and not a disagreement.
    print(f"  Largest difference: {worst:.1%}.")
    if worst < 0.01:
        print("  The two methods agree to within the simulation's own noise, so the")
        print("  figure quoted in the drafts, that the registered rule passes about")
        print("  three times in ten at its own thresholds, rests on two methods now.")
    else:
        print("  The two methods disagree by more than the simulation's noise should")
        print("  allow. Do not quote either figure until this is understood.")


if __name__ == "__main__":
    main()
