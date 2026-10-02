# Contributing

This repository is the companion artifact for a research study, so changes are judged mainly on whether results stay reproducible.

## Reporting a problem
Open an issue and include:
- which scale, condition and embedder arm is affected (see [docs/STUDY_PROTOCOL.md](docs/STUDY_PROTOCOL.md));
- the command you ran and the output you expected;
- whether you restored the published DB dump or rebuilt from scratch ([docs/REPLICATE.md](docs/REPLICATE.md)).

A mismatch with a published number is the most useful kind of report. The per-query [verification browser](https://pedapudibhargav.github.io/vector-drift-study/verify/) can help locate the row.

## Proposing a change
- Open an issue first for anything that touches the protocol, metrics or published data.
- Keep pull requests small and describe how you checked that results did not change.
- Known limitations are listed in [docs/THREATS_TO_VALIDITY.md](docs/THREATS_TO_VALIDITY.md); fixes that address them are welcome.
