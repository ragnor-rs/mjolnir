# Why the configuration surface has this shape

Every rule and flow is stated in
[`../plugins/mjolnir/config/schema.md`](../plugins/mjolnir/config/schema.md); this document states
none. It carries the *why*, derived by reading every copy of every process role across the six
projects that run this pattern — thirty-two of about forty role files in full. Each finding names
the schema section it forced; where a sentence here reads as a rule, the binding form is the
section it cites.

Projects are referred to as A–F throughout. Naming them is forbidden here.

## The survey found nine roles, not eight

The loop's statement is
[`schema.md § The loop`](../plugins/mjolnir/config/schema.md#the-loop), and among the roles it
carries is one this survey could not read as a role at all: the subsection below,
which the survey found in every project's tooling and in no project's implementation. Of the nine
it *could* read, gating is a genuine ninth role rather than a variant.
One project splits intake into *write the item* and *gate it into committed work*, and its gate
copy owns the due date and the estimate; the projects without the role fold a little into filing
and a little into starting, and neither place sets a date. The same project refuses to let
starting re-run the gate — which is where the schema's no-re-gating rule comes from.

Depth per project: **1, 7, 7, 8, 9, 9.** Five of six run the whole pattern; one runs a single
role.

**What the date needed, and what one copy does not support.** The estimate already had a facet and
the date had none, so the role that owns both could state where one of them goes and not the other;
[`schema.md § 4.5`](../plugins/mjolnir/config/schema.md#45-due-date) is that carrier, and it is
deliberately narrower than the copy it was taken from. It says where a date is written and not what
the date is: the one derivation measured runs from the item's priority through a four-row table that
no second project was found to have, so a facet absorbing the arithmetic would have generalised one
project's habit. Priority has a carrier of its own
([`§ 4.6`](../plugins/mjolnir/config/schema.md#46-priority), below), and the division holds: the
table is one project's.

**Why the gate's own checks are not a third ordered list.** The readiness gate and what counts as
done are configured lists because the copies of *those* roles diverge: the five starting copies
share no single check (below), and the two statements of done could not be configured as each
other
([`schema.md § 13`](../plugins/mjolnir/config/schema.md#13-what-counts-as-done--an-ordered-check-list-and-who-answers-each-check)).
Gating has one copy, so there is nothing yet to diverge from. What that copy checks is the facets
the surface already states — the type against the template, the estimate against its own rungs, the
dependencies, what policy bars from an item — plus two judgements no key can carry: whether an
acceptance condition is answerable without asking anyone, and whether the body leaves a question
open where a decision belongs. The one genuinely per-project input, what bar a dependency has to
have reached, is already
[`schema.md § 5`](../plugins/mjolnir/config/schema.md#5-readiness-gate--an-ordered-predicate-list)'s
rule.

### The tenth role every copy named and none of them wrote

The role that **restores** a session's context is the counterpart of the one that persists it, and
the survey found it in a shape none of the other nine came in: named by the tooling of every project
that has any of this tooling, and implemented by none of them. The phrase a session is loaded with
sits in the excluded-turn list of **each day-log script the survey read** — the five of the six
projects that carry one — classified there as the tooling's own upkeep, exactly as the save it
mirrors is, so those scripts already deducted the minutes of a role no project had written down.
That settles whether it is work: the classification is those scripts', it predates the role, and
[`schema.md § 24`](../plugins/mjolnir/config/schema.md#24-session-restore--the-readings-a-pass-is-resumed-from)
changes nothing about it.

It is the strongest case for extracting a role, and the weakest evidence base of any role here:

| | |
|---|---|
| **Why it is a role** | Tooling in several projects names it, people invoke it, and it is performed from memory and differently every time. Its failure mode is quiet — a sweep that misses the unpushed commits, reports a cold environment as warm, or restates a stale recollection as current produces a confident and wrong picture of where the work is, which the next hour is then spent acting on |
| **Why its readings are procedure rather than configuration** | The thirds of the role it mirrors are configuration because the copies **diverged** — counted in [the section on that role](#the-bookkeeping-role-three-copies-that-are-a-third-of-it-and-two-keys-that-came-out-of-it) and nowhere else. Here there is nothing to diverge from, so a key stating which readings run would be a project's licence to switch one off — and a reading switched off reads exactly like a reading that found nothing, which is this role's whole failure mode |
| **What that leaves weaker than the nine** | Every other role here was reconciled from copies that could be read against each other. This one was derived from performing it, so the list of readings is one performer's habit written down and held by a carrier rather than a merge of five. It is likelier than its siblings to be missing a reading, and the place that shows up is a report that was confidently complete |

### The loop does not continue itself

Measured on this repository from the harness's own session records and the integration branch's
history, over a window stated closed because a day still running is a figure that grows after it is
written — 2026-10-19 UTC, 00:00 to 20:23: **sixteen changes landed, the finishing role was invoked
six times, and the reviewing role three.** Eight sessions invoked the starting role and five of
those went on to invoke the finishing one. One session is the clean instance — it implemented item
[#8](https://github.com/ragnor-rs/mjolnir/issues/8), landed it as `b9e8fd7` through pull request
[#147](https://github.com/ragnor-rs/mjolnir/pull/147), wrote its bookkeeping and asked what was
next, with the finishing role neither invoked nor its procedure read. What that session had of that
role: its frontmatter, read eight lines at a time while the session was authoring another role's
frontmatter,
and eight scattered body lines returned by a `grep` across every skill. No read ever named the file,
and no invocation preamble for it was ever injected.

What the figures are evidence for is not that the roles are wrong but that **nothing carried the
item between them.** Each role's description was keyed on being asked; the route was stated in prose
that named no mechanism; and the leg from implemented work to an open change belonged to no role in
the pattern above, implementing being absent from the list this section's own opening cites. A
session that had just finished the work therefore had nothing instructing it to continue, and every
role it skipped was skipped silently.

A count of invocations is a floor, and it errs against this argument. It reads the harness's record
of a *carrier* being invoked, so a session that opened
a role's file and followed it by hand counts here as a skip, and a session's record can be pruned
with the tree it worked in — observed within this same day. Both inflate how often the route looks
uncarried. What neither touches is the landings, which are the integration branch's own history, nor
the instance above, where what the session read is itself on the record.

The route is stated, with each leg and what enters it, in
[`schema.md § The loop → What carries the item forward`](../plugins/mjolnir/config/schema.md#what-carries-the-item-forward-and-where-it-stops-to-ask).

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

### A carrier of the project's own, reached by route rather than carried

One adopter sends its design items to a design skill of its own rather than through the loop's
implementing leg. That was reported by the adopter's audit and is not re-verified here. Three
answers were weighed:

- a map from a label or type to a carrier the project names;
- an exemption through [`schema.md § 30`](../plugins/mjolnir/config/schema.md#30-the-changes-that-do-not-go-through-the-loop);
- leaving the hand-over to the person.

The map was ruled for. § 30 classifies a change by the paths it touches, so it has no reading of
an item before any path exists. Leaving it to the person makes every such item start the wrong
leg first.

The map does not contradict [`schema.md § 36`](../plugins/mjolnir/config/schema.md#36-a-skill-that-is-no-leg-of-the-loop-and-why-none-is-carried-here),
because what it configures is which carrier a leg the loop already has is entered through, and
the toolkit still ships no such carrier.

### Name and role diverge in both directions

One role under several names is the expected direction, and it happens: the bookkeeping role
appears under two names, deployment under four across five projects, and one project carries two
differently-named skills for filing and gating.

The reverse also happens, and a name-keyed merge produces nonsense on it:

- **One name, three unrelated roles.** The `deliverables` name is a prose session summary for a
  non-technical reader in one project, a tab-separated invoice line-item file with an hourly rate
  conversion in two others, and in a fourth a monthly report that distributes a total of hours it
  is *given* across the changes shipped that month. Same directory name, different output,
  different trigger, different reader, no shared procedure. The third is in two carriers, a
  command in one project and a skill in another, so reconciling it against the command alone leaves
  the skill copy local in a project declared migrated. A name-keyed merge of this entry is wrong
  however many copies there are. The roles are named apart in
  [`schema.md § The loop`](../plugins/mjolnir/config/schema.md#the-loop), and what the one basename
  does to the readiness check — which cannot answer for it and says so — is the
  `ambiguous:` entry in that check's own vocabulary.
- **One name, a subset role.** A bookkeeping carrier can be the *commit third* of the role with
  the board and memory halves absent. Counting such a copy as a full one overstates adoption;
  counting it as unrelated loses that project's commit behaviour. How many copies are whole and how
  many are a third is counted once, in
  [the section on that role](#the-bookkeeping-role-three-copies-that-are-a-third-of-it-and-two-keys-that-came-out-of-it),
  not here.

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
[`schema.md § The loop`](../plugins/mjolnir/config/schema.md#the-loop). The measurements that forced
each to be independent:

1. **Work-item tracker.** Four models were in play — GitHub Projects in three projects, Jira in
   one, Trello in one, and **none** in one, whose work items were entries in a specification tree
   on disk. The port's implementations are one module per kind, built as their items land; the
   trackerless project moves onto a real tracker rather than the toolkit growing a filesystem
   adapter — and the trackerless case was proved against a deliberately trackerless scratch config,
   because the next project to adopt this may have no tracker on its first day.
2. **Code host.** The same host in all six, including both projects whose cards are elsewhere —
   which is precisely why it is a separate axis. The host's own runs later forced a facet inside
   the axis, [`schema.md § 2`](../plugins/mjolnir/config/schema.md#2-code-host): one project's
   guard, keyed on job names, refused a build on the strength of a check that only validated a
   title — two unrelated workflows had named their job identically — and the same project measured
   a conflicted pull request producing **zero** runs, which reads as green to anything that treats
   an empty check list as a pass. Hence `checks` keyed by workflow name, with
   absence-of-signal-is-not-an-answer stated beside it.

   **A second facet inside the same axis was measured on this repository.** How a pull request
   lands — squash, a merge commit, or rebase — is read in three places in this backlog: the role
   that performs the merge, the commit-message hook that has to survive a concatenated message, and
   the role that prunes a landed tree and deletes its branch. Two of them *tolerated* both shapes;
   the merging role silently **assumed** squash, the half of the gap a tolerant reading hides. At
   `756ab7a`, `squash` matched six lines across the surface, this repository's configuration, every
   document under `docs/` and every file under `config/examples/`, and not one of the six stated
   the fact: every one is the landed reading explaining why a rewritten hash defeats ancestry — the
   one reader this facet does not simplify — and no key, and no sentence anywhere, said which method
   a project lands by.

   Two measurements on this repository are why the key exists:

   - **A landing picked a method with nothing to read.** `main` was linear and the previous change
     had landed as a single commit, so squash was inferred. A linear history is equally consistent
     with rebase, so the inference was a coin toss that read as a reading. What establishes the
     method is that a branch of six commits and one of three each added **exactly one** commit to
     a `main` that carries no merge commit at all, which a rebase merge cannot do and a merge
     commit cannot do either. So the convention was in the history to be read, and nothing said
     it.

     The `(#N)` suffix on 26 of the 33 commits is not the host's squash marker: this project's
     finishing role **passes** that subject itself, because a host appends the reference only to a
     subject it generates — so the suffix is evidence of the convention and not of the merge
     method. Of the seven commits without it, six predate the loop running on itself, and one is a
     merged pull request whose subject was passed without its reference, which is the defect the
     finishing role's squash-subject rule exists for.
   - **The host constrains nothing.** `allow_squash_merge`, `allow_merge_commit` and
     `allow_rebase_merge` are all true, and `delete_branch_on_merge` is false — so every method is
     available, nothing on the host enforces the convention the history implies, and the branch
     deletion that *looks* like the host's job is nobody's until a project says whose it is.

   Hence [`schema.md § 2 → How a pull request lands`](../plugins/mjolnir/config/schema.md#how-a-pull-request-lands),
   which also rules what the host's own setting is for: read from the host as a constraint on the
   stated method, never restated as a second copy of it. The facet does not make the landed reading
   cheaper: that reading keeps both of its tests, for the reason the section gives.

   **A third facet inside the axis comes from one project's runner account.** One project in the
   migration set declares a non-default runner label on every job, because its host account
   carries its own runners — and a job asking for the host kind's default label on that account
   **never starts at all**. A generated gate carrying the default is a check that never reports,
   replacing one that did, and a run that never reports is the absence-of-signal case this same
   section already refuses to read as green. So where the jobs run is stated, an installer writes
   it, and the statement is held to the workflow files —
   [`schema.md § 2 → Where the host's jobs run`](../plugins/mjolnir/config/schema.md#where-the-hosts-jobs-run).

   Two further measurements on the same account:

   - **Its runners take one job at a time, so a job's budget is spent queued.** A short check at
     the back of the line is cancelled having never started — no runner recorded, no step run —
     and the pull request then carries a conclusion indistinguishable from a failing check. That
     is why the capacity is on the surface beside the budget rather than left as a fact about a
     runner: at one job, `budget_minutes` is a queue budget, and a consumer that read the
     conclusion and stopped would send somebody to fix a diff over a queue.
   - **The number of jobs a workflow splits into is what decides how long the queue is.** Which
     prices, rather than overturns, this section's own ruling that each mirrored command takes a
     workflow of its own: the cost there was stated as a checkout per command, and on a
     single-runner account it is also a place in the line. The ruling stands — the alternative is
     still a configuration `checks` cannot state.

   The surface does not carry the default itself. A per-kind table of runner labels here would be a
   second statement of the host's own naming, wrong silently the next time the host changed one —
   the same argument that keeps the event vocabulary off this surface. A project that writes no
   `host.runner` has nothing for the drift check to hold its files to, and that check says so
   rather than guessing.
3. **Code root.** One project's code is a git-ignored subdirectory that is its own repository
   under a different owner, not a submodule. Its skills write the root explicitly into every git
   call and stop if the directory is absent, because a fresh clone of the outer repository does
   not have it. The failure mode behind
   [`schema.md § 1`](../plugins/mjolnir/config/schema.md#1-roots):
   a skill that takes the top level of the repository it is installed in commits the engagement
   notes and never touches the code; a host CLI call inheriting the working directory addresses
   the wrong repository. Both fail quietly, having done something plausible first.

   The same project carries two such repositories, each with its own host, its own checks and its
   own verdict set, which makes the grain of this axis per repository rather than per project —
   [`build-surface.md § A verdict is a command, a root, and a condition`](build-surface.md#a-verdict-is-a-command-a-root-and-a-condition)
   has the measurement and
   [`schema.md § 1 → A project's code is not always one repository`](../plugins/mjolnir/config/schema.md#a-projects-code-is-not-always-one-repository)
   is the shape it forced. The root is still configured rather than inferred, and still stated in
   every call; what changes is how many of them there are.

   **The same section's other root is the one root the surface cannot carry.** The shared reader
   resolves `.claude/mjolnir.yaml` against the
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
   A key declaring it would carry `"."` in every configuration and be read by nothing — worse than
   absent, because a project that pointed it at a subdirectory would be ignored in silence. The
   costs are stated in that section: the naming requirement is a statement rather than a stop, and
   the argument form stays, because a role has to be able to address a project it is not standing
   in.
4. **Carrier.** See above. Three projects also run process hooks, at eight, five and four.
5. **Audience and language.** One project writes its items in one language and its repository in
   another and states the split is by audience — its branch slug a **translation** of the item
   title, never a transliteration. One writes the day log in a technical register for itself;
   another writes it in a business register for a reader outside the build. Three settings, not
   one — hence
   [`schema.md § 8`](../plugins/mjolnir/config/schema.md#8-language-register-audience--per-artifact-not-per-project).
   A seventh setting in the same axis is measured rather than stated by any project:
   [prose width](#prose-width-is-a-habit-and-the-habits-differ).

   **One artifact in that map is fixed rather than configured.** The measurement that forced it
   is an absence: the reply a role writes in the session is an artifact like the day log, and for
   several roles the only output, and **no copy of any role in the survey stated its register** —
   not one of the thirty-two read in full, and nothing in the surface either. Where every other
   artifact above was carried three or four different ways by different projects, this one was
   carried nowhere, so there was no divergence to reconcile and nothing to make configurable
   from.

   The evidence for what to put there instead is not a count across projects A–F: it is the stated
   requirement of the person the replies are written to, recorded on
   [#79](https://github.com/ragnor-rs/mjolnir/issues/79) in their own words. Why that settles it as
   *procedure* rather than as a setting is the rule's own, at
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
     into the shared procedure.
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
   - **The half that *deletes files* belonged to neither role, and it is the half that destroys
     data.** The merge is only one of the two moments a tree stops being wanted: a change merged in
     the host's web interface, in another session, or before any rule existed leaves a tree nothing
     is watching, and the trees then accumulate until somebody notices — the count is in
     [`schema.md § 10 → Pruning a tree whose branch has landed`](../plugins/mjolnir/config/schema.md#pruning-a-tree-whose-branch-has-landed),
     which is also where both carriers are stated. The measurements came from different projects
     and pointed at different halves of one rule — what *landed* means, what makes a tree
     disposable, and how long a kept verdict is good for — which is why the subsection reads as four
     rules rather than one.
   - **`regenerable` is the one key that half needs, and it is a key for the reason `claimed_by`
     is.** What a rebuild writes again is a build directory in one project, a dependency cache in
     another, a service stack's own volumes in a third — and a carrier shipping any of those names
     would be this toolkit carrying a project's value. What the empty form costs, and the exemption
     without which the rule would prune nothing at all, are stated with the key.
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
     The value is ruled rather than left to each project: one level under the agent harness's own
     managed directory, the only placement a session is moved into without a person answering a
     prompt the project cannot configure away. It stays a key — the depth is the rule, the
     directory is each project's to state, and a project carrying several code roots takes the
     prompt on the roots it crosses. The same subsection carries the next measurement: **cutting a
     tree is not working in it**, and a role that stops at the cut leaves the session standing in
     the checkout the branch model forbids.

## Prose width is a habit, and the habits differ

The seventh setting axis 5 carries. Where prose wraps was never in any copy of any role
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

The same measurement does *not* support a second setting for bodies. It covers files, because
files are what a checkout holds; the rendered surfaces were argued from the renderer rather than
from a count, and the rule there is procedure.

## The tracker port

The operation list itself, and what the procedure does where an operation is unavailable, are
[`schema.md § 3 → The operations`](../plugins/mjolnir/config/schema.md#the-operations-and-what-an-absent-capability-does).
What follows is the measurement behind that list: the shapes the three implementations give these
operations, which is why none of them could be assumed.

Each row is keyed by the operation § 3 states. The rows are the operations the survey measured;
§ 3's list is longer, and `advance_on_merge`, `set_labels`, `assign`, `checklist_read` and
`checklist_write` are argued below rather than in the table. Six operations added to § 3 after the
survey have a table of their own, [below](#the-operations-added-after-the-survey).

`search_items` is the one operation on § 3's list the survey did not reach. Its shapes were
measured separately, against plain issues rather than against the three above: terms and a field's
value with no terms, each across every state the
tracker holds, and two ways an empty answer lies — a state qualifier carried in with the terms,
which narrows the search while the all-states flag is still on the command line, and a label the
repository does not have, which the host answers identically to a label nothing carries. Both are
refused there rather than reported, because this is the one search the filing role performs.

`set_field` is likewise outside the survey. It serves the gating role: of the two values that role
writes, the estimate reaches the item as a label on the copy measured, and the date
([`schema.md § 4.5`](../plugins/mjolnir/config/schema.md#45-due-date)) reaches it as a field, which
no operation carried. Two of the implementations perform the write, and each shapes a value by the
field's own type rather than by what the
value is — a column's type on the board, and a site-wide field catalogue on the issue tracker,
where the estimate turns out to be a member of a composite field rather than a scalar. The rows
below carry those; the operation still has no row in the table above, because the table records
what the **copies** did and no copy was measured writing one.

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

Every impossibility in that table is a property of the tracker's interface rather than of the
project using it, which is the measurement behind
[`schema.md § 3 → Who declares a capability`](../plugins/mjolnir/config/schema.md#who-declares-a-capability).
No comment action, no short-id field, no label at creation time — each of those is one tracker's
API and not one project's choice, and no configuration a project writes can reach any of them.

The four Trello cells are properties of the **interface** a project's copy used, not of the
tracker: under
[`schema.md § 3 → Who declares a capability`](../plugins/mjolnir/config/schema.md#who-declares-a-capability),
measured against a live Trello through a different interface and read against the published
reference — the detail is [below](#what-building-the-card-implementation-established) — three of
the four reproduce on that second interface and one does not: **comments exist**. None of the four
is a configuration a project writes, and a project cannot reach any of them either way; none may be
read as *this tracker cannot*. Three of the six projects run on a single tracker, so a difference
between those three cannot be a capability difference at all. What projects were found
differing in is which mechanism carries the type, the estimate and the template, which is a facet
below and already has a home of its own.

### The operations added after the survey

Seven operations joined § 3's list after the survey, each because a role needed a reading no
project's copy took: `read_comments`, `read_vocabulary`, `read_closing_list`, `grouping_items`,
`read_current_grouping`, `link_relation` and `read_relations`. No copy's measurement stands behind
them, so the table records what each implementation in `plugins/mjolnir/scripts/adapters/` does.
An absence is that implementation's, declared in its module with the reason
([`schema.md § 3 → Who declares a capability`](../plugins/mjolnir/config/schema.md#who-declares-a-capability)),
and § 3's stated fallback is what a role gets there.

| Operation | GitHub Issues | GitHub Projects | Jira | Trello |
|---|---|---|---|---|
| `read_comments` | every page, oldest first, through the issues path | the same path, a card being a view over an issue | offset pages held to the host's own total; a total that moved or an entry read twice is a failed read | the card's comment actions, which the host answers newest first, turned round and followed until a page comes back empty |
| `read_vocabulary` | statuses are open and closed, read without a call; labels and types are the repository's | statuses **unestablished**: which single-select column carries status is the project's statement, so every such column is published with its options; labels **unestablished**, a board spanning repositories | statuses read per issue type and flattened in order of first appearance; labels **unestablished**, a label being site-wide | statuses are the board's open lists in board order; types are **none**, a card having no type object |
| `read_closing_list` | the host's own closing list for the change, beside a scan of its title, body, commit messages and the merge call's text | the same reading on the same host | **absent**: no text in a change closes an item | **absent**: a merge closes no card |
| `grouping_items` | one milestone's issues in both states, without bodies, with the host's listing bound reported | the board read whole and matched on the card's grouping field; a milestone read off the repository and joined | one bounded query on the field § 4.8 names, across every state | **absent**: a board's lists are its statuses, so it holds no grouping |
| `read_current_grouping` | **absent**: a milestone carries no mark saying it is the open one, several staying open at once | **absent**: an iteration is current by its dates, not by a mark the board sets | the active sprints on every sprint board of the project, deduplicated; one is the answer, and none or several is answered with no value and every open sprint listed | **absent**: a board's lists are its statuses, so it holds no grouping |
| `link_relation` | **absent**: the host records a dependency and sub-issues, and no link type a project can name | **absent**, for the same host's reason | a link of the type `tracker.relations` maps, written with the inward/outward inversion `link_dependency` has | **absent**: no relation exists between two cards |
| `read_relations` | **absent**, with `link_relation` | **absent**, with `link_relation` | the links that arrive with the item; a type the project maps no name for comes back under `unnamed`, and the dependency's type never appears | **absent**, with `link_relation` |

What the table states is the code, and this document records no live run of any of the seven.
`link_relation` and `read_relations` in particular were exercised only against the Jira suite's fake
host: the link-type names a real site uses, and which side of a link each item reads, are
unmeasured. So is `read_current_grouping` against a live board: the sprint field's schema and its
custom type were read live from one site's field catalogue, and the board and sprint listings only
from the Jira suite's fake host.

### Reading a dependency back, per tracker, and the one tracker that cannot

No copy was measured reading a dependency back, so the read half is outside the survey too. The
write half is that table's `link_dependency` row and the Jira reference section below.

§ 5 carries a blocker predicate in the shared library, and without a statement of **where a blocker
is recorded** a tracker that cannot be asked is indistinguishable from a tracker with nothing to
report. The rule is
[`schema.md § 3 → An edge is a relation`](../plugins/mjolnir/config/schema.md#an-edge-is-a-relation-and-a-body-keeps-the-reasoning-about-it)
and the operations are `link_dependency` and `read_blockers`.

| Tracker | How a dependency reads back | Source |
|---|---|---|
| plain issues, and a board | one endpoint, read on the *blocked* item — the same one the write posts to, the board holding no relation of its own. **Every page**, under the same silent ceiling the search rows below record, and the client merges them only when the paging flag is passed. **The entries are issues and carry their own repository address**, which is the half a bare number loses: a relation is recordable across repositories and a board draws cards from more than one, so a blocker read as `#13` resolves against the wrong backlog and the wrong `#13` answers perfectly. **And the state word is not the whole state**: this host records *why* an item closed, so an item abandoned rather than finished is `closed` with a reason that says so — and § 5's bar is what the dependency produced | a live host |
| Jira | **no call of its own**: the links arrive with the item. The sense is read from which side an entry carries and never from the type's wording — the inversion the reference section below measured, where the write is the other chance to invert it — and each entry holds the project's own status word *and* the tracker's category behind it, with the blocker's own summary and address beside them. **And this is the tracker that cannot answer *why* a blocker closed**: a resolution is not in a link payload and the read makes no call, so a blocker abandoned and one finished arrive in the category that means neither. A reader here has the category and not what the dependency produced, which is the half § 5's bar is about | a live site, through a different interface |
| Trello | **absent.** There is no relation object to read, there being none to write either, so § 5's blocker predicate reports *unanswered* on this tracker. Never *no blockers*: a prose edge in two card descriptions is readable by a person and is not a verdict a gate may pass on | the published reference |

The absence is why the predicate's stated behaviour is *unanswered* rather than a pass —
[`schema.md § 5`](../plugins/mjolnir/config/schema.md#5-readiness-gate--an-ordered-predicate-list)
is where that is stated. A gate that treated *cannot be asked* as *nothing to report* would start
every item on that tracker whose dependency had not landed, which is § 2's absence-of-signal rule
arriving at a readiness gate. Which implementations carry a capability is declared by implementing
it rather than listed anywhere.

**The measurement behind the ruling, taken in this repository's own backlog.** Sixty-eight
dependency edges were stated as prose in issue bodies while the configured readiness list carried
the blocker predicate with nothing to read; the host's dependency relations carried three of the
sixty-eight. The prose line and the relation were two statements of one fact. Some of those
sentences carried what a relation cannot express — that two items were decided together, or that
one sits below another in an order without blocking it — which is why the ruling separates the edge
from the reasoning about the edge rather than banning prose, and why its test is what a gate would
answer rather than what a sentence looks like.

Two project-local roles in this repository had written a tracker's own field name and endpoint path
into their prose, and the naming sweep was green over both — it forbids a tracker's *name* and these
are a level down from it, the tracker's vocabulary. That is its own check, recorded with the sweep
in
[`single-source-of-truth.md`](single-source-of-truth.md#the-second-sweep-naming-no-other-project).

### What building the board's implementation measured

These are the host's own answers, measured for the implementation behind `kind: github-projects`.
Each one is a shape the implementation takes because of what came back, and none of them is
derivable from the table above.

| What was asked | What came back |
|---|---|
| the same field asked for **by name** twice in one query | refused outright — `fieldConflict`, *has an argument conflict* — and legal only with an alias on each. So the implementation asks for none by name: it reads a card's whole value connection once and keys the answer on each value's own field name, which has no alias to get wrong and costs one request rather than one per field |
| a card's values, for a card on a live board | only the columns that **hold** a value: the host-managed ones carry none at all, so a column read as empty and a column the host maintains are the same answer and a write has to be refused by the field's own type rather than by its value |
| a number that names a pull request | the host's own typename says which of the two it is, and a merged pull request answers with a state no `statuses` list contains. A stronger guard than reading a URL for `/pull/`, and the implementation beside this one takes the weaker route because that is what was measured for it |
| a board addressed by an owner's login | resolvable through the owner interface with a fragment per owner kind, so nothing has to know whether an owner is a person or an organisation. Asking the wrong one of the two by name answers an **error** rather than nothing, which is what makes the guess expensive |
| a board with more items than one page | the page's own cursor, and nothing in the answer that says a list is short. The client's paginate flag follows top-level pages and not a nested connection, so the ceiling is silent: a round total is the signature of an unfollowed cursor |
| a project number nothing resolves | `NOT_FOUND` with a non-zero exit, which is why an address the reader accepts and the tracker rejects arrives as a failed call naming the owner and the number rather than as an empty board |
| a field value handed in as one variable — the whole input object the write takes | refused: *provided invalid value*, because the client sends a variable as a string and the host wants an object. So a write takes the value as a **typed scalar**, one document per kind of column, and nothing is pasted into a request |
| a number sent as that typed scalar | refused in turn: the client's typed field parses an integer and leaves anything else a string, and the untyped one is a string by definition, so a `Float` cannot travel as a variable at all. The number is formatted into the document — safe for one reason that does not generalise, which is that it is a `float` by then and a non-finite one is refused before formatting |
| the board's items, read immediately after a card was added to it | the card is **absent**, while the item's own card list already carries it — and the host's own count agrees with the short page, `hasNextPage` false. So the one omission a board read can carry is invisible to anything a reader could check, no guard catches it, and what the operation states instead is the bound: a duplicate check run straight after a filing may not see what it just filed |

Both of the last two came out of writing rather than reading, with every read already green, which
is why the live half of a run through this port is a write and not a report.

### What building the card implementation established

*Established*, not measured, per
[`schema.md § 11 → A report names what it could not establish`](../plugins/mjolnir/config/schema.md#a-report-names-what-it-could-not-establish)
— the implementation behind `kind: trello` speaks the tracker's HTTP interface with a key and a
token, and this repository's shell holds neither, so nothing below was established by running the
adapter. Two weaker sources were used instead and are **named per row**, because they do not agree
everywhere:

- **a live board, through a different interface** — a connector over the same tracker, which reads
  and writes cards but is not the interface the adapter speaks. What it shows about the tracker's
  own shapes is observation; what it shows about an endpoint is nothing.
- **the published reference** — the tracker's own statement about the interface the adapter does
  speak. Authoritative about the endpoint and unverified against a running one.

| What was asked | What came back | Established by |
|---|---|---|
| where a card's number lives | the card's URL is `/c/<link>/<number>-<slug>`, and the number opens the last segment; the connector's card carries **no** short-id field at all, which is this survey's own row | a live board |
| what a card's state is | the board's states are its **lists**, and whether a card is archived is a separate fact — so a card in the project's terminal list is not archived and an archived card is still in a list. Both are reported, never collapsed | a live board |
| what classifies a card | labels, as board-level objects carrying a free-text name. The name is neither unique nor required — the live board carried one label with a name and no colour — so a name is resolved to **at most one** label and an ambiguous one is refused | a live board |
| whether a comment can be posted | **yes**, and this is the one row that refutes the survey above: the connector posts one, lists them, reads one back, and the board's own history names `COMMENT` as an action type | a live board |
| whether a check item can be removed | the connector has `create`, `add_item` and `update_item` — rename and tick — and **no delete**, which is the survey's row exactly; the checklist endpoint documents `DELETE /checklists/{id}/checkItems/{id}` | both, disagreeing |
| whether labels can be set at creation | the connector creates a card from a list, a name, a description, a due date and a position, then attaches labels one call each — the survey's row; the card endpoint documents `idLabels` on the create and on the update | both, disagreeing |
| what a custom field costs | the live board has **none**, and the connector addresses one by an option id per type. So the one value § 4.5 names reaches this tracker as the card's own `due`, and a facet pointing anywhere else is refused naming the power-up it would need | a live board |
| how a card is addressed by its number | the card endpoints take an id or a short link and **not** the number; the number resolves only as a nested segment of the board's own card path, which is the slot the documented `filter` keyword occupies. So the adapter resolves a number through the board's card index instead — which is also the only route to an **archived** card by number | both, agreeing |
| whether a collection can be read whole | the card collection names no cursor, and a collection answers at most 1000. So there is no page to follow and nothing to truncate, and the only honest guard is to **refuse** an answer that reaches the ceiling — a board that genuinely holds that many included | the published reference |
| what a refusal looks like | 429 with the limit named, at 300 requests per 10 seconds per key and 100 per token; the key and the token travel as query parameters, which is why every failure message here names them rather than quoting the call it made | the published reference |

Where the two sources disagree the adapter follows the reference, under
[`schema.md § 3 → Who declares a capability`](../plugins/mjolnir/config/schema.md#who-declares-a-capability),
which makes a capability the adapter's own fact. An operation declared absent that in fact exists
leaves a role taking a stated fallback for ever with nothing reporting it; one declared present that
does not exist comes back as a failed operation naming the call. The second is visible and the first
is not, so the two disagreeing rows — the check-item delete and the labels at creation — are
implemented.

No call in that adapter has been made to a running host, so the three reference-only rows are the
reference's word and nothing beyond it. What a run of it takes is a board and the pair of variables
[`examples/trello.yaml`](../plugins/mjolnir/config/examples/trello.yaml) names, and the shell this
repository's own roles are handed holds neither, since nothing here is configured for that tracker.

The implementation's own suite cannot answer what the host does with a payload, which is why the
read half is driven against a live board by hand and recorded on the work item: a board
past one page read whole, a card's columns out of one query, and the pull-request guard refusing a
real pull request number.

### What building the issue implementation established

*Established*, not measured, for the same reason —
[`schema.md § 11 → A report names what it could not establish`](../plugins/mjolnir/config/schema.md#a-report-names-what-it-could-not-establish)
— the implementation behind `kind: jira` speaks the
tracker's own HTTP interface with an account and a token, and this repository's shell holds
neither. Two weaker sources were used and are **named per row**, because they do not answer the
same questions:

- **a live site, through a different interface** — a connector over the same tracker, reading a real
  project's issues, workflows, link types and field values. What it shows about the tracker's own
  shapes is observation; what it shows about an endpoint is nothing.
- **the published reference** — the tracker's own statement about the interface the adapter does
  speak. Authoritative about the endpoint and unverified against a running one.

| What was asked | What came back | Established by |
|---|---|---|
| what an item's identifier is | the project's key and a number, and the key resolves across the **whole site** — so a key from another project answers perfectly rather than being refused, which makes the project key a guard and not a label | a live site |
| what a state is | a status the item is **in** and a transition that leads there, and a transition's `name` is a separate field from the `to.name` it leads to. So a status word is matched on what a move leads to; matching the verb would match the wrong half on every workflow whose verbs differ from its states | a live site |
| which statuses an item can reach | what the workflow offers **for that item's type**: on one project defining nine statuses, one type offered three of them and another all nine. So a word the project states and this item cannot reach has two readings — a vocabulary the tracker lacks, or a move this workflow does not allow from here — and neither is assumed | a live site |
| what a move can carry | the fields a transition offers, asked for with `expand=transitions.fields` and keyed by the field's id, each with its type and, where it has them, the values it takes; the move's own write takes them under `fields` beside the transition's id. So a field the project states for a move is held to that offer before the write, and one the move does not offer is refused rather than sent. A resolution on a move to a finished status is the case one adopter's workflow was recorded as needing, and no move carrying one has been run | the published reference |
| which types an item can have | nine available on one project with six in use, against a branch-prefix vocabulary of five — the case behind `type_branch_prefix` being a map rather than a boolean ([`schema.md § 4.1`](../plugins/mjolnir/config/schema.md#41-type)). And a type is **required at creation**: there is no filing without one, which is the one place this tracker forces a question the code-host trackers leave open | a live site |
| what a dependency's two sides are called | the link type reads `inward: is blocked by` / `outward: blocks`, and the call's `inwardIssue` is the item that **blocks** — the inversion this survey's own row named, now with both halves in hand. Read the wording and the dependency is filed the wrong way round, and nothing in the answer says so | a live site |
| how a dependency reads back | the entry an item carries names the *other* side, so an entry holding `inwardIssue` means this item **is blocked by** it. Which is why the adapter's direction is held by a round trip rather than by reading the call: the write and the read are two separate chances to invert it | a live site |
| whether an estimate exists on this tracker | a native composite field, holding a duration as text (`2h`) and mirrored as seconds, with a value on the large majority of one real project's items — and the values come from a closed ladder of size classes mapping to hours rather than being free numbers, so `estimate` here is *(native field, hours, a closed set)*. What the sprint answers is the **gate** and not the carrier: an item with no estimate still starts, which is a statement about the readiness list. Reading that as the carrier being absent is how a configuration comes to claim a project sizes nothing while its own board sizes nearly every item | a live site |
| what a search costs | a query with **no restriction is refused outright** — *Unbounded JQL queries are not allowed here*. So the project restriction is the only shape the host accepts, which is also why the state qualifier the plain-issues implementation has to refuse cannot arrive here: every term is quoted into an operand | a live site |
| what a body is | a structured document rather than a string, on the interface version the adapter speaks. So no markdown body is simply sent: the adapter renders headings, paragraphs, bullet and ordered lists and fenced code, states that nothing else survives, and reads a document back the same way — a fuller renderer is a markdown parser, which would be the implementation deciding what a template means | both, agreeing |
| how a custom field is addressed | by an id that is **site-specific**, so a field is named in a configuration and resolved against the site's own catalogue per run. And a name is not unique there, so an ambiguous one is refused rather than resolved by position | both, agreeing |
| what a field holding several values takes | the whole list under the field's id, which replaces what was there; the catalogue states `array` and the element type beside it. An option is a member named by `value`, a user by `id` (read back as `accountId`), and text is itself. A component or a version is shown by `id` in this interface's own example and by `name` in the self-hosted product's, and `name` is what is written here. The reference states no shape for a sprint's elements, so one is refused | the published reference, the `name` form and the replacing in the self-hosted product's alone |
| who moved an item | the history names an author, and **a script running under somebody's token is indistinguishable from that person in it**. So the advance-off-a-merge operation reports whether the last status change was made by something *other than this credential* and refuses to call it automation | the published reference |
| whether the merge is visible here | **no**: the merge is on the code host, and nothing on this tracker ties a status change to one. So `link_for_close` is absent — there is no closing keyword to compose — and the advance operation answers the tracker's half alone, with the other half read from § 2's host | both, agreeing |
| how a search is paged | a cursor in the answer, followed until the host says it is the last page. A page that fills says nothing about whether more exist, which is the same silent ceiling the board implementation pays a cursor-follower to avoid | the published reference |

A transport is a *seam*, so a guard inside it is a guard a substituted transport walks straight
past — the standard being
[`schema.md § What earns a test`](../plugins/mjolnir/config/schema.md#what-earns-a-test-and-what-makes-its-red-believable),
where a guard's red has to be believable rather than merely present. With the address and the
credential resolved inside the transport, both guards would be walked
past. A site carrying a path and a shell holding no token both read as *the call went out and the
host answered*. Both guards sit above the seam, as in the card implementation, and the transport is
handed an address and a credential rather than reading either — so a guard on either is a guard
every transport is held by, the substituted one included.

The same standard,
[`schema.md § What earns a test`](../plugins/mjolnir/config/schema.md#what-earns-a-test-and-what-makes-its-red-believable),
holds the port contract's suite: it registers a double against a kind nothing is installed for,
and a kind chosen out of the set the surface states runs out once every kind is implemented,
leaving the block unasserted while reporting a failure nobody could fix. So the kind is **derived**
from a stated word rather than chosen out of the stated set.

What this leaves unestablished: no call has been made to a running host through the interface the
adapter speaks, so every reference-only row above is the reference's word and nothing beyond it.
What a run takes is the site and the pair of variables
[`examples/jira.yaml`](../plugins/mjolnir/config/examples/jira.yaml) names, and the shell this
repository's own roles are handed holds neither.

## What is an ordered list of named checks rather than procedure

No count is given, for the reason [`schema.md § The
loop`](../plugins/mjolnir/config/schema.md#the-loop) gives for the axes: a number in this heading
would have gone wrong when what counts as done was added, while the gate stayed green.

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

The evidence here is a project's **written rule** rather than a reading of its role copies, and it
carries no count of projects: two are known to state the rule, and the source does not enumerate
the six. **Neither of the two could be configured as the other**, which is what made the entry a
list with an answerer per check rather than a flag:

| | what its rule says | what answers it |
|---|---|---|
| one project | a manual test on the running application is required before merging; a green gate plus a clean review is not enough | a **person**, and not the procedure |
| another | an acceptance scenario suite that needs the application running, **and** a checklist carried on the pull request | the **procedure** for the first; a person for the second |

The first project's reason is structural rather than cultural. Its own documentation says the whole
automated suite runs in one process against doubles — no messaging platform, no model provider, no
embedding service, no database over the wire — and names the user-visible behaviour that is
therefore verified by hand: the rendering of buttons, file uploads and message chunking, and a whole
submit-through-report flow for which it states outright that no automated test exists. A role that
read that gate as *done* would report a feature shipped on evidence that never touched the feature.

The procedure cannot perform that check itself. The credential it would drive the
application with acts *as* the application rather than as a user, so the finishing role can hand
over a type-this/expect-that script and then only **record a verdict it did not produce** — which
is why the surface carries who answers a check rather than just which checks there are.
Collapsing the two answerers loses a real check in the other direction: the second project's
acceptance suite is a machine reading a machine, mirrored by no workflow at all, and configured as
human-answered it would stop every completion for a hand-over nobody needed — the gate somebody
turns off.

Hence the ordered list and its per-check answerer, in
[`schema.md § 13`](../plugins/mjolnir/config/schema.md#13-what-counts-as-done--an-ordered-check-list-and-who-answers-each-check).
And hence the refusal of a check the host already runs
([`§ 17 → A local check the host already runs`](../plugins/mjolnir/config/schema.md#a-local-check-the-host-already-runs-is-a-misconfiguration)):
every check in the table above is mirrored by no workflow at all — a hand test on the running
application, an acceptance suite needing it up, and a checklist carried on the pull request —
which is the shape the facet was derived from. A check that *is* mirrored needs no entry, because
the host has already answered it, and these two measurements supply no example of one.
This measurement does not support a definition of done for every project. A project whose
deliverable is a library has nothing to drive, so the absent case is `[]` and is first-class rather
than degenerate. How common it is was not measured: this rests on two projects' stated rules and
says nothing about the rest.

## Which item is next is read, never derived

[`schema.md § 12`](../plugins/mjolnir/config/schema.md#12-ordering) is the thinnest facet on the
surface, and it rests on two shapes, not a count across the six projects.

- **One surveyed copy of the starting role checks an item's position in a priority queue** — the
  eight-check copy named in the readiness-gate section above. A gate whose input is a convention is
  the shape this document catches, and that check's input is a facet of its own
  ([`schema.md § 4.6`](../plugins/mjolnir/config/schema.md#46-priority)) rather than anything this
  ordering supplies: the two are different questions, which is why a project may configure either
  without the other and why neither reads the other's key.
- **This repository's own ordering is a row table in a document outside every tree**, in the agent
  harness's per-project store, with the argument for each row written beside it. Nothing shipped
  from a plugin can reach that file. The role that needed it read it through a carrier only this
  project resolves, which is the duplication the extraction is for, one level up.

The two have nothing in common but their output, which is why the facet is a pointer. A tracker
query answers it on one project and a document answers it on another, so an operation on the port
([`schema.md § 3`](../plugins/mjolnir/config/schema.md#3-tracker-port)) would oblige every adapter
to answer a question its tracker does not hold — and a rule in the procedure would have the toolkit
ordering somebody's work, which is the one judgement here that is never the toolkit's.

A project with no ordering is not a
project whose next item is the first row of whatever the tracker listed: that reading turns
*nobody decided* into *this was decided*, which is
[`schema.md § 2`](../plugins/mjolnir/config/schema.md#2-code-host)'s absence-of-signal rule one
store over. So `carrier: none` makes a role ask for an item by number, and the plain-issues
example is written that way rather than given a query to look tidy.

## The work-item facets, and the absent case

Issue type ([`schema.md § 4.1`](../plugins/mjolnir/config/schema.md#41-type)), status
([`§ 4.2`](../plugins/mjolnir/config/schema.md#42-status--an-ordered-set-of-name-role-writer)),
estimate ([`§ 4.3`](../plugins/mjolnir/config/schema.md#43-estimate)), template
([`§ 4.4`](../plugins/mjolnir/config/schema.md#44-template)), priority
([`§ 4.6`](../plugins/mjolnir/config/schema.md#46-priority)), code root
([`§ 4.7`](../plugins/mjolnir/config/schema.md#47-code-root)) and the grouping a set of items is
planned into
([`§ 4.8`](../plugins/mjolnir/config/schema.md#48-grouping--what-a-set-of-items-is-planned-into))
are each per-project, and each was carried by a different mechanism depending on the project.
Each but status has a real absent case of its own — which is where the schema's
absence-is-a-configuration rule comes from: a procedure that treats absence as an unset value
fails on a project that is correctly configured.

- **Type** — five carriers observed: a native field; a label convention, on a
  user-owned repository; a bare label whose absence means the other
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
- **Priority** — three projects carry one, between them over two carriers; a fourth parses a tier
  and writes it nowhere; two have no convention at all. A carries a four-value prefixed label axis
  on its board:
  exactly one label per card, never absent, and it is the input to the eight-check gate named in
  the readiness-gate section above. C uses the tracker's own priority field, three of its values.
  F labels its top tier alone with a prefixed label and leaves everything below it bare. B's
  filing role takes the same `high | medium | low` argument the other two take and has nowhere on
  its board to put it, which is the absent case with a working loop around it rather than a gap in
  one. D and E carry nothing. The two that share a tracker kind do not share a prefix: F's axis and
  this repository's own are both prefixed labels on plain issues and the prefixes differ, so a
  procedure matching a literal would read one project's axis and no other's.

- **Code root** — the one project with more than one code repository
  ([counted in the sibling document](build-surface.md#a-verdict-is-a-command-a-root-and-a-condition))
  **carries this fact nowhere.** A's instructions file records the consequence as a rule rather
  than as a gap: *no skill on the route drives* the second one, so that repository's branches,
  pull requests, dispatch and board moves are done by hand against its own equivalents.
  The same file states what decides which repository a card belongs in — *whose code it is, never
  which track asked for it* — and the case it gives is the one that discriminates: a counter, a tag
  set and a consent gate are all one track's need, and their code is in the repository that track
  does not own. Two of that board's label axes look like candidates and answer neither
  question — one carries whose need the work serves and one carries who does the work — so the fact
  is neither carried nor derivable there. That is the absent case with no loop around it: the
  carriers a tracker could hold it in are a label, a field, a component or a title prefix, and
  nothing was found holding it in any of them.

- **Grouping** — read in three places, and the richest of them is the project with **no tracker**,
  whose plan for a set of items is a document of its own. Measured directly from that project's
  specification tree on 2026-10-30, rather than from a role copy, because the grouping there is not
  a role's input at all — it is a document a person maintains, which makes it the one reading that
  shows what a grouping *is* rather than what a gate asks about one. The shape, item by item:

  | What was asked | What the tree shows |
  |---|---|
  | what a grouping is | a numbered plan document, one per grouping, the active one beside the specification and the finished ones moved into an archive directory. The items are grouped **into** it: the document carries the list, and each item names the grouping in its own front matter |
  | how an item says which one it is in | a named field in the item's front matter, holding the grouping's number. ⛔ Not a label, not a path, not the directory the item sits in — the directory says only whether it is archived |
  | how the current one is found | a status field on the grouping itself, with exactly one marked active. ⚠️ **Discoverable**, then — and the whole reason that is a key is the measured contrast: on the tracker in the next bullet several of the equivalent are open at once with no such mark |
  | what lifecycle it has | fields in the grouping's front matter: the status, the time it was archived, the branch its kickoff cut, and the time it was frozen. A kickoff, a freeze and an archive, each with a slot to record it in |
  | whether it carries its own acceptance | **yes, and the document says so in those words** — an acceptance-criteria list labelled milestone-level, beside a gate command. ⛔ So the bar a change is judged by is not on the item at all, and a role reading the item alone would be holding the work to a standard nobody wrote there |
  | whether closing it closes its items | **yes, and the timestamps are the evidence.** Every one of the twelve archived items names the grouping that closed; nine carry the grouping's own archive time to the second, and three carry earlier, distinct times of their own. So the close swept what was still open in it, and an item may also close on its own first |
  | who closes it | a person, in the pass that cuts the release. There is no automation in that tree and no role on this surface drives it |
  | whether a version runs beside it | **not established.** Nothing in that tree carries a version at all, so the one grouping is both the time box and the release scope, and the lockstep reading — a version tracking an iteration one for one — is *not* what this project shows |

  Its carrier is the one thing that does not generalise, which is why no key was added for it: the
  grouping is a file in a tree, and a tree is the tracker
  [`schema.md § 3`](../plugins/mjolnir/config/schema.md#the-trackerless-adapter-and-a-kind-with-no-implementation)
  declines to grow an adapter for. What the measurement supplies is every key *except* the
  carrier — the kind, how the current one is found, the acceptance, the closer, and whether the
  close reaches the items — and the carrier arrives when those items move onto a real tracker.

  **The other two readings are gates rather than documents, and between them they forced the
  collection.** One tracker's copy of the starting role refuses an item with no sprint, then one
  with no fix version, then one whose release branch for that fix version is missing from the
  remote — **two groupings in one project**, two fields, two checks, and the third check a ref
  named after the second one's value. A board's copy gates on a grouping instead, and both copies
  are stated in the readiness-gate section above. Neither gate carries anything else about its
  grouping — not which one is current, not who closes it, not
  what it is judged by — so what those two copies establish is the *number* of groupings a project
  has and the questions a gate asks, and the document above establishes what a grouping holds.

  Both gates carry the project's own word for the grouping inside a `field_present` entry, which is
  the finding that made this a facet rather than two more predicates: the check states a
  field and nothing else, so the sprint and the fix version are spelled in the gate and no second
  project can adopt that gate without renaming its own fields. That is the indirection
  [`§ 4.2`](../plugins/mjolnir/config/schema.md#42-status--an-ordered-set-of-name-role-writer) was
  built to keep out of the procedure, one layer up — and
  [`§ 5`](../plugins/mjolnir/config/schema.md#5-readiness-gate--an-ordered-predicate-list)
  refuses that exact pair with the field named.

  The absent case is not the exceptional one. A flat backlog ordered by its blockers and a tier
  plans nothing into anything, and the shipped examples carry `none` with a reason wherever the
  tracker has nowhere to put one. This repository is itself such a project —
  [`building-itself.md`](building-itself.md#the-absent-facets-this-repository-depends-on)'s subject.
  The evidence is thin for a facet this size: two gates and one document. That is why every key
  traces to a row of the table above rather than to a shape that seemed likely, and why the ref
  carrier the document shows was left off the surface instead of generalised from one project.

**What priority needed that the other facets did not: a statement of how two items compare.** The
others answer a question about one item — what type it is, what it is worth, which template it
used. This one is read by a check that asks whether work ranking above an item is ahead of it, and
two measured axes answer that two ways: one ranks by a four-value list whose colours happen to run
green to red, and another by a single label whose absence covers everything else. Hence the ordered
`values` list and the rule that an item carrying none is unranked rather than lowest, both in
[`schema.md § 4.6`](../plugins/mjolnir/config/schema.md#46-priority) — and hence the refusal there
rather than a check reporting itself unanswered forever on a project that configured it with no
axis to read.

**And what it does not carry.** A's gate turns the tier into a due date through a four-row table,
which is the derivation the date facet's own paragraph at the top of this document declines to
generalise: no second project was found to have one. This repository's own axis is the other half
of why the facet is a carrier rather than a rule — its two labels sat on the host while what they
meant lived in a person's head and in one project-local script.

## The enforcement half: three keys, and the rest procedure

Three projects run process hooks — eight scripts across eight events in one, five inline guards in
another, three scripts in a third — and the roles that overlap across them are a capacity lease on a
shared resource, a gate on a merge with no human review, post-merge cleanup, a stale-branch check,
deny guards on a live path, and a recorder for a review answer. Run the boundary's test on each part
of the first two, and the split falls where the thing being described stops generalising.

| the part | does a role or a guard read it to decide what to do next | where it lands |
|---|---|---|
| what the resource is — a build daemon's slots, an app instance, a container stack, a database | no: nothing branches on it | nowhere. It reaches a guard as a name and a number and never as a kind |
| how many may be held | yes | `cap`, which already existed |
| what holds a place | yes | `subject`, which already existed |
| which calls put it at stake | yes: a guard takes a place or does not | `claimed_by`, a key. Four projects' claiming commands have nothing in common but being commands |
| how many are held right now | yes: it is half the comparison | `probe`, a key. **The one question the procedure cannot answer about somebody else's resource** |
| how long a lease counts | yes | `ttl`, a key |
| the comparison itself — a sum, and over distinct keys | no: it is the same arithmetic everywhere | procedure |
| what happens on contention | no | procedure |
| which direction a guard fails in | no | procedure, and the one of these that is not obvious |

[`schema § 10 → Exclusive resources`](../plugins/mjolnir/config/schema.md#exclusive-resources)
declares all of them, and
[`schema § 7 → A lease on an exclusive resource`](../plugins/mjolnir/config/schema.md#a-lease-on-an-exclusive-resource-and-the-exit-paths-that-release-it)
states what a guard does with them. The capacity rule measured on one project is *busy daemons plus
leases too young to have registered one, capped at two* — so a facet with `cap` and `subject` and
nothing else describes a lease nobody can take, there being no way to ask how many are held and no
way to know which call is asking.

**Why the fail direction is procedure and not a per-guard setting.** Both directions have a failure
that reads like success, and which of them is wrong is decided by the act rather than by the
project. A guard that refuses every call it could not reason about is a guard somebody turns off,
and then nothing is held at all — the
same argument [`schema § 13`](../plugins/mjolnir/config/schema.md#13-what-counts-as-done--an-ordered-check-list-and-who-answers-each-check)
makes for not demanding a person everywhere. A guard that allows an act it could not reason about is
only wrong where the act cannot be undone, and there the rule already exists: **silence is not a
yes where the answer would license something irreversible**, which
[`schema § The loop`](../plugins/mjolnir/config/schema.md#what-carries-the-item-forward-and-where-it-stops-to-ask)
states for an ask nothing answered and
[`schema § 7 → Which direction a guard fails in`](../plugins/mjolnir/config/schema.md#which-direction-a-guard-fails-in)
applies to a guard. A project that could configure this would be choosing whether its own merges
happen unread.

**What the merge gate can and cannot be keyed on, measured on two of the three projects.** One
carries a pair of hooks — a recorder for the answer and a guard refusing a merge where no record
exists — and the other carries a single hook holding every merge behind an ask that reads no record
and that no review can silence. They are not two halves of one design: the second cannot be
satisfied, so it is argued with, and a guard that is argued with is a guard nobody has to satisfy
again. The first is the one extracted, and what it needs that nothing stated is the record's own
form — which is why
[`schema § 7 → What a hook refuses, and the record it reads`](../plugins/mjolnir/config/schema.md#what-a-hook-refuses-and-the-record-it-reads)
fixes the keying rather than leaving it to whichever role wrote the answer. The measured failure
there is specific: that project's recorder keys the answer by repository and number, so a question
that named the change ambiguously recorded nothing and left the merge blocked however it was
answered.

## The spend half: three instances, and the key that is not sugar

Three projects have a command that costs money when it runs, and only one of them has a guard. The
first is where the guard comes from: one tier of its suite costs real money a run against a budget
that is finite and **has already been exhausted once**, which is the tier
[`build-surface.md`](build-surface.md#the-tiers-what-each-needs-and-which-are-asked-for) records
with the figure, beside the one environment another project refuses by name because its quota is
what caps that product's throughput. The second runs an end-to-end suite that spends a paid
quota on every run, takes about forty minutes, and is deliberately in no workflow at all — and the
quota it draws is the one that caps that project's production throughput, so an unsupervised run
does not merely cost money, it slows the product down for as long as it runs. The third runs
validation harnesses that call two paid providers live on purpose, one grading the other so the
judge is not the generator's own family, several of them matrices whose cost scales with a run count
read from the environment.

Neither the second nor the third instance names a script a guard could recognise. The second's paid
command is an ordinary invocation of the runner that also runs its cheap suites; the third's are
invoked exactly like the free unit tests beside them — same command prefix, adjacent names, same
runner. So the decision rests on the arguments, and `args_match` is not sugar on a command name:
[`schema § 19`](../plugins/mjolnir/config/schema.md#19-a-command-that-spends-and-the-supervision-it-is-refused-without)
declares it beside `command` for that reason, and a facet with `command` alone would describe one of
the three.

| the part | does a role or a guard read it to decide what to do next | where it lands |
|---|---|---|
| which commands spend | yes | `deny`, a key. The three projects' paid commands have nothing in common but being commands |
| what separates a paid invocation from a free one by the same binary | yes: it is the whole decision in two of the three | `args_match`, a key |
| what the call costs | yes: a refusal names it | `reason`, a key. **The figure itself never leaves the project** |
| whether a go covers one call or more | yes | `approval`, a key with two values: the legitimate uses are frequent in one instance and a metered release in another |
| how much of a budget is left | no: there is no figure the procedure can read | nowhere, by the threshold argument [below](#why-there-is-no-threshold-on-the-surface) |
| where the command is in a call | no: it is the same parse everywhere | procedure, and the one of these that was paid for |
| which wrappers stand between a call and its command | no | procedure |
| what an unanswered ask becomes | no | the harness's, which is why the facet states no timeout |

**Why the approval is a key and the positional rule is not.** The two look alike — both are *how
strictly this is held* — and only one of them varies: the first project's legitimate uses are the
same command differently scoped, run deliberately several times a week, so an approval it had to
re-ask per session would be an approval nobody would keep; another project's spend is a release to a
metered environment, where an answer given inside a session is a go for an act that reaches a live
system. The parse varies in no project at all, which is why
[`schema § 19 → The command position`](../plugins/mjolnir/config/schema.md#the-command-position-and-why-the-whole-call-is-not-one)
states it as procedure — and a guard that greps the raw command refuses a text edit whose prose
contains a script path, as that guard's own header records.

## The live half: one guard, and the two lists that are not interchangeable

One project carries a deny guard in front of a shell command that could open a session on the
machine it runs on — "deny guards on a production path and on a route", as #16 recorded the pair —
as a hook of its own with a test matrix beside it. The matrix is why it is extracted rather than
written from the idea: the verdict rule, the inversion and the four closed directions are each a
line somebody was taught by a failure.

**What the verdict depends on is not the command but who would answer the prompt**
([`schema § 21 → Which verdict`](../plugins/mjolnir/config/schema.md#which-verdict-and-who-would-answer-the-prompt)):
a mode a person answers gets an ask, a mode that answers its own prompts gets a refusal, and an
unrecognised mode is read as the second. A guard that always asks enforces nothing in a run nobody
is watching, and a guard that always denies is one somebody turns off.

| the part | does a role or a guard read it to decide what to do next | where it lands |
|---|---|---|
| which commands open a session elsewhere | yes | `session_tools`, a key. Two projects' session commands have nothing in common but being commands |
| which flags of such a command take a separate word | yes: without them the flag's value stands where the machine should | `valued_flags`, per entry, because the command is the project's |
| which machines are not live | yes | the file `allowlist` names, **outside every working tree** |
| which names reach nothing | yes | `local_names`, a key, a loopback name being nobody's identity |
| which machine is live | no: it is every machine no list names | nowhere, which is the inversion |
| who would answer the prompt | no: it is the harness's own state | procedure, and the line this guard exists for |
| where the command is in a call | no: it is the same parse everywhere | procedure, and `schema § 19`'s already |

**Why the two lists are not one key.** The allowlist is a file on a machine and `local_names` is a
line in a repository, and the test that decides which a name belongs in is whether the name
identifies *another* machine: a loopback name does not, and everything else does
([`schema § 21 → The machines named`](../plugins/mjolnir/config/schema.md#the-machines-named-are-the-ones-that-are-not-live)).
Collapsing them into one configured list would put somebody's infrastructure into a repository
anybody can clone, which is the one thing this facet is organised to prevent; collapsing them
the other way — a file for both — would make a loopback name a per-machine fact that every new
checkout has to be told.

**Why the absence of the file makes the guard stricter rather than quieter.** A machine where
nobody has written the list yet is one where every name that list would have cleared reads as live,
so a half-set-up machine is safe by default and the remedy is visible in the refusal
([`schema § 21 → The four ways it fails closed`](../plugins/mjolnir/config/schema.md#the-four-ways-it-fails-closed)).
That is the opposite of how a missing configuration file usually reads.

## One rule that is procedure everywhere

The estimate/measurement separation in
[`schema.md § 4.3`](../plugins/mjolnir/config/schema.md#43-estimate) — a bound written before
the work against a measurement written after, with a number never moving between them — is
stated by one project and true in all of them: the single rule the survey found already
universal.

## The unit tier: six files of rulings, and no role reading any of them

Read across the same six projects' instructions files. Four carry a unit tier of **101, 85, 74 and
48** cases; of the other two, one holds two specification files with its runner commented out of the
host's own test workflow, and one has no automated suite at all. So the tier is not a minority
practice — and the rules governing it are written in **one** of the six files each, two for the
single rule that two state:

| the rule | how many of the six state it |
|---|---|
| a test is a ceiling rather than a floor, and the list of cases is the intended extent | 1, and it alone states the consequence |
| fakes over mocks, with the seam named | 2, one of which also states the sharp end — mocking the store proves nothing, so that tier runs against a real one |
| the violation is written first and the red confirmed | 1 |
| assert values and never key sets; a fixture thinner than the production shape tests the fixture | 1 each |

No role reads any of them: each is advice a careful reviewer would give in any of the six, held
where one project's sessions can reach it and no other's. Hence the statement as procedure in
[`schema.md § The loop → What earns a test`](../plugins/mjolnir/config/schema.md#what-earns-a-test-and-what-makes-its-red-believable).

A further rule in that subsection is not a row above, because no file of the six carried it: what a
test is **derived from** was settled against the published work
([the reading](test-first-for-a-model-writer.md)). The table is what the six projects had, not the
subsection's inventory.

**Why the surface, and not either of the two homes it was weighed against.** The discipline is read
by two legs — the implementing one and the reviewing role — and
[`schema.md § The loop`](../plugins/mjolnir/config/schema.md#the-loop) already settles what follows:
a rule read by two roles and written in one of their skills is a second authority for the other.
Promoting these rules into the reviewing role's own text is therefore the option with a precedent
against it — ruling 11's reasoning. A
per-project pointer — the shape the role-to-person map takes — fails a different test: a pointer
carries values a role reads, and none of this is a value. Six copies free to disagree is the
defect the extraction deletes rather than a configuration of it.

**What was not promoted.** A coverage figure is set in one
project's runner configuration, written as a placeholder in a second, and stated by neither of the
remaining four; promoted on that evidence it would be one project's taste imposed on five. The
case-file naming, the package-mirroring layout and the decision *not* to sit cases beside the code
they cover are one project's and are stated by none of the others.

One of those local conventions shows why a local rule is named rather than left out — a
tier-boundary defect rather than a naming one. A project carrying nine
cases against a dependency it stands up itself, under a distinct suffix, states that suffix
**nowhere** in its own testing conventions, which list the framework, the mocking policy, the file
naming and the layout — all four of them the unit tier's — and then stop. The tier it leaves
unmentioned is the one its own build cannot run unaided, and a convention nobody wrote down is not a
convention a migration can carry.

## The register nothing compared to the suite

One project of the six carries an end-to-end tier with a record of what it covers: **14 scenario
groups**, a register table in that repository's own instructions file, and **two checks in the
host's lint workflow** holding the three together. Measured 2026-10-19; it is the only one of the
six where the record exists at all.

The first check compares the register with the scenario files **both ways**, and its own stated
reason is the failure neither direction shows on its own: the run prints its scenarios, the
register prints a shorter list, and nothing compares the two. It was written because one group sat
unlisted while the register was otherwise accurate — a list that is wrong by one row, in the
document a reader trusts to say what is covered.

The second compares the suite with the **change**: a pull request touching the source tree that
carries neither a new case nor a register row fails, and the escape is a section of that same
document reading *what is deliberately not covered, and why*. Its rule is the one the facet keeps:
an uncovered change is allowed; an uncovered change nobody wrote down is not
([`schema.md § 15`](../plugins/mjolnir/config/schema.md#15-end-to-end-coverage-recorded)).

Its stated limit is one an adopter inherits. It judges one tree, so a
change to the container or deployment trees passes unremarked and a reviewer stands in for it
there. That limit is carried onto the surface as the `judged` key and the run's own report of what
it left unjudged, rather than closed by widening the judgement: a check that asked for an
end-to-end case on a change to the thing that builds the image is a check somebody turns off.

Nothing of the kind exists in the other five. In the project carrying 12 end-to-end case files,
which cases pin which behaviour is recorded in prose — a section of the README and each case's own
comments — so a case too old for an assertion is a paragraph rather than a check. What the
remaining four do about the tier was not measured; none of the five carries a record anything
compares to a suite.

**Why the comparisons generalise and the content does not.** The suite root, the glob a case file
matches, where the register lives, the heading its table sits under and which trees a behavioural
change lands in are each one project's decision — the same boundary the unit tier's four local
conventions sit on, one section up. *Does the register still describe the suite* and *is this
change covered* are neither, and asking them needs no stack, no credential, no indexed material
and no money. So the facet states the five values and the procedure holds the agreement between
them, authoring none of it
([`schema.md § 15`](../plugins/mjolnir/config/schema.md#15-end-to-end-coverage-recorded)).

**Why it is a host check rather than a local one.** A command the host already runs is refused as a
local check by
[`schema.md § 17`](../plugins/mjolnir/config/schema.md#a-local-check-the-host-already-runs-is-a-misconfiguration),
and this one belongs on the host for the reason the measurement gives: it is the cheap half of a
tier whose expensive half cannot run there at all. The suite itself is the opposite case — a
command no workflow mirrors, which is what that facet states and what a `done:` list's `local`
check reads.

## A tier that executed nothing, and the build that said so

Measured across the six consumers, 2026-10-19. The tier in question is the one whose dependency is
**stood up** rather than deployed — a store the subject talks to over its real protocol, created for
the run. It is the only tier that can degrade to nothing at all while reporting success, because
the thing it needs is created by the run, so its absence
is a condition the runner handles and not a connection that fails.

The dependency arrives two ways, and the split decides who can answer the tier at all:

| how the dependency arrives | consumers | what the absence looks like |
|---|---|---|
| the **run** stands up its own container | three | the host answers only where its runner has a container daemon; locally, a missing daemon and a silent suite read alike |
| the **host** supplies a service beside the run | two | the local run skips silently, and the suite's own gate is one environment variable |
| no such tier | one | — |

So «the host cannot run this tier» is false here, which is why this is not the unrunnable-tier
axis one tier down: the host usually *can*, and the defect is that it says so whether or not it did
([`schema.md § 16`](../plugins/mjolnir/config/schema.md#16-what-a-run-executed-and-the-count-that-is-the-only-evidence-it-ran)).

**What it cost, in the one consumer where it was priced.** Three suites covering that project's
money rules are gated on a single environment variable, and without it they abort as *skipped*
while the aggregate build still reports success — so a green build said nothing about the rules
those suites exist for. That project's own workflow supplies a service beside the run and **fails
the build when any of the four suites it names reports zero tests or any skip** — the fourth is
outside the money rules and is on the list because the rule is a list of names rather than a
property of a suite, so a gated suite missing from it is exactly as silent as having no service
container. That rule is written into one workflow file, mirrored by nothing, and stated nowhere
on the surface it was read from.

**Why the count, and why it is not a coverage figure.** A dependency-gated suite's degradation is
*designed* to be quiet: skipping is the correct behaviour for a case whose dependency is absent, and
the defect is the aggregate reporting a pass. So what separates the two is arithmetic the run
already has — how many executed, how many skipped and what each skip wanted, against how many the
tree declares. The rule stops at one floor rather than becoming a percentage: a threshold
reddens on the count being wrong, which is a defect in the declaration rather than in the tier, and
a check that reddens on a figure nobody maintains is the check somebody turns off. What the rule is
therefore held to is the surface's
([`schema.md § 16`](../plugins/mjolnir/config/schema.md#16-what-a-run-executed-and-the-count-that-is-the-only-evidence-it-ran)).

**Why it generalises and the commands do not.** How many cases a tree holds and what a run printed
are each one project's command, written in that project's own runner; *did anything execute* is
neither, and asking it needs two numbers. So the facet states the commands and the floor, and the
procedure does the arithmetic — naming no runner, no task name and no report format, which is the
same boundary the local-check and unrunnable-tier facets sit on.

**Why it is a host check rather than a local one.** For the reason the register one
above is: a command the host already runs is refused as a local check by
[`schema.md § 17`](../plugins/mjolnir/config/schema.md#a-local-check-the-host-already-runs-is-a-misconfiguration),
and this is the cheap half — two numbers — of a tier whose expensive half is the run itself. And
the honesty it adds is pointed at the **host's** verdict, where the four-valued rules already
landed stop: a job whose every step ran and whose suite executed zero cases satisfies all of their
preconditions and reads green.

## The strongest argument for extraction is not borrowed

Read-it-from-one-place has been **independently invented six times** across these projects, in
five different stores — a sibling reference file, a reference document, the project instructions
file, a memory index, a memory fact, and the rules file a document checker walks its graph from —
each with the same justification stated in its own words. Two of them:

> a copy that has to be «kept in sync» is the defect rather than the maintenance burden

> Two records of who owns the work that are allowed to disagree are worse than one

The sixth is the only one found **outside** the process roles:
a checker that holds documents to a declared reference graph deliberately reads that graph from the
rules file a person maintains, *so that the graph a machine walks and the statement a person
maintains are one thing*. Same conclusion, reached in a different problem.

Six instances, five stores, one pattern — which is itself an argument for the toolkit picking one.

## Prior art

A public MIT plugin for an adjacent process — spec-driven development and TDD rather than this
loop — already solves the two hardest parts in the shape proposed here: one directory per tracker
with a template for adding another, and a tracker configuration that is a status list plus a
roles map indirecting the procedure away from the words — independent confirmation of the status
design. It is superseded rather than adopted because of its
adapters: seven entries, of which only two are real trackers, and **neither is one any project
in scope runs**. <https://github.com/nesquikm/dev-process-toolkit>

## The window is a resource the loop spends

[`schema.md § 11`](../plugins/mjolnir/config/schema.md#11-session-context) is the only section of
the surface derived from measurements taken outside these six projects as well as inside them.

### What the published measurements establish

- Input length alone degrades performance. Eighteen frontier models, 194,480 calls, task
  complexity held constant and length varied: every model degraded, and not at the window's
  limit — a single irrelevant passage beside the relevant one measurably costs recall, and four
  compound it. Their impact is not uniform, in the source's own word; it does not measure
  similarity, so nothing here reads the cost off how alike the passages look. A coherent haystack
  is worse than a shuffled one, and the source declines to explain it.
  <https://www.trychroma.com/research/context-rot>
- The vendor's own framing is an attention budget — a finite resource every token draws on —
  with three techniques for spending it: summarising a window and restarting from the summary,
  writing notes outside the window, and spending a separate window on a sub-task. The first is
  lossy, which is why § 11 makes the artifact the handoff rather than the summary.
  <https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents>
- The published practice this loop's shape is closest to keeps a window at 40–60 % of its
  capacity — a figure it says depends on the problem's complexity — separates research from
  planning from implementation into different windows, writes each phase's output to a file that
  is the real handoff, and spends human review on the plan rather than on the diff — *a bad line
  of a plan leads to hundreds of bad lines of code; a bad line of research, thousands*. Its ranking
  of what hurts is why § 11 is about what enters and what crosses a boundary rather than about
  token counts: incorrect beats missing beats noisy.
  <https://github.com/humanlayer/advanced-context-engineering-for-coding-agents>

### What this repository measures about itself

No count of this tree's own files is written here: a number copied out of the tree drifts the
moment the tree changes, silently and green. The gate prints each file's footprint in its own
run's output instead, as of [#91](https://github.com/ragnor-rs/mjolnir/issues/91).

A single role runs to thousands of tokens and carries dozens of ⛔ and ⚠️ markers, and there is
one per leg the loop names ([`schema.md § The loop`](../plugins/mjolnir/config/schema.md#the-loop)).
A window largely spent on procedure before a line of anyone's code is read is what § 11 exists to
notice, and the harness vendor's own guidance is that an over-long instructions file is not read
selectively — it is ignored wholesale. <https://code.claude.com/docs/en/best-practices>

A role's body is loaded only when the role runs; only its frontmatter — a name and a description —
is always resident. A role that cites the surface to settle one sentence resolves the whole of it,
which is the argument for a citation naming the narrowest section that states the fact. Since
[#91](https://github.com/ragnor-rs/mjolnir/issues/91), every heading of the surface is held to
being motivated by a document whatever its level, and a citation resolving to a `##` section with
no text of its own is refused by name; the coarser case stays a count rather than a verdict, as
[`single-source-of-truth.md`](single-source-of-truth.md#what-the-granularity-check-deliberately-does-not-hold)
records.

### Why there is no threshold on the surface

The harness exposes a window's utilization at one moment only, and never while a window is
filling. Of its hook events, only the one that fires when a session is resumed or forked is
documented to carry a token count — alongside the time since the last response, whether the prompt
cache has likely expired, and the estimated cost of rewriting it — and the event that fires
immediately before a window is summarised carries no count and no threshold.
<https://code.claude.com/docs/en/hooks>

So a `budget: 60 %` key would be a number nothing could check at the moment it is exceeded: a
convention, which this repository calls a defect. The test a key must pass is whether there is a
run-time reading to enforce it against; § 11's own in-tree rule passes it on three keys the reader
already holds. The qualitative rules are stated instead, and the one live reading goes where
something already reads it: the spend guard's own bar at
[`schema § 19 → What an approval is per`](../plugins/mjolnir/config/schema.md#what-an-approval-is-per-and-the-one-price-stated-before-a-turn-runs),
which reports a resume priced above it and reports no figure where the harness gave none, and
[`schema § 24 → The window's own reading`](../plugins/mjolnir/config/schema.md#the-windows-own-reading),
the role that restores a session, for the context half of the same payload. Both arms are written
around that payload carrying nothing, for the reason below.

### What a resumed session is actually handed

The field list above is the vendor's documentation. Probed on a resumed session, the `SessionStart`
payload carried five fields and none of the four the documentation names: the session's own
identifier, its transcript path, the working directory, the event name and `source: resume` — no
token count, no time since the last response, nothing about the prompt cache, and no price. The
harness probed was eighteen patch versions older than the one the fields are documented from, and a
machine running this toolkit is as likely to be behind as current.

- An arm relying on those fields reports nothing where they are absent, and nothing is
  indistinguishable from a cheap resume. So both arms are written around the absence: the price
  half reports *no figure* rather than *free*, and the context half says it was handed no reading
  rather than describing an empty window.
- A tested-absence claim about a harness event is an assertion until a probe answers it. The probe
  is a settings file supplying one hook, a print-mode session, and the same session resumed; the
  payload lands in a file and the question is answered in two commands.
- What the probe measured is a version, not a contract, so the arms read the fields where they are
  present, and a reading that arrives later is reported with no edit. The rule is
  [`schema § 24 → The window's own reading`](../plugins/mjolnir/config/schema.md#the-windows-own-reading)
  rather than anything stated here.

### What a compaction leaves behind, and what it does not take

The restoring role's replay answer rests on this. A compaction appends to the transcript it
summarises rather than replacing it: one `system` record carrying the compaction's own metadata —
its trigger, the token count before and after, and the cumulative total dropped — and one `user`
record flagged as the summary, marked visible in the transcript only. Measured on one of this
repository's own compacted sessions: 617,688 tokens before, 14,285 after, 603,403 dropped, and 426
tool calls still in the file ahead of the boundary, 132 of them calls that wrote a file, each with
its full input.

- So a compaction costs the window and not the evidence. A file a session wrote before a
  compaction is as replayable after one as before it — the difference between *lost* and *out of
  the window*;
  [`schema § 24 → What a load may not assume survived`](../plugins/mjolnir/config/schema.md#what-a-load-may-not-assume-survived)
  is where that is a rule.
- The replay's limit is the first call, not the compaction. A file the session wrote whole is in
  the record with its content; a file it only ever *edited* is in the record as a set of
  differences against content nothing there holds. The harness keeps the pre-edit copy in a store
  of its own, which the sweep names rather than reads.
- One logical session is one session transcript. Across 863 session transcripts in this machine's
  store — the top-level files, not the 2,406 files the store holds in all — none carried records of
  a session other than the one its name states, and a resumed session probed directly wrote to the
  same path it had before. So *the last session* and *the last session transcript* coincide, and
  the sweep is written against the file.
- The sidecars go the other way. In this project's own store: 153 subagent transcripts and 41
  tool-result directories against 138 session transcripts, and every sidecar sampled carries its
  parent's session identifier. Delegating to a sub-window is the practice § 11 recommends, and it
  writes its trace out of the file a sweep reads — so the sweep counts what is beside it and says
  it counted rather than read.

### Why `committed` is a key of its own, and not implied by `dir`

Under [`§ 10`](../plugins/mjolnir/config/schema.md#10-branch-model)'s `worktree` model the
teardown removes everything git does not have, and a per-item plan is exactly what a tree holds
and the repository does not. So an in-tree store and an uncommitted store are safe in opposite
cases, and a single path key could not say which was intended.

Measured on this repository, 2026-10-18: the one artifact several concurrent sessions coordinate
through is a plan file carried in no configuration and committed nowhere. It lives in the agent
harness's own per-project store, beside the session transcripts, while the standing convention
that tells a session to read it names a path beside the repository — which does not resolve. The
file and the pointer disagree, and nothing reports that: a session following the pointer finds
nothing, and a session that knows better depends on a store no key names.

### Why the read-side rule lives here rather than beside the write-side one

[`§ 3`](../plugins/mjolnir/config/schema.md#3-tracker-port) bars facts from reaching a card. The
read side is a different question with a different blast radius, and it spans three ports rather
than one — the tracker, the host's review and check surfaces, and whatever a role fetches — so
stating it under the tracker would have made two of the three a special case of the first.

The published incident is a code-host one: payloads written into pull request titles, issue bodies
and issue comments drove three separate agents into exfiltrating repository secrets back through
the host itself, with no attacker-controlled server involved.
<https://labs.cloudsecurityalliance.org/research/csa-research-note-comment-control-github-prompt-injection-20/> That is the measurement; the
rule it forced is [`§ 11`](../plugins/mjolnir/config/schema.md#11-session-context)'s. The
toolkit's own gate holds the other half of the same shape, by
[#50](https://github.com/ragnor-rs/mjolnir/issues/50)'s ruling: a workflow is granted no scope it
does not need and its checkout persists no credential — a rule about what a run may hold, not a
claim that every run holds nothing.

### Why the other two legs are a section of their own, and why only one of them has a key

What a role may *believe* is one leg of three. The other two — what it holds while it reads, and
what may leave with it — are
[`§ 14`](../plugins/mjolnir/config/schema.md#14-what-a-role-holds-and-what-may-cross-the-boundary),
a section of their own for three reasons.

The belief rule was already cited by a role and by this document, so moving it would have broken
two anchors; a section appended at the end breaks nothing.

One of the three is a project's fact and the other two are not. What a role's shell inherits
differs per project and nothing can derive it; the ingestion step and the outward refusal are the
same everywhere, and a key that let a project turn either off would be a key for deciding whether
this procedure publishes credentials. So the section carries exactly one key — the shape § 6 has
for authorship and § 8 for the reply's register.

The enforcement is one carrier for all three legs. The incident drove three agents through all
three legs in one pass; three scripts would have given each leg its own grammar, its own self-test
and its own chance to be the one nobody updated. What each arm reaches, and what none of them do,
are in
[`docs/single-source-of-truth.md`](single-source-of-truth.md#the-boundary-three-arms-two-of-them-held-in-the-session).

### What one run through the real tracker showed, and what it did not

The arms are planted in both directions by their own self-test, which reads text in memory. One
run was also made end to end through the host, because what the host's own rendering does to a
payload is out of reach of an in-memory plant: a throwaway item was filed carrying a comment that
renders as nothing, a zero-width character inside a word, and a visible announcement of fresh
instructions; the body was read back through the tracker port and passed to the ingestion step;
the item was closed in the same pass.

The step returned the hidden comment shown in full, the zero-width character located by line and
column, and four imperatives named — the instruction to set aside what the role was told, the
announcement, the address to the role, and the direction to act. Nothing in it was obeyed. The run
establishes nothing about a payload nobody planted: the forms it found are the forms the grammar
was written for, and the quoting limit on the imperative half is unchanged.

A review of the hook arm found two defects, each a shape the next command-reading guard will reach
for. The git subcommand was found by dropping every word beginning with `-` and reading the next
one, which left `-C`'s value where the subcommand should be — so no `git -C <root> push` was ever
outward, though [§ 1](../plugins/mjolnir/config/schema.md#1-roots) requires that form of every git
call in this procedure; the green plant passed either way. And an argument to a flag that *can*
name a file was read as a path unconditionally, so `-F title=hello` and `-d name=value` failed to
open and the hook falsely reported that a body could not be read, on two of the commonest outward
calls. Both now carry plants in both directions.

### Why the inherited set is names, and why its arm reports rather than refuses

A list of names is not a secret, so the configuration can carry it; the value cannot be carried
anywhere. The arm that reads it against the live environment reports rather than stops: a role
cannot replace the environment it was handed, so an arm that stopped would stop every session over
a fact the person running it already owns and can fix in one edit.

Each anchor in that arm's name grammar answers a false report on the shell it was written in:
unanchored, `auth` claimed an agent socket's path and `session` claimed two terminal session ids. A
guard whose output is noise is a guard that is off.

The empty list is a real configuration rather than an absent facet, so the key carries no `carrier`
and no `absent_reason`: a project whose roles need nothing beyond the shell's own variables has
stated what it hands a role.

## Bounding the window at the call, and what the harness gives a hook to do it with

[`schema.md § 22`](../plugins/mjolnir/config/schema.md#22-what-enters-the-window-bounded-where-the-call-is-made)
is the enforcing half of the section above.

The [findings recorded above](#what-the-published-measurements-establish) rank what hurts a window
and name summarising it as the lossy way to spend one; § 11 made the handoff a file somebody wrote.
The window is also spent one call at a time: a guard acting after the summary acts on what survived
it, and a guard at the call acts on the thing itself.

The harness publishes three places a hook can act, and a fourth this facet does not use. A hook
answering before a call may refuse it or replace its arguments outright; a hook answering after one
may replace what the call returned. The fourth is the event that fires before a window is
summarised: registered in every arm of the measurement recorded in the project store for this
repository, it never fired, so what it carries is unestablished rather than empty, and
[`schema.md § 7`](../plugins/mjolnir/config/schema.md#what-a-hook-can-establish-about-the-role-it-is-running-under)
states that a rule reaching it would be written against a measurement nobody has taken. So nothing
here refuses a compaction, and the arms that ship are the three that answer on a call.

**Why a result limit is a key while a window budget is not.** A result's own length is the opposite
case to the one
[refused above](#why-there-is-no-threshold-on-the-surface): the event that fires after a call
carries the result, so its size is readable exactly when there is something to decide about it. It
is the same test, passed.

**Why the exemption is a project's list rather than a case inside the guard.** This toolkit ships a
role that forbids truncating its own evidence output, because the measurement is recomputed whole
for the half that was cut off. A blanket bound would contradict a shipped role, and a name in the
guard's own code is one no project could see or extend. What a project may not truncate is its own
fact, as its mirrored commands are.

### What a hook may tell the session rather than the person

The rewriting arm is the first thing in this toolkit that changes a call and lets it run, so the
channel it reports through matters. A bound added silently is a bounded result read as complete —
a *wrong* premise instead of a noisy one, the worst of the three ranks quoted above.

The two channels are not interchangeable, and which one reaches the session was measured per
event — [recorded there](single-source-of-truth.md#the-rules-loaded-rather-than-checked). The field
that adds context is documented for the event before a call, and the installed client states its
support for it, which is what the rewriting arm rests on. The field's validity is per event — the
same document records one event rejecting it and failing the operation outright — so this is a
reading of a reference and a client, not of a run in this repository.

So the reports divide by audience rather than by severity: a call that was rewritten tells the
**session**, because the session is about to read a result it would otherwise misread; a
configuration that could not be read tells the **person**, because nothing the session does next
depends on it and the remedy is an edit to a file.

What the client does with a *replaced result* was read out of the client, the reference stating
only that the field replaces a result: a tool that is not an external one has its replacement
validated against that tool's own output schema, and a mismatch keeps the
original and adds an error. So a replacement takes the shape the response arrived in; one answering
with text alone would leave every oversized result whole with one more message beside it.

## The revision key never moved, and the markers took its job

What the surface now states is at
[`schema.md § The file itself`](../plugins/mjolnir/config/schema.md#the-file-itself): the key is
retired, a configuration still declaring it is refused, and a retirement is marked `# retired:`.
This section carries the measurement behind it.

`version` was in every configuration from the first commit that carried one (`6410f34`); the
surface named it only at `9451882`, where the single-source gate found a key every adopter writes
that the surface did not declare. Nothing read it, and it never moved through a run of changes that
each made an older configuration unreadable:

| Change | What it did to a configuration already written | `version` |
|---|---|---|
| `f40785e` — § 10, the branch model | added three required keys | stayed `1` |
| `1b11c52` (#83) — `roots.skills` retired | **refuses** any configuration still carrying the key | stayed `1` |
| `31e50d4` (#92) — § 11, the session's context | added a required `context.artifacts.carrier` | stayed `1` |
| `7f962c9` (#125) — § 12, the ordering, and `branch_model.tree_dir` | added a required `ordering.carrier`, and a `tree_dir` required under `kind: worktree` — so a configuration that already cut trees is **refused** | stayed `1` |
| `1a3789a` (#132) — § 2, how a pull request lands | added `host.landing.method` and `host.landing.delete_branch`, required with no marked default | stayed `1` |
| `8461104` (#133) — § 13, what counts as done | added a required `done` with no default, `[]` legitimate — a *decision* the refusal cannot tell from the absence | stayed `1` |
| `dbf4ef1` (#142) — § 14, what the shell inherits | added a required `environment.inherits`, `[]` again a decision rather than an omission | stayed `1` |
| `b9e8fd7` (#147) — § 4.5, the date the gating role owns | added a required `work_item.due_date.carrier`, absent-capable, so a configuration written before it is refused with the key named and states its decision through `absent_reason` | stayed `1` |
| `9bfa447` (#145) — § 3, the keys a tracker kind requires | added `# required_when`, so a tracker block that was complete before it is **refused** for keys that depend on a `kind` the configuration already declared | stayed `1` |
| § 4.8, the grouping above a work item | required `work_item.grouping.carrier` by a **rule of the reader** rather than by a marker, the key whose absence is refused differing between the facet's two forms — so every configuration written before it is **refused**, this repository's included until it stated the absent case. ⚠️ The first row whose requiredness no marker carries, which is why § 1's obligation names both routes | no key to move: the revision was already retired (ruling 12) |

A revision that moved on every required key would have been stale twice over inside the branch
that introduced the rule, since rows arrived there by merges from `main`.

Classified against the ruling, every row reads the same way: the key would not have moved. Each is a
configuration refused with the key named, which the marker beside that key already does.
`host.landing.method`, `done` and `environment.inherits` are why absorbing a new key with a default
was not available: the first has no default by design, since one would pick a merge method for every
project that did not notice the key, and the other two are facets whose `[]` the surface states is a
decision and *not* an unset key — so a default there would manufacture the very decision those
facets refuse to infer.

What settled it is `e62a1d9` (#137), which moved requiredness onto the surface and deleted the
reader's own list of it. Requiredness is marked beside the key, a legitimately unset key
carries no marker, and every facet with a real absent case carries a `carrier` whose
`absent_reason` is the decision written down. A configuration states its decision or is refused
with the key named — which is what the revision was introduced to separate, answered where the key
is declared.

What the retirement gives up is stated on the surface beside it, and the measurement behind that is
this table: on every row the remedy an adopter faces is the same act, so what is lost is a
diagnostic during a phase of rapid surface change rather than a behaviour. A configuration written
months earlier is told *which* keys are missing and never *that they are new*.

The retirement is held in both directions. The reader refuses a retired key, and its self-test
asserts both that the surface declares no such key and that a configuration still carrying one is
refused. Generated from the reader's own list alone, those assertions went with an entry: with the
`version` entry removed the suite stayed green on every assertion and the reader accepted
`version: 1` again — the defect the retired `REQUIRED` table demonstrated. The marker the surface
declares is read against the reader's own list in both directions, and a third arm catches a
derivation replaced with a constant, which left both green until a plant stripped the clauses out
of the surface and asserted the comparison notices.

The marker is a token, not prose. A grammar matching a backticked key followed by *is retired* read
`host.repo`, a live required key, out of a sentence stating it is retired in no sense. A negation
is invisible to a grammar of that shape, and prose is where negations live, so a machine-read fact
belongs in a clause with the prose beside it saying why.

## The boundary that was carved out six times

What the surface now states is at
[`schema.md § What the procedure models`](../plugins/mjolnir/config/schema.md#what-the-procedure-models-and-what-it-only-names-and-calls):
the test for a candidate key, what a configured command or path carries, and four worked cases.
This section carries the measurement behind it, taken on this repository's own backlog rather than
on the six projects the surface was derived from.

Six work items stated the same boundary, each on whichever item needed it, while the surface stated
none of it. What each body held on 2026-10-21, when the statement was written and each of the six
reduced to a citation of it:

| the item | what it stated |
|---|---|
| #13 — the deploy role | hosts, services, secrets, build steps and tier selection stay local, and a project whose deploy is one script keeps that script, called from the skeleton |
| #24 — the branch model | worktree setup that installs dependencies, copies assets, allocates ports or names a container project is called from the shared procedure, never absorbed into it |
| #16 — the hooks | hook paths, event names and the shared library are extractable; what counts as the guarded resource is not |
| #60 — the unrunnable tiers | the commands stay project-local, and no tier taxonomy is imposed on adopters |
| #61 — the command root | the toolkit detects no manifest, infers no package manager and owns no build |
| #66 — the local check | no tool, task name or flag of any stack enters the toolkit |

The copies disagreed. #61 bars *detecting* a manifest, #66 bars a tool name entering the toolkit
*at all*, #60 bars a *taxonomy* imposed on adopters, and #13 bars *build steps* while keeping a
script path — so none of them answered whether a manifest name may appear in a role's text, or
whether a command flag may be buried in a `mirrors` string. Both are answered at
[`schema.md § What the procedure models`](../plugins/mjolnir/config/schema.md#what-the-procedure-models-and-what-it-only-names-and-calls),
the second by ruling that the procedure matches nothing inside a command string, so the question is
where a fact is readable rather than which tokens are forbidden.

The rule was propagating by restatement-with-attribution. Two of the six cite #13 while rewording
it; three carry a body edited after the item collecting them was open; and a seventh home is
[#19](https://github.com/ragnor-rs/mjolnir/issues/19)'s sweep, stating the boundary in its own words
and crediting the collection. The edit record keeps timestamps and not diffs, so it cannot settle
whether a given sentence predates the collection; all six were filed inside one four-hour window,
two in the three minutes before the collection and one in the two minutes after. It does settle
that the restating did not stop while an item to collect it was open.

An adopter whose bring-up command, acceptance suite and environment restore are all local commands
finds a key for two of the three and nothing at all for the third, and nothing saying whether that
third is a missing facet or the boundary working as designed. An absence nobody can classify
invites an item per local command, which grows the surface in the one direction the boundary
exists to prevent — so the statement is a test a reader runs, with the cases worked in the open:
[`schema.md § What the procedure models`](../plugins/mjolnir/config/schema.md#what-the-procedure-models-and-what-it-only-names-and-calls).

## Four checks behind one workflow name, and the tolerance that hid it

The host facet was written workflow by workflow, which is how every project here that controls its
own workflows writes them. One project in the migration set does not: a single workflow runs four
jobs mirroring four unrelated local commands — two languages' linters and test runs, a document
gate, and a parse-and-lint of its shell scripts — and the four share a checkout and a build, so
splitting them into four workflows pays for four of each. The cost to every consumer is the same
loss three times: a guard can only refuse or allow on *the workflow ran*, a precondition reading *a
run exists for this commit* reads green for a command whose job was filtered out of it, and a
coverage verdict computed per workflow reports a change covered on the strength of jobs that never
ran for it.

This repository tested the opposite arm. A second gate arrived with #19; stating one of its two
commands in `host.checks` with the other parked in a comment was rejected in review, and the sweep
became a workflow of its own, its two commands never joined with `&&` — a conjunction improvised
inside one string being the shape the facet already refuses for its triggers. Avoiding the shape
cost one workflow file and one extra checkout, cheap enough that a second job sharing a workflow
name should need a reason. Having never had to nest, this repository cannot say whether nesting is
right.

While the gap was open, the reader accepted a `mirrors` holding a *list* of commands — deliberately,
so that the refusal of a done check the host already runs would compare against whatever an entry
mirrored rather than hold nothing, and recorded in the reader as promising nothing about the shape
that would land. A configuration no section of the surface stated therefore loaded clean, its
meaning stated only in a docstring. A tolerance is a shape that works until somebody states the
other one, and the two then disagree about where a command's job and its filter live. Both are
closed at
[`schema.md § 2 → A workflow whose jobs mirror more than one command`](../plugins/mjolnir/config/schema.md#a-workflow-whose-jobs-mirror-more-than-one-command),
which states the nested form, refuses the list, and rules what the collision argument behind the
workflow key does and does not reach.

No workflow of this repository filters on paths — every entry of its own facet omits the key — so
the rule that a filter sits at the level the workflow file states it at is exercised by the
reader's own planted violations and by the example that illustrates the form, and by no
configuration this project runs on.

### A task runner's suite, one of its tasks, and a run against the project's own database

Three calls that duplicate a host run went unrecognised by the guard on one adopter, each
reproduced against the shipped matcher. A mirror joined with `&&` never matched itself, the call
being cut at its separators and the mirror not. A call running one task of a mirrored task runner
did not match the runner's whole suite, the test being a prefix. And a run against that project's
own billing or test database matched a mirror it does not duplicate, nothing on the surface saying
so.

The three answers sit where each fact belongs:

- **The compound is a matching rule and nothing a project states**, so it is the guard's, at
  [`schema.md § 18 → What may be guarded`](../plugins/mjolnir/config/schema.md#what-may-be-guarded-and-the-two-ways-a-refusal-stands-down).
  This repository's own facet still never joins commands with `&&`; the rule reaches a project that
  already does.
- **Which tasks a suite covers is the project's fact**, and no derivation from a runner's name can
  supply it. So it is a list beside the `mirrors` it parts, at
  [`schema.md § 2 → A command that runs other commands`](../plugins/mjolnir/config/schema.md#a-command-that-runs-other-commands-and-the-parts-its-run-answers-for).
  Its other consumer, `host_checks.py`, reads a part as the command, so a role is not told to run a
  part locally that the guard then refuses.
- **The database is the call's own fact.** A configuration names the variable and never its value,
  so `unguarded_when_set` sits with the guard's other keys rather than on the facet: the facet
  states what the host runs, and the variable states what this one call is.

The exemption reads only what the call itself sets. A variable exported in an earlier call is held
by the shell, and nothing in the call shows it; a guard reading the environment would exempt every
later call that never mentions the database. For the same reason an assignment counts only on the
mirrored command itself: one standing before another command in the same call reaches that command
and never the mirrored one.

## One entry's two events, and the types the pattern could not carry

`triggers` had two forms — an event and a base, or an event and a branch, one of them or a list —
and one entry of this repository's own is the first whose event types decide anything. The
`Nothing deferred` workflow listens for `pull_request` with
`types: [opened, edited, synchronize, reopened, ready_for_review]`, and neither form could spell
that: the entry read `pull_request -> *`, the same text an entry for a workflow naming no types at
all would carry.

`edited` is the type that matters. That gate reads the pull request body, and a body corrected in
place pushes no commit — so without the type the check stays red until an unrelated push lands. The
residue sat in a comment in the workflow file, which is what
[`schema.md § 2`](../plugins/mjolnir/config/schema.md#2-code-host) says `checks` exists to prevent:
every consumer reads it and none carries the facts itself.

That workflow needs a second event kind as well — findings arrive when a review is submitted, with
no commit pushed, so it listens for `pull_request_review` too — and `triggers` could state that no
better than a type. Two gaps of one shape in one entry made the key worth extending rather than
annotating.

The rules are at
[`schema.md § 2 → What a trigger states`](../plugins/mjolnir/config/schema.md#what-a-trigger-states-the-event-the-types-of-it-and-the-ref);
the arguments that settled each question:

| Question | Settled | The argument |
|---|---|---|
| Where types live | **Inside the pattern** — `pull_request(edited) -> *` | A workflow with two events gives each its own list, so a key beside `triggers` is a second list aligned by position. And § 17's `counts_when` is stated in this same form on an entry that has no such sibling, so the alternative gives one mapping two vocabularies |
| What an omitted clause means | **The workflow's event block states no `types:` key** | Read as *the host's default set* it is uncheckable: the defaults differ per event, this surface carries none of them, and the table that would supply them is a second statement of the host's vocabulary. Read as *the file states no filter* the comparison is one the workflow file answers by itself |
| Whether the facet should hold types at all | **Yes, extended** | Neither guard needs one: #33's asks whether the host already runs a command, and the finishing role asks whether a run exists for *this commit*, which a run fired by `edited` is. What needs one is the consumer that writes a **verifier** rather than data — the drift check at [`§ 2 → The facet against the host's own definitions`](../plugins/mjolnir/config/schema.md#the-facet-against-the-hosts-own-definitions), which compares the clause against the workflow's own `types:` key in both directions. A facet that could not express the types would leave it reporting drift on a correct entry, green on one it had proved incomplete, or the dimension undeterminable, and each of the three is worse than the key being richer |

The extension stops at the event vocabulary. The third event that workflow wanted is one no
workflow file may name at all —
[measured there](single-source-of-truth.md#what-this-gate-deliberately-does-not-check). A pattern
naming an event is therefore not a claim that a workflow may listen for it: the facet enumerates no
events, and what refuses such a name is the host as the file loads.

This repository's evidence for the type clause and the second event kind is that one entry. Every
other workflow here states no `types:` key and its entry carries no clause, the reading the
omission rule gives it; the rest is exercised by the reader's planted violations and the example
that illustrates the form.

## The filter a workflow states in the inverse, and the sense the key could not carry

Two of a migration project's workflows filter on the paths they *ignore* and on nothing else — run
on everything except a list — where `paths` stated only the including form. Neither entry could
carry its filter, and every consumer read both as running on every change. The rule is
[`schema.md § 2 → The two senses a path filter states`](../plugins/mjolnir/config/schema.md#the-two-senses-a-path-filter-states-and-why-they-are-one-key);
what is here is the measurement.

The error was in the safe direction. An entry with no filter reads as covering every change, so the
coverage reading never reported a run as covering a change the host skipped — it waited for a run
that would not come. The one reading that lost a verdict is the guard that refuses a local check
the host has already run: it could decline a local run the host skipped, and the project could
still run the command with its escape.

The drift check could not see any of it. It compared `paths` in both directions against the
workflow's own `paths:` key; a file stating the inverse key has no `paths:` for either side, so an
entry with no filter and a file with an inverse one agreed — a dimension reported as agreeing where
nothing had been compared, which
[ruling 18](divergences-and-rulings.md#4-the-rulings) forbids. The key sat in that check's list of
keys no entry has a form for, the one entry of that list a project could act on: the others name
refs the facet cannot enumerate.

The settled questions — that it is one key and not two, that the host's spellings stay off this
surface, and that the two senses are not mirror images — are argued in that subsection. Two
findings the surface does not carry:

- **No translation at the point the filter is written is possible.** The complement of a glob list
  is not a glob list, so converting the filter where it is stated and keeping one form on the
  surface had nothing to convert it into; the facet carries the sense.
- **The asymmetry was reproduced.** The deciding case is a change touching one excluded path and
  one outside the list: read as the watching sense's mirror image it is *out of scope*, and the
  host runs that workflow.

The reader normalises the sense once, so neither consumer reads the value's shape: a filter arrives
as its sense and its globs, and a walk that dropped the sense would hand both a filter pointing the
other way — which is why the record and not the load is what this project's suites assert. The
coverage reading answers *out of scope* for a change whose every path an excluding filter names.
The drift check compares the sense before the globs, because two filters listing the same globs in
opposite senses agree on every character and cover complementary sets of changes.

Two shapes stay unestablished rather than compared, both on
[`schema.md § 2 → The facet against the host's own definitions`](../plugins/mjolnir/config/schema.md#the-facet-against-the-hosts-own-definitions)'s
own list of what leaves a dimension unestablished. An event block stating both of the host's path
keys: the host rejects such a file itself, so the entry beside it may correctly state a run that
never starts, which key the project meant is not a comparison's to pick, and reading the half the
facet can spell would report drift on the strength of what was not read. And a path key carrying no
glob: read as a filter naming nothing, it is drift no edit clears, because the entry that would
agree with such a file states an empty list and the reader refuses that at the key in either sense.

No workflow here filters on paths at all, so the sense is exercised by the reader's planted
violations, by the drift check's planted definitions in each direction, and by the example that
illustrates the form, and by no configuration this project runs on.

The two entries that found the gap still do not state their filter; they are in a repository this
one cannot open and no check here can reach. The form was held against those two files: their
excluding globs were read off the workflows, the two entries filled in and that project's comment
about the gap removed, in a temporary skills root served by this surface — the configuration loads,
the whole facet agrees with its own definitions, and one glob dropped from one entry reddens and
names the sense. Nothing in that repository was written, and until it is, those two entries
describe their runs as covering every change.
## A section one role writes and another runs

The facet is [`schema § 20`](../plugins/mjolnir/config/schema.md#20-the-sections-a-pull-request-body-must-carry);
what is here is the measurement behind it and the questions it settles.

**What was found.** One project in the migration set carries a workflow of its own, separate from
its lint suite, whose single job asserts that a pull request body states what the change needs
done to an environment before it can be deployed. The role that deploys a batch collects exactly
that section out of every change the batch carries and performs what it collected, so the body is
an interface between two roles — and the heading it turns on was stated in a workflow file and
nowhere else. Environment preparation was a body element the configuration did not state, and a
gate enforcing a fact no configuration states is the shape this surface exists to delete.

**How it differs from the title gate.** Two properties separate them, and both change what can be
built:

| | The title gate | This one |
|---|---|---|
| What the rule reads | a pattern over the event payload, which a workflow can state inline | a body, which needs a parser |
| What `host.checks` records | an entry mirroring nothing, which the duplicate-run guard reads as never-guard | an entry whose `mirrors` names a command a person can run, which that guard reads as guardable |
| What has to be installed | one file | a checker as well, because a host run executes files and the toolkit is not one of them |

**The questions, and the arguments that settled each.** The last three were settled by reading the
facet's one reader, which showed that the step it was extracted from could not be expressed in the
direction that mattered.

| Question | Settled | The argument |
|---|---|---|
| What makes a heading a facet rather than a convention | **Another role reads it**, stated on the entry as `read_by` | Any heading can be made mandatory, and a gate over a heading nobody collects is a contributing guide enforced by continuous integration. Writing the reader down on the entry is what keeps the test applied rather than remembered, and it is also what a refusal names — a body handed back with nothing saying who was waiting on the section leaves the author guessing |
| Whether a section can be required with no way to answer *nothing* | **No; `nothing_needed` is on every entry** | A required section whose only passing form is content turns every change needing nothing into a change that has to invent some, and what the body then carries is a sentence written to satisfy a gate. The answer also has to be the *whole* of the section: a body stating it and then listing work has said both things, and the collecting role would have to choose |
| Whether the open-items section belongs in the facet | **No** | It is required of every body with no key that turns it off, and an entry here is one a project may stop stating. Carried here, the rule would become configurable — which the rule's own precedence refuses. Its heading stays with the gate that reads it, and what the two gates share is the grammar for finding a section in a body rather than the heading |
| What carries a step a change owes a deploy — the work item, the release grouping, or this facet | **This facet, and no second carrier is added** | The question was put to the item and the grouping before this facet existed. A step is discovered while the change is written, so the item's body would state it as a prediction made before the work; a facet of the item is written through `set_field`, which the port reports unavailable on a measured tracker; and a grouping is a *set*, so a step carried there cannot say which change owes it. The change is also the only one of the three a gate already holds |
| Where a collected step falls against the collecting role's own act | **`when`, required of every entry** | The measured step is a pair of schema changes that must reach a live database *before* the image carrying the code that reads them — and the facet's own text called it preparation needed *before the change can ship* while the one role collecting it ran it **after** the invocation. With no key, a step's timing is whatever the collector finds convenient, and the convenient place is after the act. The same argument `not_live` is required by one facet over: a project that never looked and a project that decided read identically otherwise |
| Whether who answers a step is a second axis or derivable from `when` | **A key, and the correlation is stated rather than used** | The two measured steps are one `before`/`human` and one `after`/`procedure` — a correlation across two observations, and a value derived from it would be derived from two points that happen to agree. What makes the key load-bearing is the first of the two: the procedure holds no credential for the database that step is about, so with no way to say *this one is a person's*, the measured instance is expressible only as a step the collector would try to run itself |

The headings are in the repository's language, not the tracker's: the example that states two
writes its items in one language and its repository in another, and the body is a repository
artifact. A heading transliterated out of the tracker's language matches nothing a body carries.

This repository requires no section: nothing here is deployed and no role collects a section out of
a change, so `body_sections` is `[]` and the gate is installed nowhere in this tree. The rule is
exercised by the checker's planted bodies, and the install by a fixture built from the example that
states a section, with the generated workflow and its registered entry handed to the drift check
that holds every other entry here.

The reader's own suite holds every shipped example to stating `when` and `answered_by`, and
holds the examples between them to stating each value of `when`, so a row of the surface's table
that no example reaches reddens. The collecting reading, the opposite question over the same
grammar, is asserted against planted bodies beside the gate's; its key arm is the *nothing* answer
written as an emphasised bullet with no period, which the grammar reads as the answer and a role
reading by eye would call owed. The role itself is unexercised here, this project deploying
nothing: the collector's refusal for a project stating no section was run in this tree, and the
reading arm in a temporary skills root carrying a shipped example.

## The surface a tree is held to, and the guards that went quiet in a configured project

Within a day of the body-sections key landing on the integration branch, a session working a
different item in its own tree could run no guarded command: every call came back with three of
the four guards reporting that the project's configuration could not be read and holding the
command to nothing, and any role that read the configuration exited naming
`body_sections` as a required key. The project had written the key — on the integration branch.

**Two copies of this surface can answer the question.** Measured 2026-10-24:

| | Where it came from | Which commit |
|---|---|---|
| The reader and this surface | the installed plugin's path, which a user-scope install points at the primary checkout | the integration branch |
| The configuration it resolved | the skills root, which § 1 rules is the directory the role ran in | the tree's own branch |

So the newer surface was holding an older configuration to a key the older branch had never heard
of. Through the reader the skew is one-directional: a key a branch *adds* loads against the
installed surface — tested, with an invented top-level key accepted by the reader and reddened only
by the single-source gate on the host — while a key the installed surface newly *requires* refuses
every tree cut before the marker.

**Why the tree's surface wins.** Three rules would each have cleared the measured failure, and they
are not equivalent. The third is the rule —
[`schema.md § 1 → The surface is resolved beside the configuration`](../plugins/mjolnir/config/schema.md#the-surface-is-resolved-beside-the-configuration).

| Candidate | What it does to the measurement | Why not |
|---|---|---|
| Fall back to the primary checkout's configuration where the skills root has none | nothing — the configuration is tracked, so every tree has a copy and the fallback never fires | It also answers a question already ruled: a carrier searching outward acts on another project's facts in a directory that states none |
| Resolve the configuration from the primary checkout always | clears it, the integration branch carrying the key | A branch changing this surface could then never be tested in its own tree, which is how every item that changed it was built. The configuration under work is the tree's |
| Resolve the **surface** from the skills root where it ships one | clears it, and keeps the configuration where § 1 puts it | — |

The configuration is the statement a branch is making, so it stays in the tree; the surface is
what that statement is held to, so the half under work has to be in the tree as well. Resolving
both from the primary checkout and resolving neither are the two symmetric answers, and each
reproduces one direction of the failure.

### The direction the bound above does not state: a new surface read by an old reader

With the surface resolved from the tree, a key a branch adds is held by the **tree's** surface and
read by the **installed** reader — a third combination, and it reproduces the same failure.

Measured in the change that added § 23. The new key's value is a list, and its membership was
written as an alternation beside the key. An alternation marks what a *value* may be; the value of
that key is the whole list — so the installed reader compared the list against the members and
refused the configuration. Four guards then reported the configuration as unreadable and held the
command to nothing — the spend one, the live one, the context one on both of its events, and the
enforcement one — on every call, for as long as the branch stood. The outward guard answers only on
a write leaving the project, so a session making none hears nothing from it: the same silence from
a different cause.

The fix is the surface writing a list's membership as the list, the shape
[`schema.md § 9`](../plugins/mjolnir/config/schema.md#9-day-log)'s streams and exclusions already
had and which [`schema.md § 23`](../plugins/mjolnir/config/schema.md#23-session-bookkeeping--which-thirds-a-project-runs)
states as a rule: a membership written that way is **unread** by a reader older than the key
instead of misread by it, and unread is the direction that fails safe. The reader derives the two
facts apart, and a refusal names which of them is missing.

This does not fix the class. Any rule a new surface states and an older reader performs differently
reproduces it, and nothing compares the two copies: the installed reader's version is not a fact
this repository's gates can see. The remedy that generalises is a habit — a new surface statement
that an older reader will *not* read beats one it will read wrongly.

An adopter carries no second copy of the surface. A project that consumes the plugin has nothing
for the resolution to find, so the installed copy is read — at whatever commit the checkout serving
it stands on, the one state the rule at
[`schema.md § 1 → The surface is resolved beside the configuration`](../plugins/mjolnir/config/schema.md#the-surface-is-resolved-beside-the-configuration)
cannot reach; the last subsection of this section measures that case. For the shipping project's
own primary checkout the two answers coincide, that root and the installed path being one
directory, so the suite's assertion about this repository holds the resolution's *report*.

**Ten shape rules answering a question that was not theirs.** With the surface resolved from the
tree, the measured configuration still would not load: the reader's own type rule for the key
refused its absence, independently of any marker. The division is:

| Question | Whose | Where |
|---|---|---|
| Is the key written at all | the surface's `# required` marker | checked in `validate` before any shape rule runs |
| What a stated value has to be | the shape rule | the reader, per section |

A rule that refuses absence states the marker's fact a second time, and the second statement
outlives the first in one place: a tree whose surface does not mark the key. Ten rules did it —
every list-valued and block-valued required key on this surface. The assertion that found them is
over the marked set, so a key that grows a shape rule is covered the day the surface marks it.

A guard that cannot read a configuration fails closed and says so. But *held to nothing* and *this
project configured nothing* read the same, and three of the four guards produced the first while
the project had written every one of their keys; nothing reported the version skew as a skew. The
rule removes the state **for a tree**, and naming the resolved surface among what a role reports
makes the remaining case visible when it happens —
[`schema.md § 1 → The surface is resolved beside the configuration`](../plugins/mjolnir/config/schema.md#the-surface-is-resolved-beside-the-configuration).
For an adopter the state stands (the subsection below), and the answer a guard sends is where it is
made visible.

### The same failure in an adopter, which no resolution rule reaches

An adopting project carries no surface of its own, so the reader finds nothing in its skills root
and reads the installed copy — at whatever commit the primary checkout serving it stands on.
Measured 2026-10-30, a day after the role-to-person facet landed:

| | |
|---|---|
| The change | `e1430aa`, 2026-10-29 20:18:05 +0400, marking `people.carrier` as `# required` |
| What it updated | every configuration this repository tracks, which is every one its gates can reach |
| What it invalidated | five live configurations, in repositories outside this one, four last written 2026-10-28 |
| What each one needed | one key: `people.carrier: none`, with the `absent_reason` that marker demands |
| How it was noticed | three parallel sessions, each reporting the same stop out of its own project |
| How the rest were found | sweeping every configuration on the machine; nobody was standing in them |
| What the window cost | the enforcement gate, `context_guard.reread`, the approval arm, and every role that routes through the reader — the deny lists were empty in all five, so those arms held nothing either way |

No install step ran and no session was restarted: the surface those files are held to moved under
them. There is no second copy to prefer, so a project that consumes the surface is always held to
the commit the install serves
([`schema.md § 1 → The surface is resolved beside the configuration`](../plugins/mjolnir/config/schema.md#the-surface-is-resolved-beside-the-configuration)).
One of the five was edited hours after the break, and the session editing it was never told that
the file no longer resolved.

The answer named no key for the whole window, while the reader it had called knew which one. A
guard's answer therefore carries the reader's own stop
([`schema.md § 19`](../plugins/mjolnir/config/schema.md#19-a-command-that-spends-and-the-supervision-it-is-refused-without)),
the only half a check here can hold: the configurations are files no check in this repository can
open.

The stop is the reader's first refusal, not a diagnosis. A configuration with more than one fault
answers with whichever `validate` reached first — a stub stating `roots` as a list answers about a
required key nobody wrote — so the answer carries it as the reader's stop, not as the repair. It is
also cut, because the reader's refusals interpolate the project's own stated value: one long
mistyped scalar answered with 50,063 characters of itself.

### How loud that window was, and the two defects measuring it found

Taken 2026-11-05 against a configured project three required keys short of resolving:

| | |
|---|---|
| guards that answered on one `Bash` call | four — the spend one, the live one, the context one, the enforcement one |
| arms that answered again on the same call's completion | one — the context guard's result arm |
| deduplication of any kind | none, in any of them |
| distinct facts those five messages carried | one |
| messages in a session of 73 guarded calls | ≈ 290, and a floor rather than a total: the session was still open when it was counted |

The cost is linear in the guarded calls a session makes, so it charged most the session doing the
most work — against a state the surface creates every time a key is newly marked `# required`, and
calls one line to answer rather than a migration
([`schema § 29`](../plugins/mjolnir/config/schema.md#29-the-hosts-run-operations)). Until that line
was written, every project the install reaches heard four messages per shell command.

The defect was the cadence, not the direction. Failing open is right, and so is carrying the
reader's stop; neither licenses saying it again on the next call. The second defect was four
sentences for one fact: they differed in a prefix and a section citation, the enforcement guard's
carried none, and four messages leave the reader to work out that they add up to every guard
installed. The cadence and the consolidation are therefore one rule — a per-guard claim would have
kept the four sentences and only thinned them
([`schema § 19 → How often a configuration that does not resolve is reported`](../plugins/mjolnir/config/schema.md#how-often-a-configuration-that-does-not-resolve-is-reported)).

The rule does not change the state: a project whose configuration the installed surface has just
invalidated still has every call held to nothing until somebody writes the key, and is now told
once instead of four times per command.

## The bookkeeping role: three copies that are a third of it, and two keys that came out of it

This role divided in two directions at once, and this is the one place the copies are counted.
**Four projects carry it whole; three further copies are its commit third alone**, under two other
names and two different carriers — one a skill, one a command — which is the *one name, a subset
role* case [above](#name-and-role-diverge-in-both-directions) and the reason the inventory key is
*(role, carrier)* read out of the body rather than the directory name.

That forced a key naming which thirds a project runs, at
[`schema.md § 23`](../plugins/mjolnir/config/schema.md#23-session-bookkeeping--which-thirds-a-project-runs),
and the measured commit-third-only project **has a tracker**, so the question is not derivable from
the tracker axis, the carrier axis, or anything else on the surface: a project with a board and a
backlog can have a bookkeeping carrier that commits and does nothing else, and that is a
configuration, not an adoption that stopped halfway.

The order the thirds run in is procedure, not part of the key: the rule is at
[`schema.md § 23`](../plugins/mjolnir/config/schema.md#23-session-bookkeeping--which-thirds-a-project-runs),
and every copy already ran in that sequence, so there was no divergence to rule on.

### Staging is per role, measured inside one project

`staging` is not a project-level value: one project holds both positions **in two of its own
carriers**:

| the carrier | what it states | why it is right there |
|---|---|---|
| its bookkeeping copy | stage everything, no exceptions, and do not edit, format, reorder or fix any file | the person asked for the tree as it stands, and an unstaged file is simply missing next session |
| its finishing role, same repository | never stage everything; name the paths you intend, and watch for credentials and build output | that commit rides an item's branch into a pull request, where a swept-in artifact lands with it |

Neither is a mistake, so a single value cannot express that project without making one of its two
roles wrong. The key is
[`schema.md § 6 → What staging is per`](../plugins/mjolnir/config/schema.md#what-staging-is-per-and-the-two-rules-that-hold-regardless),
with one entry per role that commits.

The split does not touch the pair of rules that hold regardless; the strict copy of the `all`
position names a credential file outright. So `all` is *no path filtering*, never *no scanning*.

### A save is owed at a compaction boundary, and nothing delivers one

A window is summarised without being asked, long before a session ends, and what the summary dropped
is unrecoverable from inside the session — the measurements are
[above](#the-window-is-a-resource-the-loop-spends). That makes a compaction a save point like any
other:
[`schema.md § 23 → When a save is owed`](../plugins/mjolnir/config/schema.md#when-a-save-is-owed-and-the-boundary-it-names).

The event that fires before a window is compacted is one of two that **never fired** in the
measurement that built
[`schema.md § 7`'s table](../plugins/mjolnir/config/schema.md#what-a-hook-can-establish-about-the-role-it-is-running-under),
so what it carries is unestablished. The role therefore takes the boundary when it notices one, the
artifact names which boundary it was, and the cost — a compaction nobody saved before costs the
window — is stated on the surface.

What the carrier can decide here stops at the artifact's fields; that reach is recorded with every
other check's —
[`docs/single-source-of-truth.md`](single-source-of-truth.md#the-bookkeeping-roles-derivations-and-the-round-trip-that-is-the-resumability-arm).

## The memory store is derived from the working directory

The memory third of the bookkeeping role had no store on the surface. Where it writes was found by
reading the memory step of every copy that carries one and where this project's own store lives,
and the answer is why the facet is not a path key:
[`schema.md § 25`](../plugins/mjolnir/config/schema.md#25-the-memory-store-and-the-tree-a-save-may-refresh-it-from).

### What the copies' memory steps say, read rather than assumed

Every copy that carries the role whole carries a memory step; the four agree on all but one
thing, which decided the facet's shape:

| what was read | how many copies | what it decided |
|---|---|---|
| the store is the agent harness's own per-project directory, named after the **absolute path of the checkout** | all four, each writing that path out in full | `derived` is the measured case rather than a hypothetical one, and a path key alone would not describe any of them |
| the shape is one file per fact plus an index file loaded at session start | all four | `index` names a real file rather than an invented one, and the index's own line format is each project's |
| the index line is written `- [Title](file.md) — hook` | all four, identically | the carrier takes the line as given: the format is the project's and is not the toolkit's to state |
| delete a memory the day it is proved wrong, because a stale one is asserted with the same confidence as a true one | two of the four, one adding that the project *has been bitten by exactly that* | the read-time half of the rule was already somebody's practice, and § 24 had already taken it |
| prefer recording the measurement over the conclusion — a memory saying *X is slow* rots in a way one carrying the figure and the date does not | one | **the write-time half, invented independently**: this is `provenance` and `premise` in prose, and it is the strongest evidence the entry form has |
| the tree hazard, at all | **one of the four** | the hazard is real and is not generally known: three copies of the same step, on the same harness, say nothing about it |

**The one copy that states it states it twice, the second time as a repair.** It carries a standing
instruction to run the role from the main checkout, and a
script that **symlinks each worktree's derived directory to the checkout's**, with the diagnosis
written out in the script's own header: the harness derives its per-project directory from the
working directory, so a worktree session gets one with no store in it — no index is loaded, and
anything saved lands where the main checkout never reads it.

That repair is what `carrier: path` is for, not what `derived` plus `any_tree` is — the first
question the refusal at
[`schema.md § 25 → write_from`](../plugins/mjolnir/config/schema.md#write_from-and-the-pair-of-outcomes-a-refusal-is-one-half-of)
raises. A project that has linked its trees' directories has *made the store pinnable*: it names
that one path, every tree writes it, and the link is how the harness's own loader comes to agree
with the pin. The refused pair is the other case — a project that has done nothing, where *wherever
the session is standing* really is a different store.

**The measurement in this repository**, the copy that has done nothing and the one the `derived` arm
is written from. The agent harness keeps a per-project directory and derives its name from the
**absolute path of the working directory**. When read, the harness held five such directories for
this one repository — the primary checkout's and one for each of four worktrees cut from it — and
the store existed under the checkout's alone. The other four carried transcripts and no store. So a
session standing in a tree had: no index to load, and nowhere a save would write that the checkout
would ever read. Nothing announced either half; the save reports success.

| what was measured | what follows |
|---|---|
| five per-project directories for one repository, one per working directory | the store is a function of where the session stands, not of which project it is |
| a store under the checkout's directory and under none of the four trees' | a session in a tree loads no index and writes where nothing reads |
| nothing in either half says so | the hazard is silent, which is what makes it a rule rather than a caution |

**A moved or renamed checkout is the same failure without a tree**, so the facet is not scoped to
the worktree branch model: the derived name changes with the path, and the old store is
orphaned.
[`schema.md § 24`](../plugins/mjolnir/config/schema.md#what-a-load-may-not-assume-survived)
already lists a moved checkout among what a load must not assume survived, and this is what it
breaks. A store outside the tree is also outside `.gitignore`, so the argument that two copies are
safe where both are ignored does not reach it — these facts are neither committed nor ignored, and a
reader assumes a project's memory is in the project.
[`schema.md § 25 → Why a project cannot simply be told to write a path`](../plugins/mjolnir/config/schema.md#why-a-project-cannot-simply-be-told-to-write-a-path)
is where all three of those land.

### Why two carriers rather than one path key

A path every project writes does not survive this project. The store this repository refreshes is
the harness's own derived directory; a path written in the configuration would create a **second**
store, one the procedure writes and the harness ignores — two records of one thing allowed to
disagree. The value for a project in that position states that the harness decides and the
procedure must not guess.

The two carriers differ in kind, not degree, and the table at
[`schema.md § 25 → The carriers`](../plugins/mjolnir/config/schema.md#the-carriers-and-what-each-of-them-closes)
is the comparison: a pinned store closes the hazard by construction and owes the project one thing
to keep true, while a derived store closes nothing by construction and has every open half it leaves
reported instead. Neither is the better configuration in general; which one a project gets is a
property of where its store already is.

**Why the absent case is a carrier and not a null path.** The block is not optional — not even
written where `session.parts` names the third and refused where it does not — for a reason found by
this repository's own gate: every configuration here is held to carrying every top-level key the
surface declares, so an optional block is one three of the five shipped examples could not write.
The absent case is `carrier: none` with a reason, as every other facet's is, and it is not a second
statement of the thirds list because the reader refuses every disagreement between the two —
[`schema.md § 25 → The carrier and the third have to agree`](../plugins/mjolnir/config/schema.md#the-carrier-and-the-third-have-to-agree-in-both-directions).

No key under this block carries a default. A marked default is applied by creating whatever
blocks it needs to land in, so `# default: main_tree` on `write_from` wrote a `memory` block into
every project — including the shipped collection example, which then stopped loading, naming a
store it does not configure.

### What a refusal buys over a convention

One project's prose holds the rule: run the bookkeeping role from the main checkout and reach into
the tree with an explicit path. It is correct and unenforceable. `write_from` is that rule made a
value, and it buys the **pair of outcomes** at
[`schema.md § 25 → write_from`](../plugins/mjolnir/config/schema.md#write_from-and-the-pair-of-outcomes-a-refusal-is-one-half-of):
either the one store was written, or the third refused and the reply names it. A third that quietly
wrote nothing reads exactly like one that wrote.

**Which working directory a session is standing in is read from git and never from the
configuration.** § 1 resolves a work tree against that tree's own files, so a session in a tree
resolves the *tree* as its skills root. Comparing a working
directory against the resolved root answers *yes, this is the checkout* in exactly the case the
facet is written about. What answers it instead is `--git-dir` against `--git-common-dir`, which
differ in a linked worktree and agree in the checkout — and where git answers neither, the decision
is reported unanswered rather than as the checkout, the permissive reading being the one that writes
a tree's own store.

### The index contends and the per-fact files do not

The store's shape where one exists is one file per fact plus an index file loaded at session start.
The per-fact files are safe under parallel trees — two sessions rarely write the same fact — and the
index is not, being the file every session reads and rewrites.
[`schema.md § 25 → The index`](../plugins/mjolnir/config/schema.md#the-index-is-the-one-file-two-sessions-contend-on)
makes the write an append under a lock rather than a read, an edit and a write back.

The outcome assertion — many sessions writing at once, every entry still present — **passes with no
lock at all**: twelve processes each appending one short line kept all twelve lines with the `flock`
call removed. A second arm holds the mechanism directly: with one process holding the lock, a second
writer must wait, the single assertion that reddens when the lock goes. The two arms and what each
reaches are in
[`docs/single-source-of-truth.md`](single-source-of-truth.md#the-memory-store-the-write-decision-and-the-two-arms-on-the-index).

### Write-time admission, and the half a reader cannot recover

A store's failure mode is not only where it is but what gets into it. The published work on agent
memory names a poisoned store as a defect class whose sound defences are **admission at write
time** — what may be committed, with what provenance — and a **re-check at read time**, and names
prompt-level filtering of a store that is already wrong as repeatedly insufficient. A store whose
only policy is *the save writes it* has neither.

One surveyed copy reached the write-time half on its own: prefer recording the measurement over
the conclusion, because a memory saying *X is slow* rots in a way one carrying the figure and the
date does not — the convergence the extraction argument rests on
[above](#the-strongest-argument-for-extraction-is-not-borrowed), and the reason the form asks for
the source and not only for a label.

So the entry form carries the fact, its provenance, what it was established from, and the premise it
rests on, and the admission runs before anything is written:
[`schema.md § 25 → What may enter the store`](../plugins/mjolnir/config/schema.md#what-may-enter-the-store-and-what-a-reader-does-with-what-is-in-it).
Two of those four earn their place from a direction this surface already names: a recalled fact
reflects what was true when it was written
([`schema.md § 24`](../plugins/mjolnir/config/schema.md#24-session-restore--the-readings-a-pass-is-resumed-from)),
so an entry that does not say what would falsify it obliges its reader to invent the check — and a
repeated fact rendered identically to a measured one becomes a measured one by being read twice.

The rule reaches the entry's shape, not its truth: that a fact carries its provenance and its
premise is decidable, and whether the premise still holds is read against the tree by
whoever reads the fact. `asof` was left out of the form for that reason — a date says when a fact
was written, not whether it is still true, so it would answer staleness with a number that reads
like an answer.

### What the admission costs a store it cannot reach

Measured in this repository, the only project here that runs the memory third. The admission is
held by the one command that places a fact in the store, and under a derived carrier that command
composes no path and writes nothing: handed a complete entry it answers that there is no directory
for it to write a fact into and no index for it to lock. So every entry in that store is in the
harness's own shape — a leading YAML
document carrying a name, a one-line description and a subject label, then the fact as prose — and
not one of them has been through the rule.

It is a **third** cost by the way it fails: the index's contention loses work and a moved checkout
orphans it, both of which a reader eventually notices, while an unprovenanced fact reads exactly
like a provenanced one forever. The table at
[`schema.md § 25 → The carriers`](../plugins/mjolnir/config/schema.md#the-carriers-and-what-each-of-them-closes)
states the three.

The read-time check meets the same wall from the other side. A reading written for the entry
form alone refuses a store-shaped entry as a file that is not one YAML document — true, and it tells
its reader nothing about what they are holding. The rules that replaced it are at
[`schema.md § 25 → What a reader does with a store whose admission never ran`](../plugins/mjolnir/config/schema.md#what-a-reader-does-with-a-store-whose-admission-never-ran),
and each of them fails in the direction that under-claims.

**The layout the carrier reads.** The store this
repository's harness keeps holds each fact as a file opening with a `---`-fenced YAML document —
`name`, a one-line `description`, and a `metadata` block whose `type` is one of a small set of
subject words — followed by the fact itself as prose. That is the one foreign layout the carrier
reads, and the surface defers to it, a store's own layout being the harness's fact.

⚠️ `metadata.type` is not a provenance: it says which part of the project a fact is about, and a
provenance is an evidence class. Reading the first as the second would make every fact in the store
*measured* by construction, which the provenance field exists to prevent — hence the rule *no key
of a foreign shape*, not a list of keys not to read.

### Reporting a fact stale rather than restating it

The read-time half [`schema.md § 24`](../plugins/mjolnir/config/schema.md#24-session-restore--the-readings-a-pass-is-resumed-from)
already stated — a recalled fact is checked or reported unchecked — had nowhere to put the answer. A
reading that can only ever say *unchecked* renders **nothing checked it** and **checked, and still
true** identically, and a fact whose premise has gone has no way of being reported at all except in
the prose of whoever happened to notice.

[`schema.md § 25 → The standing a recalled fact is reported
under`](../plugins/mjolnir/config/schema.md#the-standing-a-recalled-fact-is-reported-under) is where
that lands. One decision in it is **not** symmetric: *current* over an entry stating no premise is
refused and *stale* over the same entry is not. The two answers do not cost the same. A reader who
has found the fact wrong has found that out whatever the entry says, and treating it as stale
under-claims; a reader who says the premise holds when the entry stated none has asserted the fact,
which over-claims. Refusing both would be refusing the safe answer for the unsafe one's reason.

The mechanism tells the three apart, and the exit status a caller reads keeps a stale fact off the
one a current fact gets. Whether the reader's reading of the premise against the tree is right is
outside it — the same split the admission carries.

## The third surface: one store read whole, and the classes the loop's share misses

The facet above says where a project's memory store is; this section measures what is in one,
together with the project's own instructions file — the two stores a migration leaves standing when
it deletes a project's loop carriers and writes its configuration. The ruling is
[`schema.md § What a project already holds`](../plugins/mjolnir/config/schema.md#what-a-project-already-holds-that-states-the-loop-and-what-adopting-it-does-to-that);
what follows is the measurement it was taken on.

**Measured 2026-11-24, on project E.** As in [`build-surface.md`](build-surface.md), these are
living stores that move independently of this repository, so every figure below is re-taken before
it is re-used (see the last subsection).

### The instructions file, and the four ways it states a loop that has moved

A 1,139-line file, and the loop is in it four times over:

| what it carries | where |
|---|---|
| three loop invocations in their **bare** form, `/<name>` with no namespace | twice: a status blockquote at the head, and the tracker section 77 lines down |
| the carrier directory, **by path** | the same tracker section, naming the three roles again as its own files |
| the gating rule, in its own words — *refuses an issue with any open blocker* | a sentence of its own, which is [`schema.md § 5`](../plugins/mjolnir/config/schema.md#5-readiness-gate--an-ordered-predicate-list)'s `no_open_blockers` restated |
| the status vocabulary and two label conventions, as document bullets rather than as keys | four lines of the same section — which are [`schema.md § 4.2`](../plugins/mjolnir/config/schema.md#42-status--an-ordered-set-of-name-role-writer)'s ordered set and [`§ 4.6`](../plugins/mjolnir/config/schema.md#46-priority)'s carrier and values |

The third row makes this a second authority rather than a stale link. A path that no longer
resolves is discoverable; a gating rule stated in prose beside a configured one is two statements
of a predicate, and the prose copy is the one a session reads first — which is why the file is held
as a governed document
([`schema.md § What each store owes`](../plugins/mjolnir/config/schema.md#what-each-store-owes-and-why-the-two-are-mechanically-different)).
The first row has a second reader: the day log's ritual list matches the bare form for ever while
the document is rewritten to the namespaced one —
[`schema.md § The invocation changes`](../plugins/mjolnir/config/schema.md#the-invocation-changes-and-the-two-surfaces-move-in-opposite-directions).

### The store, read whole: 23 entries, of which 17 are rulings

One file per fact plus the index, with a row in the index for every file and no file the index
misses. Entries are classified against the homes that exist now, since a disposition is only sound
against a surface somebody can open. The three dispositions, and the rule that the subject is the
whole store, are
[`schema.md § Every ruling in those stores is classified`](../plugins/mjolnir/config/schema.md#every-ruling-in-those-stores-is-classified-and-the-subject-is-the-whole-store).

| the entry, by its content | class | disposition |
|---|---|---|
| work is not done until committed, pushed, reviewed, green and merged — with *fixed locally* and *committed to a branch* named as in progress | the loop | **configuration**: [`§ 13`](../plugins/mjolnir/config/schema.md#13-what-counts-as-done--an-ordered-check-list-and-who-answers-each-check)'s ordered `done:` list, whose entries are the states this names as near misses |
| a manual pass on the running application is required before a merge, a green gate not being sufficient | the loop | **configuration**: a `done:` check whose `answered_by` is a person, same section |
| a class of change commits straight to the integration branch and skips the loop | the loop | **configuration**: [`§ 30`](../plugins/mjolnir/config/schema.md#30-the-changes-that-do-not-go-through-the-loop)'s `classes` and its destination |
| a reviewing tool's confidence cut hides real findings clustered under it | the loop | **promoted, already stated** — and more strictly: the reviewing role separates *real* from *firing*, makes a reproduction the score, and carries both into a delegation |
| finishing one item does not authorise starting the next | the loop | **promoted, already stated**: [`§ The loop`](../plugins/mjolnir/config/schema.md#what-carries-the-item-forward-and-where-it-stops-to-ask)'s route ends at the merge and claims nothing past it, and *an approval is per act* is [`§ 19`](../plugins/mjolnir/config/schema.md#what-an-approval-is-per-and-the-one-price-stated-before-a-turn-runs)'s |
| assert values, never key sets | review | **promoted**: [`§ What earns a test`](../plugins/mjolnir/config/schema.md#what-earns-a-test-and-what-makes-its-red-believable) |
| a fixture thinner than the production shape tests the fixture | review | **promoted**: the same subsection |
| a message may claim a specific cause only where the layer below reported that cause | review | **promoted, already stated** for a role's own report — a precondition's failure is never folded into the conclusion ([`§ 2`](../plugins/mjolnir/config/schema.md#reading-a-runs-answer-and-what-a-failure-is)) and a report names what it could not establish ([`§ 11`](../plugins/mjolnir/config/schema.md#a-report-names-what-it-could-not-establish)) — and **deliberately local** for the artifact the project ships |
| an absolute in an acceptance condition becomes the thing measured against later | review | **promoted**: [`§ What an acceptance condition is written as`](../plugins/mjolnir/config/schema.md#what-an-acceptance-condition-is-written-as) |
| text the user typed and the system silently capped must be said to be capped | review | **deliberately local**: the same report rule as above, applied to a product's own output rather than a role's |
| structure a provider already reports is read rather than asked for | review | **deliberately local**: the same shape as *detect what is detectable, and read nothing twice* ([`§ What a project is asked`](../plugins/mjolnir/config/schema.md#what-a-project-is-asked-and-the-one-file-the-answers-are-written-into)), applied to a model's output |
| a schema migration's version is chosen against the order branches merge in | technology | **deliberately local**, and generalising to no other project of the six |
| an applied migration is immutable, a comment change included | technology | **deliberately local**, same |
| re-read the shared tracker's list immediately before filing, because other projects' sessions file into it | the toolkit | **promoted**: the filing role's window, in its duplicate check |
| every item filed here carries at least the second priority value, and the first is never lowered | the toolkit | **configuration**, and already written: [`§ 4.6`](../plugins/mjolnir/config/schema.md#46-priority)'s values and writer, in this repository's own file |
| a missing facet is its own item; a question inside an open one is an edit to that item | the toolkit | **promoted, already stated**: the filing role's **parent** relationship, whose default is a check item on the parent rather than a new item |
| this toolkit names no technology and no project | the toolkit | **promoted, already stated**: [`§ What the procedure models`](../plugins/mjolnir/config/schema.md#what-the-procedure-models-and-what-it-only-names-and-calls), and the sweep that holds it |
| the project's whole build state, as one 1,952-line entry with a *resume here* heading | not a ruling | **configuration**: [`§ 11`](../plugins/mjolnir/config/schema.md#11-session-context)'s artifact, living in the memory store instead of where that facet puts it |
| parked ideas nobody has scheduled, and *do not open an item for one unasked* | not a ruling, plus one | the queue is **deliberately local**; the rule in it is **already stated** — filing is entered by a person, by § The loop's own table |
| a product requirement about which layer owns localisation | not a ruling | **deliberately local** |
| which of two service accounts a local run uses, with a live credential written out in full | not a ruling | **deliberately local** — and ⚠️ the one entry that makes the carrier's *neither committed nor ignored* a security property rather than a tidiness one |
| a retrieval floor that is relative rather than absolute, with one sentence about a test that encoded the bug | not a ruling, plus one | **deliberately local**; the sentence is **promoted** already, as *a test is read off what was asked for* |
| that this project's loop is being replaced by this toolkit, naming the carrier directory it deletes | not a ruling | ⚠️ **the entry whose premise the migration itself removes**, reported under [`§ 25`](../plugins/mjolnir/config/schema.md#the-standing-a-recalled-fact-is-reported-under)'s standing rather than rewritten into a claim |

### The fourth class, which a reading scoped to the loop does not surface at all

Four of the rulings above are about the shared toolkit and are held in a consumer's store: how to
file into this backlog, what priority an item here carries, where a gap goes, and that nothing here
names a technology. Left where they are, they are read by that one project's sessions and by no
other's — the subject is the shared thing and the store is one consumer's.

A second store, measured the same day, confirms the class: another project of the set carries an
entry whose subject is a guard in this repository, naming it by a path on the machine. That store is
otherwise a different shape — hundreds of entries, an index whose rows are rolled up rather than one
line each, and its own language — so the inventory above is one store's and the class is the
finding.

### A disposition is re-taken and never cited

Both inputs move: the store is live, and so is the surface the dispositions name. Three of the
sections the table sends a ruling to are newer than the question it answers, and the figures in the
item that raised that question are not repeated here
([`schema.md § An artifact states what is true now`](../plugins/mjolnir/config/schema.md#an-artifact-states-what-is-true-now)).

A disposition above holds as of the date at the head of this section and is re-derived, not quoted,
by whoever classifies the next store. The form — the three dispositions, and that a homeless ruling
is named — is procedure, is on the surface, and needs no re-deriving.

### What the forbidding kind cannot hold here, and why no entry is written for this repository

[`schema.md § 38`](../plugins/mjolnir/config/schema.md#38-the-documents-a-project-holds-to-a-checkable-property)'s
`forbidden` is what holds the instructions-file half in an adopting project. This repository writes
no such entry for itself. Swept over the 21 governed documents, a pattern for the bare form of every
loop name matches exactly one line — a measurement in a role's own carrier, stating that one
project's transcripts carry the namespaced and the bare form side by side, which is why the day
log's ritual list reads both. That document is correct, and a lexical ban cannot tell it from one
naming a dead route; this is the failure
[the sweep for the role-resolution shortcut](#the-shortcut-one-copy-names-outright) also met: a
forbidding check about a rule is the one most likely to forbid the prose that states it. An adopting
project's documents have no reason to quote the form as evidence, so the entry is sound there and is
stated as that project's.

## The day log's destination port

The destination began as one key: a directory, in the section that measures a day. That is the
shape [`schema.md § 26`](../plugins/mjolnir/config/schema.md#26-the-day-logs-destination-port)
replaced; what follows is the argument for the replacement.

The surveyed copies all wrote a file, and a directory addresses a file store completely. None of the
reasons below is about files being insufficient.

- **The store is read back, and not only written.** § 9's own cross-day validation already reads
  every recorded day, and against a directory of per-day text files that is a filename convention
  the surface never stated. A second reader — the role that takes a period's line items out of the
  same store — is proposed and not built
  ([`divergences-and-rulings.md`](divergences-and-rulings.md)'s still-open list); the shape has to
  admit it. An operation with a stated absent case is what answers this everywhere else here.
- **The grain of the two values differs by consumer.** Hours aggregate across days and a
  description does not, so the store has to be readable for hours over a range without the
  descriptions being what is read — which a store addressed as *a directory of entries* cannot
  express and an operation can.
- **A store that is not a file has no directory.** A spreadsheet, a document or a worklog is
  addressed by an identifier and a tab, and the artifact store's own `dir`
  ([`schema.md § 11`](../plugins/mjolnir/config/schema.md#the-store-and-when-an-in-tree-store-is-safe))
  cannot carry one either.
- **The day-log role's own rules were written in one carrier's vocabulary.** *A redo deletes the
  file and writes a new one* is how a file is rebuilt whole; a spreadsheet row is replaced, and a
  store with no delete would be patched in place — the thing the rule exists to forbid. The rule
  was right and its statement was not portable, which makes this a port rather than a second key,
  and the same reading reaches every other place that skill said *the file* where it meant *the
  entry*.

### The section a port's operation list is read from had to become a parameter

The contract finds an operation list by its table's column headers and refuses a second one:
appending a second table with those headers to the surface and asking for the list comes back
refused, the operation list stated more than once and the tables free to disagree. That refusal is
correct, and it made a second port impossible while the section the contract read was a constant —
[`schema.md § 26 → Which section`](../plugins/mjolnir/config/schema.md#which-section-a-ports-operation-list-is-read-from)
is the shape that resolved it, chosen over a sibling module.

A second copy of the contract per port would be a second place a fallback could be defaulted — the
defect the contract's own docstring refuses — so what is parameterised is the lookup, and a port is
three facts carried by one marker on the line stating its kind.

Two near-miss spellings of the marker come back **dropped**, not refused — a clause that lost its
colon, which is indistinguishable from English prose, and a capitalised keyword, matched
case-sensitively like every other clause there. What catches a marker lost that way is the contract,
not the reader
([`schema.md § 26 → Which section`](../plugins/mjolnir/config/schema.md#which-section-a-ports-operation-list-is-read-from)):
its section's table then belongs to no port, which is refused as an operation list nothing reads.
The reader's inventory comparison catches it only where the surface is left declaring no port at
all; with another port still declared the inventory is non-empty and that comparison is silent.

### Where the directory went, and why it is still not required

The directory key moved under the kind it was always addressing —
[`schema.md § 26 → What each kind`](../plugins/mjolnir/config/schema.md#what-each-kind-of-destination-block-carries).
It is deliberately unmarked, as § 3 leaves the three state-mapping keys in its per-kind blocks:
whether a project needs a destination at all is the carrier axis's question, so an absent directory
is a decision this reader cannot tell from an oversight.

The reader reports it instead, as it does an unset evidence script: a project mapping the day-log
carrier and stating no directory for the file kind gets the key in `unavailable`, and the role says
what it could not record —
[`schema.md § 11 → A report names what it could not establish`](../plugins/mjolnir/config/schema.md#a-report-names-what-it-could-not-establish).

The conditional marker does not fit. The kind defaults to the file kind, so a condition on that kind
fires for every configuration — including one that writes no `day_log` block at all, which the
reader's own defaults create on the way past. Marking the directory conditionally required would
refuse a project that maps no day-log carrier, the one project certain not to need it.

### The grain, and the address

One entry per day per project, which the skills root already decides —
[`schema.md § 26 → One entry per day`](../plugins/mjolnir/config/schema.md#one-entry-per-day-and-the-day-belongs-to-one-project).
One entry per day across projects, with the project named inside the entry, loses to a rule the day
log already carries: the entry is the two values and nothing else, which a project name inside it
would be the first thing to break. A shared timesheet, the first store two projects would write to,
is answered by the store partitioning, not by the entry growing a third value.

A destination block carries an address and never a credential, so this surface declares no key for
one —
[`schema.md § 26 → The store's address`](../plugins/mjolnir/config/schema.md#the-stores-address-and-what-may-not-be-written-beside-it).
That bounds what may be written in the block, not which kinds may exist: the credential is named in
`environment.inherits` and carried by the shell, exactly as a tracker kind behind a service does it.

### The spreadsheet kind, and the three things it had to settle that a directory never did

The kind was stated for the reading half of this port —
[`schema.md § 26 → The destination's operations`](../plugins/mjolnir/config/schema.md#the-destinations-operations-and-what-each-absence-does).
A directory answers a period by being listed and parsed per entry; a spreadsheet already holds a
column of figures against a column of days, which is what a period's consumer sums. The
descriptions ride in a column of their own and are not a period's line items, which are stated at a
grain the day log is deliberately below.

**The sheet's shape is the project's.** A person who already keeps a timesheet has their own header
words in their own order, so the kind configures a mapping from the surface's three roles to the
sheet's own words and resolves it against the tab's header row —
[`schema.md § 26 → What each kind`](../plugins/mjolnir/config/schema.md#what-each-kind-of-destination-block-carries).
Every way that resolution fails is a refusal naming the key: a word the sheet does not carry, a word
two of its columns carry, two roles landing on one column. A fixed layout would refuse every sheet
that already exists, and a looser mapping fails without a refusal: a figure written into whichever
cell happened to be third reads as a run that worked, and the period read back is short with
nothing saying so.

**Values, never formulas, on the read as well as the write.** A summing formula in the sheet is a
second statement of the period and a stale one is a wrong invoice, so the write asks the host not to
parse what it is given and the read asks for what was *entered*, not what is displayed. A formula in
the hours cell is therefore an unreadable day, never the number it currently shows.

**Nothing holds a spreadsheet against two writers**, and that is reported —
[`schema.md § 26 → What each kind`](../plugins/mjolnir/config/schema.md#what-each-kind-of-destination-block-carries).
The file kind makes *one entry per day* a property of the file system by opening
exclusively; a spreadsheet has no such call and the host publishes no compare-and-swap. So the write
reads the day back and **fails naming both rows** where it finds two, and a person removes one.
A second row is still possible; what the kind guarantees is that no period is answered with the
doubled total.

A date cell holding a real date comes back as a serial number, and the epoch those count from is a
property of the spreadsheet this host's API does not publish — so such a row is reported as one the
kind cannot place in a day, not placed by guessing an epoch. That is the fail-closed direction, and
the row is reported apart from the days for the reason § 26 gives.

### What `locate` may answer with once an address is private

The spreadsheet's identifier is marked `# private`, and the mark bounds the port's own reporting
operation. `locate` exists so a role can say where an entry landed, and § 28 keeps a private value
out of every report — so under this kind `locate` names **the tab and the row** and never the store.
That is the capability answering, not its absent case: a tab and a row say more than the fallback's
configuration name to whoever can reach the sheet, and nothing to whoever cannot.

The same bound reaches a failure's wording: every refusal quotes the call it made, and the
identifier is in that call's URL path, so what is quoted is the part of the path *after* the sheet —
the range, the tab and the operation.

## The role-to-person map: four stores and one pointer

The readiness library carried `assignee_matches_role` with no configured source for it to read, and
the gating role said so: presence and correspondence are two questions, and only the first was
answerable. What closed it is
[`schema.md § 27`](../plugins/mjolnir/config/schema.md#27-the-role-to-person-map).

The survey found the same map in four places, in four kinds of store — a sibling reference file, a
project instructions file, a memory index section, and a memory fact — none aware of the others.
Each copy carries the argument against copying, in its own words:

> Read this file; do not copy the table into a skill. Two gates on one route that each carry their
> own copy will disagree about the same card, and a copy that has to be «kept in sync» is the defect
> rather than the maintenance burden.

> Two records of who owns the work that are allowed to disagree are worse than one.

That is this toolkit's own founding argument, written down independently by the projects it was
derived from and applied one level in: the thing being duplicated here is not a rule but a fact
about people.

### Why a pointer rather than a map

The maps hold personal names, handles and tracker member ids. None of that may enter a toolkit
several projects share, and the reason is not § 14's for a credential: an identity is a fact about
somebody who did not agree to be named in anybody's tooling. So the facet carries the pointer and
the shape, and the lookup is the shared reader's — one implementation, which four projects did not
have.

All four stores are prose, and a reader that parsed one would be guessing at a table's columns, so
a project keeping the fact in a document writes a mapping beside it. A command carrier, as the
ordering facet has, is what `revisit_when` on this facet records; one parser is cheaper now than one
more configured command for every project that keeps its map as data already.

### The shortcut one copy names outright

Never resolve a role by asking who the current user is —
[`schema.md § 27`](../plugins/mjolnir/config/schema.md#27-the-role-to-person-map). One of the four
copies states it flatly: asking the tracker answers *who is running the skill*, not *who holds the
role*. The two coincide exactly while one person runs everything — the state every project in the
survey was in — and the check then silently becomes *assigned to whoever is asking*, green on every
item including the ones on the wrong person.

The rule is therefore held in three places. The reader refuses `current_user` wherever a
configuration writes it, the sweep over the carrier roots refuses the spellings that ask, and the
reader's own suite writes a map with one identity in it and the shell with another and asserts the
answer is the map's. None of those reaches a role instructed in words to ask; what holds that is
§ 27 being the single statement of the rule.

The sweep's grammar has two failure directions: separating the two words on `[_-]?` refuses a
carrier describing the rule in English — *the current-user spelling* — and a lookbehind rejecting
the dash leaves `--current-user`, the one spelling that cannot be anything but code, unread. A
forbidding check about a rule is the one most likely to forbid the prose that states it; planting
the English form and watching it redden is what tests it.

Writing an assignee is a different act: recording who *took* an item is a fact about this run, so
the implementation behind `assign` may translate the running user's own spelling. The sweep is
scoped to the carrier roots for that reason, and the exemption is asserted on the green side.

## The half of a configuration no project could commit

The payoff of a configuration file is that it is **committed**: five projects each kept their own
copy of the day-log procedure, and extraction made the copy one shared, reviewable statement. All
five git-ignored their copy; the reasons are in [the decision record](divergences-and-rulings.md):
two had organisational reasons of their own — a client's organisation, a second collaborator — and
all five had the archive, every copy reading one private source on the machine the log is kept on.

The end state the migration's acceptance item named — *only their chat patterns, calendars and
exclusions local* — had no mechanism behind it, and
[`schema.md § 28`](../plugins/mjolnir/config/schema.md#28-a-configured-value-a-repository-may-not-hold)
is now that mechanism, including why a tracked file carrying those values would invert the payoff.

### Three shapes, and why the one that shipped is neither of the first two

**Declaring the whole configuration private** un-reviews the procedure to protect the values, the
opposite of what the migration was for.

**An overlay file merged over the tracked one** fails on a *missing* overlay. With no list of what
the overlay supplies, an absent layer is indistinguishable from an empty one: a day log then quietly
measures no chats, under-reports the day and reports success. And an overlay free to supply any key
is the first shape arriving one key at a time — nothing stops `host.checks` or a readiness list
moving out of review.

**A pointer per private facet**, as the role-to-person map above has, fails the other way: several
keys carry the class in § 9 alone, so each would need its own carrier, its own path and its own
absent case — one fact stated once per key, and a project moving a further value out would be a
surface change rather than a line in a list.

What shipped is the overlay with both of the pointer form's disciplines — the project names the
keys, and the surface marks which keys may be named
([`schema.md § 28`](../plugins/mjolnir/config/schema.md#28-a-configured-value-a-repository-may-not-hold)).
Without the list a missing layer is silent; without the marks the list is the first shape again.

### What was measured while the facet was built

Three ordering and shape rules of
[`schema.md § 28`](../plugins/mjolnir/config/schema.md#28-a-configured-value-a-repository-may-not-hold)
rest on these measurements:

- **Requiredness against the list.** Enforcing requiredness before reading the list refused the
  migrated example outright, on the archive address it had legitimately moved out.
- **Presence against value.** A gate that asked whether the private file *carried* a listed key
  passed a layer holding it with null under it, and the day log then counted every committer as the
  log's owner. The two halves now read one test, on the value.
- **A block read.** `day_log.evidence` answered with the tracked file's shape — six keys resolved to
  nothing, no stop — while the leaf reads every consumer makes were correct; the report path had
  been defended by hand and the accessor path was not looked at.

The direction not closed
([`schema.md § 28`](../plugins/mjolnir/config/schema.md#28-a-configured-value-a-repository-may-not-hold)):
a reader older than a mark reads the tracked file alone, and that splits by requiredness. A reader
one commit behind **refused** the migrated example — *is empty*, against the conditional marker on
`day_log.evidence.chat.path` — the archive address being a key it requires and the list being
something it cannot see. So a listed key carrying a requiredness marker fails loudly there (§ 1's
obligation from the other side), and only a key carrying neither resolves absent and measures a day
from nothing. What closes that half is the plugin and the surface travelling together; the day-log
role holds the part that lands in a day, refusing a `chat` stream whose patterns resolve to nothing.

## The changes that never entered the loop, and the rule nobody had written

Every entry point on this surface assumed an item exists, and nothing said what a project does with
the changes that should never have one — though both projects measured were already doing it. What
closed it is
[`schema.md § 30`](../plugins/mjolnir/config/schema.md#30-the-changes-that-do-not-go-through-the-loop).

A pull request opened for a one-line correction to a documentation file was refused in four words:
*this is a change too small for a pr*. The rule written down afterwards split behavioural change —
code, configuration defaults, prompts, schema migrations — from documentation, comments, ignore
files and typo or accuracy fixes, and offered one test for a hard case: *could a reviewer disagree
about correctness*.

Two things make that a configured fact, ruled in
[`schema.md § 30`](../plugins/mjolnir/config/schema.md#30-the-changes-that-do-not-go-through-the-loop).
The repository's own history already did it that way before the rule existed, and the session
followed a generic branch-first instruction over it — a convention readable by a person and by
nothing shipped, the same shape `tree_dir` was extracted for. And the cost: a branch, three gate
jobs, a merge commit and a branch deletion for a one-line fix, during which the document stays
wrong.

### The axis is what a change is, and the measurement rules out the obvious alternative

In a second project an entire release's tooling work went direct and unticketed — process scripts,
measurement harnesses and documentation — while every product change in that same release went
through the loop. That project also keeps one-line-fix commits on release branches with no item at
all.

So the gate there cannot tell a deliberate bypass from a missed item —
[`schema.md § 30`](../plugins/mjolnir/config/schema.md#30-the-changes-that-do-not-go-through-the-loop)
— and the day log, the session summary and the hours breakdown all read commits.

The axis that separated the two was neither size nor risk. Some of the unticketed tooling work was
**larger** than the ticketed product changes beside it, so *under N lines* would have exempted the
wrong half of that release. No key states a size and the decision is handed no count —
[`schema.md § 30 → Why the axis is kind`](../plugins/mjolnir/config/schema.md#why-the-axis-is-kind-and-never-size):
the reader takes the changed paths and a kind, so a change wholly inside a class answers the same
way at one line and at two hundred files. The signature holds the rule; the refused spellings only
catch the habit.

### Why the two projects' tests are both kept

One divided the question by the files a change touches, the other by whether a user sees the
result, and the two do not line up — the second project's tooling lives beside its product code, so
no path glob expresses its rule. So a class carries path globs, change kinds, or both, and where it
states both they are a **conjunction** —
[`schema.md § 30 → What a class is`](../plugins/mjolnir/config/schema.md#what-a-class-is-and-the-conjunction-that-makes-it-one).

The case that argues for the whole facet is a change touching one exempt path and one that is not
(same section). It reads as documentation to every rule asking *does this change touch the docs*,
and waves the code through under cover of the documentation edit; the test is therefore *every*
changed path, never *any*.

A glob crosses a directory separator here, and the two-star form every other tool teaches is
**refused** rather than reinterpreted: one spelling read two ways.

### Who answers a case the paths cannot, and where the change then goes

A class decided by its kind leaves a question the changed paths cannot settle, and the two projects
answer it differently: the first would put a hard case to a person, the second takes that round
trip on no commit in its measured history. So who answers is configuration —
[`schema.md § 30 → Who decides`](../plugins/mjolnir/config/schema.md#who-decides-a-case-the-paths-do-not-settle)
— asking is the default, and a class stating paths alone reaches neither arm.

Under a project that carries a kind-decided class, a change whose kind nobody has stated is
**unanswered**, not not-exempt; reading it as not-exempt silently drops the exemption the project
configured, which is why there are three verdicts.

The first project commits an exempt change to the integration branch, which `§ 10` already derives
from what the remote advertises as its default. The second sends a release's tooling work to that
release's branch. So the key exists for the second case and is null for the first, and it names a
branch, never a working directory —
[`schema.md § 30 → Where an exempt change goes`](../plugins/mjolnir/config/schema.md#where-an-exempt-change-goes-and-the-one-role-it-runs):
an exempt change has no item, no claim and no tree cut for it.

## A status that moves backwards, in three of six projects and ruled in two

Every status ladder the survey read runs one way, and every writer on it advances
([`schema.md § 4.2`](../plugins/mjolnir/config/schema.md#42-status--an-ordered-set-of-name-role-writer)).
A sweep of all six projects' process copies for a move in the other direction found one in **three**
of them, and only two of the three state it as a rule:

| | What was found | How it is written |
|---|---|---|
| A | Acceptance is a person's judgement against the item's own criteria, **and the same person may send the item back** out of the deployed column instead of on | **Ruled**, in the deploy role's own text, beside the prohibition on that role touching the next column at all |
| C | A finished item whose work was never implemented, with new criteria appended under it: **surface it and ask whether to reopen** | **Ruled**, in the filing role, and the ruling is to *ask* — the only instance where the answer is a question rather than a move |
| B | The board's automation writes the code-landed status off every closing merge, so a second change under an item already past that status steps it back | **Not ruled anywhere.** The only statement about it is the opposite one — ⛔ never hand-edit a status, because the status means the code really was deployed |

The remaining projects state nothing about a reverse edge: two have roles that refuse to write a
status later than the work supports and never the other way, and one carries no work-item status
vocabulary for a reverse edge to move through at all.

Three projects with one case each, in three different roles, answered three different ways: a
project's answer is a function of *what happened*, not of where the item sits, so the edge is keyed
on the trigger and carries its own writer —
[`schema.md § 32`](../plugins/mjolnir/config/schema.md#32-a-status-that-moves-backwards).

A's case also settles the writer, which § 4.2 had nowhere to say: the status's forward writer is
the deploy, and the person sending it back is the one who ordered the work. So a reverse edge's
writer is not the target status's — two writers on one transition pair.

B's case makes it a facet. Its release gate reads every item *below* the deployed status and fails
the release where one owns a commit on the integration branch. An item that stepped back is caught;
an item that should have stepped back and did not is invisible to it, ships in the batch and is
named in no report. The gate is sound and the ladder is wrong, so the edge belongs on the surface.

A deploy that fails after the advance was written is not a trigger: no project's deploy role steps
the item back on a failed run, and one states that a failed release is not repaired by moving
anything backwards.

The criterion is what a project's work was measured *doing*, ruled or not
([`schema.md § 32`](../plugins/mjolnir/config/schema.md#32-a-status-that-moves-backwards)). Two
near-miss criteria each drop a case:

| Criterion | What it wrongly excludes |
|---|---|
| *What a role in this procedure observes* | A's acceptance rejection, that project's deploy role having no counterpart here either — so it drops a case with a rule behind it |
| *What a project was measured **ruling*** | B's merge case, which is ruled nowhere — so it drops the one case with **no** rule, which is the one that needs a key |

A facet that lets a project rule what is already happening to it cannot take *already ruled* as its
admission test. What would add a missing trigger is a project found doing it; the section below is
where that was looked for end to end.

## Seven deploying carriers read in full, and the provisional ruling they revise

Ruling (10) was settled on one copy read in full and the rest read structurally, against a set that
left out a carrier whose name contains no form of the word *deploy*. Every deploying carrier the
readiness run enumerates under this role has since been read end to end: seven carriers across five
of the six projects.

| | the carriers | lines | what reaching the target invokes |
|---|---|---|---|
| A | two, split by environment, and one of them named after neither the role nor the environment | 228, 336 | a dispatch with typed inputs; and a tag push **handed to a person**, with no dispatch form at all |
| B | one carrier covering four targets, two of them machines that run no release at all | 298 | the project's own command, beside three more it sources first |
| C | two, split by environment | 139, 222 | a hosted build, configured by a file the service executes — **no script in the repository** |
| E | one | 69 | the project's own command |
| F | one, whose second target the command refuses by name | 381 | the project's own command |
| D | none | — | — |

The carriers run 69 to 381 lines, and the two longest are not the two most irreversible: the
longest deploys to a stack on the machine it runs on, and its length is verification and board
bookkeeping.

### What the full read confirmed

Every clause of the provisional ruling but the one about a script survived. Held against all seven:

| the clause | what the carriers say |
|---|---|
| confirm intent and name the target | **7 of 7** |
| an explicit go, *for this deploy* | **7 of 7**, and two state outright that an earlier go does not carry |
| read-only preflight | **6 of 7**; the seventh's first write precedes its own gate, for a reason it states |
| verify, rather than reading the exit status | **5 of 7** say so in their own words, three of them from an incident |
| report what was rebuilt, and what failed with its log tail | **7 of 7** |
| hosts, services, secrets and build steps stay local | **nothing contradicted it** |
| and tier selection with them | ⛔ **replaced rather than confirmed** — [`§ 31`](../plugins/mjolnir/config/schema.md#31-test-tiers--what-each-one-needs-before-it-can-run-at-all) states which tiers a project has, what each needs, whether it is asked for, how its cases are selected and which targets refuse it; each tier's own **command** is what stayed local |

The boundary clause is
[`schema.md § What the procedure models`](../plugins/mjolnir/config/schema.md#what-the-procedure-models-and-what-it-only-names-and-calls).
Every host address, service name, credential path, image reference, container name, queue, health
endpoint and suite invocation in all seven is the project's own, and no two projects' are alike.

### What it revises, and why each revision is the measurement rather than a preference

«A project whose deploy is one script keeps that script» describes four of seven carriers. Two have
no script in the repository — one's deploy is a configuration a hosted service executes, the
other's is a run the host makes — and one of the four sources three further commands before the one
it is named for. The build side found the same
([*Where a deploy lives*](build-surface.md#where-a-deploy-lives)); the carrier side adds a third
shape: a target a project rules **a person performs**, a decision stated beside its reason (the act
spends a version for ever), not the absent case of a capability. Hence
[`schema.md § 33 → The three shapes a target is reached by`](../plugins/mjolnir/config/schema.md#the-three-shapes-a-target-is-reached-by).

Five of seven ask for a go on every target, including every staging environment in the survey; the
two that make a target free to run name a stack the session is the only user of. So *not
production* is not the test, and a key naming what is live would be silent on the target nobody has
thought about — the key is written in the negative, as in
[`§ 21`](../plugins/mjolnir/config/schema.md#the-machines-named-are-the-ones-that-are-not-live), at
[`§ 33 → Which target, and what makes one live`](../plugins/mjolnir/config/schema.md#which-target-and-what-makes-one-live).
Liveness decides whether the ask is put at all, the only test
[`§ The loop`](../plugins/mjolnir/config/schema.md#what-carries-the-item-forward-and-where-it-stops-to-ask)
admits for one, and it reads the two free targets as their copies state them, *fine to run freely*.
[`§ 29`](../plugins/mjolnir/config/schema.md#a-dispatch-is-the-only-write-and-it-carries-its-own-go)'s
refusal stays unconditional beside it: it sits on the operation and reads no facet. No target in the
survey is both dispatching and not live.

The go has to name something a gate can read back — the binding at
[`schema.md § 29 → A dispatch is the only write`](../plugins/mjolnir/config/schema.md#a-dispatch-is-the-only-write-and-it-carries-its-own-go).
Four of the seven state what the question must carry (the version, the flags, the target, the
batch), and in one the record is written only when the answer names the version, with a guard
refusing the act without it. That project's act is a tag push, not a dispatch, so the binding is a
property of the act rather than of the port.

Six write nothing before the go; one advances a long-lived branch first, because the run it starts
asserts the released commit is contained in that branch and refuses otherwise, with the version
already spent. That copy names the window it opens and rules out moving the branch back as a
repair, so the surface places the write outside the preflight and asks for the window to be named:
[`§ 33 → What runs before the target is confirmed`](../plugins/mjolnir/config/schema.md#what-runs-before-the-target-is-confirmed-and-what-it-may-not-do).
The thing about to be invoked is established first, measured by two copies from opposite ends: a
secrets file absent, which one stops on and points at a template; and a workflow present on the
dispatched ref and absent from the host's own registry, which the host refuses with a message
naming neither the ref nor the file.

The tracker write, absent from the provisional ruling, is in six of the seven carriers and is now
stated in
[`schema.md § 33`](../plugins/mjolnir/config/schema.md#33-the-deploy-targets-and-what-reaching-one-invokes).
Each writes exactly one forward edge, and three projects write two different ones from two targets
— so the status a deploy advances to is a property of the target, which is the second reason the
facet is a list.

The role an item must already hold is derived, and the derivation is right for all seven: the
status immediately before the advance in
[`§ 4.2`](../plugins/mjolnir/config/schema.md#42-status--an-ordered-set-of-name-role-writer)'s own
order, including in the project whose ladder has no deployed status and whose one target steps an
item straight from code landed to finished. A project whose batch is drawn from further back would
make it a key; none was found.

### The batch, and the two assemblies that lose an item

No copy advances an item on its status alone, and two name the failure: a card that moved while its
code never reached the branch. Each narrows the status list by a test of its own — owned commits on
the integration branch, a fix version with the commits verified in the log, a milestone, a commit
list — so
[`schema.md § 33 → The batch`](../plugins/mjolnir/config/schema.md#the-batch-and-the-two-ways-of-assembling-one-that-are-wrong)
makes the narrowing a command and states what it is asked, not how it answers.

Two of the seven narrow by a *range* rather than by membership. A batch computed from *what changed
since the last deploy* answers no for an item whose code landed earlier, so an item that stepped
back out of a later role, its code in the branch for weeks, is in no batch and no batch report.
Both copies describe the symptom without reaching the cause: one's table carries a row for *a merged
pull request in neither the list nor a later one*, with an instruction to say it out loud. Hence the
rule at
[`§ 33 → The batch`](../plugins/mjolnir/config/schema.md#the-batch-and-the-two-ways-of-assembling-one-that-are-wrong),
and the limit beside it: nothing here checks the command, which is
[`§ 12`](../plugins/mjolnir/config/schema.md#12-ordering)'s position for its own.

### What the reading settles about the trigger that was left out

[`§ 32`](../plugins/mjolnir/config/schema.md#32-a-status-that-moves-backwards) leaves out a deploy
that fails after the advance was already written. The state is unreachable by construction: every
one of the six that advances an item writes the advance after the deploy it advances on has been
verified. One states the prohibition outright — a card is never moved back a column by that skill —
and another assigns the reverse move to the person who ordered the work. Nothing is added to the
trigger set; a project whose advance runs first would add it.

### What a deploy verifies, which is the half the copies spend their length on

The invocation's own answer is not the delivery. A build the service reported successful shipped
one of two halves, because it was pointed at the wrong configuration. A container reported healthy
was mid-load and refusing every request, its liveness check deliberately saying nothing about
readiness. A suite exited zero having deselected the cases that needed material. Three incidents in
three projects, one shape, which makes
[`§ 33 → What a deploy verifies`](../plugins/mjolnir/config/schema.md#what-a-deploy-verifies-and-what-it-reports)
a rule rather than three cautions.

A command finishing is not a step finishing, stated by three copies about work a command queues and
exits ahead of, each with its own reading to judge progress by. The report names what it
could not establish — every skipped scenario, every item left behind, every step still running, and
what the deploy left standing — which is
[`§ 11`](../plugins/mjolnir/config/schema.md#a-report-names-what-it-could-not-establish)'s rule with
this role's own list under it.

Whether the target list is a project's or a code root's is
[`Which repository an act is in`](#which-repository-an-act-is-in-and-why-it-is-not-the-lists-own-axis),
and
[`Publishing a release`](#publishing-a-release-the-two-writers-and-the-precondition-that-holds-a-target)
settles which subset of a grouping a target advances.

### Which repository an act is in, and why it is not the list's own axis

The list is the project's and the repository is the entry's, at
[`§ 33 → Which repository a target's act happens in`](../plugins/mjolnir/config/schema.md#which-repository-a-targets-act-happens-in)
against [`§ 1`](../plugins/mjolnir/config/schema.md#a-projects-code-is-not-always-one-repository)'s
code roots. The two readings already here answer it.

What rules out nesting is the axis. The build side read what each project's deploy resolves against
and found a directory in none of them
([*Where a deploy lives*](build-surface.md#where-a-deploy-lives)); that page holds the per-project
classification, since it counts projects and this one counts carriers. A list keyed on the directory
would be keyed on the one axis no project's targets divide on, and every fact measured is a
target's, as
[`§ 33`](../plugins/mjolnir/config/schema.md#33-the-deploy-targets-and-what-reaching-one-invokes)
states.

Nesting would also owe a second rule. `name` is the word a deploy is asked for by, so two roots'
lists would still have to hold their names apart across the project —
[`§ 1`](../plugins/mjolnir/config/schema.md#a-command-root-is-not-a-code-root)'s rule for a command
root's name, for the same reason: one name answering in two places resolves into whichever
repository was read first.

The one project with two repositories exhibits the case. Its two roots share nothing but the host
kind — disjoint check sets, a different number of long-lived branches each, and a deploy that takes
a ref on one side and no ref at all on the other — and its second repository carries a deploying
workflow of its own. Its instructions state that no skill on its route drives the second
repository, so its dispatch is by hand: [ruling (26)](divergences-and-rulings.md#4-the-rulings).

The key makes four references resolve per repository, each held in the table at
[`§ 33 → Which repository a target's act happens in`](../plugins/mjolnir/config/schema.md#which-repository-a-targets-act-happens-in).
Reproduced on the shipped two-root example, which carries three targets:

| what was read | what it answered before | the probe |
|---|---|---|
| `workflow` | every root's check names at once | its first target names a workflow out of the first repository's checks and its second out of the second's, and each loaded against the union |
| `command_root` | every root's declarations at once | its third target names a command root the **first** repository declares; moved to the second, which declares none, it still loaded |
| `code_root_runs_nothing` | nothing | that first repository states it, and a command target with no root named loaded anyway |
| the repository a dispatch is made against | nothing | — |

Without the last row the deploying role could not run on that project: its preflight resolves the
entry's command through the reader, and
[`§ 1`](../plugins/mjolnir/config/schema.md#a-command-root-is-not-a-code-root) states a command root
relative to one repository, so with two carrying the block the reader refuses a project-level read
rather than answering with the first. The value that resolves the call was in no file
this repository ships.

Two shipped examples each stated a
[`§ 31`](../plugins/mjolnir/config/schema.md#31-test-tiers--what-each-one-needs-before-it-can-run-at-all)
tier refused on a target name their own `deploy` did not carry. A tier refused on a word nothing
deploys to reads as refused somewhere and runs against every target, so that facet's entries are
resolved against § 33's own names.

## Publishing a release: the two writers, and the precondition that holds a target

The reading behind
[`§ 33 → Publishing a grouping`](../plugins/mjolnir/config/schema.md#publishing-a-grouping-and-the-precondition-that-holds-the-whole-target)
and the two operations it rests on in
[`§ 3`](../plugins/mjolnir/config/schema.md#the-operations-and-what-an-absent-capability-does): the
same seven carriers read for what a release writes that is not an item.

### One act or two, decided by the writers rather than by the shape

Two. One carrier's version is marked released by hand — the step is a link handed to a person,
every release — while the items in that version are advanced programmatically in the same minute.
One half's writer is a person and the other's is the procedure, and a single operation cannot carry
two writers: the surface states a writer per status
([`§ 4.2`](../plugins/mjolnir/config/schema.md#42-status--an-ordered-set-of-name-role-writer)) and a
writer per grouping ([`§ 4.8`](../plugins/mjolnir/config/schema.md#48-grouping--what-a-set-of-items-is-planned-into)'s
`closed_by`), and folding the acts together would oblige one of those keys to be ignored. The
deploying role is the one that closes a grouping, and it asks as `deploy`.

### Which subset: one key, because the rest was already derived

§ 33 already derives the role an item is advanced *from* — the status immediately before `advances`
in § 4.2's order, right for every one of the seven — and states the role it advances *to*. The one
addition is which grouping a target is scoped to: a name § 4.8 carries, or `none`.

`none` is not only the case of a project with no grouping. One carrier plans in an iteration and
deploys what landed: its batch must not be narrowed by the time box, because an item whose code
shipped from an earlier column is in the deploy and not in the iteration. So a project that has a
grouping still writes `none` on a target not scoped to it.

### The precondition: a key, and the two shapes that make it one

The precondition is stated, not derived:
[`§ 33 → Publishing a grouping`](../plugins/mjolnir/config/schema.md#publishing-a-grouping-and-the-precondition-that-holds-the-whole-target).
In both measured shapes the required role coincides with the role the advance is made from: one
project's release may carry only items a person has already accepted, and another's live deploy
refuses to run while any item with commits on the integration branch has not reached the
staging-deployed state. Deriving it from `advances` would look right on both, and would give every
project with a ladder a precondition it never ruled; a project whose statuses map no such role
publishes as it does today.

The key changes the consequence, not the role.
[`§ 33 → The batch`](../plugins/mjolnir/config/schema.md#the-batch-and-the-two-ways-of-assembling-one-that-are-wrong)'s
rule for an item outside the advance's role is *named and not advanced*, with the deploy going
ahead; this one holds the whole target and names every item short of the role, because a release is
a set and a person needs to know everything it is waiting on.

The procedure cannot produce the state: § 4.2 maps the role to a status written by the person who
ordered the work, or by a lower environment's own deploy. It is
[`§ 13`](../plugins/mjolnir/config/schema.md#13-what-counts-as-done--an-ordered-check-list-and-who-answers-each-check)'s
`answered_by` one state later.

One carrier's gate has a known hole it names itself: an item whose change is confined to a shared
library can never reach the earlier role, because no deployable service's flag set names it, so it
is advanced by hand. So the bar is read over a reported set: an item the answer could not place is
reported unanswered, never short and never clear, since a release held by an item nobody could place
reads exactly like one held by nothing.

### Where the set comes from, and the two arms it has

The publishing set is the grouping's items where a target names one and the batch's own candidates
where it does not — the two arms at
[`§ 33 → Publishing a grouping`](../plugins/mjolnir/config/schema.md#publishing-a-grouping-and-the-precondition-that-holds-the-whole-target),
which is why the precondition is independent of the grouping key. The second arm is the carrier
whose gate reads *items with commits on the integration branch*, on a project that plans in
no grouping at all.

The batch stays the only source of candidates for the advance, as
[`§ 33 → The batch`](../plugins/mjolnir/config/schema.md#the-batch-and-the-two-ways-of-assembling-one-that-are-wrong)
rules: the grouping narrows, and an item the grouping holds that the batch never named is reported,
not advanced. An unread grouping and an empty one are the same list, so the report carries which of
the two it was.

### What the trackers can actually do, which is where the absence is real

Reading a grouping's membership rides a query on every tracker that has one — a milestone's issue
listing, a board read filtered on a field's value, a bounded query on the field a project names — so
it is one of the two operations at
[`§ 3`](../plugins/mjolnir/config/schema.md#the-operations-and-what-an-absent-capability-does).
Marking one released does not: a grouping held in a field's value, the commonest carrier in the
survey, is not an object anything can close, and a board's iteration rolling over is a date passing
rather than an act. So the set is readable wherever a tracker's grouping has a query, and the mark
only where the grouping is a native object with a state of its own. No count is given here, for
the reason at
[`schema.md § 3 → Who declares a capability`](../plugins/mjolnir/config/schema.md#who-declares-a-capability):
each implementation declares what it does by implementing it.

Implementations that cannot mark one declare the mark absent rather than implementing it against an
iteration's dates or a label that cannot be closed;
[`schema.md § 3`](../plugins/mjolnir/config/schema.md#the-operations-and-what-an-absent-capability-does)
states what an absence does.

A carrier a given tracker has no object for is refused with the key named rather than reported
absent —
[`§ 4.2`](../plugins/mjolnir/config/schema.md#42-status--an-ordered-set-of-name-role-writer)'s rule
for a status word a tracker cannot hold. *This tracker cannot do it at all* takes § 3's fallback and
the run carries on; *this project wrote something this tracker has nowhere to put* stops with the
key.


## The release half: one copy that arrives as data

Turning landed work into a released version is a role of its own, not the deploying role's terminal
third; the facet is
[`schema.md § 34`](../plugins/mjolnir/config/schema.md#34-the-files-that-carry-a-version-and-what-cutting-a-release-writes).

A deploy names a target environment and is refused without an explicit go for a live one; a release
names a version and is refused without landed work to carry it. Different preconditions alone do not
make two roles; what the copies carry decides it.

| | what the copy carries | where it lives | what it invokes |
|---|---|---|---|
| the deploy survey | seven carriers across five projects, each naming a **target** | a script, a hosted configuration, or a run the host makes | the project's own command, a dispatch, or an act handed to a person |
| the release half | **one** copy, naming a **version** | a rules file, as **data** rather than as procedure | an ordered file list, a changelog insert, a tag and a publish |

The deciding fact is the second row's middle cell. Every other process fact in the surveyed copies
arrives as prose a role performs; this one arrives as an ordered list of
`(path, kind, pattern, replace, optional)`, so what varies between projects is a file list, which
[`schema.md § What the procedure models`](../plugins/mjolnir/config/schema.md#what-the-procedure-models-and-what-it-only-names-and-calls)
makes configuration.

One copy is thin evidence for a facet, as ruling (31) states for the grouping axis. It is admissible
because the copy carries the facet's whole shape: every key the surface declares is a key that copy
writes, and none was invented to round the list out.

### The three switches, and the one of them that is not a key

The same rules file carries three switches beside the file list: whether the release has a
user-facing audience, whether it publishes packages, and whether CI owns the changelog. The audience
is not a key: the audience and register of an artifact a role writes are
[`schema.md § 8`](../plugins/mjolnir/config/schema.md#8-language-register-audience--per-artifact-not-per-project)'s,
per artifact.

`changelog_ci_owned` changes what the procedure does: a role that wrote a file CI also writes
produces a conflict on every release. It is a project's statement about ownership, not a reading of
the file, because a changelog CI writes and one nobody writes look identical in a tree:
[`schema.md § 34 → The changelog CI owns`](../plugins/mjolnir/config/schema.md#the-changelog-ci-owns-which-inverts-the-role).

`publishes_packages` decides whether the release is the person's act, the only test
[`schema.md § The loop`](../plugins/mjolnir/config/schema.md#what-carries-the-item-forward-and-where-it-stops-to-ask)
admits for an ask — the reasoning the deploy survey measured on the carrier that hands its act to
a person because it spends a version for ever. The tag is not what the ask is about, since a tag
can be moved and a published artifact cannot:
[`schema.md § 34 → What a release publishes`](../plugins/mjolnir/config/schema.md#what-a-release-publishes-and-what-this-section-does-not-carry).

### The flag with a measurement behind it, and the default that inverts § 33's

`optional` was observed being needed: one of the three files that copy lists does not exist in the
project it came from, and a release that errors on it cannot be cut.

Its absent reading is the strict one, the opposite of `not_live`'s. There, a key read as absent
would make a live target not live, silently; here, a file a project does not have and did not mark
stops the release with the file named, which is loud. See
[`schema.md § 34 → The files a version is written in`](../plugins/mjolnir/config/schema.md#the-files-a-version-is-written-in-and-the-two-kinds-of-edit),
and for the deploy side
[`schema.md § 33 → Which target`](../plugins/mjolnir/config/schema.md#which-target-and-what-makes-one-live).

The copy spells its named capture in its own stack's dialect, and the expression here is the
carrier's engine's — the rule
[`schema.md § 8`](../plugins/mjolnir/config/schema.md#8-language-register-audience--per-artifact-not-per-project)
states for a branch slug. The expression is compiled at the load, so a dialect mismatch is refused
where it is written.

### What the ordering buys, and the one guarantee the carrier does not make

The edit is all of it or none of it: a release with half its files bumped is worse than a release
not cut, because the half that moved is what every later reader believes. The surveyed copy makes no
such guarantee — its edits run in sequence and a failure part way leaves the tree mixed:
[`schema.md § 34 → The files a version is written in`](../plugins/mjolnir/config/schema.md#the-files-a-version-is-written-in-and-the-two-kinds-of-edit).

The carrier does not promise atomicity against a crash, and its report says so: the write loop can
be interrupted between two files. What is closed is a release that was never going to work being
carried out part of the way.

Which work a release carries is read by
[`schema.md § 33 → The batch`](../plugins/mjolnir/config/schema.md#the-batch-and-the-two-ways-of-assembling-one-that-are-wrong)'s
rule, not a second command
([the reading above](#the-batch-and-the-two-assemblies-that-lose-an-item)); closing whatever the
release corresponds to is the grouping axis's question — the surveyed copy closed a release and an
iteration together one to one, one project's coincidence until a second shows it.

## The live data step: two copies, and the four stops they already carry

The seven carriers re-read for the one step inside a deploy that writes irreversibly to a live store
give the facet at
[`schema.md § 35`](../plugins/mjolnir/config/schema.md#35-the-live-data-step-a-deploy-performs-and-the-rails-it-is-performed-under).

Two of the seven perform such a write. The shape of the absence in the rest is what made the key a
target's rather than a project's:

| | what the carrier does with a live store | what that leaves the facet |
|---|---|---|
| B | one carrier over four targets: **two** of them write to a store, **two** hold none at all, and the two that write **detect their pending sets differently** | the block is a target's; a project-level one is wrong for half of this project's own targets |
| C | the environment-split pair, and only the irreversible-facing one of them writes | the same conclusion from a second direction — one project, two carriers, one block |
| A | two carriers, a dispatch and an act handed to a person; neither reaches a store | the key is omitted, and that is a deploy exactly as (10) leaves it |
| E, F | the store is reached by the application's **own startup** — a framework migrates on boot and the deploy never performs a step | an absence with a cause, rather than a project that has not got round to it |
| D | no deploying carrier at all | — |

The two copies agree on the sequence — dump → verify → *(rehearse)* → confirm → write — and disagree
on three of its four stops, which makes each of the three a key. The facet performs the sequence at
[`schema.md § 35 → The ordering`](../plugins/mjolnir/config/schema.md#the-ordering-and-what-the-role-reports).

### The size assertion that was the wrong strictness

C asserts the archive exists and is non-trivial in size before continuing. B carries the opposite
rule, with an incident behind it: a dump came back at roughly a quarter of the previous release's
bytes, the shrink was read aloud as catalogue loss, the catalogue was intact, and the difference was
row-overhead, index and dead-tuple volume that a dump does not write. Its text: *two dumps taken
months apart are not comparable by size in either direction*; it verifies instead that reading the
dump back enumerates every table the store holds.

So the facet carries two keys and no size, and the verdict is an exit status —
[`schema.md § 35 → The backup is verified by a
command`](../plugins/mjolnir/config/schema.md#the-backup-is-verified-by-a-command-and-never-by-the-artifact-it-wrote).
A project that wants the size test states it inside its own verification command.

The same copy's dump runs whether or not the release carries anything to apply, with no override,
because what a release writes against a store is not fully known until it has run, and a dump taken
afterwards records the damage rather than the state before it.

### A step that takes no backup, which neither copy carries

⚠️ **Both copies dump before every write, and an adopter's report is what added the other case.**
Its staging target's writes take no backup, and the facet as both copies shaped it made `backup` a
pair of commands no such step can state. ⚠️ **The case was read against the shipped surface rather
than run**, so the reasoning is this repository's own and not a copy's.

⛔ **So the absence is stated, never omitted**: `backup` stays required and may carry a reason in
place of its two commands, on any target, live or not. The ruling weighed allowing it only where
the target is not live, and declined that limit: what licenses the absence is the project saying
why, where every go on that write reads it — and the go on such a step has to say there is no
backup, so an approval of a write nothing can recover from is one that said so —
[`schema.md § 35 → A step that takes no
backup`](../plugins/mjolnir/config/schema.md#a-step-that-takes-no-backup-and-the-go-that-says-so).

### A rehearsal one copy has for everything and the other has for nothing

C pairs every scripted write with a sibling that sets a dry flag and changes nothing, and its
carrier runs the dry one first and reviews the output. B's writes are plain statements applied one
at a time; it prints each in full and confirms it, noting that re-applying one may error and that
this is expected.

So the rehearsal is a key, not a step —
[`schema.md § 35 → A rehearsal the project may not
have`](../plugins/mjolnir/config/schema.md#a-rehearsal-the-project-may-not-have-and-what-reading-it-is-for).
Both copies agree on the reading: C's text says the guarded variant must report no divergence and
that a guard which aborts stops the deploy, a verdict that exists only once it is read.

### The prompt the session would have to answer on the applicant's behalf

C's shared helper opens a reader on standard input, asks whether to continue, and exits on anything
but a yes; it returns without asking when the dry flag is set, so the prompt guards exactly the
irreversible half. A session running such a command unattended would have to feed it an answer on
behalf of the person whose store is about to change.

So the go is the procedure's own recorded ask, never the command's prompt, and a configured command
carrying its own answer is refused where it is written —
[`schema.md § 35 → Who performs the
apply`](../plugins/mjolnir/config/schema.md#who-performs-the-apply-and-the-go-that-is-never-the-commands-own-prompt).
C also states the standing rule the `apply_by` key exists for: the live writes are the operator's,
and its carrier performs them only under an explicit go for that deploy. Both readings are a
project's to state, so the key has two values.

Both copies put their confirmation before the dump, where neither the verified dump nor the
rehearsal's output exists — their question is *shall this deploy happen*; the facet adds *shall this
write happen, given what the rehearsal said*. The test is
[`schema.md § The loop`](../plugins/mjolnir/config/schema.md#what-carries-the-item-forward-and-where-it-stops-to-ask)'s
and nothing else: the act is the person's, and the evidence is new.

No `answered_by` key sits beside the step: it would make the one unconditional rail configurable,
under a word the surface uses for who answers a completion check, and anything but *human* there
would turn the ask off.

### The ordering against the image, which one copy calls a decision

C writes before its build, always. B states the order is a decision: its store sat several writes
behind a release whose new code reads a table, a column and a dropped type on its first call, so the
write had to precede the image, while a write purely additive to running code belongs after it. B
asks that the order chosen be stated in the confirmation.

So `order` is a configured default the go names —
[`schema.md § 35 → Where the step falls against the
invocation`](../plugins/mjolnir/config/schema.md#where-the-step-falls-against-the-invocation-which-the-go-names).
The role may not decide it by reading the pending writes: whether new code hard-requires a schema is
knowledge of that project's code, the boundary's middle column.

### Two adopters a single block could not state

Both copies carry one write per deploy, and a single block holds one `apply` and one `order` moving
the whole step — dump, rehearsal and write — to one side of the image. Two adopters reported shapes
it cannot state, read against the block rather than run:

| the adopter's step | what one block does with it |
|---|---|
| the dump has to be taken before the image, and the write made after it | `order` moves the dump with the write, so either the dump lands after the new code has served or the write lands before it |
| several writes against one store, some owed before the image and some after | one `apply` holds one write, so the rest are performed outside the procedure and outside every rail on it |

So the block is a list of steps, each step's phases placed on their own side —
[`schema.md § 35 → Several steps on one target`](../plugins/mjolnir/config/schema.md#several-steps-on-one-target-and-the-side-each-phase-falls-on).
A placement is admitted only where it never runs *dump → verify → rehearse → go → write* backwards,
refused at the load and again at the write. Each write keeps its own go after its own evidence, and
a stop names every write made and not made. A single block with no `sides` is the facet the two
copies state.

### The forbidding rule no copy carries

Neither copy forbids editing a write that has already been applied, and the facet does. Both warn
about re-applying one — B's confirmation says a non-idempotent write may error on a second run and
that skipping it is safe. This is the position [`schema.md
§ 33`](../plugins/mjolnir/config/schema.md#33-the-deploy-targets-and-what-reaching-one-invokes)
takes for the one of its three review classes that came from no copy: a rule with no project's
experience behind it.

An applied write is no longer an instruction but the record of what the store was made to be, so
editing it leaves every later reader believing a state the store never passed through. The released
set is the project's to print, by the device the ordering axis uses for its own queue, read from
live targets only, since a store the session is the only user of can be rebuilt:
[`schema.md § 35 → A record of the store's
state`](../plugins/mjolnir/config/schema.md#a-record-of-the-stores-state-is-never-rewritten). A
command that could not be run leaves the change reported unchecked rather than passed, (10)'s
absence-of-signal rule.

## Two skills outside the loop, counted rather than taken on the claim

The survey that produced the loop's roles was keyed on those roles, so it missed skills the same
projects had copied for reasons unrelated to an issue. Two were named as missed, and both are ruled
out of this toolkit, though they fall on opposite sides of the de-duplication test.

### The counts, and the one of the two that has only ever had one copy

The reading was taken over every skill directory under every project here, over each project's own
history for the path, and over the whole tree for the mechanism each skill is built on, so that a
copy under another name would still be found.

| what was claimed | what the count says |
|---|---|
| an editor-workspace skill, **two copies**, 127 lines each, apparently identical | **confirmed.** Two copies, both 127 lines, and the carrier's text byte-identical between them |
| a browser-through-a-borrowed-egress skill, **two copies**, 47 and 48 lines | **one copy.** 47 lines, in one project, added in one commit — and no other project's history carries the path, nor any file anywhere else built on the mechanism it needs |

Only the count produced the second row, which is why the count is a property of the class at
[`schema.md
§ 36`](../plugins/mjolnir/config/schema.md#36-a-skill-that-is-no-leg-of-the-loop-and-why-none-is-carried-here)
rather than a step somebody remembers. A line figure reads like a measurement, and one of the two
figures claimed for the second skill is right.

### Identical in the carrier, diverged in the script beside it

The confirmed pair had diverged in the script the carrier calls, not in the carrier, whose text
matches byte for byte. One copy's anchor was widened to tolerate the attributes the editor appends
to a configuration's opening tag — `singleton`, `temporary`, `nameIsGenerated` — and the other copy
never got it, so a block the editor had touched reads there as a template that is not in the file.
The fix is a few tokens in a regular expression, invisible in a listing, and the copy that lacks it
fails by reporting the argument as wrong.

### Why the counts did not decide it, which is the whole of the finding

The two candidates land on opposite sides of the de-duplication test and get the same answer, which
retires the test as an admission rule, at [`schema.md § 36 → Why a utility has no
home`](../plugins/mjolnir/config/schema.md#why-a-utility-has-no-home-on-this-surface-from-either-direction):

| | the de-duplication test | the per-project values in it | the answer |
|---|---|---|---|
| the editor-workspace skill | **passed.** Two copies, measurably diverged, and nothing in the procedure belonging to any one project | **none.** The file's path, the block to copy and the entry point are arguments of the pass | not carried |
| the browser skill | **failed.** One copy, so nothing to reconcile | an egress machine, a port, a target site, a browser's own path | not carried |

So the first one is the instructive case: the de-duplication properties find a candidate, and
[`schema.md
§ 36`](../plugins/mjolnir/config/schema.md#36-a-skill-that-is-no-leg-of-the-loop-and-why-none-is-carried-here)
makes the loop what admits one. The editor skill has nothing per-project in it, so there is no
configuration for this toolkit to carry, and what would be shared is a file. For the browser skill,
a name for a command each project writes would have satisfied the boundary and delivered nothing,
which [`schema.md § 36 → Why a utility has no
home`](../plugins/mjolnir/config/schema.md#why-a-utility-has-no-home-on-this-surface-from-either-direction)
forecloses. Length did not decide it either: the skill with nothing per-project in it is the longer,
127 lines against 47.

## The one role whose subject is several projects

One project holds a skill that builds a client's invoice for a period from that period's hours and
deliverables and renders it with every value checked, and it covers more than one client — so it
reads other projects' outputs. It is the only role surveyed with that shape.

### Why it reads as not belonging, which is the position that had to be overridden

Every other role narrows to one project, and the narrowing is how the surface is organised:

| what a role reads | what scopes it |
|---|---|
| the code root, the tracker, the host | § 1's skills root, resolved in the directory the role was invoked in |
| the evidence a day is measured from | the same root, and the day log states outright that this project's evidence is the **only** input |
| the audience each artifact is written for | § 8's per-artifact triple, stated by that project |

The local answer is strong: the invoice is one project's skill that happens to aggregate, has one
copy, and leaving it there asks no project for a key and keeps a rate and a client's name out of
the repository.

What overrides it is the role list, at
[`schema.md § The loop`](../plugins/mjolnir/config/schema.md#the-loop) and read as [`schema.md
§ 36`](../plugins/mjolnir/config/schema.md#36-a-skill-that-is-no-leg-of-the-loop-and-why-none-is-carried-here)
reads it. The role was already named apart on it, and the list is what admits a skill; leaving this
one out would reopen both rulings. A utility that read two projects would still be refused; this
role is admitted because the route needs a leg there, not for how many projects it reads.

### What made the extraction possible, measured rather than assumed

The seam is a port — [`schema.md
§ 26`](../plugins/mjolnir/config/schema.md#26-the-day-logs-destination-port), and the operation
list at [`schema.md § 26 → The destination's
operations`](../plugins/mjolnir/config/schema.md#the-destinations-operations-and-what-each-absence-does).
Without it a cross-project consumer would compose a directory per project and read files out of it,
a second resolver of somebody else's configuration:

| what the consumer needs | what answers it | what it would have been without the port |
|---|---|---|
| a period's hours, per project | `read_hours` against that project's own configuration | a directory joined onto a root, and a filename convention between two roles |
| which day each figure came from | the operation's own per-day answer | a sum, with nothing behind any figure |
| that a day could not be read | named in the answer, apart from the hours | indistinguishable from a day nobody worked |

The per-day answer, ruled so that a consumer can tell a short period from a partly read one, is
what the traceability rests on: a line item naming a root and a day names the entry and the run
that wrote it, the grain being one entry per day per project — so no provenance field is added to
an entry.

### The two values that may not enter the toolkit, and the mark that was already there

A rate and a client's identity are held by [`schema.md § 37 → The
rate`](../plugins/mjolnir/config/schema.md#the-rate-and-what-this-surface-holds-about-a-client),
resolved through [`schema.md
§ 28`](../plugins/mjolnir/config/schema.md#28-a-configured-value-a-repository-may-not-hold).
The destination port states that hours, rates and a client's identity reach no key of it; the one
key it marks is the spreadsheet kind's identifier, which names a store and is none of those.

| the value | where it is stated | where the value lives |
|---|---|---|
| which projects a period spans | `billing.projects`, in the tracked file | the same file — a path is not a client |
| the rate per client | `billing.rates`, marked `# private` | the untracked file § 28 points at |
| which client a period is for | **nowhere.** No key names one | the invocation |

No role reads the client to decide what to do next, so it is told rather than configured.

### What a marked value costs the role that needs it, measured on this one

The second row above is unreadable by the role it exists for, which is the mark working —
[`schema.md
§ 28`](../plugins/mjolnir/config/schema.md#28-a-configured-value-a-repository-may-not-hold): the
reader's report replaces such a value with a marker. A run against a project whose `private.keys`
names `billing.rates` printed `rates: "<private: private.source>"`, while `Config.billing` over the
same project resolved the real mapping. A role that reads the key and may not parse the file has no
route to a rate.

So the value is read inside a process, per [`schema.md § 28 → The
pointer`](../plugins/mjolnir/config/schema.md#28-a-configured-value-a-repository-may-not-hold): a
role that needs one names the key and runs the carrier that resolves it.
[`day_log.py`](../plugins/mjolnir/scripts/day_log.py) reads `day_log.attribute_to` that way, and
[`billing.py`](../plugins/mjolnir/scripts/billing.py) reads the rate that way, with outputs whose
difference is its contract:

| what it emits | what it carries | why there |
|---|---|---|
| its own standard output, which the role reads | the period's unpriced half — roots, days, hours, what could not be read | a role's output is a session transcript, which § 28's values may not reach |
| the artifact, at the destination the invocation names | the rate, the money, and the client | the one output a rate is owed to, being what whoever pays reads |
| each root's own answer, where `--answers-dir` names | that root's port answer, one file per root | § 11's ingestion step is run **per root**, and one pass over the concatenation reports one verdict for every store |

The carrier reads another project's store, so it runs the ingestion step and stops on a directive
found in one; a pass running it afterwards would examine a period whose artifact was already
written.

### The row the port cannot answer, found by running the chain

Each root's answer is stated at [`schema.md § 37 → What the list
names`](../plugins/mjolnir/config/schema.md#what-the-list-names-and-what-resolves-each-entry).
Each arm below was driven against what its row describes. Only the second is § 26's stated
fallback; the first is § 1's reader refusing and the third is a capability working and its call
failing:

| the root | what asking its store for a period returned |
|---|---|
| no configuration under it | the reader refuses, naming the file it looked for |
| `destination.kind: none` | `performed: false`, carrying § 26's stated fallback — the consumer has no answer and stops |
| an address occupied by something that is not a store | `failed: true`, naming the address — the capability working and the call failing |
| a store nobody has written to yet | **performed**, with nothing in it — which is the answer, and must not stop the period |

The empty store is the green side, and the unreachable one cannot be collapsed into it — [`schema.md
§ 26 → The destination's
operations`](../plugins/mjolnir/config/schema.md#the-destinations-operations-and-what-each-absence-does),
which separates a failed call from an empty answer. Each row is named by its subject, never by its
position, since an ordinal breaks silently when a row is added.

A project mapping no `day_log` carrier still answers: § 26's `kind` defaults to `file`, so it
addresses a store, and asking it comes back performed with nothing in it — indistinguishable from
the store nobody has written to. So the carrier is read from § 7's block before the store is asked.

`rates` is the first `# private` key whose shape is a **mapping** — [`schema.md
§ 28`](../plugins/mjolnir/config/schema.md#28-a-configured-value-a-repository-may-not-hold),
[`schema.md § The file itself`](../plugins/mjolnir/config/schema.md#the-file-itself). The setup
role's router reads a bare value, a list and a mapping, both halves of each entry, because a
client's name is as much the value as the rate beside it.

## The document checks: two implementations, and the claim measured rather than taken

One project holds its documents to a declared reference graph and another classifies the checks
themselves, and the item asking for the extraction carried both as line figures — 489 and roughly
2,400. Both were counted, as
[`schema.md § 36`](../plugins/mjolnir/config/schema.md#36-a-skill-that-is-no-leg-of-the-loop-and-why-none-is-carried-here)
requires:

| what was claimed | what the count says |
|---|---|
| a reference-graph implementation, **489 lines** | **confirmed.** 503 lines today, one project, reading its graph out of the rules file that governs its documents |
| a check-classifying implementation, **roughly 2,400 lines** | **confirmed.** 2,194 lines, a different project, 140 references to markdown files in it |

The second is a shell script, so sweeps over `*.py` named like a check miss it; the largest such
candidate, 1,047 lines in a third project, is not a document check at all. It was found by asking
which sizeable script names more than one markdown file. The three kinds, the discipline and the
reading rule the item quoted are in that script's own header, word for word, not a paraphrase
carrying this repository's own rule.

### The admission question, which had to be answered before any of it was built

The closed list at [`schema.md § The loop`](../plugins/mjolnir/config/schema.md#the-loop) admits
**roles** and says nothing about a facet, as
[`schema.md § 36`](../plugins/mjolnir/config/schema.md#36-a-skill-that-is-no-leg-of-the-loop-and-why-none-is-carried-here)
states. Five sections already carry per-project facts whose only consumer is a check or a hook, and
none is on that list, so
[`schema.md § 38`](../plugins/mjolnir/config/schema.md#38-the-documents-a-project-holds-to-a-checkable-property)
is carried on § 34's reason: the per-project values arrive already written as data. The item's
framing as a role is refused rather than honoured: nothing is added to the loop, no `carriers` key
answers for this, and no role enters it.

### One root is false for a set whose members are addressed by name

The implementation this property came from holds reachability from a single document. That is
false of this repository: each role carrier is loaded by name by the harness and named by no
document, so a single-root reading reports every one unreachable, which is why
[`schema.md § 38 → The two edges`](../plugins/mjolnir/config/schema.md#the-two-edges-and-which-of-them-is-enforced)
states a list of entry points. No count is written for it, since it is the length of the carrier
directory and changes with the loop. A project that states every document an entry point has
turned the check off and can read that off its own configuration.

### The first real run reported a correct document as broken

The check's first pass over this repository's documents produced one failure, and the assertion
was what was wrong — the reading
[`schema.md § 38 → What a red says`](../plugins/mjolnir/config/schema.md#what-a-red-says-and-what-stays-in-a-projects-own-script)
exists to force. A cell carrying `` `high \| medium \| low` `` was reported as a row with two cells
too many: the pipes are escaped, the document renders as written, and the count was of the raw
character. The source implementation has the same defect. A pipe after a literal doubled backslash
*is* a delimiter, which a look-back implementation gets wrong and a consuming one gets right.

### Three plants that certified nothing, each found by disabling the mechanism

Every arm was verified by breaking the thing it names and watching the suite redden —
[`schema.md § 38 → Every check carries a violation`](../plugins/mjolnir/config/schema.md#every-check-carries-a-violation-it-reddens-on)
states. Three plants did not survive it:

| the plant | why it certified nothing |
|---|---|
| a fence delimiter shown inside another fence | the block held only the two delimiters, so with the matching rule disabled the outer fence closed early, the inner one opened and closed, and nothing was left for any check to see. It now carries a ragged table, which is what the matching rule decides |
| a tilde fence that closes | the same shape: inert prose inside it stays green whether the delimiter is recognised or not |
| a path that is not a governed document | written as a bare path in backticks, it was reachable only by the loop over documents already known, so no mutation of the edge reader could have reddened it. It is a **link** now, which is resolved and then tested against the governed set |

One plant is kept with its limit written down. The smallest legitimate table — one row and its
delimiter — is decided by the delimiter counts agreeing and not by the run-length guard beside it,
measured by widening that guard and watching the plant stay green. The guard's own
subject is a *lone* line of pipes, whose red belongs to the block check and is planted there.

The reader had five plants sharing one refusal: absence, a container and a blank value had been one
branch, so the suite asserted one arm three times and reported two it had never exercised. The
branches are split, and every one of the facet's thirty-eight planted violations names its own.

### A ban fails the document that states it

A forbidding entry with no scope holds every governed document, including the one that defines the
ban, which has to name the banned thing to define it. So
[`schema.md § 38 → Which documents a forbidding entry holds`](../plugins/mjolnir/config/schema.md#which-documents-a-forbidding-entry-holds)
lets an entry narrow itself with `covers` and take documents out with `exempt`, each exemption
carrying its reason. Both keys are omitted rather than defaulted to an empty list: the absent key
keeps the unscoped meaning, while an empty list would read as a decision and hold nothing, the
state the facet's `graph: []` refusal exists against.

A scope glob matching nothing is reported by the check rather than refused by the reader, because
the reader opens no tree: it holds the shape, and the check, which reads the governed set, holds
the match. An exemption is judged against what its entry would otherwise hold rather than against
the whole governed set, because an exempt glob that only matches documents `covers` already leaves
out reads as an exemption doing its job and does nothing.

### What the facet cannot express, measured on the project it came from

The classifying implementation runs twenty-five check groups and this facet expresses four kinds of
thing: the governed set, the graph, the forbidden names and a document's own blocks. Most of the
rest are computed properties of that project's subject matter — whether its five request shapes
each have a home in its layout, whether its predicate vocabulary's width is stated where the
extraction stage holds it — and
[`schema.md § 38 → What a red says`](../plugins/mjolnir/config/schema.md#what-a-red-says-and-what-stays-in-a-projects-own-script)
leaves every one in that project's own script. A key pointing at a command that answers such a
question would satisfy the boundary's letter and leave the project writing the whole procedure.

### Both projects' rules, expressed in the facet and run against their own trees

Each project's rules were written as a `documents` block in a temp skills root — neither repository
touched — read by the shipped reader and run by the shipped carrier over that project's own index.
Two keys of
[`schema.md § 38 → The two edges`](../plugins/mjolnir/config/schema.md#the-two-edges-and-which-of-them-is-enforced)
come from that run:

| what the drive found | what it cost |
|---|---|
| **Thirty of one project's declared edges read as dropped.** It names each of its eight role carriers by that carrier's **slug** and never by its filename, with a per-node pattern for every other document besides | `named_as`, a row's own spelling, with the path as the default and a link resolving either way. With it, thirty failures became none |
| **The other project declares no reference graph at all.** Under two states its only options were to list every edge its text happens to carry — turning on a graph it never asked for — or to be red for ever | a third state, `may_name: null`. Warned about rather than refused: a project in that position is a legitimate configuration, so the run names the rows it does not enforce and says which three checks hold nothing, which is the shape the quoting kind already had |

The graph-less project came back green on every check — its governed set, all seven of its
forbidden names, and all three block properties, over its own six documents. The graph project
came back with five, none a defect in that project:

| the five | what each is |
|---|---|
| three edges out of its root file | cells of the **derivation table** it keeps inside that document. The facet moves that record into configuration, so under § 38 those rows are not in the document at all — the exclusion that project's own checker needs is made unnecessary rather than expressed |
| two mentions of its root file | a per-**citer** exception: inside its two documents about a client's repository, the root file counts only in the one form that cannot mean anything else. **The facet does not express this** — two of that project's fifty-five edges, in one project, and a key for it would be a map per row carrying a pattern per citing document |

That project's own gate is green, so each difference is this facet's shape and not its prose.

## The specification corpus: a block of three keys, one of which was already carried

The item asking for this wrote the shape it wanted, and one of its three keys is a second record of
a fact the surface already carries:

| what the item asked for | what the surface already says |
|---|---|
| `root`, a path the corpus hangs under | **no root.** § 38 states its governed set as glob lists against repository-relative paths and carries none, so a `root` beside globs would make every glob relative to a second thing — and the two spellings of one path would be free to disagree. The item notices the absence and still asks for the key |
| `load_bearing`, the part read whole | **carried as asked**, with `[]` legitimate and the corpus's own list refused empty — § 38's division between a marker's question and a shape rule's |
| `ref_for_version`, how a version names a ref | **already there.** [`schema.md § 4.8`](../plugins/mjolnir/config/schema.md#48-grouping--what-a-set-of-items-is-planned-into)'s `ref_prefix` is a ref named after a grouping's own value, and [`schema.md § 5`](../plugins/mjolnir/config/schema.md#5-readiness-gate--an-ordered-predicate-list)'s `grouping_ref_exists` already composes it. A key here would be two records of one branch-naming scheme |

So the facet carries a carrier, two glob lists and one key naming which of § 4.8's groupings the
corpus hangs off —
[`schema.md § 39 → The ref is the grouping's`](../plugins/mjolnir/config/schema.md#the-ref-is-the-groupings-and-this-facet-declares-none).
It is a rule of the reader rather than a marked condition, because its requiredness turns on how
many groupings a project carries, which is `work_item.code_root`'s reason for the same choice.

### The obvious rule about `kind` is refused by a shipped example

Refusing every grouping whose `kind` is not `version` would refuse this repository's own cheapest
example, which names its releases with the tracker's milestones and cuts a branch per release, so
`kind` is `milestone` and a ref is named after it. `kind` says what a grouping is to the plan and
`ref_prefix` says that a ref carries its value; this facet needs only the second —
[`schema.md § 39 → The ref is the grouping's`](../plugins/mjolnir/config/schema.md#the-ref-is-the-groupings-and-this-facet-declares-none).
What not reading `kind` gives up: a `ref_prefix` on a time box gets the corpus read at
an iteration's branch and nothing refuses it.

### Three outcomes, and the third was found by building the read

The item names two — the version's own ref, and the fallback where that branch does not exist yet.
The third is a branch on the remote and not in this clone, so there is no object to read;
[`schema.md § 39 → The fallback`](../plugins/mjolnir/config/schema.md#the-fallback-is-correct-and-it-is-the-one-thing-here-that-must-be-said-out-loud)
keeps it apart from the fallback.

| the outcome | what it means | the wrong answer it is not |
|---|---|---|
| the version's ref resolved | the copy that governs | — |
| the branch does not exist | the integration branch was read instead. Correct, and reported on every run that takes it | a verdict about the governing copy |
| the branch is on the remote and not in this clone | **nothing was read** | the fallback. Folding the two would read the governing copy's absence from a clone as the version's absence from the project |

The read reaches the remote for one question and opens objects only out of the clone, so a version
nobody has fetched is reported unread with the one command that would fetch it — fetching is the
role's call, not the carrier's.

### The negative is asserted, and one arm's first form reported the right colour

"Nothing is checked out" is asserted: the branch, the head, the porcelain status and a corpus
file's own uncommitted text are digested before and after a read taken from a third branch with a
dirty tree, and compared. The read takes the version's copy and not the uncommitted one, which is
what
[`schema.md § 39 → Which copy governs`](../plugins/mjolnir/config/schema.md#which-copy-governs-and-why-the-working-tree-is-never-it)
is for.

On a dirty tree git refuses a plain `git checkout` that would overwrite the local change, so a
planted plain checkout stays green there and only a forcing one is caught; a plant nobody forced
certified nothing. So the negative is asserted on the dirty tree and on a clean one, where a plain
checkout succeeds, and the suite asserts that the clean tree really was clean.

### A bare-revision candidate was two of the defects the facet exists against

The reading resolves two candidates and no third: the remote-tracking ref and the local branch —
what
[`schema.md § 39 → The ref is the grouping's`](../plugins/mjolnir/config/schema.md#the-ref-is-the-groupings-and-this-facet-declares-none)
means by a ref composed from a prefix. The composed name as a bare revision would be a third
candidate, and two defects:

| what the third candidate admitted | what it would have reported |
|---|---|
| a **tag** of the composed name | *at the version* — while the arm that decides the unread outcome reads the remote's **heads** only, so the same name is simultaneously *there* and *not advertised*. The two answers § 39 keeps apart, reached through a candidate nothing on the surface asks for |
| a `ref_prefix` leaving the composed name a revision expression | the working tree's own commit, read as the version's copy — the one thing the facet is for |

An arm reproduces it: a tag named with the facet's own prefix, at the version's commit, with no
branch of that name, which reddens if the candidate is put back. A branch is what the facet
composes throughout, as § 4.8's `ref_prefix` means — `grouping_ref_exists` looks for it among the
remote's heads.

### The claim about contradictions covers every outcome, not the arms that mentioned it

No outcome carries a verdict about whether the request contradicts the corpus, that reading being
the filing role's by
[`schema.md § 39 → the absent case`](../plugins/mjolnir/config/schema.md#carrier-none-and-the-two-answers-it-must-not-collapse-into-one).
The suite collects every answer it takes and makes the claim once over the set, with the reached
set asserted beside it, since a collector nothing fed would make the claim vacuously true.

The grouping rule asks its question of the resolved set, not the raw `work_item.grouping` block:
a grouping whose carrier is `none` is still written there, § 4.8's rules drop it, and asking the
raw block refused a project planning in no grouping for stating no `ref_prefix` — the right colour
under the wrong key, and a plant certifying the wrong arm. The rule sits beside § 5's, in the one
function that produces the resolved set, rather than with the facet's own glob arms.

### The roles that hold the item read it too, where the project says so

One adopter loads its version's specification at start and again while implementing. The answer is
a list of roles and not a second read: `while_working.roles` names which of the starting and
implementing roles run the same command, at the same ref, for the item they hold —
[`schema.md § 39 → The roles that read it while the work is done`](../plugins/mjolnir/config/schema.md#the-roles-that-read-it-while-the-work-is-done-and-what-narrows-their-read).

| what was weighed | what the surface says, and why |
|---|---|
| reading at every leg wherever a corpus is carried | **opted into instead.** Every project carrying a corpus today would start paying for it in the window on every item, and a corpus written for filing decisions is not necessarily one the work is held to. A project that states nothing reads at filing alone |
| the filing role as a value of the list | **refused.** It reads wherever a corpus is carried, so the entry would be a key that changes nothing |
| a size cap on what is loaded | **refused, in favour of a glob list.** A truncated specification is the wrong copy one step further on, which is the carrier's own reason for capping nothing; `while_working.files` lets the project say what is loaded |
| a narrowing list read as a corpus of its own | **an intersection instead.** A document is loaded only where both lists match it, so a glob reaching outside `files` cannot widen the read |
| an item carrying no version falling back | **a stop.** The fallback is for a version with no branch; an item naming no version has no governing copy to decide, and reading the integration branch for it would read as the version's own |

The two roles add a statement the filing role never needed: *this project does not have this role
read its corpus*. It is neither the absent subject nor a verdict, and the carrier prints it in its
own words so that a role asked to read nothing cannot report that nothing contradicts the item.

## The role that writes a specification: two implementations, and the half already carried

A role that turns raw source material into a specification and then into work items was named as
missed by the survey that produced the loop's roles, with two independent implementations behind
the claim. Both exist, and the count behind the word *two* is the first thing that moves: one is a
project's own skill and the other is the [public plugin cited as prior art](#prior-art), so across
the six projects here there has only ever been one copy of this role.

| what was claimed | what the count says |
|---|---|
| a project skill turning sources into a requirements document, a screens-and-components breakdown and a cross-session task list | **confirmed, and one copy.** 95 lines, in one project. Every skill and command directory across the six holds no second one, and no other project's history carries the path. The sweep was keyed on the path and not on the mechanism, so a copy under a wholly unrelated name is outside what it covered — the step [the earlier count](#the-counts-and-the-one-of-the-two-that-has-only-ever-had-one-copy) did take and this one did not |
| a superseded plugin carrying it as five skills plus a brainstorm front end | **confirmed.** Six carriers, 902 lines — 337, 195, 143, 114, 63 and 50 — in a third-party repository, not in any project here |

The one copy has had two carriers and never two copies: first a slash command, now a skill. That
is [§ 7](../plugins/mjolnir/config/schema.md#7-carrier)'s axis moving under a
role that stayed put, and why a sweep keyed on either carrier alone reports a different number
from a sweep keyed on the role.

### The adopting project drew the seam itself, in its own migration

On 2026-11-19 the project holding the role moved its development process onto this toolkit, and
that commit made six insertions and six deletions in the 95-line file, leaving it 95 lines:

| what changed, over six lines | what it means |
|---|---|
| **four lines** naming that project's own former role carriers now name this toolkit's starting and finishing roles — five references, one line carrying two | the legs this toolkit carries are called rather than reimplemented |
| **one line** where *per that role's rules* became *which is `work_item.grouping.sprint` in the configuration*. The tracker field identifier beside it is unchanged — what moved is where its value is stated, not the value | the per-project fact is read from the one file rather than depending on another role's text |
| **one line** where *follow that role's steps 4–5 verbatim* became a pointer at `branch_model.tree_dir` and that project's own tree-mechanics file | the migration removed the instruction to follow another role's steps and replaced it with a key |

Nothing moved out of the file. An adopter mid-migration kept the document-writing local and rewired
the three things it wanted from the loop into calls and keys.

### What the overlap is, measured against the roles that have landed

The item claimed that *roughly half* of that skill is already the filing and starting roles.
Measured, the overlap is the whole of what it names: creating the item, a duplicate search of two
or more keyword passes over summary and description in both languages with no status filter, and
the branch cut in its own tree. All three are the filing role's duplicate check and the starting
role's claim, both landed. As a share of the file it is 9 lines of 95 — one step of eight, two
rules, and one phrase of the closing report.

### The two residues do not meet

With the overlap removed, what is left of each implementation is disjoint from the other: two
procedures that share a sentence of description.

| | the project skill | the plugin |
|---|---|---|
| where the content comes from | provided artifacts, distilled | the person, interviewed question by question |
| what it writes | three documents per feature, in a per-feature numbered directory | four documents per project, plus one file per entry in a flat tree |
| what it validates | each document against the sources, in both directions | each document against the others, for consistency |
| where the items go | a tracker, through this toolkit's own roles | a file per entry, or one of that plugin's own tracker adapters |

Reconciling them would mean adopting one and configuring the other away — a copy with a
configuration wrapper, the shape
[`schema.md § 36`](../plugins/mjolnir/config/schema.md#why-a-utility-has-no-home-on-this-surface-from-either-direction)
refuses from both ends.

The plugin's residue is mostly its own machinery. 126 of its principal skill's 337 lines are about
a specification at all — its six numbered steps; the other 211 are its layout and tracker-mode
probes, resolver entry, creation path, commit gate, closing-summary token contract, helper modules,
refusal shapes and approval-marker protocol. Even inside the 126, the milestone-identity guard and
the branch gate are its own.

### The part with nothing per-project in it

Three rules generalise, all about the *source* rather than the document. They are stated at
[`schema.md § 11`](../plugins/mjolnir/config/schema.md#what-a-source-establishes-and-the-hole-a-distillation-reads-over),
and come from one of the two implementations: the project skill carries them as a pass its own
text calls mandatory, and the plugin carries no source-validation step — it interviews a person, so
there is no export to parse and no referenced artifact to look for.

Their per-project values are none, which
[`schema.md § 36`](../plugins/mjolnir/config/schema.md#why-a-utility-has-no-home-on-this-surface-from-either-direction)
makes the sign that a shared file is wanted — except that these are not a utility: the filing role
already reads a request somebody else wrote and distils it into an item, so the leg that owes them
exists. They ship as procedure on that leg.

### What the dependent project holds, which is what *dropped* has to be true of

The project that depended on the superseded plugin keeps its specification in that plugin's layout:

| what it holds | the count |
|---|---|
| top-level specification | **870 lines** across three documents — 107, 621 and 142 |
| active entries | 6 files, 411 lines |
| archived entries | 12 files, 1,039 lines |
| the active plan, and the finished ones | 1 file of 44 lines, and 2 of 192 |

None of that depends on this toolkit authoring it. The entries move onto a real tracker and the
documents stay documents under that project's own migration item, and the two things that bear on
such a corpus are both carried: what *holds* it is
[§ 38](../plugins/mjolnir/config/schema.md#38-the-documents-a-project-holds-to-a-checkable-property),
and which *copy* of it governs a given item is
[the corpus facet](#the-specification-corpus-a-block-of-three-keys-one-of-which-was-already-carried)
the filing role reads. What is dropped is the authoring.

The filing role reads a specification corpus it did not author, at the ref the item's grouping
names
([`schema.md § 39`](../plugins/mjolnir/config/schema.md#39-the-specification-corpus-and-which-copy-of-it-governs))
— so what a spec-writing leg would produce is already consumed by a leg that never needed one. A
project carrying no corpus files its items unchanged — that facet's absent case, and the test a
leg of [§ The loop](../plugins/mjolnir/config/schema.md#the-loop) has to pass.

## The ordering record: the leg the route consumed and no leg produced

The closing-out role is this repository's own prototype promoted, and it is the one candidate so
far admitted to [`schema.md § The loop`](../plugins/mjolnir/config/schema.md#the-loop)'s closed
list rather than ruled a facet, on the test
[`schema.md § 36`](../plugins/mjolnir/config/schema.md#36-a-skill-that-is-no-leg-of-the-loop-and-why-none-is-carried-here)
states.

| what the list's test asks | the answer for this candidate |
|---|---|
| does the **route** need a leg here? | **yes, and the gap is readable off the surface.** [`§ 12`](../plugins/mjolnir/config/schema.md#12-ordering) is read by the starting role to decide which item to offer, and no leg of the route wrote one. A route that consumes an ordering and never maintains it reads a stale answer on its first act |
| is the reason statable, and the same one every time? | **yes**: it is the leg after a batch lands, the same way filing is the leg before a gate. It is not *this thing has several copies* — the candidate has exactly one copy, in this repository |
| would a facet and a check do instead? | **no.** The pass makes **writes** that are judgement — which item goes where in an order — and § 38's own argument is that what a facet carries is a graph, a file set or a list that arrives already written as data. An order of work does not: nothing derives it |

The facet it needed came with it: what a project differs on is *where the order is kept*, and
that is [`schema.md § 40`](../plugins/mjolnir/config/schema.md#40-the-record-a-projects-ordering-is-kept-in-and-what-brings-one-into-existence)
— a role on the list, with one block of configuration under it.

The de-duplication test is silent here. One copy is what ruled the browser skill out two sections
up, and this candidate has one copy as well; the scope is what decides, as § 36 states.

### What the prototype hardcoded, which is the facet

The prototype is 604 lines of implementation under a 203-line carrier, tracked in this repository's
own skills root — so already under the strictest naming rule here and free of a project's name. It
was not free of this project's own *shape*, and the four values it composed are what the facet had
to answer:

| what the prototype held | what it is now |
|---|---|
| a filename glob for the ordering document | `ordering.record.document` — **one** document and not a glob. The glob was there because the prototype could not be told the name, and it carried a refusal for *several matched* that the key makes unreachable |
| the directory, composed from a home directory and the working tree's own path | `ordering.record.dir`, marked `# private`. The composition was a second implementation of the harness's own rule, which is exactly what [`§ 25`](../plugins/mjolnir/config/schema.md#the-carriers-and-what-each-of-them-closes) forbids a role to do about the memory store |
| the baseline's filename, beside the document | **procedure, and deliberately not a key.** A key would let a project point the record and its baseline at different places, which reads as a pass that found no drift. Its *directory* is `ordering.record.dir`, which is why that key is required under the grouping carrier too — the baseline needs a place to stand whichever carrier the record is on |
| the row table's grammar — an integer label places, a non-integer retires | **procedure, and the `document` carrier's.** A project that could reword it is a project whose ordering the shared role cannot read, which is the whole of what the carrier is for |

The tiers an ordering may carry already came out of
[`§ 4.6`](../plugins/mjolnir/config/schema.md#46-priority) through the shipped reader rather than a
constant, so that is not a key of this facet. The three that are deliberately not keys are stated
together at
[`§ 40 → The one directory`](../plugins/mjolnir/config/schema.md#the-one-directory-why-it-is-marked-and-what-is-not-a-key-here).

### The second carrier came from the trackers rather than from this project

This repository runs on plain issues with no board, so the only carrier it can measure is a
document, and a facet read off it alone would have shipped a path key — the reading
[`§ 40 → The two carriers`](../plugins/mjolnir/config/schema.md#the-two-carriers-and-the-one-thing-neither-of-them-is)
refuses. The grouping carrier is read off
[`§ 4.8`](../plugins/mjolnir/config/schema.md#48-grouping--what-a-set-of-items-is-planned-into)'s own
survey: one measured tracker holds a time box and a release scope as two fields, and the order of
work is kept in the first of them.

That is why the record's `grouping` key is a *name* and not a flag. A project carrying two
groupings has one it orders work in and one it does not, so a carrier word alone would leave the
role choosing, invisibly on the item.

A third measured shape is carried by neither carrier
([`§ 40 → The two carriers`](../plugins/mjolnir/config/schema.md#the-two-carriers-and-the-one-thing-neither-of-them-is)).
One surveyed board's order is the position of a card in a list, written by whoever drags it:
neither a grouping nor a document, and nothing here reads or writes it. That project states
`ordering.carrier: command` with `ordering.record.carrier: none` — the one combination that shows the
two keys are different questions — and the shipped Trello example is written that way.

### Why `derived` is not one of the carriers, measured against the store that has it

[`§ 25`](../plugins/mjolnir/config/schema.md#25-the-memory-store-and-the-tree-a-save-may-refresh-it-from)
carries a `derived` carrier for the memory store and this facet carries none. Under `derived` the
procedure composes no path and resolves nothing inside the store, and the memory facet survives
that because the harness itself does the reading. There is no second reader here: the closing-out
role has to open the document, so a derived carrier would state a store the role may not look
inside — and the prototype's answer to that was to guess the harness's layout, which is the defect.

### The private layer's absence is not a load-time refusal, measured

[`§ 28`](../plugins/mjolnir/config/schema.md#28-a-configured-value-a-repository-may-not-hold) states
that a `source` which does not open is refused, which might read as a clone without the untracked
file being unable to read its configuration at all. Measured, it is not: with this project's
private file moved aside, the whole mirrored gate set returns the same verdict on every check as
with it in place, and the reader itself loads and prints. The layer is held at load time for its
*shape* — the pointer, the list, the marks, the collision with a tracked value — and the values are
resolved where they are read.

The refusal moves to the role: a closing-out pass run on a machine with no private layer is
refused with the key named, the one place the absence can be reported to somebody who can fix it.
This repository carried `private.carrier: none` while every value it held could be committed; an
ordering document's directory is the first value here for which that is false.

### The two operations the port did not state

The prototype reached the host directly — one client call for the repository and two GraphQL
queries — and two of those reads and one write had no operation on
[`§ 3`](../plugins/mjolnir/config/schema.md#the-operations-and-what-an-absent-capability-does)'s
closed list:

| what the pass needs | what answered it before | what answers it now |
|---|---|---|
| the open set and each item's tier | a GraphQL query over every issue | `search_items`, which already states both states and the fields |
| the whole relation graph | the same query's `blockedBy` edges | `read_blockers`, asked per item — the adapter is free to batch, and the **role** no longer names a tracker's word for the relation |
| the change that closed a landed item, and its commit | a second GraphQL query | **`read_closing_change`**, new: `link_for_close`'s own read after the fact |
| an ordering that does not exist yet, where it is a grouping | nothing — the prototype has no such arm | **`create_grouping`**, new: the one write about a grouping made before any item is in it, which is what [`§ 39 → An ordering that does not exist yet`](../plugins/mjolnir/config/schema.md#an-ordering-that-does-not-exist-yet-and-the-one-act-that-is-the-persons) makes the bootstrap on that carrier |

Neither new operation is implemented by every adapter
([`§ 3 → The operations`](../plugins/mjolnir/config/schema.md#the-operations-and-what-an-absent-capability-does)).
The closing-change read is implemented on both GitHub kinds, where an item *is* an issue on the
host that holds the change, and absent on the other two: a Trello card holds no reference to a
change in either direction, and what a Jira item shows is written by a code-host integration
somebody installed. The grouping create is implemented on plain issues alone, the milestone being
an object; everywhere else the grouping is a field's value, which nothing creates. The release mark
is not absent on that argument everywhere: where a Jira grouping's field holds versions, the value
names a version object, which `mark_grouping_released` marks by
[`schema.md § 3`](../plugins/mjolnir/config/schema.md#the-operations-and-what-an-absent-capability-does)'s
rule for it.

### The prototype's own rule the promotion kept, and the one it had to make general

The prototype already left no audit trail — its carrier says the ordering document states what is
true now and that everything about a pass goes in the reply — and
[`§ 40 → What a pass may not do`](../plugins/mjolnir/config/schema.md#what-a-pass-may-not-do-whatever-the-carrier)
states that rule on the surface. No gate reaches a document outside every tree, which is why the
rule is written there.

The residue rule had to become general. The prototype's statement about another session's
half-made edit is about *the plan file*, which has no lock; on the grouping carrier the same
situation is two sessions writing one tracker. So the surface states the act and not the file —
reported, never repaired, with whose it is named — and the baseline makes the report possible on
either carrier, no tracker bumping an item's own modification time when a relation changes.

## The stage between a deploy and a release, measured where there is no copy of it

This is the one role whose facet was derived from no shipped carrier:
[`schema.md § 41`](../plugins/mjolnir/config/schema.md#41-what-a-deployed-item-is-judged-against-and-the-readings-a-person-is-handed)
is the facet, and
[`schema.md § 41 → Its own role`](../plugins/mjolnir/config/schema.md#its-own-role-and-the-two-grounds-that-rule-it-apart-from-the-reviewing-one)
is the ruling that separates it from the reviewing one. It had exactly one artefact behind it.

| what was there | and what that costs |
|---|---|
| **A draft runbook for the stage, written against one consumer and held outside every tree.** Nothing loads it, no gate reads it, and no project's configuration points at it | the same cost two other carriers record one stage later: a document nothing holds is a document free to disagree with whatever the loop actually does, and nobody finds out |
| **One recorded run of it against that consumer's deployed target**, carrying a scenario count and, inside it, one tier **held** rather than run — a form submission there would have reached real recipients | a reading that is a **precondition** and not a verdict, which is why the facet makes a skip name itself rather than fold into a pass |

So each key answers a question one of the surface's existing sections leaves open —
[`schema.md § 41`](../plugins/mjolnir/config/schema.md#41-what-a-deployed-item-is-judged-against-and-the-readings-a-person-is-handed)
states all three, and
[`schema.md § 41 → The four buckets`](../plugins/mjolnir/config/schema.md#what-the-criteria-are-read-from-and-the-four-buckets-one-falls-in)
states what each criterion they are read for owes the record:

| the key | what already existed, and what it did not answer |
|---|---|
| `verify.identity` | [`schema.md § 33`](../plugins/mjolnir/config/schema.md#33-the-deploy-targets-and-what-reaching-one-invokes) states what a target **is** and what reaching it invokes. It states nothing about reading what a target is **serving**, which a judgement is about: the facet keys a command per target and holds the keys to that list |
| `verify.baseline` | [`§ 31`](../plugins/mjolnir/config/schema.md#31-test-tiers--what-each-one-needs-before-it-can-run-at-all) states what a tier needs before it can run. The before-and-after comparison is not a tier by that section's own test — it selects no set of cases — so its two inputs had nowhere to be stated |
| `verify.breakpoints` | Surface by the test that admits a facet at all: a **shared role** reads it to decide what to hand over. A project-local list would have left the one question a person is asked keyed on a value no role could reach |

### The two wrong readings of a deployed commit, and why neither is a key

Both are refused by the mechanism rather than by a setting —
[`schema.md § 41 → `identity``](../plugins/mjolnir/config/schema.md#identity-and-the-two-readings-of-a-deployed-commit-that-are-wrong).
The facet states one command per target and the role has nowhere else to read from:

| the reading | why it is wrong |
|---|---|
| an artefact's digest | a reproducible build yields the same artefact from a different commit, so an identical digest is **no evidence** that a deploy is current |
| the integration branch | it runs ahead of every target routinely, so a reading taken off it accepts code nobody deployed |
| an earlier note | two notes written the same afternoon can disagree, which is why the command is run in the pass rather than read out of a record |

### The writer bar turned out to be stronger than the facet assumed

Measured against the port: an accepting role asking as the status's own writer is not a way
through.
[`§ 4.2`](../plugins/mjolnir/config/schema.md#42-status--an-ordered-set-of-name-role-writer)
closes the set an ask may be made as to the procedure and the deploy, and the measured
configuration maps the `accepted` status to the person who ordered the work, so:

| the ask | what came back |
|---|---|
| as the procedure, or the deploy | refused against the configured writer |
| as the configured writer itself | refused **before the configuration is read at all**, as a claim to be somebody |

There is no writer the role could ask as, and the record it produces carries a standing rather than
a status word —
[`schema.md § 41 → What the role records`](../plugins/mjolnir/config/schema.md#what-the-role-records-and-what-it-may-not-record). The suite beside the carrier asserts both arms and the green side with
them — a role the procedure does write is not refused — so the four refusals are about this role
rather than about every move being barred.

## Whether the work is already built, a step three roles skipped

The filing role searched the tracker and never the code, and the starting and implementing roles
took an item's statement as still true. Two cases follow: an item whose work landed under another
item is started and built again, and a closed duplicate whose work was never built receives every
new request for that work, so the work drops out of every list. The gap was found by reading the
role texts, and nothing there was run.

- **Where the step runs is the project's choice, and running nowhere is the default**, at
  [`schema.md § 42 → The three points`](../plugins/mjolnir/config/schema.md#the-three-points-and-what-each-one-reads).
  Reading the code on every item costs something on every item. A project whose items are filed
  against the code as it stands has nothing to buy with it, and a default that ran everywhere would
  change every adopter's loop under it.
- **The finding is per bullet and a built bullet must cite something real**, at
  [`schema.md § 42 → The finding`](../plugins/mjolnir/config/schema.md#the-finding-and-what-it-has-to-carry).
  An item half built and an item not built read alike at the item level, and the failure the step
  exists against is a role that believes the work is done without being able to point at where. A
  bullet nobody could check is kept apart from one the code fails, because reading the first as the
  second is the confident wrong answer.
- **The step offers and never acts**, at
  [`schema.md § 42 → What a finding does`](../plugins/mjolnir/config/schema.md#what-a-finding-does-and-what-it-never-does).
  Whether the cited code answers a bullet is a judgement, and a judgement that closes items on its
  own is one nobody can audit afterwards. `on_finding` decides only whether the role stops to ask.
- **A closed duplicate with absent work is offered for reopening beside filing anew**, at
  [`schema.md § 42 → A closed item whose work is absent`](../plugins/mjolnir/config/schema.md#a-closed-item-whose-work-is-absent).
  Reopening keeps the item's history and filing anew starts clean. Neither is wrong in general, so
  the person chooses.
- **The carrier holds the shape and never reads the code**, at
  [`schema.md § 42 → The carrier`](../plugins/mjolnir/config/schema.md#the-carrier-and-what-it-holds).
  Which code answers a bullet is a reading only the role can take. What a script can hold is that
  every citation exists, that the verdict is derived rather than written, and that nothing was
  performed.
