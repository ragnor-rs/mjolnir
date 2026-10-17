# Why the configuration surface has this shape

The single statement of every rule and flow is
[`../plugins/mjolnir/config/schema.md`](../plugins/mjolnir/config/schema.md); this document
states none. It carries the *why*: it was derived by reading every copy of every process role
across the six projects that run this pattern — thirty-two of about forty role files in full —
and the findings below are measurements rather than preferences. Each one names the schema
section it forced. Where a sentence here reads as a rule, the binding form is the section it
cites.

Projects are referred to as A–F throughout. Naming them is forbidden here, and the counts are
what carry the argument anyway.

## The pattern is nine roles, not eight

The loop's statement is [`schema.md § The loop`](../plugins/mjolnir/config/schema.md#the-loop--nine-roles).
What the survey established is the count: gating is a genuine ninth role rather than a variant.
One project splits intake into *write the item* and *gate it into committed work*, and its gate
copy owns the due date and the estimate; the projects without the role fold a little into filing
and a little into starting, and neither place sets a date. The same project refuses to let
starting re-run the gate — which is where the schema's no-re-gating rule comes from.

Depth per project: **1, 7, 7, 8, 9, 9.** Five of six run the whole pattern; one runs a single
role.

## Three findings that reshaped the surface rather than confirming it

### A role's carrier is an axis beside its name

Project B reads as the shallowest adopter at depth 2 and is actually the second deepest: a sweep
of skill directories finds two files, and the other six roles are slash commands. That undercount
recurring at migration time — the project declared done with six roles still local — is what
forced [`schema.md § 7`](../plugins/mjolnir/config/schema.md#7-carrier).

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

Hence `(name, role, writer)` and the refusal in
[`schema.md § 4.2`](../plugins/mjolnir/config/schema.md#42-status--an-ordered-set-of-name-role-writer).
That design turns what read as three contradictory bookkeeping skills into three correct
configurations of one mechanism — the strictest of them being the project whose tracker
credential is a person's own account, where every write reads as that person speaking, which is
where `writer: never` comes from.

The vocabularies measured differ in **length and meaning**, not merely wording: three states in
one project, four in another, seven and eight in two more, with a state between review and
completion that some reason about explicitly and others do not have.

## Five axes, not three

The axes are stated in
[`schema.md § The loop`](../plugins/mjolnir/config/schema.md#the-loop--nine-roles). The
measurements that forced each to be independent:

1. **Work-item tracker.** Four models were in play — GitHub Projects in three projects, Jira in
   one, Trello in one, and **none** in one, whose work items were entries in a specification tree
   on disk. The port ships with three implementations; the trackerless project moves onto a real
   tracker rather than the toolkit growing a filesystem adapter — and the trackerless case was
   proved against a deliberately trackerless scratch config anyway, because the next project to
   adopt this may have no tracker on its first day.
2. **Code host.** The same host in all six, including both projects whose cards are elsewhere —
   which is precisely why it is a separate axis.
3. **Code root.** One project's code is a git-ignored subdirectory that is its own repository
   under a different owner, not a submodule. Its skills write the root explicitly into every git
   call and stop if the directory is absent, because a fresh clone of the outer repository does
   not have it. The failure mode behind
   [`schema.md § 1`](../plugins/mjolnir/config/schema.md#1-roots--three-independent-paths): a
   skill that takes the top level of the repository it is installed in commits the engagement
   notes and never touches the code; a host CLI call inheriting the working directory addresses
   the wrong repository. Both fail quietly, having done something plausible first.
4. **Carrier.** See above. Three projects also run process hooks, at eight, five and four.
5. **Audience and language.** One project writes its items in one language and its repository in
   another and states the split is by audience — its branch slug a **translation** of the item
   title, never a transliteration. One writes the day log in a technical register for itself;
   another writes it in a business register for a reader outside the build. Three settings, not
   one — hence
   [`schema.md § 8`](../plugins/mjolnir/config/schema.md#8-language-register-audience--per-artifact-not-per-project).

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

Three of these measurements each forced a property of the port, stated in
[`schema.md § 3`](../plugins/mjolnir/config/schema.md#3-tracker-port):

- Closing being declarative on one tracker (a keyword on merge), webhook-automated on another
  (where the procedure must *not* do it by hand) and absent on the third is why `link_for_close`
  and `advance_on_merge` are separate capabilities.
- Comment, delete-a-checklist-item, set-labels-atomically and assign-a-member each missing on at
  least one tracker is why capabilities are queried with a stated fallback per absence. One
  project's skills already did this: a failed gate written into the description *because*
  comments are impossible there.
- One project barring source code, credentials, hosting details, file paths and branch names from
  a third-party tracker holding someone else's material is why policy sits on the port beside
  capability — and why that project's branch name goes in the run report instead.

## Two things are ordered lists of named checks, not procedure

### The readiness gate

The five copies of the starting role **share no single check**. One refuses to start on an open
native blocker and a wrong state; another adds a missing weight and a missing iteration and has
no dependency check at all; another refuses without a sprint, a fix version, and the release
branch for that fix version existing on the remote, and has no state check at all; another runs
eight checks including the item's position in a priority queue.

A fixed sequence would be wrong for every one of them — hence the ordered predicate list in
[`schema.md § 5`](../plugins/mjolnir/config/schema.md#5-readiness-gate--an-ordered-predicate-list),
each of whose three rules traces to one copy: *the list runs whole* is one copy's own statement
that an item with four problems should hear about four, not be bounced once per round trip; the
two-bar dependency check is the copy that distinguished a code dependency (satisfied on the
integration branch) from a non-code one (satisfied only when finished); and `stop_quietly` is
the project whose eight checks include two that stop on an item which is correct and merely
early, or whose board automation did not fire — an author with nothing to fix must not be
flagged.

### The day log's exclusions

The sets differ in membership, not merely in length. One project's heaviest exclusion is a
scope-of-engagement rule no other project has, and it is the one that does most of the cutting
there — hence the named, extensible list in
[`schema.md § 9`](../plugins/mjolnir/config/schema.md#9-day-log), whose default set is a
decision rather than the only possible one.

## The four facets, and the absent case

Issue type, status, estimate and template
([`schema.md § 4`](../plugins/mjolnir/config/schema.md#4-work-item-facets)) are each per-project,
and each was carried by a different mechanism depending on the project. Three of the four had a
real absent case — which is where the schema's absence-is-a-configuration rule comes from: a
procedure that treats absence as an unset value fails on a project that is correctly configured.

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
  Hence the semantic-section map in
  [`schema.md § 4.4`](../plugins/mjolnir/config/schema.md#44-template).

## One rule that is procedure everywhere

The estimate/measurement separation in
[`schema.md § 4.3`](../plugins/mjolnir/config/schema.md#43-estimate) — a bound written before
the work against a measurement written after, with a number never moving between them — is
stated by one project and true in all of them: the single rule the survey found already
universal.

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
