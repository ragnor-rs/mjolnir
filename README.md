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
session serves. Register the tree itself as the marketplace instead, at **user scope**:

```
claude plugin marketplace add /path/to/this/repo --scope user
claude plugin install mjolnir@mjolnir --scope user
```

`user` rather than `local`, because whoever works on the toolkit is also the person adopting it in
every other project on the same machine, and one registration serves both: self-hosting here, and
every other project — whose adoption then costs exactly one file, `.claude/mjolnir.yaml`, with no
install step at all.

`local` does not confine a registration the way its name suggests, which is the sharper reason to
pass `user` explicitly rather than a matter of reach. Only the *declaration* lands in one project's
`.claude/settings.local.json`; the registry entry that resolution actually reads is machine-wide and
keyed by marketplace name. Measured: a project declaring nothing of its own resolved the plugin
from an entry a different project's `local` add had written, a second `local` add of the same name
re-pointed that entry for every project instead of coexisting with the first, and a `remove` from
one project emptied it for all of them — leaving the first project's own declaration pointing at
nothing. So `local` is not a narrower `user`; it is the same machine-wide entry with its declaration
filed somewhere that does not govern it.

What those two commands write, so the choice is checkable rather than asserted. Paths are inside
the harness's own user configuration directory, wherever `CLAUDE_CONFIG_DIR` puts it:

| | |
|---|---|
| `settings.json` | `extraKnownMarketplaces.mjolnir` — `source: directory` with the path — and `enabledPlugins["mjolnir@mjolnir"]` |
| `plugins/known_marketplaces.json` | `installLocation`, which for a directory source **is the working tree** |
| `plugins/installed_plugins.json` | `scope`, a `version`, a `gitCommitSha`, and an `installPath` under `plugins/cache/` |

**That `installPath` is a snapshot copy, and it is vestigial.** It is written once, at install, and
pinned to the recorded `gitCommitSha`. Nothing refreshes it: `plugin marketplace update` leaves it
alone, and `plugin update` is version-gated, so it reports the plugin already at its latest version
while the snapshot stays where it was. Measured in this repository: the snapshot was byte-identical
to its pinned commit, three commits behind the branch tip, and differed from the tree in six of its
seven files.

Edits are live anyway, because a session resolves a directory-source plugin through the
marketplace's `installLocation` — the working tree — and never through `installPath`.
`$CLAUDE_PLUGIN_ROOT` resolves there too, so plugin-provided scripts and hooks also run from the
tree. Reading `installPath` and concluding the install is frozen is reading the copy nothing serves.

Two consequences of that, worth knowing before editing:

- A session started **afterwards** serves an edited skill or `hooks/hooks.json` with no reinstall,
  no `plugin update` and no version bump. A session already running keeps the configuration it
  started with.
- Only the registered tree is served, so a branch in a git worktree is served **nowhere** until it
  reaches that tree. A change to the procedure cannot be dogfooded from the worktree it was written
  in.

This matters because the toolkit
[builds itself with itself](https://github.com/ragnor-rs/mjolnir/issues/27) — every issue here is
filed, started, finished and reviewed through the loop this repository ships, on the configuration
in [`.claude/mjolnir.yaml`](.claude/mjolnir.yaml).

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
its axes, the tracker port and its capabilities, the work-item facets with their absent
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
| [`tools/check_single_source.py`](tools/check_single_source.py) | The single-authority check, run by the `Checks` workflow on every change |
| [`tools/check_no_project_names.py`](tools/check_no_project_names.py) | The sweep that holds the convention above: no other project named anywhere, and no value, tracker or stack in any carrier root |

The remaining eight roles land here as they are reconciled. A project that has not been migrated
keeps working throughout — that is a safety property of the migration, not an acceptable end state.

## Conventions

**This repository names no *other* project, anywhere, ever** — no repository slug, board or card
id, tracker account, label, milestone, assignee, host, service name, or path under anyone's home
directory. Three things are not that:
[`plugins/mjolnir/config/examples/`](plugins/mjolnir/config/examples/), which is example *data*
rather than procedure and uses placeholders throughout; this repository's own slug and
backlog, which the install command, `.claude/mjolnir.yaml` and the documents cite because the
toolkit [builds itself with itself](https://github.com/ragnor-rs/mjolnir/issues/27); and the two
public artifacts cited as evidence — the plugin cited as
[prior art](docs/configuration-surface.md#prior-art), and the published practice the
[window-as-a-resource measurements](docs/configuration-surface.md#the-window-is-a-resource-the-loop-spends)
are drawn from — each an artifact rather than a project in scope. Nothing under `skills/` carries a value.

That is a **search** rather than a reading of the procedure, and the search is the check:
[`tools/check_no_project_names.py`](tools/check_no_project_names.py) runs in the `Names no other
project` workflow, reads the one permitted slug out of `.claude/mjolnir.yaml` and the forbidden
value set out of the configurations themselves — this project's own included — and holds every
carrier root, whether it holds skills, commands or hooks, to a stricter rule than the rest of the
tree. Its exceptions are in the script, and what it deliberately leaves to a reviewer is in
[`docs/single-source-of-truth.md`](docs/single-source-of-truth.md#the-second-sweep-naming-no-other-project).

Projects referred to in the documentation are lettered A–F. The counts are what carry the argument.

⛔ **The only author is the authenticated user** — here and in every project the toolkit drives.
The [authorship rule](plugins/mjolnir/config/schema.md#authorship-is-procedure-not-configuration)
is the single statement of what that means, why it is procedure rather than a setting, and the
one trap in it.

## License

MIT. See [LICENSE](LICENSE).
