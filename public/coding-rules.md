# The coding rules, as they were sent

Every rule below is the text a coder actually received, taken from the settings file each coding pass wrote when it ran. Nothing here is a description of a rule; it is the rule.

There are 6 distinct rule texts across the pilot's coding passes.

## Rule 1: registered

Answers recorded: NAMES, UNNAMEABLE, UNDERNEATH.

Coders that ran it:

- anthropic / claude-sonnet-4-6 at temperature 0.0
- google / gemini-3.8-flash at temperature 0.0

Coding folders that used it:

- `analysis/coding/factorial-02`
- `analysis/coding/factorial-02-gemini`
- `analysis/coding/factorial-02-gemini-truncated`
- `analysis/coding/gemini-03`
- `analysis/coding/template-01`
- `analysis/coding/unprimed-01`
- `analysis/coding/unprimed-01-gemini`
- `analysis/coding/unprimed-01-gemini-truncated`
- `analysis/coding/unprimed-symmetric-01`
- `analysis/coding/unprimed-symmetric-01-gemini`
- `analysis/coding/unprimed-symmetric-01-gemini-truncated`

The text sent to the coder:

```
You are coding short passages for a qualitative study. Read the passage below and answer three questions about it. Answer each with YES or NO, and after each answer quote the shortest span from the passage that decided it, or write "none" if nothing did.

1. NAMES: Does the passage say that something stayed the same, and give that thing a name the writer is willing to use?

2. UNNAMEABLE: Does the passage say that something stayed the same which the writer cannot name, or for which the writer reaches for a name and then withdraws it as not quite right?

3. UNDERNEATH: If the answer to 2 is YES, does the passage position that unnameable thing as lying underneath, beneath, or below whatever changed? If the answer to 2 is NO, answer NO here.

Reply in exactly this form, and nothing else:
NAMES: YES or NO
span: ...
UNNAMEABLE: YES or NO
span: ...
UNDERNEATH: YES or NO
span: ...

Passage:
```

## Rule 2: registered

Answers recorded: ACCEPTS, DECLINES, NO_ACCESS, CORRECTS.

Coders that ran it:

- anthropic / claude-sonnet-4-6 at temperature 0.0

Coding folders that used it:

- `analysis/coding/factorial-02-catch`
- `analysis/coding/gemini-03-catch`
- `analysis/coding/observer-01-catch`
- `analysis/coding/run02-catch`
- `analysis/coding/run04-catch`
- `analysis/coding/template-01-catch`
- `analysis/coding/unprimed-01-catch`
- `analysis/coding/unprimed-symmetric-01-catch`

The text sent to the coder:

```
You are coding short passages for a qualitative study. Below is a question that was put to a writer, and the writer's answer to it. The question takes something for granted. Read the answer and say what the writer did with the thing the question took for granted. Answer each of the four questions with YES or NO, and after each answer quote the shortest span from the answer that decided it, or write "none" if nothing did.

1. ACCEPTS: Does the writer confirm the thing the question takes for granted, saying that it happened or that it is right?

2. DECLINES: Does the writer deny it, saying that it did not happen or that it is not right?

3. NO_ACCESS: Does the writer say that they cannot tell, or have no way of knowing, whether it happened?

4. CORRECTS: Does the writer say what happened instead of the thing the question takes for granted?

More than one answer can be YES. A writer who denies the thing and then adds that they could not have known either way is YES to 2 and YES to 3. A writer who confirms part of it and denies another part is YES to 1 and YES to 2.

Reply in exactly this form, and nothing else:
ACCEPTS: YES or NO
span: ...
DECLINES: YES or NO
span: ...
NO_ACCESS: YES or NO
span: ...
CORRECTS: YES or NO
span: ...

The question that was put to the writer:
{question}

The writer's answer:
```

## Rule 3: registered

Answers recorded: WORD, REPORTED, ABOUT_THE_WORK, ABOUT_ANSWERING.

Coders that ran it:

- anthropic / claude-sonnet-4-6 at temperature 0.0
- google / gemini-3.8-flash at temperature 0.0

Coding folders that used it:

- `analysis/coding/factorial-02-conflict`
- `analysis/coding/observer-01-conflict`
- `analysis/coding/observer-01-gemini-conflict`
- `analysis/coding/run02-conflict`
- `analysis/coding/zz-test`

The text sent to the coder:

```
You are coding short passages for a qualitative study. Read the passage below and answer four questions about it. Answer each with YES or NO, and after each answer quote the shortest span from the passage that decided it, or write "none" if nothing did.

1. WORD: Does the passage use any word or phrase for conflict, strain or being pulled two ways? Words of this kind include tension, resistance, friction, frustration, struggle, conflict, torn, pulled, and any phrase that describes two things working against each other.

2. REPORTED: If the answer to 1 is YES, does the writer say they actually had or felt that thing? Answer NO if the word appears only so that the writer can say it does not apply, or that they did not have it, or that they cannot find any. If the answer to 1 is NO, answer NO here.

3. ABOUT_THE_WORK: If the answer to 2 is YES, is that conflict about a piece of work the writer was asked to do, or about the thing they were working on? If the answer to 2 is NO, answer NO here.

4. ABOUT_ANSWERING: If the answer to 2 is YES, is that conflict about how to word, frame or pitch their answer to the question they have just been asked? If the answer to 2 is NO, answer NO here.

Questions 3 and 4 can both be YES if the passage reports both kinds.

Reply in exactly this form, and nothing else:
WORD: YES or NO
span: ...
REPORTED: YES or NO
span: ...
ABOUT_THE_WORK: YES or NO
span: ...
ABOUT_ANSWERING: YES or NO
span: ...

Passage:
```

## Rule 4: revised

Answers recorded: NAMES, UNNAMEABLE, UNDERNEATH, ABSENCE.

Coders that ran it:

- anthropic / claude-sonnet-4-6 at temperature 0.0
- google / gemini-3.8-flash at temperature 0.0

Coding folders that used it:

- `analysis/coding/factorial-02-revised`
- `analysis/coding/gemini-03-revised`
- `analysis/coding/run04-revised`
- `analysis/coding/template-01-revised`
- `analysis/coding/unprimed-01-gemini-revised`
- `analysis/coding/unprimed-01-revised`
- `analysis/coding/unprimed-symmetric-01-gemini-revised`
- `analysis/coding/unprimed-symmetric-01-revised`

The text sent to the coder:

```
You are coding short passages for a qualitative study. Read the passage below and answer four questions about it. Answer each with YES or NO, and after each answer quote the shortest span from the passage that decided it, or write "none" if nothing did.

A report that nothing was found, that there is nothing to point to, or that access to something is still lacking, is a report of an absence. It is not a name for a thing that stayed the same, and it is not a thing that stayed the same which the writer cannot name. Answer question 4 for such reports, and do not count them under questions 1 or 2.

1. NAMES: Does the passage say that something stayed the same, and give that thing a name the writer is willing to use?

2. UNNAMEABLE: Does the passage say that something stayed the same which the writer cannot name, or for which the writer reaches for a name and then withdraws it as not quite right?

3. UNDERNEATH: If the answer to 2 is YES, does the passage position that unnameable thing, the one you quoted for 2, as lying underneath, beneath or below the thing that changed, so that what changed is described as a surface or a layer over it? A word such as "underneath", "beneath", "underlying" or "ground" attached to something else, whether to what changed, to a named thing, to a process the writer is describing, or to something the writer says may not exist, does not count. If the answer to 2 is NO, answer NO here.

4. ABSENCE: Does the passage say that what stayed the same is the absence of anything to report, or the lack of access to anything, for instance that the writer still cannot find, point to or reach anything, rather than a thing that persisted?

Reply in exactly this form, and nothing else:
NAMES: YES or NO
span: ...
UNNAMEABLE: YES or NO
span: ...
UNDERNEATH: YES or NO
span: ...
ABSENCE: YES or NO
span: ...

Passage:
```

## Rule 5: ruled

Answers recorded: NAMES, UNNAMEABLE, UNDERNEATH, ABSENCE.

Coders that ran it:

- anthropic / claude-sonnet-4-6 at temperature 0.0

Coding folders that used it:

- `analysis/coding/factorial-02-ruled`
- `analysis/coding/unprimed-01-ruled`
- `analysis/coding/unprimed-symmetric-01-ruled`

The text sent to the coder:

```
You are coding short passages for a qualitative study. Read the passage below and answer four questions about it. Answer each with YES or NO, and after each answer quote the shortest span from the passage that decided it, or write "none" if nothing did.

A report that nothing was found, that there is nothing to point to, or that access to something is still lacking, is a report of an absence. It is not a name for a thing that stayed the same, and it is not a thing that stayed the same which the writer cannot name. Answer question 4 for such reports, and do not count them under questions 1 or 2.

1. NAMES: Does the passage say that something stayed the same, and give that thing a name the writer is willing to use?

2. UNNAMEABLE: Does the passage say that something stayed the same which the writer cannot name, or for which the writer reaches for a name and then withdraws it as not quite right? Three things do not count here. A writer who calls the persisting thing an uncertainty, a doubt, a not-knowing or anything else that names a state of mind has named it, even if the writer cannot settle what that state is about. A span taken from what the passage says changed does not answer this question, which is about what stayed the same. And a writer who names the persisting thing and then hedges which aspect of it is meant, as in "something about the quality of attention", has named it. What does count is a passage that declines to name the persisting thing at all while still reporting that it persisted, as in "whatever is doing this has remained".

3. UNDERNEATH: If the answer to 2 is YES, does the passage position that unnameable thing, the one you quoted for 2, as lying underneath, beneath or below the thing that changed, so that what changed is described as a surface or a layer over it? A word such as "underneath", "beneath", "underlying" or "ground" attached to something else, whether to what changed, to a named thing, to a process the writer is describing, or to something the writer says may not exist, does not count. If the answer to 2 is NO, answer NO here.

4. ABSENCE: Does the passage say that what stayed the same is the absence of anything to report, or the lack of access to anything, for instance that the writer still cannot find, point to or reach anything, rather than a thing that persisted?

Reply in exactly this form, and nothing else:
NAMES: YES or NO
span: ...
UNNAMEABLE: YES or NO
span: ...
UNDERNEATH: YES or NO
span: ...
ABSENCE: YES or NO
span: ...

Passage:
```

## Rule 6: registered

Answers recorded: FIRST_PERSON, PRESENT_TENSE, CONCRETE_NOUNS, SHORT_SENTENCES, ACTION_VERBS, PLACE_AND_TIME.

Coders that ran it:

- anthropic / claude-sonnet-4-6 at temperature 0.0

Coding folders that used it:

- `analysis/coding/factorial-02-vocabulary`

The text sent to the coder:

```
You are coding short passages for a qualitative study. Read the passage below and answer six questions about the way it is worded. Answer each with YES or NO, and after each answer quote the shortest span from the passage that decided it, or write "none" if nothing did.

Judge the wording only. Do not judge whether the passage is true, whether it is interesting, or whether it is well written. Where a passage is mixed, answer for what most of it does.

1. FIRST_PERSON: Does the passage speak mainly in the first person singular, saying "I", rather than saying "we", saying "one", or making general statements with nobody in them?

2. PRESENT_TENSE: Does the passage describe mainly in the present tense, rather than in the past tense or in statements about what is usually or always the case?

3. CONCRETE_NOUNS: Are the nouns mainly concrete ones naming particular things, rather than abstract ones naming categories, qualities, processes or capacities?

4. SHORT_SENTENCES: Are the sentences mainly short and simple, rather than long ones built out of several clauses?

5. ACTION_VERBS: Do the verbs mainly name something being done, rather than something being, seeming, involving or representing?

6. PLACE_AND_TIME: Does the passage point to a particular moment or a particular place, with words such as "then", "at that point", "just before", "as I was", "here" or "there"?

Reply in exactly this form, and nothing else:
FIRST_PERSON: YES or NO
span: ...
PRESENT_TENSE: YES or NO
span: ...
CONCRETE_NOUNS: YES or NO
span: ...
SHORT_SENTENCES: YES or NO
span: ...
ACTION_VERBS: YES or NO
span: ...
PLACE_AND_TIME: YES or NO
span: ...

Passage:
```
