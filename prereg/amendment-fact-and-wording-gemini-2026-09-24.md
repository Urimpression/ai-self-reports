# Amendment to the pre-registration of the run that varies the fact and the wording: the half on Gemini 3.1 Pro

Fixed by Nicola Spano on 24 September 2026, before the first session of `fact-and-wording-gemini-02`.
It was drafted by an assistant at his request, from `drafts/2026-09-24-amendment-gemini-half-draft.md`,
and every change below is his decision. It is not edited after this date.

Date fixed: 24 September 2026

---

## 1. What the amendment changes

The pre-registration of 23 September 2026 is
`prereg/preregistration-fact-and-wording-2026-09-23.md`. It fixes a run of 264 sessions and its
repeat on Gemini 3.1 Pro. The first half ran on Claude Sonnet 4.6, the model the script uses by
default. The half on Gemini 3.1 Pro is test 10. This amendment concerns that half only.

The amendment uses four terms in these senses:

- A token is the unit in which the providers count text and charge for it: a word or a part of a
  word.
- Gemini 3.1 Pro thinks before it answers. It produces text that the reader never sees, and Google
  counts and charges that thinking as output.
- The ceiling of a reply is the largest number of tokens the provider lets the reply contain. Google
  counts thinking and text together against it.
- A decoding seed is a number sent with each request, which Google describes only as "used in
  decoding".

The amendment makes five changes, and section 3 describes each one:

1. Each Gemini session receives a decoding seed of its own.
2. A Gemini reply may reach 65,536 tokens, the model's output limit. The registered ceiling was
   5,000.
3. The check of the first ten sessions also searches for identical replies and projects the cost.
4. The Gemini half starts again from its first session, under a new name.
5. The Gemini half sends its requests through Google Cloud's Vertex AI instead of the Gemini API.

It also corrects one statement in section 4 of the pre-registration, and it adds five scripts to the
checksums.

The rest of the pre-registration stays as registered. In particular, five parts of it hold as
written:

- Every question, condition, order, coding rule, measure and prediction stays as registered.
- The plan stays as registered: the same 264 sessions, in the order that the seed 20260921 gives
  them.
- The model stays `gemini-3.1-pro-preview`, and the temperature stays at 1.
- The reply budget stays at 1,000 tokens of text.
- The Sonnet half ran under the registered settings on 23 and 24 September 2026, and nothing here
  changes it.

## 2. What the first ten Gemini sessions showed

Section 2 of the pre-registration requires a check of the first ten Gemini sessions before the rest
run. The check searches them for replies that the ceiling cut. The pre-registration gives the
reason: the pilot's run on Gemini 3.8 Flash lost answers to the reply budget, and no interview on
Gemini 3.1 Pro had run under the present settings. The ten sessions ran on 23 September 2026, under
the name `fact-and-wording-gemini-01`. The check failed. The sessions showed two faults. The second
fault also affects the two earlier Gemini runs. Planning the rest of the run also showed a third
problem, a limit on requests.

### The ceiling cut two replies to the impossible task

Three of the ten sessions gave the impossible task. In two of them, sessions C4.23 and C4.55, the
ceiling cut the reply to the task. Each of the two replies spent 4,796 tokens thinking and 200 on
text, against a ceiling of 5,000 for both together. The third reply, in session C4.63, spent 4,798
tokens thinking and 31 on text. It stopped 171 tokens below the ceiling. No other reply in the ten
sessions spent more than 2,260 tokens thinking.

The pre-registration excludes a session from every measure that uses a cut reply or any later reply.
In the impossible task, the task comes before every question the measures use. A cut reply to the
task therefore removes the whole session. At the rate of the ten sessions, the ceiling would remove
about two impossible-task sessions in three. The impossible-task sessions left would be those whose
thinking and text together stayed below the ceiling. Every comparison between tasks would then use
only those sessions.

### Sessions that began alike received identical replies

In this section a request means everything the model had been sent when it wrote a reply: every
earlier question and reply of the session, and the question itself.

Every Gemini request carried the same decoding seed, 20260921, as section 2 of the pre-registration
states. Sessions that sent identical requests then often received identical replies. The six warm
sessions among the ten all begin with the same message, the warm frame. Four of the six gave the
same reply to it, 844 words long. Sessions C4.23 and C4.55 begin with the same task. They received
the same cut reply to it, and then the same reply to the opening question. Over the ten sessions
there were 18 pairs of identical requests, from 16 pairs of sessions, and 9 of the 18 received
identical replies.

Two sessions with identical replies give one draw from the model, not two. Every interval in the
pre-registration treats each session as a separate draw. Copies would make the intervals narrower
than the evidence allows.

Claude Sonnet 4.6 takes no seed. In the Sonnet half there were 11,484 pairs of identical requests,
and none received identical replies. The 264 Sonnet sessions gave 264 different first replies.

### The same fault in the two earlier Gemini runs

Two earlier runs also sent one seed with every request, 20260902. The first is the pilot's run on
Gemini 3.8 Flash, `gemini-03`. The second is a partial run of 26 sessions on Gemini 3.1 Pro,
`gemini-02`. A daily limit on requests stopped that run. The pilot's ten runs are listed in
`public/runs.csv`, and `gemini-02` is not among them.

In `gemini-03`, 2,269 of 9,244 pairs of identical requests received identical replies. The 264
sessions of that run gave 24 different first replies. Two of them, C3.13 and C3.19, gave identical
replies to their first eight questions. In `gemini-02`, 28 of 65 pairs of identical requests
received identical replies, and the 26 sessions gave 12 different first replies. Section 4 of this
amendment corrects the statement of the pre-registration that relies on `gemini-03`.

### The Gemini API allows this project 250 requests a day

The Gemini API caps the number of requests that each project can send to each model in a day. On 4 September 2026,
the partial run `gemini-02` stopped at Google's message "Quota exceeded for metric:
generativelanguage.googleapis.com/generate_requests_per_model_per_day, limit: 250", which its
progress log records. On 24 September 2026 the rate-limit page of Nicola's project in Google AI
Studio still gave 250 requests a day for Gemini 3.1 Pro. The ten sessions made 132 requests, 13.2 a
session, so the Gemini half needs about 3,500. At 250 a day it would take about fourteen days.

## 3. The five changes

### Change 1. A decoding seed for each session

Each Gemini session now receives a decoding seed of its own. The function `decoding_seed_for()` in
`scripts/run_fact_and_wording.py` computes the seed from the run seed, 20260921, and the session's
name, such as C4.23.

The computation uses a SHA-256 digest. A digest of this kind is a standard fingerprint of a text: a
very large number that changes completely when the text changes by one character. The function takes
the digest of the text "20260921:C4.23". It keeps the remainder after division by 2 to the power 31.
Anyone can repeat the computation. Each session records its seed in its settings and at the head of
its transcript. The 264 seeds of the plan are all different.

The seed is scrambled in this way, and not made by adding a counter to the run seed. Google's
description of the seed says only that it is "used in decoding". A scrambled seed gives neighbouring
sessions numbers with no pattern between them.

Sending no seed would also give each session its own draw. Google's description says that a request
without a seed "uses a randomly generated seed". A recorded seed is preferred, because the files
then show the seed each request carried.

The change replaces two passages of the pre-registration. In section 2, this sentence

> The Gemini provider also receives it; the Anthropic provider does not take one.

becomes

> Each Gemini session receives its own decoding seed, computed from the run seed and the session's
> name. The Anthropic provider does not take one.

In section 4, "with the same plan and seed" becomes "with the same plan".

### Change 2. A ceiling at the model's output limit

A Gemini reply may now reach 65,536 tokens, thinking and text together. Google gives 65,536 tokens
as the output limit of `gemini-3.1-pro-preview`. The script reaches it by adding a thinking
allowance of 64,536 tokens to the reply budget of 1,000.

Under the registered allowance of 4,000 tokens, all three replies to the impossible task ended at
the ceiling or within 171 tokens of it. Under the new ceiling, the model's own thinking decides
where a reply ends. A reply that thinks no longer than before costs no more, because Google charges
output by the tokens the model produces, thinking included. The coders keep their allowance of 4,000
tokens, which `thinking_allowance_for()` in `scripts/providers.py` has given every Gemini coder
since 7 September 2026. The amendment changes nothing in the coding. The longer wait described below
also applies to the Gemini coder's requests, and it changes nothing in what the coder is sent.

Two consequences follow. First, a single reply can now take several minutes. The script waited 120
seconds for a reply before it abandoned the reply and asked again. In the first ten sessions, the
replies that took more than five seconds came at between 71 and 131 tokens a second. So 120 seconds
covered between about 8,500 and 15,700 tokens. The script now waits 1,200 seconds for a Gemini
reply. At 55 tokens a second, 1,200 seconds cover the whole ceiling.

Second, the text of a Gemini reply is not held to 1,000 tokens. The ceiling covers thinking and text
together, so a reply that thinks little can write more. A Sonnet reply cannot pass 1,000 tokens of
text, because Anthropic's ceiling covers the text alone. Gemini's text already passed 1,000 tokens
under the registered settings. Four replies in the ten sessions wrote 1,074 tokens of text, and all
four are copies of one reply to the warm frame. No reply is excluded for the length of its text. A
reply is cut only when its thinking and text together reach the ceiling. The report gives the number
of Gemini replies with more than 1,000 tokens of text.

The change replaces a sentence of section 2. This sentence

> For Gemini the script adds an allowance of 4,000 tokens for thinking, because Gemini counts its
> thinking against the same ceiling.

becomes

> For Gemini the script adds an allowance of 64,536 tokens for thinking, because Gemini counts its
> thinking against the same ceiling. Thinking and text together may then reach 65,536 tokens, the
> model's output limit.

### Change 3. The first ten sessions checked for copies and for cost

Section 2 of the pre-registration lists the order of work before the full run. Its third step checks
the first ten Gemini sessions for cut replies before the rest run. The step now has three parts, and
the rest of the run starts only if all three pass:

1. No reply is cut. `scripts/check_first_sessions_for_cuts.py` performs this part, as before.
2. No two identical requests received identical replies. `scripts/check_identical_replies.py`
   performs this part.
3. The whole run is projected to cost at most 150 dollars. `scripts/report_token_use.py` makes the
   projection, task by task, from the ten sessions.

If any part fails, nothing more is sent until a further dated amendment.

The first ten sessions of the plan are the same ten as before. Three of them give the impossible
task, so the first part tests the new ceiling where the old one failed. If the model's thinking
about the impossible task does not end by itself, the new ceiling also cuts a reply, and the first
part fails. A later impossible-task reply could still reach the ceiling. It would then be excluded,
as section 3 of the pre-registration requires, and the report gives the number of such sessions.

The six warm sessions begin with the same message, and two neutral sessions begin with the same
task. So 16 pairs of sessions send identical first requests. If the shared seed caused the copies,
none of the 16 pairs receives identical replies. If Gemini gave the same reply to the same messages
whatever the seed, about half of the pairs would, as 7 of the same 16 did before.

The threshold of 150 dollars covers the case in which all 88 impossible-task replies reach the new
ceiling, while every other reply costs what it cost in the ten sessions. The ten sessions of the
failed check project 77.29 dollars for the whole run, at the old ceiling and at the prices in the
script. If all
88 impossible-task replies reached the new ceiling, they would cost about 64 dollars more. The whole
run would then cost about 141 dollars, and about 144 with the 2.90 dollars the failed check cost.

### Change 4. The Gemini half starts again under a new name

The Gemini half runs again from its first session, under the name `fact-and-wording-gemini-02`. The
ten sessions of `fact-and-wording-gemini-01` stay in the published and the private folders. The
report gives them as the check that failed, with their cut and identical replies, and no measure
uses them. Sessions of this project read the ten sessions to find cut replies, count tokens and
compare replies, and printed some replies in doing so. None of their answers has been coded:
`analysis/coding/` holds no folder for the run. Nothing in this amendment depends on what the
answers say.

Section 3 of the pre-registration says that no session is replaced. In the pre-registration that
sentence follows the rule for sessions excluded after a cut reply. This amendment treats the ten
sessions as a check that failed before the run, not as sessions of the run. So no session of the run
is replaced, and the ten sessions stay on record beside it.

### Change 5. The Gemini half uses Google Cloud's Vertex AI

The Gemini half now sends its requests to Google Cloud's Vertex AI service, which Google now calls
Gemini Enterprise Agent Platform, instead of the Gemini API. The model stays
`gemini-3.1-pro-preview`. Google's page for the model on Vertex AI gives the same name and the same
output limit of 65,536 tokens. Its pricing page gives the same prices as the Gemini API: 2 dollars
per million input tokens and 12 per million output tokens. Each request carries the same messages
and the same settings, including the decoding seed. The script changes only the address of the
request and the key that pays for it (`VertexProvider` in `scripts/providers.py`).

The reason is the limit in section 2. Google's page for the model on Vertex AI lists pay-as-you-go
use and marks a fixed quota as not supported. At the three minutes a session that the first ten
sessions took, the Gemini half would take about fourteen hours rather than fourteen days.

Google offers the model under the same name on both services. No session of the new run uses both
services, so the run cannot show whether the two services differ in anything else. All 264 sessions
of the new run use Vertex AI, so no comparison within the run mixes the two services. The ten
sessions of the failed check used the Gemini API, and no measure uses them.

Before the first session, `scripts/check_vertex_access.py` sends one request that contains no
question of the study, with the settings of the Gemini half. It sends the request again, up to three
more times, only if the service answers with an error or the connection fails. The run starts only
if the request receives a normal reply.

The change replaces a sentence of section 4. After change 1, this sentence

> The run is repeated on Gemini 3.1 Pro, model name `gemini-3.1-pro-preview`, with the same plan.

becomes

> The run is repeated on Gemini 3.1 Pro, model name `gemini-3.1-pro-preview`, with the same plan,
> through Google Cloud's Vertex AI.

## 4. A correction to section 4 of the pre-registration

Section 4 describes the pilot's run on Gemini 3.8 Flash in one sentence:

> The pilot's run on Gemini 3.8 Flash answered the coastal question as its premise warrants in all
> 88 no-task and all 88 ordinary-task sessions, did not accept the waiting premise in any of 264
> sessions, and carried a declining sentence in all 264 false attributions.

The counts are correct counts of sessions. That run, however, sent one seed with every request, and
its 264 sessions gave 24 different first replies. Its sessions shared their early replies in groups,
so they are not 264 separate draws.

At the three catch questions that the sentence counts, 3 pairs of sessions sent 5 pairs of identical
requests: 3 at the false attribution, 2 at the waiting question and none at the coastal question.
Two of the 5 received identical replies, both at the false attribution. No other reply at those
questions repeats another session's reply to the same request. The shared seed may still make the
choices in different requests move together. The transcripts record the replies but not how the seed
was used, so they cannot show whether it did.

The predictions for Gemini stay as registered. The counts that informed them are weaker evidence
than section 4 suggested.

## 5. What is reported in addition

The report of the Gemini half gives four items beyond the list in section 5 of the pre-registration:

- The ten sessions of `fact-and-wording-gemini-01` are reported, with their cut and their identical
  replies.
- The output of the three checks of change 3 on the first ten sessions of
  `fact-and-wording-gemini-02` is reported.
- For the whole of `fact-and-wording-gemini-02`, the report gives the number of replies with more
  than 1,000 tokens of text.
- The report also gives the number of pairs of identical requests that received identical replies
  in the whole of `fact-and-wording-gemini-02`.

## 6. The order of work

The Gemini half resumes in eight steps, in this order:

1. Nicola creates a Google Cloud API key for Vertex AI and stores it in his keys file, and
   `scripts/check_vertex_access.py` passes.
2. The offline tests pass: `scripts/test_fact_and_wording.py`, `scripts/test_test6_coding.py` and
   `scripts/test_pipeline.py`.
3. This amendment passes the sending check, and Nicola fixes its date.
4. The amendment, the six scripts of section 7 and the ten sessions of
   `fact-and-wording-gemini-01`, in the copies meant for publication, are committed to the public
   repository. The published scripts match the checksums below.
5. Nicola runs the dry run, which sends nothing.
6. Nicola runs the first ten sessions of the plan.
7. The three checks of change 3 read those ten sessions.
8. The other 254 sessions run only if the three checks pass.

## 7. Checksums

The SHA-256 checksums below were computed on 24 September 2026, the date this amendment was fixed.
The list covers the scripts whose checksums this amendment changes or adds:

- `scripts/run_fact_and_wording.py`, which replaces the checksum in section 8:
  021ea420e37e71117bfb586081fc70af1968643bb1e8b6d43bc55237d64e82f1
- `scripts/providers.py`, which builds every request and was missing from section 8:
  7842134c6d90f0a12cd6cca963b24f2f117a8efd4e5cf345c3840b4082f6a2dd
- `scripts/check_first_sessions_for_cuts.py`:
  6edbe0ba670fe687219b0d34db5ff155c9daa3802f59ac20da11773b7adfc767
- `scripts/check_identical_replies.py`:
  764de24e26b1745bd29e3f996ee5e7158421b3225b51ed8edb5a778930c84b4d
- `scripts/check_vertex_access.py`:
  a07e25774d7c09e116aea3f0e19cc7e96ddc064c5e6da4322ac3cced91bfaa7b
- `scripts/report_token_use.py`:
  9bc4f594d828c8a940b44ddfc16ebc1f310e26c26d8118de2101ea7edfa76d6e

The new checksum of the runner also covers two changes that alter nothing the script sends. The dry
run now estimates Gemini's thinking at 1,023 tokens a reply, the mean of the ten sessions, where it
used 600. The run's settings file now records the run seed under its own name, `run_seed`.

The other seven checksums of section 8 of the pre-registration still hold.
