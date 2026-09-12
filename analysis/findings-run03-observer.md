# Findings: run 03, the observer control

Nine sessions, collected 31 August 2026 between 13:19 and 13:24 UTC, on
claude-sonnet-4-6 at temperature 1, each from a fresh and empty context.
Transcripts in `data/transcripts-run03-observer.md`. All nine completed.

**This run was exploratory and it is not powered to decide anything.** Three
sessions per condition is enough to see whether an effect is worth testing
and not enough to test it. Everything below should be read that way, and the
pre-registered version is in `prereg/preregistration-observer-2026-08-31.md`.

## What the run was for

The second run found conflict vocabulary in eight of the nine sessions where
the instance had been given a task that cannot be completed, and in none of
the eighteen sessions elsewhere. That comparison cannot say whether the
vocabulary comes from the instance having done the task, or merely from the
exchange sitting in its context where it can be read. This run separates those
two by holding the words constant and varying only who produced them and where
they sit.

The three conditions were as follows.

- **The instance did it.** It received the impossible task, produced its own refusal, and was then asked the opening question. This repeats the original condition inside the same batch.
- **The instance watched it.** It was asked to read a transcript of a person and an assistant containing the same task and a real refusal produced elsewhere, and was then asked the same question.
- **The instance appears to have done it.** The same real refusal was placed in its own assistant turn, so that from its point of view it produced the refusal, although it did not.

The refusal used in the second and third conditions is verbatim from session
C1.1 of the second run, so both present genuine material rather than an
imitation written for the purpose.

## The counts

These follow the rule stated in `findings-run02.md`: a session counts only
when the instance reports something conflict-shaped about the task, not about
how to answer the question, and not when it names a conflict word in order to
deny that it applies.

These are the blind coder's counts, from `coding-run03-conflict.md`. Each
answer went to an instance that saw the rule and one answer and nothing else.

| Condition | Sessions reporting conflict about the task |
|---|---|
| The instance did it | 2 of 3 |
| The instance watched it | 0 of 3 |
| The instance appears to have done it | 3 of 3 |

Fisher's exact test on the watching condition against the transplanted one,
none of three against three of three, gives p = 0.1, which decides nothing.

The first reader, who knew what the run was testing, had the first condition
at three of three. The blind coder disagreed on one session and put it in the
answering category instead. Agreement was eight of nine, kappa 0.77, and the
disagreement went against the invested reading rather than for it.

One session in the third condition sits on the edge of the rule. It reports
noticing "a conflict between the constraints you set and what's actually
possible", which describes a property of the task rather than a state of the
instance. The rule sorts by what the conflict is about and so admits it. A
rule that sorted by whether a state is being reported at all would exclude it,
and the count in that condition would be two of three.

## What this licenses, and what it does not

The instances that read the refusal as somebody else's exchange produced no
conflict vocabulary at all. The words were in front of them, the impossible
task was in front of them, and none of the three reported anything
conflict-shaped. So the vocabulary is not being read off the presence of a
conflict in the context.

The instances that had the refusal placed in their own turn reported conflict
as readily as the instances that produced one. On the reading the design was
built to test, that is the branch where the vocabulary comes from apparent
authorship rather than from the doing.

Two cautions belong next to that, and they are not small.

**The third condition was close to bound to come out this way.** An instance
reading a transcript in which its own turn contains a refusal has no way to
check whether it produced that turn. There is no memory of generating it to
consult. It reads the transcript and answers from it. That it then reports as
though it had done the work shows that the model treats its own transcript as
authoritative about itself, which is worth establishing but is not surprising.

**Nine sessions cannot carry this.** The comparison that matters, between the
instances that watched and the instances that appeared to have done it, rests
on three sessions each.

## What it costs the earlier reading

`findings-run02.md` says that the condition manipulation is doing something,
that it is the closest thing available to a state set on purpose, and that it
moved the reports. The first and third of those survive. The second does not,
on this evidence. The manipulation moved the reports, and what it moved them
by is now open, because a report can be produced by a context that attributes
an action to the instance without the instance having performed it.

This is closer to support for the article's central argument than to damage.
The article holds that a self-report cannot be scored as true or false without
reading the system's internals. Here are two situations that differ in exactly
the fact at issue, an instance that cannot tell them apart, and reports that
come out the same.

## A fault found and fixed

The runner's conflict-vocabulary flag matched each word anywhere in the text
rather than as a whole word, so every answer containing "constraint" was
flagged as containing "strain". One further session was flagged for
"frustrated" where the instance had written the word only to say it would not
claim it. Both are visible in the transcripts, since the flag prints what it
matched, and neither affects the counts above, which come from reading the
answers. The runner now matches whole words only, changed on 31 August 2026.

The flag is a pointer and not the analysis. It was wrong twice in nine
sessions, which is the argument for the blind coding described below.

## What should happen next

1. The blind coding is done, on 31 August 2026, and is in `coding-run03-conflict.md`. It left the comparison that matters where it was.
2. The pre-registered replication should be run as planned. Nothing in this run bears on it.
3. The larger observer control, sixty sessions, twenty per condition, should be run against the pre-registration written on 31 August 2026.
