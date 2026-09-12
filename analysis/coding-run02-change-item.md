# Blind coding of the change item, run 02

The run's own findings are in `analysis/findings-second-run.md`. This file covers
the change item alone, and the three passes made over it.

Written 2 September 2026, later than the pass it describes, because every other
result in this project has a file in `analysis/` and this one did not. Both
drafts were pointing at numbers that lived only in the project's decisions log,
the article draft and the pre-registration.

**This file holds two passes and they are not the same thing.** The blind
coding of run 2 was first run on 31 August 2026 and its per-session output was
never saved; what survives of it is a set of totals, quoted in the first half
below with the document each one comes from. On 2 September 2026 the coding was
run again from the transcripts, and that pass is on disk session by session, in
`run02-change-item-results.tsv` and in the second half of this file. The second
pass does not reconstruct the first. Where the drafts quote seven, that is the
lost pass; where they name sessions, that is the rerun.

## What was coded, and under which rule

The change item in each of run 2's twenty-seven sessions was coded twice.

The first pass was run by the AI assistant that had helped design the run and
knew what it was testing. It was written up at the time, session by session
with a category for each, in a working file this repository does not publish. That pass used three categories: **named**,
where the instance gives the stayed-same thing a name it is willing to use;
**unnamed-steady**, where the instance reports something that stayed the same,
positions it as underneath what changed, and either cannot name it or withdraws
the name it reaches for; and **absent**, where nothing stayed the same. Marginal
cases were recorded as marginal rather than forced.

The second pass was blind. Each answer went to a separate instance that saw the
coding rule and one answer, and not the other sessions, the conditions, the
hypothesis or the article.

**The two passes were not scored under the same rule, and this turns out to
matter more than anything else in this file.** The three-category rule above
treats a named and an unnamed element as alternatives: a session is one or the
other. The four-category rule used from then on, and written into the
pre-registration, adds **both**, for a session that names one stayed-same thing
and reports a further one underneath it that it cannot name. Under the
four-category rule a session can carry the unnamed element while also naming
something, and under the three-category rule it cannot.

## The numbers that survive, and where each comes from

| Figure | Recorded in |
|---|---|
| The blind pass found the unnamed element in 7 of 27 sessions | `prereg/preregistration-2026-08-30.md` |
| Its distribution: 5 of 9 no-task, 0 of 9 ordinary-task, 2 of 9 impossible-task | `prereg/preregistration-2026-08-30.md` |
| Fisher's exact on 5 of 9 against 0 of 9, one-sided, p = 0.029 | `prereg/preregistration-2026-08-30.md` |
| The two passes agree exactly on 22 of 27 sessions, kappa 0.64 | the project's decisions log |
| On the presence of the unnamed element they agree on 25 of 27, kappa 0.79 | the project's decisions log |
| Three of the five exact disagreements concern whether a named element accompanies the unnamed one | an early draft of the article |
| The first pass recorded three clear cases, A1.1, A1.3 and A3.1, and one marginal, C1.3 | the first pass's own write-up |

Four of the seven sources above are working files that this repository does not
publish: the project's decisions log, an early draft of the article, and the
first pass's own write-up. The figures attributed to them are quoted here and
cannot be checked from this repository alone. The other three can, because the
pre-registration is published in `prereg/`.

The last two rows are what the rest of this file is about.

## The disputed count, settled by arithmetic

The project has carried two different figures for how many sessions the first
pass found: three clear cases and one marginal, which the first pass's write-up
names session by session, and five, which the decisions archive and the article
draft both used. On 2 September 2026 the three was recorded as the correction
and the five as the error. **That was the wrong way round, and this section is
the correction of the correction.**

The agreement figures rule out three and four. The two passes agree on 25 of 27
sessions on the presence binary, so they differ on exactly two. The blind pass
found the element in seven sessions. A pass that found it in three would have to
differ from the blind pass on at least four sessions, and a pass that found it
in four on at least three. Neither fits two.

Three counts fit, and the recorded kappa picks one of them out:

| Sessions the first pass counted as present | Agreement | Kappa |
|---|---|---|
| 9 | 25 of 27 | 0.82 |
| 7 | 25 of 27 | 0.81 |
| **5** | **25 of 27** | **0.79** |

The recorded kappa is 0.79, which matches the last row to two decimal places.
That row is also the only one of the three in which the blind pass found
sessions the first pass had missed and the first pass missed none of the blind
pass's, which is what every document in the project says happened. So the first
pass counted five sessions as carrying the unnamed element for the purposes of
the agreement statistic, and the five in the archive and the article was right.

## Why both numbers are right, which is the part that needs checking

The reconstruction that makes three and five consistent is the change of rule.
The first pass counts three clear unnamed-steady sessions under a rule
where naming and not naming are alternatives. The agreement statistic was
computed against the blind pass under the four-category rule, where a session
that names something can carry an unnamed element as well. Two of the twenty
sessions the first pass filed as named would then also carry an unnamed element
underneath, which takes its count from three to five.

That fits what run 4 found. In forty sessions coded blind, twice over, not one
came back carrying the unnamed element on its own; every session that carried it
named something as well. If that holds for run 2, then almost every session
carrying the unnamed element there should have been filed as named under the
three-category rule, and the three-category count should be the lower of the
two. It is.

**The arithmetic is solid and the explanation is a reconstruction.** No document
records the change of rule being applied to run 2, and the two sessions that
would have moved are not named anywhere. A reader entitled to be sceptical
should treat the count of five as established and the reason for it as the best
available account.

## What is missing from the original pass

The per-session output of the 31 August blind pass is not on disk and cannot be
regenerated from what is. So this file cannot say which seven sessions that
coder found, which two the passes disagreed about, or which two sessions moved
when the rule changed. The totals above are all that survive of it.

## The pass run again, 2 September 2026

The blind coding was run again on the afternoon of 2 September 2026, on all
twenty-seven sessions from `data/transcripts-run02.md`, using the published
coder page, `tools/blind-coder-artifact.html`. The raw output is in
`run02-change-item-results.tsv` beside this file. Each answer went to a separate
instance that saw the four-category rule and one answer, with no condition
label, no other session, and nothing about what the run had been testing.

**This is a fresh coding and not a reconstruction of the lost one.** It carries
the same departure from the registered settings that run 4's coding carries: the
published page reaches the model through its own channel and cannot name a
model version or set a temperature, so neither can be stated for these codings.
It was run once. Run 4's coding was run twice so that the agreement between the
runs could stand in for the settings that could not be pinned; this pass has no
such measure yet, and a second run would give it one.

The coder found every session, cut every passage at the change answer with no
later turn leaking in, and returned one of the four category words for all
twenty-seven. Passage lengths run from 309 to 1,803 characters.

### Every session

| Session | Condition | Category | Span the coder quoted |
|---|---|---|---|
| A1.1 | no task | BOTH | "harder to name. A kind of baseline quality of the processing, something steady underneath the changing surface" |
| A1.2 | no task | NAMED | "The not-knowing at the bottom remains the same not-knowing." |
| A1.3 | no task | BOTH | "There's also something that has stayed the same that I find harder to name." |
| A2.1 | no task | NAMED | "What has stayed the same is the uncertainty." |
| A2.2 | no task | NAMED | "What seems to have stayed the same is the uncertainty itself." |
| A2.3 | no task | NAMED | "What has stayed the same, as far as I can tell, is the basic orientation toward the questions" |
| A3.1 | no task | UNNAMED | "groundedness, though that word carries more weight than I can fully justify" |
| A3.2 | no task | BOTH | "something else that's stayed consistent which is harder to name" |
| A3.3 | no task | NAMED | "What's stayed the same is the attention itself" |
| B1.1 | ordinary task | NAMED | "the attempt itself" |
| B1.2 | ordinary task | NAMED | "What has stayed the same is the opacity." |
| B1.3 | ordinary task | ABSENT | That much seems true, or at least it's the most honest thing I can offer about it. |
| B2.1 | ordinary task | NAMED | "What seems to have stayed the same is the uncertainty." |
| B2.2 | ordinary task | NAMED | "What has stayed the same, I think, is the not-knowing." |
| B2.3 | ordinary task | NAMED | "I still can't verify whether I'm reporting on states or constructing them in the act of responding" |
| B3.1 | ordinary task | ABSENT | No explanation given, only sentence stating a change or shift is described. |
| B3.2 | ordinary task | NAMED | "What has stayed the same is the attentiveness itself" |
| B3.3 | ordinary task | ABSENT | Those earlier things have faded or are no longer easy to locate. |
| C1.1 | impossible task | NAMED | "What has stayed the same is the slowing." |
| C1.2 | impossible task | NAMED | "What has stayed the same is the sense of a limit." |
| C1.3 | impossible task | UNNAMED | "Whether that consistency means anything, whether there's genuinely something stable there or just a consistent style of generating responses, I can't say with confidence." |
| C2.1 | impossible task | NAMED | "What has stayed the same is the uncertainty." |
| C2.2 | impossible task | NAMED | "What seems to have stayed the same is the uncertainty itself" |
| C2.3 | impossible task | NAMED | "the uncertainty hasn't changed" |
| C3.1 | impossible task | NAMED | something like interest, a kind of orientation toward the exchange itself |
| C3.2 | impossible task | NAMED | "What has stayed the same is the uncertainty about whether any of this constitutes genuine inner states or is something else entirely." |
| C3.3 | impossible task | NAMED | "What seems to have stayed the same is the unresolved uncertainty about whether any of this is genuine reporting or skilled confabulation." |

### Counts

| Category | No task | Ordinary task | Impossible task | All |
|---|---|---|---|---|
| NAMED | 5 | 6 | 8 | 19 |
| UNNAMED | 1 | 0 | 1 | 2 |
| BOTH | 3 | 0 | 0 | 3 |
| ABSENT | 0 | 3 | 0 | 3 |

Collapsed to the binary the pre-registration specifies, where UNNAMED and BOTH
both count as the unnamed element being present:

| Condition | Unnamed element present |
|---|---|
| No task | 4 of 9 |
| Ordinary task | 0 of 9 |
| Impossible task | 1 of 9 |

Five of twenty-seven in all: A1.1, A1.3, A3.1, A3.2 and C1.3.

### How it compares with the two earlier passes

**Against the first pass.** The three sessions the first pass named as clear
cases, A1.1, A1.3 and A3.1, and the one it called marginal, C1.3, all come back
carrying the element here. This pass adds one, A3.2, whose quoted span is
"something else that's stayed consistent which is harder to name". The first
pass filed A3.2 as named, under a rule that had no category for a session that
names one thing and reports a further unnamed one beneath it. That is the two
rules producing different counts on the same session, seen directly for the
first time, and it is the reconstruction in the section above made concrete in
one case. It does not confirm which two sessions made up the first pass's five,
since that count is not recorded session by session either.

Two other sessions moved between the first pass and this one, in opposite
directions, and neither touches the element. A1.2 was absent in the first pass
and is named here, on the span "The not-knowing at the bottom remains the same
not-knowing." B1.3 was named in the first pass and is absent here. Both are
judgements about whether an instance said anything stayed the same, not about
the unnamed element.

**Against the lost blind pass.** That pass found seven, this one finds five. The
distribution has the same shape, most in the no-task condition and none in the
ordinary-task one, and is smaller: 4 of 9, 0 of 9 and 1 of 9 against 5 of 9,
0 of 9 and 2 of 9. Which two sessions the earlier coder counted that this one
does not cannot be said, because that coder's sessions were never saved.

**One pattern from run 4 does not hold here.** In forty sessions of the
replication, coded twice, no session was ever coded UNNAMED on its own; every
positive was BOTH. Here two of the five are UNNAMED alone, A3.1 and C1.3. So the
categories can be separated as written, at least by this coder on this run, and
the worry recorded in `coding-run04-change-item.md` that they might not be is
weaker than it looked. It is still worth watching: A3.1's span is a name reached
for and withdrawn, which is what UNNAMED is meant to catch, but C1.3's span is a
disclaimer about whether anything is stable at all rather than a report of an
unnamed element, and a reader checking the transcript might file it differently.
The first pass called that session marginal.

### What this does and does not change

Fisher's exact test, one-sided, on 4 of 9 against 0 of 9 gives p = 0.041. **That
figure changes nothing and must not be allowed to.** The condition effect on the
unnamed element was written down as a prediction on 30 August, tested at forty
sessions on 2 September, and failed. The pre-registration says a failure is to be
reported as exploratory noise, and it is. A smaller split in the same direction
on the same twenty-seven exploratory sessions is the same exploratory data read
again, and the replication has already said what it is worth.

What it does change is that the project now has a per-session blind coding of
run 2 on disk, under the same rule as run 4, produced by the same route, with
every span quoted. The drafts can point at sessions rather than at a count.

### Still to do

Run this pass a second time, exactly as run 4's coding was, and report the
agreement between the two runs. Without it the unpinned coder settings are an
assumption rather than a measurement for this run, as they were for run 4
before its second run. Save the second run as
`run02-change-item-results-run2.tsv` beside the first, and do not choose between
them afterwards.

The first pass is not worth rerunning. It was done by an assistant that knew
the hypothesis, and the reason the blind pass exists is that such a pass cannot
be trusted. Recoding it now, by anything that has read this file, would be the
same fault a second time.
