# Why the build half of the surface says so little

The single statement of every rule and flow is
[`../plugins/mjolnir/config/schema.md`](../plugins/mjolnir/config/schema.md); this document states
none. It is the build-half counterpart of [`configuration-surface.md`](configuration-surface.md),
which derived the process axes by reading every copy of every process role: this one was derived by
reading what each of the six projects **builds, checks and deploys with** — every workflow file,
every manifest and lockfile, every command definition, every deploy script, and the passages of the
instructions files that state when a verdict counts. The findings below are measurements rather
than preferences, and each one names the schema section or the work item it bears on. ⚠️ **Two
other kinds of sentence appear and are told apart on sight**: a **conclusion a measurement forces**
about a facet's shape, which is written as the measurement and then the shape it rules out; and a
**preference**, where a measurement leaves two honest options — each of those is labelled where it
stands.

Projects are referred to as A–F, as they are there. Naming them is forbidden here, and the counts
are what carry the argument anyway.

**What this document is for.** Three facets that touch this axis were each written from one
project: the local verdict and its conditions, the command root, and the tiers a host cannot run.
A facet shape is cheap to write and expensive to migrate off, so the shapes are read here against
six stacks before the migration meets them.

## A verdict is a command, a root, and a condition

The entry point whose exit status is a verdict, and the directory it runs in:

| | what produces the verdict | the root it runs in |
|---|---|---|
| A | a Python runner mirroring every pull-request job, plus `make lint` and `make e2e` | two: the client repository the runner lives in, and a directory **inside a running container** — both reached from a parent checkout that holds none of the code and is where the invocation is made |
| B | `./gradlew build` with four exclusions, `./gradlew detekt`, and a Flutter task behind a Gradle one | the code root only |
| C | `npm run` per script — `lint`, `format`, `check`, `lint:styles`, seven `test:*` suites | two package roots; the code root has no manifest and runs nothing |
| D | `./gradlew detekt test`, stated as the gating rule | the code root only, where one module's `test` task shells out to npm |
| E | `./gradlew detekt test`, `ruff check <tree>`, `pytest` | the code root, plus one package root for `pytest` |
| F | `./gradlew detekt test --no-daemon`, `ruff check <four trees>`, `pytest` by marker, a docs script, `bash -n` and shellcheck | the code root only, every command taking paths as arguments |

**Three of six run a verdict command somewhere other than the code root — A, C and E — and one of
the three has no command valid at the code root at all**: C, whose instructions file states that the
root carries no manifest and that npm cannot run there. That is the shape
[#61](https://github.com/ragnor-rs/mjolnir/issues/61) was written from, and reading C again confirms
every clause of it: two package roots, each with its own manifest, `lint` and `format` present in
**both** and meaning different things, and the test runner in one root with the type checker and the
style linter in the other. E is a second instance in a different language pair — a JVM build at the
root and a Python package root whose suite the host workflow reaches by setting a working directory.

**The root A's linters run in is not a directory of any checkout.** Its lint targets and its local
runner both reach their tools through a container exec, and the directory they pass is a path
inside the image, named after the theme it holds; the container is identified by a name read out of
an environment file rather than written down. #61's shape — a command root whose `path` is relative
to the code root — cannot state that root. Its `invoke` field can, which is where the amendment
belongs: a command root is **how a command in it is run**, and only sometimes a directory.

**In A the root decides the verdict rather than merely locating it.** Its instructions record that
running the linter from the theme directory does not reproduce the pull request's finding, and that
only the host's own invocation does — from the repository root, with the configuration passed
explicitly and plugins resolved against the theme. A local pass obtained the other way is not the
same claim.

**One command name is a verdict in one root and work in the other.** In C, `npm run lint` is
`eslint --fix` in one package root and a pure check in the other. Its own guard against duplicating
the host's checks declines to classify it for exactly that reason, and says so: telling the two
apart needs a path heuristic more fragile than the duplicate run it would prevent. A facet that
states a command per root without stating whether that command *judges* or *changes* the tree
cannot express this, and
[`schema § 13`](../plugins/mjolnir/config/schema.md#13-what-counts-as-done--an-ordered-check-list-and-who-answers-each-check)
is where the distinction matters, because a `done:` check reads a verdict.

## What a pass does not prove: six shapes, in five projects

[#66](https://github.com/ragnor-rs/mjolnir/issues/66) names two of these and records both as
measured in one project. Across six stacks the shapes are:

| the shape | where | what defeats it |
|---|---|---|
| a **replay** — the build reports work it did not do | D and F both switch the build cache on in a properties file; D's stated gating command names nothing that defeats it, and the only such flag on F's host command is one whose subject is the build *daemon* rather than the cache or the incremental state. ⚠️ Read from the configuration: neither was executed twice to watch a second run skip the work | not a flag: the cache and the incremental state, each named |
| a **suite that never ran** — its dependency was absent and skipping is correct | B, four suites gated on one environment variable, three of them over its money rules, which ran nowhere but one machine while the aggregate build reported success | the executed count, which is [`schema § 16`](../plugins/mjolnir/config/schema.md#16-what-a-run-executed-and-the-count-that-is-the-only-evidence-it-ran) |
| the **wrong root** | A, where only the host's invocation reproduces the finding | the root, as above |
| the **wrong tree** | A, whose runner derives the container name per checkout, because a constant sends every exec to whichever stack holds the default name — the linters then report on another branch and exit zero | [`schema § 10 → Which tree a verdict belongs to`](../plugins/mjolnir/config/schema.md#which-tree-a-verdict-belongs-to) |
| a command that **repairs what it judges** | C in both roots (`--fix`, `--write`), A in three targets, and C's host workflow runs the rewriting form and reports the diff | nothing in the facet today |
| a **deploy** that replays | A: a named volume over the content directory is seeded from the image only while it is empty, so every stand deploy pulled a new image and served the old code until an entrypoint was made to copy it in on each start | emptying the volume — a state to destroy, not a form of a command |

**The last row is why `invalidate:` cannot be a form of the command.** #66's field is described as
the form that defeats a cached or incremental pass. Two of the six measured staleness defeats are
not forms of anything: a volume that has to be removed first, and a generated source tree that has
to be rebuilt before the type checker is believable (C compiles its message catalogue in the
workflow step before the check). A string naming a flag cannot express either, and the facet's
`invalidate:` has to be **a command in its own right** — which the project has anyway, because
something already does it.

⛔ **None of that changes what the procedure may know**, by
[`schema § What the procedure models`](../plugins/mjolnir/config/schema.md#what-the-procedure-models-and-what-it-only-names-and-calls):
each of these is a command or a state the project names, and the procedure runs it and reads an exit
status.

## Preconditions a command does not check itself

Eight classes, measured. #66's `requires:` is described as a precondition a consumer can evaluate,
so what the class **is** decides whether that holds:

| what the command needs and does not check | where | can a consumer evaluate it |
|---|---|---|
| a container daemon, for suites that stand their own store up | D, E, F — three of six | yes, and all three host workflows state it in a comment instead |
| a **running container**, not merely a daemon | A, whose lint targets and local runner exec into the app container; its runner carries a predicate for exactly this | yes |
| a tool on PATH for an unrelated module | D, where the aggregate test task needs npm present even for a change that touches only the JVM side | yes |
| a generated source tree | C, whose message catalogue is compiled in the step before the type check | yes |
| an environment file | E, whose image build step copies the example into place first | yes |
| an environment variable read at collection | B (the gate on four suites), F (the suite's own refusal to run anywhere but one target) | yes |
| a credential | B (a user-account session for the bot suite, and a model quota), F (an account and a model credential), A (one password for every path on the stand) | only as presence, never as validity |
| a browser on the machine | A, whose acceptance run is deliberately not a container target | yes |

**A missing precondition is already reported as a third value in two projects.** A's runner records
a check whose tool is absent as a skip and exits 2 — *a check could not be run, which is not a pass*
— and its deploy-policy and suite-guard branches do the same for a missing interpreter. F's docs
gate reports one assertion as skipped because the tree it reads is not in the checkout, and the
script declines to call the run a clean pass. That is
[`schema § 11 → A report names what it could not establish`](../plugins/mjolnir/config/schema.md#a-report-names-what-it-could-not-establish)
arrived at independently, twice, and it is the behaviour #66 asks of an unmet `requires:`.

**No measured precondition is a version.** Eight classes across six projects, and every one is a
presence, a state or a credential. The one case where a version *is* a precondition nothing checks
is a defect rather than a fact a role reads: A's main line does not build because an image fails to
pin one tool against another's major version, which its own audit carries as a finding. That is
read by an image build, never by a role.

## Whether the host's verdict covers this code

**Four of six carry a probe that answers this before a local check runs, and the four answer in four
vocabularies.** Two of them are hooks that refuse the command; two are scripts a role reads.

| | the answer the probe gives | what it does with uncertainty |
|---|---|---|
| A | operational · BLOCKED · unknown | **runs the checks locally** — anything it cannot establish counts as "run them here" |
| B | four conditions, all of which must hold: a pull request exists, the workflow that *mirrors this command* ran, its head commit equals local `HEAD` with a clean tree, and nothing reports a startup failure | **fails open** — a needless local build costs minutes, and blocking the only available check risks shipping unchecked code |
| C | exit 0 covers · 1 does not · 2 the pull request is conflicted · 3 undeterminable | the hook blocks only commands that produce a verdict and change nothing, with a named override |
| F | a **reason** per unmet precondition, and only a blank reason means covered: the client is absent · this is not a git tree · there is no remote to ask about · the tree is dirty, so the host has never seen these edits · the head is unreadable · no run exists for this commit · the run's conclusion or status · how many steps its jobs executed | **stands aside** wherever a reason exists, and the local run proceeds |

**What makes these a facet rather than four habits is that the four agree on five facts, each of
which had to be learnt.** The mapping is on the **workflow name** and not the job name, because two
workflows in B call their job the same thing. A path-filtered workflow means "the pull request has
some live check" says nothing about the command in hand. An empty check list is not a pass: in C it
is usually a conflict, and in B a pending run exits non-zero from the host's own client, so reading
that exit status throws the answer away in exactly the state the question was asked for. The run
must be for **this commit**, which B reads as head-equals-`HEAD` and F as a run listed for the sha.
And a run that executed **no steps** is not an answer — F counts the steps of every job in the run
and treats the count as part of the question.

⛔ **Those five are
[`schema § 2 → Reading a run's answer`](../plugins/mjolnir/config/schema.md#reading-a-runs-answer-and-what-a-failure-is)**,
arrived at independently in four projects, one of which enumerates all four of that section's
preconditions — uncommitted work, a run for this commit, steps executed, concluded green — in its
own words. ⚠️ What none of the four states is the **remedy** on uncertainty, and the four disagree
about it: two run the checks anyway, one stands aside, one fails open. So the facet carries the
conditions and the project carries what to do when they cannot be established.

**One condition no probe can be written against today.** Three of C's four code checks, and its
type check among them, run only on a pull request whose base is a release branch — so for an
ordinary change into the main line the host runs one path-filtered formatter and nothing else, and
the local verdict is the only verdict there is. The condition is the **base branch**, which is a
property of the change rather than of the command, and
[`schema § 2`](../plugins/mjolnir/config/schema.md#2-code-host)'s `triggers` carries the event and
the base already; what reads it is the facet #66 is open for.

## The tiers, what each needs, and which are asked for

[#60](https://github.com/ragnor-rs/mjolnir/issues/60)'s four bullets were written from F, and its
five needs — host-runnable, a deploy, a credential, material, money — are offered as a vocabulary
for all six. Measured against six, each need holds in at least two projects:

| | tiers present | what the unrunnable ones need | asked for rather than automatic | refused outright |
|---|---|---|---|---|
| A | no unit suite at all; acceptance scenarios; a manual checklist | a running site, a browser on the machine, a password, and for some scenarios the app container | the whole acceptance run, which takes the site under test as a required argument | the writing scenarios against production, by the suite's own guard |
| B | unit; integration against a real store; a bot suite over a user account | a store the host supplies as a service; a deployed bot, a user-account session, model quota | the bot suite, in no workflow at all; and every measurement run on a server | one measurement environment, refused by name, because its quota is the one that caps throughput |
| C | one unit runner; seven suites against a store; live-model harnesses | a store the host supplies as a service | the live-model harnesses, which no workflow runs | — |
| D | unit and store integration, under one task | a container daemon | — | — |
| E | unit; store integration; route tests; an image build | a container daemon; a stack somebody brought up | the live-platform path, deliberately not automated | — |
| F | hermetic tiers on the host; an end-to-end suite; an evaluation set | a deployed stack, an account, a model credential, and indexed material | the evaluation set, about $3.65 a run against a finite budget | the end-to-end suite against production, because it writes to a real account |

**What the reading adds to #60 is how a tier is *selected*, which the facet does not state.** Three
mechanisms, and the difference is load-bearing:

- **by marker** — F's cases declare one of three markers for what they reach, and the host selects
  the complement; a case that grows a dependency on the world drops out by declaring a marker, and a
  list of file names would go stale silently in both directions.
- **by a named list** — B asserts that each of four suites produced a report with tests and no
  skips, by name, so a fifth gated suite is exactly as silent as having no service container.
- **by what the run found** — A's acceptance run skips the scenarios whose dependency is absent and
  **lists them rather than counting them as passed**; F drops the cases that need material, selected
  by the marker each carries rather than by name, when the index has not caught up.

So a partial run reports in two measured forms — skipped-and-listed, and dropped-by-criterion — and
the floor that catches the third case is already surface at
[`schema § 16`](../plugins/mjolnir/config/schema.md#16-what-a-run-executed-and-the-count-that-is-the-only-evidence-it-ran).
⚠️ **A preference, labelled:** of the three selection mechanisms, marker and named list are both
honest and the choice between them is a project's, so the facet should state *that a tier declares
how its cases are selected* and not which mechanism.

**A's whole suite is the one the surface would otherwise read as absent.** It has no automated unit
tier, its release trigger is manual because of that, and its coverage rule is a check over the
**diff**: a change in behaviour with no scenario and no register entry fails the local run. That is
[`schema § 15`](../plugins/mjolnir/config/schema.md#15-end-to-end-coverage-recorded) in use, in the
project whose host runs the fewest of its checks.

## What is pinned, and where

| | the build tool | the language runtime | the linters | a lockfile |
|---|---|---|---|---|
| A | none declared; a container image per service | by the host workflows' setup steps and by the images | by the two lockfiles the host installs from | both of the theme's, one per ecosystem |
| B | the wrapper's own properties file | a toolchain declaration in the build, and the one runtime-version file in all six projects | by the manifest's dependency versions | one, for the non-JVM module |
| C | none | by the host workflow's setup step and by the images | by each root's manifest | both roots |
| D | the wrapper, a major version ahead of B's | a toolchain declaration in the build | by the manifest | one, for the non-JVM module |
| E | the wrapper | by the host workflow and the images only — no toolchain declaration in the build | one installed unpinned in the workflow | none at all |
| F | the wrapper | a toolchain declaration in a convention plugin of its own | **pinned in the workflow, with the reason stated** | none at all |

**Six facts, each measured rather than reasoned.** Across six projects there is exactly **one**
runtime-version file of the kind a version manager reads — B's, for its non-JVM module. Everywhere
else a language runtime is an input to a host workflow's setup step, in five of the six, and in one
of those five it is stated **twice with two different values**, by two workflows in one repository
that install different major versions of the same runtime. **Four of the six run a JVM build and
none of them locks its dependencies**, so a build is reproducible to the versions its manifests
name and no further. F is the only project that pins its linters with an argument for doing so: an
unpinned linter reddens the build on a day nobody changed any code, which teaches people that red
means "try again". And A is the only one that pins the host's own actions by digest rather than by
tag, in every workflow step that uses one — fourteen references against none anywhere else.

⚠️ **The two-values case is what the non-goal ruling below has to survive, and it does.** Nothing
reads either value to decide what to do next, so the disagreement is invisible to every role and is
the project's own to settle inside the commands it already runs; a key would record the
disagreement without resolving it.

**Only one project states where a version string lives.** D carries a declared list of release
files — a pattern per file, with one marked optional — which is
[#36](https://github.com/ragnor-rs/mjolnir/issues/36)'s subject stated as configuration by a project
that has not adopted anything. A's answer is the opposite and equally explicit: the code is the
artifact, an image is a build product, and a deployment is identified by the commit it was built
from. The two are not in conflict — they are the two ends of #36's axis, and both were found rather
than designed.

## Where a deploy lives

[#13](https://github.com/ragnor-rs/mjolnir/issues/13) leaves the deploy script project-local and
expects a script. Measured, the shapes are three:

| | the deploy | the targets, and which are live |
|---|---|---|
| A | a dispatch of the host's own workflow — two of them, one per stand kind, plus a manual release procedure in a runbook | a stand and production; two older shared boxes, one being retired |
| B | one script with a required environment argument | five, of which three are production hosts with different roles; one target refuses two services and starts them stopped |
| C | a hosted build configuration with substitutions, and no script at all | two, by substitution |
| D, E | one script each, plus a host provisioning script beside it | one live target each |
| F | one script with a required environment argument, which **refuses the remote target by name** rather than half-attempting it | one implemented, one refused |

**What each resolves against is a second axis, and it is not the code root.** B's and F's scripts
take the environment as a required argument and resolve the host from a library beside them, so the
root they resolve against is a **target** rather than a directory; D's and E's resolve one target
each; C's substitutions are supplied by whoever triggers the hosted build. ⚠️ **A's resolves against
a ref, and the default is the wrong one**: the dispatch's `ref` input defaults to the integration
branch, so publishing the stand's branch has to name it explicitly, and the branch chooses which
image tag is published — one tag per stand kind, because one tag for both delivered a build to a
stand nobody had deployed to. So a deploy facet that assumed a directory would be wrong in six cases
out of six.

**So "a project whose deploy is one script keeps that script" describes four of six.** C has no
script to keep — its deploy is a configuration file a hosted service executes — and A's is a
workflow dispatch, which is the host's. ⛔ **Neither is a gap**, by
[`schema § What the procedure models`](../plugins/mjolnir/config/schema.md#what-the-procedure-models-and-what-it-only-names-and-calls):
a dispatch and a configured pipeline are both reached by a command, and what the facet needs from
them is the same thing it needs from a script. What it cannot assume is the *file*.

## The toolchain version is a non-goal, and the boundary is where that is stated

The question this item was opened to settle is whether a runtime or toolchain version belongs on the
surface. Run the boundary's own test — does any role read it to decide what to do next — against
everything the six projects pin:

- a build-tool version is read by the wrapper the project ships;
- a language runtime is read by the build's toolchain declaration, the host workflow's setup step,
  or the image;
- a linter version is read by the command that installs it, inside the mirrored command;
- a release file's version string is read by the project's own release step, which is #36's.

No role reads any of them, and the measured preconditions a command does not check for itself are
presences, states and credentials rather than versions — so a version is not a `requires:` entry
either. ⛔ **It is a non-goal, stated at**
[`schema § What the procedure models`](../plugins/mjolnir/config/schema.md#what-the-procedure-models-and-what-it-only-names-and-calls)
with the other facts a project's own command reads, and no key is owed for it.

## What the reading did not force

Stated so that the absences are read as results rather than as work left undone:

- **No new axis.** Every finding above lands on a facet that exists or on an open item for one.
- **No facet per stack**, and no tool, task name or flag of any stack enters a carrier's text —
  which is a search rather than a reading, and the search is #19's sweep, whose stack class is in
  force.
- **No second ordered list.** The conditions under which a verdict counts are #66's one facet, not a
  predicate list beside
  [`schema § 5`](../plugins/mjolnir/config/schema.md#5-readiness-gate--an-ordered-predicate-list).
- **The commands stay project-local.** Six stacks produced six command sets with nothing in common
  but their shape, which is the measurement behind that boundary rather than a preference about it.
