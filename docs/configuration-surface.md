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

## The survey found nine roles, not eight

The loop's statement is [`schema.md § The loop`](../plugins/mjolnir/config/schema.md#the-loop--ten-roles),
and it now states ten — the tenth is the subsection below, which the survey found in every project's
tooling and in no project's implementation. What the survey established about the nine it could read
is the count: gating is a genuine ninth role rather than a variant.
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
project's habit. ⚠️ **Priority has since acquired a carrier of its own**
([`§ 4.6`](../plugins/mjolnir/config/schema.md#46-priority), below) **and the division is unchanged**
— the table is still one project's, which is the measurement that decided it rather than the absence
of anywhere to read a tier from.

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
rule and is read there rather than restated.

### The tenth role every copy named and none of them wrote

The role that **restores** a session's context is the counterpart of the one that persists it, and
the survey found it in a shape none of the other nine came in: named by the tooling of every project
that has any of this tooling, and implemented by none of them. The phrase a session is loaded with
sits in the excluded-turn list of **each day-log script the survey read** — the five of the six
projects that carry one — classified there as the tooling's own upkeep, exactly as the save it
mirrors is, so those scripts already deducted the minutes of a role no project had written down.
⚠️ **Which is also what settles whether it is work**: the classification is those
scripts', it predates the role being written, and
[`schema.md § 24`](../plugins/mjolnir/config/schema.md#24-session-restore--the-readings-a-pass-is-resumed-from)
changes nothing about it.

That is the strongest case for extracting a role there is, and it is also the weakest evidence base
of any role here, both of which are worth saying plainly:

| | |
|---|---|
| **Why it is a role** | Tooling in several projects names it, people invoke it, and it is performed from memory and differently every time. Its failure mode is quiet — a sweep that misses the unpushed commits, reports a cold environment as warm, or restates a stale recollection as current produces a confident and wrong picture of where the work is, which the next hour is then spent acting on |
| **Why its readings are procedure rather than configuration** | The thirds of the role it mirrors are configuration because the copies **diverged** — counted in [the section on that role](#the-bookkeeping-role-three-copies-that-are-a-third-of-it-and-two-keys-that-came-out-of-it) and nowhere else. Here there is nothing to diverge from, so a key stating which readings run would be a project's licence to switch one off — and a reading switched off reads exactly like a reading that found nothing, which is this role's whole failure mode |
| **What that leaves weaker than the nine** | Every other role here was reconciled from copies that could be read against each other. This one was derived from performing it, so the list of readings is one performer's habit written down and held by a carrier rather than a merge of five. The honest consequence is that it is likelier than its siblings to be missing a reading, and the place that shows up is a report that was confidently complete |

### The loop does not continue itself

Measured on this repository from the harness's own session records and the integration branch's
history, over a window stated closed because a day still running is a figure that grows after it is
written — 2026-10-19 UTC, 00:00 to 20:23: **sixteen changes landed, the finishing role was invoked
six times, and the reviewing role three.** Eight sessions invoked the starting role and five of
those went on to invoke the finishing one. One session is the clean instance — it implemented item
[#8](https://github.com/ragnor-rs/mjolnir/issues/8), landed it as `b9e8fd7` through pull request
[#147](https://github.com/ragnor-rs/mjolnir/pull/147), wrote its bookkeeping and asked what was
next, with the finishing role neither invoked nor its procedure read. ⚠️ **What that session had of
that role is worth being exact about**, since the weaker claim is the one that survives: its
frontmatter, read eight lines at a time while the session was authoring another role's frontmatter,
and eight scattered body lines returned by a `grep` across every skill. No read ever named the file,
and no invocation preamble for it was ever injected.

What the figures are evidence for is not that the roles are wrong but that **nothing carried the
item between them.** Each role's description was keyed on being asked; the route was stated in prose
that named no mechanism; and the leg from implemented work to an open change belonged to no role in
the pattern above, implementing being absent from the list this section's own opening cites. A
session that had just finished the work therefore had nothing instructing it to continue, and every
role it skipped was skipped silently.

⚠️ **A count of invocations is a floor, and the direction it errs in is against this argument rather
than for it.** It reads the harness's record of a *carrier* being invoked, so a session that opened
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

### Name and role diverge in both directions

One role under several names is the expected direction, and it happens: the bookkeeping role
appears under two names, deployment under four across five projects, and one project carries two
differently-named skills for filing and gating.

The reverse also happens, and a name-keyed merge produces nonsense on it:

- **One name, two unrelated roles.** The `deliverables` name is a prose session summary for a
  non-technical reader in one project, and a tab-separated invoice line-item file with an hourly
  rate conversion in two others. Same directory name, different output, different trigger, no
  shared procedure.
- **One name, a subset role.** A bookkeeping carrier can be the *commit third* of the role with
  the board and memory halves absent. Counting such a copy as a full one overstates adoption;
  counting it as unrelated loses that project's commit behaviour. ⚠️ **How many copies are whole
  and how many are a third is counted once**, in
  [the section on that role](#the-bookkeeping-role-three-copies-that-are-a-third-of-it-and-two-keys-that-came-out-of-it),
  and this passage carries no number of its own — the first version of it said *one project's* and
  the survey the role was extracted from found more.

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
[`schema.md § The loop`](../plugins/mjolnir/config/schema.md#the-loop--ten-roles) — which
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

   **A third facet landed inside the axis once the toolkit started generating workflow files, and
   it came from one project's runner account rather than from the survey.** One project in the
   migration set declares a non-default runner label on every job, because its host account
   carries its own runners — and a job asking for the host kind's default label on that account
   **never starts at all**. The consequence is the one that makes the fact load-bearing rather
   than cosmetic: a generated gate carrying the default is a check that never reports, replacing
   one that did, and a run that never reports is the absence-of-signal case this same section
   already refuses to read as green. So where the jobs run is stated, an installer writes it, and
   the statement is held to the workflow files —
   [`schema.md § 2 → Where the host's jobs run`](../plugins/mjolnir/config/schema.md#where-the-hosts-jobs-run).

   Two further measurements on the same account, both of which the obvious shape of the facet
   would have left out:

   - **Its runners take one job at a time, so a job's budget is spent queued.** A short check at
     the back of the line is cancelled having never started — no runner recorded, no step run —
     and the pull request then carries a conclusion indistinguishable from a failing check. That
     is why the capacity is on the surface beside the budget rather than left as a fact about a
     runner: at one job, `budget_minutes` is a queue budget, and a consumer that read the
     conclusion and stopped would send somebody to fix a diff over a queue.
   - **The number of jobs a workflow splits into is what decides how long the queue is.** Which
     prices, rather than overturns, this section's own ruling that each mirrored command takes a
     workflow of its own: the cost there was stated as a checkout per command, and on a
     single-runner account it is also a place in the line. ⚠️ The ruling stands — the alternative
     is still a configuration `checks` cannot state — and the price is now written down once
     instead of being rediscovered per project.

   ⚠️ **What the surface deliberately does not carry is the default itself.** A per-kind table of
   runner labels here would be a second statement of the host's own naming, wrong the next time
   the host changed one and wrong silently — the same argument that keeps the event vocabulary off
   this surface. The consequence is a stated limit rather than a hidden one: a project that writes
   no `host.runner` has nothing for the drift check to hold its files to, and that check says so
   rather than guessing.
3. **Code root.** One project's code is a git-ignored subdirectory that is its own repository
   under a different owner, not a submodule. Its skills write the root explicitly into every git
   call and stop if the directory is absent, because a fresh clone of the outer repository does
   not have it. The failure mode behind
   [`schema.md § 1`](../plugins/mjolnir/config/schema.md#1-roots):
   a skill that takes the top level of the repository it is installed in commits the engagement
   notes and never touches the code; a host CLI call inheriting the working directory addresses
   the wrong repository. Both fail quietly, having done something plausible first.

   ⚠️ **This survey read that root as one subdirectory, and the build survey counted two.** The
   same project carries two such repositories, each with its own host, its own checks and its own
   verdict set, which makes the grain of this axis per repository rather than per project —
   [`build-surface.md § A verdict is a command, a root, and a condition`](build-surface.md#a-verdict-is-a-command-a-root-and-a-condition)
   has the measurement and
   [`schema.md § 1 → A project's code is not always one repository`](../plugins/mjolnir/config/schema.md#a-projects-code-is-not-always-one-repository)
   is the shape it forced. Nothing above is overturned by it: the root is still configured rather
   than inferred, and still stated in every call. What changes is how many of them there are.

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
   - **The half that *deletes files* belonged to neither role, and it is the half that destroys
     data.** The merge is only one of the two moments a tree stops being wanted: a change merged in
     the host's web interface, in another session, or before any rule existed leaves a tree nothing
     is watching, and the trees then accumulate until somebody notices — the count is in
     [`schema.md § 10 → Pruning a tree whose branch has landed`](../plugins/mjolnir/config/schema.md#pruning-a-tree-whose-branch-has-landed),
     which is also where both carriers are stated and is not quoted back here. What is worth
     recording beside it is that **the measurements came from different projects and pointed at
     different halves of one rule** — what *landed* means, what makes a tree disposable, and how
     long a kept verdict is good for — which is why the subsection reads as four rules rather than
     one and why no single project's experience would have produced it.
   - **`regenerable` is the one key that half needs, and it is a key for the reason `claimed_by`
     is.** What a rebuild writes again is a build directory in one project, a dependency cache in
     another, a service stack's own volumes in a third — and a carrier shipping any of those names
     would be this toolkit carrying a project's value. ⚠️ What the empty form costs, and the
     exemption without which the rule would prune nothing at all, are stated with the key rather
     than explained twice.
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

⚠️ **`set_field` is newer than this survey, and the sentence above is bounded by that.** It arrived
with the gating role: of the two values that role writes, the estimate reaches the item as a label
on the copy measured, and the date
([`schema.md § 4.5`](../plugins/mjolnir/config/schema.md#45-due-date)) reaches it as a field, which
no operation carried. ⛔ **What that bound no longer covers is the implementations**: two of them
perform the write now, and each shapes a value by the field's own type rather than by what the
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

⚠️ **Every impossibility in that table is a property of the tracker's API rather than of the
project using it**, which is the measurement behind
[`schema.md § 3 → Who declares a capability`](../plugins/mjolnir/config/schema.md#who-declares-a-capability).
No comment action, no short-id field, no label at creation time — each of those is one tracker's
API and not one project's choice, and no configuration a project writes can reach any of them.

⛔ **The sentence above is narrowed by what building the third implementation found, and the four
Trello cells are where** — the rule it serves being
[`schema.md § 3 → Who declares a capability`](../plugins/mjolnir/config/schema.md#who-declares-a-capability),
which is what the narrowing has to leave standing. *API* there is doing work it cannot carry: a
tracker is reached through
some **interface**, a project's copy had one, and four of that column's cells are properties of the
interface rather than of the tracker. Measured against a live Trello through a different interface
and read against the published reference — the detail is
[below](#what-building-the-card-implementation-established) — three of the four reproduce on that
second interface and one does not: **comments exist**. What the sentence still holds for is the
direction of the argument, which is the half § 3 depends on: none of the four is a configuration a
project writes, and a project cannot reach any of them either way. What it must not be read as is
*this tracker cannot*, which is the reading the implementation would have taken into the adapter.
⚠️ **And three of the six run on a single tracker**, so a difference between those three cannot be
a capability difference at all — the API answering them is one API. What projects were found
differing in is which mechanism carries the type, the estimate and the template, which is a facet
below and already has a home of its own.

### What building the board's implementation measured

The survey above read the copies; these are the host's own answers, measured while the
implementation behind `kind: github-projects` was written. Each one is a shape the implementation
takes because of what came back, and none of them is derivable from the table above.

| What was asked | What came back |
|---|---|
| the same field asked for **by name** twice in one query | refused outright — `fieldConflict`, *has an argument conflict* — and legal only with an alias on each. So the implementation asks for none by name: it reads a card's whole value connection once and keys the answer on each value's own field name, which has no alias to get wrong and costs one request rather than one per field |
| a card's values, for a card on a live board | only the columns that **hold** a value: the host-managed ones carry none at all, so a column read as empty and a column the host maintains are the same answer and a write has to be refused by the field's own type rather than by its value |
| a number that names a pull request | the host's own typename says which of the two it is, and a merged pull request answers with a state no `statuses` list contains. ⚠️ A stronger guard than reading a URL for `/pull/`, and the implementation beside this one takes the weaker route because that is what was measured for it |
| a board addressed by an owner's login | resolvable through the owner interface with a fragment per owner kind, so nothing has to know whether an owner is a person or an organisation. Asking the wrong one of the two by name answers an **error** rather than nothing, which is what makes the guess expensive |
| a board with more items than one page | the page's own cursor, and nothing in the answer that says a list is short. ⚠️ The client's paginate flag follows top-level pages and not a nested connection, so the ceiling is silent: a round total is the signature of an unfollowed cursor |
| a project number nothing resolves | `NOT_FOUND` with a non-zero exit, which is why an address the reader accepts and the tracker rejects arrives as a failed call naming the owner and the number rather than as an empty board |
| a field value handed in as one variable — the whole input object the write takes | refused: *provided invalid value*, because the client sends a variable as a string and the host wants an object. So a write takes the value as a **typed scalar**, one document per kind of column, and nothing is pasted into a request |
| a number sent as that typed scalar | refused in turn: the client's typed field parses an integer and leaves anything else a string, and the untyped one is a string by definition, so a `Float` cannot travel as a variable at all. The number is formatted into the document — safe for one reason that does not generalise, which is that it is a `float` by then and a non-finite one is refused before formatting |
| the board's items, read immediately after a card was added to it | the card is **absent**, while the item's own card list already carries it — and the host's own count agrees with the short page, `hasNextPage` false. ⛔ So the one omission a board read can carry is invisible to anything a reader could check, no guard catches it, and what the operation states instead is the bound: a duplicate check run straight after a filing may not see what it just filed |

Both of the last two came out of writing rather than reading, with every read already green — which
is the same shape the first implementation's three defects had, and the reason the live half of a
run through this port is a write and not a report.

### What building the card implementation established

⛔ **Not *measured*, and the heading says so deliberately** — which is
[`schema.md § 11 → A report names what it could not establish`](../plugins/mjolnir/config/schema.md#a-report-names-what-it-could-not-establish)
applied to this document rather than to a run. The implementation behind `kind: trello` speaks the
tracker's HTTP interface with a key and a token, and this repository's shell holds neither — so
nothing below was established by running the adapter. Two weaker sources were used instead and are
**named per row**, because they do not agree everywhere:

- **a live board, through a different interface** — a connector over the same tracker, which reads
  and writes cards but is not the interface the adapter speaks. What it shows about the tracker's
  own shapes is observation; what it shows about an endpoint is nothing.
- **the published reference** — the tracker's own statement about the interface the adapter does
  speak. Authoritative about the endpoint and unverified against a running one.

| What was asked | What came back | Established by |
|---|---|---|
| where a card's number lives | the card's URL is `/c/<link>/<number>-<slug>`, and the number opens the last segment; the connector's card carries **no** short-id field at all, which is this survey's own row | a live board |
| what a card's state is | the board's states are its **lists**, and whether a card is archived is a separate fact — so a card in the project's terminal list is not archived and an archived card is still in a list. Both are reported, never collapsed | a live board |
| what classifies a card | labels, as board-level objects carrying a free-text name. ⚠️ The name is neither unique nor required — the live board carried one label with a name and no colour — so a name is resolved to **at most one** label and an ambiguous one is refused | a live board |
| whether a comment can be posted | **yes**, and this is the one row that refutes the survey above: the connector posts one, lists them, reads one back, and the board's own history names `COMMENT` as an action type | a live board |
| whether a check item can be removed | the connector has `create`, `add_item` and `update_item` — rename and tick — and **no delete**, which is the survey's row exactly; the checklist endpoint documents `DELETE /checklists/{id}/checkItems/{id}` | both, disagreeing |
| whether labels can be set at creation | the connector creates a card from a list, a name, a description, a due date and a position, then attaches labels one call each — the survey's row; the card endpoint documents `idLabels` on the create and on the update | both, disagreeing |
| what a custom field costs | the live board has **none**, and the connector addresses one by an option id per type. So the one value § 4.5 names reaches this tracker as the card's own `due`, and a facet pointing anywhere else is refused naming the power-up it would need | a live board |
| how a card is addressed by its number | the card endpoints take an id or a short link and **not** the number; the number resolves only as a nested segment of the board's own card path, which is the slot the documented `filter` keyword occupies. So the adapter resolves a number through the board's card index instead — which is also the only route to an **archived** card by number | both, agreeing |
| whether a collection can be read whole | the card collection names no cursor, and a collection answers at most 1000. ⛔ So there is no page to follow and nothing to truncate, and the only honest guard is to **refuse** an answer that reaches the ceiling — a board that genuinely holds that many included | the published reference |
| what a refusal looks like | 429 with the limit named, at 300 requests per 10 seconds per key and 100 per token; the key and the token travel as query parameters, which is why every failure message here names them rather than quoting the call it made | the published reference |

⛔ **Where the two sources disagree the adapter follows the reference, and the direction of the two
mistakes is the argument** — under
[`schema.md § 3 → Who declares a capability`](../plugins/mjolnir/config/schema.md#who-declares-a-capability),
which makes a capability the adapter's own fact and leaves nothing else to decide it. An operation
declared absent that in fact exists leaves a role taking a
stated fallback for ever with nothing reporting it; one declared present that does not exist comes
back as a failed operation naming the call. The second is visible and the first is not, so the two
disagreeing rows — the check-item delete and the labels at creation — are implemented.

⚠️ **What this leaves unestablished, which is more than for the two implementations before it**: no
call in that adapter has been made to a running host, so the three reference-only rows are the
reference's word and nothing beyond it. What a run of it takes is a board and the pair of variables
[`examples/trello.yaml`](../plugins/mjolnir/config/examples/trello.yaml) names, and the shell this
repository's own roles are handed holds neither — which is a fact about this repository rather than
about the adapter, since nothing here is configured for that tracker.

⚠️ **What the implementation's own suite cannot answer is what the host does with a payload**, which
is why the read half is driven against a live board by hand and recorded on the work item: a board
past one page read whole, a card's columns out of one query, and the pull-request guard refusing a
real pull request number.

### What building the issue implementation established

⛔ **Not *measured*, and the heading says so for the reason the one above it does** —
[`schema.md § 11 → A report names what it could not establish`](../plugins/mjolnir/config/schema.md#a-report-names-what-it-could-not-establish)
applied to this document rather than to a run. The implementation behind `kind: jira` speaks the
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
| what a state is | a status the item is **in** and a transition that leads there, and a transition's `name` is a separate field from the `to.name` it leads to. ⛔ So a status word is matched on what a move leads to; matching the verb would match the wrong half on every workflow whose verbs differ from its states | a live site |
| which statuses an item can reach | what the workflow offers **for that item's type**: on one project defining nine statuses, one type offered three of them and another all nine. ⚠️ So a word the project states and this item cannot reach has two readings — a vocabulary the tracker lacks, or a move this workflow does not allow from here — and neither is assumed | a live site |
| which types an item can have | nine available on one project with six in use, against a branch-prefix vocabulary of five — the case behind `type_branch_prefix` being a map rather than a boolean ([`schema.md § 4.1`](../plugins/mjolnir/config/schema.md#41-type)). ⛔ And a type is **required at creation**: there is no filing without one, which is the one place this tracker forces a question the code-host trackers leave open | a live site |
| what a dependency's two sides are called | the link type reads `inward: is blocked by` / `outward: blocks`, and the call's `inwardIssue` is the item that **blocks** — the inversion this survey's own row named, now with both halves in hand. ⛔ Read the wording and the dependency is filed the wrong way round, and nothing in the answer says so | a live site |
| how a dependency reads back | the entry an item carries names the *other* side, so an entry holding `inwardIssue` means this item **is blocked by** it. ⛔ Which is why the adapter's direction is held by a round trip rather than by reading the call: the write and the read are two separate chances to invert it | a live site |
| whether an estimate exists on this tracker | a native composite field, holding a duration as text (`2h`) and mirrored as seconds, with a value on the large majority of one real project's items — and the values come from a closed ladder of size classes mapping to hours rather than being free numbers, so `estimate` here is *(native field, hours, a closed set)*. ⛔ What the sprint answers is the **gate** and not the carrier: an item with no estimate still starts, which is a statement about the readiness list. Reading that as the carrier being absent is how a configuration comes to claim a project sizes nothing while its own board sizes nearly every item | a live site |
| what a search costs | a query with **no restriction is refused outright** — *Unbounded JQL queries are not allowed here*. ⛔ So the project restriction is the only shape the host accepts, which is also why the state qualifier the plain-issues implementation has to refuse cannot arrive here: every term is quoted into an operand | a live site |
| what a body is | a structured document rather than a string, on the interface version the adapter speaks. ⚠️ So no markdown body is simply sent: the adapter renders headings, paragraphs, bullet and ordered lists and fenced code, states that nothing else survives, and reads a document back the same way — a fuller renderer is a markdown parser, which would be the implementation deciding what a template means | both, agreeing |
| how a custom field is addressed | by an id that is **site-specific**, so a field is named in a configuration and resolved against the site's own catalogue per run. ⚠️ And a name is not unique there, so an ambiguous one is refused rather than resolved by position | both, agreeing |
| who moved an item | the history names an author, and ⛔ **a script running under somebody's token is indistinguishable from that person in it**. So the advance-off-a-merge operation reports whether the last status change was made by something *other than this credential* and refuses to call it automation | the published reference |
| whether the merge is visible here | **no**: the merge is on the code host, and nothing on this tracker ties a status change to one. ⛔ So `link_for_close` is absent — there is no closing keyword to compose — and the advance operation answers the tracker's half alone, with the other half read from § 2's host | both, agreeing |
| how a search is paged | a cursor in the answer, followed until the host says it is the last page. ⚠️ A page that fills says nothing about whether more exist, which is the same silent ceiling the board implementation pays a cursor-follower to avoid | the published reference |

⛔ **One defect this implementation's own suite found, recorded because the shape generalises** —
the standard it is measured against being
[`schema.md § What earns a test`](../plugins/mjolnir/config/schema.md#what-earns-a-test-and-what-makes-its-red-believable),
which is where a guard's red has to be believable rather than merely present. The address and the
credential were resolved **inside** the named transport in the first draft — and a
transport is a *seam*, so every guard inside it is a guard a substituted transport walks straight
past. A site carrying a path and a shell holding no token both read as *the call went out and the
host answered*. Both guards sit above the seam, which is where the card implementation puts its
own, and the transport is handed an address and a credential rather than reading either — so a
guard on either is a guard every transport is held by, the substituted one included.

⛔ **And one it reddened in a sibling**, held to the same standard —
[`schema.md § What earns a test`](../plugins/mjolnir/config/schema.md#what-earns-a-test-and-what-makes-its-red-believable).
The port contract's suite registers a double against a kind
nothing is installed for, and it chose one out of the set the surface states — so the day the last
implementation landed there was no such kind left and the whole block went unasserted while
reporting a failure nobody could fix. ⚠️ A gate that reddens on the project finishing is the shape,
and the fix is the one the same file already records a block earlier: the kind is **derived** from a
stated word rather than chosen out of the stated set.

⚠️ **What this leaves unestablished** is what the two implementations before it leave: no call has
been made to a running host through the interface the adapter speaks, so every reference-only row
above is the reference's word and nothing beyond it. What a run takes is the site and the pair of
variables [`examples/jira.yaml`](../plugins/mjolnir/config/examples/jira.yaml) names, and the shell
this repository's own roles are handed holds neither.

## What is an ordered list of named checks rather than procedure

No count is given, for the reason [`schema.md § The
loop`](../plugins/mjolnir/config/schema.md#the-loop--ten-roles) gives for the axes — a count
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
([`§ 17 → A local check the host already runs`](../plugins/mjolnir/config/schema.md#a-local-check-the-host-already-runs-is-a-misconfiguration)):
every check in the table above is mirrored by no workflow at all — a hand test on the running
application, an acceptance suite needing it up, and a checklist carried on the pull request —
which is the shape the facet was derived from. A check that *is* mirrored needs no entry, because
the host has already answered it, and these two measurements supply no example of one.
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
  eight-check copy named in the readiness-gate section above. A gate whose input is a convention is
  the shape this whole document exists to catch, and that check's input is a facet of its own
  ([`schema.md § 4.6`](../plugins/mjolnir/config/schema.md#46-priority)) rather than anything this
  ordering supplies: ⚠️ **the two are different questions**, which is why a project may configure
  either without the other and why neither reads the other's key.
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

## The work-item facets, and the absent case

Issue type ([`schema.md § 4.1`](../plugins/mjolnir/config/schema.md#41-type)), status
([`§ 4.2`](../plugins/mjolnir/config/schema.md#42-status--an-ordered-set-of-name-role-writer)),
estimate ([`§ 4.3`](../plugins/mjolnir/config/schema.md#43-estimate)), template
([`§ 4.4`](../plugins/mjolnir/config/schema.md#44-template)), priority
([`§ 4.6`](../plugins/mjolnir/config/schema.md#46-priority)) and code root
([`§ 4.7`](../plugins/mjolnir/config/schema.md#47-code-root)) are each per-project,
and each was carried by a different mechanism depending on the project. Each but status has a
real absent case of its own — which is where the schema's absence-is-a-configuration rule comes
from: a procedure that treats absence as an unset value fails on a project that is correctly
configured.

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
- **Priority** — three projects carry one, between them over two carriers; a fourth parses a tier
  and writes it nowhere; two have no convention at all. A carries a four-value prefixed label axis
  on its board:
  exactly one label per card, never absent, and it is the input to the eight-check gate named in
  the readiness-gate section above. C uses the tracker's own priority field, three of its values.
  F labels its top tier alone with a prefixed label and leaves everything below it bare. B's
  filing role takes the same `high | medium | low` argument the other two take and has nowhere on
  its board to put it, which is the absent case with a working loop around it rather than a gap in
  one. D and E carry nothing. ⚠️ **The two that share a tracker kind do not share a prefix**, which
  is the sharpest thing in the row: F's axis and this repository's own are both prefixed labels on
  plain issues and the prefixes differ, so a procedure matching a literal would read one project's
  axis and no other's.

- **Code root** — the one project with more than one code repository
  ([counted in the sibling document](build-surface.md#a-verdict-is-a-command-a-root-and-a-condition))
  **carries this fact nowhere.** A's instructions file records the consequence as a rule rather
  than as a gap: *no skill on the route drives* the second one, so that repository's branches,
  pull requests, dispatch and board moves are done by hand against its own equivalents.
  ⚠️ **The same file states what decides which repository a card belongs in** — *whose code it is,
  never which track asked for it* — and the case it gives is the one that discriminates: a counter,
  a tag set and a consent gate are all one track's need, and their code is in the repository that
  track does not own. ⚠️ Two of that board's label axes look like candidates and answer neither
  question — one carries whose need the work serves and one carries who does the work — so the fact
  is neither carried nor derivable there. That is the absent case with no loop around it: the
  carriers a tracker could hold it in are a label, a field, a component or a title prefix, and
  nothing was found holding it in any of them.

**What priority needed that the other facets did not: a statement of how two items compare.** The
others answer a question about one item — what type it is, what it is worth, which template it
used. This one is read by a check that asks whether work ranking above an item is ahead of it, and
two measured axes answer that two ways: one ranks by a four-value list whose colours happen to run
green to red, and another by a single label whose absence covers everything else. Hence the ordered
`values` list and the rule that an item carrying none is unranked rather than lowest, both in
[`schema.md § 4.6`](../plugins/mjolnir/config/schema.md#46-priority) — and hence the refusal there
rather than a check reporting itself unanswered forever on a project that configured it with no
axis to read.

**And what it deliberately does not carry.** A's gate turns the tier into a due date through a
four-row table, which is the derivation the date facet's own paragraph at the top of this document
declines to generalise. That decision is unchanged by the tier now having a key: what made the
table one project's habit was that no second project was found to have one, and that is still true.
⚠️ This repository's own axis is the other half of why the facet is a carrier rather than a rule —
its two labels sat on the host while what they meant lived in a person's head and in one
project-local script, which is the shape every facet here was extracted from.

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
| how many are held right now | yes: it is half the comparison | `probe`, a key. ⛔ **The one question the procedure cannot answer about somebody else's resource** |
| how long a lease counts | yes | `ttl`, a key |
| the comparison itself — a sum, and over distinct keys | no: it is the same arithmetic everywhere | procedure |
| what happens on contention | no | procedure |
| which direction a guard fails in | no | procedure, and the one of these that is not obvious |

⛔ **The four keys that were already there are the measurement, and the three new ones are the same
measurement one layer down**:
[`schema § 10 → Exclusive resources`](../plugins/mjolnir/config/schema.md#exclusive-resources)
declares all of them, and
[`schema § 7 → A lease on an exclusive resource`](../plugins/mjolnir/config/schema.md#a-lease-on-an-exclusive-resource-and-the-exit-paths-that-release-it)
states what a guard does with them. The capacity rule measured on one project is *busy daemons plus
leases too young to have registered one, capped at two* — so a facet with `cap` and `subject` and
nothing else describes a lease nobody can take, there being no way to ask how many are held and no
way to know which call is asking.

**Why the fail direction is procedure and not a per-guard setting.** It is the one part of this that
looks like a preference and is not: both directions have a failure that reads like success, and
which of them is wrong is decided by the act rather than by the project. A guard that refuses every
call it could not reason about is a guard somebody turns off, and then nothing is held at all — the
same argument [`schema § 13`](../plugins/mjolnir/config/schema.md#13-what-counts-as-done--an-ordered-check-list-and-who-answers-each-check)
makes for not demanding a person everywhere. A guard that allows an act it could not reason about is
only wrong where the act cannot be undone, and there the rule already exists: ⛔ **silence is not a
yes where the answer would license something irreversible**, which
[`schema § The loop`](../plugins/mjolnir/config/schema.md#what-carries-the-item-forward-and-where-it-stops-to-ask)
states for an ask nothing answered and
[`schema § 7 → Which direction a guard fails in`](../plugins/mjolnir/config/schema.md#which-direction-a-guard-fails-in)
applies to a guard. A project that could configure this would be choosing whether its own merges
happen unread.

**What the merge gate can and cannot be keyed on, measured on two of the three projects.** One
carries a pair of hooks — a recorder for the answer and a guard refusing a merge where no record
exists — and the other carries a single hook holding every merge behind an ask that reads no record
and that no review can silence. ⛔ **They are not two halves of one design**: the second cannot be
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

⚠️ **What makes the second and third instances the sharp ones is that neither names a script a guard
could recognise.** The second's paid command is an ordinary invocation of the runner that also runs
its cheap suites; the third's are invoked exactly like the free unit tests beside them — same
command prefix, adjacent names, same runner. ⛔ **So the decision rests on the arguments, and
`args_match` is load-bearing rather than sugar on a command name**:
[`schema § 19`](../plugins/mjolnir/config/schema.md#19-a-command-that-spends-and-the-supervision-it-is-refused-without)
declares it beside `command` for that reason, and a facet with `command` alone would describe one of
the three.

| the part | does a role or a guard read it to decide what to do next | where it lands |
|---|---|---|
| which commands spend | yes | `deny`, a key. The three projects' paid commands have nothing in common but being commands |
| what separates a paid invocation from a free one by the same binary | yes: it is the whole decision in two of the three | `args_match`, a key |
| what the call costs | yes: a refusal names it | `reason`, a key. ⛔ **The figure itself never leaves the project** |
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
system. ⛔ **The parse varies in no project at all**, which is why
[`schema § 19 → The command position`](../plugins/mjolnir/config/schema.md#the-command-position-and-why-the-whole-call-is-not-one)
states it as procedure, and the correction it carries is the reason it is extracted rather than
rewritten: the guard's own header records an earlier version that grepped the raw command and
refused a text edit whose prose contained a script path.

## The live half: one guard, and the two lists that are not interchangeable

One project carries a deny guard in front of a shell command that could open a session on the
machine it runs on. It began as one of two inline guards — "deny guards on a production path and
on a route", which is how #16 recorded them with no acceptance item and no key on the surface for
either — and by the time it was extracted it was a hook of its own with a test matrix beside it.
⚠️ **That matrix is why it is extracted rather than written from the idea**: the verdict rule, the
inversion and the four closed directions are each a line somebody was taught by a failure, and a
rewrite from the idea reproduces none of them.

**What the verdict depends on is not the command.** ⛔ **It is who would answer the prompt**, and
that is the load-bearing line
([`schema § 21 → Which verdict`](../plugins/mjolnir/config/schema.md#which-verdict-and-who-would-answer-the-prompt)):
a mode a person answers gets an ask, a mode that answers its own prompts gets a refusal, and an
unrecognised mode is read as the second. Both failures of that rule are cheap to picture and were
expensive to find — a guard that always asks enforces nothing in a run nobody is watching, and a
guard that always denies is one somebody turns off.

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
⛔ **Collapsing them into one configured list would put somebody's infrastructure into a repository
anybody can clone**, which is the one thing this facet is organised to prevent; collapsing them
the other way — a file for both — would make a loopback name a per-machine fact that every new
checkout has to be told.

**Why the absence of the file makes the guard stricter rather than quieter.** A machine where
nobody has written the list yet is one where every name that list would have cleared reads as live,
so a half-set-up machine is safe by default and the remedy is visible in the refusal
([`schema § 21 → The four ways it fails closed`](../plugins/mjolnir/config/schema.md#the-four-ways-it-fails-closed)).
⚠️ **That is the opposite of how a missing configuration file usually reads**, and it is the
direction this facet cannot afford to have backwards.

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
single rule that two state, every one of them written the day somebody was corrected:

| the rule | how many of the six state it |
|---|---|
| a test is a ceiling rather than a floor, and the list of cases is the intended extent | 1, and it alone states the consequence |
| fakes over mocks, with the seam named | 2, one of which also states the sharp end — mocking the store proves nothing, so that tier runs against a real one |
| the violation is written first and the red confirmed | 1 |
| assert values and never key sets; a fixture thinner than the production shape tests the fixture | 1 each |

⚠️ **No role reads any of them.** That is what makes this an extraction rather than a tidy-up: each
is advice a careful reviewer would give in any of the six, held where one project's sessions can
reach it and no other's. Hence the statement as procedure in
[`schema.md § The loop → What earns a test`](../plugins/mjolnir/config/schema.md#what-earns-a-test-and-what-makes-its-red-believable).

**Why the surface, and not either of the two homes it was weighed against.** The discipline is read
by two legs — the implementing one, which no role owns, and the reviewing role — and
[`schema.md § The loop`](../plugins/mjolnir/config/schema.md#the-loop--ten-roles) already settles
what follows: a rule read by two roles and written in one of their skills is a second authority for
the other. Promoting these rules into the reviewing role's own text is therefore the option with a
precedent against it rather than the cheap one, and it is ruling 11's reasoning arriving a second
time. A per-project pointer — the shape the role-to-person map takes — fails a different test: a
pointer carries values a role reads, and none of this is a value. Six copies free to disagree is the
defect the extraction deletes rather than a configuration of it.

**What was not promoted, and the measurement is the reason.** A coverage figure is set in one
project's runner configuration, written as a placeholder in a second, and stated by neither of the
remaining four; promoted on that evidence it would be one project's taste imposed on five. The
case-file naming, the package-mirroring layout and the decision *not* to sit cases beside the code
they cover are one project's and are stated by none of the others.

⚠️ **One of those local conventions is also the measurement for why a local rule is named rather
than left out** — and it is a tier-boundary defect rather than a naming one. A project carrying nine
cases against a dependency it stands up itself, under a distinct suffix, states that suffix
**nowhere** in its own testing conventions, which list the framework, the mocking policy, the file
naming and the layout — all four of them the unit tier's — and then stop. The tier it leaves
unmentioned is the one its own build cannot run unaided, and a convention nobody wrote down is not a
convention a migration can carry.

## The register nothing compared to the suite

One project of the six carries an end-to-end tier with a record of what it covers: **14 scenario
groups**, a register table in that repository's own instructions file, and **two checks in the
host's lint workflow** holding the three together. Measured 2026-10-19, and it is the only one of
the six where the record exists at all.

The first check compares the register with the scenario files **both ways**, and its own stated
reason is the failure neither direction shows on its own: the run prints its scenarios, the
register prints a shorter list, and nothing compares the two. It was written because one group sat
unlisted while the register was otherwise accurate — a list that is wrong by one row, in the
document a reader trusts to say what is covered.

The second compares the suite with the **change**: a pull request touching the source tree that
carries neither a new case nor a register row fails, and the escape is a section of that same
document reading *what is deliberately not covered, and why*. ⛔ Its rule is the one the facet
keeps: an uncovered change is allowed; an uncovered change nobody wrote down is not
([`schema.md § 15`](../plugins/mjolnir/config/schema.md#15-end-to-end-coverage-recorded)).

⚠️ Its stated limit is the one an adopter inherits rather than discovers. It judges one tree, so a
change to the container or deployment trees passes unremarked and a reviewer stands in for it
there. That limit is carried onto the surface as the `judged` key and the run's own report of what
it left unjudged, rather than closed by widening the judgement: a check that asked for an
end-to-end case on a change to the thing that builds the image is a check somebody turns off.

⚠️ **Nothing of the kind exists in the other five.** In the project carrying 12 end-to-end case
files, which cases pin which behaviour is recorded in prose — a section of the README and each
case's own comments — so a case too old for an assertion is a paragraph rather than a check. ⚠️
What the remaining four do about the tier was not measured; what was measured is that none of the
five carries a record anything compares to a suite.

**Why the comparisons generalise and the content does not.** The suite root, the glob a case file
matches, where the register lives, the heading its table sits under and which trees a behavioural
change lands in are each one project's decision — the same boundary the unit tier's four local
conventions sit on, one section up. *Does the register still describe the suite* and *is this
change covered* are neither, and asking them needs no stack, no credential, no indexed material
and no money. ⛔ So the facet states the five values and the procedure holds the agreement between
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
the run. ⛔ It is the only tier that can degrade to nothing at all while reporting success, and the
reason is structural rather than a lapse: the thing it needs is created by the run, so its absence
is a condition the runner handles and not a connection that fails.

The dependency arrives two ways, and the split decides who can answer the tier at all:

| how the dependency arrives | consumers | what the absence looks like |
|---|---|---|
| the **run** stands up its own container | three | the host answers only where its runner has a container daemon; locally, a missing daemon and a silent suite read alike |
| the **host** supplies a service beside the run | two | the local run skips silently, and the suite's own gate is one environment variable |
| no such tier | one | — |

⛔ **So «the host cannot run this tier» is false here**, which is why this is not the unrunnable-tier
axis one tier down: the host usually *can*, and the defect is that it says so whether or not it did
([`schema.md § 16`](../plugins/mjolnir/config/schema.md#16-what-a-run-executed-and-the-count-that-is-the-only-evidence-it-ran)).

**What it cost, in the one consumer where it was priced.** Three suites covering that project's
money rules are gated on a single environment variable, and without it they abort as *skipped*
while the aggregate build still reports success — so a green build said nothing about the rules
those suites exist for. That project's own workflow supplies a service beside the run and **fails
the build when any of the four suites it names reports zero tests or any skip** — the fourth is
outside the money rules and is on the list because the rule is a list of names rather than a
property of a suite, so a gated suite missing from it is exactly as silent as having no service
container. ⚠️ That rule is written into one workflow file, mirrored by nothing, and stated nowhere
on the surface it was read from — which is the shape a fact takes just before it is extracted.

**Why the count, and why it is not a coverage figure.** A dependency-gated suite's degradation is
*designed* to be quiet: skipping is the correct behaviour for a case whose dependency is absent, and
the defect is the aggregate reporting a pass. So what separates the two is arithmetic the run
already has — how many executed, how many skipped and what each skip wanted, against how many the
tree declares. ⚠️ **Why the rule stops at one floor** rather than becoming a percentage: a threshold
reddens on the count being wrong, which is a defect in the declaration rather than in the tier, and
a check that reddens on a figure nobody maintains is the check somebody turns off. What the rule is
therefore held to is the surface's
([`schema.md § 16`](../plugins/mjolnir/config/schema.md#16-what-a-run-executed-and-the-count-that-is-the-only-evidence-it-ran)).

**Why it generalises and the commands do not.** How many cases a tree holds and what a run printed
are each one project's command, written in that project's own runner; *did anything execute* is
neither, and asking it needs two numbers. ⛔ So the facet states the commands and the floor, and the
procedure does the arithmetic — naming no runner, no task name and no report format, which is the
same boundary the local-check and unrunnable-tier facets sit on.

**Why it is a host check rather than a local one.** For the reason the register one
above is: a command the host already runs is refused as a local check by
[`schema.md § 17`](../plugins/mjolnir/config/schema.md#a-local-check-the-host-already-runs-is-a-misconfiguration),
and this is the cheap half — two numbers — of a tier whose expensive half is the run itself. ⚠️ And
the honesty it adds is pointed at the **host's** verdict, where the four-valued rules already
landed stop: a job whose every step ran and whose suite executed zero cases satisfies all of their
preconditions and reads green.

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
repository's standing remedy — and the gate prints the live figure instead as of
[#91](https://github.com/ragnor-rs/mjolnir/issues/91), which made each file's footprint part of its
own run's output.

What is stable enough to state without a number going stale: **a single role runs to thousands of
tokens and carries dozens of ⛔ and ⚠️ markers, and the loop has ten roles.** A window largely
spent on procedure before a line of anyone's code is read is what § 11 exists to notice, and the
harness vendor's own guidance is that an over-long instructions file is not read selectively — it
is ignored wholesale. <https://code.claude.com/docs/en/best-practices>

Two consequences, both already true of this tree rather than predicted of it. A role's body is
loaded only when the role runs, and only its frontmatter — a name and a description — is always
resident: that is the right shape, and it was not arrived at deliberately. And a role that cites
the surface to settle one sentence resolves the whole of it to do so, which is the argument for a
citation naming the narrowest section that states the fact. Since
[#91](https://github.com/ragnor-rs/mjolnir/issues/91) closed, every heading of the surface is held
to being motivated by a document whatever its level, and a citation resolving to a `##` section with
no text of its own is refused by name; what stays a count rather than a verdict is the coarser case,
which
[`single-source-of-truth.md`](single-source-of-truth.md#what-the-granularity-check-deliberately-does-not-hold)
records against itself.

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
rules are stated instead, and the one live reading goes where something already reads it: the spend
guard's own bar at
[`schema § 19 → What an approval is per`](../plugins/mjolnir/config/schema.md#what-an-approval-is-per-and-the-one-price-stated-before-a-turn-runs),
which reports a resume priced above it and reports **no figure** where the harness gave none, and
[`schema § 24 → The window's own reading`](../plugins/mjolnir/config/schema.md#the-windows-own-reading),
the role that restores a session, for the context half of the same payload. ⚠️ **Both arms are
written around that payload carrying nothing**, which the subsection below is why.

### What a resumed session is actually handed

The field list two paragraphs up — the one carrying the vendor's own link — is the vendor's
documentation. What a resumed session's event actually carried,
probed rather than read: **five fields, and none of the four the documentation names.** A
`SessionStart` payload on a resumed session carried the session's own identifier, its transcript
path, the working directory, the event name and `source: resume` — no token count, no time since the
last response, nothing about the prompt cache, and no price. The harness in question is **eighteen
patch versions older** than the one the fields are documented from, which is the explanation and not
an excuse: a machine running this toolkit is as likely to be behind as current.

Three consequences, and the first is the one that matters:

- ⚠️ **An arm written to rely on those fields reports nothing on a machine where they are absent,
  and nothing is indistinguishable from a cheap resume.** So both arms reading that payload are
  written around the absence — the price half already reported *no figure* rather than *free*, and
  the context half says it was handed no reading rather than describing an empty window.
- ⚠️ **A tested-absence claim about a harness event is an assertion until a probe answers it**, and
  this is the second time that has been paid for in this repository. The probe is cheap: a settings
  file supplying one hook, a print-mode session, and the same session resumed — the payload lands in
  a file and the question is answered in two commands.
- ⛔ **What the probe measured is a version and not a contract**, so the arms are written to read the
  fields where they are there. A reading that arrives tomorrow is reported with no edit, and the
  rule those arms are held to is
  [`schema § 24 → The window's own reading`](../plugins/mjolnir/config/schema.md#the-windows-own-reading)
  rather than anything stated here.

### What a compaction leaves behind, and what it does not take

The replay answer the restoring role gives rests on this, so it is measured rather than reasoned
about. A compaction **appends** to the transcript it summarises rather than replacing it: one
`system` record carrying the compaction's own metadata — its trigger, the token count before and
after, and the cumulative total dropped — and one `user` record flagged as the summary, marked
visible in the transcript only. Measured on one of this repository's own compacted sessions: 617,688
tokens before, 14,285 after, 603,403 dropped, and **426 tool calls still in the file ahead of the
boundary**, 132 of them calls that wrote a file, each with its full input.

- ⛔ **So a compaction costs the window and not the evidence.** A file a session wrote before a
  compaction is as replayable after one as before it, which is the difference between *lost* and
  *out of the window* —
  [`schema § 24 → What a load may not assume survived`](../plugins/mjolnir/config/schema.md#what-a-load-may-not-assume-survived)
  is where that is a rule.
- ⚠️ **The replay has a real limit, and it is the first call rather than the compaction.** A file
  the session wrote whole is in the record with its content; a file it only ever *edited* is in the
  record as a set of differences against content nothing there holds. The harness keeps the
  pre-edit copy in a store of its own, which the sweep names rather than reads.
- ⚠️ **One logical session is one session transcript here**, which is the opposite of what was
  expected when the role was specified: across **863** session transcripts in this machine's store —
  the top-level files, which is the universe the claim is about and not the 2,406 files the store
  holds in all — none carried records of a
  session other than the one its name states, and a resumed session probed directly wrote to the
  same path it had before. So *the last session* and *the last session transcript* coincide, and the
  sweep is written against the file.
- ⚠️ **The sidecars are the other half of that and go the other way.** In this project's own store:
  **153** subagent transcripts and **41** tool-result directories against **138** session
  transcripts — and every sidecar sampled carries its **parent's** session identifier, which is
  exactly the spans-more-than-one-file shape the item predicted, one level down from where it was
  predicted. Delegating to a sub-window is the practice § 11 recommends, and it writes its trace out
  of the file a sweep reads — so the sweep counts what is beside it and says it counted rather than
  read.

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

## Bounding the window at the call, and what the harness gives a hook to do it with

[`schema.md § 22`](../plugins/mjolnir/config/schema.md#22-what-enters-the-window-bounded-where-the-call-is-made)
is the enforcing half of the section above, and what forced it into a facet of its own is worth
recording beside the measurements that forced that one.

The [findings recorded above](#what-the-published-measurements-establish) rank what hurts a window
and name summarising it as the lossy way to spend one; § 11 took the conclusion for the artifact,
making the handoff a file somebody wrote rather than what a summary left behind. What it did not
reach is the other end of the same finding: the window is spent one call at a time, and every one
of those calls was a decision nothing was holding. A guard that acted after the summary would be
acting on what survived it; a guard at the call is acting on the thing itself.

So the facet is about **three places the harness publishes, and a fourth it does not**. A hook
answering before a call may refuse it or replace its arguments outright; a hook answering after one
may replace what the call returned. ⚠️ **The fourth place is the event that fires before a window is
summarised, and it is the one this facet does not use** — it was registered in every arm of the
measurement recorded in the project store for this repository and **never fired**, so what it
carries is unestablished rather than empty, and
[`schema.md § 7`](../plugins/mjolnir/config/schema.md#what-a-hook-can-establish-about-the-role-it-is-running-under)
already states that a rule reaching it would be written against a measurement nobody has taken.
⛔ That is why nothing here refuses a compaction, and why the arms that ship are the three that
answer on a call.

**Why a result limit is a key while a window budget is not.** A result's own length is the opposite
case to the one
[refused above](#why-there-is-no-threshold-on-the-surface): the event that fires after a call
carries the result, so its size is readable exactly when there is something to decide about it.
⚠️ **It is the same test, passed rather than failed** — that subsection states what the test is, and
this is why the same document can refuse one threshold and carry another without contradicting
itself.

**Why the exemption is a project's list rather than a case inside the guard.** This toolkit ships a
role that **forbids** truncating its own evidence output, and states why: the measurement is
recomputed whole for the half that was cut off. A blanket bound would therefore contradict a shipped
role — and the first shape that suggests itself, a name in the guard's own code, is the defect this
repository exists to delete, since no project could see it and no project could add its own. The
list is a project's for the same reason the mirrored commands are: what a project may not truncate
is its own fact.

### What a hook may tell the session rather than the person

The rewriting arm is the first thing in this toolkit that changes a call and lets it run, and that
makes the channel it reports through load-bearing rather than cosmetic. A bound added silently is a
bounded result read as complete — the window would then hold a *wrong* premise instead of a noisy
one, which is the worst of the three ranks quoted above.

⚠️ **The two channels are not interchangeable, and which one reaches the session was measured rather
than read off the names** — the measurements are
[recorded per event](single-source-of-truth.md#the-rules-loaded-rather-than-checked) and are not
restated here. ⛔ **What is new for this facet is the event**: the field that adds context is
documented for the event before a call, and the client that is installed states its support for it
outright, which is what the rewriting arm rests on. ⚠️ **It is still a field whose validity is per
event rather than universal** — the same document records one event rejecting it and failing the
operation outright — so this is a reading of a reference and a client rather than of a run in this
repository.

So the reports divide by audience rather than by severity: a call that was rewritten tells the
**session**, because the session is about to read a result it would otherwise misread; a
configuration that could not be read tells the **person**, because nothing the session does next
depends on it and the remedy is an edit to a file.

⚠️ **What the client does with a *replaced result* was read out of it rather than from the
reference**, which states only that the field replaces a result: a tool that is not an external one
has its replacement validated against that tool's own output schema, and a mismatch keeps the
original and adds an error. ⛔ **So the shape of a replacement is not a choice the facet had** — it
is the shape the response arrived in, and a first version answering with text alone would have left
every oversized result whole with one more message beside it.

## The revision key never moved, and the markers took its job

What the surface now states is at
[`schema.md § The file itself`](../plugins/mjolnir/config/schema.md#the-file-itself): the key is
retired, a configuration still declaring it is refused, and a retirement is marked `# retired:`.
What this section carries is the measurement that forced it.

`version` was in every configuration from the first commit that carried one (`6410f34`) and the
surface named it only at `9451882`, where this repository's own single-source gate found a key
every adopter writes that the single statement of the surface did not declare. It was then read by
nothing for the whole of its life, and it never moved — through a run of changes that each made an
older configuration unreadable.

The table below is the statement, and no count of its rows is written beside it: a figure in prose
goes stale on the next row, green, which is the defect one level up from the one this section
records.

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

⚠️ **The rows kept arriving while this change was open**, and each was added by merging `main` into
it rather than by anyone revisiting the question. A revision that moved on every required key would
have been stale inside the very branch that introduced the rule, twice over — which is the argument
the table makes, made by the only means that can make it. ⛔ It is also why no figure accompanies
the table: each of those merges would have falsified one.

**Classified against the ruling, every row reads the same way: the key would not have moved.** The
revision is retired, so no row is an instance of a revision that should have been bumped and was
not — each is a configuration refused with the key named, which is what the marker beside that key
already does. `host.landing.method`, `done` and `environment.inherits` are why the alternative of
absorbing a new key with a default was not available: the first has no default by design, since one
would pick a merge method for every project that did not notice the key, and the other two are
facets whose `[]` the surface states in as many words is a decision and *not* an unset key — so a
default there would manufacture the very decision those facets refuse to infer.

**What settled it is `e62a1d9` (#137), which moved requiredness onto the surface and deleted the
reader's own list of it.** Before that, a reader met a missing key with no way to say whether the
project had decided against it; after it, requiredness is marked beside the key, a legitimately
unset key carries no marker, and every facet with a real absent case carries a `carrier` whose
`absent_reason` is the decision written down. A configuration states its decision or is refused
with the key named. That is the whole of what the revision was introduced to separate, answered
where the key is declared rather than by a number describing the file.

⚠️ **What the retirement gives up is stated on the surface** beside the retirement itself, and the
measurement behind it is this table: on every row the remedy an adopter faces is the same act, so
what is lost is a diagnostic during a phase of rapid surface change rather than a behaviour. The
cost falls on a configuration written months earlier, which is told *which* keys are missing and
never *that they are new*.

**The retirement is held in both directions, and the arm that holds the set was missing until this
change.** The reader refuses a retired key and its self-test asserts both that the surface declares
no such key and that a configuration still carrying one is refused — but every one of those
assertions was generated from the reader's own list, so deleting an entry deleted the refusal and
its only assertion together. Measured: with the `version` entry removed the suite stayed green on
every assertion and the reader accepted `version: 1` again. That is exactly the defect the retired
`REQUIRED` table demonstrated, surviving in the one list still shaped like it. What closes it is
the marker the surface now declares, read against the reader's own list in both directions — and
a third arm beneath those two, because the pair of them compare the derivation only against that
list: replacing the derivation with a constant left both green until a plant stripped the clauses
out of the surface and asserted the comparison notices.

⚠️ **That marker is a token because the first attempt at it was not.** The retired set was first
read out of the surface's prose, by a grammar matching a backticked key followed by *is retired* —
and it read `host.repo`, a live required key, out of a sentence stating it is retired **in no
sense**. A negation is invisible to a grammar of that shape, and prose is where negations live, so
a machine-read fact belongs in a clause with the prose beside it saying why.

## The boundary that was carved out six times

What the surface now states is at
[`schema.md § What the procedure models`](../plugins/mjolnir/config/schema.md#what-the-procedure-models-and-what-it-only-names-and-calls):
the test for a candidate key, what a configured command or path carries, and four worked cases.
What this section carries is the measurement that forced it — and unlike the rest of this document,
it is a measurement of this repository's own backlog rather than of the six projects the surface
was derived from.

**Six work items stated the same boundary, each on whichever item happened to need it**, while the
surface stated none of it. What each body held on 2026-10-21, the day the statement was written and
each of the six reduced to a citation of it:

| the item | what it stated |
|---|---|
| #13 — the deploy role | hosts, services, secrets, build steps and tier selection stay local, and a project whose deploy is one script keeps that script, called from the skeleton |
| #24 — the branch model | worktree setup that installs dependencies, copies assets, allocates ports or names a container project is called from the shared procedure, never absorbed into it |
| #16 — the hooks | hook paths, event names and the shared library are extractable; what counts as the guarded resource is not |
| #60 — the unrunnable tiers | the commands stay project-local, and no tier taxonomy is imposed on adopters |
| #61 — the command root | the toolkit detects no manifest, infers no package manager and owns no build |
| #66 — the local check | no tool, task name or flag of any stack enters the toolkit |

⛔ **The copies disagreed, which is the part a list of homes understates.** #61 bars *detecting* a
manifest, #66 bars a tool name entering the toolkit *at all*, #60 bars a *taxonomy* imposed on
adopters, and #13 bars *build steps* while keeping a script path — so a reader could answer from
none of them whether a manifest name may appear in a role's text, or whether a command flag may be
buried in a `mirrors` string. Both are answered now at
[`schema.md § What the procedure models`](../plugins/mjolnir/config/schema.md#what-the-procedure-models-and-what-it-only-names-and-calls),
the second by ruling that the procedure matches nothing inside a command string, so the question is
about where a fact is readable rather than about which tokens are forbidden.

**The rule was propagating by restatement-with-attribution, which is the failure the collection was
filed about.** Two of the six cite #13 while rewording it; three carry a body edited after the item
collecting them was already open; and a **seventh** home is in the tree,
[#19](https://github.com/ragnor-rs/mjolnir/issues/19)'s sweep stating the boundary in its own words
and crediting the collection for it. ⚠️ **What the edit record cannot settle** is whether a given
sentence predates the collection by minutes or postdates it by days: it keeps timestamps and not
diffs, and all six were filed inside one four-hour window — two of them in the three minutes before
the collection and one in the two minutes after. What it does settle is that the restating did not
stop while an item to collect it was open.

⛔ **What the absence cost is the half that is not about tidiness.** An adopter whose bring-up
command, acceptance suite and environment restore are all local commands reads the surface, finds a
key for two of the three and nothing at all for the third, and meets nothing saying whether that
third is a missing facet or the boundary working as designed. The honest response to an absence
nobody can classify is an item per local command, which grows the surface in the one direction the
boundary exists to prevent — so what the statement had to be was a test a reader runs, with the
cases worked in the open, rather than a list of what stays local:
[`schema.md § What the procedure models`](../plugins/mjolnir/config/schema.md#what-the-procedure-models-and-what-it-only-names-and-calls).

## Four checks behind one workflow name, and the tolerance that hid it

The host facet was written workflow by workflow, which is how every project here that controls its
own workflows writes them. One project in the migration set does not: a single workflow runs **four
jobs mirroring four unrelated local commands** — two languages' linters and test runs, a document
gate, and a parse-and-lint of its shell scripts — and the four share a checkout and a build, so
splitting them into four workflows pays for four of each. What that configuration cost every
consumer is the same loss three times: a guard can only refuse or allow on *the workflow ran*, a
precondition reading *a run exists for this commit* reads green for a command whose job was
filtered out of it, and a coverage verdict computed per workflow reports a change covered on the
strength of jobs that never ran for it.

**This repository tested the opposite arm and the facet held, which is what made it evidence rather
than a second instance.** A second gate arrived with #19, and the obvious shape was a second job of
the existing workflow. The first attempt stated one of the two commands in `host.checks` and parked
the other in a comment beside it; a review rejected that, the sweep became a workflow of its own,
and the two commands were never joined with `&&` — a conjunction improvised inside one string being
the shape the facet already refuses for its triggers. So the cost of avoiding the shape was measured
here at one workflow file and one extra checkout, which is cheap enough that a second job sharing a
workflow name should need a reason. ⚠️ **What this repository could not tell anybody is whether
nesting is right**, having never had to nest.

**The tolerance is the part that was invisible.** The reader accepted a `mirrors` holding a *list*
of commands for as long as the gap was open — written deliberately, so that the refusal of a done
check the host already runs would compare against whatever an entry mirrored rather than hold
nothing, and recorded in the reader as promising nothing about the shape that would land. A
configuration no section of the surface stated therefore loaded clean, and the only statement of
its meaning was a docstring. ⛔ **That is the failure mode a tolerance has**: it is not a gap a
reader meets, it is a shape that works until somebody states the other one, and the two then
disagree about where a command's job and its filter live. Both are closed together at
[`schema.md § 2 → A workflow whose jobs mirror more than one command`](../plugins/mjolnir/config/schema.md#a-workflow-whose-jobs-mirror-more-than-one-command),
which states the nested form, refuses the list, and rules what the collision argument behind the
workflow key does and does not reach.

⚠️ **One half of that statement is held against nothing in this tree.** No workflow of this
repository filters on paths — every entry of its own facet omits the key — so the rule that a filter
sits at the level the workflow file states it at is exercised by the reader's own planted violations
and by the example that illustrates the form, and by no configuration this project runs on.

## One entry's two events, and the types the pattern could not carry

The same facet, a dimension over. `triggers` had two forms — an event and a base, or an event and a
branch, one of them or a list — and one entry of this repository's own is the first written against
it whose event **types** decide anything. The `Nothing deferred` workflow listens for
`pull_request` with `types: [opened, edited, synchronize, reopened, ready_for_review]`, and neither
form could spell that: the entry read `pull_request -> *`, which is the same text an entry for a
workflow naming no types at all would carry.

**`edited` is the one that is not decoration.** That gate reads the pull request body, and a body
corrected in place pushes no commit — so without the type the check stays red until an unrelated
push lands. The residue sat in a comment in the workflow file, which is the thing
[`schema.md § 2`](../plugins/mjolnir/config/schema.md#2-code-host) says `checks` exists to prevent:
every consumer reads it and none carries the facts itself.

**The second dimension turned up only once the first was being written down.** That workflow needs
a second **event kind** as well — findings arrive when a review is submitted, with no commit
pushed, so it listens for `pull_request_review` too — and `triggers` could state that no better
than it could state a type. Two gaps of one shape in one entry is what made the key worth extending
rather than annotating.

**Three questions, and the arguments that settled each.** They are stated as rules at
[`schema.md § 2 → What a trigger states`](../plugins/mjolnir/config/schema.md#what-a-trigger-states-the-event-the-types-of-it-and-the-ref);
what is here is why each went the way it did.

| Question | Settled | The argument |
|---|---|---|
| Where types live | **Inside the pattern** — `pull_request(edited) -> *` | A workflow with two events gives each its own list, so a key beside `triggers` is a second list aligned by position. And § 17's `counts_when` is stated in this same form on an entry that has no such sibling, so the alternative gives one mapping two vocabularies |
| What an omitted clause means | **The workflow's event block states no `types:` key** | Read as *the host's default set* it is uncheckable: the defaults differ per event, this surface carries none of them, and the table that would supply them is a second statement of the host's vocabulary. Read as *the file states no filter* the comparison is one the workflow file answers by itself |
| Whether the facet should hold types at all | **Yes, extended** | Neither guard needs one: #33's asks whether the host already runs a command, and the finishing role asks whether a run exists for *this commit*, which a run fired by `edited` is. What needs one is the consumer that writes a **verifier** rather than data — the drift check at [`§ 2 → The facet against the host's own definitions`](../plugins/mjolnir/config/schema.md#the-facet-against-the-hosts-own-definitions), which compares the clause against the workflow's own `types:` key in both directions. A facet that could not express the types would leave it reporting drift on a correct entry, green on one it had proved incomplete, or the dimension undeterminable, and each of the three is worse than the key being richer |

⚠️ **The event vocabulary is where the extension stops, and the bound was measured rather than
chosen.** The third event that workflow wanted is one no workflow file may name at all, and
[the measurement is where it already lived](single-source-of-truth.md#what-this-gate-deliberately-does-not-check)
rather than restated here. What it settles for the facet is that a pattern naming an event is not a
claim that a workflow may listen for it: the facet enumerates no events, and what refuses such a
name is the host as the file loads.

⚠️ **What this repository can say about the type clause is one entry's worth.** Every other
workflow here states no `types:` key and its entry carries no clause, which is exactly the reading
the omission rule gives it; the one that does is the whole of the evidence that the clause is worth
having, and the second event kind rests on that same entry. What exercises the rest is the reader's
planted violations and the example that illustrates the form.

## A section one role writes and another runs

The facet is [`schema § 20`](../plugins/mjolnir/config/schema.md#20-the-sections-a-pull-request-body-must-carry);
what is here is the measurement that made it one, and the three questions settled while it was
being written.

**What was found.** One project in the migration set carries a workflow of its own, separate from
its lint suite, whose single job asserts that a pull request body states what the change needs
done to an environment before it can be deployed. The section is not decoration there: the role
that deploys a batch collects exactly it out of every change the batch carries and runs what it
collected. So the body is an interface between two roles — and the heading it turns on was stated
in a workflow file and nowhere else. Read against the surface as it then stood, § 6 ruled the body
a summary and a test plan and deferred the closing form to § 3; environment preparation was a
third element the configuration did not state, and a gate enforcing a fact no configuration states
is the shape this surface exists to delete.

**Why it is not the title gate one item over.** Two properties separate them, and both change what
can be built:

| | The title gate | This one |
|---|---|---|
| What the rule reads | a pattern over the event payload, which a workflow can state inline | a body, which needs a parser |
| What `host.checks` records | an entry mirroring nothing, which the duplicate-run guard reads as never-guard | an entry whose `mirrors` names a command a person can run, which that guard reads as guardable |
| What has to be installed | one file | a checker as well, because a host run executes files and the toolkit is not one of them |

**Three questions, and the arguments that settled each.**

| Question | Settled | The argument |
|---|---|---|
| What makes a heading a facet rather than a convention | **Another role reads it**, stated on the entry as `read_by` | Any heading can be made mandatory, and a gate over a heading nobody collects is a contributing guide enforced by continuous integration. Writing the reader down on the entry is what keeps the test applied rather than remembered, and it is also what a refusal names — a body handed back with nothing saying who was waiting on the section leaves the author guessing |
| Whether a section can be required with no way to answer *nothing* | **No; `nothing_needed` is on every entry** | A required section whose only passing form is content turns every change needing nothing into a change that has to invent some, and what the body then carries is a sentence written to satisfy a gate. The answer also has to be the *whole* of the section: a body stating it and then listing work has said both things, and the collecting role would have to choose |
| Whether the open-items section belongs in the facet | **No** | It is required of every body with no key that turns it off, and an entry here is one a project may stop stating. Carried here, the rule would become configurable — which the rule's own precedence refuses. Its heading stays with the gate that reads it, and what the two gates share is the grammar for finding a section in a body rather than the heading |

⚠️ **The headings are the repository's language and not the tracker's**, which is visible in the
example that states two: its items are written in one language and its repository in another, and
the body is a repository artifact. A heading transliterated out of the tracker's language matches
nothing a body carries.

⚠️ **This repository requires no section and that is not a hole in the evidence.** Nothing here is
deployed and no role collects a section out of a change, so `body_sections` is `[]` and the gate is
installed nowhere in this tree — which is the facet's own stated absence rather than a project
standing down. What exercises the rule is the checker's planted bodies, and what exercises the
install is a fixture built from the example that states a section, with the generated workflow and
its registered entry then handed to the drift check that holds every other entry here.

## The surface a tree is held to, and the guards that went quiet in a configured project

The facet above is also what measured this one. Within a day of the body-sections key landing on
the integration branch, a session working a different item in its own tree could run no guarded
command at all: every call it made came back with three of the four guards reporting that the
project's configuration could not be read and the command held to nothing, and any role that read
the configuration exited naming `body_sections` as a required key. The project that produced those
messages had written the key — on the integration branch, in the file every adopter writes.

**Two copies of this surface can answer the question, and nothing had decided which one does.**
Measured 2026-10-24:

| | Where it came from | Which commit |
|---|---|---|
| The reader and this surface | the installed plugin's path, which a user-scope install points at the primary checkout | the integration branch |
| The configuration it resolved | the skills root, which § 1 rules is the directory the role ran in | the tree's own branch |

So the newer surface was holding an older configuration to a key the older branch had never heard
of. The skew is one-directional through the reader and that is worth stating, because it bounds what
had to change: a key a branch *adds* loads against the installed surface — tested, with an invented
top-level key accepted by the reader and reddened only by the single-source gate on the host — while
a key the installed surface newly *requires* refuses every tree cut before the marker.

**Why the tree's surface wins rather than the primary checkout's configuration.** Three rules would
each have cleared the measured failure, and they are not equivalent:

The third is what the surface now states —
[`schema.md § 1 → The surface is resolved beside the configuration`](../plugins/mjolnir/config/schema.md#the-surface-is-resolved-beside-the-configuration).

| Candidate | What it does to the measurement | Why not |
|---|---|---|
| Fall back to the primary checkout's configuration where the skills root has none | nothing — the configuration is tracked, so every tree has a copy and the fallback never fires | It also answers a question already ruled: a carrier searching outward acts on another project's facts in a directory that states none |
| Resolve the configuration from the primary checkout always | clears it, the integration branch carrying the key | A branch changing this surface could then never be tested in its own tree, which is how every item that changed it was built. The configuration under work is the tree's |
| Resolve the **surface** from the skills root where it ships one | clears it, and keeps the configuration where § 1 puts it | — |

⚠️ **The asymmetry is the whole of the rule**: the configuration is the statement a branch is
making, so it stays in the tree; the surface is what that statement is held to, so the half under
work has to be the one in the tree as well. Resolving both from the primary checkout and resolving
neither are the two symmetric answers, and each reproduces one direction of the failure.

### The direction the bound above does not state: a new surface read by an old reader

The bound above says the skew is one-directional and that a key a branch *adds* loads against the
installed surface. ⚠️ **That clause predates the rule beside it.** With the surface now resolved
from the tree, a key a branch adds is held by the **tree's** surface and read by the **installed**
reader — a third combination, and it reproduces the same failure the section opens with.

Measured in the change that added § 23. The new key's value is a list, and its membership was first
written as an alternation beside the key. An alternation marks what a *value* may be; the value of
that key is the whole list — so the installed reader, which has no rule telling the two apart for
this key, compared the list against the members and refused the configuration. Four guards then
reported the project's configuration as unreadable and held the command to nothing — the spend one,
the live one, the context one on both of its events, and the enforcement one — on every call, for
as long as the branch stood. ⚠️ **The outward guard is absent from that list and was not spared
either**: it answers only on a write leaving the project, so a session making none hears nothing
from it in the ordinary case — the same silence from a different cause, which is why the count is
four rather than every hook installed.

⛔ **What fixed it is the surface writing a list's membership as the list**, which is the shape
[`schema.md § 9`](../plugins/mjolnir/config/schema.md#9-day-log)'s streams and exclusions already
had and which [`schema.md § 23`](../plugins/mjolnir/config/schema.md#23-session-bookkeeping--which-thirds-a-project-runs)
now states as a rule rather than a habit: a membership written that way is **unread** by a reader
older than the key instead of misread by it, and unread is the direction that fails safe. The
reader derives the two facts apart, and a refusal names which of them is missing.

⚠️ **What this does not fix is the class.** Any rule a new surface states and an older reader
performs differently reproduces it, and nothing compares the two copies: the installed reader's
version is not a fact this repository's gates can see. The remedy that generalises is the one above
applied as a habit — a new surface statement that an older reader will *not* read beats one it will
read wrongly — and the cost of getting it wrong is bounded to a branch's own work tree, since an
adopter has no second copy of the surface at all.

⚠️ **An adopter is unaffected, and that is a property of the test rather than a case handled.** A
project that consumes the plugin carries no copy of this surface, so there is nothing for the
resolution to find and the installed copy is read — the behaviour that existed before the rule. The
two answers also coincide for the shipping project's own primary checkout, that root and the
installed path being one directory, which is why the suite's assertion about this repository holds
the resolution's *report* rather than a difference it cannot produce here.

**What the rule found once it was enforced: ten shape rules answering a question that was not
theirs.** With the surface resolved from the tree, the measured configuration still would not load —
the reader's own type rule for the key refused its absence, independently of any marker. The
division had been stated in the comment beside that rule and not performed by it:

| Question | Whose | Where |
|---|---|---|
| Is the key written at all | the surface's `# required` marker | checked in `validate` before any shape rule runs |
| What a stated value has to be | the shape rule | the reader, per section |

A rule that refuses absence states the marker's fact a second time, and the second statement
outlives the first in exactly one place: a tree whose surface does not mark the key. Ten of them did
it — every list-valued and block-valued required key on this surface. The assertion that found them
is over the marked set rather than a list in the test, so a key that grows a shape rule is covered
the day the surface marks it.

⛔ **What the silence cost is the reason this is a correctness rule and not a convenience.** A guard
that cannot read a configuration fails closed and says so, which is right. But *held to nothing* and
*this project configured nothing* are the same two lines to whoever is reading them, and three of
the four guards produced the first while the project had written every one of their keys. Nothing
reported the version skew as a skew. The rule removes the state, and naming the resolved surface
among what a role reports is what makes the remaining case visible at the moment it happens —
[`schema.md § 1 → The surface is resolved beside the configuration`](../plugins/mjolnir/config/schema.md#the-surface-is-resolved-beside-the-configuration).

## The bookkeeping role: three copies that are a third of it, and two keys that came out of it

This role divided in two directions at once, and this is the one place the copies are counted.
**Four projects carry it whole; three further copies are its commit third alone**, under two other
names and two different carriers — one a skill, one a command — which is the *one name, a subset
role* case [above](#name-and-role-diverge-in-both-directions) and the reason the inventory key is
*(role, carrier)* read out of the body rather than the directory name. ⚠️ **No superlative is
claimed for the figure**: the day-log role's five copies carry their own argument for extraction a
document over, and a *most* stated in two places is the restated fact this document keeps catching.

What that forced is a key naming which thirds a project runs, at
[`schema.md § 23`](../plugins/mjolnir/config/schema.md#23-session-bookkeeping--which-thirds-a-project-runs),
and ⚠️ **the load-bearing observation is which reading it rules out**: the measured
commit-third-only project **has a tracker**. So the question is not derivable from the tracker axis,
from the carrier axis, or from anything else already on the surface — a project with a board and a
backlog can still have a bookkeeping carrier that commits and does nothing else, and that is a
configuration rather than an adoption that stopped halfway.

The order the thirds run in is procedure and not part of the key, and ⚠️ **the reason is one the
copies agree on without any of them stating it** — which is why the rule is on the surface at
[`schema.md § 23`](../plugins/mjolnir/config/schema.md#23-session-bookkeeping--which-thirds-a-project-runs)
and the observation is here: no copy had to be overridden to reach it, so there was no divergence to
rule on, only a sequence every copy already ran in.

### Staging is per role, measured inside one project

The first form of the staging ruling made `staging` a project-level value. It is wrong, and the
counter-example is one project holding both positions **in two of its own carriers**:

| the carrier | what it states | why it is right there |
|---|---|---|
| its bookkeeping copy | stage everything, no exceptions, and do not edit, format, reorder or fix any file | the person asked for the tree as it stands, and an unstaged file is simply missing next session |
| its finishing role, same repository | never stage everything; name the paths you intend, and watch for credentials and build output | that commit rides an item's branch into a pull request, where a swept-in artifact lands with it |

Neither is a mistake, so a single value cannot express that project without making one of its two
roles wrong — and the ruling as first written would have picked one of them. The revised key is
[`schema.md § 6 → What staging is per`](../plugins/mjolnir/config/schema.md#what-staging-is-per-and-the-two-rules-that-hold-regardless),
with one entry per role that commits.

⚠️ **What the split does not touch is the pair of rules that hold regardless**, and the strict copy
of the `all` position is the evidence for that rather than against it: it names a credential file
outright. So `all` is *no path filtering* and has never been *no scanning*, which is the distinction
a per-role key has to keep and the one a reader skimming two opposite instructions would lose.

### A save is owed at a compaction boundary, and nothing delivers one

A window is summarised without being asked, long before a session ends, and what the summary dropped
is unrecoverable from inside the session — the measurements are
[above](#the-window-is-a-resource-the-loop-spends). That makes a compaction a save point like any
other, which is
[`schema.md § 23 → When a save is owed`](../plugins/mjolnir/config/schema.md#when-a-save-is-owed-and-the-boundary-it-names).

⚠️ **The mechanism that would have handed the role that boundary is unavailable, and the limit is
recorded rather than designed around.** The event that fires before a window is compacted is one of
two that **never fired** in the measurement that built
[`schema.md § 7`'s table](../plugins/mjolnir/config/schema.md#what-a-hook-can-establish-about-the-role-it-is-running-under),
so what it carries is unestablished and a rule resting on it would be written against a measurement
nobody has taken. The role therefore takes the boundary when it notices one, the artifact names
which boundary it was, and the cost — a compaction nobody saved before costs the window — is stated
on the surface instead of being discovered by whoever loses one.

⚠️ **Two of the item's acceptance bullets split at exactly that line**, one of them decidable and
one of them only decidable as far as the artifact's fields. Which end of that split the carrier
holds, and what it does not reach, is the reach of a check and belongs where every other check's
reach does —
[`docs/single-source-of-truth.md`](single-source-of-truth.md#the-bookkeeping-roles-two-derivations-and-the-round-trip-that-is-the-resumability-arm).

## The memory store is derived from the working directory

The memory third of the bookkeeping role was the one third of it with no store on the surface at
all. What it writes to was found by reading the memory step of every copy that carries one and by
asking where the store this project itself refreshes lives, and the answer is the reason the facet
is not a path key:
[`schema.md § 25`](../plugins/mjolnir/config/schema.md#25-the-memory-store-and-the-tree-a-save-may-refresh-it-from).

### What the copies' memory steps say, read rather than assumed

Every copy that carries the role whole carries a memory step, and the four of them were read
against each other. ⚠️ **They agree on more than the surface needed and disagree on exactly one
thing**, which is what decided the facet's shape:

| what was read | how many copies | what it decided |
|---|---|---|
| the store is the agent harness's own per-project directory, named after the **absolute path of the checkout** | all four, each writing that path out in full | `derived` is the measured case rather than a hypothetical one, and a path key alone would not describe any of them |
| the shape is one file per fact plus an index file loaded at session start | all four | `index` names a real file rather than an invented one, and the index's own line format is each project's |
| the index line is written `- [Title](file.md) — hook` | all four, identically | the carrier takes the line as given: the format is the project's and is not the toolkit's to state |
| delete a memory the day it is proved wrong, because a stale one is asserted with the same confidence as a true one | two of the four, one adding that the project *has been bitten by exactly that* | the read-time half of the rule was already somebody's practice, and § 24 had already taken it |
| prefer recording the measurement over the conclusion — a memory saying *X is slow* rots in a way one carrying the figure and the date does not | one | **the write-time half, invented independently**: this is `provenance` and `premise` in prose, and it is the strongest evidence the entry form has |
| the tree hazard, at all | **one of the four** | the hazard is real and is not generally known: three copies of the same step, on the same harness, say nothing about it |

**The one copy that does state it states it twice, and the second statement is a repair rather than
a rule.** It carries a standing instruction to run the role from the main checkout, and a
script that **symlinks each worktree's derived directory to the checkout's**, with the diagnosis
written out in the script's own header: the harness derives its per-project directory from the
working directory, so a worktree session gets one with no store in it — no index is loaded, and
anything saved lands where the main checkout never reads it.

⚠️ **That repair is what `carrier: path` is for, and not what `derived` plus `any_tree` is**, which
is worth being exact about because it is the first question the refusal at
[`schema.md § 25 → write_from`](../plugins/mjolnir/config/schema.md#write_from-and-the-pair-of-outcomes-a-refusal-is-one-half-of)
raises. A project that has linked its trees' directories has *made the store pinnable*: it names
that one path, every tree writes it, and the link is how the harness's own loader comes to agree
with the pin. The refused pair is the other case — a project that has done nothing, where *wherever
the session is standing* really is a different store.

**The measurement in this repository**, which is the copy that has done nothing and is therefore
the one the `derived` arm is written from. The agent harness keeps a per-project directory and
derives its name from the **absolute path of the working directory**. At the time this was read the
harness held five such directories for this one repository — the primary checkout's and one for each
of four worktrees cut from it — and the store existed under the checkout's alone. The other four
carried transcripts and no store. So a session standing in a tree had: no index to load, and nowhere
a save would write that the checkout would ever read. Nothing announced either half; the save
reports success.

| what was measured | what follows |
|---|---|
| five per-project directories for one repository, one per working directory | the store is a function of where the session stands, not of which project it is |
| a store under the checkout's directory and under none of the four trees' | a session in a tree loads no index and writes where nothing reads |
| nothing in either half says so | the hazard is silent, which is what makes it a rule rather than a caution |

**A moved or renamed checkout is the same failure without a tree**, which is why the facet is not
scoped to the worktree branch model: the derived name changes with the path, and the old store is
orphaned.
[`schema.md § 24`](../plugins/mjolnir/config/schema.md#what-a-load-may-not-assume-survived)
already lists a moved checkout among what a load must not assume survived, and this is what it
breaks. A store outside the tree is also outside `.gitignore`, so the argument that two copies are
safe where both are ignored does not reach it — these facts are neither committed nor ignored, and a
reader assumes a project's memory is in the project.
[`schema.md § 25 → Why a project cannot simply be told to write a path`](../plugins/mjolnir/config/schema.md#why-a-project-cannot-simply-be-told-to-write-a-path)
is where all three of those land.

### Why two carriers rather than one path key

The obvious shape — a path every project writes — was tried against this project first and does not
survive it. The store this repository refreshes is the harness's own derived directory; a path
written in the configuration would create a **second** store, one the procedure writes and the
harness's own machinery ignores. That is two records of one thing allowed to disagree, which is the
defect the whole toolkit exists to delete, so the honest value for a project in that position is a
statement that the harness decides and the procedure must not guess.

What the two carriers buy is therefore different in kind rather than in degree, and the table at
[`schema.md § 25 → The carriers`](../plugins/mjolnir/config/schema.md#the-carriers-and-what-each-of-them-closes)
is the comparison: a pinned store closes the hazard by construction and owes the project one thing
to keep true, while a derived store closes nothing by construction and has its two open halves
reported instead. Neither is the better configuration in general; which one a project gets is a
property of where its store already is.

**Why the absent case is a carrier and not a null path.** The first form of this facet made the
block optional — written where `session.parts` names the third, refused where it did not. It is
wrong for a mechanical reason found by this repository's own gate: every configuration here is held
to carrying every top-level key the surface declares, so an optional block is a block three of the
five shipped examples could not write. The absent case is therefore `carrier: none` with a reason,
exactly as every other facet's is, and what keeps that from being a second statement of the thirds
list is that the reader refuses every disagreement between the two —
[`schema.md § 25 → The carrier and the third have to agree`](../plugins/mjolnir/config/schema.md#the-carrier-and-the-third-have-to-agree-in-both-directions).

⚠️ **A second mechanical finding, recorded because it decided a key's shape.** `write_from` was
first marked `# default: main_tree`. A marked default is applied by creating whatever blocks it
needs to land in, so the default wrote a `memory` block into every project — including the shipped
collection example, which then stopped loading, naming a store it does not configure. No key under
this block carries a default, and the reason is that rather than a preference about defaults.

### What a refusal buys over a convention

The standing practice before this facet was a rule held in one project's prose: run the bookkeeping
role from the main checkout and reach into the tree with an explicit path. It is correct and it is
unenforceable, which is the shape this toolkit replaces everywhere else. `write_from` is that rule
made a value, and the thing it buys is the **pair of outcomes** at
[`schema.md § 25 → write_from`](../plugins/mjolnir/config/schema.md#write_from-and-the-pair-of-outcomes-a-refusal-is-one-half-of):
either the one store was written, or the third refused and the reply names it. A third that quietly
wrote nothing reads exactly like one that wrote.

**Which working directory a session is standing in is read from git and never from the
configuration**, and that is the part worth recording: § 1 resolves a work tree against that tree's
own files, so a session in a tree resolves the *tree* as its skills root. Comparing a working
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

⚠️ **The measurement that decided how that is tested.** The obvious assertion — many sessions
writing at once, every entry still present — **passes with no lock at all**: twelve processes each
appending one short line kept all twelve lines with the `flock` call removed. So the outcome arm
does not reach the mechanism, and a second arm holds it directly: with one process holding the lock,
a second writer must wait. That one is the single assertion that reddens when the lock goes. The two
arms and what each reaches are in
[`docs/single-source-of-truth.md`](single-source-of-truth.md#the-memory-store-the-write-decision-and-the-two-arms-on-the-index).

### Write-time admission, and the half a reader cannot recover

A store's failure mode is not only where it is but what gets into it. The published work on agent
memory names a poisoned store as a defect class whose sound defences are **admission at write
time** — what may be committed, with what provenance — and a **re-check at read time**, and names
prompt-level filtering of a store that is already wrong as repeatedly insufficient. A store whose
only policy is *the save writes it* has neither.

⚠️ **And one of the surveyed copies had already reached the write-time half on its own**, in its own
words: prefer recording the measurement over the conclusion, because a memory saying *X is slow*
rots in a way one carrying the figure and the date does not. That is this rule arrived at from
inside the practice rather than from the literature, which is the same convergence the extraction
argument rests on [above](#the-strongest-argument-for-extraction-is-not-borrowed) — and it is why
the form asks for the source and not only for a label.

So the entry form carries the fact, its provenance, what it was established from, and the premise it
rests on, and the admission runs before anything is written:
[`schema.md § 25 → What may enter the store`](../plugins/mjolnir/config/schema.md#what-may-enter-the-store-and-what-a-reader-does-with-what-is-in-it).
Two of those four earn their place from a direction this surface already names: a recalled fact
reflects what was true when it was written
([`schema.md § 24`](../plugins/mjolnir/config/schema.md#24-session-restore--the-readings-a-pass-is-resumed-from)),
so an entry that does not say what would falsify it obliges its reader to invent the check — and a
repeated fact rendered identically to a measured one becomes a measured one by being read twice.

⚠️ **What the rule reaches is the entry's shape and not its truth**, and the split is stated rather
than implied: that a fact carries its provenance and its premise is decidable, and whether the
premise still holds is read against the tree by whoever reads the fact. `asof` was considered for
the form and left out for that reason — a date says when a fact was written, not whether it is still
true, so it would answer staleness with a number that reads like an answer.

### What the admission costs a store it cannot reach

⚠️ **Measured in this repository, which is the only project here that runs the memory third and the
copy the `derived` arm was written from.** The admission is held by the one command that places a
fact in the store, and under a derived carrier that command composes no path and writes nothing:
handed a complete entry it answers that there is no directory for it to write a fact into and no
index for it to lock. So every entry in that store is in the harness's own shape — a leading YAML
document carrying a name, a one-line description and a subject label, then the fact as prose — and
not one of them has been through the rule.

The consequence is a **third** cost rather than a restatement of the two the carrier already
reports, which is why the table at
[`schema.md § 25 → The carriers`](../plugins/mjolnir/config/schema.md#the-carriers-and-what-each-of-them-closes)
now names three:

| what the derived arm leaves open | what it costs |
|---|---|
| the index's contention | work somebody did is lost, two concurrent rewrites of one file clobbering each other |
| a moved or renamed checkout | the store is orphaned, and the old one is never read again |
| the admission it cannot reach | every fact in it is unprovenanced and uncheckable, **while reading exactly like a fact that carries both** |

⚠️ **The read-time check met the same wall from the other side.** A reading written for the entry
form alone refuses a store-shaped entry as a file that is not one YAML document — true, and it tells
its reader nothing about what they are holding. Three rules were added for the store a project in
this position actually has, each failing in the direction that under-claims:
[`schema.md § 25 → What a reader does with a store whose admission never ran`](../plugins/mjolnir/config/schema.md#what-a-reader-does-with-a-store-whose-admission-never-ran).

⚠️ **And the one mapping a reader would reach for is the one that must not be made.** The leading
document's subject label says which part of the project a fact is about; a provenance is an evidence
class. Reading the first as the second makes every fact in the store *measured* by construction,
which is the precise failure the provenance field exists to prevent — so no key of a foreign shape
is read as a field of the form at all, and a document that happens to carry the form's own fields
inside such a shape is still read as stating none.

### Reporting a fact stale rather than restating it

The read-time half [`schema.md § 24`](../plugins/mjolnir/config/schema.md#24-session-restore--the-readings-a-pass-is-resumed-from)
already stated — a recalled fact is checked or reported unchecked — had nowhere to put the answer. A
reading that can only ever say *unchecked* renders **nothing checked it** and **checked, and still
true** identically, and a fact whose premise has gone has no way of being reported at all except in
the prose of whoever happened to notice.

[`schema.md § 25 → The standing a recalled fact is reported under`](../plugins/mjolnir/config/schema.md#the-standing-a-recalled-fact-is-reported-under)
is where that lands: three standings, the premise's answer supplied by the reader rather than by the
entry, and *current* over an entry stating no premise **refused** — there was nothing to check, so
an answer that it holds is an assertion about the fact rather than a reading of it.

⚠️ **What this reaches is which of the three was reported and not whether the answer is right**,
which is the same split the admission itself carries: a wrong reading of the premise against the
tree is wrong here too. What it buys is that the three are told apart at all, and that the status a
caller reads keeps a stale fact off the one a current fact gets — a stale fact sharing that status
being the restatement the whole rule is against, read off the status alone.

## The day log's destination port

The destination was on this surface from the start, and as one key: a directory, in the section
that measures a day. That is the shape
[`schema.md § 26`](../plugins/mjolnir/config/schema.md#26-the-day-logs-destination-port) replaced,
and what follows is the argument it was replaced on rather than a second statement of the rule.

**The surveyed copies all wrote a file**, which is why nothing in the original survey put this in
tension: a directory addresses a file store completely, and a single implementation needs no
contract. What moved it afterwards is below, and none of it is about files being insufficient.

- **The store is read back, and not only written.** § 9's own cross-day validation already reads
  every recorded day, and against a directory of per-day text files that is a filename convention
  the surface never stated. ⚠️ **A second reader is proposed and not built** — the role that takes
  a period's line items out of the same store is in
  [`divergences-and-rulings.md`](divergences-and-rulings.md)'s still-open list — so what carries
  this is the reader that exists, with the proposed one as the reason the shape has to admit
  another. An operation with a stated absent case is what already answers this everywhere else
  here.
- **The grain of the two values differs by consumer.** Hours aggregate across days and a
  description does not, so the store has to be readable for hours over a range without the
  descriptions being what is read — which a store addressed as *a directory of entries* cannot
  express and an operation can.
- **A store that is not a file has no directory.** A spreadsheet, a document or a worklog is
  addressed by an identifier and a tab, and the artifact store's own `dir`
  ([`schema.md § 11`](../plugins/mjolnir/config/schema.md#the-store-and-when-an-in-tree-store-is-safe))
  cannot carry one either.
- **The day-log role's own rules were written in one carrier's vocabulary.** *A redo deletes the
  file and writes a new one* is how a **file** is rebuilt whole; a spreadsheet row is replaced, and
  a store with no delete would be patched in place — which is the thing the rule exists to forbid.
  The rule was right and its statement was not portable, which is the diagnosis that makes this a
  port rather than a second key, and the same reading reaches every other place that skill said
  *the file* where it meant *the entry*.

### The section a port's operation list is read from had to become a parameter

⛔ **The contract finds an operation list by its table's column headers and refuses a second one.**
Measured, by appending a second table with those headers to the surface and asking the contract for
the list: it came back refused, with the operation list stated more than once and the tables free to
disagree. That refusal is correct, and it is also what made a second port impossible while the
section the contract read was a constant —
[`schema.md § 26 → Which section`](../plugins/mjolnir/config/schema.md#which-section-a-ports-operation-list-is-read-from)
is the shape that resolved it, and the alternative it was chosen over was a sibling module.

⚠️ **A second copy of the contract per port was the obvious move and is the worse one.** A copy is
a second place a fallback could be defaulted, which is the defect the contract's own docstring
exists to refuse — so what is parameterised is the lookup, and a port is three facts carried by one
marker on the line stating its kind.

⚠️ **The marker's own limit is stated rather than discovered**: two near-miss spellings come back
**dropped** rather than refused — a clause that lost its colon, which is indistinguishable from
English prose, and a capitalised keyword, matched case-sensitively like every other clause there.
⛔ **What catches a marker lost that way is the contract and not the reader**
([`schema.md § 26 → Which section`](../plugins/mjolnir/config/schema.md#which-section-a-ports-operation-list-is-read-from)):
its section's table then belongs to no port, which is refused as an operation list nothing reads.
⚠️ **The reader's own inventory comparison catches it only where the surface is left declaring no
port at all** — with another port still declared the inventory is non-empty and that comparison is
silent, which is why the comparison is written out rather than derived but is not what holds this.

### Where the directory went, and why it is still not required

The directory key moved under the kind it was always addressing —
[`schema.md § 26 → What each kind`](../plugins/mjolnir/config/schema.md#what-each-kind-of-destination-block-carries).
⚠️ **It is deliberately still unmarked**, which is the position § 3 already takes on the three
state-mapping keys in its own per-kind blocks and for the same reason: whether a project needs a
destination at all is the carrier axis's question, so an absent directory is a decision this reader
cannot tell from an oversight.

⛔ **What makes that safe rather than lax is that the reader reports it**, which is the route an
unset evidence script already takes: a project mapping the day-log carrier and stating no directory
for the file kind gets the key in `unavailable`, and the role says what it could not record —
[`schema.md § 11 → A report names what it could not establish`](../plugins/mjolnir/config/schema.md#a-report-names-what-it-could-not-establish).

⚠️ **The conditional marker was measured and rejected here.** The kind defaults to the file kind, so
a condition on that kind fires for every configuration — including one that writes no `day_log`
block at all, which the reader's own defaults create on the way past. Marking the directory
conditionally required would therefore refuse a project that maps no day-log carrier, which is the
one project certain not to need it.

### The grain, and the address

⛔ **One entry per day per project**, which the skills root already decides rather than this port
adding anything —
[`schema.md § 26 → One entry per day`](../plugins/mjolnir/config/schema.md#one-entry-per-day-and-the-day-belongs-to-one-project).
The alternative considered was one entry per day across projects with the project named inside the
entry, and it loses to a rule the day log already carries: the entry is the two values and nothing
else, which a project name inside it would be the first thing to break. ⚠️ **A shared timesheet is
the first store two projects would write to**, and it is answered by the store partitioning rather
than by the entry growing a third value.

⛔ **A destination block carries an address and never a credential**, which is why this surface
declares no key for one —
[`schema.md § 26 → The store's address`](../plugins/mjolnir/config/schema.md#the-stores-address-and-what-may-not-be-written-beside-it).
⚠️ **That is a stated bound on what may be added here rather than a hole in what is**: the file kind
needs no secret, so nothing shipped is waiting on it, and a kind that cannot be reached without one
is a kind this surface cannot state until private values have a home.
