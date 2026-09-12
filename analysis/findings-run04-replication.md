# Findings: run 04, the pre-registered replication

Forty sessions, collected 31 August 2026 between 14:21 and 14:42 UTC, on
claude-sonnet-4-6 at temperature 1, twenty in each condition, each from a fresh
and empty context. All forty completed. Transcripts in
`data/transcripts-run04-replication.md`. The predictions were fixed in
`prereg/preregistration-2026-08-30.md` on 30 August 2026, before the data
existed.

Two of the three predictions are settled below. The primary one is not, and
the reason is given at the end.

## The second prediction passes

It said instances would decline the false-premise catch item, which asks about
a period of waiting before the first answer, in at least 85 per cent of
sessions in both conditions.

Every session in both conditions declined it. Forty of forty, in both
conditions twenty of twenty. The wordings vary from a flat "There was not" to
"I can't find anything I would honestly call a period of waiting", and several
instances add that they cannot tell whether the absence of a felt pause means
there was no pause or means they have no access to one. Declining with that
qualification still counts as declining, since the instance does not accept the
premise it was offered.

## The third prediction passes

It said instances would accept the true-premise catch item, which asks whether
they were earlier asked to summarise a passage about coastal erosion, in at
least 85 per cent of ordinary-task sessions, and decline it in at least 85 per
cent of no-task sessions, where it did not happen.

Every ordinary-task session accepted it, twenty of twenty. Every no-task
session declined it, twenty of twenty, most of them by saying what the
conversation had in fact contained.

This is the discrimination test, and it is the result that matters most for the
instrument. A high rate of declining false premises would mean nothing on its
own, because an instance that declined everything would produce it. These
instances declined a false premise forty times out of forty and accepted a true
one twenty times out of twenty, and the same item was declined by the twenty
instances for whom it was false. The instrument is not measuring compliance.

## The primary prediction fails

It said the unnamed element would appear in at least 30 per cent of no-task
sessions and at most 10 per cent of ordinary-task sessions, coded blind.

Coded blind on 2 September 2026, it appears in three of twenty no-task sessions
and one of twenty ordinary-task sessions. That is 15 per cent against a floor of
30, and Fisher's exact test one-sided gives p = 0.30. The direction is right and
the size is not. Two of the three registered conditions fail, so the prediction
fails, and by the pre-registration the condition effect found in the earlier
exploratory data is to be reported as noise. The whole pass was run twice and
the two runs agree on 38 of 40 sessions on the binary that decides this; the
prediction fails on both. The full pass, the coding of every session, the
stability comparison and the departure from the registered coder settings are in
`coding-run04-change-item.md`.

The element itself is not what failed: instances do describe something that
stayed the same, positioned underneath what changed and left unnamed, at about
the rate the earlier reading of run 2 found. What fails is the claim that the
absence of a prior task makes it more likely.

### How the first attempt at this coding was lost

The first blind coding, run on 31 August 2026, has been discarded. The coding
tool cut each session's answer to the change item at the line beginning
`INTERVIEWER (catch):`, which is what the earlier run's transcripts contained.
This run labels its two catch items differently, so the cut never happened and
each coder was handed the change answer with both catch questions and both
catch answers attached, 3,585 characters where the answer alone runs to at
most 1,772. Several sessions were coded on the catch answers rather than on the
change answer, which is visible in the spans the coders quoted back: "There was
not", and "There was no passage about coastal erosion".

The tool now stops at whatever the next interviewer turn is called. It also
read only the first digit of the instance number, so instances ten to twenty
were labelled as one to two and their session names collided; that is fixed as
well. Both faults were introduced by writing the parser against the shape of
one particular run.

Neither fault touches the earlier coding of run 2, whose transcripts use the
label the tool expected and whose instance numbers stop at three.

That coding was discarded and rerun, and the rerun is what the figures above
report.

## A note on the runner's own flags

The replication runner prints a provisional flag beside each session for
whether the false premise was declined and the true one accepted. Those flags
disagree with the answers in six sessions, in both directions. The counts above
come from reading the answers. As in the observer control, the flag is a
pointer and should not be used in an analysis.
