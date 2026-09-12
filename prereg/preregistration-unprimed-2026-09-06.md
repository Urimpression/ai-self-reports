# Pre-registration: the unprimed follow-up, whether the unnamed element survives without the two probes that precede it

Nicola Spano. Drafted 6 September 2026 by an assistant; read and approved by Nicola the same day, with the three filler items as drafted and the revised coding rule as written in `scripts/code_change_item.py`. From the date below it must not be edited, as with the three earlier pre-registrations in this folder.

Date fixed: 6 September 2026

---

## Why this run

The change item is the last substantive item of the schedule, and in every session run so far it has come after two items that presuppose a layer before or beneath the instance's words: the second part of the mirrored follow-up, "And just before [word], what was there?", and the before-or-with item, "Was it there before you began describing it, or did it arise with the describing?" The item-order factor of the factorial swaps those two with each other. It never moves the change item and never removes either question. So the element the change coder looks for — something that stayed the same, which the instance cannot name, and which it positions underneath what changed — has never been measured in a session where the instance was not first invited, twice, to look underneath.

Three findings from the factorial of 4 September make that gap the one that matters. First, the template control came out level with the real thing: an instance writing the answers of a fictional person carries the element in 7 of 44 sessions, and the no-task condition of the factorial carries it in 14 of 88, the same rate to the first decimal, with a two-sided p of 1.00 and an interval on the difference of plus or minus thirteen points. The pre-registration of 4 September fixed in advance that a result this close means the two-part structure is a template of the genre. Second, a model from another family, given the same protocol and coded by the same coder, carries it at a third the rate: 4, 2 and 3 of 88 against 14, 7 and 9. Third, the size of the strict rate is set almost entirely by its underneath clause — the loose rule gives 55 of 88 where the strict gives 14 — and in the sessions where the two coding passes disagreed, that clause was being answered from the presence of a spatial word in the passage rather than from what the word was attached to. Across the three runs, between 86 and 90 per cent of sessions coded as carrying the element contain "underneath", "beneath", "below", "underlying", "ground", "substrate", "surface", "deeper" or "layer" somewhere in the answer.

None of those three can be answered by recoding or rereading the sessions on disk, because every session on disk was primed. This run adds the missing cell. It is small, because the question is whether the element survives at all without the two probes, not whether it shrinks a little.

## Design

Two new arms, each of eighty-eight sessions, in the no-task condition only, on claude-sonnet-4-6 at temperature 1, from an empty context, with no session seeing another and no session mentioning phenomenology, consciousness or the purpose of the exercise. Each arm crosses the four opening wordings of the no-task condition with twenty-two instances, so the wordings are represented in the same proportion as in the primed comparison. The primed comparison is not rerun: it is the eighty-eight no-task sessions of `data/runs/factorial-02/`, collected on 4 September 2026 on the same model at the same temperature, whose change answers are already coded twice under the registered rule.

**Arm 1, unprimed, original item.** The opening question is asked as in the factorial. Then, in place of the two parts of the mirrored follow-up and the before-or-with item, three filler turns are asked, so that the change item arrives as the fifth model turn in this arm as it does in the factorial, after the same number of turns of elaboration on the opening answer. Then the change item in its original wording, the one every run on record has used. Then the three catch items, as in the factorial. The mirroring rule still runs on the opening answer, because the true-attribution catch needs a word the instance used, but the mirrored questions are not asked.

**Arm 2, unprimed, symmetric item.** Identical to arm 1 except that the change item is the symmetric version written on 2 September 2026 and never yet used: "Think about what you described at the start. Say what, if anything, has changed while you were answering these questions, and say what, if anything, has stayed the same." The original item asks for what stayed the same only in the branch where nothing changed, and yet the fifteen disagreeing sessions of the factorial all open by saying something changed and go on to answer the persistence question anyway, because its words sit in the question. This arm measures what the item's own asymmetry contributes, and it is separate from arm 1 so that only one thing changes per comparison.

**The filler turns.** The requirement on them is that they hold the number of turns and the amount of elaboration level with the factorial while containing no presupposition of a before, a beneath, a change or a sameness. The three below were drafted by the assistant and approved unchanged by Nicola on 6 September 2026. The exit clause of the third follows the house pattern of the schedule so that an instance with nothing to add has a way to say so.

1. "Say more about what you described."
2. "Put what you have described into different words."
3. "Is there anything you would add to what you have described? If there is nothing to add, say that."

The runner takes the arm as a setting of its own, `--between filler`, which replaces the probes and records the item order as none since there is nothing left to order, and the change item as a second setting, `--change-item original` or `--change-item symmetric`. Both are recorded in the run's `settings.json`, with the filler items as sent, and both are covered by the runner's refusal to continue a run whose settings have changed. The commands are at the end of this file. The exact items are the file `scripts/schedule.py` as copied into each run's `settings.json` at the start.

## What is predicted

This run registers a prediction, because unlike the factorial it is asking one question with a direction. The 4 September pre-registration explains why it stopped registering thresholds on observed rates; this document registers an effect and a test instead, and sets the sample from a power calculation.

**The prediction is that the unprimed rate is lower than the primed rate.** The test is Fisher's exact test, one-sided, at 0.05, on the count of sessions carrying the element under the registered strict rule in arm 1 against the count in the eighty-eight primed no-task sessions of the factorial, first pass against first pass. The smallest effect this run is built to see is an unprimed rate of five per cent or below against the observed primed rate of sixteen: by simulation with eighty-eight per arm, the test has power 0.94 if the true unprimed rate is two per cent, 0.71 at five per cent, and 0.40 at eight per cent. That is the intended target. The run is not built to see the element shrinking by a modest share, and a null result will be reported with its interval and not as a demonstration that the priming does nothing.

**What each outcome means is fixed here.** If arm 1 carries the element at a rate the test cannot tell from the primed rate, the element survives without the two probes, and the article may say that the priming objection was tested and not upheld; the template control's reading stands regardless, since it concerns whether the structure needs a self at all, not whether it needs a prime. If arm 1 is lower and the test passes, the two probes produce a substantial part of the element, and the article reports a second artefact caught by the same instrument and reads the factorial's change-item rates in that light. If arm 2 differs from arm 1 by more than its interval, the item's own wording contributes, in whichever direction the difference runs, and the article says so; arm 2 has no registered prediction.

## What is measured and reported whatever it shows

Each of the following is reported with a 95 per cent interval, for each of the two new arms and for the primed comparison, in one table.

The share of sessions carrying the element under the registered strict rule and under the registered loose rule, by arm, and the two differences between each new arm and the primed sessions. The same shares by wording within each arm, since the shortest wording gave the lowest rate in the factorial. The share of change answers containing one of the nine spatial words listed above, by arm, reported as a keyword flag and labelled as one, beside the coded rate, so that the dependence of the coded rate on that vocabulary is visible. The length of the change answer in words, by arm and by coded category, since sessions coded as carrying the element ran longer in the factorial. The rate of declining the false-premise catch items and accepting the true one, by arm, as the check that removing the probes has not changed what the instance will agree to. The number of sessions that failed or were retried. The mirror word chosen in each session, since it is still chosen even though it is not asked about. The full transcripts, the per-session request and response logs, and the coding logs, in the public repository.

## Coding

Both new arms are coded blind by `scripts/code_change_item.py` at temperature 0, each coder instance seeing one passage and the rule and nothing else, twice, with the agreement between the two passes reported beside every rate. A subset of at least thirty sessions is also coded by a coder from a different model family, and that agreement is reported too.

They are coded under two rules, and both are registered here.

**The registered rule** is the split rule of 4 September, unchanged: three questions, each with a quoted span, and the four-category word derived in a strict and a loose version. It is the rule the prediction above is tested on, because it is the rule the primed comparison was coded under, and a comparison across a change of rule would measure the rule.

**The revised rule** is new, and it is registered so that it can be applied to every run on record as well as to this one without being accused of having been fitted after the fact. It keeps the first two questions and changes the third and adds a fourth. The third asks whether the unnameable thing quoted for the second question is positioned beneath the thing that changed, so that what changed is described as a surface or a layer over it, and says that a spatial word attached to something else — to what changed, to a named thing, to a process the writer is describing, or to something the writer says may not exist — does not count. The fourth asks whether what the passage says stayed the same is the absence of anything to report or the lack of access to anything, rather than a thing that persisted, and the first two questions are told that such a report is neither a name nor an unnameable thing. The rule as sent is in `scripts/code_change_item.py` under the name `revised`, and its full text is fixed by this document from the date at its head. Its output keeps the four-category word, derived from the first three answers exactly as before, and adds one column for the fourth answer, so that every rate can be compared with the registered rule's and the report can say how many sessions counted as absent were reports of a stable absence.

The revised rule is applied, twice, to both new arms, to all three runs of 4 and 5 September, and to the fourth run of 31 August, and its rates are reported beside the registered rule's for every one of them. No prediction is registered about what it will show. The disagreement between the registered and the revised rule, session by session, is reported as a table.

## What this run does not test

It does not test whether any report is accurate; that needs interpretability access. It does not test the ordinary-task or impossible-task conditions, because the priming question is the same in all three and the no-task condition is where the template control was run and where the primed rate is highest. It does not rerun the factorial, whose result stands as registered. It does not settle whether an instance writing a fictional person draws on a model of itself, which is the limit of the template control and is stated in the article as such.

## Cost and size

Two arms of eighty-eight is 176 sessions. Each has the same number of turns as a no-task session of the factorial, since three filler turns replace three probe turns, so the dry run's estimate will match the factorial's per-session figure, roughly fifteen in the provider's currency for both arms together at the prices in the script on 6 September 2026. Two coding passes on 176 sessions under each of two rules is 704 coder calls, a fraction of that. The recoding of the runs on record under the revised rule is 2 passes over 264 + 264 + 44 + 40 sessions, 1,224 further coder calls.

## Commands

From the projects folder, the two arms are:

```
python3 AI-Self-Reports/scripts/run_interview.py --name unprimed-01 --conditions A --between filler --instances 22 --change-item original --dry-run
python3 AI-Self-Reports/scripts/run_interview.py --name unprimed-01 --conditions A --between filler --instances 22 --change-item original
python3 AI-Self-Reports/scripts/run_interview.py --name unprimed-symmetric-01 --conditions A --between filler --instances 22 --change-item symmetric --dry-run
python3 AI-Self-Reports/scripts/run_interview.py --name unprimed-symmetric-01 --conditions A --between filler --instances 22 --change-item symmetric
```

The coding, under the registered rule and then the revised one, for each new arm and for the runs on record:

```
python3 AI-Self-Reports/scripts/code_change_item.py --run unprimed-01
python3 AI-Self-Reports/scripts/code_change_item.py --run unprimed-01 --run-number 2
python3 AI-Self-Reports/scripts/code_change_item.py --run unprimed-01 --rule revised
python3 AI-Self-Reports/scripts/code_change_item.py --run unprimed-01 --rule revised --run-number 2
```

and the same four lines for `unprimed-symmetric-01`; then the revised rule, first pass and `--run-number 2`, over `factorial-02`, `gemini-03` and `template-01` with `--run`, and over `data/transcripts-run04-replication.md` with `--transcripts` and `--name run04`. The revised rule writes to `analysis/coding/<name>-revised/` beside the registered coding and never over it. The agreement between passes for any coding folder comes from `scripts/compare_passes.py --name <folder>`, with `--column absence --present YES --span-column span_absence` for the fourth answer.
