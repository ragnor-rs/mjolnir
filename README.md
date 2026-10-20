# mjolnir

### Run your whole development process from one place — without a copy of it in any repository.

Copy a process into a second project and you maintain two. Copy it into a handful and no two are
alike any more, and the lines that differ are the corrections you paid for once and lost
everywhere else. You find out which copy is wrong when it is already wrong.

mjolnir is that process as **one shared procedure over per-project configuration** —
[nine roles](plugins/mjolnir/config/schema.md#the-loop--nine-roles), from filing a work item to
the day's log, reading whatever differs between your projects out of one file you write once.

Installed as a Claude Code plugin. **No clone, no submodule, no symlink, and no copy of anything in
your project.** Adopting it in the next project costs that one file and nothing else.

```
/plugin marketplace add ragnor-rs/mjolnir
/plugin install mjolnir@mjolnir
```

## What you get

- **A correction lands once.** Fix how finishing works and every project that reads this procedure
  has it — because there is no second copy to keep in sync.
- **Your facts stay yours, and they are a closed set.** Tracker, code host, branch model, what
  counts as done, who answers each check, the ordering, the language. One file, every key
  [stated once](plugins/mjolnir/config/schema.md).
- **The loop carries the item, so you are not the one holding it.** The session that starts an item
  finishes it, the pass that finishes it reviews it, and each leg is entered on a stated condition
  rather than on being asked — [§ The loop](plugins/mjolnir/config/schema.md#what-carries-the-item-forward-and-where-it-stops-to-ask).
- **It refuses rather than hopes.** A claim on a work item is a published ref that git itself
  refuses to duplicate; a merge is read back from the host's state, never from an exit status; an
  absent tracker capability has a stated fallback instead of an improvisation.
- **Work cannot be quietly dropped.** No change merges while an item raised against it is
  unresolved, counted in the body and in the review threads by a gate rather than by whoever is
  keen to merge.
- **It already runs on itself.** Every issue in this repository is filed, started, finished and
  reviewed through the loop this repository ships, and every change is held by
  [the gates you can watch run](https://github.com/ragnor-rs/mjolnir/actions) — so the first thing
  standing on this surface is the thing that finds its holes.
- **Adopt what you have.** A tracker with no board and no status field, or no tracker at all, are
  configurations the surface covers rather than cases it refuses.

## Where this is different

A toolkit that hands you a **process of its own** — a spec lifecycle, a phase gate, a set of named
agent personas — asks your project to adopt that process, and usually writes its directories and
templates into your repository as the price of entry. This one does neither, and every row below
is checkable in the tree it links.

| | |
|---|---|
| **It models the process you already run** | Filing, gating, starting, finishing, reviewing, logging a day. There is no spec artifact to adopt, no phase to pass through, and no persona to learn |
| **Your tracker stays your tracker** | Your statuses, your labels, your ordering, your definition of done — read through a port with a stated fallback for every capability your tracker lacks, rather than replaced by a board of its own ([`§ 3`](plugins/mjolnir/config/schema.md#3-tracker-port)) |
| **Absence is a configuration, not a failure** | No board, no estimate, no item template, no due date, no tracker at all — each is a stated answer the procedure runs on, with the reason recorded where the key would have been |
| **Nothing of it lives in your repository** | One file you write. No vendored copy, no templates directory, nothing to re-sync when the procedure improves |
| **Your commands, run and reported** | What counts as done is an ordered list of checks you name, each with who answers it ([`§ 13`](plugins/mjolnir/config/schema.md#13-what-counts-as-done--an-ordered-check-list-and-who-answers-each-check)), and which item is next comes from a command you configure ([`§ 12`](plugins/mjolnir/config/schema.md#12-ordering)). Your build, your suites, your ordering argument |

So it is not a spec-driven kit. It ships no spec format, no test taxonomy and no opinion about your
architecture. What it does is make the loop *around* that work the same in every project, and hold
it there.

## Install

**What you need:** Claude Code, `python3` on your `PATH`, and PyYAML — which the configuration
reader uses to read your one file, and will tell you to install if it is missing
(`python3 -m pip install pyyaml`). Nothing else: no CLI to install, no package manager of its own,
and no runtime added to your project.

Two commands above, then one file. Write your project's own facts into `.claude/mjolnir.yaml`:
start from whichever of
[`plugins/mjolnir/config/examples/`](plugins/mjolnir/config/examples/) matches your tracker, and
[`plugins/mjolnir/config/schema.md`](plugins/mjolnir/config/schema.md) says what every key means.
That file is the whole of what adoption costs — there is nothing to vendor and nothing to keep up
to date.

## What you type

Skills are addressed **namespaced, with no alias** — the rule, and why it is procedure rather than
a setting, is [`schema.md § 7`](plugins/mjolnir/config/schema.md#invocation).

| | |
|---|---|
| `/mjolnir:file-work-item` | Turns a request — or a chat log — into well-formed items, checked against everything your tracker already holds and related to what they block |
| `/mjolnir:gate-work-item` | Runs your own readiness checks whole on an item somebody else wrote, and admits it to committed work |
| `/mjolnir:start` | Takes the next item your ordering makes available, claims it where a sibling session cannot take it twice, and cuts its branch into its own tree |
| `/mjolnir:finish` | Commits, pushes, opens the change, reads the host's answer about it, asks before merging, and releases the tree once the merge is read back from state |
| `/mjolnir:review` | Reads the conversation, reads the diff, reproduces what it finds, fixes it under the same item, and drives the gate green |
| `/mjolnir:day-report` | Builds a day's time-log entry from session transcripts, git, the host, chat and the calendar |

You type the first one, and the loop carries the item from there: `start` hands the finished branch
to `finish`, which enters `review` on the open change, which comes back to `finish` for the merge.
Each hand-off happens on a stated condition rather than on being asked, and the two places it stops
to ask you are stated too —
[§ The loop](plugins/mjolnir/config/schema.md#what-carries-the-item-forward-and-where-it-stops-to-ask).

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

## Why this shape, and not a template you copy

This surface was not designed and then justified. Every copy of every process role across the
projects that ran this pattern was read first, and each key here exists because the reading forced
it. What drifted, how far it drifted and the decision that settled each divergence are in
[`docs/divergences-and-rulings.md`](docs/divergences-and-rulings.md), which opens on the
measurement; what each key cost to arrive at is in
[`docs/configuration-surface.md`](docs/configuration-surface.md), section by section.

Only a closed set of facts actually differs between projects. Those facts belong in
configuration, and the procedure belongs in one place.

The argument is not borrowed: read-it-from-one-place had already been independently invented
across those projects, in several different stores
([the instances](docs/configuration-surface.md#the-strongest-argument-for-extraction-is-not-borrowed)),
each time with the same justification in its own words —

> a copy that has to be «kept in sync» is the defect rather than the maintenance burden

That is the sentence this toolkit is built to make unnecessary.

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

**This page is written to sell the toolkit to whoever is deciding whether to adopt it**, and its
register is a product page's rather than a document's: it leads with what you get, it is meant to
be read in under a minute, and it is the only artifact here written to persuade. What it leaves out
is one hop away — the measurements the surface was derived from in
[`docs/configuration-surface.md`](docs/configuration-surface.md), and what an install writes in
[`docs/working-on-the-toolkit.md`](docs/working-on-the-toolkit.md).

Two things bound the persuasion, and both are the reason it can be trusted at all. **Every claim
above is checkable in this repository**, by reading the surface it links or by running the gate
that holds it; and a measurement this page rests on is cited where that measurement lives rather
than copied here, because a front page is kept while a reply is spent as it is read. No survey
figure appears above: a number a reader cannot check is asserted at them rather than argued.

⚠️ The register [§ 8](plugins/mjolnir/config/schema.md#the-reply-to-the-person-running-a-role)
fixes is a **reply's**, and it forbids exactly this one — persuasive, for an artifact whose reader
a project does not choose. This page's reader is chosen, so that register does not reach it. What
does reach it is the
[floor](plugins/mjolnir/config/schema.md#the-floor-under-prose-a-role-writes-into-a-file) under
every file: three properties of the text that hold whatever register is chosen over it, and a page
written to persuade can carry all three.

Both halves are a convention of this repository and not a rule of the procedure: the README is not
one of the artifacts § 8's `artifacts` map names, and no check holds either half — stated with the
gate's other limits in
[`docs/single-source-of-truth.md`](docs/single-source-of-truth.md#what-it-deliberately-does-not-check).

## License

MIT. See [LICENSE](LICENSE).
