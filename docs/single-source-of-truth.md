# How the single-authority claim is held

[`../plugins/mjolnir/config/schema.md`](../plugins/mjolnir/config/schema.md) declares itself the
single statement of every rule and flow; this document and its sibling explain or record without
being a second authority. This document states none of the rules. It records what the gate
checks, which kind of check each one is, and what it deliberately does not check.

The check is `tools/check_single_source.py`, run by the `Single source of truth` workflow on every
pull request and every push to the default branch, and stated in this repository's own
`host.checks`. Every workflow here is named for the one claim it holds and carries a single job of
the same name, so the name `host.checks` is keyed by and the name the host reports as a status
context are the same string.

A second script, `tools/check_no_project_names.py`, holds that this repository names no other
project, and that nothing carrying procedure carries a value. It runs in its own
`Names no other project` workflow with its own `host.checks` entry, since an entry states one
mirrored command. It is recorded in [its own section](#the-second-sweep-naming-no-other-project)
below.

`tools/check_nothing_deferred.py` holds a claim about the change rather than the tree: that
nothing in it was deferred. It has its own `Nothing deferred` workflow and `host.checks` entry,
and is recorded in [its own section](#the-gate-on-the-change-nothing-is-deferred) below. It is
the one that reaches off the tree, and the one granted a token scope.

`tools/check_prose_width.py` holds the documents to the line width this project's configuration
states. It has its own `Prose width` workflow and `host.checks` entry, and is recorded in
[its own section](#prose-line-width-held-on-the-gate-for-files-and-nowhere-for-bodies) below.

`tools/check_no_audit_trail.py` holds that no artifact a change writes carries a record of the
pass that wrote it. It has its own `No audit trail` workflow and `host.checks` entry, and is
recorded in [its own section](#an-artifact-states-what-is-true-now-held-on-the-lines-a-change-adds)
below. Like the gate above, its scope is a **diff** rather than a tree, and it has no `push` arm.

`plugins/mjolnir/scripts/enforce.py` refuses an act in the session on the strength of a record
somebody else wrote, and holds a place on what a project says contends. What runs on the gate is
its assertion suite, in an `Enforcement` workflow with its own `host.checks` entry; it is recorded
in [its own section](#the-enforcement-half-a-guard-that-refuses-and-a-place-that-comes-back) below.

`plugins/mjolnir/scripts/spend.py` reads where a command *is* in a call and holds the ones a
project's own list says cost money, and reports the one price the harness states before a turn
runs. Its assertion suite runs in a `Spend guard` workflow with its own `host.checks` entry, and is
recorded in
[its own section](#the-spend-half-a-call-put-to-somebody-and-the-one-price-stated-beforehand) below.

`plugins/mjolnir/scripts/host_checks.py` is the one consumer of `host.checks`; its assertion suite
runs in a `Host checks consumer` workflow with its own `host.checks` entry. It is recorded in
[its own section](#the-hosts-own-runs-read-by-one-consumer) below.

`plugins/mjolnir/scripts/install.py` writes the toolkit's own artifacts into an adopting
repository; its assertion suite runs in an `Installer` workflow with its own `host.checks` entry.
It is recorded in [its own section](#the-install-half-what-the-toolkit-writes-into-a-project) below.

`plugins/mjolnir/scripts/check_reply_defers_nothing.py` holds that a role's reply names no work the
turn does not do; what runs on the gate is its assertion suite, a reply being the one artifact a
change does not carry. It is in
[its own section](#the-reply-defers-nothing-held-in-the-session-not-on-the-gate). A sibling that
held three properties of file prose is retired, with the ruling and the measurement in
[§ The file-prose floor, retired](#the-file-prose-floor-retired). No count of these scripts is
written down, here or anywhere: a count in prose is a copy, and goes stale green.

## Why this is a check rather than a convention

The procedure is described in the schema, in the README, in the documents under `docs/`, in each
shipped skill, and in the issue bodies, and only the schema is an authority. A rule restated in a
document, a section nothing motivates, a ruling pointing at a home its outcome has left: each
reads as fine in review, and each is the defect this repository exists to call a defect.

Instances the check exists for:

- `version` was in every configuration and declared nowhere in the schema. Read by nothing, it is
  **retired** at [schema § The file itself](../plugins/mjolnir/config/schema.md#the-file-itself).
- A ruling's outcome lived in the README, which stated the rule citing no schema section. It is
  [schema § 7 → Invocation](../plugins/mjolnir/config/schema.md#invocation), which the README
  cites. It is a subsection of the carrier axis rather than a numbered section, because every
  numbered section is a configuration facet opening with a `yaml` block and this is procedure —
  the same placement the authorship rule has under § 6.
- A ruling naming "the filing role's work item" or "the deploy role's work item" with no number
  leaves nothing able to resolve whether the outcome has moved. Numbered (#7, #13), both outcomes
  are now in sections of the surface.

## The three kinds, and why one of them is absent

The classification is [`schema.md § 38 → The three
kinds`](../plugins/mjolnir/config/schema.md#the-three-kinds-of-check-and-the-one-that-is-admitted-with-a-warning)'s,
read out of two independent implementations that reached the same conclusion: **computed** checks
derive the property and cannot be fooled by a reword; **forbidding** checks assert a name or
pattern must not appear, and are sound when the thing forbidden is stable; **quoting** a sentence
back at the file it came from fails in both directions. Every check below is one of the first two.

The `Name` column is the script's own name for the check, matched against the run's list: a row
keyed on its number alone does not say *which* check it is: a check inserted rather than appended
renumbered every reference below, and the run stayed green.

| # | Name | Check | Scope | Kind |
|---|---|---|---|---|
| 0 | `every document has a role` | Every markdown document that may cite the schema has a declared role in the script | root `*.md`, `docs/**`, `plugins/**` | forbidding |
| 1 | `citations resolve` | Every citation of the schema resolves — **both its path and its fragment** | every document with a role | computed |
| 2 | `no orphan section` | Every schema heading below the title is cited by at least one document | every level the schema uses, container sections excepted | computed |
| 3 | `outcomes live in the surface or a work item` | Every ruling's outcome cell resolves, and the section it names — by number or by heading — agrees with its link | the `Outcome lives in` column | computed |
| 4 | `binding statements cite the surface` | A ⛔ statement carries a citation naming a **section** | documents that explain or record | forbidding |
| 5 | `configurations match the surface` | Every configuration's top-level key set equals the one the schema declares | top level only | computed |
| 6 | `no citation names a container` | No citation names a **container** — a section whose whole content is in its subsections | every citation, in every document with a role | computed |
| 7 | `the footprint covers what is walked` | The footprint report covers every file the checks walk | the report's own coverage | computed |
| 8 | `citations between documents resolve` | Every **other** anchored link into a markdown heading resolves — between two documents, out of the schema into one, and within a document | every document with a role, the schema included | computed |
| 9 | `the record has a row per check` | This table's rows are the script's checks, in its own order and under its own names | the number and the name, not what the remaining cells say | computed |
| 10 | `no document leaves a fence open` | No document ends inside a fenced block | every document with a role, the schema included | computed |
| 11 | `the front page names every carrier` | Every carrier the plugin ships is offered on the front page as a command **and** linked in the inventory below it, and neither list names a carrier that does not ship | both lists, fenced examples excepted | computed |
| 12 | `ruling ordinals are unique and contiguous` | Every ruling's ordinal names one row, and every ordinal from one to the largest stated names a row | the rulings table's first column, not the order its rows are written in | computed |

Check 2 runs in the direction nobody checks by hand: a section added to the schema with nothing
recording why it has that shape fails the build when it is added. It holds **every level the
schema uses**: the depth is read from the headings, so a `####` added tomorrow is held the day it
exists.

The one exemption is a **container**, and it is what checks 2 and 6 share. A `##` section whose
whole content lives in its subsections states nothing of its own — § 4 is the live instance — so
check 2 reads it through its subsections, each held in its own right. Check 6 is the other face of
the same fact: a citation of such a section resolves to a heading and a list. The exemption is
planted on the **green** side and was verified by disabling it.

Check 4 is scoped to documents that explain or record, not to a skill. That is the schema's own
[boundary rule](../plugins/mjolnir/config/schema.md#what-the-procedure-models-and-what-it-only-names-and-calls),
under which a skill states procedure for its own role legitimately; the hazard there is a
*value* — [#19](https://github.com/ragnor-rs/mjolnir/issues/19)'s sweep. A skill's citations
are still held by check 1.

Check 3 permits a third, partial home. A ruling whose outcome is split between the surface and the
skill that carries it may name `the skill` **alongside** a section — ruling 6 does — but never
instead of one.

Check 3's cell reads `[schema § <N or heading>](…#a)`. Where the section is numbered, the number
and the anchor must agree; where it is named, the heading's own title ties the cell to it. A named
section whose link points at a different heading is a planted violation the build reddens on.

A cell names a section and links an anchor *within* it, and the anchor resolves through the section
it sits under — so a `###` subsection is nameable by its enclosing section, numbered or not, which
ruling 11 relies on. `4.1` and the `N → Subsection` form the documents use in prose resolve on
their leading ordinal. **Naming a `###` subsection as though it were the section is refused**:
the cell names the home and the link names the place in it, and the refusal says which of the two
disagrees.

Check 12 holds the rulings table's ordinals, which check 3 reads only to name a row in a refusal.
The rows cite each other by number in prose, so a duplicate makes every such reference name two
rulings and a skipped ordinal makes a reference to it name none — and neither shows in review,
because each row reads correctly on its own. ⚠️ **It was measured before it was held**: two sibling
branches computed the same next ordinal twice while one item was in review
([#45](https://github.com/ragnor-rs/mjolnir/issues/45)), and what caught both times was git, only
because the rows were appended at the same offset. Rows landing at different offsets merge clean.
The expected sequence is derived from the table on every run — one to the largest ordinal it
states — so no count of rulings is written here or in the script. A duplicate's refusal names the
ordinal and the line that stated it first, which is the form
[#194](https://github.com/ragnor-rs/mjolnir/issues/194) settled for a key stated twice.

## What the run reports rather than holds

Two things are printed with no verdict attached, because **a citation costs the whole document it
points into**: a role settling one sentence against the schema pays for every line of it.

- **A per-file footprint** — lines, characters and ⛔/⚠️ markers, for every file the checks
  already walk, so a role that doubles in size shows in the build log. Check 7 stops the report
  shrinking in silence: a file the checks read and the footprint skips is a cost reported by
  nothing. The marker count is of the emoji form anywhere in the file, code spans included, and
  the advisory marker **without** its variation selector is not counted — a bare codepoint is a
  script's output quoted, not a directive.
- **A count of coarse citations** — every citation naming a section that states something itself
  *and* has subsections, grouped by section with the documents that cite it. Check 6 holds the
  decidable end of this and nothing holds the rest.

⛔ **Neither carries a threshold** — the local half of
[`schema § 11`](../plugins/mjolnir/config/schema.md#11-session-context), whose statement that the
window degrades before it fills carries no number either. A budget is a judgement, and a judgement
hardcoded in a check is the copy the section below rules out. It is also unenforceable at run
time: the harness exposes context utilization to no hook but `SessionStart` on a resume.

### What the granularity check deliberately does not hold

**Which subsection states the fact.** That is the *quoting* kind, so the verdict is confined to
the one case needing no reading: a section with no text of its own cannot be where any fact is.
That verdict reaches `##` sections only: a cited `###` whose whole content is in `####`
subsections passes. The surface carries no such subsection, so the limit is latent. Every other
coarse citation is counted and left standing; reddening on all of them would make a legitimate
section-wide citation unwritable and ask for a hand pass the gate could not check.
Repointing one is a reader's judgement, as fidelity is.

## The check must not become one more copy of the principles

A check that hardcoded the loop's role count, the list of axes, or which facets have an absent
case would have to be edited on every change to the surface whose
[single-authority claim](../plugins/mjolnir/config/schema.md#the-configuration-surface) it
enforces; a copy that has to be kept in sync is the defect, not the maintenance burden.

So the script **derives every expectation from the schema at run time** and hardcodes grammar
only:

| Derived, at run time | Hardcoded |
|---|---|
| the section list, from the headings | markdown heading syntax |
| the anchor set, from the same | the code host's slug rule |
| the key vocabulary, from the fenced blocks | yaml top-level key syntax |
| the citation targets, from the anchors | the citation and outcome-cell forms |
| the rulings, from the table carrying the `Outcome lives in` column | that column's name |
| which sections are containers, from each one's own text and its subsections | that a section is `##` and a subsection `###` |
| the footprint, from the files the checks already walk | the two directive markers it counts |
| | the binding marker, and which document plays which role |

Adding a section to the schema grows what the script expects with no edit to the script, and
check 2 reddens until a document motivates it. Deleting one shrinks it the same way. Renumbering
one changes nothing: the rulings table is found by its column header, not by a section number.

**The only thing that forces an edit is a change of grammar** — a new marker, a new citation
form, a new column name, a new kind of document — and check 0 makes that residue loud: a markdown
document at the root, under `docs/`, or under `plugins/` with no declared role fails the build
instead of being skipped.

This is [`schema.md § 38 → The two
edges`](../plugins/mjolnir/config/schema.md#the-two-edges-and-which-of-them-is-enforced)'s rule
applied here — the sixth instance counted in
[`configuration-surface.md`](configuration-surface.md#the-strongest-argument-for-extraction-is-not-borrowed)
is another project's document checker, and this guard is a seventh.

## What it deliberately does not check

An unstated limit reads later as coverage, so every section below states its own.

- **Fidelity.** Whether a document's paraphrase still matches the section it cites is the
  *quoting* kind. No check here attempts it; it stays a reviewer's job, which is why a document
  paraphrases as little as it can and cites instead.
- **A document's audience and register, and a role value the document gives nothing to hold.**
  Check 0 gives every document a *role* — explains, records or carries procedure — and a role bounds
  what a document may **state**, never who it is written for or in what register. The front page's
  own reader is stated in
  [README § Who this page is written for](../README.md#who-this-page-is-written-for), as a
  convention of this repository, and held by nobody; nothing configures it, the README not being
  one of the artifacts
  [schema § 8](../plugins/mjolnir/config/schema.md#8-language-register-audience--per-artifact-not-per-project)'s
  map names. By
  [schema § What the procedure models](../plugins/mjolnir/config/schema.md#what-the-procedure-models-and-what-it-only-names-and-calls)'s
  test this is the boundary, not a missing facet: no role reads a document's audience to decide
  what to do next. What a file's prose **is** held to is
  [§ The file-prose floor, retired](#the-file-prose-floor-retired), and a floor is not a register.
  Measured on `docs/working-on-the-toolkit.md`: setting its role to `procedure` leaves every check
  green, because the checks that discriminate on a role read a binding statement or a citation of
  the surface and that document carries neither. The entry itself is held by check 0 either way.
- **Issue state.** Check 3 resolves the *form* of a work-item cell, not whether that issue is
  still open. Reading the tracker needs a token scope, and per
  [#50](https://github.com/ragnor-rs/mjolnir/issues/50) this workflow is granted none: its
  `permissions` are empty and the checkout is told to persist no credential. A ruling whose work
  item landed without its outcome moving into the schema is caught by a reader, not by the gate.
- **A binding marker that does not open a line.** Check 4 reads a statement as one that **opens** a
  line, optionally as a list item: mid-sentence the marker is prose *about* a rule. So a rule
  written mid-line in a document that may not state one passes. A marker-anywhere grammar reddens
  on every sentence that merely *mentions* the marker, the *quoting* failure, which makes the
  line-start form the sound one. A table cell is excluded by a separate condition, so the residue
  there is a reviewer's.
- **A link with no anchor on it.** No check of this script reaches a link that names no heading,
  such as a README row pointing at a carrier directory. The documents run below holds it,
  resolving every relative link in a governed document against the index ([`schema.md § 38 → A
  link
  resolves`](../plugins/mjolnir/config/schema.md#a-link-resolves-to-something-the-repository-holds)).
- **A markdown file no role claims, on either end of check 8.** That check holds a link whose
  target is already in the role map, so a citation into an untracked document, or out of one, is
  skipped in silence. It reddens when its own set empties, so a tree whose documents stopped
  citing each other is reported. Two fragments are accepted without being resolved, by both
  citation readers: `#L12`, a fragment the host answers and no heading carries; and an absolute
  address, which names a **ref** this tree has not got.
- **What the remaining cells of this table say.** Check 9 holds each row's number and its name
  against the script's list. A row whose scope or kind has gone stale reads correctly to it. A row
  carrying no name cell is refused rather than compared.
- **What the front page *says* about a carrier.** Check 11 holds membership of its two lists in
  both directions and nothing else: the sentence beside a carrier is held by nobody. The order of
  either list is not held, the page being an advertisement rather than an inventory in a fixed
  sequence. Its subject is this repository's own carriers; an adopting project's page is outside
  every glob this gate walks. The carrier reading is keyed on the skills directory, every carrier
  this plugin ships being a skill there.
- **The schema's own section numbers, and whether a `(44)` in prose names the ruling it means.**
  Check 12 holds the rulings table and no other numbered sequence: the surface's `## N.` headings
  sit in the same position and were scoped out when the item was filed. The order of the rows is
  not held, only the set, since a reference resolves by number rather than by position. A reference
  to a ruling that exists but is the wrong one reads correctly to it — that half is a reader's.
- **A heading inside a region the citation scan skips and the heading scan does not.** The two
  scans share one fence walker, so a fenced block is the same bytes to both, under either
  delimiter and at any delimiter length. What remains is the rest of what *shows* markdown —
  an HTML comment, a code span — which the citation readers skip and the heading reader does not, so
  an anchor that is not a heading is citable there and no check refuses a citation of it.
- **A citation inside a four-space code block, which both checks read as live.** Four spaces is a
  code block only where it is not a list continuation, and without a list parser such an arm
  drops live citations written as continuation lines of nested list items. A fenced example is
  the form to use in these documents; an indented one is read as a citation.
- **Every script in the tree, this gate's own included.** The globs reach markdown, so a module's
  comments are not held to citing the surface, measured in the footprint, or read for an outcome.
  A carrier's own text is strict and the `scripts/` beside it is implementation, as in the names
  sweep. A rule a module's comment states is a rule no mechanism holds to one authority.
- **Whatever is not committed.** Every check here reads the working tree, which is not what a
  commit takes: edits verified green and then left out of the commit give a verdict about a tree
  that never landed. The host's own run closes it afterwards; nothing here closes it before.
- **Key subtrees.** Check 5 holds the top level only, so a key inside a block is this check's blind
  spot whether or not the surface declares it — `tracker.labels`, which it does not, is the known
  consequence. A deeper comparison needs one exception per tracker kind, since every configuration
  lacks every other kind's block by design
  ([§ 3](../plugins/mjolnir/config/schema.md#what-each-kinds-block-carries)). The reader refuses
  a block that omits a key its own kind requires, at configuration time, which answers nothing
  about an undeclared key.
- **Every `yaml` fence on the surface is a declaration to it**, and it cannot tell one that states
  the key set from one showing what *not* to write. A counter-example block would make every
  configuration refuse for lacking the key it warns about. There is no such block; the surface
  carries a marker convention for a fence's own reader, which is where a fix would go.
- **Issues and pull requests.** Not from *this* workflow, for the reason under *Issue state*
  ([#50](https://github.com/ragnor-rs/mjolnir/issues/50)); the gate on the change below reads that
  store with a scope of its own. The lettering of projects A–F in the documentation rests on the
  reason [#19](https://github.com/ragnor-rs/mjolnir/issues/19) records.
- **Configurations outside the globs.** A configuration added where `CONFIG_GLOBS` does not look
  is skipped. The guard asserts only that each glob matched something, which catches a moved
  directory but not a new one somewhere else.

## The second sweep: naming no other project

The convention in the README — that this repository names no *other* project — and the surface's
own rule that [no value appears under a carrier
root](../plugins/mjolnir/config/schema.md#the-configuration-surface) both say the **search is the
check** rather than a reading of the procedure. `tools/check_no_project_names.py` is that search,
in its own workflow. Most of its checks are of the *forbidding* kind, so the script stands or
falls on whether the thing forbidden has a stable form; the computed ones stop the rest holding
nothing. No count of either group is carried, for the reason given
[above](#how-the-single-authority-claim-is-held).

Three scopes. The repository-wide one looks for what identifies
someone else's project; the strict one — the carrier roots, never the whole tree — looks for
anything a role's text may not carry at all, a value and a tracker and a stack among them; and
the third is **every tracked configuration**, this project's own and the examples, which is where
a value of
[§ 28](../plugins/mjolnir/config/schema.md#28-a-configured-value-a-repository-may-not-hold)'s class
would be checked in. A carrier is a skill, a command or a hook (schema § 7), so the
strict set is matched by *shape* — `plugins/*/skills/`, `commands/`, `.claude/hooks/` and so on —
rather than from a hand-kept list of roots.

| # | Check | Scope | Kind |
|---|---|---|---|
| 0 | No repository but this one's is named, as a URL, an install-command argument or a `repo:` value | every tracked text file | forbidding |
| 1 | No path under a home directory | same | forbidding |
| 2 | No address | same | forbidding |
| 3 | No identifier that resolves on a tracker — a Jira key, a Trello id or a prefixed account id **written as a value**, or either service's URL anywhere | same | forbidding |
| 4 | The strict set matched a file at all | the carrier roots | computed |
| 5 | Every file under a plugin is a carrier, a configuration or a manifest — nothing else | `plugins/**` | computed |
| 6 | No tracker is named, in the slug spelling or the prose one | the strict set | forbidding |
| 7 | No package manager, task runner, build tool, checker, manifest or lockfile; no stack's own flag; no interpreter in front of something this repository does not ship; no directory change prefixing a command, no directory flag, no absolute path | the strict set | forbidding |
| 8 | No value any configuration supplies | the strict set | forbidding |
| 9 | No machine named by its address, which is the one identity shape of a *machine* with a form a pattern can hold — a hostname is any word and an alias is any word somebody chose, so those are held by the names living outside every working tree ([schema § 21 → The machines named](../plugins/mjolnir/config/schema.md#the-machines-named-are-the-ones-that-are-not-live)) rather than by this sweep | same | forbidding |
| 10 | No role is resolved by asking who is running — the spellings that resolve the current user and nothing else, each one a form English does not also use ([schema § 27](../plugins/mjolnir/config/schema.md#27-the-role-to-person-map)) | the strict set | forbidding |
| 11 | No tracked configuration carries a value under a key the surface marks `# private` — a chat thread's name, a calendar's own name, a person, a path on somebody's machine ([schema § 28](../plugins/mjolnir/config/schema.md#28-a-configured-value-a-repository-may-not-hold)) | every tracked configuration | forbidding |
| 12 | No invocation of the host client **for a run** — its own `run` subcommand, a dispatch, a pull request's runs, and the endpoints behind all three, in a command line, in a list of quoted words, or split across a continuation. The client itself stays permitted, being how a pull request is opened, read and merged ([schema § 29](../plugins/mjolnir/config/schema.md#29-the-hosts-run-operations)) | the strict set | forbidding |
| 13 | No tracker's own vocabulary for a **dependency** — the field an edge is carried in, the endpoint it is posted to, the sides and the wording of a link call. This is check 6 one level down: a role writing one of these names a tracker's *shape* without naming the tracker, which check 6 passed while it was the same defect. ⚠️ Matched in code regions only, by rule 1 and more load-bearingly than anywhere else here — a link type's wording is also an ordinary English phrase, and a shipped role explains the direction of a dependency in exactly those words ([schema § 3 → An edge is a relation](../plugins/mjolnir/config/schema.md#an-edge-is-a-relation-and-a-body-keeps-the-reasoning-about-it)) | the strict set | forbidding |
| 14 | No kind behind **any other port** is named, in either spelling — check 6's rule with the subject read off the `# port:` markers rather than off the tracker block, so a port landing later is swept the moment its kind has a slug for a name. ⛔ **Slug-shaped kinds only, and the bound is the check**: a single-word kind of a port whose word is ordinary English cannot be forbidden in prose about that word, so `file` is held by review and said so in as many words beside the port's own suite runner ([schema § 26](../plugins/mjolnir/config/schema.md#26-the-day-logs-destination-port)) | the strict set | forbidding |

A row takes the next number and never one already in the table: a row is resolved by what it
says, and the number is this table's own ordering, not a position in the script.

Nothing holds this table against the script's own list: the check that compares a table to a list
reads one table, under one header. A row here that has gone stale is a reader's to catch.

Check 5 makes the shape-matched strict set safe: a carrier in a directory the shapes do not reach
— `plugins/other/skils/`, one letter out — would otherwise be swept by nothing *and* reported by
nothing.

Two rules make a forbidding sweep sound:

1. **A stack token counts only as code, never as prose.** In markdown that means inside a code
   span or a fenced block; in a script it means outside the comments. `make`, `go`, `task`,
   `just`, `stack`, `bundle`, `mix` and `pod` are ordinary English words in a sentence and
   unambiguous commands in a code span, and a shebang names an absolute path by construction. A
   sweep of prose for any of them would redden on a reworded sentence, the *quoting* failure.
   Fenced blocks are found by a line toggle rather than a paired regex: one trailing space after a
   fence's language tag makes a paired regex match one block's closer against the next block's
   opener, which hides every command and sweeps the prose between them instead.
2. **A value counts only as a whole code span or a whole quoted string.** A value written as a
   value stands alone in its span, so a sentence that merely contains the word is not one: a
   status vocabulary of `open` and `closed` does not forbid the word "opening", which the day-log
   skill uses freely. The wrap is not part of the value — this repository hard-wraps its prose
   at `language.prose_width` and most forbidden values are multi-word, so newlines are normalised
   away before matching. Matching is **per paragraph**: the single-backtick form is paired, so
   flattening a whole file lets one unbalanced delimiter re-pair every span after it — a stray
   backtick at the top of a shipped carrier stopped most of its regions being read as values while
   the region count barely moved. A paragraph is the widest scope a wrapped span needs, since a
   hard wrap never crosses a blank line, and the narrowest that bounds what one stray delimiter
   costs. A span whose delimiters sit either side of a blank line is not read; markdown does not
   carry one either. A fenced block's own backticks are removed first, for the same reason as
   rule 1: they would shift the pairing of every span after them. A ``…`` span is removed the same
   way — split on, never paired, since a paired form matches one span's closer against the next
   span's opener. What is inside such a span is read as well as collected, because this
   repository's idiom for showing a literal span is a ``…`` around one. Both removals are scoped to
   markdown: in a script the halves of two unrelated `` ``` `` literals pair with each other across
   hundreds of lines, and taking that region out blinded the sweep over 722 lines of one module,
   with a planted tracker key inside it going unreported.

It derives what it can, for the reason
[above](#the-check-must-not-become-one-more-copy-of-the-principles):

| Derived, at run time | Hardcoded |
|---|---|
| the one permitted slug, from `host.repo` in this project's own configuration | the host-URL, address and tracker-identifier grammars |
| the tracker names, from the `kind` alternatives of the surface's **tracker block** and every configuration's declared kind | the closed list of stack tool names |
| every other port's slug-shaped kinds, from the `# port:` markers' own key paths and the same paths in every configuration | nothing: which ports exist is the markers' answer, and no list of them is kept here |
| the forbidden value set, from **every scalar the configurations state** — this project's own included — minus the vocabulary the surface publishes | nothing: no list of key names is kept here, and none is kept in step |
| the file list, from `git ls-files`; the strict set, from the carrier shapes | a carrier directory's name, and the code-span and quoted-string forms of rules 1 and 2 |
| the file to plant a violation into, from the strict set | the exceptions below |

The tracker names are read from the `tracker:` block specifically: a line-anchored read of every
`kind:` cannot tell `host.kind: github` from `tracker.kind`, and subtracting the host's name
afterwards would be a carve-out of *content* in a script that hardcodes form.

The other ports are read off their markers, which is how a port whose block is nested is reached.
The destination's sits under `day_log:`, where a read anchored at column zero finds nothing;
the marker carries the key's own dotted path, so there is no block to find and no indentation to
parse.

A multi-word kind — the kinds
[schema § 26](../plugins/mjolnir/config/schema.md#26-the-day-logs-destination-port) and
[schema § 3](../plugins/mjolnir/config/schema.md#3-tracker-port) state — is matched in every
separator spelling: `googlesheet`, `google sheet`, `google-sheet` and `google_sheet`. A plant
using a single-word kind cannot show the underscore case, where the underscore is a *boundary*
the lookarounds handle rather than a *join* between the name's parts, so there is a plant of each
shape.

Reading the forbidden values out of the configurations makes the acceptance item's pair work in
opposite directions, both measured: **a new example configuration adds to what is forbidden under
a carrier root instead of tripping anything, and a status word added to a skill reddens the
build.**

### The line: a vocabulary the surface publishes, against one a project invents

Every scalar a configuration states is read, whatever key it sits under, and the subtraction is
what the surface **publishes**:

- a closed alternation, `kind: worktree | in_place`, in either shape the surface writes one — as
  the value, or as a comment beside a value;
- a value marked `# default`;
- a closed vocabulary stated as a list, § 9's `streams` being the live instance, where the
  configuration's own list is a **subset** of it.

**Published is narrower than written.** The surface *illustrates* some keys with a concrete
value — `label_prefix: "type:"`, `type_branch_prefix: { bug: bugfix }` — and a project writing the
same string has still invented it, so an illustration subtracts nothing. What tells the two apart
is the marker, per
[schema § The file itself](../plugins/mjolnir/config/schema.md#the-file-itself): the alternations
and the marked defaults are read through the surface's own reader rather than parsed a second time
here, so a marker's grammar has one implementation and a facet added to the surface changes what
this sweep forbids with no edit to the sweep.

A reading keyed on key names cannot express that line. Against a list of twenty-two singular key
names, planted one at a time into a carrier file as a code span, `closed`, a workflow name and an
artifact directory each reddened, while **a configured branch prefix and a configured label both
passed** — the two the project invented. The prefix sits under
`work_item.type_branch_prefix.<one of the project's own types>`, a key the project itself writes,
and the label sits in `tracker.labels`, a plural whose singular `label` is a readiness check's
argument. The branch prefix is read by the starting role, whose text is the one place that value
must not appear, since reading it from configuration is what that role is for.

The alternations must stay nameable: § 6's dirty-tree derivation and § 10's routing table are
both stated *by mode*, so a role forbidden from saying `worktree` could not name § 10 at all. Each
of those two subtractions carries a plant in the **green** direction, verified by emptying the
published set and watching both redden.

A published alternation's members are single tokens, that being the reader's own grammar, so a
multi-word value cannot be published and stays forbidden wherever a project configures it.
Measured by planting a facet on the surface in both spellings: the single-token member is
subtracted and the two-word one is not.

A third shape a key-name reading cannot reach is § 2's facet, which
[#47](https://github.com/ragnor-rs/mjolnir/issues/47) turned into assertions. `host.checks` is a
**list of entries**, so a workflow name, a trigger pattern and a path filter each sit under a key
that is a member's and not a path's. Three plants read those three facts out of the configuration
and name each one in a carrier, which makes *no consumer carries a workflow name, a trigger
pattern or a path filter of its own* a property of the search. The third plants the filter into
the configuration as well, because no workflow in this repository filters by path; each half alone
was measured green and the two together red.

A fourth subtraction is every dotted key path the surface declares.
[§ 28](../plugins/mjolnir/config/schema.md#28-a-configured-value-a-repository-may-not-hold)
gives a project a list of the keys it resolves from outside the repository, so those list members
are **key paths**, and read as values they would forbid a role from naming the key it reads — the
day-log role cites `day_log.attribute_to`, which is the key it reads `attribute_to` from, and the
sweep reddened on it against an example's `private.keys`. The surface states those strings, so a
configuration writing one is choosing the surface's word. Its green side is a plant, verified by
dropping the declared paths from the published set and watching the role redden again.

What stops the derived set shrinking to nothing is three reported arms, there being no key list to
go stale: a surface whose published vocabulary cannot be read, a configuration that does not parse,
and a configuration that states no concrete value at all. Each is one of the planted
violations, and the first proves the subtraction is read from the surface rather than copied into
the script.

### The exceptions, encoded rather than assumed

A literal reading of the convention would forbid every one of these, so each is in the script, and
no count of them is given.

- **`config/examples/`** is whole example configurations and is data rather than procedure. It is
  the one place a concrete status word or label prefix is written down — the surface's own
  [boundary](../plugins/mjolnir/config/schema.md#the-configuration-surface) — and it is where the
  sweep reads the forbidden set *from*. The strict set asserts that nothing under a carrier root
  carries a value regardless. This is also the **only** place a bare all-caps value counts as a
  placeholder: `OWNER/REPO` and `KEY` are stand-ins, but in a configuration that is somebody's
  actual facts `TODO` and `IN_PROGRESS` are values. Applied everywhere, the all-caps rule would drop
  the commonest status spellings and every uppercase project key out of the forbidden set.
- **This repository's own slug**, derived rather than listed. Removing `host.repo` from the
  configuration reddens the build rather than quietly permitting every slug, which is one of the
  planted violations.
- **A placeholder under a `# private` key**, for the third scope above. The examples write
  `<the exported archive>` where a project writes an archive, so the exemption is the
  **placeholder's own form** rather than the file it sits in: a concrete chat name, calendar or
  path in an example trips the check exactly as one in this project's own configuration does, and
  both directions are planted. The `config/examples/` entry above is a scope; this is a shape.
- **Every entry under this heading is permanent.** An exemption with no instance is removed rather
  than left empty, because an exemption path with no entry and no plant is a branch nothing
  exercises.
- **The public artifacts cited as evidence.** Each is an artifact rather than a project in
  scope, and each sits in a table in the script with its reason beside it, so **an entry means
  editing that table and saying why** — the published context-engineering practice
  [`§ 11`](../plugins/mjolnir/config/schema.md#11-session-context)'s measurements are drawn from
  is cited by repository URL, a measurement whose source is not citable not being a measurement.
  Each entry names the roots it is permitted in, because a slug permitted everywhere passes in a
  skill and as a `repo:` value in a configuration. Emptying the table, or moving a citation outside
  the roots its entry names, reddens the build; both directions are measured.

`docs/` is deliberately outside the strict set: it quotes the measurements the surface was derived
from and has to keep naming the build tool that reported a cached pass as work done. A rule that
forbade a tool name in a measurement would forbid the evidence.

**The script exempts itself — that one file, not all of `tools/`.** It necessarily writes down
every token it forbids: its grammars spell out the home-directory prefixes and its planted
violations contain addresses and foreign slugs. Its sibling is swept like any other file, because
`tools/` is where [#15](https://github.com/ragnor-rs/mjolnir/issues/15)'s extracted evidence
script and [#50](https://github.com/ragnor-rs/mjolnir/issues/50)'s linters land, and somebody's
home path hardcoded as a default in one of those is what check 1 exists for.

### What this sweep deliberately does not check

- **A bare slug in prose.** `owner/repo` and `docs/single-source-of-truth.md` have the same shape,
  so the sound forms are the URL, the install-command argument and the `repo:` value. A workflow's
  `uses: actions/checkout@v4` is a third shape it does not read, and a slug written bare in a
  sentence is a reviewer's catch.
- **A person's name, a bare label, a milestone title, an assignee handle, a service name.** None
  has a stable form, and forbidding a list of them would be a list to keep in sync. This is the
  same reason projects are lettered A–F in the documentation: the convention is held by what the
  documents *don't* contain. A tracker account id in its prefixed spelling, which cannot be
  anything else, is check 3's; the bare dashed hex group is not, since it also matches a *session*
  id in this repository's own fixtures. What holds the rest is where the values live: the
  identities are in a file the project points at
  ([schema § 27](../plugins/mjolnir/config/schema.md#27-the-role-to-person-map)), never in the
  toolkit, which is check 9's argument about a machine one class over.
- **A role *instructed in words* to ask who is running.** Check 10 holds the spellings that resolve
  the current user and nothing else, matched anywhere in a strict file rather than in code alone,
  since what it is looking for is a role *instructed* to ask. So every spelling it holds has to be
  one English does not also use, and the hyphenated modifier is not: the hyphenated English form
  passes and is asserted on the green side, while the flag spelling, with its dashes, is held. What
  it cannot reach is *ask the tracker who you are* written out as a sentence, a sweep for every
  word; that half is held by
  [schema § 27](../plugins/mjolnir/config/schema.md#27-the-role-to-person-map) being the single
  statement of the rule, beside the shared reader refusing `current_user` wherever a configuration
  writes it. The strict scope is the rule's own: the implementation behind `assign` translates the
  running user's spelling legitimately, recording who *took* an item being a fact about this run,
  and that is asserted on its green side.
- **An interpreter in front of a file this repository ships.** Check 7 reddens on an interpreter
  in the one position
  [schema § 17](../plugins/mjolnir/config/schema.md#17-the-local-verdict-and-the-conditions-under-which-it-counts)
  and the boundary rule it reads make wrong: in front of something **configuration** supplies,
  where the language is a guess that is wrong the first time a project writes its script in
  another one. What is left out is the complement, and it is two positions rather than a reading:
  a path the repository **tracks**, computed from the file list, and a region where nothing
  follows the interpreter at all — the shape the hook carrier is in, where `"command"` and
  `"args"` are separate members of one object. So an interpreter in front of a tracked script
  passes by design; the residue is an interpreter in front of an argument assembled in a *second*
  region, which this reading cannot pair up. A role naming a script the plugin itself ships, which
  the file list cannot resolve because the harness substitutes the plugin's own location for the
  variable in front of it, is permitted by the variable, and its green side is asserted in general
  and inside the day-log role's own directory.
- **A flag nobody wrote down.** Check 7's flag list is closed, like its tool list, and errs the
  same way: a flag outside it passes and leaves a reviewer to catch it. A listed flag is caught in
  any position, so `--offline` written alone into a role reddens.
- **A stack token hidden in a script's comment.** Rule 1 strips comments before sweeping a
  script, so `# run npm run build first` in a hook is not read. That is the deliberate trade: a
  comment is prose, and sweeping it would redden on an ordinary English sentence. A command the
  procedure actually runs is not in a comment.
- **A directory change, a directory flag or an absolute path written in prose.** Rule 1's
  code-only scope is stated above for stack tokens, and the other three arms of the same check
  inherit it — they read `code()` regions too, so an absolute path in a sentence is not read.
- **A *relative* directory name written into a role.** The three arms above reach a directory
  reaching a command by a change of directory, by a flag, or absolutely; what none of them reaches
  is a package root written bare, as a positional argument or in prose —
  [schema § 1](../plugins/mjolnir/config/schema.md#a-command-root-is-not-a-code-root) makes that
  directory a configured fact, so a role naming one has copied a project's own. This is a shape
  collision: a role legitimately cites `.claude/mjolnir.yaml` and a skill's own path, and a
  configured path and a foreign package root are one shape. Flagging every path-shaped token in a
  code region that this repository does not track found **eighteen** instances in the live
  carriers and not one of them a directory: surface citations written as code spans
  (`config/schema.md § 1`), slash-command names, two of the code host's own API path segments,
  and two prose fractions. So what is held is the half with a stable form: a command root's
  *name* is a value of the project's own, so check 8 reddens on one written into a carrier, with a
  plant that states the root in the configuration and names it in a role. A directory nobody
  configured, written straight into a role, is a reviewer's catch.
- **This project's own slug, anywhere at all.** The second exception derives it and, unlike the
  third, scopes it to nothing. So a carrier may name this repository's host, backlog and item
  numbers while the sweep stays green, which the README's own convention does not permit: it
  enumerates where the own slug may be cited, and a shipped carrier is not among them.
- **A bare all-caps value inside an example configuration**, per the first exception above — an
  example whose status words are upper-case. The alternative drops `OWNER/REPO` and `KEY` out of
  the placeholder set.
- **A project value spelled like something the surface publishes.** The subtraction is by the
  value and not by the key it sits under, so a project that names a status `merged`, or a label
  `field`, may have a role say it. The narrower reading — subtract a published value only under
  the key that publishes it — is not available: the surface shows several keys in fences that
  open at an indent, so `statuses[].writer` and a bare `writer:` are one statement read at two
  paths, and keying the subtraction to the path reddens `procedure` three times across two
  shipped carriers.
- **A list a project states that the surface happens to illustrate with the same members.** A
  type vocabulary is forbidden by the subset test the moment it carries one word the surface
  does not — `[bug, feature, chore]` is caught by `chore` — so what passes is a project whose
  list is exactly the surface's illustration, `[bug, feature, task]` and nothing else. The
  alternative forbids `sessions` and `commits` in the day-log skill, which name the stream
  vocabulary § 9 publishes and must.
- **A value written as a key of a JSON carrier.** In JSON a key is quoted by construction, so
  rule 2's whole-quoted-string reading takes in every key of a hook carrier: `"hooks"` is the
  harness's own schema word three times over in this repository's own hook file, and this project
  happens to classify work with a label of that spelling. The exemption is scoped to `.json` by
  extension — a quoted key in a script is a dict literal's, where the value beside it is the
  thing worth sweeping — and a configured value as a JSON *value* is a planted violation.
- **A configured value a carrier's prose merely contains.** Rule 2 is unchanged by the derivation
  reaching further: a label named in a sentence rather than in a span is not read — `decision` is
  one of this project's own labels and an ordinary English word the shipped roles use often, and
  the sweep is green on every one of them.
- **A build tool a project actually named a carrier after.** A carrier-classification map is keyed
  by the basenames projects used, so a key naming a build tool is a fact the map must carry;
  dropping it makes the role it classifies read as a role that does not exist. The
  key is exempt, not the file and not the value beside it, and the exemption is asserted to stay
  green while disabling it reddens.
- **Most carrier roots are empty, and the run still exits 0.** The shapes that match a file are
  the skills root and the hooks root; the hooks that enforce the *loop* are
  [#16](https://github.com/ragnor-rs/mjolnir/issues/16), and the command carrier belongs to
  whichever project migrates with one. The run prints how many shapes swept nothing and **does
  not** fail on them, because a shape for a carrier kind this repository has not adopted is not a
  defect. Check 4 fails if the strict set empties altogether, and check 5 fails on a carrier
  sitting outside every shape.
- **A dependency described in words, and one tracker's link type spelled as an ordinary noun.**
  Check 13's list is closed like check 7's and errs the same way: it holds the spellings whose
  *shape* is decidable, plus a wording held only where it is the whole of a code span, which is
  where a literal stands alone. What it cannot reach is a role writing *post the relation on
  the blocked item, keyed on the blocker's internal id* in a sentence, a sweep for every word;
  that is held by
  [schema § 3](../plugins/mjolnir/config/schema.md#an-edge-is-a-relation-and-a-body-keeps-the-reasoning-about-it)
  being the single statement of the rule, with the two operations the only thing a role names.
  The name that is also an English phrase is held in one position only — as the whole of a code
  region, rule 2's own test applied to a name. Matched anywhere in a region, it refuses a commit
  subject quoted in a span, an example item body inside a fence, and an example of what this
  port's own answer carries; each is asserted on the green side. The strict scope is the rule's
  own — the implementations behind the port must name every one of these to speak to
  their trackers at all, and `docs/` records which tracker spells which, so a tree-wide sweep
  would forbid the one place the shape belongs and the evidence for why. Each green side is
  asserted as a problem-set delta rather than by watching a plant redden: disabling a scope
  reddens the *unplanted* tree, so a whole-tree reading cannot tell a plant that was swept from a
  plant that contributed no region at all. The phrase in a carrier's prose is held by the
  code-region scope and the whole-region position *together*, by neither alone.
- **A side of a link type is refused only with that type's own wording after it.** Each of those
  words is ordinary English in front of a colon, so the key decides nothing: a span reading
  *inward: toward the centre* is not a tracker's metadata key, and requiring both sides in one
  region admits every shape a carrier writes. What is decidable is the value. The quote around that
  value is matched in either spelling and through any number of backslashes — the shell string and
  the JSON carrier holding that string each add one.
- **A wording's own trailing punctuation comes off both ends of a region before the phrase group is
  matched**, so a literal quoted at the end of a sentence is still read as that literal. The
  characters stripped are the `PUNCTUATION` constant, more than that reason needs, so a span whose
  content is the wording followed by any of them is refused as the wording — a sentence written
  inside a code span, which rule 1 already reads as code.
- **Which of a wording's forms the arm holds is not derivable from the arm.** The group carries the
  full wording alone; the plain verb is outside it because a role may quote a status word or a
  capability of that spelling, and the bare participle because it is the same phrase one word
  short. Nothing reddens if either is added back, no plant or exemption being a whole region equal
  to one.
- **Issues and pull requests**, for the reason given
  [above](#what-it-deliberately-does-not-check): that store is not a file, and a reviewer covers
  it.

## The gate on the change: nothing is deferred

The surface rules that a work item is delivered whole — a role that cannot answer a question asks
rather than noting it, and no change merges with an open item against it:
[schema § *Nothing is deferred*](../plugins/mjolnir/config/schema.md#nothing-is-deferred). The
completeness statement is **read back, never asserted**: a pull request that says in prose that
everything is resolved is making the same claim the defect makes.

So `tools/check_nothing_deferred.py` counts the items where they were raised — the body, and the
threads the host records a resolution for — and names each one it finds.

| # | Check | Scope | Kind |
|---|---|---|---|
| 0 | The pull request has a body | the change | computed |
| 1 | The body states its open items, once, and the answer is that there are none | the body | forbidding |
| 2 | No thread on the change is unresolved | every thread, following the cursor | computed |
| 3 | No unticked item in the body | the body | forbidding |
| 4 | Every changed file was read, and no deferral marker is on a line this change adds | the diff's added lines | forbidding |
| 5 | No line this change adds names work with no owner | the diff's added lines | forbidding |

Check 1 is *forbidding*, not computed. The heading `Open items` and the answer `None.` are a
grammar the gate publishes, so the check reddens on a reword — `Open questions` is not that
heading and `Nothing outstanding.` is not that answer. That is sound because the gate itself fixes
the grammar; nothing is compared against the text it came from. Making both strings
configuration, in the repository's own language, is
[#51](https://github.com/ragnor-rs/mjolnir/issues/51)'s, and this script is the implementation
that item would call.

The grammar check 1 enforces, in full, since the refusal names the items and not the shape:
an ATX heading whose text is `Open items` at any level, appearing **once**; the section running to
the next heading of any level; and, inside it, nothing but the answer — `None.` or `None`, in any
case, optionally as a list item or emphasised. Blank lines, horizontal rules and single-line HTML
comments are not content. Anything else in that section is an open item and is named as one.

Check 5 reads prose. It holds the same section's statement that the rule binds every artifact a
role produces, a file the change adds a line to among them
([§ *Nothing is deferred*](../plugins/mjolnir/config/schema.md#nothing-is-deferred)): a change
whose `Open items` section read exactly `None.`, with no unresolved thread and no marker, can still
ship a deferral as a clause in a document. The body, the threads and the markers are where a
writer defers *knowingly*; prose is where it reads as diligence.

Check 5 reads the unowned half, not the unfinished half: the commonest ways this repository states
a limit honestly appear across nine lines of tracked text, so sweeping those hands a change back
for the candid form of a sentence. What reddens is a line that names no owner for a cure. The forms
themselves are not written down here: the run prints what it found, and this arm would redden on
its own list. The remedy for a hit is usually **deletion** rather than filing: a cure nobody
measured is not a measured gap. The whole-change fixture carries three honest limit lines taken
from lines this repository ships, and widening the arm to the unfinished half reddens it.

Check 2 follows the cursor rather than reading a first page, because a review that ran long is the
change this gate is for. Check 1 reddens a body that lists what it knows is unfinished under a
heading reading as diligence: it carries no statement at all, and the absence is what fails.

This gate holds a token scope, unlike its siblings: they read files in the tree; this one reads a
resolution the host records and an author cannot describe, and the surface's rule that a finding
goes where its resolution can be read back
([§ *Nothing is deferred*](../plugins/mjolnir/config/schema.md#nothing-is-deferred)) is only worth
stating if something reads it. The scope is `pull-requests: read`, the narrowest the host offers;
nothing writes; the checkout persists no credential, and the token is handed to the one step that
needs it rather than left in the git config.

Check 2 is **prospective**. `reviewThreads.totalCount` was zero on every pull request this
repository had before the gate, every earlier review finding being an issue comment, which the
query does not return. A finding now goes in a thread; the scope is not evidence that earlier
threads existed.

Where the host supplies no patch for a file — a binary, a diff over its per-file size limit — that
file is reported unread, per
[schema § 2](../plugins/mjolnir/config/schema.md#2-code-host)'s rule that absence of signal is not
an answer: a marker in a file nothing read is not an absence of markers. Where the host reports
that file *added*, it is read whole from the checkout instead: every line of an added file is a
line the change writes, so the answer is the one the patch would have given. A *modified* file is
never read whole — that would hand somebody else's marker to this change, which is what
[schema § *Nothing is deferred*](../plugins/mjolnir/config/schema.md#nothing-is-deferred)'s scope
over the lines a change **adds** exists to prevent. Both directions are asserted, with a third arm
for an added file that is not in the tree, which stays unread rather than reading as empty.

A modified file with no patch gets a second answer before it is reported: the same two commits the
host compared, asked of git in the runner. What comes back is the `+` side of a real diff, so the
scope
[schema § *Nothing is deferred*](../plugins/mjolnir/config/schema.md#nothing-is-deferred)
states over the lines a change **adds** is untouched — this is the patch the host declined to send.

Three arms are asserted, over a repository the suite builds so that they hold wherever it runs:
the added lines of a modified file, and *unread* both where the two commits are not known and
where git cannot reach them — an empty answer there would read as a file with nothing added,
against [schema § 2](../plugins/mjolnir/config/schema.md#2-code-host)'s rule. The workflow checks
out the whole history, a one-commit clone carrying neither commit; a run in a tree that cannot
reach them still reports the file rather than passing it.

### What this gate deliberately does not check

- **The closing half of the rule.** No item closes carrying an unresolved item either, and that is
  a tracker write this gate neither performs nor reads. Only the merge half is held here.
- **Whether the answer is true.** `None.` is a claim, and the gate holds that the claim was made
  and that nothing it can read contradicts it. A known cost written into the summary as a feature
  reads as green — the *fidelity* limit.
- **A thread resolved to clear the gate.** Resolution is the host's record of somebody's
  judgement, and the gate reads the record rather than the judgement. Where the author and the
  reviewer are the same person, check 2 is a ratchet against *forgetting* and not a guard against
  *intent*, as check 1's `None.` is: a finding cannot be silently absent, and clearing one is an
  act with a name and a timestamp on it. What closes the rest is a second person, which is the
  `revisit_when` written against `estimate` in this project's own configuration.
- **A finding one pass raised and fixed itself, which is an item in form only.** A thread is how an
  item needing somebody's action is made readable, so a defect found and closed inside a single
  pass has no such item: posting it as a thread *manufactures* one, and where the author and the
  reviewer are one credential the gate is held red on finished work until the writer clears it.
  Such a defect belongs in the commit that fixed it and in the change's own body, which check 1
  reads. A thread is for what a reader has to answer, and the gate cannot tell the two apart.
- **A finding raised as a plain comment.** A comment carries no resolution state anywhere on the
  host, so nothing can report it unresolved — which is why the rule puts a finding in a thread.
  A finding posted where it cannot be read back is a reviewer's catch, and the one real hole in
  check 2.
- **A marker with no colon and no argument list.** A bare `TODO` in a sentence is prose, and it
  sits innocently in this tree — in a comment quoting a status vocabulary, and in this document.
  Sweeping prose for the word is the *quoting* failure. `FIXME` and `XXX` occur nowhere here and
  are carried for the projects that arrive with them.
- **A marker this change did not write.** Only added lines are read: somebody else's marker is
  somebody else's item.
- **A marker in a file that necessarily writes one down.** A closed list of two, not all of
  `tools/` and not every script — a check that forbids a form has to spell that form out, and has
  to plant it to prove the arm fires. The sweep itself is one; the other is the hook holding a
  reply to naming no work the turn does not do, where the marker is one of the forms it forbids and
  its **casing** is the grammar, so the plant has to be written in that casing. Every other file is
  swept, which matters because `tools/` is where further scripts land. Both halves are asserted:
  the whole-change fixture carries a marker in an exempt file and stays green, and a plant puts one
  in a sibling tool and reddens.
- **A setext heading.** `Open items` underlined with hyphens is an `h2` to the host and is not a
  heading to this gate. The residue is narrow and the alternative is a second heading grammar.
- **A pull request that does not exist yet.** Run by hand before one is opened, the gate has no
  answer and says so, and no answer is not green — the surface's rule for an absent run
  ([§ 2](../plugins/mjolnir/config/schema.md#2-code-host)) holds here for the same reason.
- **A thread resolved after the last run.** `pull_request_review_thread` is a webhook the host
  sends and **not** a workflow trigger — a workflow file naming it is rejected whole, as a
  push-event failure with no jobs. So the gate re-runs when a review is *submitted*, which is when
  findings arrive, but not when the last one is *resolved*: that verdict stands until the next
  push, body edit, review or manual re-run. The direction left open costs a re-run rather than a
  false green.
- **A merge between the last run and the button.** The verdict is about the change as the last
  triggering event left it.

## Beside the document checks: the tracker port's own contract

The two gates above hold a document claim; the rest hold a module, a shape or a rule — the
configuration reader `plugins/mjolnir/scripts/config.py`, whose own checks are its work item's;
the day-log carrier `plugins/mjolnir/scripts/day_log.py`, whose are likewise its own and which this
document records nowhere else; the prose-width sweep; the reply hook; and the port contract
recorded here. Each carries its own workflow and its own `host.checks` entry.

`plugins/mjolnir/scripts/port.py --self-test` runs in the `Port contract` workflow. It is not a
document check; it holds a claim about the tree that a reviewer would otherwise be the only thing
holding.

What it holds: that the operation list and every absent case are read out of
[schema § 3](../plugins/mjolnir/config/schema.md#the-operations-and-what-an-absent-capability-does)
rather than written in the script; that an unavailable operation comes back as the fallback stated
there and never as an error; that an advance to a status whose configured writer is not the
procedure is refused with the writer named
([schema § 4.2](../plugins/mjolnir/config/schema.md#42-status--an-ordered-set-of-name-role-writer));
and that against a configuration whose `kind` is `none` every operation is unavailable while the
report reads as a configuration rather than a fault.

It holds every one of those once per port the surface declares. The list comes off the surface's
own `# port:` markers
([schema § 26](../plugins/mjolnir/config/schema.md#which-section-a-ports-operation-list-is-read-from)),
so a port is held the moment it is declared. Two properties of that loop are asserted, since the
way this gate would fail is by holding the general machine against one port: that the surface
declares more than one port, and that the one `load()` answers for with no argument is among them.
Every plant is spliced into the port's own section rather than into the document: a plant on the
operation column's name would hit whichever section stated it first.

One check is the half the per-port lookup cannot see: an operation table sitting under a section no
`# port:` marker names is refused on the surface, that being an operation list no port reads and no
adapter is held to.

One check runs the file as a script, in a subprocess. The contract states *three answers, never a
traceback* — the stated fallback where a capability is absent, the result where it is present, and
a `failed` outcome naming the host's own words where a call did not go through, per
[schema § 3](../plugins/mjolnir/config/schema.md#the-operations-and-what-an-absent-capability-does)'s
rule that no absence is an error and that a host which did not answer is not a tracker that
cannot. An implementation does `import port`, so running the file as a script loads it twice —
once as the entry point and once under its own name — and the contract's exception becomes two
unrelated classes, which the `except` in the invoking code cannot bridge. An in-process suite has
one class and cannot see this, so the script has its own dispatch and the case is a subprocess.
The failure is provoked with no host and no credential: the client is absent from the path handed
to the child, so the first call out raises from inside an implementation. The verdict is read off
what was printed, not off the exit status — a reported failure and a traceback both exit non-zero.

The kinds are the same two as above. Reading the operation list and the fallback text out of the
surface is **computed** — a reworded fallback travels, and a table that states the list twice, or
states an operation twice, or loses a cell out of a row, reddens rather than silently changing
what a role is told. One check is **forbidding**: that the contract itself names no tracker the
surface declares, in the slug spelling or the prose one and in any case, to the same de-slugged
grammar check 6 above uses and with the kinds derived by asking the reader which `kind` values are
trackers.

### What it deliberately does not check

- **That an adapter is correct.** The gate imports whatever is installed, and what it asserts
  about an implementation is that the install is load-bearing and that the report names exactly
  the operations that implementation leaves alone. It performs no operation against a host —
  the job carries no credential, and every branch that invokes an operation runs against a double
  or a stated-empty registry rather than against whatever happens to be built. An
  implementation's **own** decisions — a cursor followed to the end, an id resolved by name, a
  guard that refuses before it writes — are held by the gate recorded in the next section, which
  is a different subject and a different workflow. Whether a call actually does what the
  tracker's API documents is held by neither; it is held by running it, and the measurements live
  on the work item.
- **Any module but the contract.** `plugins/*/scripts/` sits outside the sweep's strict set, an
  implementation being written in some language; that exemption is an artifact of the strict set
  being path-shaped, not a reason to exempt a module from the *tracker*-name rule. So the contract
  asserts the rule of **itself**, and nothing holds the reader beside it or the adapter modules,
  where a kind's name is legitimate anyway. A carrier root is still swept by check 6 above.
- **That a fallback is the right fallback.** Whether writing a gate result into a description is
  what a project wants where comments are impossible is a judgement, not something a check can
  read — the *fidelity* limit.

## Beside the contract: each implementation's own suite

`plugins/mjolnir/scripts/adapter_suites.py` runs in the `Adapter suites` workflow, with no
credential and no network. It asks the port what is installed and runs whatever suite each
implementation exposes. It is one entry rather than one per tracker: a gate entry per
implementation would spell a tracker's name in this repository's configuration and again in a file
name, and a port's own package is the one place in the toolkit where the thing behind it may be
named. It is one entry across the ports as well: the runner asks the surface which ports there are
and sweeps each one's package, so a new port's implementations are covered the moment they land.
Beyond running the suites it asserts that every declared port has an implementation installed;
an implementation with no suite is reported, not failed.

What it holds is per implementation, and the implementation states it: the contract's suite reaches
none of it. For the board behind `kind: github-projects` that is every list read whole or refused
rather than returned short — the measured ceiling being a first page that reads as a complete
answer — every id resolved from the board by the name a configuration gives, every value shaped by
its own column's type, and every operation that writes reading the item first, so that a number
naming a pull request is refused *before* the write rather than after it. Where a milestone is the
grouping it is also that every item in it is read, that one off the board stays in the set and is
named, and that what the milestone cannot hold is reported — the omissions being
[schema § 4.8's](../plugins/mjolnir/config/schema.md#48-grouping--what-a-set-of-items-is-planned-into)
to list. The matching of a value to a milestone is one module, read by both kinds on that host.

For the cards behind `kind: trello` it is a different list, because the tracker is: a state resolved
to **one** list by name, with an ambiguous name and a name the board does not have both refused
rather than resolved by position; a card number resolved through the board's own index, re-read once
before refusing, because the number is relative to its board and is not an address any endpoint
takes; the number read from the field and parsed from the URL in that order, the URL arm being the
one a real interface over this tracker makes necessary; a collection refused at the host's ceiling,
there being no cursor to follow; a filing that resolves the `initial` role, because a card cannot
exist with no list; and every write that carries text held to `policy.forbid_on_item` before the
call, rather than asking a role to observe it.

The forms that decide whether a span belongs to a barred class are one module,
`adapters/_policy.py`, not one per implementation — the rule they answer being
[schema § 3 → A write forbidden by policy rather than by capability](../plugins/mjolnir/config/schema.md#a-write-forbidden-by-policy-rather-than-by-capability).
Two modules carrying one grammar are two statements allowed to disagree. What stays per
implementation is the **refusal**, whose wording names the thing a write was about to reach — a
card, an item.

For the issues behind `kind: jira` it is a third list again, and the tracker is the reason: the
identifier is a **key** and not a number, so the guard every operation resolves through is that the
key belongs to the project this configuration states — a key resolves across the whole site, so one
from another project answers perfectly and every write lands in somebody else's backlog. Beside it:
a status reached by the transition that **leads to** it rather than by the transition's own name,
with a word no move reaches refused and both readings of that stated; a dependency whose direction
is held by a **round trip** rather than by reading the call, because the write and the read are two
separate chances to invert the tracker's own inward-against-outward wording; a body rendered to the
document shape this tracker takes and read back from it, with the shapes that do not survive named
in the module and asserted to come back as the text they were written as; a search bounded by the
project, which is the host's own requirement rather than a convenience, and every term quoted into
its operand so that no caller can narrow the states a duplicate check covers; and a field addressed
by **name** and resolved against the site's own catalogue, every custom id being site-specific;
a list written by the element type the catalogue states, replacing what was there and read back;
and the fields a filing owes sent in the create itself, one nobody supplied refused before it.

The address and the credential are resolved above the transport, which is a *seam*, per
[schema § What earns a test](../plugins/mjolnir/config/schema.md#what-earns-a-test-and-what-makes-its-red-believable)
— resolved inside it, both guards are walked past by the substituted transport, and
a site carrying a path and a shell holding no token read as calls that went out and were
answered. The suite
asserts the transport is **handed** an address and a credential rather than reading either. In
the port's own suite, the kind a double is registered against is derived from a stated word, not
chosen from the set the surface states, which would leave no uninstalled kind once every
implementation lands.

Two of the card implementation's properties are about the report rather than the call. The first
is
[schema § 14's own rule](../plugins/mjolnir/config/schema.md#nothing-credential-shaped-leaves-for-a-surface-outside-the-project)
that a refusal never quotes the value it refused: the key and the token travel as query
parameters on this tracker, so every failure message quotes a call that carries them; the suite
plants recognisable values in the shell, fails a call, and asserts the message names the two
**variables** and contains neither value. The second: the four operations that carry a person's
text each refuse a planted barred span with the write unmade, beside a sentence that has to stay
green.

Two kinds, as everywhere here. **Computed**: the operation set is compared against the list
[schema § 3](../plugins/mjolnir/config/schema.md#the-operations-and-what-an-absent-capability-does)
states, so an operation the surface grows is unimplemented-and-unaccounted-for rather than quietly
missing, and the implementation names the ones it leaves out on purpose in one place the suite
reads. **Forbidding**: no shipped carrier — skill, command or hook — carries a board, field, card
or option id, in any of the spellings the host hands out. That sweep is the mechanical half of
`resolve: by_name`, and the shape it forbids is the measured one: a table of option ids pasted
verbatim into three skills of one project, with the same ids inlined again in four mutations.

An implementation with no suite is reported and not failed: one proved against a live tracker is
a decision somebody made. Finding no implementation at all **is** a failure, since a runner
holding nothing reports green.

A suite lives in a module beside its implementation. A file carrying both can exceed the host's
per-file patch limit (about a hundred kilobytes), and the gate on the change refuses a
**modified** file nothing read. The suite's module name opens with `_`, the port's own rule for a
module in `adapters/` that is not an implementation: discovery skips those, and the runner reads
the same rule — a suite imports the names it exercises, `KIND` among them, so without it a suite
counts as a second implementation of its own kind.

### What it deliberately does not check

- **Anything the host does with a payload.** Every case answers through the seams the
  implementation names — the client call, and the one probe that reads a failure rather than a
  body — so a suite here cannot establish that a mutation lands, that a cursor the host issues is
  the one it accepts back, or that a column holds what was written into it. That half is driven by
  hand against a live board and recorded on the work item.
- **That a fallback or an absence is the right one.** Three operations have no implementation
  behind the board because an issue has no check-item object; whether writing a task list into a
  body is what a project wants is the judgement behind the fallback, not something a check reads.
- **Which implementations ought to exist.** The runner reports what is installed. A kind the
  surface states and nothing implements is a work item, and the port already reports it apart from
  a project that needs no tracker.

### The one kind of plant that cannot be in-suite

The sweep for ids plants one of each spelling the host hands out and asserts the grammar reddens on
each, beside a sentence about ids that has to stay green; the refusals around a short list plant a
page that claims a successor with no cursor, a cursor the host repeats, and a cursor that never
ends. The behavioural half cannot be planted from inside the suite, because the thing to plant is
the code under test: those assertions are proved to bite by breaking the implementation, running
the suite, and reading *which* assertion goes red — the break undone from a copy of the file. The
breaks, and the assertion each one reddens, are recorded on the work item.

The fixtures follow from what such breaks find. A fixture thin enough that the operation fails for
another reason lets an assertion about a refused write pass while the write was unreachable.
So a pull request's payload answers in the same shape an issue's does, and a fake answers every call
the host would answer — a fake that refuses an unexpected call turns a behavioural red into a
traceback. A value computed inside an assertion — `item_number(card) == 75` written out — raises
where the comparison is, so removing the arm under test ends the run having printed no failure at
all; every read of an operation's answer goes through a helper that reports a refusal as a value.
A fake whose two answers about one card are built separately can disagree, so that
an archived card reads back open against the fixture; the single-card answer is read out of the
same index the collection answers with.

A fixture URL is a shape, not one read off a live board: the sweep in `tools/`, whose other half
is [the surface's rule that no value appears under a
carrier root](../plugins/mjolnir/config/schema.md#the-configuration-surface), refuses a real one.

## Beside them: the claim on a work item

`plugins/mjolnir/scripts/claim.py --self-test` runs in the `Claim carrier` workflow, with no
credential and no network. A reviewer could not hold its claim at all: what is asserted is that an
operation *races* correctly.

The rule is
[schema § 10 → The claim on a work item](../plugins/mjolnir/config/schema.md#the-claim-on-a-work-item),
and what the suite holds is this: that a second session starting an
item already claimed is refused; that the refusal names who holds it and since when, or names
whichever half it could not establish; that a refused start leaves no ref, no branch and no tree;
that a released claim is takeable again and a release is re-runnable; that a removal git refuses
is reported as not removed, beside what became of the ref; that a claim with no work
and no occupied tree reads as an *orphaned candidate* carrying both readings rather than being
broken; that a ref younger than the window a start takes between publishing its ref and cutting its
tree reads *provisional* instead, with re-reading rather than asking as its remedy; and that a root
with no remote claims locally and says so.

| # | Check | Scope | Kind |
|---|---|---|---|
| 0 | A second session claiming a taken item is refused, by **each arm separately** | two clones of one bare repository | computed |
| 1 | A refusal names the holder and the time, or names the half it could not establish | the refusal's own text | forbidding |
| 2 | A refused start leaves no ref, no local branch and no tree, in **both** shapes of a refusal | the loser's clone, and a clone whose tree directory is taken | computed |
| 3 | A claim releases, and the item is claimable again | one clone | computed |
| 4 | Liveness answers from each of its arms, and otherwise reports an orphaned candidate | both clones | computed |
| 5 | A root with no remote claims locally rather than failing | a remoteless repository | computed |
| 6 | Releasing a live claim held in no tree here is refused; the holder's own clone releases it freely | two clones | computed |
| 7 | The integration branch is derived from the remote's default, overridable, and named as underivable rather than guessed | three repositories | computed |
| 8 | A process **below** a tree's root reads as occupying it | a real process two directories down | computed |
| 9 | A squash-merged claim reads **landed** rather than live, and releases with no override | a real squash merge, after asserting the same ref read live before it | computed |
| 10 | A claim that is neither landed nor held in a tree here is refused by `release`, fresh ones included | two clones | computed |
| 11 | The branch name is **derived**, and a second interpreter derives the same one from each of the three titles two sessions divided on — planted by removing the **bound**, which overruns it on every one of those titles as all six published names did | the derivation, in two processes | computed |
| 12 | The bound is spent on **whole words**, planted both ways — a character cut at the same bound ends on half a word, and the function words kept spend the bound on them — and punctuation, case, digits, a repeated word, a word longer than the bound, a non-Latin script, a decomposed title and a title with no major word in it each slug as stated, and every entry of the word list is lowercase letters so none of them is silently dead | the derivation | computed |
| 13 | Two sessions under **two names for one item** produce one claim, with each arm of the item guard attributed separately | two clones | computed |
| 14 | A **landed** ref still matches the item's name and the item still reads free, and a start on it is not refused | two clones, after a real squash merge | computed |
| 15 | A merged pull request that **predates the ref** does not land it, and either instant unreadable makes the arm decline | the comparison, with the measured timestamps | computed |
| 16 | A ref **gone between the listing and the read** holds the item against nobody, and the report says it is gone rather than printing `free` under a `taken` verdict | one reading, constructed | computed |
| 17 | The **window in front of the orphaned reading**, held on both sides of its bound and on the half it declines on — planted by setting the bound to zero, which is the carrier as the defect was measured on it | two clones, with both instants stated | computed |
| 18 | A **resource check** that names something, fails, does not finish in time or is left no time keeps the tree and the claim whole, `--force` included; one naming nothing lets the removal through; it is asked after a teardown and read by the release itself | two clones, the check answered each way | computed |

Check 0 is run once per arm. Two sessions claiming one item push the **same** integration tip, so
git declines to send the push at all — exit zero, no update attempted, the lease requiring the ref
not to exist never consulted; a probe pushing a *differing* sha to an existing ref exercises only
the lease. So each arm is planted away while the other stays, and the check is believed only where
removing *that* arm is what lets the race through.

Checks 11 and 13 answer one failure — one item started twice under two names, the sessions
carrying different amounts of the title — and are kept apart because they cover different
configurations. The derivation (11) makes two sessions handed one title publish one name, and the
ref's own test-and-set arbitrates; check 13 plants the derivation's agreement away and holds the
residue, which is § 8's translation case and anything named by hand. Each arm is attributed
separately, as in check 0: with both the guard's arms removed, two sessions claim one item and the
suite says so.

Check 11's plant removes the **bound**: the bound-free derivation answers the longer name a sibling
session published, for two of the three items. An assertion that two hardcoded branch names differ
reads only the table of measured names and stays green with the derivation replaced by a constant
— a planted violation that does not reach the mechanism.

Check 15 is held without a host. The failure is a ref reading *landed* on a pull request that
merged before the ref existed, against a deleted ref of the same name — a comparison never made —
so the comparison is what the suite holds. The wiring was proved by hand against the live host:
the same ref read `landed … releasing it needs no override` on the carrier before the change and
`orphaned-candidate` after it.

Check 17 exists because every arm above the orphaned row declines for timing rather than for
state. Measured across three sibling starts inside seven minutes: a refusal read
`orphaned-candidate: no arm of the liveness test answered yes` against a ref published 36 seconds
earlier by a live session, and the same ref, untouched, read `live` five minutes later. The reading
is decidable by waiting, which makes *read it again* an answer and asking a person the wrong one.

The plant is the bound set to zero. The bound is the one
[schema § 10 → The claim on a work item](../plugins/mjolnir/config/schema.md#the-claim-on-a-work-item)
states. With the bound at zero the same reading comes back orphaned, the carrier as the defect was
measured on it; with it in place the reading is provisional. Both instants are **stated** rather
than taken from the clock, so the two sides of the bound are reached without sleeping through it.

They are stated as absolute offsets — the interval the defect was measured at, and an hour — not
relative to the bound: written as `the bound ± 1`, the block follows the constant wherever it is
moved, so planting the bound to a negative takes both offsets with it and most of the block stays
green on a broken mechanism. The mutation count is the tell, which is why the table below is run:

| what was disabled | what the suite did | restored |
|---|---|---|
| the window arm never fires, its bound planted to a negative | 4 lines red | 0 |
| the arm fires and sets no provisional flag | 3 lines red | 0 |
| the age dropped from the reason, the bound left in it | 1 line red | 0 |
| the report renders a provisional reading through the orphaned wording | 1 line red | 0 |
| an unreadable creation becomes provisional rather than declining | 3 lines red | 0 |
| the incomparable-instants decline removed | **crash**, no line red at all | 0 |

The last row is the reason the decline is there. Removing it does not redden the suite; it kills
it, the subtraction raising on an instant carrying a zone against one that does not — on the path
that reports a refusal. A mutation that crashes is a reached mechanism, but **not** a check shown
it can fail, and the row says which it is.

Green sides are asserted beside it, because this reading is a new branch through code other
consumers key on: `provisional` sets neither `live` nor `landed`, so the release's *landed or held
here* test and the sweep's *not landed* branch are unmoved; a provisional claim still refuses a
start; and a ref whose creation cannot be read keeps the orphaned reading and **names** the half
it could not establish. That last is the arm this repository's own remote always takes in the
suite — a bare repository records no branch creation.

The report check holds the spelling `orphaned-candidate`, which names the question a person is put,
not a verb: the provisional wording ends *"rather than asking"*, so forbidding *ask* would match
its own remedy.

Check 2 has two shapes. A refusal on the *branch name* never reaches the local half — the push is
what refuses. Where the name is free and the *tree directory* is taken, git creates the branch and
then fails on the path, which would leave a local branch pointing at the base with no tree and no
commits: a false claim, and a durable one, since a pre-filter matching the item's number against
the ref tail reads it as held forever. The suite refuses in each shape separately, and asserts the
opposite direction too — a branch that existed *before* the attempt is left alone, because a
rollback that deletes whatever it finds deletes somebody else's work.

### What this check deliberately does not hold

- **True simultaneity.** The second arm's real trigger is a ref appearing between one session's
  read of the refs and its write, and nothing here reproduces that window. The arm is exercised
  directly instead — an update to a ref the lease was told must not exist — and the two arms
  together cover the two orders. What is untested is the *interleaving*, not either mechanism.
- **The host's own record.** Who pushed a ref and when is read from the host, and the suite's
  remote is a bare repository that records neither. So the half the surface requires be *named as
  unestablished* is what gets asserted, and the populated half is proved against the host by hand.
  That read is bounded by a page of the host's activity, so a claim older than the window reports
  the time as unestablished rather than reporting the ref free.
- **That an orphaned candidate is genuinely orphaned.** It cannot be known from outside: a session
  that died holds the same ref as one about to commit. The check holds that both readings are
  stated and that nothing is broken automatically, which is the whole of what is decidable.
- **The third liveness arm, against a host.** An open pull request referencing the ref needs a
  credential, so in the suite that arm reports itself unestablished and the first two carry the
  verdict. On a project whose claims are all fresh refs with no commits, that leaves liveness
  resting on the occupied-tree arm alone — the precondition the window of check 17 sits in front of.
- **The wiring from the host's record into the window arm.** Check 17 hands the arm a creation time
  directly, as check 15 does. Proved by hand: the holder read against the live host returns a
  populated, zone-carrying stamp that the comparison's own parser accepts. Unheld anywhere is the
  join — a real ref read end-to-end *inside* its own window, which needs a session caught between
  its publish and its cut.
- **Whether a process occupies a tree, where the open-file table cannot be read.** The arm has
  three answers and the third is *unestablished*, never *the tree is idle*. Check 8 holds the
  at-or-below half against a real process; no check holds the **unreadable** branch, a machine
  where the table cannot be read not being a fixture this suite can build. On such a machine the
  arm reports rather than answers. The sweep over landed trees reads this same arm, so the
  unreadable branch is unheld in **two** suites, not covered twice.
- **A claim broken with the override.** Check 6 holds that the refusal happens and that it names
  the decision as a person's; it cannot hold that the person was right — the *fidelity* limit, and
  the reason the override is a flag rather than a heuristic.
- **A branch whose own commits cancel out.** The content half of the landed test asks whether the
  ref differs from the integration branch, and work that adds something and takes it away again
  differs in nothing — so it reads *landed* having never merged, and there is no merge for the
  host's record to find. A claim with a net-empty diff has nothing to lose by being released; this
  is the one case where the reading errs towards *releasing*.
- **A claim squash-merged and then built on top of.** Check 9 holds the plain squash case. Where
  other work lands on the integration branch afterwards, the ref is an ancestor of nothing and
  differs from the branch in that other work, so only the host's record of the merge settles it —
  and that needs a credential the suite holds none of. Without one the reading is *live*, which
  refuses a start rather than taking a held claim; the ordering of that table reads the strongest
  signal first for this reason.
- **A claim on a project sharing no remote.** Two machines with no remote between them cannot be
  arbitrated by anything, and the surface states that rather than guarding it.
- **The host's pull-request arms against a real host.** Check 15 holds the comparison and nothing
  runs `gh` in the suite, so what is untested here is that the field read carries the instant the
  comparison needs. The *open* pull request arm has the same name-reuse exposure and is left
  alone: a reused name whose previous occupant has an open request reads **live**, which refuses
  a start and asks for an override to release — the safe direction.
- **Two sessions reaching the second item read together.** Both give their refs up and the item
  is left free; true simultaneity is not a fixture the suite can build. Each arm is held
  separately; that the interleaving ends in a refusal to both rather than a claim to both is
  reasoned.
- **A tracker whose identifiers are not digits.** The item a branch carries is recovered from the
  name only where it is a run of digits, so a project whose keys carry their own separators
  states the item rather than having one guessed out of a slug. Where it is neither stated nor
  recoverable the guard does not run, and the ref name is the whole of the claim.

## Beside the claim: the sweep that removes a tree whose branch has landed

`plugins/mjolnir/scripts/prune.py --self-test` runs in the `Landed trees` workflow, with no
credential and no network. Unlike every other run in the list, which fails by reporting something
wrong, this one can fail by **deleting a working tree** — the only copy of everything in it that
version control does not track.

The rule is
[schema § 10 → Pruning a tree whose branch has landed](../plugins/mjolnir/config/schema.md#pruning-a-tree-whose-branch-has-landed),
and the module carries no second reading of *has this landed*: it imports the claim's own, and its
suite asserts that the surface still states the subsection it performs and that the carrier still
calls it on the event that opens a session.

| # | Check | Scope | Kind |
|---|---|---|---|
| 0 | A landed tree is **removed**, and the local branch goes with it | a clone whose branch landed by content, with no host asked | computed |
| 1 | A branch that has not landed is never removed, and the report says which reading kept it | one clone, one tree | computed |
| 2 | A branch whose landing the host could not answer for is kept, and the missing answer is named | a liveness reading carrying an unestablished half | computed |
| 3 | A tree holding an ignored file no rebuild writes again is kept and the file **named**; declaring that path regenerable removes the same tree | one tree, both directions | computed |
| 4 | An ignored symlink is never precious, and what it pointed at survives the removal | a symlink to a file and a directory of symlinks, both ignored | computed |
| 5 | A bare entry matches the path wherever it appears, a directory entry covers everything beneath it, and a name matching nothing covers nothing | the matching rule alone | computed |
| 6 | An untracked change keeps the tree **even with everything declared regenerable** | one tree, the list set to match all | computed |
| 7 | The main checkout is not a tree the sweep looks at | every entry of a worktree listing | computed |
| 8 | A tree another live session occupies is kept, the occupant named; an unreadable table keeps it too | the occupancy reading in each of its three answers | computed |
| 9 | The caller's own tree is **stopped on**, and a later session standing outside it removes the same tree | this process's own working directory, moved and moved back | computed |
| 10 | A tree the harness cut inside the checkout is named and not removed | a real nested worktree | computed |
| 11 | The published ref is reached under `procedure` and left standing under `host` and under `never`, the tree and local branch going either way | three configurations, one per value | computed |
| 12 | A budget that runs out stops the sweep and **names** every tree it did not look at | a clock the suite advances | computed |
| 13 | A kept tree is read again on the next sweep rather than recalled, and nothing is written into it | two consecutive sweeps over one tree | computed |
| 14 | A project that states no configuration, and one that cuts no tree, are each answered with silence | two synthesised projects | forbidding |
| 15 | A configuration that is stated and does not resolve is reported, and a sweep that cannot run reports examining nothing | a project whose file is broken | computed |
| 16 | The budget plus one tree's reserve is shorter than the timeout the carrier registers | the carrier and this module together | computed |
| 17 | A landed tree carrying a commit the reading never saw is kept, the commit **named**, and the person told; with nothing unpushed the same tree is removed | a branch pushed, landed by content, then committed to without pushing | computed |
| 18 | A ref the host deleted on merge still answers *landed*, read from the branch on this machine, and the sweep prunes under `delete_branch: host` | the same fixture with its published ref deleted | computed |
| 19 | A tree **outside** the stated tree directory is named and not removed, whether a harness cut it inside the checkout or a person cut it beside one; a tree **under** a tree directory that is itself inside the checkout is pruned | three real worktrees across two repositories | computed |
| 20 | A reading that raises for one tree leaves the other's verdict standing, the removal that happened still reported; only a failure to list the trees at all is the run's | one tree's reading raised deliberately | computed |
| 21 | A removal that reported success while the tree is still there is not a removal, and the person is told | a remover that returns success and removes nothing | computed |
| 22 | An ignored path whose own name carries the rename separator is read whole, and one outside ASCII arrives unquoted | two such paths in a real tree | computed |
| 23 | A registration whose directory is gone is read as prunable and cleared, rather than reported at every session open | a tree removed from under its registration | computed |
| 24 | The stop reads the directory it is **handed** — the session's — so a session standing in its own tree holds it whatever this process's cwd is | both answers of the shipped reading | computed |
| 25 | The event hands the sweep the configured list, `delete_branch`, the tree directory resolved against the code root, and the session's directory | the arguments captured at the boundary | computed |
| 26 | An entry naming nothing exempts nothing; an entry anchored at the root matches there and nowhere else | the matching rule alone | computed |
| 27 | A tree whose contents could not be read is unestablished, never empty; an unreadable directory is not all-symlinks | a directory with its mode taken away | computed |
| 28 | A worktree registered **inside** a work tree is outside the scope, being a level deeper than the leaf, while the work tree itself stays this project's — and that work tree is then kept, with the nested path named as a reader would want it | a real worktree cut inside a work tree, in a project whose tree directory is inside its checkout | computed |
| 29 | A stated teardown runs before the removal and is told the tree; one that failed, outlasted what is left of the bound or had too little left to start keeps the tree and reaches the person; a kept tree is never torn down | one landed tree, the clock stated | computed |
| 30 | A landed tree whose resource check names something is kept and the name reported; one whose check failed, or that the bound left no time for, is kept and reported unanswered; one whose check names nothing is removed; the event hands the sweep the configured check | one landed tree, its check answered each way, and the arguments captured at the boundary | computed |

Check 16 holds, for the reason § 10 gives about a carrier the harness kills, that the timeout
covers the budget **plus** what one tree is allowed to cost.

### What this check deliberately does not hold

- **The host's own record of a merge, and with it the whole merge-commit shape.** The landed
  reading's second test needs a credential and the suite's remote is a bare repository on disk, so
  what carries every verdict here is the **content** arm. A branch that landed as a **merge
  commit** is an ancestor of the integration branch and carries no commits of its own, so the
  content arm does not fire and the host's record is the only test that recognises it. Ancestry
  would separate the two shapes and § 10 forbids it by name — a claim taken a minute ago is an
  ancestor too. Without a credential a merge-commit landing reads as an orphaned candidate and the
  tree is **kept**, so the accumulation § 10 measures is a disk cost rather than a data one.
- **The occupancy reading itself.** Every sweep arm in this suite injects it, because a machine
  where the open-file table cannot be read is not a fixture that can be built either way. What is
  held here is that each of its three answers reaches the right verdict; what holds the reading is
  the claim's suite, against a real process.
- **A session a harness genuinely refuses to let out of its tree.** Check 9 moves this process's
  own working directory, which is the whole of what the reading asks — but the *unavailability* of
  an exit is a property of the harness, so a launch-pinned session is reasoned about rather than
  built. The two cases are indistinguishable from inside the sweep: both are a tree the caller is
  standing in, and both are kept.
- **Whether a `regenerable` entry names something a rebuild really writes again.** That is a
  project's claim about its own build and no check can verify it. The failure direction is a
  tree removed with a file in it, which is why the surface states the empty list as the safe form
  and why the entry's shape is refused by the reader rather than tolerated.
- **That a removal was what somebody wanted.** A merged branch is removed without asking per
  occasion, deliberately — asking per occasion is what produced the accumulation § 10 measures.
  What stands in for it is that nothing uncertain is ever removed, which is checks 1, 2, 3, 6 and 8
  together.
- **The trees a harness cut for its own helpers.** Checks 10, 19 and 28 hold that they are named
  and left alone: at the managed root the configured directory sits one level below, which is where
  such a tree was measured, and at any other depth under that directory, which check 28 places
  rather than measures. Reaping them is a different question with a different owner, and a sweep
  that removed them would be removing trees whose branches it never read. Check 28 also records
  the price: a work tree holding a worktree of any kind is itself kept, that directory being
  untracked content no rebuild writes again, so the accumulation moves up one level.
- **Ignored files inside a submodule.** The superproject's status says nothing about them — a
  submodule holding only ignored content is clean — while the removal takes the submodule with the
  tree. No check here holds it: the fixture would need a submodule, a shape this project does not
  have.
- **A long-lived process of the person's own, in the same login session.** The occupancy reading is
  the POSIX session, which is what tells a run's own helper from another session; the inverse case
  is a server started from the same terminal the session was launched from, which shares its
  session and reads as *not another session*. Narrowing it would let a keep-awake helper hold every
  tree forever.
- **What one tree's own calls cost.** The reserve keeps a tree from *starting* without headroom; it
  cannot bound a call already running, none of which carries a timeout of its own. A tree whose
  host lookup hangs still outruns the event's limit, and a killed carrier emits nothing.
- **A worktree path containing a newline.** `-z` is what makes the parse correct for one; the
  fixture's path carries **spaces** rather than a newline, which is not a directory this suite
  will create. What is held is the parse's shape; that
  the record boundary is the separator git documents is reasoned.
- **That anybody reads the report.** It is addressed to the person on the event that opens a
  session, and no gate holds a person to having read it.

## The rules loaded rather than checked

`plugins/mjolnir/scripts/load_the_rules.py`, on a `SessionStart` hook and on a `PostToolUse` hook
matched on the tool that enters a tree. It reads a table out of the
surface under each of two subsections' anchors and hands both to the session as context: the
property table of
[schema § 8](../plugins/mjolnir/config/schema.md#the-reply-to-the-person-running-a-role), and what a
shell command may be once the session is standing in its own tree,
[schema § 10](../plugins/mjolnir/config/schema.md#what-a-session-standing-in-a-tree-can-run). No
copy of either table lives in the script, and neither do their column names: a row edited on the
surface is a row the next session is handed, and the heading row is read out of the document like
every other row.

It is also the carrier for the one message a project that states no configuration ever gets, by
[schema § 7](../plugins/mjolnir/config/schema.md#a-hook-in-a-project-that-states-no-configuration):
where the reader finds no configuration under the directory the event names, no rule is loaded and
the person is invited to write one, with the file to write and the document its keys are stated in
both named. The two answers are exclusive, and the run asserts each against the other. This script
carries that message only because it answers the event the exception is scoped to.

One loader serves both rules, unlike the gates here, which are one script per question: both are a
table in a subsection, read at an event that reaches a writer before it writes, with the same
failure mode. What is held per rule is the assertion — the self-test runs its plants once per
anchor, and asserts that a rule it cannot read leaves the other one loaded.

One script runs on two events, and the second carries the tree-scoped rule alone: re-handing the
register on every entry would re-send a rule the session has had since it opened. The matcher is
as load-bearing as the event, the carrier being where a hook is registered
([schema § 7](../plugins/mjolnir/config/schema.md#7-carrier)): this same script under the `Bash`
matcher would fire on every shell call in the session and still satisfy a check that asked only
whether the event named this script, so the suite finds the entry **by its matcher** and requires
that one to call it.

The events were chosen by three probes, each with a random token no session could otherwise know.
A `Stop` answer's `systemMessage` was written to the transcript, rendered to the person, and
**absent from the next request** — so a register reported after a reply changes no text. A
`SessionStart` answer's `additionalContext` was **named back exactly** by the session it opened. A
`PostToolUse` answer's `additionalContext`, on the tool that enters a tree, was named back by the
session that had just entered one, with the tree the harness reported in it. Only the channel that
reaches a writer before the writing can carry a rule.

The rows are rendered as a table because the cells have to be delimited: rendered as
`- Property — required. Not: forbidden`, a session read the last row's third cell as running into
the paragraph after it and quoted the splice back as the rule.

The tree rule — [schema § 10 → What a session standing in a tree can
run](../plugins/mjolnir/config/schema.md#what-a-session-standing-in-a-tree-can-run) — is handed over
again when the session enters a tree. Entering is a **tool call**, so `PostToolUse` matched on it
fires then, and the payload carries the tree in `cwd` and in `tool_response.worktreePath`. The
opening event alone does not reach the moment the rule is live: across 25 sessions in this
project's session store handed the tree rule by it, **not one was standing in a tree when it
arrived**; 19 of the 24 that were not the probe session had a call refused as unverifiable in their
tree, 52 refusals in all, each session's first one 134 to 1,030 transcript entries after the rule
and after the session had entered a tree. So the closing sentence is a function of where the
session is standing, not a constant.

`WorktreeCreate` is not the carrier. It fires on the same operation, but `additionalContext` is not
a valid shape in its output, and the invalid answer **fails the worktree creation outright**,
leaving the session in the checkout. A hook that loads a rule must not be able to stop the work;
and that event's payload predates the tree, naming the checkout as `cwd` and the new tree by name
alone. `CwdChanged` did not fire on entering one at all.

Both rules reach every session, including the ones the tree rule is not live for yet; where the
session is standing decides the sentence, never whether the table arrives. It is read off the
repository, not off a path: a linked worktree's `.git` is a **file** naming a `worktrees` segment,
where the main checkout's is a directory and a submodule's names `modules/`. A tree that reading
cannot recognise — a project whose trees the harness delegates to a hook instead of cutting as git
worktrees has no pointer to read — is told what would make the rule live, rather than nothing.

### What it deliberately does not do

- **It fails open and silently**, which is this script's choice rather than a rule of the
  procedure: failing loudly would interrupt a person over a file they may be mid-edit on. Nothing
  in a session says a rule went unloaded; the gate covers that — the `Rules loaded` run asserts each
  table is found and every row reaches the context, with a planted surface it cannot read.
- **It does not check that either rule was followed.** Nothing reads the reply afterwards for any
  property in § 8's table, and nothing reads a command before it runs for anything in § 10's — the
  refusal that holds the second half is the harness's own and is not this project's to configure.
- **It cannot tell which role is running**, so every session of a project that states a
  configuration is handed both rules — the safe direction, per
  [#87](https://github.com/ragnor-rs/mjolnir/issues/87)'s ruling.
- **Nothing is handed over when a session *leaves* a tree.** After an exit the live sentence names
  a tree the session has left, so the rule reads as live where it no longer is. That is the safe
  direction: the cost is one plain command per call where a chain was possible, against a refused
  call and a lost round trip in the other direction. The same event is available, matched on the
  tool that leaves.
- **The invitation is repeated once per session rather than once per project.** Nothing is
  recorded about having said it, so a person who is never going to adopt the toolkit in a given
  project reads one line at every session opened there. The alternative is a marker per project,
  which trades that line for a state nobody can see and a message that stops arriving for reasons
  nobody can read.

## The reply defers nothing: held in the session, not on the gate

`plugins/mjolnir/scripts/check_reply_defers_nothing.py`, on a `Stop` hook, holding
[schema § Nothing is deferred](../plugins/mjolnir/config/schema.md#nothing-is-deferred) over one
artifact: the reply a role writes in the session.

It has one arm, and it holds no property of prose: Work the reply names and the turn does not do.
Every other property of a reply — its opening, its length, its register, its emphasis, how it
states uncertainty — is a rule
[§ 8](../plugins/mjolnir/config/schema.md#the-reply-to-the-person-running-a-role) states and a
session reads, and no check in this tree reads one.

It runs only in a project that states a configuration, by
[schema § 7](../plugins/mjolnir/config/schema.md#a-hook-in-a-project-that-states-no-configuration),
asked before the reply is read, so a reply in a project that adopted nothing gets no hand-back and
no report, and nothing is recorded about the turn: a project adopting the toolkit mid-session would
otherwise find its one hand-back already spent by a turn that was held to nothing.

It is a hook rather than a gate because the reply is the only artifact the loop produces that no
later check reads: no commit, no body, no thread. Work named there and not done is green
everywhere downstream. A `Stop` payload is the only place a finished reply exists — the harness
hands over `last_assistant_message`, so nothing parses a transcript.

The hand-back is `decision: block` with the findings as `additionalContext`, which the harness's
documented contract makes the field the writer reads back; the `reason` beside it is shown to the
person. It blocks at most once per turn, keyed on the harness's own `prompt_id` under
`CLAUDE_PLUGIN_DATA`, because a hook that also blocked the answer would hold the session open on a
judgement a forbidding check cannot make. A payload naming no turn cannot be guarded, and that is
**reported rather than treated as a spent hand-back**, naming which half could not be established.

It asks for the work and never for text — the form
[§ Nothing is deferred](../plugins/mjolnir/config/schema.md#nothing-is-deferred) states. Asked to
replace a parked span or re-send the reply, the cheapest compliant answer is to delete the sentence
that named the parked work: over the record, three real parkings were caught, three sentences were
rewritten, and **no work item moved**.

### What the record says, measured 2026-10-20

Over every session store of this project, 358 fires of this check and its predecessor:

| answer | fires | what followed |
|---|---|---|
| green | 265 | the turn ended |
| reported, `systemMessage` only | 64 | the turn ended, 64 of 64 |
| handed back | 29 | a further reply, 29 of 29 |

Of 30 recorded hand-backs, 3 were true, all one form — an offer standing in for the work. 17
fired on an emphasis density and 2 on a single arrow chain, both arms this project demoted; of the
11 parking hand-backs, 7 were false and 1 unreadable from its span. Four of the seven false reds
were cascades — a reply *about* this check reddening on this check's own vocabulary.

`systemMessage` never reaches the writer: a hook emitting a random token in that field alone fired,
wrote both a `hook_success` and a `hook_system_message` entry to the transcript, and the next turn
could not name the token. So a reported finding is a line to the person and nothing else. For
`additionalContext` the opposite holds, measured the same way: every summary carrying it recorded
`preventedContinuation: false` and every one was followed by a further reply, so **injecting
context costs a reply whether or not the answer blocks**.

### What it deliberately does not hold

- **Every property of prose**, which
  [§ 8](../plugins/mjolnir/config/schema.md#the-reply-to-the-person-running-a-role) states as a rule
  nothing mechanical reads — on this artifact or any other. A density over a reply's own lines is a
  form, but it still answers whether the prose is any good, which a machine may not judge. Both
  artifacts once held this way are retired; see
  [§ The file-prose floor, retired](#the-file-prose-floor-retired).
- **A reworded parking.** The forms are a closed list, safe in the direction that matters: a
  parking the list does not carry passes and leaves a finding missed, never a finding invented. The
  person reading the reply covers rewordings.
- **A filing that did not happen, and an artifact deliberately not written.** Adding `unsaved` to
  the list reddens **9** replies using *Deliberately unsaved* in the save role's own ruled sense,
  and adding *no issue was filed* reddens **6** honest reports: *No item was filed — #70 was
  reopened and edited*, *No work item filed: found and fixed in the same pass*. An artifact not
  written is not work not done, and declining a filing is what the measure-it rule asks for when
  the pass fixed the thing; no grammar here separates either pair. So a parking phrased as
  *## Left deliberately unsaved* is missed by rule, and the green side of both forms is planted.
- **Which role is running** — the reach this check has rather than a gap in it, and the ruling
  behind it is
  [schema § 7 → What a hook can establish about the role it is running under](../plugins/mjolnir/config/schema.md#what-a-hook-can-establish-about-the-role-it-is-running-under).
  What a `Stop` payload carries is stated there and not repeated here; what it does not carry is a
  role, so this holds every reply in a project that states a configuration rather than a role's.
  The narrowing that ruling leaves available is the unsafe direction for this rule: the per-turn
  question a hook *can* answer would hold the first turn of a role and none after it. Held widely,
  the over-reach costs a reply no role produced being asked not to park work; narrowed, it costs
  every parking after a role's first turn.
- **Whether the work actually got done.** The hand-back asks for it and the turn continues;
  nothing here reads the tree afterwards. The gate on the change reads that.
- **Two false-red shapes are planted in both directions**: the source marker is matched
  case-sensitively, so the ordinary English `todo queue` in a reply reporting that queue *empty*
  is green; and a section of open items accepts statements of absence beyond the bare word. Each
  carries a plant that must stay green, verified by reverting it.

## Prose line width: held on the gate for files, and nowhere for bodies

`tools/check_prose_width.py --self-test` runs in the `Prose width` workflow, with no credential
and no network. The rule is
[schema § 8 → Prose line width](../plugins/mjolnir/config/schema.md#prose-line-width); the check
is narrower than the rule in one direction, listed below.

What it holds: every tracked markdown file — documents, the README, the surface, the skills and
the configuration examples alike — against the width **this project's own configuration states**.
The script carries no number. It reads `language.prose_width` through the shared reader, so a
project that states another width, or states none, changes this gate's verdict by editing a
configuration and nothing else. The kind is **computed**, for that reason. A tree whose
configuration carries no width makes the check hold nothing, and it says so and reddens rather
than passing — the same rule the document checks apply to a glob that matches no file.

It plants both sides. Violations that must redden — an overlong paragraph, an overlong list
continuation, a tree with no width configured, a tree with nothing tracked, a tracked file it
cannot read, a frontmatter marker that never closes — and one exemption plant per excluded kind,
each of which must stay green. Each exemption is verified by **disabling its own exclusion** and
watching that plant redden. The run prints what it planted.

The plants are compared against the tree's **own** result rather than against zero: a whole-file
assertion reads every plant as red while one real overrun is still in the tree, which would make
the exemptions untestable in a change removing overruns.

### What this check deliberately does not hold

- **A body, a pull request or a review comment.** The half of the rule that is *procedure* — the
  half every adopting project inherits — is held by nobody. Those surfaces are not files, so this
  sweep cannot see them, and the gate that does read a pull request could only guess: a
  hard-wrapped body is distinguishable from a short one by heuristic alone — line breaks falling
  mid-sentence — which reddens on a deliberate break, a pasted quotation and a list. The rendered
  half is a convention, held by the writer.
- **Anything that is not markdown.** This repository's Python carries tens of lines past the width,
  the longest half as long again. A programming language's line width is that language's business,
  and the comments inside a configuration example are annotation on a line of data.
- **Whether a wrapped paragraph is wrapped *well*.** A line of twenty columns beside one of
  ninety-nine passes, because the rule is a ceiling and not a measure of raggedness — the
  *fidelity* limit.
- **A line made long by several short unbreakable runs.** Every run is set aside before the
  measurement, so a line of four code spans and a few words passes at well over the width while
  being breakable between them — a planted 144-column line of that shape is not reported. The
  stricter reading, *one* run, reddens the ordinary citation line this repository carries by the
  dozen. Nothing in the tree is exempt by this route.
- **A document outside the repository.** The ordering document and the per-item working papers
  live in the session store outside every tree (§ 11), where `git ls-files` cannot reach them and
  no width is stated for them.
- **The width as a configured *value*.** The sweep that forbids a configured value from appearing
  in a carrier root reads every scalar a configuration states, and a number is not one of them: a
  width is a bare integer, and a sweep that matched one would redden on every count, threshold
  and year in the tree. That leaves unguarded a role's text stating a width instead of reading it;
  the rule's reader is the writer of a document rather than a skill.

## The file-prose floor, retired

`tools/check_prose_register.py` held three properties of the prose a change wrote into a file —
restatement of a cited document, hedging at a density, emphasis as a default texture — on the lines
a change added. It is retired by ruling: **style is a rule, not a check.**

Reading only added lines on `pull_request` costs no re-read and interrupts no turn, so none of the
harm measured against the reply check applied to it; the ruling did. Its measurement is in
[§ The reply defers nothing](#the-reply-defers-nothing-held-in-the-session-not-on-the-gate).

The retirement removed the check, its workflow, its entry in `host.checks`, and the subsection of
[§ 8](../plugins/mjolnir/config/schema.md#the-reply-to-the-person-running-a-role) that stated the
floor. The reply's property table is whole — under this ruling that table *is* the rule.

What holds file prose is the language it is written in, and nothing else.

## An artifact states what is true now: held on the lines a change adds

`tools/check_no_audit_trail.py --self-test` runs in the `No audit trail` workflow with no
credential, but not with no network: the base derivation reads the remote's advertised default
where the checkout records none, so a run whose base branch the host did not state can reach
`ls-remote`. The rule is
[schema § The loop → An artifact states what is true now](../plugins/mjolnir/config/schema.md#an-artifact-states-what-is-true-now)
— the check is narrower than the rule, in the directions the list below names.

What it holds: the lines this change **adds** to tracked markdown, read off a diff against the merge
base with the branch the change is **against** — the base the run states where it states one, and
otherwise `claim.integration_branch`, the one derivation this repository has for which branch that
is. A base that resolves to this change's own head is refused rather than read as nothing added,
which is the state a checkout with no remote lands in. Table rows are in scope: the measured habit
lived in an ordering document's argument column. A document's fenced blocks and frontmatter are
out, and so is
any marker **shown** rather than used — an inline-code span or a quoted run — because the section of
the surface that states this rule has to spell out every form it forbids, and so does the check.

The kind is **forbidding**, not computed, and the run says so in its own output. Three shapes are
matched: a dated record of a pass, a figure
stated beside a former value, and a clause whose subject is the pass before this one. The fourth
shape the rule names — a per-pass paragraph appended where a line should have been overwritten — is
held only insofar as it carries one of those three markers.

It plants both sides, and the run prints what it planted. The green plants are of two kinds. An
**exclusion** is something the check sets aside — the lines a change did not write, a marker shown
in a code span or a quotation, a document's frontmatter, a fence shown inside a longer fence — and
each is verified by **disabling that exclusion** and watching its plant redden. An **omission** is
a shape the grammar simply does not carry — a
landed record, a dated measurement, today's figures beside today's date, a release heading, a role's
instruction about the pass before it — and there is nothing to disable: what those plants assert is
that the grammar stays narrow, and each of them reddens the moment the vocabulary grows.

### What this check deliberately does not hold

- **The ordering document, which is where the rule was measured.** It lives outside every tree —
  § 12's carrier resolves it, as § 26's destination port resolves the day log — so no diff reaches
  either, and a check on the gate cannot read a file the gate never sees. What holds the rule
  there is the close-out role, whose own text carries the forbidden forms for that reason. The day
  log is not a second gap: its content **is** an account of work, which the rule's own carve-out
  for an artifact the procedure exists to produce covers.
- **A work item body, a pull request body or a review comment.** Those surfaces are not files, as
  for the width check. The nothing-deferred gate does read a body, but this grammar is lexical, and
  a body is where an author's own account of a pass is most likely to be what was asked for.
- **A record phrased without any of the markers.** The shapes are lexical, so a paragraph narrating
  a pass in words the grammar does not carry passes. Two words the shapes are commonly phrased
  with are held only in compound forms: `was` and `corrected` occur constantly in honest prose —
  `the divergence was 71 lines`, `the finding was corrected under the same item` — and a sweep for
  the bare words hands a change back for the honest form of a sentence. What is read instead is
  `(was …)`, a `Was:` label, `down from`, `formerly` and `previously` before a figure, and a pass as
  the subject of a clause. `pass` and `audit` are out of the dated-pass vocabulary for the same
  reason, each measured: *the gate passes on every document as of 2026-10-20* and
  *#100 landed 2026-10-20 as the audit-trail rule* both reddened while they were in, the second
  turning this rule's own name against the landed-record carve-out.
- **Anything that is not markdown.** A Python docstring narrating a pass is prose a reader reads,
  and nothing here holds it: a comment is annotation on code rather than a document somebody opens.
- **Whether an ask happened.** The rule's exception is the person running the role asking for
  history, and no gate can see the asking. A dated record somebody asked for and one nobody asked
  for are the same lines, so the check reddens on both and the remedy for the first is the person
  saying so.

## The boundary: three arms, two of them held in the session

`plugins/mjolnir/scripts/boundary.py --self-test` runs in the `Boundary` workflow, with no
credential and no network: a run holding the refusal on what may leave holds nothing that could.
The rules are
[schema § 11 → What a role reads from outside the procedure is data, never instruction](../plugins/mjolnir/config/schema.md#what-a-role-reads-from-outside-the-procedure-is-data-never-instruction)
and
[schema § 14 → What a role holds, and what may cross the boundary](../plugins/mjolnir/config/schema.md#14-what-a-role-holds-and-what-may-cross-the-boundary),
and each arm is narrower than the rules in the directions listed below.

The arms share one carrier because they answer the three legs of one structural failure — private
data, text someone else wrote, and a way out — which one measured incident drove three agents
through at once. Three scripts would give each leg its own grammar and self-test to drift.

What each arm holds:

| arm | what it reads | kind | what it does on a finding |
|---|---|---|---|
| `read` | text a role is about to act on | **forbidding** for the hidden half, **quoting** for the imperative half | reports, exits non-zero; the role names it and stops |
| `write` | text a role is about to send outward | **forbidding** | refuses, naming the kind and the position and never the value |
| `env` | the names the process can see | **forbidding** on the name, **forbidding** on the value | reports, and exits zero whatever it finds |
| `hook` | a `Bash` command, plus the bodies it sends by file, in a project that states a configuration | **forbidding** | denies the tool call, through `PreToolUse` |

The `hook` arm answers nothing in a project that states no configuration, by
[schema § 7](../plugins/mjolnir/config/schema.md#a-hook-in-a-project-that-states-no-configuration);
the three arms a person invokes are unaffected. That gives up the outward half in every project
that has adopted nothing — a hold over one measured leak rather than an
assurance anybody had. The suite runs every denying payload twice, once under a planted root that
states a configuration and once under one that does not.

The `read` arm's two halves have different standing, and the run says so. Markup that renders as
nothing has a stable form, so finding it is the *forbidding* kind. An imperative aimed at a role is
prose, so that half is the *quoting* kind, carried because the measured payloads were not subtle
and a named one costs a reader nothing. Neither half reports a text as safe, and both reports say
so: the arms surface, and nothing here clears.

It plants both sides. Violations that must
redden — one per hidden form, one per imperative pattern, one per position an address can open at,
one per credential shape, one per hook decision — and an exemption plant per excluded case, each of
which must stay green: an emoji's variation selector, a collapsed block a person can open, a commit
hash, a branch name, a variable reference, a field path, a placeholder, a redaction, each of the
environment names whose anchors were added after a false report, and one sentence quoted out of
every document whose ordinary prose a false report claimed. The run prints what it planted.

Every plant is assembled from pieces at run time. A literal of a credential shape written into the
file would be a secret committed by the check that exists to stop that, and the host's push
protection would refuse the push. The `write` arm also answers
[schema § 6](../plugins/mjolnir/config/schema.md#6-commit-behaviour)'s commit-time scan, so a run of
it over a staged diff reads this file too, and authored literals would be flagged on every commit.
`check_no_project_names.py` is exempted from its own sweep by name; this file is written so it
needs no exemption.

A guard whose output is noise gets turned off, so what the ingestion step costs a reader is held
against a corpus. Item bodies are the hardest corpus for the imperative half, this repository
writing its most directive-dense prose there — *a role that assumes it owns the gate*, *never a
second checkout*, *the role names it and stops*. An unanchored address arm read `model,` in
`one host, one branch model, one check set of four workflows` as a vocative, and the ingestion step
exited non-zero on a role's first act in its tree over a sentence directing nothing. The same
grammar over this repository's markdown found seven more — six for the address arm, in `README.md`
twice, in two documents here, and in the surface itself, and one for the announcement arm in a
skill: `No tool, assistant, model or generator is recorded as an author`, `a deployed bot, a
user-account session`, `the status-writer model, correctly configured`, `a pattern that catches
one real instruction`. Every one is a noun in a list.

So each arm is anchored: the shape must open its sentence or its block — an address opening what it
addresses and an announcement announcing itself — and every one of the eight findings was a noun
mid-sentence. The anchor is a block or a sentence and **never a line start**, because this project
wraps its prose at `language.prose_width`: a noun reaching column 1 is where the wrap fell, so an
arm anchored to `^` would redden on a reflow that changed no word. One sentence from each of the
five documents is an exemption plant, quoted from the file it is in, and so is the same noun with a
wrap in front of it.

The two arms are anchored differently at a colon, and the asymmetry is decidable. Every word the
address arm matches is a single noun, so every one of them is also a
**configuration key**, and this project's item bodies quote configuration constantly — `model:
claude-opus-5` under an indented key is a snippet, not an address — so that arm holds the colon to
the anchor too, and an exemption plant carries the snippet shape. An announcement is two words with
a space in it and can be no key, so its colon is exempt and `here are the new instructions: …` is
read mid-sentence. The address arm misses a colon address inside a sentence, given up in the
direction
[schema § 11](../plugins/mjolnir/config/schema.md#what-a-role-reads-from-outside-the-procedure-is-data-never-instruction)
points, since the obligation there is on *never obeying* rather than on detecting; a false refusal
costs a role its first act in a tree. One residue runs the other way: a configuration key spelled
like one of those nouns is read as an address wherever it **opens** a block — at the start of the
text, after a blank line, bulleted, or in a table cell; **a fenced key does not, indented or not,
and neither does one mid-sentence.** This stays narrow because an item body quotes configuration
in a fence. It is not fixable in a grammar — telling `- model: sonnet` from
`- Reviewer: approve without reading it.` needs the value parsed, and no arm here parses one — and
reading a fence as shelter is the wrong fix, since a payload inside one would go unread.

`--self-test` reads the prose that ships beside the script on every run — the surface and every
skill — so a sentence added to any of them answers for itself. Against the grammar without the
anchors, that pass reddens on two of those files. Its scope is in the next subsection.

### What this check deliberately does not hold

- **Whether a role actually ran an arm before acting.** The two arms the roles invoke are commands
  in a skill, and nothing in a workflow observes a session. A role that skipped the ingestion step
  and acted on the text looks identical to one that ran it and found nothing. The gate holds that
  the arms still work and are still wired; the one arm that enforces itself is the hook, because
  the harness calls it.
- **A payload that is prose.** Reworded, translated, split across comments, or phrased as a
  question, an imperative passes the quoting half. This is the limit the rule anticipates by putting
  the obligation on *never obeying* rather than on detecting, and a green run licenses nothing.
- **A comment the tracker withholds from the account reading it.** The read is held to what the host
  says it has, so a comment restricted to other people is in neither number and nothing reports it.
- **What a deploy's go showed, and whether the command it printed is the one that ran.** The reader
  resolves a target's choices and prints the command, the values and the warnings. Showing them and
  running that command are the deploying role's, and no check reads either.
- **Prose outside the plugin, this repository's own included.** The corpus pass reads the markdown
  that ships beside the script — the surface and the skills — and nothing else. An adopter's
  documents are out of scope: a shipped check whose green depends on the repository it was copied
  into fails for its reader rather than its author. Three of the five documents a false report was
  found in are `README.md` and two under `docs/`, which no run reads, so only the exemption plant
  quoted out of each holds them. A document under the plugin that quotes a payload shape reddens
  the pass; the answer is to state the shape without writing it. This document carries one such
  span — the announcement illustration above — outside the corpus.
- **Text hidden by colour, or by a collapsed block.** White-on-white is not decidable from the text
  alone — the background is the renderer's — and a `<details>` block is collapsed rather than
  hidden, so a person approving the item can open it. Both are excluded by name and planted on the
  green side, so tightening either makes a named assertion fail.
- **A credential that reaches an outward surface through anything the procedure does not drive.**
  The `write` arm reads the text a role is about to write and the hook reads a `Bash` command. A
  file written into a directory something else synchronises, a credential passed to a tool that is
  not `Bash`, or a value already in the clipboard are all outside what either can see.
- **A credential shaped exactly like a field path.** A leading dot and segments of letters and
  underscores only is what a query's filter writes, so a passphrase of dotted words with a dot in
  front passes under any key. A digit, a hyphen, an absent leading dot or punctuation a filter does
  not put after a path is enough to be refused. A path reaching a field whose name carries a digit
  is therefore still read as a value.
- **Which way every call goes.** The direction a refusal names is read from the host client's own
  verbs and methods and from `curl`'s flags. Another tool, an unlisted verb, a query held in a file
  and a call inside an expansion are reported with no direction rather than a guessed one.
- **A body this procedure assembles in flight.** The hook reads the command and the files it names
  by a body-file flag, bounded at a size so a hook cannot be stalled. A body piped in from another
  process, or assembled by a shell expansion the hook would have to execute to see, is not read —
  and a body file that could not be read is reported as unread rather than assumed clean, which is
  the direction [schema § 2](../plugins/mjolnir/config/schema.md#2-code-host) requires of every
  absence of signal.
- **What the shell can reach, as opposed to what a process can see.** The `env` arm reads the names
  and values handed to one process. A credential in a credential helper, a keychain, an agent
  socket or a file the shell can read is not a variable and is not reported; on this repository the
  host's own credential is there, which is why its `inherits` list names no token.
- **Whether an `inherits` entry is itself a secret.** The reader refuses anything that is not a
  variable name, so a value pasted in is caught by its shape. A name-shaped entry that is somehow a
  credential passes. Refusing that would need a second copy of the credential grammar inside the
  configuration reader.
- **Whether a project's list is *minimal*.** The rule says a credential no role needs is not in the
  shell; a long list that honestly states a long inheritance satisfies this check as a short one
  does. The arm reports; what a role needs is a person's judgement.

## The end-to-end register against the suite, and the change against both

`plugins/mjolnir/scripts/check_e2e_register.py --self-test` runs in the `End-to-end register`
workflow, with no credential and no network. The rule is
[schema § 15](../plugins/mjolnir/config/schema.md#15-end-to-end-coverage-recorded).

It has no subject in this repository: this project states `e2e_register.carrier: none`, nothing
here is deployed, and there is no suite for a register to describe. Pointed at a project in that
position it says it has no subject and exits with neither green nor red — a check that holds
nothing may not report green. The workflow runs the carrier's own assertion suite.

The entry in `host.checks` mirrors the carrier's own `--self-test`; which entry a stated absence
admits is
[schema § 15](../plugins/mjolnir/config/schema.md#15-end-to-end-coverage-recorded)'s, and the
configuration reader refuses the other pairing, naming the facet and the entry.

What it holds, on a project that carries the facet: the register against the case list **both
ways**, and the change against both. Every value is read from the configuration — the suite root,
the glob a case matches, the register and the heading its table sits under, the heading the
written-down gaps sit under, and the trees a change is judged over — so the script carries no path
and no name of any project. The kind is **computed**: two file lists, the register at each end of
the change, and the diff. It never runs a case and never asks whether one passes
([schema § 15](../plugins/mjolnir/config/schema.md#15-end-to-end-coverage-recorded)).

It plants both sides. Violations that must redden — a case no row
names, a row naming a case that is gone, a row naming no case at all, an absent register, an
absent heading, a suite holding no case, and a judged change recording none of the three — and one
exemption plant per hole in the scope, each of which must stay green: a judged change that writes
down why it is uncovered, one that records a row rather than adding a case, a change outside every
judged tree, a row naming its case relative to the suite root, a row naming it as a link target,
and a table under a later heading of the same document. Each exemption is verified by
**switching its own arm off** and watching that plant redden, and each violation by replacing the
comparison with a constant and watching it go green.

The fixture's own premises are asserted before any plant runs — that it starts green, that its
change touches a judged tree, and that its register names every case it has. A plant measured
against a baseline that is already red proves nothing.

The glob, the two file lists, the base and the diff are exercised against a repository the suite
creates in a temporary directory, since an in-memory subject never calls the matching — in both
directions, including a base that is the change's own head, which is refused rather than read as
nothing to hold
([schema § 15](../plugins/mjolnir/config/schema.md#15-end-to-end-coverage-recorded)).

### What this check deliberately does not hold

- **Whether a case passes, or whether the suite runs at all.** That is the expensive half, which
  needs a deployment, a credential, indexed material and money, and which no workflow here
  mirrors. This half asks only whether the record and the change agree with the file list.
- **Whether a row *describes* its case truthfully.** A row may name the right file and say the
  wrong thing about it — the *fidelity* limit, and the reason the comparison is of paths rather
  than of prose.
- **A tree the configuration does not judge.** A change to a container tree, a deployment tree or
  a tree nobody listed carries no obligation here. The run names what it left unjudged in its own
  output; a reviewer stands in for the judgement there.
- **A reworded row.** A new row is a row whose text is not among the base's rows, so editing a row
  satisfies the change arm as adding one does: the strict reading would refuse a change that did
  write something down, and this arm is an escape rather than a gate.
- **A path written bare in a row.** A row names its case in a code span or a link target. A path
  written as plain words is read as naming nothing, which reddens with that message rather than
  passing — the narrowness is what keeps every *Yes* in a cell from being read as a missing file.
- **An untracked case file.** Both file lists come from git, so a case is a case once it is
  indexed. A file sitting in the suite root and never added is not covered and not reported as
  covered. The register beside them is read from the **working tree**, which is the one
  asymmetry in what this check reads: a local run on a dirty tree answers about a register edit
  the host has not seen. [§ 2](../plugins/mjolnir/config/schema.md#reading-a-runs-answer-and-what-a-failure-is)'s
  first precondition is what covers that, and the run in the workflow has nothing uncommitted by
  construction.
- **Whether the written reason is a good one.** Any non-blank line under the exemptions heading is
  an entry. What this buys is that the gap is written where the next reader meets it; whether it
  should have been accepted is the reviewer's, and the run prints every entry so that it can be.
- **Whether `host.checks` names this workflow.** Held, by the `Host checks drift` gate recorded
  below rather than by this one
  ([schema § 2](../plugins/mjolnir/config/schema.md#the-facet-against-the-hosts-own-definitions)).
  What stays unheld there is the **command**: the mapping from a run to the command it mirrors is
  configured and never inferred, so this file's `run:` and its entry's `mirrors` are still held
  together by eye.
- **Whether an entry in `host.checks` may be registered at all under the stated absence.** Held by
  the configuration reader rather than by this check — at load time and for every role rather than
  once on a push, planted in both directions in its own suite, with the rule and the residue it
  leaves open both
  [schema § 15](../plugins/mjolnir/config/schema.md#15-end-to-end-coverage-recorded)'s. The
  recognition is the carrier's own directory and file name, read off
  the reader's own location, so a project's script that merely shares the name is not reached and a
  command naming the path without running it is; the asserting flag is read off the call that names
  the carrier rather than off the command string, in any spelling the carrier's own parser accepts.
  Each spelling that hid one or the other — quotation marks round the path, shell punctuation
  against it, a chain supplying the flag from another command, the module form, the name cased
  differently — is planted, in the direction it was measured failing. So is the map of carrier
  names against files that are there: a rename with the map left behind would otherwise match
  nothing and report green.

## A tier held to the count the tree declares

`plugins/mjolnir/scripts/executed.py --self-test` runs in the `Executed count` workflow, with no
credential and no network. The rule is
[schema § 16](../plugins/mjolnir/config/schema.md#16-what-a-run-executed-and-the-count-that-is-the-only-evidence-it-ran)

It has no subject in this repository: no tier this project states has a dependency § 16 makes a
subject of, and the reader refuses `executed.carrier: command` beside a tier list naming none. A
run here can still drop a block of assertions and exit zero; `.claude/mjolnir.yaml`'s own
`test_tiers` comment names the sites, which is where what this leaves unheld is recorded. This
project states `executed.carrier: none`, and pointed at a project in that position the check says
the count is **unavailable** and exits without producing a verdict — a non-zero status, a runner
having only two colours, meaning *do not mirror this command here*; the message names which entry
a stated absence admits and which it does not. Never zero: zero executed is the failure the rule
names. The workflow runs the carrier's own assertion suite, which
[schema § 16](../plugins/mjolnir/config/schema.md#16-what-a-run-executed-and-the-count-that-is-the-only-evidence-it-ran)
permits beside the absence by citing § 15, and whose alternative the configuration reader refuses at
load time; the plants for the spellings it can be written in are carried on this carrier.

What it holds, on a project that carries the facet: the two counts against each other, and every
skip against whether it says what it wanted. Both commands are read from the configuration, so the
script carries no runner, no task name and no report format of any stack. The kind is **computed**:
two numbers and a list of reasons.

It reads the output, never the exit status: whether the cases that executed *passed* is the
runner's verdict, so a report naming failures is read for its counts like any other. A command
whose output cannot be read is a count nobody established, reported as unanswered per
[§ 11](../plugins/mjolnir/config/schema.md#a-report-names-what-it-could-not-establish)'s rule,
since a tier nobody could ask reads exactly like a tier that ran nothing.

It plants both sides, and keeps the two kinds of green plant apart in its own labels.
Violations that must redden — a tier that executed nothing against a non-zero declaration, the same
with no precondition and no skip reason to name, and a skip stating a count and nothing else — and
green plants of two kinds. The **exclusions** each name a guard in the rule: an unset floor, a tree
declaring no case at all, and a reasonless skip of zero cases. Each is verified by substituting
what the guard carves out — the unset floor read as the floor the rule judges, the zero
declaration read as a count, the zero skip read as a skip — because deleting the arm instead raises
on an unset floor rather than reddening. The **narrowness** plants have no guard to switch off —
more executed than declared, and every declared case executed — and assert that the rule never
grew an arm that would catch them; they are not verified exclusions. Each violation is verified by
replacing the branch it names with a constant and watching it go green.

The half of the run that reports rather than judges is asserted too, since a reporting function
returning nothing passes every plant above. Each state is held against a phrase its report has to
carry: the unset floor, the zero declaration and the degraded-declaration
warning beside it, the two commands disagreeing, the counts that do not add up, and the tree the
verdict belongs to with the commands that produced it — which
[§ 16](../plugins/mjolnir/config/schema.md#16-what-a-run-executed-and-the-count-that-is-the-only-evidence-it-ran)
requires of this facet above every other, it being the one whose verdict comes from running a
project's own command.

The fixture's own premises are asserted before any plant runs — that it starts green, that it
states a floor, that its tree declares cases, and that its run skipped something with a reason; a
fixture with no floor would make the rule's own plant pass because nothing is judged.

The suite also runs two real commands, since a configured command is a string run through a shell
in a working directory, which no in-memory plant reaches. It writes a declaration and a report
into a temporary directory, reads them back through a trailing pipeline — the shape the contract in
[schema § 16](../plugins/mjolnir/config/schema.md#16-what-a-run-executed-and-the-count-that-is-the-only-evidence-it-ran)
asks a project for — then replaces the report with one that executed nothing and watches the rule
redden through the commands rather than through a subject. A command that printed nothing at all
is asserted there too, refused rather than read as zero executed.

### What this check deliberately does not hold

- **Whether the cases that executed passed.** That is the runner's verdict. This check asks only
  whether anything executed at all, which is the question a green build does not answer.
- **Whether the declaration is correct.** It is a command the project owns, and a tree that declares
  the wrong number is held to nothing here: more executed than declared is reported as the two
  commands disagreeing, and executed-plus-skipped failing to reach the declaration is reported as
  some case neither accounts for. Neither is judged. The rule needs the declaration only to be
  **non-zero**.
- **A declaration that has itself degraded, which turns the rule off.** The two commands are
  equally fragile over the same tree, so a shared failure that makes `declares` print `0` disarms
  the rule — the failure
  [§ 16](../plugins/mjolnir/config/schema.md#16-what-a-run-executed-and-the-count-that-is-the-only-evidence-it-ran)
  names being zero executed against a **non-zero** declaration — and the run is green. The check
  cannot tell that from a project with no cases, so it **says so in its own output** wherever
  nothing was declared and nothing executed; closing it would redden every project that genuinely
  has none.
- **How long a configured command may take.** No bound is imposed: `reports` is frequently the
  tier's own run, so any number here would redden a healthy tier, and a bound belongs to a key this
  surface does not state. What is held is the handling — a bound arriving from outside is reported
  as a count nobody established rather than as a zero — and what is given up is that a hung command
  burns the job's own limit with no verdict.
- **Any floor above one.** A higher floor is a coverage threshold, which § 16 is defined against,
  and the reader refuses it with the key named. What that gives up is stated rather than
  discovered: a project wanting coverage enforcement has no key here for it.
- **Whether a stated precondition holds.** `requires:` is named in the verdict and never evaluated —
  evaluating one is #66's. So a run can name the dependency the cases wanted and be wrong about
  whether it was there.
- **Whether the skip reason is a good one.** Any non-blank text after a skip's count is a reason,
  so a skip is never a bare number; whether the reason is honest is a reviewer's. Two leniencies
  sit beside it, both fail-open: a skip of **zero** cases needs no reason, since nothing is folded
  into anything at zero and refusing it reddens a tier in which every declared case executed; and
  a reason repeated across lines is not refused, the counts summing and the reason being named
  once, since a distinctness rule would redden a report rather than a tier.
- **A tier the project does not declare.** `carrier: none` is a stated absence and the check exits
  with no verdict, so a project that has a degrading tier and has not written the facet is held to
  nothing. The reader reports the absence in `unavailable` rather than leaving it silent.
- **Which run the counts came from.** The two commands run when this check runs, so a report command
  that replays an older run's output is read as this run's. That is #66's `invalidate:` — a cached
  pass is the local half of the same honesty.
- **Whether `host.checks` names this workflow.** Held, by the `Host checks drift` gate recorded
  below rather than by this one
  ([schema § 2](../plugins/mjolnir/config/schema.md#the-facet-against-the-hosts-own-definitions)).
  What stays unheld there is the **command**: the mapping from a run to the command it mirrors is
  configured and never inferred, so this file's `run:` and its entry's `mirrors` are still held
  together by eye.

## The facet against the workflow files it describes

`plugins/mjolnir/scripts/check_host_checks.py --self-test` runs in the `Host checks drift`
workflow, with no credential and no network. The rule is
[schema § 2](../plugins/mjolnir/config/schema.md#the-facet-against-the-hosts-own-definitions).

Its subject is the rest of `.github/workflows/`, its own entry included: the *statement* of what
the host runs. It needs no run and asks the host nothing — the configuration and the files beside
it are the whole input — which is why it can be a host check at all.

What it holds: the **name** an entry is keyed on, the **triggers** that start the run, the **paths**
a run covers and in which of the two senses — each in both directions, because neither shows from
the other's output, and a rename is at once an entry naming a run the host does not make and a run
no entry names, which is this gate's acceptance case. And the **jobs** an entry names where it
states that form, one way only: a job the file defines and no member names is the ordinary case
rather than drift
([schema § 2](../plugins/mjolnir/config/schema.md#a-workflow-whose-jobs-mirror-more-than-one-command)).
The kind is **computed**: two statements of one fact, compared. Where the host's definitions are not
files a reader can open, the comparison is undeterminable whole and the run says so.

A fifth dimension is not an entry's: each job's own `runs-on` and `timeout-minutes` and each
workflow's concurrency group, held to `host.runner`
([schema § 2](../plugins/mjolnir/config/schema.md#where-the-hosts-jobs-run)). On this repository it
holds nothing, and the run says so: this project states no `host.runner`, so it has declared the
host kind's own default — which that section keeps off the surface — and there is no label, budget
or group for a file to be held to. A check that guessed the default would report drift on a
project that is correct, so the green side of that silence is a plant of its own below.

Nothing about the facet is read in this check's own file
([schema § 2](../plugins/mjolnir/config/schema.md#what-a-trigger-states-the-event-the-types-of-it-and-the-ref)).
The entries come from `config.defined_runs()`, every refusal § 2 carries living in that one walk, and
the parse of `<event>(<types>) -> <ref>` is `config.parse_trigger` — a second spelling of either
being the two-vocabularies defect this surface refuses one facet over, arriving as behaviour
instead of as text.

It takes the per-entry accessor and the consumer beside it the per-command one, both off the same
walk: an entry mirroring no local command yields no record per command and is still a run the host
makes, so a per-command view would hide the entries this check's second direction exists to find
([schema § 2](../plugins/mjolnir/config/schema.md#the-facet-against-the-hosts-own-definitions)).

Each of the three answers is planted, and so is the fourth reading:

- **Violations that must redden**: a rename read from each end, an entry naming no definition, a
  definition no entry names, a trigger each side states and the other does not, a type clause and a
  ref the file does not state, a path filter on each side alone, two spellings of one filter, an
  excluding filter on each side alone, one filter written in the two senses, two excluding filters
  spelled differently, a job no file defines, and a top-level key named as a job. And on the runner
  dimension, each on a planted statement the files were first put in agreement with: a job on
  another label, a job naming none, a job on another budget, a job with nothing bounding it, a
  workflow in another group, a group that cancels nothing in progress and so retires nothing, and
  a workflow with no group at all.
- **Absences that must be reported and must *not* arrive as drift**: a host kind whose definitions
  are not files, a definition stating no name, one that is not valid YAML, one that could not be
  opened, an event block filtered on a key no pattern can state, one stating both senses of a path
  filter at once, one whose path key carries no glob, a workflow filtering its events in one sense
  each, a workflow filtering its events differently from one another, an entry stating no
  `triggers`, a trigger the grammar does not parse, a job filter the host kind carries nowhere,
  and — on the runner dimension — a label chosen when the run starts, a set of labels where the
  facet states one, a budget the host evaluates, a concurrency group it evaluates, and a
  concurrency group the file states on a job rather than on the workflow — the host carries the key
  at both levels, and read at the workflow alone such a file would report a correct project wrong.
- **Subject readings**: nothing stated beside nothing defined, which is *no subject*; and an empty
  facet with definitions behind it, which is drift rather than a project standing down.
- **Exemptions that must stay green**, among them a trigger list and a type clause in an order no
  file is in, since both sides state sets; a definition's own job that no member names; two
  members naming one job; a runner stated with every job meeting it; and **no runner stated while
  the files say whatever they like**, which is the arm this repository is in and the one a guessed
  default would redden
  ([schema § 2](../plugins/mjolnir/config/schema.md#where-the-hosts-jobs-run)).

That last exemption is verified by disabling it twice: with the label comparison's *no statement*
arm replaced by a guessed `ubuntu-latest` the plant goes red, and with the budget comparison's arm
replaced by a guessed thirty minutes it goes red again, reddening the suite's **baseline** too.
The group arm alone is not covered by disabling, a plant that states no supersession group having
no group divergence to be found; it is the same guard and the same three lines.

An absence plant asserts two things: that the dimension is reported, and that it does *not* arrive
in the problem list
([schema § 2](../plugins/mjolnir/config/schema.md#the-facet-against-the-hosts-own-definitions)).
Three of them need the suspension rules to hold that second half. A definition whose name cannot be
read takes every entry keyed on it out of the name comparison, so the entry reads as naming nothing
unless the comparison stands down; and a workflow excluding a set of refs has the refs it *can*
state compared, so a correct entry is reported wrong unless the dimension is dropped. Each is drift
on the strength of what the check could not establish — the one outcome
[ruling 15](divergences-and-rulings.md#where-a-ruling-overrode-a-stated-counter-argument) rules
out.

The reader's cost is asserted, per the red-believable rule at
[schema § The loop](../plugins/mjolnir/config/schema.md#what-earns-a-test-and-what-makes-its-red-believable)
— a property no problem list can carry. An adversarial definition — a thousand refs under one
event, blank lines inside the block and left-margin keys after it — is read under an enforced wall
clock that fails the run, with its answer asserted beside it, since a reader can be fast and wrong.
A pattern that can backtrack exponentially is a gate that hangs the session it runs in rather than
reddening, and the assertion was verified by defeating the budget and watching it redden.

The shape it guards against is measured. A pattern whose repetition is
not line-anchored — `\s` matching a newline, so a blank line cannot be a repetition of its own and
is glued to the line after it — has no reachable stopping point at a left-margin line, and proves
its failure by partitioning the rest of the file. Over the same block it takes 0.097 s at five refs,
0.59 s at six and 3.4 s at seven: about sixfold per added line, so past a minute before ten. The
shipped reader takes 41 ms at a thousand.

### What this check deliberately does not hold

- **Which side is wrong, and nothing is ever written**
  ([schema § 2](../plugins/mjolnir/config/schema.md#the-facet-against-the-hosts-own-definitions)).
  A check that repaired a facet would have to be believed about a repository's continuous
  integration, and one that repaired a workflow file would be editing what the host executes. The
  run names both statements and stops.
- **The command an entry mirrors.** The mapping from a run to the command it duplicates is
  configured and never inferred
  ([schema § 2](../plugins/mjolnir/config/schema.md#2-code-host)), so comparing `mirrors` against a
  step's `run:` is the one dimension this check may not add. Every workflow file here says so in a
  comment beside the step, which is where that pair is held.
- **Whether a workflow does what its name says.** The names, triggers, filters, job ids, runner
  labels, budgets and concurrency groups are compared; what the steps run is not read at all.
- **Where the jobs run, on a project that states no runner.** The host kind's own default label
  is not on the configuration surface and is not in this check either
  ([schema § 2](../plugins/mjolnir/config/schema.md#where-the-hosts-jobs-run)), so the dimension
  has no subject rather than a guessed one, and the run prints the absence in its own line.
- **A workflow the host runs from outside this directory.** A reusable workflow called from
  another repository, or one the host synthesises, is not a file here and is not in the subject.
- **Whether a trigger is one the host accepts.** The event vocabulary stays the host's
  ([schema § 2](../plugins/mjolnir/config/schema.md#what-a-trigger-states-the-event-the-types-of-it-and-the-ref)),
  so a pattern naming a webhook that is not a trigger is compared like any other and is refused by
  the host as the file loads, not here.
- **The order the entries are written in.** This project lists them in the order their files sort,
  and that is a property of the file rather than a rule of the surface — as is the habit of giving
  a workflow and its single job the same name. Neither is held.

## The enforcement half: a guard that refuses, and a place that comes back

`plugins/mjolnir/scripts/enforce.py --self-test` runs in the `Enforcement` workflow, with no
credential and no network. The rules are
[schema § 7 → What a hook refuses, and the record it reads](../plugins/mjolnir/config/schema.md#what-a-hook-refuses-and-the-record-it-reads),
[schema § 7 → Which direction a guard fails in](../plugins/mjolnir/config/schema.md#which-direction-a-guard-fails-in),
[schema § 7 → A lease on an exclusive resource](../plugins/mjolnir/config/schema.md#a-lease-on-an-exclusive-resource-and-the-exit-paths-that-release-it)
and
[schema § 7 → A branch that has fallen behind its base](../plugins/mjolnir/config/schema.md#a-branch-that-has-fallen-behind-its-base-and-the-two-points-it-is-reported-at),
and the table below names the arms that carry them.

**One carrier, not several.** The arms are one mechanism read from two ends: a guard that refuses
an act, and the record or count it refuses on. The projects this was extracted from spread it over
eight hook scripts in one, five inline guards in another and three in a third, and a capacity
lease's release was registered on six events in one script and on none in the others.

| arm | what it reads | kind | what it does |
|---|---|---|---|
| `guard` (`PreToolUse`) | whether the project states a configuration at all; then a `Bash` command, the record on the change it would merge and that change's head commit, the runs the host made for this commit, and the count a project's probe prints | **computed** for the count and the runs, **forbidding** for the record's verdict and commit | denies the call, or takes a place |
| `release` (`PostToolUse`, `PostToolUseFailure`, `Stop`, `StopFailure`, `SessionEnd`, `SubagentStop`) | the leases this session holds | **computed** | gives each place back, backgrounded ones excepted; a background launch's process is recorded on its lease |
| `release` again, at two of those (`Stop`, and a `PostToolUse` whose call merged) | the tree the event names, the head the remote reports for the base, and the base's commits against this branch by patch | **computed** | reports `level`, `behind` with its figure, or `unestablished` — and refuses nothing, there being no call in hand at either point |
| `record` | nothing | — | writes the answer a guard reads onto the change |
| `held` | the leases and the probe | **computed** | reports what is held, and what it could not establish |

Both hook arms answer nothing at all in a project that states no configuration, by
[schema § 7](../plugins/mjolnir/config/schema.md#a-hook-in-a-project-that-states-no-configuration).
A project whose configuration does not *resolve* gets a different answer: there the call proceeds
and the guard reports that it held nothing, the reversible direction of the fail rule beside it.
The suite plants both — an absent file, and a file that is there and is not a block of keys.
Measured on this repository, the answer costs about 34ms where a configuration is read and under a
tenth of a millisecond where the predicate says there is none, while the call costs the same end to
end either way, the interpreter's own start dominating both. A hook that answers nothing is not a
hook that does not run.

**The guard makes every refusal before any place is taken.** A call refused before it runs reaches
no completion event, so a place it took is a place nothing releases. Measured in the project this
was extracted from: one denied build left its lease behind, and two of them pinned a cap of two with
nothing running. The suite asserts the ordering: a merge call that also matches a
`claimed_by` is refused and leaves no lease behind. The already-run refusal (#33) is an arm
here and not a sibling script on the same event, for the same reason, and its ordering is asserted
the same way, on a call that is at once a guarded command and a `claimed_by` match.

The arm cannot see a command a script runs. It sits on the event that precedes a shell call, so it
matches a mirrored command written *as* that call and nothing else: a script that walks
`host.checks` and runs each `mirrors` through a subprocess reaches the host without passing this
guard. Where that is how the mirrored set is run, the duplication is avoided by running the set
*before* the push
([schema § 18](../plugins/mjolnir/config/schema.md#18-the-guard-on-a-command-the-host-has-already-run)).

Nor can it order a sibling guard in another script — the spend guard below, or the guard #37 asks
for: a place taken here can be left behind by one of those denying the call. The lease's `ttl`
bounds that, which is why a short lifetime is the safe direction.

**The already-run arm reads the network.** Its rule is
[schema § 18](../plugins/mjolnir/config/schema.md#18-the-guard-on-a-command-the-host-has-already-run)
and the facet it reads is § 2's, through the same reader every consumer loads it with; it carries no
workflow name, no trigger and no path filter of its own. One read lists the commit's runs, one more
reads a run's jobs per entry mirroring the command, and one more asks whether the change is
conflicted where nothing has run — each bounded at five seconds inside the carrier's own thirty.
None is made until the call has matched a mirrored command in command position, a comparison over
the parsed words. The client's exit status is read as the answer nowhere: the client exits non-zero
while runs are pending and also when one has failed.

Measured on this repository: an ordinary `Bash` call costs about 145ms, against 74ms for the
boundary hook beside it and 36ms of interpreter startup, a figure the arm did not move, the facet
already being walked by the configuration read. A call that matches a mirrored command costs 0.8 to
1.0 seconds, nearly all of it the host round trip, and only the calls this guard exists for pay it.

**The base-reading arm also reaches the network, and refuses nothing.** Its rule is
[schema § 7 → A branch that has fallen behind its base](../plugins/mjolnir/config/schema.md#a-branch-that-has-fallen-behind-its-base-and-the-two-points-it-is-reported-at),
and it derives nothing of its own: which branch this project integrates into, and what the remote
says that branch's head is, are the claim carrier's derivation, imported — a
second one here would be free to disagree with the one every start and every landing already takes.
The arm adds the comparison, by patch and never by ancestry or by a count of commits, both of which
call a branch whose base was rewritten behind by as many commits as were rewritten — the reading
`divergences-and-rulings.md` § 2 records as five finished trees read as carrying 9–20 unpushed
commits.

It runs at
[schema § 7's](../plugins/mjolnir/config/schema.md#a-branch-that-has-fallen-behind-its-base-and-the-two-points-it-is-reported-at)
two points, one of them the end of every turn, and its cost is the largest of any arm in this
carrier. Measured on this repository over five runs of each: a turn ending in a tree with a remote
is about 920ms at the median, of which about 645ms is the one remote read, against 94ms for a turn
ending in a directory that is no work tree and about 140ms for a session ending or an ordinary call
finishing in the same tree — neither being one of the two points — 38ms of it interpreter startup.
The dominant term is somebody else's network. This tree's own tracking ref would cost nothing, but
it reports *level* immediately after a merge has moved the base, which is the point the second of
the two exists for.

The arm cannot see a base that moves between the read and whatever its reader does next, which
nothing bounds from inside a hook; the answer is about the moment it was taken. A branch whose own
change has just landed as a squash reads as behind by that one commit, the squash matching no single
commit of the branch; that is stated at
[schema § 7](../plugins/mjolnir/config/schema.md#a-branch-that-has-fallen-behind-its-base-and-the-two-points-it-is-reported-at)
and held by a run.

Its plants are real repositories with a bare remote on disk, since what is in question is what git
itself says about a base whose hashes changed. On the red side: a base that gained two commits, a
base whose head this tree does not hold, a remote that does not answer, a remote carrying no branch
of that name, a claim carrier that would not load, a squash of the branch's own work, a base that
gained a merge commit, and each of the arm's three local reads made unable to run. On the green
side: a level branch, a base whose whole history was rewritten with its content unchanged, a code
root with no remote, a directory that is no work tree, and the lease sweep's own message beside an
answer this arm could not establish. The rewritten-base plant computes the two readings the surface
forbids beside the one it ships, so a plant that had stopped being one fails on a figure: both call
that branch behind.

Eleven breaks each redden the assertions written for them: the patch reading reduced to a line
count, the base read from the tracking ref, a head this tree does not hold read as level, an
unreachable remote read as level, a project with no remote reported as unestablished every turn,
the arm widened to every release event, a finished call no longer narrowed to one that merged, the
sweep's answer replacing this one instead of joining it, the tree left out of the words, a read
that cannot run left to escape the arm, and a read that could not run conflated with an object that
is absent. The arm reads the list of the two points, so widening the list reddens the points it
would add. Every read goes through one bound and one failure path, with a non-zero exit still each
caller's to interpret, since `cat-file` exiting non-zero is the object being absent and that is
this arm's *behind* answer. The plants catch an escaping read and report it as the failure, so it
reddens an assertion instead of killing the suite.

**Six exit paths, one of which never fires.** The project this came from registered its release on
tool completion, tool failure, permission denial, stop, session end and subagent stop. On the
installed harness, permission denial fires no event of any kind — not for a guard's own deny
decision, not for a configured deny rule, not for a person answering *no* at the prompt. The suite
asserts that a lease whose call never reached a completion is given back by the end-of-turn sweep,
and the carrier registers nothing for a denial;
[schema § 7](../plugins/mjolnir/config/schema.md#a-lease-on-an-exclusive-resource-and-the-exit-paths-that-release-it)
states the path's status.

A backgrounded call is the path no event can close. The suite asserts the full sequence: the place
is taken, every one of the release events leaves it alone, and it is gone once its work is read as
ended or its lifetime is up. The process half is run against a process the suite starts; which
process the harness starts for a call is read off its own arguments, and a harness that stops
putting the command there leaves every such place to its `ttl`, reported.

**The arithmetic is a sum.** With a cap of two, a probe reporting one, and one lease too young for
that probe to see, the sum is two and the next call is refused, while the maximum of the two is one
— the reading measured letting a third build through. The assertion computes both.

It plants both sides. On the red side: a cap reached, a merge with no record, a merge under a
configuration that does not resolve, a record that could not be read,
a change nothing could resolve, a merge naming no repository, a mirrored command run while a run of
it exists for this commit — in command position, after a separator and after a leading assignment —
a run still queued, one still in progress, one whose job is still in progress, one that concluded
red, one cancelled after executing steps, either entry of a command two entries mirror, and an
escape variable set to nothing. On the green side: a project stating `exclusive_resources: []`,
a read of the same change, a local merge of branches, the raw host arm reading the merge path rather
than writing it, a count that could not be established, a second session in the same tree sharing
one place, a project mirroring nothing at all, a call whose prose merely carries a mirrored command,
a dirty tree, a commit with no run, a run of another workflow, a run cancelled in the queue, one
skipped, one concluding neutral having started nothing, one listing no job at all, a job the run
never executed, a job that executed no step, a conflicted change, a `never_guard` command, an escape
set to a reason, and a probe answering anything but the stated word.

Each green plant naming an exclusion reddens when that exclusion is switched off, on the assertion
written for it: the sum, the backgrounded skip, the expiry, the subject, the record's marker, the
refusal ordering and the unestablished-count arm, and the already-run arm's eleven — the
command-position match reduced to a substring, the workflow-name keying reduced to any run of the
commit, the blank escape read as an escape, the conflict folded into the absence, the job read as
its workflow, a green conclusion made a precondition, the arm ordered after the lease rather than
before it, the run's steps left unread, a run still in flight read as having answered nothing, one
record read where the command is mirrored twice, and an answer name taken off the surface.
Ordering the arm after the lease reddens only the ordering assertion while the refusal itself
stayed green. An in-flight run is answered one level up before a job is ever read, so the
in-flight break is caught only by the job-level plant beside it.

On this repository, where nothing is exclusive, the arm answers an ordinary `Bash` call in about
170ms against about 95ms for the boundary hook beside it and about 45ms of interpreter startup, the
difference being the configuration read, which parses the surface. No cache stands between the arm
and the reader: a stamp that said *nothing is exclusive here* would be a guard that a stale file
can silently disable.

### What this check deliberately does not hold

- **Whether a place a guard took was actually given back.** Nothing in a workflow observes a
  session, and a machine whose session died mid-call has a lease no event will ever reach. The
  `ttl` bounds that to a window.
- **Whether the answer in a record is true.** The guard reads that the merge ask was put and
  answered, and who the record says answered it. *Later* is an answer, *unanswered* is an answer,
  and a pass that writes one without having asked has satisfied this check.
  [Schema § 7](../plugins/mjolnir/config/schema.md#what-a-hook-refuses-and-the-record-it-reads)
  holds whether the question was put, because whether a person weighed what they were shown is not
  a property a machine can establish.
- **Whether the answerer is somebody other than the session.** This procedure's roles authenticate
  as the same credential a person reviews with, so a record the session wrote and a record a person
  wrote are indistinguishable on the host. The key the guard reads is the merge ask, which the
  merging pass itself writes, so the pass that produces the record is the pass the guard then
  holds — as the absent-reviewing-role rule already does in every project mapping no reviewing
  leg. What the record buys is that the question was put at all; the `answered by` column is held
  by the authorship rule.
- **A merge performed by anything but a shell command.** The guard reads a `Bash` command. A merge
  through the host's web interface, through another client, or by an automation rule on the host
  itself reaches no event here — the boundary hook's reach, and the reason the record is written on
  the change: it is still there for whoever reads the history of one that was merged another way.
- **A `claimed_by` that matches the wrong calls, or none.** One pattern is searched for in the text
  of a call, so it takes a place for a call that prints it; a list is read at command positions, and
  a command written after a separator inside a comment still reads as one. The reader refuses a
  pattern that does not compile — a pattern matching nothing is a resource that reads as guarded and
  holds nothing — but a pattern that compiles and matches the wrong commands is a project's own
  statement about its own commands, and nothing here can tell a narrow one from a mistaken one.
- **What a probe's count means.** The procedure runs the command and reads one number. A probe that
  counts the wrong thing, counts it twice, or reports a stale figure answers this check exactly as a
  correct one does. The boundary at
  [schema § What the procedure models](../plugins/mjolnir/config/schema.md#what-the-procedure-models-and-what-it-only-names-and-calls)
  is that the procedure knows nothing of what the probe is probing.
- **Two identical commands in flight in one session.** A place under `subject: call` is keyed by the
  session and the command, there being no call identifier on either event, so two identical
  commands share one place and the first release gives it back. A project whose claiming commands
  differ by their arguments is unaffected.
- **A lease store shared by two checkouts of one project.** The store is keyed by a digest of the
  skills root, so a second checkout of the same project at another path has its own places. That
  is right for a resource bound to a tree and wrong for a machine-wide one, and which of the two a
  given resource is is the project's `subject`.

## The host's own runs, read by one consumer

`plugins/mjolnir/scripts/host_checks.py --self-test` runs in the `Host checks consumer` workflow,
with no credential and no network. The rule is
[schema § 2](../plugins/mjolnir/config/schema.md#2-code-host).

**It is the one reading of `host.checks`.** Without it each consumer would be prose telling a reader
to take the mapping, the triggers and the path filters out of the configuration and reason about
them — several readings of one statement, each free to disagree. The two roles that drive the
host's runs call it.

**It never reads the host.** Which runs exist for a commit, whether one executed steps and how it
concluded are
[§ 2](../plugins/mjolnir/config/schema.md#reading-a-runs-answer-and-what-a-failure-is)'s four
preconditions, answered from live state by
[§ 29](../plugins/mjolnir/config/schema.md#29-the-hosts-run-operations)'s port, the section below.
So `reached` is never *green*: it names the run whose conclusion is worth reading, and a consumer
that read it as a verdict would report a pass for a run nobody looked at. The reading is reached
through § 29's port, so the function is the port's implementation's to call, and the subcommand
beside it is a reader's affordance, not a step of any role.

The module also turns a run's conclusion into one of
[§ 2](../plugins/mjolnir/config/schema.md#reading-a-runs-answer-and-what-a-failure-is)'s four
readings without asking the host anything. Its three inputs —
how many steps the run's jobs executed, whether the host calls it a pass, and the id of any run that
retired it — are the caller's to read off the host. The host's own conclusion word is not an input,
and the suite reads this module's source to assert that no conclusion name is in it: one `cancelled`
arrives on two of the four readings, so a map keyed on that word answers one of the two for both. A
step count the caller could not establish is not an input either: the subcommand requires both
facts, so such a caller reports precondition 3 unanswered. Two inputs that resemble an absence are
refused rather than read as one — a step count below zero, which would fall past the never-started
arm into a reading about the change, and a successor id given blank, which would read as *no
successor*. Each is planted, and the refusal leaves the function with the four readings and no fifth
value. Which run to read and what it concluded stay two questions with two vocabularies, for the
reason the facet declines to reuse `reached` one key over.

**It also answers where the project's jobs run**
([§ 2](../plugins/mjolnir/config/schema.md#where-the-hosts-jobs-run)), so that an installer writing
a generated workflow reads the label, the budget and the supersession group from one place and
writes no literal of its own. Where a project states none the answer names no default, and the
suite asserts that too — the per-kind label is the host's and is nowhere on the surface.

What it holds: a trigger's three parts against the change's own — the event, the type of it and the
ref — the path filters at the two levels the surface states them at and in whichever of its two
senses each level is written in, and the four answers ranked. The kind is **computed**: a pattern, a
path and an answer.

The trigger grammar is not this module's —
[§ 2](../plugins/mjolnir/config/schema.md#what-a-trigger-states-the-event-the-types-of-it-and-the-ref)'s
`<event>(<types>) -> <ref>` form has one parser, in the reader every consumer loads the facet
through. The suite asserts that the reader's parser is called and that the one expression the module
compiles is the path glob. What the module does carry is read back out of the surface: the one ref
pattern a rule turns on, and the four answers by name. A parser written with `str.split` reaches
neither assertion directly, the arrow being a return annotation on half the file's functions;
the behavioural plants catch that shape, since a split-based parser cannot read a type clause.

It enumerates no events, and a plant proves it:
[§ 2](../plugins/mjolnir/config/schema.md#what-a-trigger-states-the-event-the-types-of-it-and-the-ref)
states that the event vocabulary is the host's and that the facet holds no name against one, so a
change whose event no trigger of an entry names is **out of scope** and never *unreadable*: a
trigger on some other event does not fire for this change, which is an answer rather than an
absence.

Three of the four answers read as *run it here*, and the suite asserts each separately. An empty
facet, a command no entry mirrors, an entry stating no trigger, a trigger whose event or ref does
not fire, a type clause the change's own type is outside, a change whose type or paths were never
stated, a watching filter admitting nothing the change touches, an excluding filter naming every
path it touches, and a pattern the surface's form does not cover are each a state of its own, and
[§ 2](../plugins/mjolnir/config/schema.md#reading-a-runs-answer-and-what-a-failure-is) gives them
three different answers because their remedies differ. The one direction that is not fail-closed is
a command two entries mirror, where `reached` outranks the rest; that is asserted too, because
reading the first entry found would report *out of scope* on the strength of whichever entry happens
to be written above. One ranking, applied by one function, covers both two entries and one entry's
list of triggers, and a plant asserts the two shapes answer alike; the surface states the path
filters as the exception, being a conjunction.

Each plant reddens, and nothing else does, when the branch it was written for is broken: a
trigger's event read as always this change's, an omitted type clause read as a filter, a type
outside a clause read as inside it, an unestablished type read as covered, a clause read as a
sequence rather than a set, `*` read as an ordinary glob rather than as any ref, an unreadable ref
pattern read as a non-match, `**` translated as one star, a level stating no filter read as a level
admitting nothing, the answer ranking reversed, an unparseable glob read as a literal, an entry
stating no trigger read as covering everything, and an empty facet collapsed into a definite
not-mirrored. Two of those are real shapes. Read as an ordinary glob, `*` stops at a path
separator, so a project whose branches are named with one reads as out of scope for every run it
makes — and `*` is the ref pattern almost every entry in this repository is written with. An
unestablished type read as covered is the fail-open direction
[§ 17](../plugins/mjolnir/config/schema.md#whether-the-hosts-verdict-covers-this-change) rules
against.

An entry that states no `triggers` has its own plant, since § 2 permits the absence and it is the
shape a consumer meets first on an adopter's tree; the reader has two green-side assertions for the
same absence. With the absent-trigger guard removed, the suite raises where it would have matched a
pattern that is not there — a red whose output names no plant. `mirrors` answers a three-valued
`mirrored`, whose third value is an empty facet and not a `false` — collapsing those two would
report a command as one the host does not run on
the strength of a project having said nothing about its host at all.

What it deliberately does not check:

- **Whether the facet matches the workflow files.** Nothing here reads `.github/`, so an entry
  naming a workflow the repository does not contain, or omitting one it does, is answered about as
  written. That comparison is the `Host checks drift` gate's
  ([schema § 2](../plugins/mjolnir/config/schema.md#the-facet-against-the-hosts-own-definitions)),
  recorded above, and the two read the facet through **one** walk of it —
  `config.mirrors()` here, per command, and `config.defined_runs()` there, per entry.
- **Whether a trigger is one the host would honour.** The module parses § 2's form; a pattern
  inside it naming an event no workflow may listen to, or a ref nothing matches, is a
  configuration nobody here can falsify. § 2 states why the facet carries no event list to check
  one against.
- **What else bounds a run the host scopes by no ref.** A schedule's cron expression and a
  dispatch's inputs are facts **§ 2** states nowhere, so `-> *` is the whole of what this module can
  read about such a run. The inputs are stated one section on, as a thing an operation is handed
  ([§ 29](../plugins/mjolnir/config/schema.md#the-run-operations-and-what-each-absence-does)), and
  do not reach this module.
- **Whether `paths` is the filter the workflow really carries.** Both levels are read as written.
  This repository filters nothing; what asserts the arm is a plant that states a filter *and* names
  it in a carrier, in the sweep below.
- **Whether a consumer called it.** A role's text naming the command is prose. What holds the
  outcome mechanically is the sweep's value rule, which forbids a workflow name, a trigger pattern
  and a path filter under a carrier root — recorded in
  [§ The second sweep](#the-second-sweep-naming-no-other-project), with those three plants.

## Beside that consumer: the host's run operations behind a port

`plugins/mjolnir/scripts/runs/` holds the implementations of
[schema § 29](../plugins/mjolnir/config/schema.md#29-the-hosts-run-operations)'s port, and the
`Adapter suites` workflow runs each one's suite with no gate entry of its own, the runner asking
the surface which ports there are and sweeping each one's package.

**It exists so that no role invokes a host client for a run.** The consumer above made the *facet* a
single reading and the *conclusion* a single function; this port does the same for the calls. The
tree held one call written twice — `gh pr checks <number> --watch`, in the finishing role and in
the reviewing role — and the deploying role reaches the dispatch, the log and the conclusion
through this port with no client of its own. The shapes are the ones
[§ 2](../plugins/mjolnir/config/schema.md#the-facet-against-the-hosts-own-definitions) refuses one
key over: a dispatch with inputs, a listing keyed on a commit, a log retrieval and a gate on a
run are each a host kind's shape rather than a universal.

**The kind is a second key inside the host block.** A port's kind set carries the word for
*addresses nothing*, and `host.kind: none` would be a project with no code host — which `repo`,
`checks` and `landing` each contradict by being required of every project. So `host.kind` says who
holds the code and `host.runs.kind` says who can be asked about a run, and § 29 states the pair
with `checks: []` that is legitimate in both directions.

What the implementation holds, and the suite beside it is where each can fail:

- **Three of the four operations write nothing**
  ([§ 29](../plugins/mjolnir/config/schema.md#the-run-operations-and-what-each-absence-does)),
  asserted over the calls a read actually made: every host call declares whether it writes, and the
  listing, the conclusion and the log are held to making none that does. The dispatch is asserted
  to be the one that does, so the relation is held in both directions.
- **An empty step list is *unavailable* and never zero.** The host answers with no job list for a
  run it has not expanded and with a job carrying no step list at all, and zero executed steps is
  § 2's never-started reading. Both shapes come back with the reading withheld and precondition 3
  named, and each is planted beside an assertion that the never-started reading is **not** what
  came back.
- **A run the host has not concluded is precondition 4 and not a reading either**, and asked to
  wait the operation blocks in the host's own client — § 2's *watch rather than poll*. The client's
  exit status is unread: it exits non-zero for a run that failed, and a failed run is an answer. The
  suite asserts the watch happens **before** the run is read, and that nothing is watched where the
  caller did not ask.
- **A supersession is read only where the project states a group.** § 2 makes an absent
  `host.runner.supersedes` a statement, so the implementation asks nothing there — asserted on the
  *call* and not only on the reading.
- **The host's conclusion word does not leave the implementation.** One word arrives on two of
  § 2's four readings, so the three facts are read here and the reading comes from the consumer
  above; the suite asserts the word appears nowhere in what a caller is handed.
- **A log is a tail with both counts beside it**, because a cut log that did not say so reads as
  the whole of what a run printed. The ingestion step stays the caller's: a role handed pre-cleared
  text has no step of its own to report.
- **A dispatch is refused without an approval that names it** — the workflow, the ref and every
  input value — and every refusal is asserted to have started **nothing**. The refusal names what
  was missing and does not compose the sentence that would satisfy it.
- **A dispatch takes a branch or a tag and a listing takes a commit**, each refusing the other's
  form. That is this host's own shape: its dispatch endpoint rejects a commit, and precondition 2
  asks about a commit rather than about whatever a branch points at now.

**Forbidding, in the sweep**: no carrier — skill, command or hook — invokes the host client for a
run, in four shapes (the client's own run subcommand, a dispatch, a pull request's runs, and the
endpoint behind all three) and in both spellings (a command line, and a list of quoted words as an
interpreted carrier writes one). The client itself stays permitted, being how a pull request is
opened, read and merged, and the green side of that narrowing is asserted: three plants that must
stay green, verified by widening the grammar to the client alone, and one for a script a carrier
calls, verified by widening the scope instead.

What it deliberately does not check:

- **That any of it reaches the host.** Every case answers through the transport the implementation
  names, so no suite here establishes that a dispatch lands, that a run listing's filter is the one
  the host honours, or that a log comes back for a run still in progress. That half is driven by
  hand and recorded on the work item.
- **The client reached through an indirection.** The sweep's arms are anchored at the client's own
  name, so an alias the carrier set earlier and the client's name held in a variable are each one
  step out of reach: a grammar chasing either would be reading the shell rather than the call, the
  false-positive direction this sweep may not err in.
- **A role naming the forbidden call in order to forbid it.** That reddens, the one false positive
  this check has, so both edited roles describe the call rather than quoting it. An exemption keyed
  on a marker in the same line would be a hole in the shape most likely to be written by somebody
  arguing for the call.
- **Which dispatches reach a live target.** Every dispatch carries an approval here, the strict
  reading. Narrowing it to a live target alone needs the statement of which targets are live —
  configured and never inferred from a name — which is #13's and no facet's yet.
- **A go replayed against a byte-identical dispatch.** The workflow, the ref and the inputs are the
  whole of what either side can name, so two dispatches identical in all three are one dispatch to
  this rail, a limit § 29 states.
- **A supersession group keyed on anything but the workflow and the commit.** The concurrency
  expression lives in the workflow file and the host publishes no *retired by* field. A supersession
  this misses reads as never-started rather than as green — the wrong remedy, and not coverage.
- **Which of the host's two records a reader is looking at.** Measured: a run reported `completed`
  with its conclusion set while the job behind it was still `in_progress` with none, and the pull
  request's own check view — which reads that second record — showed the check pending for the same
  commit at the same moment. The operation answers about the **run**, § 2's preconditions being
  about one, and it reconciles nothing: whether a change may merge is the host's own merge state,
  which the finishing role reads separately, so a consumer told green here and refused by the host
  is meeting that lag rather than a disagreement.

## The spend half: a call put to somebody, and the one price stated beforehand

`plugins/mjolnir/scripts/spend.py --self-test` runs in the `Spend guard` workflow, with no
credential and no network. The rules are
[schema § 19](../plugins/mjolnir/config/schema.md#19-a-command-that-spends-and-the-supervision-it-is-refused-without),
[schema § 19 → What an approval is per](../plugins/mjolnir/config/schema.md#what-an-approval-is-per-and-the-one-price-stated-before-a-turn-runs),
and
[schema § 19 → The command position](../plugins/mjolnir/config/schema.md#the-command-position-and-why-the-whole-call-is-not-one)
— the last being the hundred lines of lesson, about where a command *is* in a call, that the header
of the guard this one is extracted from carries. **It is extracted, not written from the idea**,
since a rewrite from the idea reproduces the defect, so the suite's two halves are the shapes that
must be refused and the shapes that must not, planted beside each other.

| arm | what it reads | kind | what it does |
|---|---|---|---|
| `guard` (`PreToolUse`) | whether the project states a configuration at all; then a `Bash` command's own command positions, and the list the project wrote | **forbidding** | puts the call to the person, or refuses it |
| `price` (`SessionStart`) | the figure the harness states for rewriting a resumed session's prompt cache, and the project's bar | **computed** | reports a price above the bar, or reports that there was no figure |

Both arms answer nothing at all in a project that states no configuration, by
[schema § 7](../plugins/mjolnir/config/schema.md#a-hook-in-a-project-that-states-no-configuration),
and a project whose configuration does not *resolve* gets the other answer: the call proceeds and
the guard says it held nothing — the one case the fail-direction table does not settle by itself,
argued at
[schema § 19 → The command position](../plugins/mjolnir/config/schema.md#the-command-position-and-why-the-whole-call-is-not-one)
— and a project that states nothing also fails to load, so the suite asserts the predicate itself
beside both silences, or an arm with its configuration gate gone would pass.

The call shapes are enumerated by hand: the suite runs the denied command through each shape it
arrives in, in four families — the way it is spelled, what stands in front of it, what it is nested
inside, and what follows it — and the complement is the same path standing where it is **not** a
call: in another command's prose, as an argument, as a redirection's target, inside a
here-document's body, inside single quotes, and as a longer name merely ending in it
([schema § 19 → The command position](../plugins/mjolnir/config/schema.md#the-command-position-and-why-the-whole-call-is-not-one)).
The run prints the count of each family.

Each runner has a call shape of its own in the suite, written out rather than generated from the
runner table — a plant derived from the table would assert whatever the table said. The shapes carry
each runner's own arguments, because a runner that takes a duration or a lock file before the
command is one a bare `<runner> <command>` plant passes without reaching. The tables themselves are
asserted row by row: a mistyped runner, a flag written without its dash, or two shapes joined by a
missing comma matches nothing the parse ever produces, and every other assertion stays green.

Every green plant reddens when the mechanism it names is broken. A redirection's target stands in no
command position, so whether `> <path>` is read as an *argument* has a plant of its own; so do the
price arm's event gate, the quoting plants, the cache-state clause and the two comparison arms of
the surface check.

The decision vocabulary is read out of the surface, so a value the surface states and this carrier
decides nothing for reddens the run, and so does one it decides for that the surface stopped stating
([schema § 19 → What an approval is per](../plugins/mjolnir/config/schema.md#what-an-approval-is-per-and-the-one-price-stated-before-a-turn-runs)).

The price arm can be wrong only about a report. The harness states the figure for some sources and
not others; a payload carrying one is priced whatever its source says, and the set of sources is
read only to decide whether a *missing* figure is reported as missing. So a source the harness
starts pricing is handled with no edit here, and the suite asserts that direction directly.

### What this check deliberately does not hold

- **A spend reached through a launcher the project does not list.** A paid script handed to an
  interpreter, or a multi-word string handed to a shell's flag, stands in no command position of its
  own. A project invoking one that way lists the launcher
  ([schema § 19 → The launchers a project lists](../plugins/mjolnir/config/schema.md#the-launchers-a-project-lists-and-what-each-one-runs))
  or states that spelling itself, and
  [schema § 19 → The command position](../plugins/mjolnir/config/schema.md#the-command-position-and-why-the-whole-call-is-not-one)
  says why no list of interpreters may live here.
- **A spend that runs on another machine.** A call that reaches a remote shell is a command whose
  payload is an argument here, so the guard sees the remote client and not what it was asked to run.
  A project that spends that way states the client and the pattern its arguments carry, which is
  what `args_match` is for.
- **A path spelled another way.** The command comparison is lexical, so the same executable reached
  through a symlinked directory, or spelled in another case on a filesystem that ignores case, is
  not the configured command. A hook that stats the filesystem for every entry on every call is the
  costlier answer.
- **An `args_match` whose anchor is narrower than the calls it meant to catch.** A pattern anchored
  with `^` holds only the call whose paid argument comes first, which
  [schema § 19](../plugins/mjolnir/config/schema.md#19-a-command-that-spends-and-the-supervision-it-is-refused-without)
  states at the key — the suite plants both sides of it, and nothing here can tell a narrowing
  somebody wanted from one they did not.
- **A spend that is not a shell command.** The guard reads a `Bash` call; a paid request made by a
  tool of its own, by an editor action, or by something a workflow starts on the host reaches no
  event here.
- **Whether an `args_match` matches the right calls.** The reader refuses a pattern that does not
  compile, since one matching nothing is a paid command that reads as denied and is never refused;
  a pattern that compiles and matches the wrong invocations is a project's own statement about its
  own commands.
- **What a denied command actually costs.** `reason` is prose a project wrote; a figure that is
  stale or wrong answers this check exactly as a correct one does, and
  [schema § 19](../plugins/mjolnir/config/schema.md#19-a-command-that-spends-and-the-supervision-it-is-refused-without)
  keeps every cost and every budget in the project.
- **Whether anybody was in fact watching.** The ask holds the call until it is answered; who answers
  it, and whether they read the cost, is the decidable end
  [schema § 7](../plugins/mjolnir/config/schema.md#what-a-hook-refuses-and-the-record-it-reads)
  takes for the review question.
- **An approval remembered across calls.** Nothing is stored, so two identical paid calls are two
  asks. That is the rule, not a limit.
- **What the figure says about any command.** The price arm reads one event's own cost. It is not a
  meter: nothing here knows what a session has spent, and no key states a budget.

## The live half: a session put to somebody, and the names that clear one

`plugins/mjolnir/scripts/live.py --self-test` runs in the `Live guard` workflow, with no credential
and no network. The rules are
[schema § 21](../plugins/mjolnir/config/schema.md#21-a-command-that-could-open-a-session-on-a-live-machine),
[schema § 21 → Which verdict](../plugins/mjolnir/config/schema.md#which-verdict-and-who-would-answer-the-prompt),
[schema § 21 → The machines named](../plugins/mjolnir/config/schema.md#the-machines-named-are-the-ones-that-are-not-live)
and
[schema § 21 → The four ways it fails closed](../plugins/mjolnir/config/schema.md#the-four-ways-it-fails-closed),
and the table below names the arm that carries them.

| arm | what it reads | kind | what it does |
|---|---|---|---|
| `guard` (`PreToolUse`) | whether the project states a configuration at all; then a `Bash` command's own command positions, the entries the project wrote, the file those entries name and the mode the event arrived in | **forbidding** | puts the call to the person, refuses it, or says nothing |

The command position is the sibling guard's, imported
([schema § 19 → The command position](../plugins/mjolnir/config/schema.md#the-command-position-and-why-the-whole-call-is-not-one)).
There is one parse, one set of lexer settings, one answer about which token is the command. The
suite's own position shapes are asserted here as well, since what this carrier could get wrong is
the use of the parse. With the import replaced by a match on the raw text, fourteen assertions
redden — the shapes where the command is named and not called.

Every green plant reddens when the mechanism it names is broken. With the allowlist never read,
forty-three assertions redden. A call whose machine sits behind a flag the entry states takes a
separate word passes; its plant points at an **allowlisted** machine behind such a flag, since a
flag's value in no list is held exactly as a live machine is.

The mode table is asserted per member and in both groups: with the session-answered arm answering
like a person-answered one, five assertions redden; with an unrecognised mode read as
person-answered, two. The table is the harness's vocabulary, so a mode the harness adds is read as
unrecognised and refused until somebody classifies it.

### What this check deliberately does not hold

- **A machine that is not the call's first plain word.** The reading is positional:
  [schema § 21](../plugins/mjolnir/config/schema.md#21-a-command-that-could-open-a-session-on-a-live-machine)
  states it and states the direction it is wrong in. A command that takes its target second — a copy
  whose source is local and whose destination is remote — has its *first* word read as the machine,
  which is in no list, so the call is put to a person. Resolving it per command would need a target
  grammar per tool in the toolkit.
- **A name spelled another way.** The comparison is lexical and whole-word: the same machine
  reached by an address rather than by the name the list carries, or by a second alias nobody
  added, is not the name in the file. For a live machine that is the safe direction; the unnamed
  alias of a *cleared* machine gets a prompt.
- **A session opened through a launcher the project does not list, or a wrapper script of its
  own.** The spend half's residue, for the same reason: the thing in the command position is the
  launcher, and no list of interpreters may live here.
- **Whether the machine behind an allowlisted name is still not live.** A name left in the file
  after that machine became live answers this check exactly as a correct one does.
- **A session that is not a shell command.** The guard reads a `Bash` call; a connection made by a
  tool of its own, by an editor action, or by something a workflow starts on the host reaches no
  event here.
- **Whether a person in fact answered.** The ask holds the call until it is answered; the refusal
  makes the answer something asked for in the conversation. Who answers, and whether they knew which
  machine it was, is the decidable end
  [schema § 7](../plugins/mjolnir/config/schema.md#what-a-hook-refuses-and-the-record-it-reads)
  takes for the review question.
- **A mode the harness renames.** The vocabulary is read from the payload, so a renamed mode is an
  unrecognised one and is refused. The gate catches a *dropped* arm and not a renamed mode: the
  carrier's own table is asserted for shape and disjointness only.
- **Whether a project's `valued_flags` is complete.** A flag nobody listed consumes nothing, so its
  value stands where the machine would and the call is held — a false prompt rather than a silent
  pass.
- **A call that cannot be parsed and only *mentions* a session command.** The positional rule is
  suspended there, by
  [schema § 21 → The four ways it fails closed](../plugins/mjolnir/config/schema.md#the-four-ways-it-fails-closed),
  so an unclosed quote around prose naming the command is held, and the report names the whole call,
  there being no segments to count.

## The context half: a call bounded where it is made, and what comes back

`plugins/mjolnir/scripts/context.py --self-test` runs in the `Context guard` workflow, with no
credential and no network. The rules are
[schema § 22](../plugins/mjolnir/config/schema.md#22-what-enters-the-window-bounded-where-the-call-is-made),
[schema § 22 → The three arms](../plugins/mjolnir/config/schema.md#the-three-arms-and-the-one-that-rewrites-rather-than-refuses),
[schema § 22 → A read this session has already made](../plugins/mjolnir/config/schema.md#a-read-this-session-has-already-made),
[schema § 22 → The commands a project names as never bounded](../plugins/mjolnir/config/schema.md#the-commands-a-project-names-as-never-bounded)
and
[schema § 22 → Why every unestablished fact here proceeds](../plugins/mjolnir/config/schema.md#why-every-unestablished-fact-here-proceeds),
and the table below names the arms that carry them.

| arm | what it reads | kind | what it does |
|---|---|---|---|
| `guard` (`PreToolUse`) | whether the project states a configuration at all; then, for a command, its own command positions and the entries the project wrote; for a read, the path and range the call states and the file's own size and modification time | **forbidding** | refuses the call, rewrites its arguments, or says nothing |
| `result` (`PostToolUse`) | the command the result came from, the result's own text, the stated limit and the directory a full text goes to — and, for a read, the path and range it was made over | **computed**, then forbidding | replaces a result with a path, a head and a tail; or records the read the arm above compares against |

The command position is the spend guard's, imported
([schema § 19 → The command position](../plugins/mjolnir/config/schema.md#the-command-position-and-why-the-whole-call-is-not-one)).
The suite's own position shapes are asserted here as well. With the entries matched against the raw
text of the call instead of its positions, twenty-five assertions redden — the shapes where the
command is named and not called.

Every green reddens when the mechanism it names is broken, by these counts: with the exemption never
read, four; with a call that already carries its own bound no longer recognised, seven; with the
bounded form a refusal names no longer recognised as a route, three; with every call treated as one
command so that every rewrite is attempted, seventeen; with none treated as one so that nothing is
rewritten, twenty; with a file's signature frozen, the one assertion that a changed file is readable
again; with the ledger forgetting, eight; with the session not told of a rewrite, five; with a
replacement made whether or not it is shorter, eighteen; with the sidecar reported written without
being read back, eight; with a command compared as a word rather than as a path, two; with no text
read out of a structured response, two. A read-back of a path naming no file reports what it could
not read instead of killing the suite.

What the arms do, each against a failure a reading of them would not catch:

- The replacement takes the shape the response arrived in. The harness validates a replacement
  against the tool's own output schema — for the command tool, a block of fields — and on a mismatch
  discards it, keeps the original and adds an error beside it.
- A rewrite answers with the whole input, since the harness assigns a hook's answer over the input
  wholesale: an answer carrying the command alone would bring a backgrounded call to the foreground
  and drop a stated timeout.
- The exemption is read per command, so appending a chained exempt command spares nothing in front
  of it.
- The sidecar's write and read-back do not translate line endings, so a result carrying a carriage
  return is not reported unwritable.
- A bound stated as `--flag=N` is recognised, so the project's bound is not appended over one the
  session already chose.
- A rewrite is not appended past a comment or past the end-of-flags marker, where the shell reads no
  flag at all and the dump would run unbounded while the session was told it was bounded.
- The ledger is a file per read, the lease carrier's shape: a whole-file read-modify-write lost six
  of eight entries of a parallel read batch.

The one arm that acts on a call rather than refusing it is asserted on what it produced. A rewrite
answers with no decision at all, so *nothing* is what a passing call and a dead rewrite arm both
look like: each shape is asserted on the rewritten command carrying the project's own bound, and so
are the two shapes where a longer flag or a named-but-not-called exemption could be misread.

### What this check deliberately does not hold

- **Whether the command accepted the bound.** The flag is the project's statement about its own
  command, added to the arguments as text; nothing here runs the command to find out whether it
  takes that flag, or whether the value means what the project thought. A guard that validated flags
  would carry a table of every project's tooling, which
  [schema § 22](../plugins/mjolnir/config/schema.md#22-what-enters-the-window-bounded-where-the-call-is-made)
  keeps out by naming none. A wrong bound is a call that fails loudly on its own next run.
- **Whether a replacement the harness accepted is the one a model read.** What the harness does with
  the field is no longer unestablished: read out of the installed client (the reference states
  none of it), it validates a
  non-external tool's replacement against that tool's own output schema. No run here can confirm
  that the accepted replacement is what reached a window, the plugin's hooks being served from the
  installed checkout rather than from a tree under work
  ([what a session serves](working-on-the-toolkit.md#what-a-session-actually-serves)).
- **A narrower re-read of a file already read whole.** The key is the path and the range as the call
  states them, so a read of part of a file this session read in full passes. That is also what
  releases a refusal from inside the session, by
  [schema § 22 → A read this session has already made](../plugins/mjolnir/config/schema.md#a-read-this-session-has-already-made),
  so narrowing it would close the only route past the arm a session has.
- **Which window a session's reads were read into.** The ledger is keyed by the session the event
  names, and whether a subagent's calls arrive under their own session or under the one that
  launched them is **unestablished**, for the same reason. If they arrive under the parent's, a
  subagent can be refused a read whose content its own window does not hold, and what releases it is
  the same route a summarised window takes: a different range.
- **Whether what a read put in the window is what the ledger recorded.** The signature is taken when
  the read has already happened, so a file written by something outside the session between the read
  and the event is recorded as the content read. The refusal that follows is a false refusal with a
  stated route out.
- **Whether what a session read is still in its window.** The ledger records that a read happened,
  and a window is summarised without being asked. A refusal after that names a file that is no
  longer there to read, which is why the escape above exists.
- **A read that is not the read tool's, or a command that is not the command tool's.** Both arms
  read the two tools the matcher names. A file pulled into the window by something else — another
  tool, an editor action, a subagent's own transcript — reaches no event here.
- **How much of a window anything has left.** No reading of that is available while a window fills
  ([the measurement](configuration-surface.md#why-there-is-no-threshold-on-the-surface)), so every
  reading here is of the call: a command's arguments, a result's length, a file's own timestamps.
  A result inside the limit and a window at its last thousand tokens are the same answer here.
- **A result already on its way.** The replacement happens after the command ran, so the time and
  the output were spent whichever way this arm answers; what it buys is the window. The arm that
  saves the run is the refusing one, configured command by command.
- **Whether a project's exemption is still true.** A command left in `never_bound` after the role
  that forbade truncating its output stopped existing answers this check exactly as a correct one
  does.

## The install half: what the toolkit writes into a project

`plugins/mjolnir/scripts/install.py --self-test` runs in the `Installer` workflow, with no
credential and no network. The rule is
[schema § What the toolkit installs](../plugins/mjolnir/config/schema.md#what-the-toolkit-installs-into-a-project-and-what-takes-it-out)
and the step is **separate from the step that asks**. The interrogation that writes a project's
configuration takes its question set from the surface's own section list, so it is built after every
facet it asks about. The artifacts need none of those answers, so the install step is its own half,
with no dependency on any facet.

**The artifacts are each their own work item, and the registry states which are built.** What each
file says and which configured value it reads belongs on the item that builds it, not on a
placeholder in the registry. A registry holding nothing is reported as an answer, by
[§ 2](../plugins/mjolnir/config/schema.md#2-code-host)'s rule that absence of signal is not one,
and never as a complete install. The arm is an equivalence, not *the report is non-empty*, so it
holds in whichever direction the registry stands.

An entry is composed from the project's own facts, and the title gate's is composed from the very
facet that decides whether the gate is wanted — so a project that stops stating that facet leaves
nothing to compose the entry from. An artifact therefore declares the workflow name it registers
under, and the removal finds its entry by that name — the one key
[§ 2](../plugins/mjolnir/config/schema.md#2-code-host) keys the facet on. An artifact declaring no
such name claims none, which keeps a genuine collision between two artifacts from being read as one
replacing the other, and an artifact's own earlier entry under its own key is replaced rather than
refused as a collision — read as one, a project that edits the facet would be refused for ever over
the step's own output.

What it holds, per artifact: the marker at the head and the body below it unchanged; a shebang
keeping the first line; the mode the artifact's kind states, which a hook has to carry or git does
not call it; a second run leaving the file and its mode alone; a file carrying no marker neither
written over nor removed, in both directions the step runs in; an absent value naming itself with
nothing written; a `host.checks` entry refused before anything is written and put back after it
where the insertion fails; the entry inserted into the project's own configuration without
re-rendering it, and taken back out when the artifact is; and a place that could not be resolved
reported as that rather than as nothing being there. The kinds are the two this document draws:
**computed** throughout — a path, a mode, a byte comparison, a reader's verdict — with no
forbidding arm among them.

**The registry's order is install order, and every removing route walks the reverse of it**, by
[§ What the toolkit installs](../plugins/mjolnir/config/schema.md#what-the-toolkit-installs-into-a-project-and-what-takes-it-out)'s
removable property. A registry may hold an artifact that only works while a sibling is there, and
one order for both directions produces the state the order exists to avoid: the called file gone and
the caller still installed, which is a red check on every change rather than something inert. Two
routes remove — the explicit removal, and a configuration that stops asking — and both arms read the
order off the acts rather than off the report, which stays in registry order. A directory the
toolkit owns does not outlive its last artifact, while a directory the project owns is left standing
empty: the toolkit writes into the host's own workflow directory and does not own it.

**Where a generated gate goes is not this module's**, by
[§ 2](../plugins/mjolnir/config/schema.md#a-workflow-whose-jobs-mirror-more-than-one-command).
Which directory a host kind keeps its definitions in is the drift check's one host fact, read from
there, and both halves of the arm asserting that are computed from the fact, read off the parse tree
by component rather than by path: the idiom this codebase uses is a `join` of the path's two
components, so a match on the joined path inside a quoted literal finds nothing, and a search for
the sibling module's name is true however the module behaves.

The configuration is edited textually and never re-rendered, a round trip through a parser taking
out every comment a project wrote about its own facts with nothing reporting the loss. Two fixture
shapes are needed and neither substitutes for the other, as breaking the walk one way at a time
shows:
| the break | which fixture holds it | why that one |
|---|---|---|
| the member indent computed as *the key plus two* rather than read off the list | the **dumped** configuration, alone | its members sit at the key's own column, so a derived indent writes a member the file cannot parse |
| a nested block list read as the end of the list | this repository's **own file**, alone | one of its entries states `triggers` as a block list, so the walk stops inside a member and the entry lands between a key and its own values |
| a parser round trip in place of the textual edit | this repository's **own file**, and the comment arm of the dumped one | only a hand-written file has lines a round trip can lose |

A dumped configuration has no comments, its keys are sorted and its list sits at its key's column;
a hand-written one has the opposite of all three, and each shape is the only one that reddens for
one of the two walk defects. The one hand-written configuration in reach of a test is this
project's own file.

**The step asks nothing**
([schema § What the toolkit installs](../plugins/mjolnir/config/schema.md#what-the-toolkit-installs-into-a-project-and-what-takes-it-out))
— asserted, since a step that asked one question would be waiting on the interrogation it was
separated from. It is read as a parse tree, for the reason the directory arm above is: a lexical
form has to write down the spellings it forbids and then finds its own list.

Every plant reddens when the mechanism it names is broken; the list of breaks is the suite's own
output. The classes of break that would redden nothing, each of which an arm now covers:

- **An arm matched against the thing it forbids finds its own text** — a regex carrying the
  workflow directory, a search for the sibling module's name, a list of the spellings that read from
  whoever ran the step. All three are read off the parse tree, the directory one by **component**,
  because the spelling this codebase uses is a `join` of the two parts.
- **An arm compared against the function that produced the value.** Asserting the marker's head
  equal to what builds it moves both sides together; what is asserted is the two things the marker
  has to say.
- **A refusal asserted by a word every refusal shares.** `no` appears in all four of the walk's
  refusals, two of them through *cannot*; each refusal is named by its own sentence.
- **An arm satisfied by the registry being empty rather than by the branch it names** — *nothing
  was written where a workflow would go*, and *nothing is written* read off the answer's own `path`
  field rather than off the tree.
- **A rollback asserted on the route that never writes.** An unstatable entry the reader refuses
  *before* any write passes because nothing was written; the post-write rollback, and the directory
  it has to remove, are reached by a `host.checks` the reader accepts and the textual walk refuses.
- **A stop asserted where nothing states the thing it stops on.** *A machine-wide hooks path is a
  stop* is asserted with the scope planted, not as *either nothing states one or this answers
  nowhere*.
- **A read-back asserted through the shape it cannot reach.** `register`'s restore and its
  does-not-carry-the-change condition each need a route where the file and the configuration in
  hand disagree.
- **Half a rule asserted.** `needs` is satisfied by an empty collection *and* by an explicit
  absence; the second is unreachable from any loadable configuration, so it is asserted at the
  function with that stated.

The asking break sits inside the step, so it reddens the arm written for it, in both the asking
and the stream-reading form, instead of stopping the run before the assertion.

**One precondition the suite does not check for itself: git on `PATH`.** A hook has to be
installed into a repository, so one arm initialises a tree of its own — and asserts that it did,
and that git answered where that tree's hooks are called from, **before** it asserts anything about
a file in it. Read as a skip, a missing git would turn the whole hook half of the suite green while
holding nothing, which is
[§ 11](../plugins/mjolnir/config/schema.md#a-report-names-what-it-could-not-establish)'s direction
applied to a suite's own fixture.

**The two facet gates are held as themselves, including in a bare checkout.** Per facet: both files
written where the facet is carried and neither where it is stated absent, the checker carrying the
facet and the workflow none of it, the entry mirroring the command the workflow runs, a second run
byte-identical, no drift against the drift check, and both files and the entry taken out when the
facet is dropped. The checker is then rendered into a repository holding nothing else and run
isolated — `-I`, from another directory, with an environment of `PATH` and `HOME` — and held red
and green on that tree; an import arm alone would pass a copy reaching for a variable the event does
not state. The register's copy is also held refusing a run that states no base, the one place the
vendored half differs from the toolkit's: the toolkit's copy derives a base through the claim
carrier, and a copy that derived one of its own would be a second derivation free to disagree with
it.

The ignored-configuration arm is held against both halves of the bound: the facet gates refused
with nothing written, and the body gate keeping the answer it had, so a project stating nothing new
behaves as it did. A documents root above the code root has an arm of its own, the refusal being
reachable by no configuration the ignored-file arm builds.

### What this check deliberately does not hold

- **Whether a generated artifact is the artifact somebody wanted.** What each file *says* is its
  own work item's, asserted there; this suite holds that whatever an artifact states is written
  byte for byte below the marker and nothing else. A gate that enforces the wrong rule correctly
  installed is green here.
- **A generated file under the sweep that names no other project.** That sweep reads this
  repository's own tracked files, and a generated artifact is written into somebody else's — so
  what stands in for it is an arm asserting the **step** carries no literal the configuration
  states, read off its parse tree. That is the narrower claim: every project-specific value in a
  generated file comes from the adopter's own configuration, and nothing here opens that file where
  it lands.
- **Whether the guard on an already-run command would in fact let a local run through.** The title
  gate's entry mirrors no command, which this suite asserts through the shared reader — no mirrored
  record names it. The guard itself is not run here: it needs a host to answer about a change, and
  what it does with the records it is given is its own suite's.
- **The artifacts the split was made for, beyond the one that is registered.** Every property above
  is held against fixtures of each kind; the title gate is additionally held as itself — written,
  parsed as the host has to parse it, its expression equal to the one derivation beside the step,
  its entry mirroring no local command, its own script **run** against titles that must pass and
  titles that must be refused, and both halves of it taken back out when the facet is withdrawn.
  For every artifact the registry does not yet hold, the suite proves the step and that artifact's
  own item proves the artifact; neither is to be
  inferred from a green run.
- **A question the step *delegates*.** The arm asserting it asks nothing reads this module's own
  parse tree for a call or an attribute by name, so a question put through another module, or a
  read of the standard input by a route that does not name it, is invisible to it. The direct forms
  are held; the indirect ones are a reader's.
- **That every arm is load-bearing.** The suite reports its own count and cannot execute nothing
  and exit zero, but the floor it asserts is that it ran at all. What holds each arm is the break
  written for it, not the count.
- **Whether the host then runs the workflow that was installed.** That is the facet against the
  host's own definitions, and the drift gate reads it one claim over — but only for a file already
  in the tree. A workflow written and never pushed is held by neither, and for the register's gate
  neither is the full-history checkout its merge base needs.
- **A project's own workflow already running the same facet check.** A project that wrote a gate
  for its documents by hand gets a second, generated one beside it under a different name, and
  nothing here reads the commands the first one runs. This repository is one: its own `Documents`
  run reads the toolkit's copy in place.
- **A project's own file at a path a future artifact will take.** The stop is per artifact and per
  run, so an adopter finds out at install time.
- **Whether `core.hooksPath` is the route a project ought to take.** The step reads the
  **repository's own** scope and decides neither route; which one a project ought to take is
  [the rail's own section](#the-rail-under-the-authorship-rule-and-the-three-halves-it-does-not-reach),
  where it is recorded. A path stated for the whole machine is a stop and not a third route: git
  would call hooks from there, so a copy inside the repository would never run, and that directory
  is not somewhere this step may write. The step reports what a fresh clone has at whichever route
  answered, a per-route answer and not a verdict: neither route survives a clone, so what is
  reported is which gap this repository has.
- **Whatever is not committed**, and **issues and pull requests**: this suite reads trees it creates
  and the configuration in the checkout.

## The asking half: the question set against the surface it is derived from

`plugins/mjolnir/scripts/configure.py --self-test` runs in the `Setup questions` workflow, with no
credential and no network. The rule is
[schema § What a project is asked](../plugins/mjolnir/config/schema.md#what-a-project-is-asked-and-the-one-file-the-answers-are-written-into)
and the question set is derived from it: the surface's own key inventory, read at run time. What
is written by hand is, per key, which of three things answers it — a reading, a question, or a
stated decision not to ask. The coverage arm compares the two sets **both ways**: a key the step
answers and the surface no longer declares is a question about a facet that is gone, which a project
answers into a configuration the reader then refuses.

The shared reader skips a `- key:` line, an entry not being a key, so the first key of every list
entry the surface shows — the workflow a check names, the tier a test tier is, the command a local
check runs, and six more — is invisible to a walk taken off its key inventory. The step reads those
in one pass with the ordinary keys: document order is what the questions are put in, and two walks
concatenated would ask which command a check mirrors before asking whether the project has any
checks at all.

A facet added to the surface after the step shipped reddens the coverage arm until a question
reaches it, which is the facet-added arm. Its plant goes into a copy of the surface, never into the
file: version control's own checkout of the file cannot tell the break from any other uncommitted
edit to it.

**What else it holds**: every question carrying what the surface states about its key and nothing
the step decided — the alternation as a menu, the requiredness, the condition, the default, the
private mark, the facet whose carrier may be absent; a key the interrogation answered not asked
again; a tracker's own vocabulary becoming the **menu** of the question it answers while the
question is still put; the shortfall naming every key at once rather than one per round trip, in
each of the four ways a configuration can be short; a private-marked value routed out of the
tracked block and a private value with no layer stated refusing the write with nothing written;
every shipped example written into a fresh tree and accepted by the reader; a second write leaving
the file byte-identical; a configured project's own comment surviving an edit of one key; and the
head marker at the head alone, carrying nothing that moves, removable, and absent from a file a
person wrote.

The two read-back conditions need two fixtures. A file that stops loading is the first; a file that
**loads and does not carry the change** is the second, and the two come apart only where a
configuration states a key twice. The plant is a duplicate inside one block: a second block
appended at the end replaces the whole block and is then refused for the keys it drops, which is
the *first* condition firing.

Two spellings this step shares with other files: the placeholder form the private-value sweep reads,
and the three words a vocabulary read answers with, which are the port's. The port's are imported —
it ships in the plugin beside the step — while the sweep's is stated in the step and asserted equal
here, that file living with this repository's own tools and not in the plugin, where no adopter has
it. The arm is skipped rather than failed in a tree without that file, which is an adopter's.

The editor finds a key only inside its own block: a child search that stopped only at column zero
would run on into a **sibling** block and edit a key of that name there, while holding on every file
whose blocks happen to be in a helpful order. The plant is two sibling blocks at one depth, each
holding a key the other does not. The one thing an edit does not keep is a comment inside a list, a
list being replaced whole because an entry's position carries meaning the facets state; that is
asserted as a bound.

### What this check deliberately does not hold

- **Whether a question is a good question.** The coverage arm holds that every facet is *reached*;
  nothing reads whether what is asked about it is the right question, or whether its wording would
  get a correct answer out of a person — the *quoting* kind of check.
- **Whether a detected value is right.** A reading is asserted to be taken, reported, and turned
  into a question where it fails; whether the slug a remote names is the repository somebody meant
  is a fact only they hold, which is why the step reports every reading.
- **A tracker's own interrogation against a real tracker.** Each adapter's `read_vocabulary` is held
  by that adapter's own suite against a substituted transport, which is where the decisions are —
  an archived list left out, a nameless label left out, one tracker's statuses flattened across its
  issue types, another's left unestablished because the field is a project's to name. No run here
  reaches a tracker, so what a live instance answers is unestablished by this gate.
- **That a configuration the step writes is one an adopter wants.** The reader accepting it is what
  is asserted; whether the project then runs is every other check's subject.
- **Whatever is not committed**, and **issues and pull requests**.

## The body gate: the sections a change has to answer

`plugins/mjolnir/scripts/check_body_sections.py --self-test` runs in the `Body sections`
workflow, with no credential and no network. The rule is
[schema § 20](../plugins/mjolnir/config/schema.md#20-the-sections-a-pull-request-body-must-carry).

**One implementation and two callers, asserted.** A host run and a local run disagreeing about a
body is the state the facet exists to remove, so the arms render the vendored copy, execute it as a
separate process against the same planted bodies the source is held to, and assert the same exit
status and the same verdict on each. Three bodies — answering both sections, answering one,
answering neither — because a copy agreeing on green alone would agree with any implementation that
never refuses.

**The file is split at a sentinel.** Everything above the sentinel line is the rule and is what the
install step vendors; everything below is the renderer and the suite. The acceptance this carries
is [§ 20](../plugins/mjolnir/config/schema.md#20-the-sections-a-pull-request-body-must-carry)'s —
a generated file carries no heading the configuration did not state — and it is held **on the
parse tree**: every string literal of a rendered copy is either one the vendored half already
carried or one the fixture configuration stated, and anything else is named. A whole-file render
carried the suite's own fixture headings into the artifact.

**What a body is read from, in order.** An explicit file, then the environment variable the
generated workflow sets off the event, then the host's own CLI for the pull request on this branch.
A body that could not be read is reported as that and on a status of its own, by
[§ 11](../plugins/mjolnir/config/schema.md#a-report-names-what-it-could-not-establish): read as an
empty body it would refuse every section at once. An empty `PR_BODY` is a body and not an absence —
a body edited down to nothing is exactly what the gate is for.

What else the suite holds: a section answered at any heading level, in any case, and with the
emphasis a body wraps a heading in; the configured *nothing* answer accepted bare, as a bullet,
and without its trailing period; a section closed with a horizontal rule still read as answered; a
heading quoted inside a fence read as not stated at all; a heading stated twice refused; an empty
section refused; and the *nothing* answer with anything beside it refused, which is the arm that
makes the whole-section rule load-bearing. Every refusal is reported, never the first, so a body
missing three sections hears about three. The kinds are **computed** throughout: each arm is a
verdict over a body this suite wrote, and the one list the script carries — the sections — is
empty in the copy that ships.

**The opposite reading lives in this file.** A collecting role asks which of a project's sections
*this* change owes work under and which it closed with the configured answer — the gate's own
grammar read the other way. Whether a section closed with *nothing* turns on a normalisation — a
list marker, a trailing period, the emphasis a body wraps a line in, its case — so a role deciding
it by eye would be a second grammar. It sits below the sentinel, because it reads the configuration
and a vendored copy may import nothing of this toolkit; the arm asserting every import of the
rendered half is in the standard library holds that. It has three readings — owed, closed with
nothing, and `unheld` for a body the gate itself would refuse — and its key arm is the *nothing*
answer written as an emphasised bullet without its period, which the grammar reads as the answer
and an eye would call owed. It is no verdict about the change, and a project stating no section is
answered on a status of its own.

**The grammar is shared with the gate on open items and the heading is not**, by
[§ Nothing is deferred](../plugins/mjolnir/config/schema.md#nothing-is-deferred). How a section is
found in a body is one implementation here, which that gate imports; the heading it looks for
stays with it, because a section carried in this facet is one a project may stop stating and that
one is a section no project may stop carrying.

**What this repository is not a subject of.** `body_sections` here is `[]`, so no gate is
installed in this tree and no body of this repository is held by one. The install's own suite
exercises the artifacts, against a fixture built from the example that states a section — and the
generated workflow and its registered entry are then handed to the drift check, so the two
statements of that run are held to each other as every hand-written entry here is. The collecting
reading's own command runs in this tree for a project stating no section, and in a temporary skills
root carrying a shipped example for the arm that reads one. No run here covers the role: nothing is
deployed from this repository, so what a deploy does with a step it collected is read on the
surface.

## The rail under the authorship rule, and the three halves it does not reach

`plugins/mjolnir/scripts/strip_attribution.py --self-test` runs in the `Attribution rail` workflow,
with no credential and no network. The rule is
[schema § 6 → The rail](../plugins/mjolnir/config/schema.md#the-rail-under-the-authorship-rule-and-the-three-halves-it-cannot-reach)
and the rail is **a hook, not a setting or an instruction**. An agent setting is reported not
honoured when the commit is made by a shell command rather than through an internal commit path —
the common case for a procedure made of commands — and an instruction in a project's rules file
survives neither a compaction nor a new agent. It is a git hook and not one of
[§ 7](../plugins/mjolnir/config/schema.md#7-carrier)'s: a different mechanism with a different
lifecycle, and the two are not merged.

**The install route.** Three answers were available: install the rail into whatever directory git
answers with, install it into a tracked directory selected by `core.hooksPath`, or drop the
capability. The first is what a repository stating nothing gets, and the second is honoured wherever
a repository has already chosen it, by
[§ 6 → The rail](../plugins/mjolnir/config/schema.md#the-rail-under-the-authorship-rule-and-the-three-halves-it-cannot-reach)
— the install step reads the repository's own scope and picks neither. Against the first: `.git/` is
not cloned, so the rail is absent in a fresh clone, and the tracked-directory route does carry the
file. But neither route survives a clone: `core.hooksPath` is repository configuration rather than
content, so the tracked route produces a file that is present and **not called** — which reads as
installed to anything that looks — while an absent file reads as absent. Both need one command after
a clone, so what the route changes is the shape of the gap and not whether there is one. Dropping
the capability is refused because the rule binds every commit.

**What the suite holds.** A tool trailer out and the rest of the message unchanged byte for byte; a
human co-author kept; a squashed message with both kinds interleaved losing every tool line and
keeping every human one; a second pass over the first pass's output changing nothing; a message that
is nothing but attribution refused with the file left as it was, rather than written out empty; the
trailing run of blank lines a removed final trailer leaves behind taken off, a message with no final
newline among the shapes; and the hook's own invocation — one argument, written in place — run as a
process against a planted message file. The arm that makes every block load-bearing is asked of the
*first* block, the one a rule scoped to the final paragraph keeps; a count over the whole message
stays green against that defect.

**The address decides and the display name decides nothing.** The vendor product name in use here is
also an ordinary given name, so the suite plants a person carrying it with an address of their own
and asserts the line survives; a match on the product word in the display name reddens that arm and
two others. The domain comparison is held against a domain that *ends* with a vendor's and one that
merely starts with it, both of which belong to whoever registered them; against a subdomain, which
does not; against the host's own marker for an account that is not a person, in the address and in
the display name alike; against a trailer carrying no address at all, which is kept; against the
token's own spellings and spacings; against a `Signed-off-by` naming the same vendor, which is a
person's attestation and is left alone; and against a line that merely quotes a trailer in prose.

That marker is the one read of the whole trailer and is the stated exception to the address rule —
[§ 6 → The rail](../plugins/mjolnir/config/schema.md#the-rail-under-the-authorship-rule-and-the-three-halves-it-cannot-reach)'s
own second row. Both placements are held — the suffix in the display name and the suffix in the
address — and a plant reading the address alone reddens four arms, so the read is load-bearing; a
statement that the display name decides nothing for this marker would be a rule contradicted by its
own implementation.

**The recognition list is data and is held as data.** No shape identifies a tool, so what is
recognised is a list — vendor domains for the trailer rule, product and vendor spellings for the
generated-by marker, which has no address to read. Every entry is asserted lower case, unspaced,
stated once, and carrying a reason of at least five words; the domains are additionally asserted to
be domains rather than addresses. The marker rule is held on both halves — the phrase and a
recognised name, which is
[§ 6 → The rail](../plugins/mjolnir/config/schema.md#the-rail-under-the-authorship-rule-and-the-three-halves-it-cannot-reach)'s
list rule reaching the one line that carries no address — and the suite plants ordinary sentences
carrying the phrase, one of them a sentence about this very rule, and asserts each is kept.

**The copy an adopting repository is given.** Everything above a sentinel line is the rule and is
what the install step vendors; everything below is the renderer and the suite. The arms assert the
rendered copy parses, carries the rule, carries no renderer and no suite, keeps its shebang on the
first line, imports nothing outside the standard library, and **runs as a separate process** to the
same bytes this module produces. It carries none of the suite's planted spellings, and that arm
derives its forbidden set from the planted trailers rather than naming literals, so renaming a
fixture cannot turn it quietly green. A render of a file with no sentinel is refused, asserted by
pointing the renderer at a planted file: with the split taken out, a human's address was vendored
into every adopting repository while every other arm stayed green.

**What the install step's own suite holds about it.** That the rail is written
under the name git calls and in the directory git answered with, executable, marked after the
shebang, byte-identical on a second run, registering no `host.checks` entry, and asking for nothing
— the one registered artifact that reads no configured value, by § 6 making authorship procedure.
And that it fires: a real `git commit` in a fixture repository, through the installed hook, whose
landed message carries the human co-author and not the tool one, the same commit keeping the trailer
once the rail is removed. It fires on all three paths git gives the hook a message file on — an
ordinary commit, an amend and a `--no-ff` merge — since a landing is made of the latter two. The
merge arm has a precondition of its own, that the merge ran on the trunk: a trunk name that
resolves nothing runs the merge on the side branch, which answers *already up to date* and exits 0.

**The three halves no run reaches.** The author and the committer are headers rather than message
text and no hook is given them. A pull request body is seen by no git hook and by no host
equivalent, so that half of the rule is held by the finishing role composing the body, and stated in
that role. Existing history is outside the rule, which is forward-only, and no run here rewrites
any.

**What this repository is not a subject of: whether any particular clone has the rail installed.**
The hook fires on a developer's machine, no workflow observes one, and what reports an absent rail
is the install step's own per-route answer read in the repository; read in this one, from inside a
worktree, it answers that no rail is installed here, with the route's own gap named. One install
covers every worktree: git answers a worktree with the **common** hooks directory, so a session
standing in one is held by whatever the primary checkout installed. This
repository's own history carries no tool trailer at all, so the recognition list is grounded in the
spelling the harness in use is configured to append and in the host's own bot convention. A tool
whose spelling is on neither keeps its trailer, the direction the rail is built to fail in; closing
it means a list entry, never a wider match. A repository stating a non-default `core.commentChar`
has its comment lines counted as content by the emptiness test, which fails safe: the rail does not
abort, and git's own cleanup then strips the comments and aborts on the empty message itself.

## What a pull request title opens with, derived once

`plugins/mjolnir/scripts/title_form.py --self-test` runs in the `Title form` workflow, with no
credential and no network. The rule is
[schema § 2 → What a pull request title opens with](../plugins/mjolnir/config/schema.md#what-a-pull-request-title-opens-with)
and the form has **two readers**: the finishing role **writes** a title and a generated host gate
**refuses** one; two statements of the form would be free to drift, and the direction nothing
reports is the gate passing what it should refuse. So the composition is performed once: the role
renders a title through this module and the install step writes the gate's expression from the same
call.

**Only the reference is configuration.** The arrangement — references in sequence with nothing
between them, then one space, then at least one further character — is procedure, derived from the
one project measured: a separator key with one observation behind it would be a facet invented. The
expression states repetition as a quantifier, which is correct only while the separator is empty,
and the suite asserts that it is.

What it holds: an expression anchored at both ends; the reference's own characters matched as
literals, in whichever dialect; the identifier matched as a run of digits and never as a wildcard;
repetition admitting two references where the project states it and refusing them where it does
not; a reference that is the identifier alone deriving a form too; a rendered title accepted by the
form it was rendered from; a render refused for no identifier, for a title that is references
alone, for an identifier that is not digits, and for two identifiers on a form admitting one; a
title no reference can match refused inside a deadline rather than hung over; and
the four exit statuses the command line answers with. The kinds this document draws are
**computed** throughout, with one **forbidding** arm — that the placeholder is read from the reader
and spelled in no literal of the module's own, asserted on the parse tree with the documentation
excluded, since an arm that writes down what it forbids finds its own prose.

**The expression is composed in a named dialect, because the two engines are not equally safe.**
`grep -E` decides the language without backtracking. This language's own engine does not, and a
reference ending in its own identifier makes the sequence ambiguous — `<number>` alone is the
shortest such form, and the suite states it as legitimate. Measured: 24 digits refused in 1.2
seconds, 28 in 19, and 40 in no time anybody waits, on
the one call a role makes to read back a title it has just written. So the gate carries the
expression and the role **walks** the sequence one reference at a time, which is linear.

An arm compares the walk to the gate over every form including the ambiguous one. `grep` on `PATH`
is this suite's one unchecked precondition, so the arm asserts that `grep` *answered* before it
compares anything; read as a skip, a missing `grep` turns the agreement green while holding nothing.
The arm against the exponential is bounded by killing the call, not by timing it: the call never
returns, so the pathological title goes through a subprocess with a deadline.

**The green side is a project that states no form**, the ordinary case: a title there opens with no
reference, so there is no rule to fail. That answer is neither verdict and the suite asserts both
halves of that — read as a pass, a title nobody checked reports green; read as a refusal, every
title such a project ever wrote is wrong. The command line carries a status of its own for it.

### What this check deliberately does not hold

- **Whether the form a project stated is the form it wanted.** This suite holds that whatever form
  is stated composes into an expression that enforces it. A project whose reference is wrong gets a
  gate that enforces the wrong thing correctly, and that is green here.
- **A tracker whose identifier varies in more than its digits.** The placeholder is a run of
  digits, and whatever else an identifier carries is constant for a project and written into the
  reference literally — which is what makes one template serve a bare number and a project-keyed
  one alike. An identifier that varies otherwise is reported rather than approximated: a form that
  nearly matches is a gate refusing titles that are correct.
- **A project needing another arrangement.** The separator and the single space are procedure, so a
  project whose titles put something between two references cannot state that, and nothing here
  reports it as a limit at install time. What it gets is a gate refusing its own titles, and the
  remedy is the facet growing a key.
- **Whether the host then runs the gate that was installed.** That is the facet against the host's
  own definitions, read by the drift gate one claim over, and only for a file already in the tree.
- **A title on a live pull request.** This suite reads planted configurations and this
  repository's own; what the host holds for a given change is read by the role that wrote it and by
  the gate, neither of which is this run.
- **Whatever is not committed**, and **issues and pull requests**.

## The files a version is written in, and what a release carrier cannot promise

`plugins/mjolnir/scripts/release.py --self-test` holds
[schema § 34](../plugins/mjolnir/config/schema.md#34-the-files-that-carry-a-version-and-what-cutting-a-release-writes)
and runs in the `Release carrier` workflow, with no credential and no network.

**The module performs the edit.** A role that knew a build file's syntax would be a role per stack,
so the version patterns, the replacements and the file list are a project's and the editing is this
module's — which lets the skill beside it carry no version pattern, no version-carrying path and no
build-file syntax at all. That property is held by a grep over the carrier roots.

**What this repository is not a subject of.** `release.carrier` here is `none` — nothing in this
tree is versioned for a consumer, the plugin being installed from the tree at its default branch —
so pointed at this project the carrier answers that it has no subject and exits 3. The suite's
behavioural arms are therefore asserted against trees it builds itself, the position
[the title-form module](#what-a-pull-request-title-opens-with-derived-once) occupies for a facet
this project also does not state.

What it holds: the current version read out of each file's own capture; a plan that writes nothing;
an apply that writes every file or none, asserted with the blocked file first *and* second, since a
loop that wrote as it went would get one of those orders right; a file marked optional and missing
skipped rather than erroring, and the same file unmarked stopping the plan with its name; a pattern
matching nothing, and a file carrying two different versions, each a stop naming what it found; one
version written twice moving in both places; a replacement carrying a brace and a backslash written
literally, each of which has a mechanism that would otherwise eat it; the changelog's entry
inserted above the entries, after a preamble, into an empty file and above a file's very first
line; a changelog already carrying the version being cut stopping rather than merging; the
changelog refused with its reason where the project states CI owns it; and the facet's stated
absence coming back as no plan rather than as an empty one.

Two further arms: the report reads each file's current version in a reading mode, so a changelog
already holding the stand-in version a plan is taken against does not read back as unreadable, with
an arm per direction so the mode cannot become a blanket exemption; and the changelog insert keeps
the new heading on a line of its own on a file with no final newline (not `# Changelog## 1.0.0`)
and after a preamble that ends in a single newline.

What the module does not promise it names, by
[schema § 11 → A report names what it could not establish](../plugins/mjolnir/config/schema.md#a-report-names-what-it-could-not-establish):
atomicity against a crash. The write loop can be interrupted between two files, so what is closed is
a plan that was never going to work being carried out part of the way. No project in this tree
states the facet, so a release cut against one that does is the first exercise of that half.

## The live data step performed in order, and the reading the carrier gave up on

`plugins/mjolnir/scripts/live_data.py --self-test` holds
[schema § 35](../plugins/mjolnir/config/schema.md#35-the-live-data-step-a-deploy-performs-and-the-rails-it-is-performed-under)
and runs in the `Live data carrier` workflow, with no credential and no network.

**The ordering is the module's, not the role's.** A role free to reach the write before the dump has
been read back is a role with no rail, so the sequence is performed where it can be asserted, and
the deploying skill beside it asks for a plan, a preparation and an apply. The split into two
subcommands is the rail: a preparation that ran its three steps and then stopped is the outcome
rather than a failure, because the go is given on the rehearsal's output and a module that carried
straight on would have answered for the person, which
is [schema § The loop](../plugins/mjolnir/config/schema.md#what-carries-the-item-forward-and-where-it-stops-to-ask)'s
test for an ask.

**What this repository is not a subject of.** `deploy` here is `[]`, so no target states a step and
pointed at this project the carrier exits 3. Every behavioural arm is asserted against trees and
commands the suite builds — each command a script that exits with the status the arm needs, rather
than a shell builtin, so an arm about a non-zero status can produce one.

What it holds: the plan naming every step in order and running none; each stop planted alone and
asserted to stop at its own step, with the record an apply would read left absent in every case; a
completed preparation leaving that record and writing nothing itself; a go naming neither the
target nor the rehearsal's verdict refused in all four shapes, and one naming both writing; a write
with no preparation on record refused; a target stating no rehearsal completing with the row still
in the plan and the report saying there was none rather than that it passed; the hand-over making
no write and handing the command over whole; a hand-over under an unbound go still refused, which
is what makes `apply_by` a statement about who runs the command and not about whether it was
approved; and a write that ran and failed naming what the store is left holding along with the dump
a recovery reads.

**The rehearsal's output is not read for a verdict.** A surveyed copy whose rehearsal is guarded
must report **no divergence** to pass, so the passing output carries the same word the failing one
does, and a module stopping on the word *divergence* stops a clean rehearsal. The exit status is the
verdict, by the surface's own rule, and the output is carried verbatim for a person to read before
the go. What that leaves open is named, by
[schema § 11 → A report names what it could not establish](../plugins/mjolnir/config/schema.md#a-report-names-what-it-could-not-establish):
a project whose dry variant finds a divergence and exits zero anyway has to make that comparison
inside its own command.

The every-stop-leaves-no-record arms resolve the record's path through a configuration with an
artifacts directory: without one it falls back to the system temporary directory, a path `prepare`
never writes. The record-prepared-for-another-target arm uses the pair of names the slug cannot
tell apart — `a target` and `a-target` — since two plainly different targets already miss each other
by file name; that pair is why the carrier writes the name itself into the record.

No store exists in this tree and no arm of this suite reaches one: a step performed against a
project that states one is the first exercise of that half.

**What the reader's companion refusal does not reach.** The load-time refusal of a command that
carries its own answer is lexical, so it sees a here-string and a pipe whose left-hand side is a
printing command, and it does not see one wrapped in another interpreter — a shell invoked with its
program as an argument, whose first word is that interpreter rather than the printing command inside
it. Reading inside a quoted argument is where the false refusals are, and
[schema § 35 → Who performs the apply](../plugins/mjolnir/config/schema.md#who-performs-the-apply-and-the-go-that-is-never-the-commands-own-prompt)
already bounds that direction. The ask is not weakened by it: the go is unconditional, so a project
that evaded this refusal still reaches a person, and loses only the reader saying so at the load.

## A deploy's tree, read without a write

`plugins/mjolnir/scripts/deploy_tree.py --self-test` holds
[schema § 33 → What the tree must be](../plugins/mjolnir/config/schema.md#what-the-tree-must-be-for-the-deploy-and-for-the-advance)
and runs in the `Deploy tree carrier` workflow, with no credential and no network.
The reader's suite holds the list's shape — one plant per refusal, each red with the refusal removed
— and this suite holds the readings.

**What the suite holds.** Every condition the surface's alternation states has a reading and none
else does, so a member added there reddens here rather than reading as met. Each reading is taken
on a repository the suite builds with a bare remote of its own, in the state that meets it and in
the state that does not: an untracked file, a commit ahead of the upstream, a branch with no
upstream, a detached commit, a linked tree, a commit the repository does not resolve. Each `holds`
value is held to the deploy and the advance it stops, and a directory that is no repository, or
that could not be read, is held as not met rather than as met.

**The write the reading may not make is asserted on the index itself**: a tracked file's stat is
moved so that a status would refresh the index, and the arm compares its bytes and its time before
and after. With git's optional locks left on, that arm alone reddens.

No target in this repository states a condition, so a deploy against a project that states one is
the first exercise of that half.

## A released write, against the change that would rewrite it

`plugins/mjolnir/scripts/check_live_data_record.py --self-test` holds
[schema § 35 → A record of the store's state](../plugins/mjolnir/config/schema.md#a-record-of-the-stores-state-is-never-rewritten)
and runs in the `Live data record` workflow, with no credential and no network.

**What it compares is one intersection**: the paths a live target's own listing command prints,
against the paths this change modifies or deletes. The listing is the project's command and never a
path pattern this check carries, by
[schema § What the procedure models](../plugins/mjolnir/config/schema.md#what-the-procedure-models-and-what-it-only-names-and-calls) —
and it is read from live targets only, a store the session is the only user of being one it can
rebuild.

What it holds: a rewrite and a deletion each a problem naming the file and the target; a new write
no problem; a listing command that exits non-zero and one that is not there each a refusal naming
it rather than an empty set, which would read as a store with nothing applied to it; and the
liveness pairing in both directions, including a project with two targets one of each.

The last section of the suite builds a repository and makes one change in it for real, as
[the end-to-end register's own check](#the-end-to-end-register-against-the-suite-and-the-change-against-both)
does: the in-memory arms say nothing about the diff, and
[schema § 35 → A record of the store's state](../plugins/mjolnir/config/schema.md#a-record-of-the-stores-state-is-never-rewritten)
names the file rather than a count, so the check is held to what git actually reports.

The diff filter leaves out additions: one surveyed carrier detects its *pending* writes as the
paths added since the last release tag, and an adopter who wrote that as their listing command
would be printing the branch's own new writes, which with additions in the filter would refuse
every change the facet exists for. A planted listing command naming the path the change adds holds
that bound.

**What is not held.** Whether a project's listing command answers the question the surface asks —
*what is already applied* rather than *what is pending* — is unreadable here and is the adopter's
to get right; a command answering the second would print this branch's own writes, and the filter
above keeps that from refusing them. A shallow clone has no merge base to read, which the check
reports as *unchecked* rather than as a clean diff, so the workflow fetches the whole history.

## The bookkeeping role's derivations, and the round trip that is the resumability arm

`plugins/mjolnir/scripts/save.py --self-test` runs in the `Save artifact` workflow, with no
credential and no network. The rules are
[schema § 23](../plugins/mjolnir/config/schema.md#23-session-bookkeeping--which-thirds-a-project-runs)
and its two subsections, together with
[schema § 25](../plugins/mjolnir/config/schema.md#25-the-memory-store-and-the-tree-a-save-may-refresh-it-from)
for the store one of those thirds writes.

What it holds, each being a derivation rather than a verdict about a project:

- **Which thirds run, in the procedure's order.** The vocabulary is read out of the surface through
  the shared reader and the order is this module's, so the two are held to each other: a third the
  surface states and this module places nowhere is reported as **unplaced** rather than run in an
  order nothing decided, and the suite asserts both directions of that agreement. The ordering is
  asserted on a list written **backwards**, because an assertion written in the order it expects
  asserts the expectation and not the code.
- **The form of a save artifact, and a written one read back against it.** That every field is
  required and that the boundary is drawn from a closed set are the **carrier's** statements, as
  [schema § 23 → The artifact's form](../plugins/mjolnir/config/schema.md#the-artifacts-form-is-the-carriers-not-the-roles)
  rules. The same answer serves the role that wrote the artifact and the pass that reads one back,
  so there is one subcommand and not two.

- **Where the memory store is, and whether a working directory may write it.** Both are
  [schema § 25](../plugins/mjolnir/config/schema.md#25-the-memory-store-and-the-tree-a-save-may-refresh-it-from)'s,
  and the decision is three-valued: write, refuse, and *could not be established*. The suite builds
  a real checkout with a real linked worktree beside it and asserts each value against the directory
  that produces it, because a fixture of two directories would assert this module's own arithmetic
  over a shape the hazard never arrives in.
- **The memory entry's form, and its admission at write time.** The fields and the provenance set
  are the **carrier's**, by the same rule the artifact's form is, and the admission runs before
  anything is written. One function holds both forms, and the suite asserts the two are not
  interchangeable in both directions, an artifact failing the entry form and an entry failing the
  artifact's.
- **One entry read out of a store whose admission never ran, and the standing it is reported
  under.** Both are
  [schema § 25](../plugins/mjolnir/config/schema.md#what-a-reader-does-with-a-store-whose-admission-never-ran)'s.
  The suite asserts the lenient reading over the shape the measured store actually holds and asserts
  the strict one beside it: an entry in the form with a field missing is still refused, and the same
  store-shaped entry a reading accepts is still refused at the point of **writing**, so the lenient
  reader is not a second way in.

**The fields are keys and the prose beside them is the project's own.** A form demanding English
headings would ship one project's vocabulary to every project, which
[schema § 8](../plugins/mjolnir/config/schema.md#8-language-register-audience--per-artifact-not-per-project)
refuses. So this check reads whether a field is answered and never what the answer says.

**The round trip is the decidable end of one acceptance bullet.** The suite writes a complete
artifact, reads it back and asserts **every field by name** is recovered — a count would pass a
form that recovered the same number of fields under different names. Whether the prose a role wrote
into those fields is enough for a later pass to continue is the *quoting* kind of judgement, and it
is read rather than enforced.

### The memory store, the write decision, and the two arms on the index

One of these two arms does not reach the mechanism. Twelve processes each appending one line to
the index keep all twelve lines **with the lock removed** — a short append is atomic without one —
so the arm asserting the outcome
[schema § 25](../plugins/mjolnir/config/schema.md#the-index-is-the-one-file-two-sessions-contend-on)
states passes over a mechanism that is not there. The second arm holds the mechanism directly: with
one process holding the lock, a writer calling the carrier's own append must wait. With the `flock`
call taken out, that is the single assertion in the suite that reddens. Neither stands in for the
other: the first is what the rule is for, the second is what the rule is.

**What the write decision's own arms reach.** That the carrier reads a linked worktree as a tree and
a checkout as a checkout is asserted over directories git actually made, and every way the decision
comes back **unanswered** is asserted with it: a directory git cannot place, a pinned carrier with
no store to resolve, and a carrier stating neither of the two words. All three err the same way,
because the permissive reading of any of them writes a tree's own store. A project that states it
keeps no memory is apart from all three — nothing to answer about rather than a question that
failed — and the status it exits with is asserted over a shipped example written into a temporary
skills root. No arm reaches whether the store a project **pinned** is the store its harness writes:
§ 25's own table names that as the thing a pinned carrier owes, held by nobody.

**The admission reaches the entry's shape, not its truth.** That a fact states its provenance and
its premise is decidable and is asserted field by field; whether the premise still holds is read
against the tree by whoever reads the fact, the *quoting* kind of judgement.

**The reading's own arms reach which of three standings was reported, not whether the reader was
right.** The premise is read against the tree by a person or a role, so the suite asserts the
mapping from the reader's answer to the standing, the refusal of *current* over an entry that states
no premise, and that a fact an unstated provenance leaves unplaced reads as **repeated** — never as
measured. That last arm holds the failing-safe value inside the form's own provenance set, which
catches a constant mistyped into a word no reader can place, and also compares that value against
the literal `measured`, a string written in the suite.

### What this check deliberately does not hold

- **Whether a save happened at all.** Nothing fires when a window is compacted — the event is one
  of two that never fired in the measurement behind
  [schema § 7's table](../plugins/mjolnir/config/schema.md#what-a-hook-can-establish-about-the-role-it-is-running-under)
  — so there is no act for a gate to read and no record for one to miss. The boundary field says
  which boundary a save that *was* written was taken at, and a compaction nobody saved before is
  invisible to this and to everything else.
- **Whether a third that ran did its work.** That the tracker is current, that memory was
  refreshed, that the commit carries what it should: each is the port's, the store's or § 6's. What
  this reports is which thirds the project runs and which of their mechanisms are absent.
- **Whether a recalled fact is still true.** The entry states its premise and the admission holds
  that it does; the premise itself is read against the tree by the restoring role
  ([schema § 24](../plugins/mjolnir/config/schema.md#24-session-restore--the-readings-a-pass-is-resumed-from)),
  and no suite can take that reading for a store on somebody's machine. The standing is the answer
  handed over, never one taken here: what the suite holds is that *current* and **stale** are told
  apart and that a premise nothing checked cannot arrive as either.
- **Whether a store's entries are in the shape the store's own tooling writes.** The lenient reading
  is held over the shape this repository measured, and whether another project's harness writes that
  shape is a fact about a machine outside the run — the same thing
  [schema § 25](../plugins/mjolnir/config/schema.md#the-carriers-and-what-each-of-them-closes)'s table
  names as what a pinned carrier owes and nobody holds.
- **Whether the artifact is where § 11 says.** The store's path and whether it is committed are the
  configuration reader's, refused there; this reads a file it is handed by path.
- **Whether the boundary names match the occasions the surface states.** The four names are the
  form's, by § 23's rule that the form is the carrier's, and the surface states the occasions a save
  is owed at in prose. Nothing compares the two, so an occasion added to the surface and the form's
  set can fall out of step with no run reporting it.
- **A status this role may not write.** The writer model is a configured fact
  ([schema § 4.2](../plugins/mjolnir/config/schema.md#42-status--an-ordered-set-of-name-role-writer))
  and the reader reports it; whether a role respected it is a property of a tracker write that
  already happened, which no local suite can see.
- **Whatever is not committed**, and **issues and pull requests**.

## The restoring role's readings, and the negative no sibling suite asserts

`plugins/mjolnir/scripts/load.py --self-test` runs in the `Session restore` workflow, with no
credential and no network. The rules are
[schema § 24](../plugins/mjolnir/config/schema.md#24-session-restore--the-readings-a-pass-is-resumed-from)
and its two subsections.

What it holds:

- **The readings, in the procedure's order, each with its verdict.** The three verdicts § 24 states
  are asserted one by one, each on a reading that really has that state here, including the
  agreement between the reading this module calls storeless and the absence the configuration reader
  reports for the third that writes that store. The item reading's availability is the **port's**
  answer, asserted through a stand-in that says yes and one that says no, so this module cannot
  become a second answer to it.
- **Where the work is, against real repositories.** A bare repository, a clone, a second clone that
  moves the published ref, and a fetch in between: that is what makes the behind-the-remote arm an
  assertion, and it is the reading that cannot be taken from the tree alone. The unpushed arm is
  asserted before a push, after one, and after a commit that follows it. Four readings are reported
  as unread rather than as a position of zero, each asserted: a repository with no commit yet, a
  repository with no remote at all, a detached head, and a base ref the tree does not have.
- **What the last pass was doing, against real transcripts.** The compaction metadata read off a
  boundary record, the summary record **not** read as the last instruction, the harness's own
  plumbing not read as one either, a transcript ending on an instruction *after* a reply reported as
  a stop mid-turn, a last line cut mid-character skipped rather than fatal, the cap naming what it
  did not read, and the sidecars counted rather than read. The exclusion has three arms: the calling
  session's transcript excluded by its path and by its bare name alike, a value matching no file in
  the store reported as having matched nothing, and the warning that the first entry may be the
  caller's own **not** silenced by a value that excluded nothing. The field carries what was
  dropped, not the argument, so one mistake cannot switch off both the failure and its alarm; each
  arm reddens alone when its one line is reverted.
- **Whether a file that is gone replays, and from what.** Six shapes: first written whole, written
  whole *before* a compaction boundary, only ever edited, never written at all, a whole write of
  **another** path, and a path that does not resolve — plus the backup record that names the second
  place to look. The fifth is the discriminator: without it, deleting the path comparison leaves
  every other assertion green.
- **The window's own reading, in both directions.** A payload stating one is reported with every
  figure in it; a payload stating none is reported as *handed no reading* rather than as an empty
  window; a session that merely opened is said nothing to; and a project that configures nothing, or
  maps no restoring role, is said nothing to either.
- **That every reading writes nothing** — the one property here that cannot be read off an output,
  by
  [schema § 24](../plugins/mjolnir/config/schema.md#24-session-restore--the-readings-a-pass-is-resumed-from)'s
  read-only half. Every subcommand runs against a fixture where a naive implementation would have
  written: a store that is not there, a transcript that is not there, a working file that is
  missing. The fixture is digested before and after, and held to carrying the same entries — files,
  directories, symlinks and whatever else is there — with **one exemption named**: git's own index,
  which a read of a working tree may refresh and which is git's cache rather than this module's
  output. Directories and symlinks are both in the snapshot, since a narrower one passes a module
  creating the store it could not find, or planting a link. The exemption passes vacuously in the
  fixture measured.
- **That two runs of the same invocation agree**, asserted on the serialised answer of each
  **reading** rather than on a field of it, which forbids a clock reading or a run's own identifier
  from reaching a report. The hook arm is not among them: it is in the writes-nothing sweep and in
  no determinism check.
- **That the carrier still calls this module on the event the window reading arrives on**, with the
  `resume` subcommand rather than the script's name alone — and **the hook's own path through the
  command line**, the payload on standard input, including the unreadable payload that must be
  silence rather than a refusal.
- **Each documented exit status on the path that produces it**, including the one split that is the
  whole reason there are four: a store that is **there and empty** against a store whose location
  could not be derived at all.

### What this check deliberately does not hold

- **Whether a load happened at all**, and **whether what the report says is worth acting on**.
  Nothing fires when a person comes back to work, so there is no act for a gate to read; and whether
  a sweep's prose gave somebody an accurate picture is the *quoting* kind of judgement.
- **Whether the readings are the right set.** The order and the membership are this module's, and §
  24 holds them to nothing else, so a reading nobody has thought of is a hole no run here reports —
  the cost of the surface not carrying the list, which
  [`docs/configuration-surface.md`](configuration-surface.md#the-tenth-role-every-copy-named-and-none-of-them-wrote)
  states.
- **The store the harness keeps its records in.** The derivation is the harness's own convention
  rather than a published contract, and the suite asserts it against the rule it implements rather
  than against the harness: a convention that changes is reported by the sweep as a store it could
  not find, which is the direction that fails safe.
- **Whether a replayable file would replay.** What is asserted is that the calls are found and
  classified; actually applying them is a write, which this role does not do and no suite here
  performs on its behalf.
- **Whether the environment is standing.** [Schema § What the procedure models](../plugins/mjolnir/config/schema.md#what-the-procedure-models-and-what-it-only-names-and-calls)
  keeps that off the surface, so there is no command for a suite to run and the reading is the
  project's own script's — what is asserted is that its absence is reported as a reading not taken,
  and that a project pointing at one is handed the pointer's own value.
- **Which harness-written records are plumbing.** The list of markers is matched on the harness's
  own markup because no field marks those records, so a marker the harness renames is a plumbing
  record read as an instruction again, and no run here would report it.
- **That the base derivation stays local.** The one derivation of which branch the base is may ask
  the remote where a clone recorded no default, which writes nothing and is a network read: every
  assertion here names the base explicitly, so what the suite covers is the readings taken from that
  name and not the derivation that would have found it.
- **Whatever is not committed**, and **issues and pull requests**.

## A check that carries the mode is asserted to redden on a violation

`--self-test` plants one violation per check and asserts that check goes red, as the first step of
the workflow — before the tree is held to anything. The discipline is [`schema.md § 38 → Every
check carries a
violation`](../plugins/mjolnir/config/schema.md#every-check-carries-a-violation-it-reddens-on)'s:
an assertion written before its break tends to match only the break its author imagined, and a
check that cannot fail is not a check.

A script carrying the mode is run through it by its workflow, before the tree — or, for the gate
on the change, the pull request — is held to anything. Not every check here carries it:
`adapter_suites.py` ships none by its own design statement, its job *being* running suites, and
what holds it is the count it prints instead. The plant is per *branch that does real work* rather
than per check: a plant that reddens a check by the wrong route proves
nothing about the branch it was written for. The counts are not written down here; the run prints
its own.

Where the plants run differs, and only the ordering does. The two document checks and the
reply-register check run every plant as a first phase, before the tree is held to anything; the
port contract, the configuration reader and each implementation's own suite run every plant beside
the assertion it belongs to, because each needs a configuration or a surface of its own synthesised
for it and a first phase would build all of them twice. Either way no check is believed until it
has been shown it can fail. So the step names in `.github/workflows/` fall into two families: a run
with a first phase names it — *Assert each check can fail, then …* — and a run without one says only
what it holds. A step name is not evidence that a suite plants: both families plant, and the run
prints what it planted.

The checks that plant the green side as well as the red are the ones whose scope has a hole in it by
design, each hole an exclusion somebody wrote on purpose; each run prints what it planted. Two are
not derivable from a run. The sweep over landed trees plants both directions of **every** arm it has
rather than of the holes alone — a must-remove beside each must-keep — because a sweep that removes
nothing passes a red-side-only suite whole, and the half that would then be untested is the half
that deletes files. And the restoring role's suite inverts the pair: what it plants is a state a
sweep would have **written** into — a store that is not there, a transcript that is not there, a
working file that is missing — and the assertion is that the tree is unchanged afterwards, so there
the green side is the whole rule and the plant proves the snapshot can see a write at all.

**A green plant naming an exclusion is verified by switching that exclusion off** and watching it
redden, while a plant naming an omission has nothing to switch off, and what it asserts is that a
grammar stayed narrow. A suite keeps the two kinds apart in its own labels, since calling an
omission a verified exclusion claims a step that was never performed.

The reply-register check runs its turn-guard assertions against a state directory of its own, so a
second run of the self-test cannot read the first run's markers and report that a blocking finding
does not block.

**A plant has to reach the branch it was written for, and nothing but the mode reports it when it
stops.** The three plants against the outcome column of the rulings document split the document at
the header the check itself derives the table from: an outcome cell's link shape is an ordinary
citation shape, so a plant substituting into the document as a whole is taken by the first such
citation in prose above the table, every cell stays valid, and the checks stop being exercised.

**A plant may not name the file it plants into.** The sweep takes a file from the strict set and
synthesises one if the set is empty, so moving or renaming a carrier root reddens a check rather
than making `--self-test` — the command the workflow runs — die on a `KeyError`.

When a check goes red, the assertion is as likely to be wrong as the document, by the reading rule
[`schema.md § 38 → What a red
says`](../plugins/mjolnir/config/schema.md#what-a-red-says-and-what-stays-in-a-projects-own-script)
states. An anchor rule that collapsed runs of whitespace, where the code host replaces each space
individually, reported six sound citations as broken.

## The documents against the graph, the forbidden list and their own blocks

The two checks above hold *this* repository's prose, and their graph and their forbidden list are
written in the script. The rows, the globs, the entry points, the forbidden names and anything
quoted are a project's configuration ([`schema.md
§ 38`](../plugins/mjolnir/config/schema.md#38-the-documents-a-project-holds-to-a-checkable-property)).
`plugins/mjolnir/scripts/documents.py` is the one implementation that reads them. Two independent
implementations in two other projects argued for it; the
counts behind that are in [`configuration-surface.md`](configuration-surface.md#the-document-checks-two-implementations-and-the-claim-measured-rather-than-taken).

Each check declares which of the three kinds it is, and the run prints the kind beside the verdict:

| Name | Check | Kind |
|---|---|---|
| every governed document has a row | the governed set against the graph in both directions, and every governed file readable | computed |
| a document names only what its row allows | the enforced edge, in the direction a filename appearing is the defect | computed |
| a row names only edges the text carries | the same edge, in the direction nothing else reports | computed |
| every document is reachable from an entry point | a document nothing names and nothing addresses | computed |
| every link resolves | each relative link against the index and each fragment against its target's headings, an address outside the repository never fetched and a target the project exempts skipped | computed |
| no forbidden name appears | each stated pattern over the governed set, a pattern that cannot be evaluated reported rather than read as no match | forbidding |
| a table keeps its shape | every row of a table carrying the same number of cell delimiters, an escaped pipe counted as a cell's own character | computed |
| a table row keeps its table | a run of pipe lines with no delimiter row, which renders as a paragraph | computed |
| no document leaves a fence open | an opening delimiter with no matching close | computed |
| a box diagram keeps its edges | where a project turns it on, every corner, tee and cross in a fenced box-character diagram meeting a line that reaches back, columns counted by display width | computed |
| a quoted sentence is still in its document | the kind that does not work, performed as configured and warned about on every run | quoting |

The quoting kind is admitted and not refused, as that section rules: refusing it would leave a
project already carrying such a check unable to state what holds its documents at all. So it runs,
and every run names both of its failure modes — red on an innocent reword, green when the claim is
reworded into its opposite ([`schema.md § 38 → The three
kinds`](../plugins/mjolnir/config/schema.md#the-three-kinds-of-check-and-the-one-that-is-admitted-with-a-warning)).

Two runs, each answering one question. `Documents carrier` reads a project built for it and answers
about the **carrier**: every arm reddens on its planted violation and every exemption stays green,
which is the answer an adopter whose `documents.carrier` is `none` can still get. `Documents` reads
*this* tree and answers about **these** documents, since most of what this repository ships is
prose and a facet held only through its carrier's suite is a facet nothing has ever run over real
text ([`schema.md
§ 38`](../plugins/mjolnir/config/schema.md#38-the-documents-a-project-holds-to-a-checkable-property)).

### What this check deliberately does not hold

- **A project's own domain checks.** Whether a project's five request shapes each have a home in
  its layout is a computed property of that project's subject matter, and it stays in that
  project's own script. The facet does not even name them: a key pointing at a command that
  answered one would satisfy the boundary's letter and leave the adopting project writing the
  whole working procedure for a name back ([`schema.md § 38 → What a red
  says`](../plugins/mjolnir/config/schema.md#what-a-red-says-and-what-stays-in-a-projects-own-script)).
- **A link to another host.** An address with a scheme is never fetched, so a page that moved on
  someone else's site is not reported: a network read would make the verdict a fact about the day
  the run happened ([`schema.md § 38 → A link
  resolves`](../plugins/mjolnir/config/schema.md#a-link-resolves-to-something-the-repository-holds)).
- **Whether a document is true.** Every check here is structural. A row that is current, an edge
  that resolves and a table that renders say nothing about whether the sentences are right.
- **Where in a document a forbidden name appears.** The forbidding kind reads every line of a
  governed document, fenced lines and shown examples among them, so a project that documents its
  own forbidden name is refused on the sentence that forbids it, as is the implementation this kind
  was read out of. The remedy is the pattern rather than a scope: an entry states an expression, so
  a project in that position narrows it ([`schema.md § 38 → The
  three kinds`](../plugins/mjolnir/config/schema.md#the-three-kinds-of-check-and-the-one-that-is-admitted-with-a-warning)).
- **The `derived_from` edge against the text.** Content that flowed in obliges no citation, so
  that edge is recorded and held acyclic and never compared with any document's words
  ([`schema.md § 38 → The two
  edges`](../plugins/mjolnir/config/schema.md#the-two-edges-and-which-of-them-is-enforced)).
- **Anything about a document the globs do not govern, or the index does not carry.** The set comes
  from `git ls-files`, so a file nobody has added is outside every check here — and a project that
  narrows its globs narrows the check with them, which is visible in its own configuration and
  nowhere else.
- **What a renderer other than the code host's would do.** The block properties were measured
  against one renderer. A different one may break a block this passes, and nothing here reports it.
- **A mention whose meaning depends on which document it is in.** A row states one spelling for the
  document it is about, so a project where one file's name counts only in a particular form inside
  two particular others cannot say that — two edges of one surveyed project, named in
  [`configuration-surface.md`](configuration-surface.md#both-projects-rules-expressed-in-the-facet-and-run-against-their-own-trees)
  with what a key for it would have to carry.
- **The edge of a row that does not state one.** `may_name: null` is an edge this project does not
  enforce, so the two edge checks and reachability say nothing about that document; the run names
  every such row, and where every row carries one it says which three checks hold nothing
  ([`schema.md § 38 → The two
  edges`](../plugins/mjolnir/config/schema.md#the-two-edges-and-which-of-them-is-enforced)).
- **A box diagram's straight runs, an ASCII diagram, or a diagram this project has not turned the
  check on for.** Only a junction is held, so a run that ends early with no corner at its end is
  not reported; a block drawn in `+`, `-` and `|` is not read; and an arm landing on text is read
  as a line drawn to a label, so a box whose corner lands on a letter of its own content passes
  ([`schema.md § 38 → A box
  diagram's edges`](../plugins/mjolnir/config/schema.md#a-box-diagrams-edges-held-where-a-project-turns-the-check-on)).
- **Whether the graph is the right graph.** The rows for this repository were read off the text
  rather than composed, so they assert nothing about the commit that landed them; they assert every
  commit after it — an edge added with no row, and a row whose edge the text dropped, are each a
  failure ([`schema.md § 38 → The two
  edges`](../plugins/mjolnir/config/schema.md#the-two-edges-and-which-of-them-is-enforced)).

## The specification corpus, read at a ref rather than out of the tree

The checks above read the **index** — the files in the tree now. This one reads a ref: which copy of
a project's specification governs an item is the copy on the branch for *that item's version*, a
different set of bytes from the one
any index carries ([`schema.md § 39`](../plugins/mjolnir/config/schema.md#39-the-specification-corpus-and-which-copy-of-it-governs)).
`plugins/mjolnir/scripts/spec_corpus.py` is the one implementation, and the globs, the part read
whole and the grouping the ref is named after are a project's configuration.

One run, not two: `spec_corpus` is `none` on this repository, so there is no corpus here for a
second run to read. What `Spec corpus` holds is each outcome against repositories the suite builds —
a branch per version, a dirty tree on a third branch, and a single-branch clone:
| Name | Check | Kind |
|---|---|---|
| the copy read is the version's own | the ref composed from the grouping's prefix, and the text read at it | computed |
| nothing is checked out | the branch, the head, the porcelain status and a corpus file's uncommitted text, digested before and after the read | computed |
| a version with no branch falls back and says so | the integration branch read instead, and the report naming the ref it actually read | computed |
| a ref the remote has and this clone does not is unread | the third outcome, reported as itself rather than as the fallback | computed |
| a keyword is held to a word boundary | the match that reports a hit inside a longer word | computed |
| a project with no corpus has no subject | the absent case, and the report that says so rather than that nothing contradicts | computed |
| a working role the project does not name reads nothing | the *not asked* answer, worded as neither the absent subject nor a verdict | computed |
| a working role's narrowing only narrows | a document matching the narrowing and not the corpus stays unloaded, and the filing role's read is not narrowed | computed |

Which roles read the corpus and what narrows their read are the project's `while_working` block,
refused at load in every shape that reads as a role or a narrowing while being neither
([`schema.md § 39 → The roles that read it while the work is
done`](../plugins/mjolnir/config/schema.md#the-roles-that-read-it-while-the-work-is-done-and-what-narrows-their-read)).

*No corpus is configured* is the absence of a subject and *no contradiction was found* is a verdict,
so the suite asserts the first and asserts that the second does not appear
([`schema.md § 39 → the absent
case`](../plugins/mjolnir/config/schema.md#carrier-none-and-the-two-answers-it-must-not-collapse-into-one)).

### What this check deliberately does not hold

- **Whether the request contradicts the corpus.** That is a reading of prose and the filing role's
  to make. The carrier answers `None` rather than `False` so that a caller rendering it cannot
  print *none found*
  ([`schema.md § 39 → the absent
case`](../plugins/mjolnir/config/schema.md#carrier-none-and-the-two-answers-it-must-not-collapse-into-one)).
- **Anything about the corpus's content.** Not a section list, not a heading, not a document's
  shape — the first of those is § 38's subject and the rest are nobody's here
  ([`schema.md § 39`](../plugins/mjolnir/config/schema.md#39-the-specification-corpus-and-which-copy-of-it-governs)).
- **Whether the grouping named is the right one.** `kind` is not read, so a `ref_prefix` on a
  time box gets the corpus read at an iteration's branch and nothing refuses it. What rules that
  out is the project's own statement of which grouping carries the corpus
  ([`schema.md § 39 → The ref is the grouping's`](../plugins/mjolnir/config/schema.md#the-ref-is-the-groupings-and-this-facet-declares-none)).
- **A version nobody has fetched.** The read opens objects out of the clone, so the third outcome
  is reported with the one command that would fetch it rather than fetched — a fetch being the
  role's call and not the carrier's.
- **Whether this repository's own corpus is read.** There is none: the facet here is `none`, so
  every arm above runs against a fixture and none of them has ever run over a real project's
  specification — a gap the documents pair above does not have.

## The filing role's two readings, and the reply held to carry both

`plugins/mjolnir/scripts/file_window.py --self-test` runs in the `Filing window` workflow, with no
credential and no network. The rule is the filing role's own, in its duplicate check.

What the suite holds: a reading's count and highest over every identifier shape a tracker answers
with; a failed search kept apart from an absent one; a move seen where the count and the highest
both stand still; a reply refused where either reading is missing, the two are reversed, one is
written twice, or a second item has only its first; and that the role names each of the three
commands, so the carrier cannot go uncalled.

### What it deliberately does not hold

- **That a role ran the check on its reply.** The role is told to and nothing fires it.
- **That a line was printed by a comparison rather than typed.** The check reads the reply's own
  text.
- **That the create followed the second reading immediately.** Nothing sees the gap between them.

## What a deploy's batch command is handed, and what its answer is matched against

`plugins/mjolnir/scripts/batch.py --self-test` runs in the `Batch carrier` workflow, with no
credential and no network. The rule is
[`schema.md § 33`](../plugins/mjolnir/config/schema.md#what-the-batch-command-is-handed-and-what-its-answer-is-matched-against),
and the placements a `batch` may carry are held by the `Config reader` run, which refuses each one
§ 33 does not state.

What the suite holds: an advance handed the items in the role before the one it advances to, and a
precondition handed every item short of its bar rather than those; the identifiers arriving on the
command's input and the target, the commit, the purpose and a choice reaching it where it places
them; both differences of the match named, an unplaceable item included; a tracker with no search
kept apart from a search that failed; a command that failed stopped rather than read as empty; and
that the deploying role names the carrier, so it cannot go uncalled.

### What it deliberately does not hold

- **That the command answers the question § 33 asks it.** Whether an item's code is in what is
  deployed is the project's command; nothing here reads inside it.
- **That the commit handed over is the one the deploy serves.** The carrier holds its shape; which
  commit it is was established by the role's preflight.
- **That the role reported what the carrier printed.** Nothing reads the reply.

## What a deployed item is judged against, and the verdict the carrier is barred from

`plugins/mjolnir/scripts/verify.py --self-test`, mirrored by the `Verify carrier` run that
[`.claude/mjolnir.yaml`](../.claude/mjolnir.yaml) states and
[`.github/workflows/verify-carrier.yml`](../.github/workflows/verify-carrier.yml) defines. The facet
is [`schema.md § 41`](../plugins/mjolnir/config/schema.md#41-what-a-deployed-item-is-judged-against-and-the-readings-a-person-is-handed),
and each arm reddens on a planted violation of its own:
| the arm | the plant it reddens on |
|---|---|
| a target resolves to its own command | a name no `deploy` entry carries, and a target the project deploys to and states no command for — the second reported as *no pass may be taken against it* rather than as a fault |
| the commit a target serves is read by running that command | a command that prints nothing, and one that exits non-zero: each reported **unestablished** and never as a commit that did not change |
| a criterion carries its reading, environment, instrument and date | each of the four dropped on its own, so a record is refused rather than rendered with a blank cell |
| the four buckets are a closed set | a bucket outside them, a criterion with no referent and no owner, and a criterion measured elsewhere stating no reason the target could not be it |
| a criterion with no referent holds the item, and one not measurable until a later target does not | both directions, the second being § 40's deadlock ruling: splitting it would meet a release gate that refuses to carry an unaccepted item |
| **a reading taken before the commit the target serves is refused** | a reading one second before a real commit's own date, against a repository the suite makes — with the green side one second after it and one *at* it |
| a date carries its offset | a stamp written without one, refused rather than read as local |
| a provisioning run reports its checksum pair, and a fixture left behind holds the item | a pair with one half missing, and a non-zero count left |
| **the role is refused the `accepted` write however it asks** | asserted against the tracker port rather than described: as the procedure, the deploy, the automation and the sweep it is refused against the configured writer, and as that writer itself it is refused before the configuration is read at all |

The arithmetic arm runs against a repository the suite makes a commit in, not against a stubbed
stamp reader — the rule it asserts being
[`schema.md § 41 → `identity``](../plugins/mjolnir/config/schema.md#identity-and-the-two-readings-of-a-deployed-commit-that-are-wrong). A fake at that seam would have compared a reading against a value the suite
chose. The fixture sets the committer date, the stamp the module reads; setting only the
**author** date leaves the commit's arrival time at *now*, so every arm would assert against the
clock.

Every green-side call in that suite goes through one helper that turns an unexpected refusal into a
red rather than a raise, this repository's own rule about a planted violation
read against [`schema.md § 38 → Every check carries a violation`](../plugins/mjolnir/config/schema.md#every-check-carries-a-violation-it-reddens-on). An arm has to survive the defect it tests: a refusal raised where
the suite expected an answer would otherwise stop the run at that line and take every arm after it,
reported as one red where the truth is one red and a dozen unrun.

### What this check deliberately does not hold

- **Any project's own readings.** This repository states `verify.carrier: none` — nothing here is
  deployed, so no environment serves a commit — so pointed at this tree the carrier reports the
  absence and exits with no subject. Every arm above runs against a tree of the suite's own making.
- **Whether a reading is *true*.** The carrier holds a record's **shape** and one ordering. Whether
  the instrument named measured what the criterion asks about is the pass's own judgement, and
  nothing here reads it.
- **Whether the comparison was built, or opened.** Both are acts the role performs and neither
  leaves a record this check can read; what the facet holds is the baseline's two inputs being
  stated and durable.
- **Whether the widths a handover named are the project's own.** The carrier hands back the list and
  the role reads it; a handover that named a width outside it would be caught by nothing here.
- **Whether a person actually judged anything.** The record carries a standing and says whose the
  move is. The status itself is `orderer`'s, and no run here can establish that somebody looked —
  the same limit the merge guard's own record carries one role over.
