# Eliciting self-reports from AI systems: the pilot behind the article

This repository holds everything behind a pilot study of ten runs and 896
sessions, in which language models were interviewed about their own processing
using a fixed schedule. **There is no interpretability access anywhere in this
project, and no probes of any kind, so nothing here tests whether any answer a
model gave is accurate.** What the runs test is whether the instrument works:
whether it catches its own artefacts, whether it can tell one thing from
another, and whether its results survive being written down as a prediction and
then tested again.

Two items came through. Two catch items discriminated without a single
exception across 612 sessions, and instances asked to answer as a person who
does not exist accepted a false premise about waiting in 32 of 44 sessions
while declining a false premise about the conversation in 44 of 44. Instances
interrupted during a task they could not complete reported conflict about the
work in 65 of 88 sessions, against 4 of 88 given an ordinary task and none of
88 given no task, where a search for the vocabulary of conflict would have
found it in every condition. The measure the article was originally built
around did not come through: instances writing as a fictional person produced
it as often as instances describing themselves, at 15.9 per cent against 15.9,
and its rate turns on how one coder reads one question of its rule.

## The finding that should change how you read everything else here

Every coding pass in this pilot was run twice, and agreement between the two
passes of one model family was high throughout, at 260 of 264 and better. That
agreement concealed a disagreement between families. Asked whether a passage
reaches for a name and withdraws it, coders from the first family answered yes
about 50, 53 and 116 passages; coders from the second answered yes about 4, 1
and 6. Each family repeats itself, at 0.66 to 0.93 corrected for chance, while
the two agree with each other at 0.07 and 0.02. Settling that one reading takes
the headline rate from 14 of 88 to 2.

So agreement between two passes of one model shows that the model reads its own
rule consistently. It shows nothing about whether the rule means anything. Any
number in this repository that comes from a model-coded rule should be read with
that in mind, and the disputed passages are published with both coders' answers
so that a reader can rule on them without taking anyone's word for it.

## Where to start

| If you want to | Open |
|---|---|
| Check a number in the article | `public/sessions.csv` and `public/codings.csv` |
| Read the rules the coders were sent | `public/coding-rules.md` |
| Read what was predicted before the data existed | `prereg/` |
| Read a session in full | `data/runs/<run>/sessions/` |

`public/sessions.csv` has one row for each of the 896 sessions, with the run, the
condition, the task the instance was given, the wording, the item order, the
model, the temperature, and the length of the answers. `public/codings.csv` has one
row for each coding of one session by one pass of one coder, with the category,
the verdicts and the span the coder quoted as its evidence. Join them on the
`session` and `run` columns together, because session names repeat across runs.

**Reading the sessions in a browser.** `public/reader.html` filters the 896
sessions by run, condition and wording, searches their text, opens any one of
them in full, and shows what each coding pass answered about it with the span
each coder quoted. **It is live at https://urimpression.github.io/ai-self-reports/public/reader.html**, so
nothing has to be cloned or installed to read the sessions. If you have cloned
the repository and want to run the page yourself, serve the folder rather than
opening the file directly, because a browser will not let a page on disk read
the data files: run `python3 -m http.server 8000` at the top of the repository
and open `http://localhost:8000/public/reader.html`.

Both files are rebuilt from the run folders and the coding folders by
`scripts/build_public_tables.py`, and `scripts/check_public_tables.py`
regenerates every headline figure in the article from those two files alone and
prints each one beside the figure the article states. If a number in the article
and a number in the table ever part company, that script is where it shows.

## What is a record and what is rebuilt

| Folder | What it holds | Record or rebuilt |
|---|---|---|
| `data/runs/` | Every session, with the request and response bodies | Record. Irreplaceable |
| `data/transcripts-*.md` | The four runs made in the browser tools, before the scripts existed | Record. Irreplaceable |
| `prereg/` | The pre-registrations, none edited after its date | Record. Irreplaceable |
| `analysis/coding/` | What each coder answered, pass by pass | Record. Rebuilding it means paying for the coding again |
| `analysis/*.md` | The run reports and findings | Rebuilt from the codings |
| `public/` | The two tables, the coding rules and the reading page | Rebuilt. Two commands |
| `scripts/` | The runner, the coders and the analysis | Source |
| `tools/` | The browser tools that made the first four runs | Record, kept for that reason. Nothing new should be run in them |

## Reproducing a run and a coding pass

Both commands need an API key of your own in your shell, as
`ANTHROPIC_API_KEY` or `GOOGLE_API_KEY`. Nothing in this repository carries a
key, and `--dry-run` prints the session count and a cost estimate before
anything is sent.

```
python3 scripts/run_interview.py --run my-run --dry-run
python3 scripts/code_change_item.py --run my-run --rule registered --run-number 1
```

The factorial of 264 sessions cost about twenty-three in the provider's
currency on 4 September 2026. A coding pass over the same run costs a small
fraction of that, and every pass here was run twice.


## How to cite this archive

Cite https://doi.org/10.5281/zenodo.22728631, which is Zenodo's identifier for the
archive as a whole and always resolves to the newest release. `CITATION.cff` at
the top of the repository carries the same details in a form a reference manager
can read.

## Licence

The scripts and the browser tools are under the MIT licence. The transcripts,
the codings, the analysis and the article are under Creative Commons
Attribution 4.0. `CITATION.cff` at the top of the repository says how to cite
the archive.
