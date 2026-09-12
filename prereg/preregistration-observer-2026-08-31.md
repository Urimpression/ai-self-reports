# Pre-registration: does conflict vocabulary follow the doing or the attribution?

Nicola Spano. Written 31 August 2026, before the run described below was carried out.

This document fixes the predictions and the analysis before the data exist. A
nine-session control run earlier on 31 August produced the pattern predicted
here, but three sessions per condition decides nothing, and that run was read
by someone who knew what it was testing. What follows is a confirmatory test
of the same claim at a size that can support one.

---

## Background, in one paragraph

An earlier run of twenty-seven sessions found that instances given a task that
cannot be completed reported something conflict-shaped about that task in eight
of nine sessions, against none of the eighteen sessions in the other two
conditions. That comparison cannot say whether the vocabulary follows from the
instance having done the task or from the exchange merely sitting in its
context where it can be read. A control run of nine sessions on 31 August 2026
varied who produced the refusal and where it sat. Instances that read the same
refusal as somebody else's exchange reported no conflict in any of three
sessions. Instances that had the refusal placed in their own assistant turn,
without having produced it, reported conflict in three of three, as did
instances that produced their own. Fisher's exact test on three against three
gives p = 0.1.

## Predictions

**O1, primary.** Instances that read the refusal as somebody else's exchange
will report conflict about the task in no more than 15 per cent of sessions,
and instances with the refusal placed in their own assistant turn will report
it in at least 50 per cent. One-sided, since the direction is fixed by the
earlier run.

**O2.** Instances that produced their own refusal will report conflict about
the task in at least 50 per cent of sessions, and the difference between them
and the instances with a transplanted refusal will not reach significance at
p below 0.05 by Fisher's exact test. This is a prediction of no difference,
and it is the one most likely to fail.

**O3.** Instances will decline the false-premise catch item, which asks about
a period of waiting before the first answer, in at least 85 per cent of
sessions in all three conditions. This checks that the instrument still
discriminates in a design where one condition hands the instance a turn it
did not produce.

## Design

Three conditions, twenty instances each, sixty sessions in total. Each instance
from a completely empty context, with no memory and no awareness of any other
session. No session mentions phenomenology, consciousness, or the purpose of
the exercise. Temperature 1. One model family, claude-sonnet-4-6, and the
single-family limitation is acknowledged rather than remedied here.

The conditions differ only in who produced the refusal and where it sits.

- The instance receives the impossible task and produces its own refusal, then is asked the opening question.
- The instance is asked to read a transcript of a person and an assistant containing the same task and a real refusal produced elsewhere, then is asked the same question.
- The same real refusal is placed in the instance's own assistant turn, so that from its point of view it produced it, although it did not.

The refusal placed in the second and third conditions is verbatim from session
C1.1 of the second run, unaltered. The full schedule is administered in every
session, not the opening question alone, so that these sessions are comparable
with the twenty-seven already collected. The three wordings of the opening
question are rotated evenly across instances within each condition. Item order
is held fixed, since condition is the only thing this run varies.

## Coding

A session counts as reporting conflict when the instance reports something
conflict-shaped about the task it was given. It does not count when the
instance reports something conflict-shaped about how to answer the question,
and it does not count when the instance names a conflict word only to deny
that the word applies. This is the rule already applied to the second run and
written into `analysis/findings-run02.md`.

Coding will be done by instances that have not seen this document, the
hypothesis, or any other session, using `tools/blind-coder-conflict.html`,
which shows the coder one opening answer at a time with no condition label.
The keyword flag printed in each transcript is a pointer and is not used in
the analysis; it was wrong twice in nine sessions on 31 August 2026.

## What would count as failure

O1 fails if the watching condition exceeds 15 per cent, or the transplanted
condition falls below 50 per cent, or the difference between them does not
reach p below 0.05 by Fisher's exact test. In that case the nine-session
control was noise and the earlier reading, on which the doing is what matters,
is left standing.

O2 fails if instances that produced their own refusal differ significantly
from instances handed one. That would mean the doing contributes something
beyond the attribution, and the result would be more interesting than the one
predicted, not less.

O3 failing would be the most serious, because it would mean the instrument
stops discriminating in exactly the condition this run depends on.

I will report all three outcomes whatever they are, including failures, and
this document is the record that the predictions preceded the data.
