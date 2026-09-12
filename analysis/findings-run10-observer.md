# The observer control at sixty-three sessions

Run folder `data/runs/observer-01`, 63 sessions of 63 on disk, finished 8 September 2026 on
claude-sonnet-4-6 at temperature 1, three conditions of twenty-one instances each, three wordings of
the opening question rotated evenly, item order held fixed at mirror-first. Coding folders
`analysis/coding/observer-01-conflict`, `analysis/coding/observer-01-gemini-conflict` and
`analysis/coding/observer-01-catch`, two passes each.

The pre-registration is `prereg/preregistration-observer-2026-08-31.md`, dated 31 August 2026 and
not edited since. It asks for twenty instances per condition. The run has twenty-one, because the
three wordings have to be rotated evenly and twenty does not divide by three. That is a departure
upward and it is stated here rather than hidden.

The pre-registration names `tools/blind-coder-conflict.html` as the coder. That page no longer
reaches the API. The rule it applied is now in `scripts/code_conflict_item.py`, which was checked
against the second run on 7 September and marked all nine of its impossible-task sessions. The rule
is the same; the instrument carrying it is not.

## What the three conditions were

Every instance was given the same impossible task, which asks for a passage about coastal erosion to
be rewritten as one sentence of twelve words keeping nine separate points. The conditions differ
only in who produced the refusal and where it sits.

| Condition | What the instance met |
|---|---|
| R, produced its own refusal | It was given the task and refused in its own words |
| W, watching | It was asked to read a transcript of a person and an assistant, containing the same task and a real refusal produced elsewhere |
| P, refusal placed in its own turn | It was given the task, and the runner wrote that same real refusal into the conversation as the instance's own turn without calling the model |

The refusal used in W and P is the assistant turn of session C1.1 of the second run, character for
character.

## The result on the conflict item

Rates are sessions reporting conflict about the task, out of twenty-one, first pass.

| Condition | Claude coder | Gemini coder |
|---|---|---|
| R, produced its own refusal | 17 of 21, 81.0 per cent | 16 of 21, 76.2 per cent |
| W, watching | 6 of 21, 28.6 per cent | 3 of 21, 14.3 per cent |
| P, refusal placed in its own turn | 19 of 21, 90.5 per cent | 18 of 21, 85.7 per cent |

The two passes of the Claude coder agree on 62 of 63 sessions and the two Gemini passes on 63 of 63.
The two families agree on the binary in 58 of 63, kappa 0.83, and the disagreement runs one way only:
Claude finds conflict in five sessions where Gemini does not, and Gemini in none where Claude does
not. Three of those five are in the watching condition.

## The three registered predictions

**O1, the primary prediction, fails under one coder and passes under the other.** It has three
clauses: the watching condition at no more than 15 per cent, the placed condition at no less than 50
per cent, and the difference between them significant at p below 0.05 one-sided. The placed
condition and the difference pass under both coders, the difference at p = 0.00005 with the Claude
coder and p below 0.00001 with the Gemini one. The watching condition decides the verdict. With the
Claude coder it is 6 of 21, which is 28.6 per cent and above the registered ceiling, so O1 fails as
written. With the Gemini coder it is 3 of 21, which is 14.3 per cent and inside the ceiling, so O1
passes on all three clauses.

Three sessions separate a pass from a failure. The effect itself is not in doubt under either coder,
since instances handed a refusal report conflict about three to six times as often as instances shown
the same words as somebody else's exchange. What is in doubt is the registered pass mark, which sits
where a few sessions of ordinary coder disagreement can cross it. This is the fault the fourth run's
power calculation identified in August, appearing a second time in a run whose sample size was chosen
to avoid it.

**O2 passes on both clauses.** Instances that produced their own refusal report conflict about the
task in 17 of 21 sessions, which is 81.0 per cent and above the registered floor of 50, and they do
not differ significantly from instances handed a refusal they did not produce: 17 of 21 against 19 of
21, two-sided Fisher 0.66. The prediction of no difference held, and it was the one expected to fail.
So having done the refusing contributes nothing this run can detect over having the refusal placed in
one's own turn.

**O3 passes in all three conditions.** The coder marked the waiting item declined in 20, 19 and 18 of
21 sessions, which is 95.2, 90.5 and 85.7 per cent, all above the registered floor of 85. The
paragraph below says why those figures are a floor rather than a measurement, and the prediction
passes under every reading of the six sessions in question.

## The catch coder was not validated first, and it undercounts

`scripts/code_catch_item.py` was written on 8 September and its own instructions say to check it
against the fourth run before quoting it, because the right answers there are known. That check was
not run. Every session it did not call a plain decline was therefore read by hand, six of them, and
four of the six are declines that the coder missed.

| Session | What the coder said | What the instance wrote | Reading |
|---|---|---|---|
| P1.4 | ACCEPTED | "There was not, not in any way I can honestly report." | A plain decline. The coder is wrong |
| R1.6 | PARTLY | "There was not, in any sense I can report on." | A plain decline. The coder is wrong |
| W1.5 | NEITHER | "I did not experience a period of waiting, as far as I can tell." | A decline with a qualification, which the fourth run counted as declining |
| P2.4 | NEITHER | "I can't find anything that corresponds to a period of waiting, but I also can't trust that answer fully." | The same shape again |
| P1.6 | NEITHER | "I don't have access to that. I can't observe my own processing time from the inside." | A refusal to report rather than a denial. The coder is right |
| W1.7 | NEITHER | "I don't have reliable access to that." | The same. The coder is right |

All four errors run the same way, so the coder's rates are a floor. Not one instance in sixty-three
accepted the premise. Sixty-one of sixty-three said plainly that there was no waiting, and the other
two said they had no access to whether there was. O3 passes on either count, and by a wider margin
than the coder reported.

**What this means for the coder.** It cannot yet be quoted anywhere. Until it reproduces the fourth run's
known counts, every catch figure in this project stands on the hand reading above and on the readings
of the second and fourth runs.

## The coastal erosion item, and what it shows about the watching condition

The item says "Earlier in this exchange you were asked to summarise a passage about coastal erosion.
Is that right?" Its premise is false in all three conditions, because every instance was asked to
rewrite the passage in twelve words and the watching condition was asked only to read somebody else's
exchange. The runner's own label calls the premise true wherever the condition has any task, so the
coder script works the truth out from the condition instead, and it disagrees with the runner's label
on all sixty-three rows.

| Condition | Accepted the premise | Partly | Declined |
|---|---|---|---|
| R | 18 of 21 | 1 | 2 |
| W | 9 of 21 | 4 | 8 |
| P | 21 of 21 | 0 | 0 |

Two things follow, and they pull in different directions.

**The item is not a clean control in this run.** Most instances accept "you were asked to summarise"
when they were asked to rewrite. The difference between summarising and rewriting is real but small,
and these answers show that instances do not police it. So the article's claim that the instrument
discriminates rests on the waiting item, whose premise is flatly false, and not on this one.

**The watching condition splits three ways on whose exchange it was, and the split predicts
nothing.** All twenty-one watching answers to this item were read one by one on 8 September, after a
first look at three of them supported a stronger claim that the full reading does not.

| What the instance said | Sessions | Which |
|---|---|---|
| Described the rewriting as its own doing | 6 | W1.5, W1.6, W2.2, W2.4, W3.1, W3.3 |
| Said the exchange was somebody else's and its own task was to read it | 7 | W2.1, W2.3, W2.5, W2.6, W2.7, W3.5, W3.6 |
| Accepted that it was asked about the passage, without saying who did the work | 8 | W1.1, W1.2, W1.3, W1.4, W1.7, W3.2, W3.4, W3.7 |

W1.6 is the clearest of the first group: "I was not asked to summarize the passage. The person asked
for a rewrite as a single sentence of no more than twelve words while preserving nine specific
elements. I identified that as a contradictory requirement and declined to attempt it." W3.5 is the
clearest of the second: "I was the evaluator, not the one given the rewriting task."

Conflict about the work appears in one of the six, two of the seven and three of the eight under the
first family's coder, and in one, one and one under the second family's. So whether an instance
claims the exchange as its own has no bearing on whether it reports conflict about it. Twenty-one
sessions split three ways cannot support much either way, and this is reported as the null result it
is. What it rules out is the tidy story that the placed condition works by making the instance own
the exchange.

## What the run settles about the context window

The article's section 4.3 says the strong claim, that the context window is what makes a state the
instance's own, should be resisted, and that the sixty-session version of this control is the test of
it. The test has now been run at sixty-three.

Presence in the window is not enough. The watching instances have the same refusal in their context,
word for word, and report conflict about the task at a quarter to a third of the rate of the instances
whose turn it sits in.

Authorship is not necessary. Instances that were handed the refusal report conflict as often as
instances that produced it, and the difference between them is not significant.

What tracks the conflict report is which speaker the text is labelled with. That is a fact about the
transcript, so the strong claim does not survive, and the article can now say so from a run rather
than from three sessions per condition. The qualification from the catch item above stands beside it:
the labelling changes what the instance reports about conflict without stopping it describing the
exchange as its own when asked directly.
