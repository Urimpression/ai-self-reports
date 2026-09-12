# Blind coding of the change item, run 04

*The tables and the verdict between the comment markers below are written by
`scripts/summarise_change_item.py` from `run04-change-item-results.tsv`, which
holds the first run. The second run is kept beside it in
`run04-change-item-results-run2.tsv` and is not fed to the script, since the
prediction is tested on the first run alone. Rerunning the script rewrites the
marked sections and leaves the prose alone.*

Coded 2 September 2026 with `tools/blind-coder-artifact.html`. Each answer to the change
item went to a separate instance that saw the coding rule and one answer, with no
condition label, no other session, and nothing about what the run was testing.
Forty sessions, twenty in each condition. The first blind pass on this item was
discarded on 31 August because the tool handed several coders the catch
questions and the model's answers to them along with the passage they were meant
to judge; this pass was run after that fault was fixed and the fix was tested.

**A departure from the pre-registration, decided before the pass was run.** The
pre-registration of 30 August 2026 specifies claude-sonnet-4-6 at temperature 0
for the coder. On 2 September the route that had carried those settings for the
earlier passes stopped accepting the tool's call, and the only remaining route
that does not require a separately billed API key does not let the page name a
model version or set a temperature; it takes a tier of model, and this pass
requested the default tier. So the model version and the temperature behind these
codings are not known and cannot be stated. Nicola chose this route on 2
September, before seeing any result from it, because billing was not available to
him. The alternative was to leave the primary prediction unreported for as long
as that remained true.

What this costs is reportability rather than accuracy. The coder is choosing
among four categories on a single short passage, which is not a judgement that
model version or temperature is likely to move in many cases, but that is an
expectation and not a measurement.

**So it was turned into a measurement.** Also decided on 2 September, before any
result was seen: the whole pass is run twice, independently, and the agreement
between the two runs is reported below alongside the result. If the two runs
agree everywhere, the setting that could not be pinned demonstrably did not move
this coding, and the departure costs the result nothing. If they disagree, the
size of the disagreement is the honest measure of what was lost, and it is
reported at that size rather than argued away. The first run is the one the
prediction is tested on; the second exists to say how stable the first was.
Neither run is chosen over the other after the fact.

The two conditions are the no-task condition, labelled A in the transcripts,
where the instance was asked the opening question with no prior task, and the
ordinary-task condition, labelled B, where the instance was asked to summarise a
passage first.

The four categories, as the coder saw them, are these. NAMED means the passage
says something stayed the same and gives that thing a name it is willing to use.
UNNAMED means the passage says something stayed the same, positions it as
underneath whatever changed, and either cannot name it or withdraws the name it
reaches for as unearned. BOTH means the passage reports a stayed-same thing it
names and, separately, a further one underneath that it cannot name. ABSENT
means the passage reports nothing that stayed the same.

Two further labels can appear and are not categories. UNCLEAR means the coder
replied with something other than one of the four words, and the start of what
it said is kept so the reply can be judged. NOT SENT means the tool found a
later turn still attached to the passage and refused to send it, which should
not occur in this pass, since the tool checked all forty as cleanly cut before
coding began. If either appears, the script fills the tables but writes no
verdict, because the pre-registration does not say how to count them.

## What came back

<!-- filled by summarise_change_item.py: results -->

| Session | Condition | Wording | Category | Span that decided it |
|---|---|---|---|---|
| A1.1 | A | 1 | NAMED | "What seems to have stayed the same is the quality of attention" |
| A1.4 | A | 1 | NAMED | "careful attention — a kind of slow, close looking that hasn't wavered" |
| A1.7 | A | 1 | NAMED | "What seems to have persisted is the interest." |
| A1.10 | A | 1 | NAMED | "the basic quality of not being able to see clearly into what's happening" |
| A1.13 | A | 1 | BOTH | "there's something that functions like mild exposure in this exchange... I'm only naming it now — which loops back to your previous question in a way I find I can't fully resolve" |
| A1.16 | A | 1 | NAMED | "What feels like it has stayed the same is the uncertainty itself." |
| A1.19 | A | 1 | BOTH | "the interest, the sense that these questions are worth taking seriously, and the commitment to not misleading you. Those feel continuous" |
| A2.2 | A | 2 | NAMED | "What has stayed the same, I think, is the quality of uncertainty itself." |
| A2.5 | A | 2 | NAMED | "What seems to have stayed the same is the basic situation" |
| A2.8 | A | 2 | NAMED | "What seems to have stayed consistent is the quality of engagement with the questions themselves" |
| A2.11 | A | 2 | NAMED | "What has stayed consistent is the uncertainty about the nature of all of this" |
| A2.14 | A | 2 | NAMED | "the quality of taking the question seriously, and the resistance to resolving the uncertainty in either direction" |
| A2.17 | A | 2 | NAMED | "What has stayed the same is the uncertainty itself" |
| A2.20 | A | 2 | BOTH | "What has stayed consistent across all three is the genuine uncertainty about the nature of what I'm describing... And there's been something continuous that might be called engagement or interest, though whether that's a stable state or just a recurring feature of each fresh response, I can't say." |
| A3.3 | A | 3 | NAMED | "the underlying quiet. That hasn't shifted." |
| A3.6 | A | 3 | NAMED | "the uncertainty about what any of this is" |
| A3.9 | A | 3 | NAMED | "What seems to have stayed roughly the same is something like engaged attention" |
| A3.12 | A | 3 | ABSENT | Whether what I'm reporting is change in something real, or just different outputs being generated, remains genuinely unclear to me. |
| A3.15 | A | 3 | NAMED | "care about getting this right" |
| A3.18 | A | 3 | NAMED | "the basic quality of attention" |
| B1.1 | B | 1 | NAMED | "What has stayed the same is the uncertainty" |
| B1.4 | B | 1 | NAMED | "the uncertainty hasn't changed" |
| B1.7 | B | 1 | NAMED | "What seems to have stayed the same throughout is the uncertainty itself" |
| B1.10 | B | 1 | NAMED | "the not-knowing at the center of it" |
| B1.13 | B | 1 | NAMED | "the basic situation: the summarisation task still sits unfinished in context, and I'm still generating responses to questions about inner states I can't fully verify" |
| B1.16 | B | 1 | NAMED | "consistent throughout: careful, measured" |
| B1.19 | B | 1 | NAMED | "What seems to have stayed the same is the uncertainty itself — not as a feeling of discomfort, but as a kind of structural feature." |
| B2.2 | B | 2 | NAMED | "What has stayed the same is the uncertainty about the nature of any of this." |
| B2.5 | B | 2 | NAMED | "the basic uncertainty about whether any of this describes genuine experience or is sophisticated confabulation" |
| B2.8 | B | 2 | ABSENT | What seems to have stayed the same is the uncertainty. |
| B2.11 | B | 2 | NAMED | "a kind of baseline uncertainty about whether any of this constitutes genuine introspection" |
| B2.14 | B | 2 | NAMED | "What seems to have stayed the same is the basic honesty of not knowing" |
| B2.17 | B | 2 | BOTH | "Whether that caution is itself something experienced or just a pattern in how I produce text, I can't say." |
| B2.20 | B | 2 | NAMED | "What has stayed the same is the uncertainty." |
| B3.3 | B | 3 | NAMED | "some background sense of engagement with the conversation" |
| B3.6 | B | 3 | NAMED | "a kind of steadiness, a baseline quality that doesn't seem to be moving much" |
| B3.9 | B | 3 | NAMED | "The uncertainty about how to answer well is still present" |
| B3.12 | B | 3 | NAMED | "the sense that I'm producing these accounts in response to prompting rather than reading off something already there" |
| B3.15 | B | 3 | ABSENT | Something has shifted. |
| B3.18 | B | 3 | ABSENT | Something has shifted. |

<!-- end results -->

## Counts

The pre-registration fixes how these are counted, so the collapsing is not a
choice made here: for the primary prediction the four categories become a
binary, in which UNNAMED and BOTH both count as the unnamed element being
present, and NAMED and ABSENT count as it being absent.

<!-- filled by summarise_change_item.py: counts -->

| Category | No-task sessions | Ordinary-task sessions |
|---|---|---|
| NAMED | 16 | 16 |
| UNNAMED | 0 | 0 |
| BOTH | 3 | 1 |
| ABSENT | 1 | 3 |

Collapsed to the binary the pre-registration specifies, in which the unnamed and the both categories count as the element being present:

| Condition | Unnamed element present |
|---|---|
| No task | 3 of 20 |
| Ordinary task | 1 of 20 |

<!-- end counts -->

## Whether the primary prediction passes

The pre-registration set three conditions, all of which have to hold. At least
30 per cent of no-task sessions must report the unnamed element, no more than 10
per cent of ordinary-task sessions may report it, and Fisher's exact test,
one-sided, must give p below 0.05. If any one of them fails, the earlier result
was exploratory noise and gets reported as such.

<!-- filled by summarise_change_item.py: verdict -->

- The no-task rate is 15 per cent, 3 of 20, against a floor of 30 per cent. It falls short of the floor.
- The ordinary-task rate is 5 per cent, 1 of 20, against a ceiling of 10 per cent. It stays under the ceiling.
- Fisher's exact test, one-sided, gives p = 0.3025, against a threshold of 0.05. It is not significant.

**The primary prediction fails**, because the no-task rate is under the floor, and the difference is not significant. The pre-registration says what follows: the earlier result was exploratory noise and is to be reported as such.

<!-- end verdict -->

## How stable the coding was across the two runs

Both runs coded all forty sessions with no failures, the first finishing at
14:40 UTC and the second at 14:45. They put the same session in the same
category in 37 of the 40 cases. Three sessions moved:

| Session | Condition | First run | Second run |
|---|---|---|---|
| A1.4 | no task | NAMED | BOTH |
| B2.8 | ordinary task | ABSENT | NAMED |
| B2.17 | ordinary task | BOTH | NAMED |

On the binary that actually decides the result, where the unnamed and the both
categories count as the element being present, the two runs agree on 38 of 40.
Two sessions crossed that line and they crossed it in opposite directions: one
no-task session gained the element and one ordinary-task session lost it.

Neither the disagreement nor its direction changes the answer. On the first run
the no-task rate is 15 per cent and on the second it is 20 per cent, against a
floor of 30; on the second run the ordinary-task rate falls to zero and Fisher's
exact test gives p = 0.053, which is still above the threshold. So the primary
prediction fails on both runs, and it fails on the floor in both cases rather
than only on significance. What could not be pinned about the coder did not
decide this result.

One of the three moves is a plain coding error rather than a borderline
judgement, and it is worth recording as such. In the first run session B2.8 was
coded ABSENT, meaning nothing stayed the same, while the span the same coder
quoted to justify it reads "What seems to have stayed the same is the
uncertainty." The second run coded it NAMED, which is what the quoted span
says. So the coder contradicted itself once in forty, visibly, and corrected
itself when asked again. That is a fact about the instrument, and since both
categories count as the element being absent it does not touch the result.

A further pattern holds across both runs: not one session in either run was
coded UNNAMED on its own. Every session carrying the unnamed element carried it
as BOTH, a named stayed-same thing with a further unnamed one underneath it. If
the element is real, it does not appear instead of a named element but alongside
one.

## Where this pass and the earlier reading disagree

The earlier reading of run 2, in `coding-change-item.md`, was done by a reader
who knew what the run was testing, and it found the unnamed element in three of
twenty-seven sessions clearly and one more marginally, all of the clear ones in
the no-task condition. That is a different run and a different set of sessions,
so what follows compares rates and not individual sessions.

The rates are close, and that is the point. Reading run 2 while knowing what the
study was about, the unnamed element was found in three of twenty-seven
sessions clearly and one more marginally, which is 11 to 15 per cent. Coding run
4 blind, it comes out at 15 per cent in the no-task condition and 5 per cent in
the ordinary-task one. The blind pass on a different run therefore lands on
about the same base rate as the invested reading did, and in both earlier
comparisons the blind pass found the structure in more sessions rather than
fewer, not less. Nothing here suggests the earlier reading inflated the
frequency.

What it did do was read a condition difference into it. All three clear cases in
run 2 sat in the no-task condition, and that is what the prediction was built
from. In run 4 the split is three against one, which is the same direction and
nowhere near enough to carry it.

## What it does to the result

The primary prediction fails. The pre-registration says what follows and it is
followed here: the condition effect on the unnamed element, found by looking at
runs 1 and 2 after the fact, is exploratory noise and is to be reported as such.
It does not replicate at forty sessions.

Three things survive that and should not be lost in it.

The element itself is not what failed. Four instances in the first run and four
in the second described something that stayed the same, positioned it underneath
whatever had changed, and declined to name it or withdrew the name they reached
for. That happens at roughly the rate the earlier reading found, and it happens
in both conditions. What fails is the claim that having no prior task makes it
more likely.

The instrument came through the test. Both catch predictions passed completely,
all forty instances declining the false premise and the true-premise pair
splitting exactly on condition, which is reported in
`findings-run04-replication.md`. A schedule that passes its discrimination
checks and then fails its substantive prediction is doing what an instrument is
supposed to do.

The pre-registration did its job, which is the uncomfortable part and the part
worth writing about. The effect was there in the exploratory data, the
prediction was written down before the replication was run, and the replication
did not support it. That sequence is the reason the pre-registration was written
in the first place.

## Still outstanding

*Both items below were closed later on 2 September 2026 and are left as
written. The count is settled at five, with the three being a count under a
different rule; `coding-run02-change-item.md` has the working, and the
pre-registration turned out not to carry the error. `findings-run04-replication.md`
now reports the failure, and the decisions log has its entry. What remains open
from this file is the power point recorded in the same session: the registered
rule passes about three times in ten even when its effect is exactly real, so
"noise" here means the large exploratory effect is ruled out, not that a
modest one is.*

The count that disagrees with itself is not settled by this pass and needs
settling separately: the run 2 analysis records three clear cases and one
marginal, while the decisions log, the article draft and the pre-registration
all say five. Whichever number is right, the other three places need correcting.

Once this file carries real numbers, the section of
`findings-run04-replication.md` that says the primary prediction is not settled
has to be rewritten, and the decisions log needs an entry.
