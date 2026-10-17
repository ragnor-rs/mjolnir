# Why the configuration surface has this shape

The reference for *what* the keys are is [`../plugins/mjolnir/config/schema.md`](../plugins/mjolnir/config/schema.md).
This document is *why*. It was derived by reading every copy of every process role across the six
projects that run this pattern — thirty-two of about forty role files in full — and the findings
below are measurements rather than preferences.

Projects are referred to as A–F throughout. Naming them is forbidden here, and the counts are
what carry the argument anyway.

## The pattern is nine roles, not eight

File a work item, **gate it into committed work**, start it, finish it, review it, deploy, log
the day, keep the session's books, produce deliverables.

Gating is a genuine ninth role rather than a variant: one project splits intake into *write the
item* and *gate it into committed work*, and the gate owns the due date and the estimate. The
projects without it fold a little into filing and a little into starting, and neither place sets
a date. The project that has it refuses to let starting re-run it, because re-gating recomputes
a commitment somebody may already have been given.

Depth per project: **1, 7, 7, 8, 9, 9.** Five of six run the whole pattern; one runs a single
role.

## Three findings that reshaped the surface rather than confirming it

### A role's carrier is an axis beside its name

Project B reads as the shallowest adopter at depth 2 and is actually the second deepest. A sweep
of skill directories finds two files; the other six roles are slash commands. **Carrier (skill,
command, hook) is therefore configured independently of role** — otherwise the same undercount
recurs at migration time and that project is declared done with six roles still local.

This also bites inside a skill. A command expands into a transcript record carrying its own
title; a skill injects a preamble naming its directory. Anything matching on those strings
breaks silently when a role's carrier changes, which is why the day log's test file asserts both
directions.

### Name and role diverge in both directions

One role under several names is the expected direction, and it happens: the bookkeeping role
appears under two names, deployment under four across five projects, and one project carries two
differently-named skills for filing and gating.

The reverse also happens, and a name-keyed merge produces nonsense on it:

- **One name, two unrelated roles.** The `deliverables` name is a prose session summary for a
  non-technical reader in one project, and a tab-separated invoice line-item file with an hourly
  rate conversion in two others. Same directory name, different output, different trigger, no
  shared procedure.
- **One name, a subset role.** One project's bookkeeping skill is the *commit third* of the role
  with the board and memory halves absent. Counting it as a full copy overstates adoption;
  counting it as unrelated loses that project's commit behaviour.

So the inventory key is *(role, carrier)*, established by reading the body, and a merge must be
able to say "this copy implements a third of that role".

### A status needs a writer, not only a role

Both the obvious design and the prior art propose a roles map — indirecting the procedure away
from a project's status words. The evidence says a role is not enough: **every bookkeeping copy
independently forbids setting certain states, and names who does set them.**

Writers observed, in the copies' own words: an automation off a merge; a deploy only; the person
who ordered the work; a mechanical path-based sweep where no judgement is needed; and the
procedure itself, which owns only the initial state and the in-flight one.

So a state is configured as `(name, role, writer)` and the procedure is **refused** when it is
not the writer. That turns what read as three contradictory bookkeeping skills into three correct
configurations of one mechanism — including the strictest case, where the procedure may write
nothing at all, because the tracker credential is a person's own account and every write reads as
that person speaking.

Status vocabularies differ in **length and meaning**, not merely wording: three states in one
project, four in another, seven and eight in two more, with a state between review and
completion that some reason about explicitly and others do not have. An absent role is a
legitimate configuration.

## Five axes, not three

1. **Work-item tracker.** Four models were in play — GitHub Projects in three projects, Jira in
   one, Trello in one, and **none** in one, whose work items were entries in a specification tree
   on disk. The port ships with three implementations; the trackerless project moves onto a real
   tracker rather than the toolkit growing a filesystem adapter. **"No tracker configured"
   survives as a supported configuration anyway**, proved against a deliberately trackerless
   scratch config, because the next project to adopt this may have no tracker on its first day.
2. **Code host.** Where branches, pull requests and CI live. The same host in all six, including
   both projects whose cards are elsewhere — which is precisely why it is a separate axis.
3. **Code root.** The path `git` and `gh` address. One project's code is a git-ignored
   subdirectory that is its own repository under a different owner, not a submodule. Its skills
   write the root explicitly into every git call and stop if the directory is absent, because a
   fresh clone of the outer repository does not have it. A skill that takes the top level of the
   repository it is installed in commits the engagement notes and never touches the code; a host
   CLI call inheriting the working directory addresses the wrong repository. **Both fail quietly,
   having done something plausible first.**
4. **Carrier.** Skill, command or hook — see above. Three projects also run process hooks, at
   eight, five and four.
5. **Audience and language, per *artifact* rather than per project.** One project writes its items
   in one language and its repository in another and states the split is by audience; its branch
   slug must be a **translation** of the item title, never a transliteration. One writes the day
   log in a technical register for itself; another writes it in a business register for a reader
   outside the build. Work-item language, repository language, and per-artifact (language,
   register, audience) are separate settings.

## The tracker port

The operations the shared procedure needs, and the shapes the three implementations give them:

| Operation | GitHub Projects | Jira | Trello |
|---|---|---|---|
| Create item | create, add to project, set status | one call | create, then **one label attach per label** — labels cannot be set at creation |
| Read item | one call | one call | one call, **plus a separate call for checklists** |
| Set state | update a field value by project, field and option id | find the transition by name, then transition | move to a list |
| Item number | the item number | the item key | **parsed out of the returned URL** — there is no short-id field |
| Link dependency | a dependencies API keyed on the **internal id, not the number**, posted on the *blocked* item | a link call, with an inward/outward inversion relative to the tracker's own metadata naming | **description links, written at both ends by hand** |
| Close via pull request | a keyword in the body, declarative, on merge | an explicit transition; no closing keyword exists | a bracketed number in the title, and **never a hash**, which would autolink to an unrelated object |
| Comment | one call | one call | **impossible** — no comment action; it goes into the description |
| Delete a checklist item | n/a | n/a | **impossible** — reword and tick instead |

Three consequences for the port:

- **Closing has a declarative implementation and an imperative one.** `link_for_close` and
  `advance_on_merge` are distinct capabilities, either of which may be absent. On one tracker a
  keyword does it on merge; on another an automation does it off a webhook and the procedure must
  *not* do it by hand; on the third there is no link and the item moves separately.
- **Some operations do not exist.** Comment, delete-a-checklist-item, set-labels-atomically and
  assign-a-member are each unavailable on at least one tracker. The port exposes capability
  queries and the procedure has a stated fallback per absence rather than failing. One project's
  skills already do this: a failed gate is written into the description *because* comments are
  impossible there.
- **A write may be forbidden by confidentiality rather than by capability.** One project bars
  source code, credentials, hosting details, file paths and branch names from the tracker,
  because it is a third-party service holding someone else's material. That is a per-project
  **policy on the port**, and it changes what the procedure may put on an item — it is why that
  project's branch name goes in the run report instead.

## Two things are ordered lists of named checks, not procedure

### The readiness gate

The five copies of the starting role **share no single check**. One refuses to start on an open
native blocker and a wrong state; another adds a missing weight and a missing iteration and has
no dependency check at all; another refuses without a sprint, a fix version, and the release
branch for that fix version existing on the remote, and has no state check at all; another runs
eight checks including the item's position in a priority queue.

A fixed sequence would be wrong for every one of them. So the gate is an ordered list of named
predicates drawn from a shared library, each with its own stop message, and **the list runs
whole** — one copy says it outright: an item with four problems should hear about four, not be
bounced once per round trip.

Two subtleties worth carrying:

- **A dependency's bar depends on what the dependency produced.** A code dependency is satisfied
  when its code is on the integration branch; a non-code dependency only when it is finished.
  Requiring the stronger bar of both stops every dependent item on the board.
- **Some failures are not defects.** Two of one project's eight checks mean the item is correct
  and merely early, or that board automation did not fire — so they stop without flagging. A gate
  that flags them flags an item whose author has nothing to fix.

### The day log's exclusions

The sets differ in membership, not merely in length. One project's heaviest exclusion is a
scope-of-engagement rule no other project has, and it is the one that does most of the cutting
there. So the exclusions are an ordered list of named entries drawn from a shared library, which
a project may extend. The default set is a decision, not the only possible one.

## The four facets, and the absent case

Issue type, status, estimate and template are each per-project, and each is carried by a
different mechanism depending on the project. **The failure to design against is a facet that is
absent rather than different** — three of the four have a real absent case, and a procedure that
treats absence as an unset value fails on a project that is correctly configured.

- **Type** — five carriers observed: a native field; a label convention, because a user-owned
  repository on one host has no type field at all; a bare label whose absence means the other
  value; a native field with nine values of which six are used; and a prefixed label mapping onto
  a five-valued branch-type vocabulary. The branch prefix is a **function** of type whose range
  differs — two values in four projects, five in another, with one type resolving to one of two
  prefixes by whether a user can see the change.
- **Estimate** — four carriers plus a designed absence: a board number field on a Fibonacci
  scale asked for at filing; a prefixed label in hours where each rung is the **top of a band**;
  a value on a card; and a project that keeps none, on the recorded grounds that its board has no
  such field, its process tracks readiness rather than velocity, and estimates on a solo build
  would be ceremony. **That absent case is the model for all of them**: it names the workflow the
  estimate came from, why it does not apply, and the condition under which to revisit — a stated
  decision with a trigger, not an unset value.
- **Template** — every copy of the filing role owned its own, which is most of why those copies
  diverged. The procedure genuinely reads sections: one project defines an item as ready to start
  only if it states an outcome, an acceptance check and the seam touched, and cross-checks the
  type label against the template the body uses, because a mismatch surfaces later as a branch
  under the wrong prefix and a branch name is the thing nobody goes back and corrects. Another
  fails a free-prose description however clear, because the structure is what makes it checkable.
  So the procedure names the **semantic** sections and each template declares which of its own
  headings fills each.

## One rule that is procedure everywhere

**An estimate is a bound written before the work; a logged hour is a measurement written after.
Never move a number between them in either direction.** One project states it; it is true in all
of them.

## The strongest argument for extraction is not borrowed

Read-it-from-one-place has been **independently invented six times** across these projects, in
five different stores — a sibling reference file, a reference document, the project instructions
file, a memory index, a memory fact, and the rules file a document checker walks its graph from —
each with the same justification stated in its own words. Two of them put it most sharply:

> a copy that has to be «kept in sync» is the defect rather than the maintenance burden

> Two records of who owns the work that are allowed to disagree are worse than one

The sixth is the most interesting, because it is the only one found **outside** the process roles:
a checker that holds documents to a declared reference graph deliberately reads that graph from the
rules file a person maintains, *so that the graph a machine walks and the statement a person
maintains are one thing*. Same conclusion, reached in a different problem.

Six instances, five stores, one pattern — which is itself an argument for the toolkit picking one.
Convergent evolution rather than a borrowed idea.

## Prior art

A public MIT plugin for an adjacent process — spec-driven development and TDD rather than this
loop — already solves the two hardest parts in the shape proposed here: one directory per tracker
with a template for adding another, and a tracker configuration that is a status list plus a
roles map indirecting the procedure away from the words. That is independent confirmation of the
status design, arrived at separately. It is superseded rather than adopted because of its
adapters: seven entries, of which only two are real trackers, and **neither is one any project
in scope runs**. <https://github.com/nesquikm/dev-process-toolkit>
