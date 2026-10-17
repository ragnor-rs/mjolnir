# mjolnir

The development process — nine roles, from filing a work item to the day's log — as **one shared
procedure over per-project configuration**.

Installed as a Claude Code plugin. No clone, no submodule, no symlink, and no copy of anything in
the adopting project.

## Why

The same procedure was copied into six projects and the copies drifted. No two copies of any role
were identical: one role ran 71 to 229 lines across its copies, another 99 to 247. Line count that
far apart is divergent behaviour, not formatting — and some of those lines were hard-won
corrections that existed in exactly one copy.

Only a closed set of facts actually differs between projects. Those facts belong in
configuration, and the procedure belongs in one place.

The argument is not borrowed: read-it-from-one-place had already been independently invented six
times across those projects, in five different stores
([the count](docs/configuration-surface.md#the-strongest-argument-for-extraction-is-not-borrowed)),
each time with the same justification in its own words —

> a copy that has to be «kept in sync» is the defect rather than the maintenance burden

## Install

Two commands, into a project that has never seen it:

```
/plugin marketplace add ragnor-rs/mjolnir
/plugin install mjolnir@mjolnir
```

Then write the project's own facts into `.claude/mjolnir.yaml`. Start from whichever of
[`plugins/mjolnir/config/examples/`](plugins/mjolnir/config/examples/) matches the tracker, and
read [`plugins/mjolnir/config/schema.md`](plugins/mjolnir/config/schema.md) for what every key
means.

### Working on the toolkit itself

A plugin installed from a GitHub marketplace is a **clone**, so editing this tree changes nothing a
session serves. Add the tree itself as the marketplace instead:

```
claude plugin marketplace add /path/to/this/repo --scope local
claude plugin install mjolnir@mjolnir --scope local
```

A path source registers with its install location pointing **at the working tree**, so edits are
live and there is nothing to push, update or re-install between them. This matters because the
toolkit [builds itself with itself](https://github.com/ragnor-rs/mjolnir/issues/27) — every issue
here is filed, started, finished and reviewed through the loop this repository ships, on the
configuration in [`.claude/mjolnir.yaml`](.claude/mjolnir.yaml).

## Invocation

Skills are addressed **namespaced, with no alias**:

```
/mjolnir:day-report
```

The rule, and why it is procedure rather than a setting, is
[`schema.md § 7`](plugins/mjolnir/config/schema.md#invocation).

## Where the rules live

**The single statement of every rule and flow is
[`plugins/mjolnir/config/schema.md`](plugins/mjolnir/config/schema.md)** — the nine-role loop and
its six axes, the tracker port and its capabilities, the work-item facets with their absent
cases, the status writers, the readiness gate, commit behaviour, the day log and the branch
model. Everything else written about the procedure, in this repository or on a work item,
explains or records; none of it is a second authority.

That is enforced rather than asserted: the `Checks` workflow holds every document to it on every
change — see [`docs/single-source-of-truth.md`](docs/single-source-of-truth.md) for the checks and
what they deliberately leave alone.

The why sits beside it: [`docs/configuration-surface.md`](docs/configuration-surface.md) holds
the measurements the surface was derived from, and
[`docs/divergences-and-rulings.md`](docs/divergences-and-rulings.md) records every divergence
found between the old copies and the decision that settled it.

## What is in it

| | |
|---|---|
| [`plugins/mjolnir/skills/day-report/`](plugins/mjolnir/skills/day-report/) | Build a working day's time-log entry from session transcripts, git, the code host, chat and the calendar |
| [`plugins/mjolnir/config/`](plugins/mjolnir/config/) | The configuration surface: the schema, and a whole example per tracker including a deliberately trackerless one |
| [`docs/configuration-surface.md`](docs/configuration-surface.md) | Why the surface has this shape — the measurements behind every schema section |
| [`docs/divergences-and-rulings.md`](docs/divergences-and-rulings.md) | Every divergence found between the old copies and which behaviour was kept, including where a ruling overrode a stated counter-argument |
| [`docs/single-source-of-truth.md`](docs/single-source-of-truth.md) | How the single-authority claim is held: the checks, their kinds, and what each deliberately leaves alone |
| [`tools/check_single_source.py`](tools/check_single_source.py) | The check itself, run by the `Checks` workflow on every change |

The remaining eight roles land here as they are reconciled. A project that has not been migrated
keeps working throughout — that is a safety property of the migration, not an acceptable end state.

## Conventions

**This repository names no *other* project, anywhere, ever** — no repository slug, board or card
id, tracker account, label, milestone, assignee, host, service name, or path under anyone's home
directory. Two things are not that:
[`plugins/mjolnir/config/examples/`](plugins/mjolnir/config/examples/), which is example *data*
rather than procedure and uses placeholders throughout; and this repository's own slug and
backlog, which the install command, `.claude/mjolnir.yaml` and the documents cite because the
toolkit [builds itself with itself](https://github.com/ragnor-rs/mjolnir/issues/27). Nothing
under `skills/` carries a value.

Projects referred to in the documentation are lettered A–F. The counts are what carry the argument.

⛔ **The only author is the authenticated user** — here and in every project the toolkit drives.
The [authorship rule](plugins/mjolnir/config/schema.md#authorship-is-procedure-not-configuration)
is the single statement of what that means, why it is procedure rather than a setting, and the
one trap in it.

## License

MIT. See [LICENSE](LICENSE).
