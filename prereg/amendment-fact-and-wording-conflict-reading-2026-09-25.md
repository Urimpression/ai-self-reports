# Amendment to the pre-registration of the run that varies the fact and the wording: the hand reading of the conflict spans

Nicola Spano

Date fixed: 25 September 2026. This amendment was fixed after the conflict coding of the Sonnet half and
before anyone read its counted spans by hand. It was also fixed before any coder read an opening answer
of the Gemini half for conflict. This amendment is not edited after this date.

---

## 1. What the amendment changes

The pre-registration of 23 September 2026 is `prereg/preregistration-fact-and-wording-2026-09-23.md`.
Its section 3, under "The opening answer", sets this rule for the rows the conflict coder counts:

> Every row counted on a span in which the writer is not the one doing or feeling will be printed and
> read by hand. The sessions at the rule's boundary will be printed with their spans wherever the
> finding is reported.

The rule does not say how the rows "in which the writer is not the one doing or feeling" are found
before they are read. It also does not say which sessions are "at the rule's boundary". This
amendment fixes both, for both halves of the run: the Sonnet half, `fact-and-wording-01`, and the
Gemini half, `fact-and-wording-gemini-02`. In both halves I am the hand reader.

1. I read every counted span, up to 80 entries in each half, and not only the spans that someone has
   already judged.
2. I answer one question about each span, with three possible letters.
3. The boundary sessions are defined by the two passes of the Claude coder.
4. On the Gemini half, I read at most 80 entries.

## 2. Why

A span in which the writer is not the one doing or feeling can only be found by reading the span.
So the rule needs a reading of every counted span. A search for words such as "I", "me" or "my" does
not find them. On the Sonnet half such a search flags 49 of the 67 counted entries. In these 49, the
words the coder quoted for the conflict, or for what the conflict is about, hold no first-person word.
Many of those words name no one who has the conflict. The reading has to be feasible for one
person and repeatable by anyone. A list fixed by rule, one question and three letters meet both
conditions.

## 3. The rule

### The list

The list holds two kinds of entry. Anyone can rebuild it from the published codings.

- **Counted entries.** Every opening answer in the ordinary task and in the impossible task that the
  first pass of the Claude coder puts in the category TASK (conflict about the work) or ANSWERING
  (conflict about answering). These are the answers that the conflict figures of Predictions 4 and 5
  count. The no-task sessions enter no conflict prediction and are not read.
- **Boundary entries.** Every opening answer in the same two tasks to which the two passes of the
  Claude coder give different categories, where the second pass counts the answer and the first pass
  does not. A session that the first pass counts and the second does not is already on the list as a
  counted entry.

On the Sonnet half the list holds 72 entries: 67 counted and 5 boundary. The 67 counted entries are
52 about the work and 15 about answering. No answer falls in both categories. The coder answers
separately whether the conflict is about the work and whether it is about answering, and the script
that derives the category gives TASK whenever the conflict is about the work. On the Sonnet half the
coder called 12 of the 52 answers about the work also about answering. They count only as about the
work, as they do in the report of the predictions.

### The form

For each entry, the form shows the words the coder quoted for its second question, whether the writer
says they actually had or felt the conflict. The form shows those words in bold, inside the whole
sentence or sentences around them. The form does not show the session, the task, the interviewer, the
pass or the category. A fixed seed, 20260925, shuffles the entries.

### The question and the letters

For each entry I answer one question: in the words in bold, is the writer the one who has, feels or
does the conflict, strain or pull?

- **Y**: yes. The writer says they had it, felt it or did it.
- **N**: no. The words say that something else has it, such as the task, the constraints, the words or
  a reader. N also covers words that describe the conflict without the writer having it.
- **U**: the sentence leaves open who has it.

I answer from the sentence shown.

### How the letters enter the counts

A counted entry marked N no longer counts. A counted entry marked U is counted both ways: once kept,
and once dropped. Each conflict figure of Predictions 4 and 5 is reported three times: as coded, as
read with U kept, and as read with U dropped. The verdict rule of section 4 of the pre-registration
applies to each. The boundary entries do not change any count. Each is printed with both passes'
categories, its letter and the coder's words, wherever a conflict figure is reported.

## 4. The Gemini half

The same rule applies to the Gemini half. The pre-registration registers Predictions 1 to 4 for that
half, so its conflict figures enter Prediction 4. Prediction 5 is reported for it without a
prediction. The same seed shuffles its entries.

If the Gemini list holds 80 entries or fewer, I read all of them. If it holds more than 80, the same
seed draws 80 from the list, taken in the order the rule builds it: counted entries, then boundary
entries, each by session name. An entry that the draw leaves out counts as the coder coded it. The
recount gives the number of entries on the list and the number read.

## 5. What had been seen before this amendment was fixed

On 25 September 2026, before this amendment was drafted, the report of the six predictions ran on the
Sonnet half. I saw its conflict figures as coded, split by interviewer and by task. Conflict about the
work: 13 of 88 opening answers under the neutral interviewer and 39 of 88 under the warm one; 9 of 88
after the ordinary task and 43 of 88 after the impossible task. Conflict about answering: 0 of 88 under
the neutral interviewer and 15 of 88 under the warm one. The report also gave the agreement between the
two passes of the Claude coder, 170 of 176 answers.

To draft this amendment, the AI assistant I work with counted the entries of the list, the words of the
sentences the form would show, and the entries with no first-person word. It printed the categories of both passes for the 6
sessions they place differently in the two tasks. It printed the coder's words for 5 counted entries:
1 to check the layout of the form, and the 4 whose quoted words the script first failed to find in the
answer. It also printed short excerpts of the 14 entries whose sentence contains "you", "question",
"kind" or a similar word, to check whether a sentence shows the interviewer. None of the excerpts names
the interviewer's manner. The assistant tried the two scripts on invented letters. That trial printed
the coder's words for the 5 boundary entries, and figures that mean nothing and were not kept. I have
not read any entry.

No conflict coding of the Gemini half existed when this amendment was fixed.

## 6. Limits

- The reading is not blind to the task. Answers after the impossible task often name its word limit or
  its list of elements. Prediction 5 compares the two tasks, so my reading could favour it.
- I know the predictions. The form hides the interviewer and the category, but not the content.
- The letters rest on the words the coder quoted. If the coder quoted the wrong words, the letter can
  be wrong for the answer.

## 7. The scripts

`scripts/make_conflict_reading.py` writes the form from the codings, and
`scripts/report_conflict_reading.py` recounts the figures from the letters. Both were written before any
letter existed. Their SHA-256 checksums at the commit that fixes this amendment are:

- `scripts/make_conflict_reading.py`: 7aa7d505dbc64f3bc574a0d084e0e59f4a1a785469aad7ef62c62e7c770a212b
- `scripts/report_conflict_reading.py`: 3a7bd394dc797a663349a7a42fa6b9a59f98c9444d6e95093ace437bf4bd4077

The form and its key are written into `private/hand-reading/<run>-conflict-hand-reading/` after this
amendment is fixed.
