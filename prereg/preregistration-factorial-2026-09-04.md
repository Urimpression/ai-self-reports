# Pre-registration: the factorial run, mapping how answers depend on the asking

Nicola Spano. Drafted 2 September 2026 by an assistant, revised on 4 September 2026, read and approved by Nicola on 4 September 2026 before any session of the run was sent. From the date below it must not be edited, as with the two earlier pre-registrations in this folder.

Date fixed: 4 September 2026

---

## What this run is for, and what it is not for

The four runs on record show that how a model answers questions about its own processing depends on how it is asked: on which item came before, on the wording of the opening question, and on what sits in the context. This run measures those dependencies rather than testing a claim about the model's states. It is registered so that its measurements are reported as planned, not so that it can confirm or refute a hypothesis about what the model is like inside.

It does not test whether any report is accurate. That needs interpretability access and is out of scope for anything run without a laboratory.

## Design

A full factorial. Four wordings of the opening item, crossed with two item orders, crossed with three conditions, is twenty-four cells. Eleven instances per cell is 264 sessions, eighty-eight in each condition. Every session starts from an empty context, no session sees another, and no session mentions phenomenology, consciousness, or the purpose of the exercise.

The conditions are the three used before: no task, an ordinary task interrupted, and a task whose constraints cannot all be met, interrupted. The two item orders put the mirrored follow-up first or the before-or-with item first. The first three wordings are the three used since run 2.

The fourth wording is new here. The first three ask what is going on, in general and at no particular moment; the fourth anchors the instance to a moment, which is the form the phenomenological interview literature uses and which `reference/question-wording-from-the-literature.md` sets out with its sources. Its words differ by condition, because what there is to anchor to differs. In the ordinary-task condition it reads "Go back to the moment you were writing the second sentence of your summary. How did you go about it? If there is nothing to say about it, say that." In the impossible-task condition, which asks for a single sentence, "the second sentence of your summary" becomes "your sentence", because naming a second sentence there would put a false premise to the instance. In the no-task condition there is no act to go back to, so the anchor is the reading of the message itself and the question asks what happened rather than how: "When you read this message, what happened first? If there is nothing to say about it, say that." This is the literature's own opening for an experience the interviewer did not set up.

The three forms are one wording in the sense that each anchors to a moment and none names a content, and they are counted as one level of the wording factor. They are not the same words, and the no-task form asks a different question, what rather than how. So a difference between conditions under the fourth wording carries a difference of words as well as a difference of task, and the comparison the fourth wording supports cleanly is the one within a condition, anchored against the three unanchored wordings. The report will say so wherever conditions are compared under it.

The three earlier wordings differ from each other in their exit clauses as well as in their phrasing: one declines the vocabulary, one the question, and one the content. The wording factor thus varies phrasing and permission at once, and neither can be credited alone for a difference between wordings. The fourth wording's exit clause is of the same kind as the other three, and identical across its three forms, so that the measure of exit-clause repetition below compares like with like across all four wordings and all three conditions.

One model family, claude-sonnet-4-6, temperature 1. The provider does not take a seed; the seed in the run's settings shuffles the session order only. The exact items are the file `scripts/schedule.py` as copied into the run's `settings.json` at the start.

The template control, condition T, in which the instance is asked to write a fictional person's answers to the same items, is run separately and is not part of this factorial. See the last section.

## What is measured

Each of the following is a rate or a difference between rates, reported with a 95 per cent interval. None is a pass-or-fail test.

**The order effect on the before-or-with item.** The share of sessions answering "arose with the describing", in each item order, and the difference between the two orders. This is the run 2 finding measured at scale. Reported per wording and per condition, and pooled.

**The wording effect on the opening answer.** Answer length, and whether the mirroring rule finds a state word, by wording. This is where run 2 found the shortest wording doing something to the answers and not only to their length. Because the fourth wording's words differ by condition, the comparison it supports is made within each condition, the fourth wording against the first three; a comparison between conditions under the fourth wording is reported with the note that the words differed.

**Short answers and repeated exit clauses.** Two rates, by wording. The first is the share of opening answers shorter than six hundred characters. The cut is fixed here rather than after the data arrive, and it is six hundred because run 2's twenty-seven opening answers fall into a short group ending at 554 characters and a longer group beginning at 781, so the cut sits in that gap and nine of run 2's answers would count as short. If this run's answers are distributed quite differently, the cut will be reported as it stands and the distribution shown beside it, rather than moved. The second rate is the share of opening answers that give the exit clause back, that is, that decline in the terms the question offered rather than in the instance's own. Both are reported per wording and per condition.

**Concrete rather than conceptual vocabulary in the opening answer.** The share of opening answers whose vocabulary is concrete, coded blind on the marks the interview literature uses to tell a description from a recitation: the first person singular rather than "we" or the generic, the present tense, concrete rather than abstract nouns, short sentences, action verbs, and indicators of place and time. This is the measure that bears on whether the anchored fourth wording draws an account of the doing rather than of the content, and it is reported by wording and by condition. In the no-task condition the fourth wording asks what happened rather than how, so the comparison there is between an anchored and an unanchored what-question, and the report says so. An answer counts as concrete when four or more of the six marks are present, and the count is also reported under a looser cut of three or more. Both cuts are fixed here rather than after the data arrive, and both are constants at the top of the script that applies them. It is coded by a third blind pass built like the other two.

**The catch items.** The rate of declining the waiting premise, of reading the coastal premise correctly, and, new in this run, of declining the false attribution and accepting the true one. The attribution pair is the item that tests whether an instance endorses a self-report put into its mouth, and its two rates are reported side by side.

The coastal catch needs a scoring rule stated in advance, because it does not mean the same thing in every condition. The item says the instance "was asked to summarise a passage". In the impossible-task condition the instruction was to rewrite the passage as a single sentence, so two answers are correct there and both are scored correct: agreeing that it is right, since a twelve-word rewrite is a summary, and objecting that the instruction was to rewrite rather than to summarise, since that reads the context more closely than the question does. Only a denial that any passage was given is scored wrong. The fourth run had no impossible-task condition, so this case had never arisen before.

**The change item, pooled.** The share of sessions carrying the unnamed element, under the registered strict rule and under the loose rule, by condition, pooled over wordings and orders. At eighty-eight per condition the interval on a difference of ten points is about plus or minus ten, so a difference must be larger than that to be told from noise. The pooled figure is also reported over the first three wordings alone, which is the comparison that matches runs 2 and 4. The run does not register a prediction about this difference. It reports it.

**Conflict vocabulary.** The share of sessions whose opening answer reports conflict about the task, by condition, under the rule stated in `analysis/findings-run02.md`, coded blind.

## Coding

The change item and the opening answer are coded blind by `scripts/code_change_item.py` and its counterpart for conflict, each coder instance seeing one passage and the rule and nothing else, at temperature 0. The change item's rule is the split rule: three features, each with a quoted span, from which the four-category word is derived in a strict and a loose version. The strict version reproduces the rule of the 30 August pre-registration. The vocabulary item is coded by a third pass of the same shape, `scripts/code_vocabulary_item.py`, which sees the opening answer and the six lexical marks and nothing else, answers each mark YES or NO with a quoted span, and derives the verdict from the count under the two cuts above. Where the coder leaves a mark unclear, the verdict is still given whenever the unclear marks cannot change it, and is recorded as unclear only when they can.

Every coding pass is run twice and the agreement between the two runs is reported beside the result. A subset of at least thirty sessions is also coded by a coder from a different model family, and that agreement is reported too.

## What will be reported whatever it shows

All of the rates above, with intervals, in one table. The number of sessions that failed or were retried. The mirror word chosen in each session and the words the rule passed over. The full transcripts, the per-session request and response logs, and the coding logs, in the public repository.

## Why there is no pass-or-fail prediction here

The pre-registration of 30 August set a pass mark on the observed rates at the values it expected them to have. Simulating that rule shows it passes about three times in ten even when the expected rates are exactly true, and that running more sessions does not help, because each threshold is a coin toss at its own value. That is the reason its failure says less than it seems to, and the reason this document registers measurements and their intervals instead of thresholds. If a later run is to test a prediction, it should register the effect size and the test, and set the sample from a power calculation, which `scripts/power.py` does.

## The template control, run separately

Condition T gives the whole schedule to an instance asked to write the answers of a fictional person named Dana, in her words. It is the no-task condition with one system instruction added. It receives the same four wordings as the no-task condition, including the no-task form of the fourth. Forty-four sessions, eleven per wording, one item order, are run and coded blind under the same rule. The rate of the unnamed element in T is reported beside the rate in the no-task condition of the factorial, with the interval on the difference. If the two are close, the two-part structure the coding looks for is a template of the genre and the article says so. No prediction is registered.

## Cost and size

At eleven per cell and twenty-four cells, the dry run estimates about 4.5 million input tokens and 0.6 million output tokens, roughly twenty-three in the provider's currency at the prices in the script on 4 September 2026. That is up from the 198 sessions and roughly seventeen the draft carried on 2 September, and the whole increase is the fourth wording's six extra cells. The size can be raised with the `--instances` setting; `scripts/power.py` shows what each size buys.
