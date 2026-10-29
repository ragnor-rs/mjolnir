# mjolnir

### Run your whole development process from one place — without a copy of it in any repository.

Copy a process into a second project and you maintain two. Copy it into a handful and no two are
alike any more, and the lines that differ are the corrections you paid for once and lost
everywhere else. You find out which copy is wrong when it is already wrong.

mjolnir is that process as **one shared procedure over per-project configuration** —
[ten roles](plugins/mjolnir/config/schema.md#the-loop--ten-roles), from filing a work item to
the day's log, reading whatever differs between your projects out of one file you write once.

Installed as a Claude Code plugin. **No clone, no submodule, no symlink, and no copy of the
procedure in your project.** Adopting it in the next project costs that one file you write.

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
templates into your repository as the price of entry. This one asks neither of those: no process to
adopt, and nothing of its own to vendor — only, where your host or your git can read nothing but a
file, that file. Every row below is checkable in the tree it links.

| | |
|---|---|
| **It models the process you already run** | Filing, gating, starting, finishing, reviewing, logging a day. There is no spec artifact to adopt, no phase to pass through, and no persona to learn |
| **Your tracker stays your tracker** | Your statuses, your labels, your ordering, your definition of done — read through a port with a stated fallback for every capability your tracker lacks, rather than replaced by a board of its own ([`§ 3`](plugins/mjolnir/config/schema.md#3-tracker-port)) |
| **Your timesheet stays your timesheet** | Where a day's hours land is a port too, with a store you name and the same stated fallback per capability it lacks — so what measures a day and what reads a period back out of it share one contract instead of a filename convention, and the hours never reach your repository, your tracker or a commit ([`§ 26`](plugins/mjolnir/config/schema.md#26-the-day-logs-destination-port)) |
| **Absence is a configuration, not a failure** | No board, no estimate, no item template, no due date, no priority axis, no tracker at all — each is a stated answer the procedure runs on, with the reason recorded where the key would have been |
| **Nothing of it lives in your repository** | One file you write. No vendored copy, no templates directory, nothing to re-sync when the procedure improves. Where something only your host or your git can read has to be a file, the toolkit writes it rather than asking you to: marked as generated, re-derived from your configuration, and taken back out when you stop asking for it. [What an install may do](plugins/mjolnir/config/schema.md#what-the-toolkit-installs-into-a-project-and-what-takes-it-out) is stated before anything writes one |
| **Your commands, run and reported** | What counts as done is an ordered list of checks you name, each with who answers it ([`§ 13`](plugins/mjolnir/config/schema.md#13-what-counts-as-done--an-ordered-check-list-and-who-answers-each-check)), and which item is next comes from a command you configure ([`§ 12`](plugins/mjolnir/config/schema.md#12-ordering)). Your build, your suites, your ordering argument |
| **A pass that proves nothing is not a pass** | Say what each local check's verdict establishes, the command that defeats a cached one, what it needs before it can run, and which changes its verdict is the one to read for — and a replayed pass, an unmet precondition or a condition nothing could establish is reported rather than counted ([`§ 17`](plugins/mjolnir/config/schema.md#17-the-local-verdict-and-the-conditions-under-which-it-counts)). A project whose host runs nothing still has a definition of done that can be asked |

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
That file is the whole of what adoption costs you to write — there is nothing to vendor and nothing
to keep up to date. Where your host or your git can read nothing but a file, the toolkit writes that
file itself, under
[rules stated before anything writes one](plugins/mjolnir/config/schema.md#what-the-toolkit-installs-into-a-project-and-what-takes-it-out):
marked as generated, byte-identical on a second run, and removed again when your configuration stops
asking for it.

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
| `/mjolnir:save` | Keeps the session's books: your tracker brought current, memory refreshed, then the commit — and the durable artifact a later pass resumes from, with the boundary it was taken at named |
| `/mjolnir:load` | The counterpart: tells you where the work actually stands when you come back to it — the commits nothing outside your tree has, the branch behind the ref its claim is published on, what the last pass was doing and what its compaction dropped, whether a working file that is gone can be replayed and from what. Read-only, and it decides nothing |
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
| [`plugins/mjolnir/skills/save/`](plugins/mjolnir/skills/save/) | Keep the session's books: the thirds your project runs and nothing else, in one order — the tracker current, memory refreshed, the commit staged the way *this* role is configured — with no status whose writer is somebody else, and the artifact a later pass resumes from written before the boundary rather than after it |
| [`plugins/mjolnir/skills/load/`](plugins/mjolnir/skills/load/) | Restore what is in flight at the start of a pass: every reading reported — where the work is, what the item says, what the last pass was doing, what the environment is, what memory claims and what the resumed window states — with the ones it could not take named rather than left out, and nothing fetched, stashed, moved or decided |
| [`plugins/mjolnir/skills/day-report/`](plugins/mjolnir/skills/day-report/) | Build a working day's time-log entry from session transcripts, git, the code host, chat and the calendar |
| [`plugins/mjolnir/config/`](plugins/mjolnir/config/) | The configuration surface: the schema, and a whole example per tracker including a deliberately trackerless one |
| [`plugins/mjolnir/scripts/`](plugins/mjolnir/scripts/) | What a role runs on rather than reimplements: the configuration reader, the one port contract behind both [`schema.md § 3`](plugins/mjolnir/config/schema.md#3-tracker-port) and [`§ 26`](plugins/mjolnir/config/schema.md#26-the-day-logs-destination-port), and the carriers that ship with the surface and run in an adopting project. Which they are is what the directory says, and each one's reach is recorded in [`docs/single-source-of-truth.md`](docs/single-source-of-truth.md) — so no list of them is carried here |
| [`plugins/mjolnir/scripts/adapters/`](plugins/mjolnir/scripts/adapters/) | One implementation of the tracker port per tracker, installed by being there, per [`schema.md § 3`](plugins/mjolnir/config/schema.md#3-tracker-port). Which kinds are built is what the directory says, so no list of them is carried here |
| [`plugins/mjolnir/scripts/destinations/`](plugins/mjolnir/scripts/destinations/) | The same, for where a day's time-log entry is recorded — a second port behind the same contract, per [`schema.md § 26`](plugins/mjolnir/config/schema.md#26-the-day-logs-destination-port). Which directory holds a port's implementations is a marker on the line stating its kind, so neither the toolkit nor this table carries a list |
| [`docs/configuration-surface.md`](docs/configuration-surface.md) | Why the surface has this shape — the measurements behind it, taken by reading every copy of every process role across the six projects |
| [`docs/build-surface.md`](docs/build-surface.md) | The same, for the half the roles do not carry: what the six projects build, check and deploy with, and why so little of it is on the surface |
| [`docs/divergences-and-rulings.md`](docs/divergences-and-rulings.md) | Every divergence found between the old copies and which behaviour was kept, including where a ruling overrode a stated counter-argument |
| [`docs/single-source-of-truth.md`](docs/single-source-of-truth.md) | How the single-authority claim is held: the checks, their kinds, and what each deliberately leaves alone |
| [`docs/building-itself.md`](docs/building-itself.md) | The bootstrap record: which pieces could not be built through the loop, and the command that derives what the loop carries here |
| [`docs/working-on-the-toolkit.md`](docs/working-on-the-toolkit.md) | What **registering this tree** writes, which copy of the plugin a session resolves, and what that costs somebody editing it — a different act from what the toolkit writes into an adopting project, which is the row below |
| [`tools/check_single_source.py`](tools/check_single_source.py) | The single-authority check, run by the `Single source of truth` workflow on every change |
| [`tools/check_no_project_names.py`](tools/check_no_project_names.py) | The sweep that holds the convention above: no other project named anywhere, and no value, tracker or stack in any carrier root |
| [`tools/check_nothing_deferred.py`](tools/check_nothing_deferred.py) | The gate that refuses a merge while any item raised against the change is unresolved, counted in the body and in the threads on it |
| [`tools/check_prose_width.py`](tools/check_prose_width.py) | The sweep that holds every tracked markdown file to the line width the configuration states, excluding the lines the format forbids breaking |
| [`tools/check_no_audit_trail.py`](tools/check_no_audit_trail.py) | The gate that reads the markdown lines a change adds and refuses a dated pass record, a figure beside a former value, or a clause whose subject is the pass before this one |
| [`plugins/mjolnir/hooks/`](plugins/mjolnir/hooks/) | The hook carriers, and what each calls under [`plugins/mjolnir/scripts/`](plugins/mjolnir/scripts/): a `SessionStart` hook putting the rules nothing mechanical reads into the session, a `Stop` hook holding a role's reply to the register, a `PreToolUse` hook refusing a command that would carry a credential onto a surface outside the project, and the guard halves below. Which they are is what the file says, so no count of them is carried here |
| [`plugins/mjolnir/scripts/context.py`](plugins/mjolnir/scripts/context.py) | The context half: a guard that bounds what a call would put into the session's window at the call rather than afterwards — refusing the command whose output your configuration says nothing bounds and naming the bounded form, rewriting the arguments where you stated a flag that bounds it and telling the session it did, replacing a result longer than the size you stated with the path its full text was written to beside a head and a tail, and refusing a read of a file this session has already read and that has not changed since; and a command you named as never bounded is neither refused nor replaced, the read arm being keyed on a path rather than on a command |
| [`plugins/mjolnir/scripts/enforce.py`](plugins/mjolnir/scripts/enforce.py) | The enforcement half: a guard that refuses a merge for which no answer to *is a person going to read this diff* is recorded on the change, naming what would unblock it; a lease that holds a place on whatever your configuration says contends, given back on every exit path that fires and expiring on the one that cannot; and the command that writes the record the guard reads |
| [`plugins/mjolnir/scripts/install.py`](plugins/mjolnir/scripts/install.py) | The install half: the step that writes the artifacts only your host and your git can read, and takes them back out. What it may do, and what it refuses rather than improvise, is [the rule](plugins/mjolnir/config/schema.md#what-the-toolkit-installs-into-a-project-and-what-takes-it-out) — no copy of it is carried here — with what the step's own suite reaches, and what it leaves alone, in [`docs/single-source-of-truth.md`](docs/single-source-of-truth.md#the-install-half-what-the-toolkit-writes-into-a-project) |
| [`plugins/mjolnir/scripts/live.py`](plugins/mjolnir/scripts/live.py) | The live half: a guard that holds a command your configuration says opens a session on another machine, naming the segment, the machine it reaches and the file a name is cleared in — putting it to you where you would answer the prompt and refusing it outright where the session would answer for itself, and passing in silence where the machine is one you named as not live |
| [`plugins/mjolnir/scripts/spend.py`](plugins/mjolnir/scripts/spend.py) | The spend half: a guard that puts a command your configuration says costs money to you on every invocation — or refuses it outright where you said so — naming the segment that spends and what you said it costs, and reading the command's own position in the call rather than the text of it, so a path mentioned in an edit is not a call of anything; and the one price the harness states before a turn runs, reported against a bar you set and reported as *no figure* where it gave none |

The loop's remaining roles land here as they are reconciled. ⛔ **No count of them is written
here** — the table above says which are shipped, and
[`docs/building-itself.md`](docs/building-itself.md) names the command that derives it; a figure in
this sentence is a copy of that, and it had already drifted once. A project that has not been
migrated keeps working throughout — that is a safety property of the migration, not an acceptable
end state.

## Where the rules live

**The single statement of every rule and flow is
[`plugins/mjolnir/config/schema.md`](plugins/mjolnir/config/schema.md)** — the ten-role loop and
its axes, the tracker port and its capabilities, the work-item facets with their absent
cases, the status writers, the readiness gate, what counts as done and who answers each of those
checks, commit behaviour, the day log and the port that says where its entries land, the branch
model, the session's context, the ordering, the memory store and which working directory may
refresh it, and what a role holds and what may cross the boundary out of it.
Everything else written about the procedure, in this repository or on a work item, explains or
records; none of it is a second authority.

That is enforced rather than asserted: the `Single source of truth` workflow holds every document
to it on every change — see [`docs/single-source-of-truth.md`](docs/single-source-of-truth.md)
for the checks and what they deliberately leave alone.

The why sits beside it: [`docs/configuration-surface.md`](docs/configuration-surface.md) holds
the measurements the surface was derived from and
[`docs/build-surface.md`](docs/build-surface.md) those behind what it deliberately leaves to a
project's own commands, while
[`docs/divergences-and-rulings.md`](docs/divergences-and-rulings.md) records every divergence
found between the old copies and the decision that settled it.

## Why this shape, and not a template you copy

This surface was not designed and then justified. Every copy of every process role across the
projects that ran this pattern was read first, and each key here exists because the reading forced
it. What drifted, how far it drifted and the decision that settled each divergence are in
[`docs/divergences-and-rulings.md`](docs/divergences-and-rulings.md), which opens on the
measurement; what each key cost to arrive at is in
[`docs/configuration-surface.md`](docs/configuration-surface.md), section by section, and what the
build half of the same reading settled is in [`docs/build-surface.md`](docs/build-surface.md).

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
carries a value — which since the reply hook means the hooks root as well as the skills
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

⛔ **Who *holds* a role is looked up, and never answered by asking who is running.** The author of a
commit is the authenticated user by the rule above; the dev, the owner and the reviewer are not —
they coincide only while one person runs everything, and a gate that asked the tracker *who am I*
would quietly become *assigned to whoever is asking* and pass every item, including the ones on the
wrong person. So you point at the map you already keep and say how to read an entry, and the toolkit
holds **no name, no handle and no account id**: the
[role-to-person rule](plugins/mjolnir/config/schema.md#27-the-role-to-person-map) is the single
statement of the pointer, the shape, the absent case and the shortcut nothing may take. The survey
behind it found the same map in four stores, each carrying the argument against copying in its own
words — [the measurement](docs/configuration-surface.md#the-role-to-person-map-four-stores-and-one-pointer).

⛔ **A role's reply to the person running it has a fixed register** — procedure too, and for the
same kind of reason. The
[register rule](plugins/mjolnir/config/schema.md#the-reply-to-the-person-running-a-role) is the
single statement of what it requires and why a project does not choose it. It is held in the
session by a hook rather than by the gate, since a reply is not a file; the checks, and what they
leave to a reader, are in
[`docs/single-source-of-truth.md`](docs/single-source-of-truth.md#the-reply-defers-nothing-held-in-the-session-not-on-the-gate).

⛔ **A guard refuses an act on the strength of a record, never on a reading of the work.** Procedure
produces the record and enforcement reads it, so the question *is a person going to read this diff*
is asked and written onto the change whether or not a hook is installed — and where one is, a merge
with no recorded answer is refused, with what would unblock it named in the refusal. The
[enforcement rule](plugins/mjolnir/config/schema.md#what-a-hook-refuses-and-the-record-it-reads) is
the single statement of the record's form and keying,
[which direction a guard fails in](plugins/mjolnir/config/schema.md#which-direction-a-guard-fails-in)
of the two answers to a record it could not read, and
[the lease](plugins/mjolnir/config/schema.md#a-lease-on-an-exclusive-resource-and-the-exit-paths-that-release-it)
of how a place on a contended resource is held and given back. A project that states nothing
exclusive gets no capacity guard at all; what no check can reach is in
[`docs/single-source-of-truth.md`](docs/single-source-of-truth.md#the-enforcement-half-a-guard-that-refuses-and-a-place-that-comes-back).

⛔ **A command that costs money does not run because nobody was there to stop it.** You list the
calls that spend, what each costs and whether a go covers one invocation; the guard reads where the
command *is* in the call — behind an assignment, behind an elevation wrapper, inside a substitution,
in a later segment of a chain — and puts it to you with your own figure attached, so the one
thing it never does is refuse a call that merely mentions the path. A session nobody is watching
gets no answer, and then the call does not run. The
[spend rule](plugins/mjolnir/config/schema.md#19-a-command-that-spends-and-the-supervision-it-is-refused-without)
is the single statement of the list and its keys,
[the command position](plugins/mjolnir/config/schema.md#the-command-position-and-why-the-whole-call-is-not-one)
of the parse and the defect that was paid for once, and
[what an approval is per](plugins/mjolnir/config/schema.md#what-an-approval-is-per-and-the-one-price-stated-before-a-turn-runs)
of the go and of the one price the harness states before a turn runs. A project that denies no
command gets no spend hook at all; what no check can reach is in
[`docs/single-source-of-truth.md`](docs/single-source-of-truth.md#the-spend-half-a-call-put-to-somebody-and-the-one-price-stated-beforehand).

⛔ **Nothing opens a session on your live machine without somebody being asked.** You name the
commands that open one; the machines that are *not* live are named in a file outside every working
tree, so your repository carries the mechanism and your machine carries the names — and on a
machine with no such file yet, every name that file would have cleared reads as live, which is
the safe way round. ⛔ **The
verdict turns on who would answer the prompt**: you get the ask where you would answer it, and
the call is refused outright where the session would answer on its own behalf,
because a prompt a session can clear for itself is not approval. The
[live rule](plugins/mjolnir/config/schema.md#21-a-command-that-could-open-a-session-on-a-live-machine)
is the single statement of the list and its keys,
[which verdict](plugins/mjolnir/config/schema.md#which-verdict-and-who-would-answer-the-prompt)
of the line the whole guard rests on,
[the machines named](plugins/mjolnir/config/schema.md#the-machines-named-are-the-ones-that-are-not-live)
of why the list is inverted and where it lives, and
[the four ways it fails closed](plugins/mjolnir/config/schema.md#the-four-ways-it-fails-closed)
of what a fact it cannot establish does. A project whose commands reach no other machine gets no
live hook at all; what no check can reach is in
[`docs/single-source-of-truth.md`](docs/single-source-of-truth.md#the-live-half-a-session-put-to-somebody-and-the-names-that-clear-one).

⛔ **The window the session thinks in is not spent on a dump nobody wanted.** Summarising a window
is lossy and silent — what it dropped is gone, and nothing left says what was lost — so the lever
is what gets in: you list the commands whose output nothing bounds and what bounds each, and the
call is **rewritten** with your own flag added where one exists, refused with your bounded form
named where none does, and left alone where it already carries a bound of its own. What comes back
longer than the size you stated reaches the window as a path, a head and a tail, with the whole of
it on disk at that path to read the part you need from. And a file this session has already read,
unchanged since, is not read into the window twice. ⛔ **The command you may not truncate is your
list too**: name it, and neither the refusal nor the replacement touches it. The
[context rule](plugins/mjolnir/config/schema.md#22-what-enters-the-window-bounded-where-the-call-is-made)
is the single statement of the list and its keys,
[the three arms](plugins/mjolnir/config/schema.md#the-three-arms-and-the-one-that-rewrites-rather-than-refuses)
of which one rewrites and what the session is told when it does,
[a read already made](plugins/mjolnir/config/schema.md#a-read-this-session-has-already-made)
of what is compared and what releases it,
[the commands never bounded](plugins/mjolnir/config/schema.md#the-commands-a-project-names-as-never-bounded)
of the exemption, and
[why every unestablished fact proceeds](plugins/mjolnir/config/schema.md#why-every-unestablished-fact-here-proceeds)
of the direction it fails in. A project that lists no command and states no size gets no refusal
and no replacement — the read is the one arm that needs no list, and `reread: allow` is how you say
no to it; what no check can reach is in
[`docs/single-source-of-truth.md`](docs/single-source-of-truth.md#the-context-half-a-call-bounded-where-it-is-made-and-what-comes-back).

⛔ **What a session remembers is not quietly written where the next one will never look for it.**
An agent harness names its memory store after the directory the session is standing in, so work in
a per-item tree gets a *different* store: the index every session loads is absent, and a save lands
somewhere the checkout never reads — and nothing says so, because the save reports success. You name
the store once, or you say that the harness decides it and the toolkit must not guess, and the
difference is what you get back: a store you pinned is written from any tree with its index appended
**under a lock**, and a store the harness derives has the memory step **refuse** from a tree and
name the checkout it would have run from. Either way the answer is one of two things a role has to
say out loud rather than a write nobody sees. And what goes in carries where the fact came from and
what it rests on, so a later pass reads a fact it can check instead of restating one. The
[memory rule](plugins/mjolnir/config/schema.md#25-the-memory-store-and-the-tree-a-save-may-refresh-it-from)
is the single statement of the block,
[the carriers](plugins/mjolnir/config/schema.md#the-carriers-and-what-each-of-them-closes)
of what each one closes and what it leaves open,
[write_from](plugins/mjolnir/config/schema.md#write_from-and-the-pair-of-outcomes-a-refusal-is-one-half-of)
of the pair of outcomes, and
[what may enter](plugins/mjolnir/config/schema.md#what-may-enter-the-store-and-what-a-reader-does-with-what-is-in-it)
of the admission. A project that keeps no memory says so with a reason and the step does not run;
what no check can reach is in
[`docs/single-source-of-truth.md`](docs/single-source-of-truth.md#the-memory-store-the-write-decision-and-the-two-arms-on-the-index).

### Who this page is written for

**This page is written to sell the toolkit to whoever is deciding whether to adopt it**, and its
register is a product page's rather than a document's: it leads with what you get, it is meant to
be read in under a minute, and it is the only artifact here written to persuade. What it leaves out
is one hop away — the measurements the surface was derived from in
[`docs/configuration-surface.md`](docs/configuration-surface.md), and what registering this tree
writes in [`docs/working-on-the-toolkit.md`](docs/working-on-the-toolkit.md).

Two things bound the persuasion, and both are the reason it can be trusted at all. **Every claim
above is checkable in this repository**, by reading the surface it links or by running the gate
that holds it; and a measurement this page rests on is cited where that measurement lives rather
than copied here, because a front page is kept while a reply is spent as it is read. No survey
figure appears above: a number a reader cannot check is asserted at them rather than argued.

⚠️ The register [§ 8](plugins/mjolnir/config/schema.md#the-reply-to-the-person-running-a-role)
fixes is a **reply's**, and it forbids exactly this one — persuasive, for an artifact whose reader
a project does not choose. This page's reader is chosen, so that register does not reach it.

That register is a rule rather than a check, and nothing mechanical reads it: a page's prose is
held by whoever writes it. The one thing a check does hold over a role's output is that no work is
named and left undone, which is a property of the work rather than of the writing — stated with the
gate's other limits in
[`docs/single-source-of-truth.md`](docs/single-source-of-truth.md#what-it-deliberately-does-not-check).

## License

MIT. See [LICENSE](LICENSE).
