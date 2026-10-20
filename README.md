# mjolnir

The development process — [nine roles](plugins/mjolnir/config/schema.md#the-loop--nine-roles), from
filing a work item to the day's log — as **one shared procedure over per-project configuration**.

Installed as a Claude Code plugin. No clone, no submodule, no symlink, and no copy of anything in
the adopting project.

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

## Invocation

Skills are addressed **namespaced, with no alias**:

```
/mjolnir:file-work-item
/mjolnir:gate-work-item
/mjolnir:start
/mjolnir:finish
/mjolnir:review
/mjolnir:day-report
```

The rule, and why it is procedure rather than a setting, is
[`schema.md § 7`](plugins/mjolnir/config/schema.md#invocation).

## What is in it

| | |
|---|---|
| [`plugins/mjolnir/skills/file-work-item/`](plugins/mjolnir/skills/file-work-item/) | Turn a request into work items: the split confirmed, a three-layer duplicate check with a human gate, the parent case where the request is a piece of an open item, and the body rendered from the project's own template |
| [`plugins/mjolnir/skills/gate-work-item/`](plugins/mjolnir/skills/gate-work-item/) | Gate a work item into committed work: the project's own checks run whole on an item somebody else wrote, who repairs what failed asked once, and then the two things written here and nowhere else — the estimate and the date — before the item is admitted |
| [`plugins/mjolnir/skills/start/`](plugins/mjolnir/skills/start/) | Take a work item: the one named or the next the project's ordering offers, the readiness gate run whole, the claim published as the item's ref, and the branch cut into a tree the session then works in |
| [`plugins/mjolnir/skills/finish/`](plugins/mjolnir/skills/finish/) | Take a finished branch to a landed pull request: the commit, the push, the pull request, the host's answer about it, what the project counts as done and who answers each of those checks, the merge read back from state, the item's move through the port, and the tree released |
| [`plugins/mjolnir/skills/review/`](plugins/mjolnir/skills/review/) | Review an open change and drive its gate green: the conversation read first, the diff read whatever else reads it, every finding reproduced and fixed under the same item, every thread answered, and a record of whether a person is going to look — which this role writes and never acts on |
| [`plugins/mjolnir/skills/day-report/`](plugins/mjolnir/skills/day-report/) | Build a working day's time-log entry from session transcripts, git, the code host, chat and the calendar |
| [`plugins/mjolnir/config/`](plugins/mjolnir/config/) | The configuration surface: the schema, and a whole example per tracker including a deliberately trackerless one |
| [`plugins/mjolnir/scripts/`](plugins/mjolnir/scripts/) | What a role runs on rather than reimplements: the configuration reader, and the tracker port behind [`schema.md § 3`](plugins/mjolnir/config/schema.md#3-tracker-port) |
| [`plugins/mjolnir/scripts/adapters/`](plugins/mjolnir/scripts/adapters/) | One implementation of that port per tracker, installed by being there, per [`schema.md § 3`](plugins/mjolnir/config/schema.md#3-tracker-port). Which kinds are built is what the directory says, so no list of them is carried here |
| [`docs/configuration-surface.md`](docs/configuration-surface.md) | Why the surface has this shape — the measurements behind every schema section |
| [`docs/divergences-and-rulings.md`](docs/divergences-and-rulings.md) | Every divergence found between the old copies and which behaviour was kept, including where a ruling overrode a stated counter-argument |
| [`docs/single-source-of-truth.md`](docs/single-source-of-truth.md) | How the single-authority claim is held: the checks, their kinds, and what each deliberately leaves alone |
| [`docs/building-itself.md`](docs/building-itself.md) | The bootstrap record: which pieces could not be built through the loop, and the command that derives what the loop carries here |
| [`docs/working-on-the-toolkit.md`](docs/working-on-the-toolkit.md) | What an install writes, which copy of the plugin a session resolves, and what that costs somebody editing this tree |
| [`tools/check_single_source.py`](tools/check_single_source.py) | The single-authority check, run by the `Single source of truth` workflow on every change |
| [`tools/check_no_project_names.py`](tools/check_no_project_names.py) | The sweep that holds the convention above: no other project named anywhere, and no value, tracker or stack in any carrier root |
| [`tools/check_nothing_deferred.py`](tools/check_nothing_deferred.py) | The gate that refuses a merge while any item raised against the change is unresolved, counted in the body and in the threads on it |
| [`tools/check_prose_width.py`](tools/check_prose_width.py) | The sweep that holds every tracked markdown file to the line width the configuration states, excluding the lines the format forbids breaking |
| [`tools/check_no_audit_trail.py`](tools/check_no_audit_trail.py) | The gate that reads the markdown lines a change adds and refuses a dated pass record, a figure beside a former value, or a clause whose subject is the pass before this one |
| [`plugins/mjolnir/hooks/`](plugins/mjolnir/hooks/) | The hook carriers, and what each calls under [`plugins/mjolnir/scripts/`](plugins/mjolnir/scripts/): a `Stop` hook holding a role's reply to the register, and a `PreToolUse` hook refusing a command that would carry a credential onto a surface outside the project |

The loop's remaining roles land here as they are reconciled. ⛔ **No count of them is written
here** — the table above says which are shipped, and
[`docs/building-itself.md`](docs/building-itself.md) names the command that derives it; a figure in
this sentence is a copy of that, and it had already drifted once. A project that has not been
migrated keeps working throughout — that is a safety property of the migration, not an acceptable
end state.

## Where the rules live

**The single statement of every rule and flow is
[`plugins/mjolnir/config/schema.md`](plugins/mjolnir/config/schema.md)** — the nine-role loop and
its axes, the tracker port and its capabilities, the work-item facets with their absent
cases, the status writers, the readiness gate, what counts as done and who answers each of those
checks, commit behaviour, the day log, the branch model, the session's context, the ordering, and
what a role holds and what may cross the boundary out of it.
Everything else written about the procedure, in this repository or on a work item, explains or
records; none of it is a second authority.

That is enforced rather than asserted: the `Single source of truth` workflow holds every document
to it on every change — see [`docs/single-source-of-truth.md`](docs/single-source-of-truth.md)
for the checks and what they deliberately leave alone.

The why sits beside it: [`docs/configuration-surface.md`](docs/configuration-surface.md) holds
the measurements the surface was derived from, and
[`docs/divergences-and-rulings.md`](docs/divergences-and-rulings.md) records every divergence
found between the old copies and the decision that settled it.

## Why one procedure over configuration

One procedure copied per project drifts, and a line that differed was sometimes a correction only
one copy had. What drifted, how far it drifted and the decision that settled each divergence are in
[`docs/divergences-and-rulings.md`](docs/divergences-and-rulings.md), which opens on the
measurement.

Only a closed set of facts actually differs between projects. Those facts belong in
configuration, and the procedure belongs in one place.

The argument is not borrowed: read-it-from-one-place had already been independently invented
across those projects, in several different stores
([the instances](docs/configuration-surface.md#the-strongest-argument-for-extraction-is-not-borrowed)),
each time with the same justification in its own words —

> a copy that has to be «kept in sync» is the defect rather than the maintenance burden

## Working on the toolkit itself

A plugin installed from a GitHub marketplace is a **clone**, so editing this tree changes nothing a
session serves. Register the tree itself as the marketplace instead, at **user scope**:

```
claude plugin marketplace add /path/to/this/repo --scope user
claude plugin install mjolnir@mjolnir --scope user
```

What those commands write, and which copy of the plugin a session resolves, are in
[`docs/working-on-the-toolkit.md`](docs/working-on-the-toolkit.md).

This matters because the toolkit
[builds itself with itself](https://github.com/ragnor-rs/mjolnir/issues/27) — every issue here is
filed, started, finished and reviewed through the loop this repository ships, on the configuration
in [`.claude/mjolnir.yaml`](.claude/mjolnir.yaml).

## Conventions

**This repository names no *other* project, anywhere, ever** — no repository slug, board or card
id, tracker account, label, milestone, assignee, host, service name, or path under anyone's home
directory. Three things are not that:
[`plugins/mjolnir/config/examples/`](plugins/mjolnir/config/examples/), which is example *data*
rather than procedure and uses placeholders throughout; this repository's own slug and
backlog, which the install command, `.claude/mjolnir.yaml` and the documents cite because the
toolkit [builds itself with itself](https://github.com/ragnor-rs/mjolnir/issues/27); and the
public artifacts cited as evidence — the plugin cited as
[prior art](docs/configuration-surface.md#prior-art), and the published practice the
[window-as-a-resource measurements](docs/configuration-surface.md#the-window-is-a-resource-the-loop-spends)
are drawn from — each an artifact rather than a project in scope. Nothing under a carrier root
carries a value — which since the reply-register hook means the hooks root as well as the skills
one.

That is a **search** rather than a reading of the procedure, and the search is the check:
[`tools/check_no_project_names.py`](tools/check_no_project_names.py) runs in the `Names no other
project` workflow, reads the one permitted slug out of `.claude/mjolnir.yaml` and the forbidden
value set out of the configurations themselves — this project's own included — and holds every
carrier root, whether it holds skills, commands or hooks, to a stricter rule than the rest of the
tree. Its exceptions are in the script, and what it deliberately leaves to a reviewer is in
[`docs/single-source-of-truth.md`](docs/single-source-of-truth.md#the-second-sweep-naming-no-other-project).

⛔ **Nothing is deferred.** A role that reaches a question it cannot answer asks, with the options
stated, rather than noting it and carrying on; and no change merges carrying an item raised
against it. The
[completeness rule](plugins/mjolnir/config/schema.md#nothing-is-deferred) is the single statement
of it, the exception for genuinely separate work, and the test that tells the two apart. It is
held by the `Nothing deferred` workflow rather than by a reviewer noticing, and what it
deliberately leaves to a reviewer is in
[`docs/single-source-of-truth.md`](docs/single-source-of-truth.md#the-gate-on-the-change-nothing-is-deferred)
— a comment finding, a `None.` that is not true, and the closing half of the rule.

⛔ **Prose here wraps at the width this repository's own configuration states, and nothing
written to the host is wrapped at all.** The
[width rule](plugins/mjolnir/config/schema.md#prose-line-width) is the single statement of which
surface answers how, what it excludes and why one half is configuration while the other is
procedure. The files half is held by the `Prose width` workflow, reading the width from
`.claude/mjolnir.yaml` rather than carrying one; the bodies half is held by nobody, which is
stated with the check in
[`docs/single-source-of-truth.md`](docs/single-source-of-truth.md#prose-line-width-held-on-the-gate-for-files-and-nowhere-for-bodies).

⛔ **An artifact states what is true now, and carries no record of the pass that wrote it unless
somebody asked for one.** The
[audit-trail rule](plugins/mjolnir/config/schema.md#an-artifact-states-what-is-true-now) is the
single statement of the four forbidden shapes, the ask that is the exception, and why the past is
left alone. A stale line is replaced rather than annotated, and what a pass did goes in the reply.
It is held on the lines a change adds by the `No audit trail` workflow; what that cannot reach —
the ordering document the habit was measured on and the day log, both outside every tree — is
stated with the check in
[`docs/single-source-of-truth.md`](docs/single-source-of-truth.md#an-artifact-states-what-is-true-now-held-on-the-lines-a-change-adds).

⛔ **The only author is the authenticated user** — here and in every project the toolkit drives.
The [authorship rule](plugins/mjolnir/config/schema.md#authorship-is-procedure-not-configuration)
is the single statement of what that means, why it is procedure rather than a setting, and the
one trap in it.

⛔ **A role's reply to the person running it has a fixed register** — procedure too, and for the
same kind of reason. The
[register rule](plugins/mjolnir/config/schema.md#the-reply-to-the-person-running-a-role) is the
single statement of what it requires and why a project does not choose it. It is held in the
session by a hook rather than by the gate, since a reply is not a file; the checks, and what they
leave to a reader, are in
[`docs/single-source-of-truth.md`](docs/single-source-of-truth.md#the-replys-register-held-in-the-session-not-on-the-gate).

### Who this page is written for

**This page is written for whoever is deciding whether to adopt the toolkit into a project of their
own.** What it leaves out is one hop away: the measurements the surface was derived from in
[`docs/configuration-surface.md`](docs/configuration-surface.md), and what an install writes in
[`docs/working-on-the-toolkit.md`](docs/working-on-the-toolkit.md).

Its register is what a kept page needs and a reply does not: a measurement this page rests on is
cited where that measurement lives rather than copied here, because a reply is spent as it is read
and a front page is not. Whether the density properties
[§ 8](plugins/mjolnir/config/schema.md#the-reply-to-the-person-running-a-role) fixes for a reply
reach prose written into a file at all is
[#126](https://github.com/ragnor-rs/mjolnir/issues/126)'s question, and is not answered here.

Both halves are a convention of this repository and not a rule of the procedure: the README is not
one of the artifacts § 8's `artifacts` map names, and no check holds either half — stated with the
gate's other limits in
[`docs/single-source-of-truth.md`](docs/single-source-of-truth.md#what-it-deliberately-does-not-check).

## License

MIT. See [LICENSE](LICENSE).
