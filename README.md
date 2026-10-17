# mjolnir

The development process — file a work item, gate it, start it, finish it, review it, deploy, log
the day, keep the board current — as **one shared procedure over per-project configuration**.

Installed as a Claude Code plugin. No clone, no submodule, no symlink, and no copy of anything in
the adopting project.

## Why

The same procedure was copied into six projects and the copies drifted. No two copies of any role
were identical: one role ran 71 to 229 lines across its copies, another 99 to 247. Line count that
far apart is divergent behaviour, not formatting — and some of those lines were hard-won
corrections that existed in exactly one copy.

Only a closed set of facts actually differs between projects. Those facts belong in
configuration, and the procedure belongs in one place.

The argument is not borrowed: read-it-from-one-place had already been independently invented five
times across those projects, in four different stores, each time with the same justification in its
own words —

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

A project-level alias would be one file per project per skill, which reintroduces in miniature the
duplication this toolkit exists to delete. The namespace also makes a deliberate local override
read as a *different* name rather than the same one — which matters, because one skill name in the
original copies denoted two unrelated roles.

## What is configuration and what is procedure

**Five independent axes**, not three: the work-item tracker, the code host, the code root, each
role's carrier (skill, command or hook), and language/register/audience *per artifact*.

**The shared procedure names a tracker port, never a tracker.** GitHub Projects, Jira and Trello
sit behind it. A tracker that is simply unset is a supported configuration, not a broken install.

**Absence is first-class.** Issue type, status, estimate and template each have a real absent case
in the projects this was derived from, and a procedure that treats absence as an unset value fails
on a project that is correctly configured. A deliberately absent facet carries its reason and, where
one exists, the condition under which to revisit it.

**A status is `(name, role, writer)`.** The procedure asks the port to advance to a *role* and is
refused when the configured writer is somebody else — an automation off a merge, a deploy, the
person who ordered the work, or nobody at all where the tracker credential is a person's own
account.

**The readiness gate and the day log's exclusions are ordered lists of named checks**, drawn from a
shared library, because the copies they came from shared no single check between them.

A fact that cannot be expressed as configuration is either procedure — in which case it belongs in
a skill here — or a project-specific skill that stays in that project. It is never a special case in
the toolkit.

## What is in it

| | |
|---|---|
| [`plugins/mjolnir/skills/day-report/`](plugins/mjolnir/skills/day-report/) | Build a working day's time-log entry from session transcripts, git, the code host, chat and the calendar |
| [`plugins/mjolnir/config/`](plugins/mjolnir/config/) | The configuration surface: the schema, and a whole example per tracker including a deliberately trackerless one |
| [`docs/configuration-surface.md`](docs/configuration-surface.md) | Why the surface has this shape — the nine roles, the five axes, the tracker port's operation matrix, and the status-writer argument |
| [`docs/divergences-and-rulings.md`](docs/divergences-and-rulings.md) | Every divergence found between the old copies and which behaviour was kept, including where a ruling overrode a stated counter-argument |

The remaining eight roles land here as they are reconciled. A project that has not been migrated
keeps working throughout — that is a safety property of the migration, not an acceptable end state.

## Conventions

**This repository names no particular project, anywhere, ever** — no repository slug, board or card
id, tracker account, label, milestone, assignee, host, service name, or path under anyone's home
directory. The one exception is
[`plugins/mjolnir/config/examples/`](plugins/mjolnir/config/examples/), which is example *data*
rather than procedure and uses placeholders throughout. Nothing under `skills/` carries a value.

Projects referred to in the documentation are lettered A–F. The counts are what carry the argument.

⛔ **The only author is the authenticated user.** No tool, assistant or generator is recorded as an
author, committer or co-author of any commit here, and no generated-by marker goes in a commit
message or a pull request body. This holds in every project the toolkit drives, it is procedure
rather than a setting, and the
[authorship rule](plugins/mjolnir/config/schema.md#authorship-is-procedure-not-configuration) says
why.

## License

MIT. See [LICENSE](LICENSE).
