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

## The axes, and why each is independent

The axes are stated in
[`schema.md § The loop`](../plugins/mjolnir/config/schema.md#the-loop--nine-roles) — which
carries the list, and no count, so this document does not hold a copy of one. There are more than
the three that are obvious. The measurements that forced each to be independent:

1. **Work-item tracker.** Four models were in play — GitHub Projects in three projects, Jira in
   one, Trello in one, and **none** in one, whose work items were entries in a specification tree
   on disk. The port's implementations are one module per kind, built as their items land; the
   trackerless project moves onto a real tracker rather than the toolkit growing a filesystem
   adapter — and the trackerless case was
   proved against a deliberately trackerless scratch config anyway, because the next project to
   adopt this may have no tracker on its first day.
2. **Code host.** The same host in all six, including both projects whose cards are elsewhere —
   which is precisely why it is a separate axis. The host's own runs later forced a facet inside
   the axis, [`schema.md § 2`](../plugins/mjolnir/config/schema.md#2-code-host): one project's
   guard, keyed on job names, refused a build on the strength of a check that only validated a
   title — two unrelated workflows had named their job identically — and the same project measured
   a conflicted pull request producing **zero** runs, which reads as green to anything that treats
   an empty check list as a pass. Hence `checks` keyed by workflow name, with
   absence-of-signal-is-not-an-answer stated beside it.

   **A second facet landed inside the same axis later, and it was measured here rather than in the
   survey.** How a pull request lands — squash, a merge commit, or rebase — was read in three
   places in this backlog and decided in none of them: the role that performs the merge, the
   commit-message hook that has to survive a concatenated message, and the role that prunes a
   landed tree and deletes its branch.

   ⚠️ **The item's own zero-hits measurement was true when it was taken and false by the time it
   was acted on**, which is recorded rather than restated, being an instance of the thing this
   document keeps catching. On 2026-10-17, at `f40785e`, `squash`, `merge_method` and `linear`
   returned **zero** hits across the surface, this repository's configuration, every document under
   `docs/` and every file under `config/examples/`. Two days later, at `756ab7a`, `squash` matched
   six lines in those same files. ⛔ **Not one of the six states the fact**, which is why the gap
   survived its own measurement going stale: every one is the landed reading explaining why a
   rewritten hash defeats ancestry — the one reader this facet does not simplify — and no key, and
   no sentence anywhere, said which method a project lands by.

   ⚠️ **Three rather than the four the item claimed, and the direction of the defect was not
   uniform either** — recorded because the correction is the kind of thing this document exists to
   keep honest. Re-read against the bodies themselves, two of the item's four quotations were
   attributed to the wrong items, and the fourth item reads the method nowhere: its single mention
   is the cost of a full loop for a one-line fix, which reads no input. Of the three that do read
   it, only two *tolerated* both shapes; the merging role silently **assumed** squash, which is the
   worse half of the same gap and the one a tolerant reading hides.

   Two measurements on this repository, 2026-10-17 and re-read 2026-10-19, are why the key exists
   rather than the argument above:

   - **A landing picked a method with nothing to read.** `main` was linear and the previous change
     had landed as a single commit, so squash was inferred. A linear history is equally consistent
     with rebase, so the inference was a coin toss that read as a reading. ⚠️ **It happened to be
     right, and what establishes that is not the shape it was read off**: a branch of six commits
     and one of three each added **exactly one** commit to a `main` that carries no merge commit
     at all, which a rebase merge cannot do and a merge commit cannot do either. So the convention
     was in the history to be read correctly, and nothing said it.

     ⚠️ **The first attempt at that evidence was wrong, and wrong in the direction this whole
     document is about.** It read the `(#N)` suffix on 26 of the 33 commits as the host's own
     squash marker. It is nothing of the kind: this project's finishing role **passes** that
     subject itself, precisely because a host appends the reference only to a subject it generates
     — so the suffix is evidence of the convention and not of the merge method. The seven commits
     without it are not the exceptions it implied either: six predate the loop running on itself,
     and one is a merged pull request whose subject was passed without its reference, which is the
     defect the finishing role's squash-subject rule exists for, sitting unnoticed in the history
     of the repository that states the rule.
   - **The host constrains nothing.** `allow_squash_merge`, `allow_merge_commit` and
     `allow_rebase_merge` are all true, and `delete_branch_on_merge` is false — so every method is
     available, nothing on the host enforces the convention the history implies, and the branch
     deletion that *looks* like the host's job is nobody's until a project says whose it is.

   Hence [`schema.md § 2 → How a pull request lands`](../plugins/mjolnir/config/schema.md#how-a-pull-request-lands),
   which also rules what the host's own setting is for: read from the host as a constraint on the
   stated method, never restated as a second copy of it. ⚠️ **What the same measurement does not
   support is the facet making the landed reading cheaper**, which was the obvious reason to want
   it: that reading keeps both of its tests, for the reason the section gives.
3. **Code root.** One project's code is a git-ignored subdirectory that is its own repository
   under a different owner, not a submodule. Its skills write the root explicitly into every git
   call and stop if the directory is absent, because a fresh clone of the outer repository does
   not have it. The failure mode behind
   [`schema.md § 1`](../plugins/mjolnir/config/schema.md#1-roots):
   a skill that takes the top level of the repository it is installed in commits the engagement
   notes and never touches the code; a host CLI call inheriting the working directory addresses
   the wrong repository. Both fail quietly, having done something plausible first.

   **The same section's other root was measured here rather than in the survey, and it is the one
   root the surface cannot carry.** The shared reader resolves `.claude/mjolnir.yaml` against the
   skills root, so that root is needed before any configuration can be read. Every in-band
   candidate was tried:

   | Candidate | Measured outcome |
   |---|---|
   | `${CLAUDE_PROJECT_DIR}` | not set in the environment a skill's command runs in |
   | `${CLAUDE_PLUGIN_ROOT}` | the plugin's own location — outside the project entirely under a user-scope install |
   | the repository top level, from the version-control tool | wrong wherever the two roots differ — which is why the rule above bars it for the code root |
   | a key on this surface | inside the file the key is needed to find |

   So it is stated as a definition rather than configured —
   [`schema.md § 1 → The skills root is where the role runs`](../plugins/mjolnir/config/schema.md#the-skills-root-is-where-the-role-runs).
   The key that used to declare it carried `"."` in every configuration and was read by nothing:
   declared and dead, which is worse than absent, because a project that pointed it at a
   subdirectory was ignored in silence. The costs are accepted with it and are stated in that
   section rather than here — the naming requirement being a statement rather than a stop, and
   the argument form staying, because a role has to be able to address a project it is not
   standing in.
4. **Carrier.** See above. Three projects also run process hooks, at eight, five and four.
5. **Audience and language.** One project writes its items in one language and its repository in
   another and states the split is by audience — its branch slug a **translation** of the item
   title, never a transliteration. One writes the day log in a technical register for itself;
   another writes it in a business register for a reader outside the build. Three settings, not
   one — hence
   [`schema.md § 8`](../plugins/mjolnir/config/schema.md#8-language-register-audience--per-artifact-not-per-project).
   A seventh setting landed in the same axis later, measured rather than stated by any project:
   [prose width](#prose-width-is-a-habit-and-the-habits-differ).

   **One artifact in that map is fixed rather than configured.** The measurement that forced it
   is an absence: the reply a role writes in the session is an artifact like the day log, and for
   several roles the only output, and **no copy of any role in the survey stated its register** —
   not one of the thirty-two read in full, and nothing in the surface either. Where every other
   artifact above was carried three or four different ways by different projects, this one was
   carried nowhere, so there was no divergence to reconcile and nothing to make configurable
   from.

   ⚠️ **The evidence for what to put there instead is of a different kind from the rest of this
   document, and that is worth naming.** It is not a count across projects A–F: it is the stated
   requirement of the person the replies are written to, recorded on
   [#79](https://github.com/ragnor-rs/mjolnir/issues/79) in their own words. The first entry here
   whose argument a count does not carry. Why that still settles it as *procedure* rather than as
   a setting is the rule's own, at
   [`schema.md § 8 → The reply to the person running a role`](../plugins/mjolnir/config/schema.md#the-reply-to-the-person-running-a-role),
   which this document does not restate.
6. **Branch model.** Four of the six cut a working tree per work item; two never do. Even the
   two that do not are not indifferent to it: one of them carries a day-log caveat — already in
   the shipped skill — that a session opened in a worktree *the configuration cannot reach*
   writes its transcripts elsewhere and is invisible to the evidence script, so the day comes out
   under-measured and is reported as under-measured rather than silently short.
   The split alone would make this configuration. What makes it an **axis** is that in two of the
   four it is stated in no one place and the layers that read it disagree: the starting role
   aborts on a dirty tree — the in-place behaviour — while the same project's hooks exist to
   manage parallel worktrees and the resources those trees contend for. A third project's
   starting role states the opposite rule in its own words, naming the dated incident that forced
   it: a `git checkout` in the shared clone switched it off the branch another session was
   mid-flight on. See
   [`schema.md § 10`](../plugins/mjolnir/config/schema.md#10-branch-model).

   The measurements that gave § 10 its shape rather than merely its existence:

   - **The mechanism is already extracted in one project and is not a skill.** A reference file
     carries the routing, the setup steps and the teardown, and its own rule is
     read-it-from-one-place again: a skill on the route **names** that file rather than restating
     it. That is the shape the facet's `mechanics` pointer keeps, rather than growing those steps
     into the shared procedure. Its length is not quoted here — the number lives in that file and
     a copy of it would drift, which is the same reason the axes carry no count.
   - **The routing itself is two measured positions, not one.** One project works in its shared
     checkout whenever that checkout is on the integration branch, clean and unoccupied, and
     takes a tree otherwise; another never works in it at all, every item getting its own tree,
     having had a shared checkout switched off a branch a second session was mid-flight on. Both
     are `kind: worktree`, so a single routing rule stated as procedure would have been one
     project's policy imposed on the other — hence `work_in_shared_checkout` and
     [`schema.md § 10 → Where the work happens`](../plugins/mjolnir/config/schema.md#where-the-work-happens).
   - **A tree is released, not just created, and the release is read from the same place.** The
     extracted mechanism ends with teardown — drop what the tree held, then remove the tree, on
     the merge as the signal — and two of the projects run it from a hook that surveys trees and
     reports rather than removing. So the facet is read by the role that finishes work as well as
     by the one that starts it, which is why `mechanics` points at setup *and* teardown.
   - **A verdict has to name its tree, because the failure is silent and passes.** One project
     records that a check run against whichever service stack happens to be up is a check of
     another branch's code, and that an idle stack is not an unused one; another found a capacity
     hook resolving its project root relatively, which made a session in a tree blind to a build
     running outside it. Neither failure announces itself — hence
     [`schema.md § 10 → Which tree a verdict belongs to`](../plugins/mjolnir/config/schema.md#which-tree-a-verdict-belongs-to).
   - **Exclusivity is a list with a cap, not a name.** Two projects cap two different resources
     each: a local application instance at **one** and a build daemon's slots at **two** in one,
     a single service stack at **one** and the same build cap of **two** in the other. A scalar
     naming one exclusive resource would have been wrong on both, and a facet implying a cap of
     one would have halved the build capacity of both — hence the list in
     [`schema.md § 10 → Exclusive resources`](../plugins/mjolnir/config/schema.md#exclusive-resources).
   - **What holds a place differs too.** One project's ticket belongs to the **working tree**, so
     two sessions in one tree share a place and two trees queue against each other; another takes
     a ticket **per call**, explicitly so that releasing one build does not release its sibling.
     Hence `subject`.
   - **The waits are not interchangeable, which is why contention is the hook's to rule and not
     this facet's.** One project waits a long time for a build slot and deliberately far less for
     a service stack, on the recorded grounds that a build is certain to finish while a stack can
     stay up indefinitely.
   - **Placement and setup are both local, and they are local in different ways.** One project
     nests the tree under its skills root with a second checkout inside it; another makes it a
     sibling of the main checkout. One must copy a four-gigabyte untracked asset directory with
     copy-on-write and make three separations in the tree's environment file before the stack's
     first boot, or the new stack silently rebinds the shared checkout's volumes. The setup does
     not generalise and stays behind the `mechanics` pointer; the **placement** is a path, and the
     two measurements differ in the value rather than in the steps — so it is a key,
     [`schema.md § 10 → Where a tree is created`](../plugins/mjolnir/config/schema.md#where-a-tree-is-created-and-how-the-session-comes-to-be-in-it).
     ⚠️ Until that key existed the two were one pointer, which left the location stated in no
     facet at all: every project that cut a tree carried its own standing convention, readable by
     the person running a role and by nothing shipped. The same subsection carries what was
     measured one step further on — that **cutting a tree is not working in it**, and a role
     that stops at the cut leaves the session standing in the checkout the branch model just
     forbade.

## Prose width is a habit, and the habits differ

The seventh thing axis 5 turned out to carry. Where prose wraps was never in any copy of any role
and in no project's written conventions, so unlike the six axes above it could not be read off
what the projects *state* — only off what they do. Measured over every tracked markdown file in
the six, counting lines of prose with fenced code, table rows and indented blocks removed:

| project | prose lines | p50 | p90 | over 100 columns |
|---|---|---|---|---|
| A | 3777 | 99 | 374 | 45% |
| B | 1708 | 94 | 257 | 29% |
| C | 1907 | 77 | 259 | 36% |
| D | 1735 | 83 | 359 | 40% |
| E | 1200 | 96 | 107 | 28% |
| F | 4978 | 87 | 97 | 2% |

Two shapes, and the gap between them is not a matter of degree. Where a project hard-wraps, nine
prose lines in ten land under 100 columns and the overruns are a tail of tens; where it does not,
the ninetieth percentile is a *paragraph* — 257 to 374 columns — because an unwrapped paragraph is
one line however long it is. F wraps and this repository wraps; four of the six do not. There is
no project in the middle, and the one that looks closest, E, is a wrapped habit at a slightly
wider column with a quarter of its lines just over.

So a single shared number would have been one habit imposed on four projects that never chose it,
and the absent case is the **commoner** of the two rather than a degenerate one — which is why
[`schema.md § 8 → Prose line width`](../plugins/mjolnir/config/schema.md#prose-line-width) makes
`prose_width` configuration with absence meaning no wrapping at all.

⚠️ **What the same measurement does *not* support is a second setting for bodies.** It covers
files, because files are what a checkout holds; the rendered surfaces were argued from the
renderer rather than from a count, and the rule there is procedure. A reader who wants the
counting to carry that half too will not find it here.

## The tracker port

The operation list itself, and what the procedure does where an operation is unavailable, are
[`schema.md § 3 → The operations`](../plugins/mjolnir/config/schema.md#the-operations-and-what-an-absent-capability-does).
What follows is the measurement behind that list: the shapes the three implementations give these
operations, which is why none of them could be assumed.

Each row is keyed by the operation § 3 states, so the two tables are read against each other
without a mapping in between. ⚠️ The rows are the operations the survey measured; § 3's list is
longer, and `advance_on_merge`, `set_labels`, `assign`, `checklist_read` and `checklist_write` are
argued below rather than in the table — stated because a reader comparing the two would otherwise
read a missing row as an operation nobody had evidence for.

⚠️ **`search_items` is the one operation on § 3's list the survey did not reach**, in the table or
in the argument below it, and it is named here so that a reader holding the two lists against each
other finds nothing unexplained. Its shapes were measured afterwards, against plain issues rather
than against the three above: terms and a field's value with no terms, each across every state the
tracker holds, and two ways an empty answer lies — a state qualifier carried in with the terms,
which narrows the search while the all-states flag is still on the command line, and a label the
repository does not have, which the host answers identically to a label nothing carries. Both are
refused there rather than reported, because this is the one search the filing role performs.

| Operation | GitHub Projects | Jira | Trello |
|---|---|---|---|
| `create_item` | create, add to project, set status | one call | create, then **one label attach per label** — labels cannot be set at creation |
| `read_item` | one call | one call | one call, **plus a separate call for checklists** |
| `set_state` | update a field value by project, field and option id | find the transition by name, then transition | move to a list |
| `item_number` | the item number | the item key | **parsed out of the returned URL** — there is no short-id field |
| `link_dependency` | a dependencies API keyed on the **internal id, not the number**, posted on the *blocked* item | a link call, with an inward/outward inversion relative to the tracker's own metadata naming | **description links, written at both ends by hand** |
| `link_for_close` | a keyword in the body, declarative, on merge | an explicit transition; no closing keyword exists | a bracketed number in the title, and **never a hash**, which would autolink to an unrelated object |
| `comment` | one call | one call | **impossible** — no comment action; it goes into the description |
| `checklist_item_delete` | n/a | n/a | **impossible** — reword and tick instead |

Three of these measurements each forced a property of the port, stated in
[`schema.md § 3`](../plugins/mjolnir/config/schema.md#3-tracker-port):

- Closing being declarative on one tracker (a keyword on merge), webhook-automated on another
  (where the procedure must *not* do it by hand) and absent on the third is why `link_for_close`
  and `advance_on_merge` are separate operations rather than one.
- `comment`, `checklist_item_delete`, `set_labels` atomically and `assign` each missing on at
  least one tracker is why a capability is queried with a stated fallback per absence — and the
  four are the measurement behind the operations the table above does not carry a row for. One
  project's skills already did this: a failed gate written into the description *because*
  comments are impossible there.
- One project barring source code, credentials, hosting details, file paths and branch names from
  a third-party tracker holding someone else's material is why policy sits on the port beside
  capability — and why that project's branch name goes in the run report instead.

⚠️ **Every impossibility in that table is a property of the tracker's API rather than of the
project using it**, which is the measurement behind
[`schema.md § 3 → Who declares a capability`](../plugins/mjolnir/config/schema.md#who-declares-a-capability).
No comment action, no short-id field, no label at creation time: a project cannot configure its way
out of any of them, and **three of the six run on one tracker**, so each of those three meets
whatever that tracker cannot do. What the survey found projects differing in is which mechanism
carries the type, the estimate and the template — a facet below, never a capability, and already
with a home of its own.

## What is an ordered list of named checks rather than procedure

No count is given, for the reason [`schema.md § The
loop`](../plugins/mjolnir/config/schema.md#the-loop--nine-roles) gives for the axes — a count
restated elsewhere drifts the moment one is added — and this section is the demonstration: it gained
what counts as done after it was written, which would have made a number in the heading wrong while
the gate stayed green.

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

### A green gate is not a definition of done

The one of this family whose evidence is a project's **written rule** rather than a reading of its
role copies. ⚠️ **And the one carrying no count of projects**, which is a property of the evidence
rather than a style: two are known to state the rule, and the source says *at least one* of the two
positions below rather than enumerating the six, so a figure here would be wider than what was
read. **Neither of the two could be configured as the other**, which is what made the entry a list
with an answerer per check rather than a flag:

| | what its rule says | what answers it |
|---|---|---|
| one project | a manual test on the running application is required before merging; a green gate plus a clean review is not enough | a **person**, and not the procedure |
| another | an acceptance scenario suite that needs the application running, **and** a checklist carried on the pull request | the **procedure** for the first; a person for the second |

**The first project's reason is structural rather than cultural**, which is why it cannot be read as
that project's taste. Its own documentation says the whole automated suite runs in one process
against doubles — no messaging platform, no model provider, no embedding service, no database over
the wire — and names the user-visible behaviour that is therefore verified by hand: the rendering of
buttons, file uploads and message chunking, and a whole submit-through-report flow for which it
states outright that no automated test exists. A role that read that gate as *done* would report a
feature shipped on evidence that never touched the feature.

**And the procedure cannot perform that check itself.** The credential it would drive the
application with acts *as* the application rather than as a user, so the finishing role can hand
over a type-this/expect-that script and then only **record a verdict it did not produce** — which
is why the surface carries who answers a check rather than just which checks there are.
⚠️ **Collapsing the two answerers loses a real check in the other direction**: the second project's
acceptance suite is a machine reading a machine, mirrored by no workflow at all, and configured as
human-answered it would stop every completion for a hand-over nobody needed — the gate somebody
turns off.

Hence the ordered list and its per-check answerer, in
[`schema.md § 13`](../plugins/mjolnir/config/schema.md#13-what-counts-as-done--an-ordered-check-list-and-who-answers-each-check).
⚠️ **And hence the refusal of a check the host already runs**
([`§ 13 → A done: check the host already runs`](../plugins/mjolnir/config/schema.md#a-done-check-the-host-already-runs-is-a-misconfiguration)):
every check in the table above is mirrored by no workflow at all — a hand test on the running
application, and an acceptance suite needing it up — which is the shape the facet was derived from.
A check that *is* mirrored needs no entry, because the host has already answered it, and the two
measurements supply no example of one.
⚠️ **What this measurement does not support is a definition of done for every project.** A project
whose deliverable is a library has nothing to drive, so the absent case is `[]` and is first-class
rather than degenerate. ⚠️ **How common it is was not measured** — unlike the prose-width table
above, which earns its *commoner* with a figure per project, this rests on two projects' stated
rules and says nothing about the rest.

## Which item is next is read, never derived

[`schema.md § 12`](../plugins/mjolnir/config/schema.md#12-ordering) is the thinnest facet on the
surface, and what it rests on is worth stating before the argument: two shapes, not a count across
the six projects.

- **One surveyed copy of the starting role checks an item's position in a priority queue** — the
  eight-check copy named in the readiness-gate section above. That check reads an order, and
  neither the copy nor the surface said where the order comes from. A gate whose input is a
  convention is the shape this whole document exists to catch.
- **This repository's own ordering is a row table in a document outside every tree**, in the agent
  harness's per-project store, with the argument for each row written beside it. Nothing shipped
  from a plugin can reach that file. The role that needed it read it through a carrier only this
  project resolves, which is the duplication the extraction is for, one level up.

The two have nothing in common but their output, and that is the whole reason the facet is a
pointer. A tracker query answers it on one project and a document answers it on another, so an
operation on the port ([`schema.md § 3`](../plugins/mjolnir/config/schema.md#3-tracker-port))
would oblige every adapter to answer a question its tracker does not hold — and a rule in the
procedure would have the toolkit ordering somebody's work, which is the one judgement here that is
never the toolkit's.

**The absent case is the one that was easy to get wrong.** A project with no ordering is not a
project whose next item is the first row of whatever the tracker listed: that reading turns
*nobody decided* into *this was decided*, which is
[`schema.md § 2`](../plugins/mjolnir/config/schema.md#2-code-host)'s absence-of-signal rule one
store over. So `carrier: none` makes a role ask for an item by number, and the plain-issues
example is written that way rather than given a query to look tidy.

## The four facets, and the absent case

Issue type ([`schema.md § 4.1`](../plugins/mjolnir/config/schema.md#41-type)), status
([`§ 4.2`](../plugins/mjolnir/config/schema.md#42-status--an-ordered-set-of-name-role-writer)),
estimate ([`§ 4.3`](../plugins/mjolnir/config/schema.md#43-estimate)) and template
([`§ 4.4`](../plugins/mjolnir/config/schema.md#44-template)) are each per-project,
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

## The window is a resource the loop spends

[`schema.md § 11`](../plugins/mjolnir/config/schema.md#11-session-context) is the only section of
the surface derived from measurements taken **outside** these six projects as well as inside them,
so what forced its shape is worth recording in both directions.

### What the published measurements establish

- Input length alone degrades performance. Eighteen frontier models, 194,480 calls, task
  complexity held constant and length varied: **every model degraded**, and not at the window's
  limit — a single irrelevant passage beside the relevant one measurably costs recall, and four
  compound it. ⚠️ Their impact is **not uniform**, which is the source's own word; it does not
  measure similarity, so nothing here reads the cost off how alike the passages look. The result
  that matters most for a repository written like this one: a **coherent** haystack is worse than
  a shuffled one, and the source declines to explain it, calling for work on how structure
  influences attention rather than offering a reading. The explanation is therefore nobody's yet,
  and this section does not supply one.
  <https://www.trychroma.com/research/context-rot>
- The vendor's own framing is an **attention budget** — a finite resource every token draws on —
  with three techniques for spending it: summarising a window and restarting from the summary,
  writing notes outside the window, and spending a separate window on a sub-task. The first is
  lossy, which is why § 11 makes the artifact the handoff rather than the summary.
  <https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents>
- The published practice this loop's shape is closest to keeps a window at **40–60 %** of its
  capacity — its own qualifier is that the figure depends on the problem's complexity —
  separates research from planning from implementation into different windows, writes
  each phase's output to a file that is the real handoff, and spends human review on the plan
  rather than on the diff — *a bad line of a plan leads to hundreds of bad lines of code; a bad
  line of research, thousands*. Its ranking of what hurts is the reason § 11 is about what enters
  and what crosses a boundary rather than about token counts: **incorrect beats missing beats
  noisy**. <https://github.com/humanlayer/advanced-context-engineering-for-coding-agents>

### What this repository measures about itself

⚠️ **No count of this tree's own files is written down here**, for the reason the gate's document
gives for refusing to count schema sections: a number copied out of the tree drifts the moment the
tree changes, silently and green. This subsection's first draft carried a three-row table of lines,
bytes and markers. It was already two commits stale when it was written — and it understated by a
fifth the one file the same change grows, so the argument it was offered as evidence for was
weaker in the document than in reality. **Deleted rather than synchronised**, which is this
repository's standing remedy; [#91](https://github.com/ragnor-rs/mjolnir/issues/91) is filed to
have the gate print the live figure instead.

What is stable enough to state without a number going stale: **a single role runs to thousands of
tokens and carries dozens of ⛔ and ⚠️ markers, and the loop has nine roles.** A window largely
spent on procedure before a line of anyone's code is read is what § 11 exists to notice, and the
harness vendor's own guidance is that an over-long instructions file is not read selectively — it
is ignored wholesale. <https://code.claude.com/docs/en/best-practices>

Two consequences, both already true of this tree rather than predicted of it. A role's body is
loaded only when the role runs, and only its frontmatter — a name and a description — is always
resident: that is the right shape, and it was not arrived at deliberately. And a role that cites
the surface to settle one sentence resolves the whole of it to do so, which is the argument for a
citation naming the narrowest section that states the fact — held today only at `##` level, as
[`single-source-of-truth.md`](single-source-of-truth.md#the-three-kinds-and-why-one-of-them-is-absent)
already records against itself and [#91](https://github.com/ragnor-rs/mjolnir/issues/91) exists to
close.

### Why there is no threshold on the surface

The harness exposes a window's utilization at **one moment only**, and never while a window is
filling. Of its hook events, only the one that fires when a session is resumed or forked carries a
token count — alongside the time since the
last response, whether the prompt cache has likely expired, and the estimated cost of rewriting
it — and the event that fires immediately before a window is summarised carries no count and no
threshold at all. <https://code.claude.com/docs/en/hooks>

So a `budget: 60 %` key would be a number nothing could check at the moment it is exceeded: a
convention written into the surface, which is the shape this repository calls a defect rather than
a guideline. ⚠️ **The test that key failed is not "is it enforceable in principle" but "is there a
run-time reading to enforce it against"** — § 11's own in-tree rule passes that test on three keys
the reader already holds, and is refused there rather than stated and hoped for. The qualitative
rules are stated instead, and the one live reading goes to the two items that already exist to
read something like it: [#31](https://github.com/ragnor-rs/mjolnir/issues/31), the role that
restores a session, and [#26](https://github.com/ragnor-rs/mjolnir/issues/26), the spend guard.

### Why `committed` is a key of its own, and not implied by `dir`

Under [`§ 10`](../plugins/mjolnir/config/schema.md#10-branch-model)'s `worktree` model the
teardown removes everything git does not have, and a per-item plan is exactly what a tree holds
and the repository does not. So an in-tree store and an uncommitted store are safe in opposite
cases, and a single path key could not say which was intended.

⚠️ Measured on this repository, 2026-10-18, which is why the hazard is stated rather than
reasoned about: the one artifact several concurrent sessions coordinate through is a plan file
carried in no configuration and committed nowhere. It lives in the agent harness's own per-project
store, beside the session transcripts, while the standing convention that tells a session to read
it names a path **beside the repository** — which does not resolve. The file and the pointer to it
disagree, and nothing reports that: a session following the pointer finds nothing, and a session
that knows better depends on a store no key names.

⚠️ **The first draft of this paragraph said the file was gone**, on a search bounded to the
repository's neighbourhood and the temp directory, which does not reach that store. The claim was
wider than the search that produced it — the same defect one level up from the one the paragraph
describes, and the reason it is recorded here rather than quietly corrected.

### Why the read-side rule lives here rather than beside the write-side one

[`§ 3`](../plugins/mjolnir/config/schema.md#3-tracker-port) bars facts from reaching a card. The
read side is a different question with a different blast radius, and it spans three ports rather
than one — the tracker, the host's review and check surfaces, and whatever a role fetches — so
stating it under the tracker would have made two of the three a special case of the first.

The published incident is a code-host one: payloads written into pull request titles, issue bodies
and issue comments drove three separate agents into exfiltrating repository secrets back through
the host itself, with no attacker-controlled server involved anywhere.
<https://labs.cloudsecurityalliance.org/research/csa-research-note-comment-control-github-prompt-injection-20/> That is the measurement; the
rule it forced, including the half about markup a reviewer never sees, is
[`§ 11`](../plugins/mjolnir/config/schema.md#11-session-context)'s and is not restated here. The
toolkit's own gate already holds the other half of the same shape, by
[#50](https://github.com/ragnor-rs/mjolnir/issues/50)'s ruling: a workflow is granted no scope it
does not need and its checkout persists no credential — which is a rule about what a run may
hold, not a claim that every run holds nothing.

### Why the other two legs are a section of their own, and why only one of them has a key

What a role may *believe* is one leg of three. The other two — what it **holds** while it reads, and
what may **leave** with it — are
[`§ 14`](../plugins/mjolnir/config/schema.md#14-what-a-role-holds-and-what-may-cross-the-boundary),
and three things forced that placement rather than a subsection under § 11.

**The belief rule had already been cited by a role and by this document**, so moving it would have
broken two anchors to buy a tidier table of contents. A section appended at the end costs nothing
and breaks nothing, which is the same argument every ordinal on this surface already rests on.

**One of the three is a project's fact and the other two are not.** What a role's shell inherits
differs per project and nothing can derive it; the ingestion step and the outward refusal are the
same everywhere, and a key that let a project turn either off would be a key for deciding whether
this procedure publishes credentials. So the section carries exactly one key, which is the shape
§ 6 already has for authorship and § 8 for the reply's register: a rule stated inside the axis it
would otherwise be a value of.

**And the enforcement is one carrier for all three legs**, which is the reason they share a section
rather than being filed beside the rules they enforce. The incident drove three agents through all
three legs in one pass; three scripts would have given each leg its own grammar, its own self-test
and its own chance to be the one nobody updated. What each arm reaches, and the several things none
of them do, are in
[`docs/single-source-of-truth.md`](single-source-of-truth.md#the-boundary-three-arms-two-of-them-held-in-the-session).

### What one run through the real tracker showed, and what it did not

The arms are planted in both directions by their own self-test, which reads text in memory. ⚠️ **One
run was made end to end through the host as well**, because the half that matters is what the host's
own rendering does to a payload and no in-memory plant reaches it: a throwaway item was filed
carrying a comment that renders as nothing, a zero-width character inside a word, and a visible
announcement of fresh instructions; the body was read back through the tracker port and passed to
the ingestion step; the item was closed in the same pass.

What the step returned: the hidden comment **shown in full**, the zero-width character located by
line and column, and four imperatives named — the instruction to set aside what the role was told,
the announcement, the address to the role, and the direction to act. Nothing in it was obeyed, which
is the bullet the run exists to answer. ⚠️ **What the run does not establish is anything about a
payload nobody planted**: the forms it found are the forms the grammar was written for, and the
quoting limit on the imperative half is unchanged by having fired once.

⚠️ **The hook arm was reviewed separately and two defects came out of it**, both recorded here
because each is a shape the next person writing a command-reading guard will reach for. The first:
the git subcommand was found by dropping every word beginning with `-` and reading the next one,
which left `-C`'s *value* standing where the subcommand should be — so no `git -C <root> push` was
ever outward, and [§ 1](../plugins/mjolnir/config/schema.md#1-roots) **requires** that form, making
it the shape every git call in this procedure takes. The arm was dead on its main case while its
green plant passed, because that plant would have passed either way. The second: an argument to a
flag that *can* name a file was read as a path unconditionally, so `-F title=hello` and
`-d name=value` failed to open and the hook reported that a body could not be read — falsely, on
two of the commonest outward calls there are, since that data is in the command text and had been
read. Both now carry plants in both directions.

### Why the inherited set is names, and why its arm reports rather than refuses

A list of names is not a secret, so the configuration can carry it; the value cannot be carried
anywhere, which is what the section exists to say. The arm that reads it against the live
environment then has only one honest answer available to it: a role cannot replace the environment
it was handed, so an arm that stopped would stop every session over a fact the person running it
already owns and can fix in one edit.

⚠️ **The anchors in that arm's name grammar were each added after a false report, measured on the
shell this was written in.** Unanchored, `auth` claimed an agent socket's path and `session` claimed
two terminal session ids — four entries on a report nobody would read twice. That is the same
failure one level up from the one the arm exists to catch: a guard whose output is noise is a guard
that is off.

What the empty list means is a real configuration rather than an absent facet, which is why the key
carries no `carrier` and no `absent_reason`: a project whose roles need nothing beyond the shell's
own variables has *stated* what it hands a role, and there is nothing for a reason to explain.
