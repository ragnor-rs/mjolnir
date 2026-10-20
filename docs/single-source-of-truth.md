# How the single-authority claim is held

[`../plugins/mjolnir/config/schema.md`](../plugins/mjolnir/config/schema.md) declares itself the
single statement of every rule and flow, and this document and its sibling explain or record
without being a second authority. This document states none of the rules either. It records what
the gate checks, which kind of check each one is, and — the part worth reading — what it
deliberately does not check.

The check is `tools/check_single_source.py`, run by the `Single source of truth` workflow on every
pull request and every push to the default branch, and stated in this repository's own
`host.checks`. ⚠️ Every workflow here is named for the one claim it holds, and each carries a
single job of the same name, so the name `host.checks` is keyed by and the name the host reports
as a status context are the same string — there is no key to get wrong. It was not always so: this
workflow was called `Checks`, which both differed from its job name and read as an umbrella over
the workflows beside it.

A second script, `tools/check_no_project_names.py`, holds a different claim — that this repository
names no other project, and that nothing carrying procedure carries a value. It runs in its own
`Names no other project` workflow, and is stated in `host.checks` as its own entry: a
`host.checks` entry states one mirrored command, so folding it into a sibling would have been a
second command with nowhere on the surface to live. It is recorded in
[its own section](#the-second-sweep-naming-no-other-project) below, because the two claims share
this document's discipline of stating every limit and not its subject.

`tools/check_nothing_deferred.py` holds a claim about the change rather than about the tree: that
nothing in it was deferred. It runs in its own `Nothing deferred` workflow and has its own
`host.checks` entry, for the same reason the sweep does, and is recorded in
[its own section](#the-gate-on-the-change-nothing-is-deferred) below. It is the one that reaches
off the tree, and the one granted a token scope — stated there rather than discovered in a
workflow file.

`tools/check_prose_width.py` holds the documents to a shape rather than to a claim about their
content: the line width this project's configuration states. It has its own `Prose width`
workflow and its own `host.checks` entry, and is recorded in
[its own section](#prose-line-width-held-on-the-gate-for-files-and-nowhere-for-bodies) below —
where the half of its rule that no check reaches is stated with it.

`tools/check_no_audit_trail.py` holds a claim about the prose a change writes rather than about
the tree it writes it into: that no artifact carries a record of the pass that wrote it. It has its
own `No audit trail` workflow and its own `host.checks` entry, and is recorded in
[its own section](#an-artifact-states-what-is-true-now-held-on-the-lines-a-change-adds) below. Its
scope is a **diff** rather than a tree — the rule's own carve-out leaves the past alone — which it
shares with the gate above, as it shares having no `push` arm.

`tools/check_prose_register.py` holds three properties of the prose a change writes into a file,
under whichever register the project nominates for it. It has its own `Prose register` workflow and
its own `host.checks` entry, and is recorded in
[its own section](#the-floor-under-file-prose-held-on-the-lines-a-change-adds) below. ⚠️ It is the
one that stands up nothing of its own: the diff and the merge base come from the check above it and
the word lists from the one below, so what is written in it is the grammar neither of them has.

`plugins/mjolnir/scripts/check_reply_register.py` holds the register of a role's reply, and it is
the one here that does not run on the gate at all. It is in
[its own section](#the-replys-register-held-in-the-session-not-on-the-gate) too, and for the same
reason: whatever holds a claim here states what it leaves alone. ⚠️ No count of these scripts is
written down, here or anywhere — a count in prose is a copy, and three open changes were each
adding themselves to this document as "the third" when it was.

## Why this is a check rather than a convention

Every other duplication in this backlog is one the toolkit exists to delete. This one is the
toolkit's own. The procedure is described in the schema, in the README, in the documents
under `docs/`, in each shipped skill, and in the issue bodies — and only the schema is an
authority. Nothing held the rest to that. A rule restated in a document, a section nothing
motivates, a ruling pointing at a home its outcome has since left: each reads as fine in review,
and each is the defect this repository was built to call a defect.

Three were in the tree when the check was written, which is the argument for it:

- `version` was in every configuration and declared nowhere in the schema — a key every
  adopter writes, that the single statement of the surface did not name. Declaring it is what
  exposed it: read by nothing and never moved, it is now **retired** at
  [schema § The file itself](../plugins/mjolnir/config/schema.md#the-file-itself), which is the
  check finding a key the surface should never have had to declare rather than one it had
  forgotten to.
- One ruling's outcome lived in the README, which stated that rule citing no schema section, so
  the README was a second authority for exactly one rule. It is now
  [schema § 7 → Invocation](../plugins/mjolnir/config/schema.md#invocation), which the README
  cites. It sits as a subsection of the carrier axis rather than as a numbered section of its
  own, because every numbered section is a configuration facet opening with a `yaml` block and
  this is procedure — the same placement the authorship rule has under § 6.
- Two rulings pointed at "the filing role's work item" and "the deploy role's work item" with no
  number, so nothing could resolve whether the outcome had moved. They now name #7 and #13.

## The three kinds, and why one of them is absent

[Work item #28](https://github.com/ragnor-rs/mjolnir/issues/28) classifies the checks themselves,
from two independent implementations that reached the same conclusion: **computed** checks derive
the property and cannot be fooled by a reword; **forbidding** checks assert a name or pattern must
not appear, and are sound when the thing forbidden is stable; **quoting** a sentence back at the
file it came from fails in both directions. Every check below is one of the first two.

| # | Check | Scope | Kind |
|---|---|---|---|
| 0 | Every markdown document that may cite the schema has a declared role in the script | root `*.md`, `docs/**`, `plugins/**` | forbidding |
| 1 | Every citation of the schema resolves — **both its path and its fragment** | every document with a role | computed |
| 2 | Every schema heading below the title is cited by at least one document | every level the schema uses, container sections excepted | computed |
| 3 | Every ruling's outcome cell resolves, and the section it names — by number or by heading — agrees with its link | the `Outcome lives in` column | computed |
| 4 | A ⛔ statement carries a citation naming a **section** | documents that explain or record | forbidding |
| 5 | Every configuration's top-level key set equals the one the schema declares | top level only | computed |
| 6 | No citation names a **container** — a section whose whole content is in its subsections | every citation, in every document with a role | computed |
| 7 | The footprint report covers every file the checks walk | the report's own coverage | computed |

Check 2 is the one that does the most work, because it runs in the direction nobody remembers to
check by hand: a section added to the schema with nothing recording why it has that shape fails
the build at the moment it is added, rather than being noticed a year later by someone wondering
whether it is load-bearing. ⚠️ **It used to hold `##` sections only**, so a `###` subsection that
no document motivated passed — two did, **each carrying a ⛔ rule of its own**, and the direction
was enforced one level less deeply than it read. It now holds **every level the schema
uses**: the depth is read from the headings rather than written down, so a `####` added tomorrow
is held the day it exists. No number of them is given here on purpose: a count is a fact about the
schema, and a copy of it in this document would go stale on the next subsection either way, green.

⚠️ **The one exemption is a container**, and it is what checks 2 and 6 share. A `##` section whose
whole content lives in its subsections states nothing of its own — § 4 is the live instance — so
there is no rule there for a document to motivate, and check 2 reads it through its subsections,
each of which is held in its own right. Check 6 is the other face of the same fact: a citation of
such a section resolves to a heading and a list, which is why it is a problem rather than a
preference. That was check 6's one finding against the tree it was written for: a sentence naming
the four facets cited the section holding them, and now cites the four. ⚠️ The exemption
is planted on the **green** side and was verified by disabling it, because a carve-out nothing can
fail is a carve-out nobody checked.

Check 4 is scoped to documents that explain or record, not to a skill. That is the schema's own
[boundary rule](../plugins/mjolnir/config/schema.md#the-configuration-surface): a fact that cannot
be expressed on the surface is either procedure, in which case it belongs in a skill, or a
project-specific skill. A skill therefore states procedure for its own role legitimately, and the
hazard there is a *value* rather than a rule —
[#19](https://github.com/ragnor-rs/mjolnir/issues/19)'s sweep. Its citations are still held by
check 1: a skill already carries one, and a dead citation in a skill is a dead citation.

Check 3 permits a third, partial home. A ruling whose outcome is split between the surface and the
skill that carries it may name `the skill` **alongside** a section — ruling 6 does — but never
instead of one. That carve-out is in the script, so it is stated here too.

⚠️ **Check 3 recognised a numbered home only until a ruling needed an unnumbered one**, and this
is the divergence that paragraph was recorded in advance of. The limit was real: the cell's form
was `[schema § N](…#a)` with the number and the anchor required to agree, so a procedure rule
sitting under an unnumbered `##` section could not be named as an outcome at all.

**The remedy was the grammar rather than the predicted workaround.** What was recorded here was that
such a ruling would have to name its work item instead — and that would have been false of the
thing it described: naming a work item says the outcome has *not* moved into the surface yet, while
this one had. So the cell now reads `[schema § <N or heading>](…#a)`, and where the section is
named rather than numbered the heading's own title is what ties the cell to it, there being no
number to cross-check. ⚠️ **That is a change of grammar**, which is the one residue this script is
allowed to carry — and it is held the same way the rest is: a named section whose link points at a
different heading is a planted violation the build reddens on.

**What that admits, stated rather than left to be inferred from the regex.** A cell names a
section and links an anchor *within* it, and the anchor resolves through the section it sits
under — so a `###` subsection is nameable by its enclosing section either way, numbered or not,
which is what the case recorded above needed and what ruling 11 already relies on. `4.1` and the
`N → Subsection` form the documents use in prose resolve on their leading ordinal. ⛔ **What is
still refused is naming a `###` subsection as though it were the section**: the cell names the
home and the link names the place in it, and the refusal says which of the two disagrees.

## What the run reports rather than holds

Two things are printed with no verdict attached, and the argument for both is the same: **a
citation costs the whole document it points into**. A role settling one sentence against the
schema pays for every line of it, and a reader following a citation to a rule that lives in one
subsection reads the others on the way. That cost is real, it moves with every change, and
nothing was reporting it.

- **A per-file footprint** — lines, characters and ⛔/⚠️ markers, for every file the checks
  already walk. A role that doubles in size is then visible in the diff of a build log rather
  than noticed when a window runs short. Check 7 is what stops the report shrinking in silence:
  a file the checks read and the footprint skips is a cost reported by nothing. ⚠️ The marker
  count is of the emoji form anywhere in the file, code spans included, and the advisory marker
  **without** its variation selector is not counted — which is what keeps the tree's one bare
  instance, a script's output quoted inside a code span, out of a count of directives.
- **A count of coarse citations** — every citation naming a section that states something itself
  *and* has subsections, grouped by section with the documents that cite it. Check 6 holds the
  decidable end of this and nothing holds the rest.

⛔ **Neither carries a threshold, and that is not an omission** — it is the local half of
[`schema § 11`](../plugins/mjolnir/config/schema.md#11-session-context), whose own statement that
the window degrades before it fills is given with no number for the same reason. A budget is a
judgement, and a judgement hardcoded in a check is the copy-that-must-be-kept-in-sync the section
below rules out. It is also unenforceable at run time: the harness exposes context utilization to
no hook but `SessionStart` on a resume. So the run measures, prints, and reddens on nothing it
cannot derive.

### What the granularity check deliberately does not hold

**Which subsection states the fact.** That is the *quoting* kind — matching a document's sentence
against the prose it came from, red on an innocent reword and green on a reword into the opposite
— and this document rules it out for the same reason everywhere else. So the verdict is confined
to the one case needing no reading at all: a section with no text of its own cannot be where any
fact is. ⚠️ **And that verdict reaches `##` sections only**, which is the shape the check's own
reading of the outline is defined over: a cited `###` whose whole content is in `####` subsections
resolves to a heading and a list exactly as a `##` container does, and passes. The surface carries
no such subsection today, so the limit is latent rather than live — stated here because a latent
limit found later in a green run reads as coverage. ⚠️ **Every other coarse citation is counted and
left standing**, and the count is not
small; the alternative measured against it was reddening on all of them, which makes a legitimate
section-wide citation unwritable and asks for a hand pass whose result the gate could not check
either. Repointing one is a reader's judgement, which is the same place fidelity already sits.

## The check must not become one more copy of the principles

⛔ A check that hardcoded the loop's role count, the list of axes, or which facets have an absent
case would have to be edited on every change to the surface whose
[single-authority claim](../plugins/mjolnir/config/schema.md#the-configuration-surface) it
enforces — this repository's own thesis violated in its own gate, and a copy that has to be kept
in sync is the defect rather than the maintenance burden.

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
one changes nothing either — the rulings table is found by its column header rather than by a
section number, which was a deliberate second pass: the first draft keyed on the literal heading
`## 4. The rulings`, so inserting any section above it would have broken the check on a content
change.

**The only thing that forces an edit is a change of grammar** — a new marker, a new citation
form, a new column name, a new kind of document — and that residue is made loud rather than
silent by check 0: a markdown document at the root, under `docs/`, or under `plugins/` with no
declared role fails the build instead of being quietly skipped.

This is [#28](https://github.com/ragnor-rs/mjolnir/issues/28)'s own finding applied here — the
sixth instance counted in
[`configuration-surface.md`](configuration-surface.md#the-strongest-argument-for-extraction-is-not-borrowed)
is another project's document checker, and this guard is a seventh: the graph a machine walks and
the statement a person maintains are deliberately one thing, read from one place.

## What it deliberately does not check

Stated, because an unstated limit reads later as coverage.

- **Fidelity.** Whether a document's paraphrase still matches the section it cites is the
  *quoting* kind: red on an innocent reword, green when a claim is reworded into its opposite.
  No check here attempts it. It stays a reviewer's job, which is why a document paraphrases as
  little as it can and cites instead.
- **A document's audience and register, and a role value the document gives nothing to hold.**
  Check 0 gives every document a *role* — explains, records or carries procedure — and a role bounds
  what a document may **state**, never who it is written for or in what register. Two audiences
  interleaved in one file is invisible here, and so is a document in no settled register. The front
  page's own reader is stated in
  [README § Who this page is written for](../README.md#who-this-page-is-written-for), as a
  convention of this repository rather than a rule of the procedure, and held by nobody; nothing
  configures it either, the README not being one of the artifacts
  [schema § 8](../plugins/mjolnir/config/schema.md#8-language-register-audience--per-artifact-not-per-project)'s
  map names. Whether the procedure should state that boundary in general is
  [#65](https://github.com/ragnor-rs/mjolnir/issues/65)'s. ⚠️ What a file's prose **is** held to,
  whichever register a project nominates over it, is
  [§ The floor under file prose](#the-floor-under-file-prose-held-on-the-lines-a-change-adds) — and
  a floor is not a register, so nothing there closes this gap either.
  ⚠️ **Measured on `docs/working-on-the-toolkit.md`:** setting its role to `procedure` leaves every
  check green, because the checks that discriminate on a role read a binding statement or a citation
  of the surface and that document carries neither — so the value is held only where the document
  gives it something to hold, and the entry itself is held by check 0 either way.
- **Issue state.** Check 3 resolves the *form* of a work-item cell, not whether that issue is
  still open. Reading the tracker needs a token scope, and per
  [#50](https://github.com/ragnor-rs/mjolnir/issues/50) this workflow is granted none: its
  `permissions` are empty and the checkout is told to persist no credential. So a ruling whose
  work item landed without its outcome moving into the schema is caught by a reader, not by the
  gate — the one gap in check 3 worth knowing about, and a deliberate trade against holding a
  credential to close it.
- **A binding marker that does not open a line.** Check 4 reads a statement as one that **opens** a
  line, optionally as a list item, which is the grammar the script states: mid-sentence the marker
  is prose *about* a rule rather than a statement of one. ⚠️ So a rule written mid-line in a
  document that may not state one passes — measured when the record first acquired markers of that
  shape and this gate stayed green; they were removed rather than cited. ⚠️ **Measured in the other
  direction too**: a marker-anywhere grammar reddens on every sentence that merely *mentions* the
  marker, which is the *quoting* failure, and it is what makes the line-start form the sound one. A
  table cell is not part of that argument — the check excludes cells by a separate condition the
  grammar does not reach — so the residue here is a reviewer's.
- **A link between two carriers, and a link from the reader.** Check 1 resolves a citation of the
  surface, which is what its pattern matches. A relative link from one skill to another, and a row
  in the README pointing at a carrier directory, resolve against nothing — so renaming a carrier
  and updating this script's role map leaves every such link dead and the build green. ⚠️ Measured
  by doing exactly that: the one path that fails loudly is the role map itself, and the rest fail
  in silence.
- **Whatever is not committed.** Every check here reads the working tree, which is not what a
  commit takes. ⚠️ Measured on the change that added this bullet: edits staged by a merge were
  verified green, then edited again and left out of the commit, so the gate's verdict was about a
  tree that never landed. The host's own run closes it afterwards; nothing here closes it before.
- **Key subtrees.** Check 5 holds the top level only, so a key inside a block is this check's blind
  spot whether or not the surface declares it — and `tracker.labels`, which it does not, is the known
  consequence. The reason is still a per-tracker block: a deeper comparison needs one exception per
  tracker kind, and **more of them since** the schema's own
  [§ 3](../plugins/mjolnir/config/schema.md#what-each-kinds-block-carries) began stating each kind's
  keys — every configuration now lacks every other kind's block by design. A bounded check that is
  sound still beats a deep one that needs carve-outs. ⚠️ What changed is only what the *surface*
  states: the reader refuses a block that omits a key its own kind requires, per kind and at
  configuration time, which is a different question from this check's key-set comparison and
  answers nothing about an undeclared key.
- **Issues and pull requests.** Not from *this* workflow, which holds no credential — reading
  that store needs a token scope, and per [#50](https://github.com/ragnor-rs/mjolnir/issues/50)
  this one is granted none. ⚠️ It is not unreachable in principle, and this document used to say
  it was: the gate on the change below does read it, with a scope of its own. What stays true
  here is the trade, not the impossibility. The lettering of projects A–F in the documentation
  rests on the same reason [#19](https://github.com/ragnor-rs/mjolnir/issues/19) records.
- **Configurations outside the globs.** A configuration added where `CONFIG_GLOBS` does not look
  is skipped. Check 0's loud-residue argument covers documents; for configurations the guard
  asserts only that each glob matched something, which catches a moved directory but not a new
  one somewhere else.

## The second sweep: naming no other project

The convention in the README — that this repository names no *other* project — and the surface's
own rule that [no value appears under a carrier
root](../plugins/mjolnir/config/schema.md#the-configuration-surface) both say the **search is the
check** rather than a reading of the procedure. `tools/check_no_project_names.py` is that search,
in its own workflow. **Seven of its nine checks are of the *forbidding* kind**, so most of the
script stands or falls on whether the thing forbidden has a stable form; the two computed ones
exist to stop the other seven holding nothing.

Two scopes. The repository-wide one looks for what identifies someone else's project; the strict
one — the carrier roots, never the whole tree — looks for a value, a tracker or a stack in text
that is supposed to be procedure. A carrier is a skill, a command or a hook (schema § 7), so the
strict set is matched by *shape* — `plugins/*/skills/`, `commands/`, `.claude/hooks/` and so on —
rather than from a hand-kept list of roots.

| # | Check | Scope | Kind |
|---|---|---|---|
| 0 | No repository but this one's is named, as a URL, an install-command argument or a `repo:` value | every tracked text file | forbidding |
| 1 | No path under a home directory | same | forbidding |
| 2 | No address | same | forbidding |
| 3 | No identifier that resolves on a tracker — a Jira key or Trello id **written as a value**, or either service's URL anywhere | same | forbidding |
| 4 | The strict set matched a file at all | the carrier roots | computed |
| 5 | Every file under a plugin is a carrier, a configuration or a manifest — nothing else | `plugins/**` | computed |
| 6 | No tracker is named, in the slug spelling or the prose one | the strict set | forbidding |
| 7 | No package manager, task runner, build tool, checker, manifest or lockfile; no directory change prefixing a command, no directory flag, no absolute path | the strict set | forbidding |
| 8 | No value any configuration supplies | the strict set | forbidding |

Check 5 is the one that makes the shape-matched strict set safe: a carrier in a directory the
shapes do not reach — `plugins/other/skils/`, one letter out — would otherwise be swept by nothing
*and* reported by nothing. It runs in the other direction and makes that residue loud, which is
check 0's argument one scope over.

**Two rules are what make a forbidding sweep sound**, and they are the part worth reading:

1. **A stack token counts only as code, never as prose.** In markdown that means inside a code
   span or a fenced block; in a script it means outside the comments. `make`, `go`, `task`,
   `just`, `stack`, `bundle`, `mix` and `pod` are ordinary English words in a sentence and
   unambiguous commands in a code span, and a shebang names an absolute path by construction. A
   sweep of prose for any of them would redden on a reworded sentence, which is the *quoting*
   failure this document already rules out. ⚠️ Fenced blocks are found by a line toggle rather
   than a paired regex: one trailing space after a fence's language tag is enough to make a paired
   regex match one block's closer against the next block's opener, which hides every command and
   sweeps the prose between them instead.
2. **A value counts only as a whole code span or a whole quoted string.** A value written as a
   value stands alone in its span, so a sentence that merely contains the word is not one: a
   status vocabulary of `open` and `closed` does not forbid the word "opening", which the day-log
   skill uses freely. ⚠️ The wrap is not part of the value — this repository hard-wraps its prose
   at about 95 columns and most forbidden values are multi-word, so newlines are normalised away
   before matching. A fenced block's own backticks are removed first, for the same reason as
   rule 1: they would shift the pairing of every span after them. ⚠️ **A ``…`` span is removed on
   the same ground and by the same means** — split on, never paired, since a paired form matches
   one span's closer against the next span's opener and takes every value between them out of the
   sweep. What is inside such a span is read as well as collected, because this repository's own
   idiom for showing a literal span is a ``…`` around one. ⛔ Both are markdown constructs and the
   removal is scoped to markdown: in a script the halves of two unrelated `` ``` `` literals pair
   with each other across hundreds of lines, and taking that region out blinded the sweep over 722
   lines of one module with a planted tracker key inside it going unreported.

It derives what it can, for the reason stated above about the check not becoming one more copy:

| Derived, at run time | Hardcoded |
|---|---|
| the one permitted slug, from `host.repo` in this project's own configuration | the host-URL, address and tracker-identifier grammars |
| the tracker names, from the `kind` alternatives of the surface's **tracker block** and every configuration's declared kind | the closed list of stack tool names |
| the forbidden value set, from **every scalar the configurations state** — this project's own included — minus the vocabulary the surface publishes | nothing: no list of key names is kept here, and none is kept in step |
| the file list, from `git ls-files`; the strict set, from the carrier shapes | a carrier directory's name, and the code-span and quoted-string forms of rules 1 and 2 |
| the file to plant a violation into, from the strict set | the three exceptions below |

⚠️ The tracker names are read from the `tracker:` block specifically. A line-anchored read of
every `kind:` cannot tell `host.kind: github` from `tracker.kind`, and the first draft subtracted
the host's name afterwards — an undeclared carve-out of *content* in a script that is supposed to
hardcode form, and one that silently let the host's own name through a carrier root.

Reading the forbidden values out of the configurations is what makes the acceptance item's pair
work in opposite directions: **a new example configuration adds to what is forbidden under a
carrier root instead of tripping anything, and a status word added to a skill reddens the build.**
Both were measured rather than reasoned about.

### The line: a vocabulary the surface publishes, against one a project invents

Every scalar a configuration states is read, whatever key it sits under, and the subtraction is
what the surface **publishes**:

- a closed alternation, `kind: worktree | in_place`, in either shape the surface writes one — as
  the value, or as a comment beside a value;
- a value marked `# default`;
- a closed vocabulary stated as a list, § 9's `streams` being the live instance, where the
  configuration's own list is a **subset** of it.

⛔ **Published is narrower than written.** The surface *illustrates* some keys with a concrete
value — `label_prefix: "type:"`, `type_branch_prefix: { bug: bugfix }` — and a project writing the
same string has still invented it, so an illustration subtracts nothing. What tells the two apart
is the marker, per
[schema § The file itself](../plugins/mjolnir/config/schema.md#the-file-itself): the alternations
and the marked defaults are read through the surface's own reader rather than parsed a second time
here, so a marker's grammar has one implementation and a facet added to the surface changes what
this sweep forbids with no edit to the sweep.

⚠️ **A keyed-on-key-names reading cannot express that line, and the two values it misses are a
measurement.** Planted one at a time into a carrier file as a code span, against a list of
twenty-two singular key names: `closed`, a workflow name and an artifact directory each reddened,
while **a configured branch prefix and a configured label both passed**. Those two are the two the
project invented, and neither is reachable by a key name — the prefix sits under
`work_item.type_branch_prefix.<one of the project's own types>`, a key the project itself writes,
and the label sits in `tracker.labels`, a plural whose singular `label` is a readiness check's
argument, a different fact one letter away. ⛔ **And the branch prefix is read by the starting
role**, whose text is the one place that value must not appear, since reading it from
configuration is what that role is for.

The alternations must stay nameable for a reason of the same kind: § 6's dirty-tree derivation and
§ 10's routing table are both stated *by mode*, so a role forbidden from saying `worktree` could
not name § 10 at all. ⚠️ Each of those two subtractions carries a plant in the **green**
direction, verified by emptying the published set and watching both redden — an exemption nothing
can fail is an exemption nobody checked.

⚠️ **A published alternation's members are single tokens**, that being the reader's own grammar,
so a multi-word value cannot be published at all and stays forbidden wherever a project
configures it. Measured by planting a facet on the surface in both spellings: the single-token
member is subtracted and the two-word one is not, with no edit to the sweep in either direction.

What stops the derived set shrinking to nothing is three reported arms rather than an assertion
that each key is still in use, there being no key list left to go stale: a surface whose published
vocabulary cannot be read, a configuration that does not parse, and a configuration that states no
concrete value at all. Each is one of the planted violations, and the first of them is what proves
the subtraction is read from the surface rather than copied into the script.

### Three exceptions, encoded rather than assumed

A literal reading of the convention would forbid all three, so each is in the script:

- **`config/examples/`** is whole example configurations and is data rather than procedure. It is
  the one place a concrete status word or label prefix is written down — the surface's own
  [boundary](../plugins/mjolnir/config/schema.md#the-configuration-surface) — and it is where the
  sweep reads the forbidden set *from*. The strict set asserts that nothing under a carrier root
  carries a value regardless. ⚠️ This is also the **only** place a bare all-caps value counts as a
  placeholder: `OWNER/REPO` and `KEY` are stand-ins, but a configuration that is somebody's actual
  facts has no such licence, so `TODO` and `IN_PROGRESS` there are values. The first draft applied
  the all-caps rule everywhere and so dropped the commonest status spellings — and every uppercase
  project key — out of the forbidden set entirely.
- **This repository's own slug**, derived rather than listed. Removing `host.repo` from the
  configuration reddens the build rather than quietly permitting every slug, which is one of the
  planted violations.
- **The public artifacts cited as evidence.** Each is an artifact rather than a project in
  scope, and each sits in a table in the script with its reason beside it, so **an entry means
  editing that table and saying why** — which is what the second one did: the published
  context-engineering practice
  [`§ 11`](../plugins/mjolnir/config/schema.md#11-session-context)'s measurements are drawn from
  is cited by repository URL, and a measurement whose source is not citable is not a measurement.
  ⚠️ **Each entry names the roots it is permitted in**, because a slug permitted everywhere is a
  hole the size of the tree: measured before the scope was added, a cited slug passed in a skill
  and as a `repo:` value in two configurations. Emptying the table, or moving a citation outside
  the roots its entry names, reddens the build — measured in both directions, so the carve-out is
  known to be load-bearing rather than decorative.

`docs/` is deliberately outside the strict set: it quotes the measurements the surface was derived
from and has to keep naming the build tool that reported a cached pass as work done. A rule that
forbade a tool name in a measurement would forbid the evidence.

⚠️ **The script exempts itself — that one file, not all of `tools/`.** It necessarily writes down
every token it forbids: its grammars spell out the home-directory prefixes and its planted
violations contain addresses and foreign slugs. Its sibling needs no such licence and is swept
like any other file, which matters because `tools/` is where
[#15](https://github.com/ragnor-rs/mjolnir/issues/15)'s extracted evidence script and
[#50](https://github.com/ragnor-rs/mjolnir/issues/50)'s linters land — and somebody's own home
path, hardcoded as a default in one of those, is exactly what check 1 exists for. The first draft
exempted the whole directory and so would have read straight past it.

### What this sweep deliberately does not check

- **A bare slug in prose.** `owner/repo` and `docs/single-source-of-truth.md` have the same shape,
  so the sound forms are the URL, the install-command argument and the `repo:` value. A workflow's
  `uses: actions/checkout@v4` is a third shape it does not read, and a slug written bare in a
  sentence is a reviewer's catch.
- **A person's name, a bare label, a milestone title, an assignee handle, a service name.** None
  has a stable form, and forbidding a list of them would be a list to keep in sync. This is the
  same reason projects are lettered A–F in the documentation: the convention is held by what the
  documents *don't* contain, and the counts carry the argument instead.
- **A language interpreter.** `python3` is on no list, and the strict set carries live instances
  of one: a configured script run under it in the day-log skill, and the hook carrier that calls
  the reply-register check. ⚠️ Whether a configured script is a path the procedure prefixes with
  an interpreter, or a command the procedure merely runs, is
  [#65](https://github.com/ragnor-rs/mjolnir/issues/65)'s and
  [#66](https://github.com/ragnor-rs/mjolnir/issues/66)'s ruling about what configuration carries.
  This check does not pre-empt it by reddening, so until that lands an interpreter named in a
  carrier is a known hole — stated, because an unstated limit reads later as coverage.
- **A stack token hidden in a script's comment.** Rule 1 strips comments before sweeping a
  script, so `# run npm run build first` in a hook is not read. That is the deliberate trade: a
  comment is prose, and sweeping it would redden on an ordinary English sentence. A command the
  procedure actually runs is not in a comment.
- **A directory change, a directory flag or an absolute path written in prose.** Rule 1's
  code-only scope is stated above for stack tokens, and the other three arms of the same check
  inherit it — they read `code()` regions too. ⚠️ Measured: an absolute path in a sentence is not
  read at all. The trade is rule 1's, for the same reason, and the live instance it allowed was a
  shipped role citing this project's own backlog by URL, caught by a reader.
- **This project's own slug, anywhere at all.** The second exception derives it rather than listing
  it, and — unlike the third, which names the roots each cited artifact is permitted in — it is
  scoped to nothing. ⚠️ So a carrier may name this repository's host, backlog and item numbers
  while the sweep stays green, which the README's own convention does not permit: it enumerates
  where the own slug may be cited, and a shipped carrier is not among them. Measured, and the
  reason that role now cites no item at all.
- **A bare all-caps value inside an example configuration**, per the first exception above. The
  residue is narrow — an example whose status words are upper-case — and the alternative was
  dropping `OWNER/REPO` and `KEY` out of the placeholder set.
- **A project value spelled like something the surface publishes.** The subtraction is by the
  value and not by the key it sits under, so a project that names a status `merged`, or a label
  `field`, may have a role say it. The narrower reading — subtract a published value only under
  the key that publishes it — is not available: the surface shows several keys in fences that
  open at an indent, so `statuses[].writer` and a bare `writer:` are one statement read at two
  paths, and keying the subtraction to the path reddens `procedure` three times across two
  shipped carriers. ⚠️ Measured in both shapes before the looser rule was the stated one.
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
  reaching further: a label named in a sentence rather than in a span is not read. ⚠️ Which the
  wider set makes load-bearing rather than theoretical — `decision` is one of this project's own
  labels and an ordinary English word the shipped roles use a dozen times over, and the sweep is
  green on every one of them.
- **A build tool a project actually named a carrier after.** The fourth exception, and the
  narrowest: a carrier-classification map is keyed by the basenames projects used, so a key naming
  a build tool is a fact the map must carry — dropping it makes the role it classifies read as a
  role that does not exist. ⛔ **The key is exempt and not the file and not the value beside it**,
  both measured, and the exemption is asserted to stay green while disabling it reddens.
- **Most carrier roots are empty, and the run still exits 0.** The shapes that match a file today
  are the skills root and — since the reply-register hook — the hooks root; the hooks that enforce
  the *loop* are still [#16](https://github.com/ragnor-rs/mjolnir/issues/16), and the command
  carrier belongs to whichever project migrates with one. ⚠️ No number is given here, for the
  reason the plant counts are not: the run prints its own, and a count in prose goes stale green.
  The run says how many shapes swept nothing and **does not**
  fail on them, because a shape for a carrier kind this repository has not adopted is not a
  defect. What is held instead: check 4 fails if the strict set empties altogether, and check 5
  fails on a carrier sitting outside every shape.
- **Issues and pull requests**, for the same reason check 3 above cannot read issue state: that
  store is not a file, the workflow holds no credential, and a reviewer covers it.

## The gate on the change: nothing is deferred

The surface rules that a work item is delivered whole — a role that cannot answer a question asks
rather than noting it, and no change merges with an open item against it:
[schema § *Nothing is deferred*](../plugins/mjolnir/config/schema.md#nothing-is-deferred). One
sentence of that rule is the whole reason a script exists for it rather than a convention: the
completeness statement is **read back, never asserted**. A pull request that says in prose that
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

⚠️ **Check 1 is *forbidding*, not computed, and the distinction is the one this document draws
above.** The heading `Open items` and the answer `None.` are a grammar the gate publishes, so the
check reddens on a reword — `Open questions` is not that heading and `Nothing outstanding.` is not
that answer. That is sound only while the forbidden thing is stable, which a grammar the gate
itself fixes is; it is not a *quoting* check, because nothing here is compared against the text it
came from. Making both strings configuration, in the repository's own language, is
[#51](https://github.com/ragnor-rs/mjolnir/issues/51)'s, and this script is the implementation
that item would call rather than a second one.

**The grammar check 1 enforces, in full**, because the refusal names the items and not the shape:
an ATX heading whose text is `Open items` at any level, appearing **once**; the section running to
the next heading of any level; and, inside it, nothing but the answer — `None.` or `None`, in any
case, optionally as a list item or emphasised. Blank lines, horizontal rules and single-line HTML
comments are not content. Anything else in that section is an open item and is named as one.

⛔ **Check 5 reads prose, and it exists because the escape it closes was measured after checks 0 to
4 were all green.** What it holds is the same section's statement that the rule binds every
artifact a role produces, a file the change adds a line to among them
([§ *Nothing is deferred*](../plugins/mjolnir/config/schema.md#nothing-is-deferred)). A change whose
`Open items` section read exactly `None.`, with no unresolved thread and no marker, shipped a
deferral as a clause in a document in this repository — a carrier named for a check, with no item
owning it. The body, the threads and the markers are the three
places a writer defers *knowingly*; prose is where it reads as diligence.

⚠️ **What it reads is the unowned half and not the unfinished half**, and the line was drawn by
counting: the three commonest ways this repository states a limit honestly appear across nine lines
of tracked text, so an arm sweeping those hands a change back for the candid form of a sentence.
What reddens instead is a line that names no owner for a cure. ⚠️ **The forms themselves are not
written down here**, for the reason the register's densities are not either — a copy in prose has
to be kept in sync, the run prints what it found, and this arm would in any case redden on its own
list. The remedy for a hit is usually **deletion** rather than filing: a cure nobody measured is
not a measured gap. ⛔ **And the green side is asserted rather than assumed** — the whole-change
fixture carries three honest limit lines, taken from lines this repository already ships, and
widening the arm to the unfinished half reddens that fixture.

Check 2 is what a reviewer cannot be, and ⚠️ it follows the cursor rather than reading a first
page, because a review that ran long is exactly the change this gate is for. Check 1 is the one
that reddens the shape the rule was written against: a body that lists what it knows is unfinished
under a heading reading as diligence — the measured case — carries no statement at all, and the
absence is what fails.

⛔ **This gate holds a token scope, and that is a departure from its siblings** rather than an
oversight in one workflow file. They read files in the tree and reach nothing; this one reads a
resolution the host records and an author cannot describe, and the surface's own rule that a
finding goes where its resolution can be read back
([§ *Nothing is deferred*](../plugins/mjolnir/config/schema.md#nothing-is-deferred)) is only worth
stating if something reads it. The scope is `pull-requests: read`, the narrowest the host offers;
nothing writes; the checkout still persists no credential, and the token is handed to the one step
that needs it rather than left in the git config.

⚠️ **What that scope did not buy, measured rather than assumed.** At the moment the gate was
written, `reviewThreads.totalCount` was **zero on every pull request this repository had ever
had**, and every review finding it had ever produced was an issue comment, which the query does
not return. So on the history to that point, body-only and body-plus-threads were
indistinguishable, and check 2 would have been green on the very pull request cited as the
measured shape. What makes the scope worth holding is not that history but the rule beside it:
a finding now goes in a thread, and the first review conducted under that rule put sixteen of them
on this gate's own pull request. ⛔ The honest reading is that check 2 is **prospective** — it
holds nothing retroactively, and a reader who takes the scope as evidence the threads were already
there has it backwards.

### What this gate deliberately does not check

- **The closing half of the rule.** No item closes carrying an unresolved item either, and that is
  a tracker write this gate neither performs nor reads. Only the merge half is held here.
- **Whether the answer is true.** `None.` is a claim, and the gate holds that the claim was made
  and that nothing it can read contradicts it. A known cost written into the summary as a feature
  reads as green — the *fidelity* limit this document already states one gate over, in a second
  place.
- **A thread resolved to clear the gate, and on one author's repository that is sharper than it
  sounds.** Resolution is the host's record of somebody's judgement, and the gate reads the
  record rather than the judgement. ⛔ Where the author and the reviewer are the same person,
  nobody else holds the record either: check 2 is then a ratchet against *forgetting* and not a
  guard against *intent*, exactly as check 1's `None.` is. Measured on this gate's own pull
  request, where the sixteen threads raised against it were resolved by the person who raised
  them. What it still buys is the part worth having — a finding cannot be silently absent, and
  clearing one is an act with a name and a timestamp on it — and what closes the rest is a second
  person, which is the `revisit_when` already written against `estimate` in this project's own
  configuration.
- **A finding one pass raised and fixed itself, which is an item in form only.** A thread is how an
  item needing somebody's action is made readable, so a defect found and closed inside a single
  pass has no such item to carry: posting it as a thread *manufactures* one, and where the author
  and the reviewer are one credential the only hand that can clear it is the hand that wrote it —
  the ratchet above, turning on finished work. ⚠️ Measured on #159, whose gate was held red by a
  finding two commits after its fix had landed. What the pass has to say about such a defect
  belongs in the commit that fixed it and in the change's own body, which check 1 already reads.
  ⛔ A thread is for what a reader has to answer, and the gate cannot tell the two apart: it reads
  resolution, which is a record of judgement, and the judgement on work already finished was never
  pending.
- **A finding raised as a plain comment.** A comment carries no resolution state anywhere on the
  host, so nothing can report it unresolved — which is why the rule puts a finding in a thread.
  A finding posted where it cannot be read back is a reviewer's catch, and the one real hole in
  check 2. ⚠️ It was the whole of this repository's review record until this gate landed.
- **A marker with no colon and no argument list.** A bare `TODO` in a sentence is prose, and it
  already sits innocently in this tree — in a comment quoting a status vocabulary, and in this
  document. Sweeping prose for the word would redden on a reworded sentence, which is the
  *quoting* failure ruled out above. `FIXME` and `XXX` occur nowhere here and are carried for the
  projects that arrive with them.
- **A marker this change did not write.** Only added lines are read: somebody else's marker is
  somebody else's item.
- **A marker in the script itself.** ⚠️ That one file, not all of `tools/` — it necessarily
  writes
  down every form it forbids, and its sibling needs no such licence, which matters because `tools/`
  is where further scripts land. Both halves are asserted: the whole-change fixture carries a
  marker in this file and stays green, and a plant puts one in a sibling tool and reddens.
- **A setext heading.** `Open items` underlined with hyphens is an `h2` to the host and is not a
  heading to this gate. The residue is narrow and the alternative is a second heading grammar.
- **A pull request that does not exist yet.** Run by hand before one is opened, the gate has no
  answer and says so, and no answer is not green — the surface's rule for an absent run
  ([§ 2](../plugins/mjolnir/config/schema.md#2-code-host)) holds here for the same reason.
- **A thread resolved after the last run.** ⚠️ `pull_request_review_thread` is a webhook the host
  sends and **not** a workflow trigger — a workflow file naming it is rejected whole, measured
  twice here as a push-event failure with no jobs. So the gate re-runs when a review is
  *submitted*, which is when findings arrive, but not when the last one is *resolved*: that
  verdict stands until the next push, body edit, review or manual re-run. The direction that
  matters is covered — findings arriving turn it red — and the direction left open costs a re-run
  rather than a false green.
- **A merge between the last run and the button.** The verdict is about the change as the last
  triggering event left it. The window is small; it is not nothing.

## Beside the document checks: the tracker port's own contract

⚠️ No count of the scripts is carried here. The two above hold a document claim and are what this
document was written for; the rest hold a module, a shape or a rule — the configuration reader
`plugins/mjolnir/scripts/config.py`, whose own checks are its work item's; the prose-width sweep,
which reads the same documents and holds none of their content; the reply-register hook recorded
two sections on; and the port contract recorded in this one. Each carries its own workflow and
its own `host.checks` entry, for the reason the sweep above does: one entry states one mirrored
command.

`plugins/mjolnir/scripts/port.py --self-test` runs in the `Port contract` workflow. It is not a
document check, and it is recorded here because its subject is the same discipline — it holds a
claim about the tree that a reviewer would otherwise be the only thing holding.

What it holds: that the operation list and every absent case are read out of
[schema § 3](../plugins/mjolnir/config/schema.md#the-operations-and-what-an-absent-capability-does)
rather than written in the script; that an unavailable operation comes back as the fallback stated
there and never as an error; that an advance to a status whose configured writer is not the
procedure is refused with the writer named
([schema § 4.2](../plugins/mjolnir/config/schema.md#42-status--an-ordered-set-of-name-role-writer));
and that against a configuration with no tracker every operation is unavailable while the report
reads as a configuration rather than a fault.

The kinds are the same two as above. Reading the operation list and the fallback text out of the
surface is **computed** — a reworded fallback travels, and a table that states the list twice, or
states an operation twice, or loses a cell out of a row, reddens rather than silently changing
what a role is told. One check is **forbidding**: that the contract itself names no tracker the
surface declares, in the slug spelling or the prose one and in any case, to the same de-slugged
grammar check 6 above uses and with the kinds derived by asking the reader which `kind` values are
trackers.

### What it deliberately does not check

- **That an adapter is correct.** One implementation is installed, and the gate imports it: what
  it asserts about it is that the install is load-bearing and that the report names exactly the
  operations the implementation leaves alone. ⛔ It performs no operation against a host — the
  job carries no credential, and every branch that invokes an operation runs against a double or
  a stated-empty registry rather than against whatever happens to be built. So whether a call
  actually does what the tracker's API documents is held by nothing here; it is held by running
  it, and the measurements live on the work item. The remaining kinds are their own items.
- **Any module but the contract.** `plugins/*/scripts/` sits outside the sweep's strict set,
  which that sweep argues in stack terms — an implementation is written in some language and
  saying so names the toolkit's stack rather than a project's. It gives no reason to exempt a
  module from the *tracker*-name rule; that exemption is an artifact of the strict set being
  path-shaped. So the contract asserts the rule of **itself**, and nothing holds the reader beside
  it or the adapter modules — where a kind's name is legitimate anyway. A carrier root,
  where a role's text lives, is still swept by check 6 above, which is the half of this that
  matters for a shared role.
- **That a fallback is the right fallback.** Whether writing a gate result into a description is
  what a project wants where comments are impossible is a judgement the measurement behind it
  carries, not something a check can read. This is the *fidelity* limit one claim over.

## Beside them: the claim on a work item

`plugins/mjolnir/scripts/claim.py --self-test` runs in the `Claim carrier` workflow, with no
credential and no network. It is recorded here for the reason the port contract is: its subject is
a claim about the tree that a reviewer would otherwise be the only thing holding — and in this case
a reviewer could not hold it at all, because what is being asserted is that an operation *races*
correctly.

The rule is
[schema § 10 → The claim on a work item](../plugins/mjolnir/config/schema.md#the-claim-on-a-work-item),
and ⛔ this document states none of it. What the suite holds: that a second session starting an
item already claimed is refused; that the refusal names who holds it and since when, or names
whichever half it could not establish; that a refused start leaves no ref, no branch and no tree;
that a released claim is takeable again and a release is re-runnable; that a claim with no work
and no occupied tree reads as an *orphaned candidate* carrying both readings rather than being
broken; and that a root with no remote claims locally and says so.

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
| 11 | The branch name is **derived**, and a second interpreter derives the same one from each of the three titles two sessions divided on — planted by removing the **bound**, which answers a name a sibling actually published | the derivation, in two processes | computed |
| 12 | The derivation's bound cuts at a word boundary and leaves no trailing separator, and punctuation, case, digits, a non-Latin script and a decomposed title each slug as stated | the derivation | computed |
| 13 | Two sessions under **two names for one item** produce one claim, with each arm of the item guard attributed separately | two clones | computed |
| 14 | A **landed** ref still matches the item's name and the item still reads free, and a start on it is not refused | two clones, after a real squash merge | computed |
| 15 | A merged pull request that **predates the ref** does not land it, and either instant unreadable makes the arm decline | the comparison, with the measured timestamps | computed |
| 16 | A ref **gone between the listing and the read** holds the item against nobody, and the report says it is gone rather than printing `free` under a `taken` verdict | one reading, constructed | computed |

⚠️ **Check 0 is run once per arm, and that is the finding this suite was written by rather than
for.** The surface states two arms because the first draft of the script shipped only the second —
a lease requiring the ref not to exist — and the first live probe of it pushed a *differing* sha to
an existing ref, which exercises that arm, passes, and says nothing about the arm that actually
fires. Two sessions claiming one item push the **same** integration tip, so git declines to send
the push at all: exit zero, no update attempted, the lease never consulted. The suite's first run
caught it, with the second session cheerfully claiming an item the first already held. ⛔ So each
arm is planted away while the other stays, and the check is believed only where removing *that*
arm is what lets the race through.

⚠️ **Checks 11 and 13 are two answers to one failure, and the suite keeps them apart because
they cover different configurations.** Three items were started twice under two names each on
2026-10-19 — the divergence being how much of the title each session carried — so the derivation
(11) makes two sessions handed one title publish one name, and the ref's own test-and-set
arbitrates as it was meant to; check 13 plants the derivation's agreement away and holds the
residue, which is § 8's translation case and anything named by hand. ⛔ Attributed separately for
the reason check 0 is: with both the guard's arms removed, two sessions claim one item and the
suite says so.

⚠️ **Check 11's plant was wrong first, and the shape of the mistake is worth keeping.** It
asserted that two hardcoded branch names differ — an expression reading only the table of
measured names and never the derivation, which stayed green with the derivation replaced by a
function returning a constant. ⛔ **A check whose planted violation does not reach the mechanism
is a check believed and unexercised**, which is the failure the planting discipline exists to
prevent and which the discipline does not catch by itself: the plant ran, something went red
elsewhere, and the row read as covered. The plant that replaced it removes the **bound**, and
what makes it a plant rather than an assertion is that the bound-free derivation answers the
longer name a sibling session actually published, for two of the three items.

⚠️ **Check 15 is held without a host, and that is the whole of what can be held here.** The
measured failure was a ref reading *landed* on a pull request that merged the day before against
a deleted ref of the same name, and what was wrong was a comparison that was never made rather
than anything about the host — so the comparison is what the suite holds. The wiring was proved
by hand against the live host instead: the same ref read `landed … releasing it needs no
override` on the carrier before the change and `orphaned-candidate` after it.

⚠️ **Check 2 has two shapes for the same reason, and the second one hid behind the first.** A
refusal on the *branch name* never reaches the local half at all — the push is what refuses — so
the no-residue assertion was exercised only where nothing local had been attempted. Where the name
is free and the *tree directory* is taken, git creates the branch and then fails on the path, and
the refusal left a local branch pointing at the base with no tree and no commits: a false claim,
and a durable one, since a pre-filter matching the item's number against the ref tail reads it as
held forever. The suite now refuses in each shape separately, and asserts the opposite direction
too — a branch that existed *before* the attempt is left alone, because a rollback that deletes
whatever it finds deletes somebody else's work.

### What this check deliberately does not hold

- **True simultaneity.** The second arm's real trigger is a ref appearing between one session's
  read of the refs and its write, and nothing here reproduces that window. The arm is exercised
  directly instead — an update to a ref the lease was told must not exist — and the two arms
  together cover the two orders. ⚠️ What is untested is the *interleaving*, not either mechanism.
- **The host's own record.** Who pushed a ref and when is read from the host, and the suite's
  remote is a bare repository that records neither. So the half the surface requires be *named as
  unestablished* is what gets asserted, and the populated half is proved against the host by hand.
  ⚠️ That read is also bounded by a page of the host's activity, so a claim older than the window
  reports the time as unestablished rather than reporting the ref free — stated because the
  failure direction worth knowing is the one that is safe.
- **That an orphaned candidate is genuinely orphaned.** It cannot be known from outside: a session
  that died holds the same ref as one about to commit. The check holds that both readings are
  stated and that nothing is broken automatically, which is the whole of what is decidable.
- **The third liveness arm, against a host.** An open pull request referencing the ref needs a
  credential, so in the suite that arm reports itself unestablished and the first two carry the
  verdict. On a project whose claims are all fresh refs with no commits, that leaves liveness
  resting on the occupied-tree arm alone.
- **Whether a process occupies a tree, where the open-file table cannot be read.** The arm has
  three answers and the third is *unestablished*, never *the tree is idle*. ⚠️ Check 8 holds the
  at-or-below half against a real process; what no check here holds is the **unreadable** branch,
  because a machine where the table cannot be read is not a fixture this suite can build. On such a
  machine the arm reports rather than answers, which is the safe direction. It is
  [#34](https://github.com/ragnor-rs/mjolnir/issues/34)'s test called rather than a second one, and
  [#31](https://github.com/ragnor-rs/mjolnir/issues/31)'s sweep is its other consumer.
- **A claim broken with the override.** Check 6 holds that the refusal happens and that it names
  the decision as a person's; it cannot hold that the person was right. ⛔ That is the *fidelity*
  limit this document states one claim over, and the reason the override is a flag rather than a
  heuristic.
- **A branch whose own commits cancel out.** The content half of the landed test asks whether the
  ref differs from the integration branch, and work that adds something and takes it away again
  differs in nothing — so it reads *landed* having never merged. ⚠️ The host's record of a merge
  does not rescue this one, since there is no merge to find; what bounds it is that a claim with a
  net-empty diff has nothing to lose by being released. Recorded because it is the one case where
  this reading errs towards *releasing* rather than towards refusing.
- **A claim squash-merged and then built on top of.** Check 9 holds the plain squash case. Where
  other work lands on the integration branch afterwards, the ref is an ancestor of nothing and
  differs from the branch in that other work, so only the host's record of the merge settles it —
  and that needs a credential the suite holds none of. ⚠️ Without one the reading is *live*, which
  refuses a start rather than taking a held claim. ⛔ This is the limit the whole ordering of that
  table exists for, and it is recorded rather than reported clean because the first version of
  this module read the weakest signal first and called every merged claim live — found on its own
  branch one minute after it merged, not by the suite.
- **A claim on a project sharing no remote.** Two machines with no remote between them cannot be
  arbitrated by anything, and the surface states that rather than guarding it.
- **The host's pull-request arms against a real host.** Check 15 holds the comparison and nothing
  runs `gh` in the suite, so what is untested here is that the field read carries the instant the
  comparison needs. ⚠️ The *open* pull request arm has the same name-reuse exposure and is left
  alone: a reused name whose previous occupant has an open request reads **live**, which refuses
  a start and asks for an override to release — the safe direction of the two, and the reason the
  merged arm was the one worth the comparison.
- **Two sessions reaching the second item read together.** Both give their refs up and the item
  is left free, which the suite does not reproduce because true simultaneity is not a fixture it
  can build — the same limit the second test-and-set arm has. ⚠️ What is held is each arm
  separately; what is reasoned is that the outcome of the interleaving is a refusal to both
  rather than a claim to both.
- **A tracker whose identifiers are not digits.** The item a branch carries is recovered from the
  name only where it is a run of digits, so a project whose keys carry their own separators
  states the item rather than having one guessed out of a slug. ⛔ Where it is neither stated nor
  recoverable the guard does not run, and the ref name is the whole of the claim again — which is
  the pre-derivation behaviour and is recorded here rather than reported as covered.

## The reply's register: held in the session, not on the gate

The surface fixes the register of the reply a role writes in the session, as procedure with no
per-project setting —
[schema § 8 → The reply to the person running a role](../plugins/mjolnir/config/schema.md#the-reply-to-the-person-running-a-role).
⛔ That rule had to be held by something other than the writer, because a writer judging its own
register while writing is the mechanism it replaces, and the honest-looking version of the defect
is the one that survives review.

**A gate cannot hold it, and that is not a limitation of this repository's gate.** A reply is not a
file; it exists in a session and nowhere a workflow can read. The harness's `Stop` event is the one
place the finished reply is available, and it hands the text over directly, so
`plugins/mjolnir/hooks/hooks.json` is the carrier and
`plugins/mjolnir/scripts/check_reply_register.py` the implementation it calls — the division
`config.py` already has, and the reason the hook script is classified rather than strictly swept.

| Property | What is checked | Kind | A finding |
|---|---|---|---|
| Opening | The first line carrying the reply's own words is not one of a closed set of preamble forms | forbidding | **blocks**, once per turn |
| Length | No text is compressed into an arrow chain — two arrows sharing an operand, with no clause between them | forbidding, over a density | reports every chain; **blocks** where compression is the texture, once per turn |
| Emphasis | Emphasised spans against the reply's own prose line count | computed | reports |
| Register | A closed list of dramatic words, and exclamations, over a density | forbidding, over a density | reports |
| Uncertainty | A closed list of hedges, over a density | forbidding, over a density | reports |
| Completeness | A closed list of parking forms — work promised, offered, or excused rather than done | forbidding | **blocks** on one span, once per turn |
| Structure | — | — | nothing; see below |

**What blocks, and what a hand-back costs.** A finding blocks where it is a fact about the text
*and* worth what handing the turn back costs — which is a correction the person reads, and was the
whole reply a second time until the measurement four paragraphs down. ⚠️ Measured on the four
hand-backs
this check had recorded on 2026-10-20, in projects with this plugin enabled and no configuration of
their own: thirteen of twenty-one prose lines came back byte for byte in the first, eight of
thirteen in the second, and the third brought back a reply whose second pass also dropped a
file-and-line citation the first had carried. Each paid that for two reworded clauses. ⛔ **Three
of the four were paid for a defect that was not there**, and all three came from matching a bare
token — a pair of arrows with a clause between them in the first, a ruled word in a sense that
parks nothing in the second, and the same ruled word in the first person in the fourth, which the
third narrowed the others without reaching. Nothing in the first shape of this check accounted for
that price.

⚠️ **The fourth arrived on the same day as the change that narrowed three of the four ruled forms,
after that change had landed**, so the figure above states the date it is true of rather than that
day's end: a count stated over a window whose end the reader cannot see keeps growing after it is
written.

⛔ **What a restatement in fact returns is measured over every hand-back this check has recorded**,
rather than over the four read by hand, since what
[§ Nothing is deferred](../plugins/mjolnir/config/schema.md#nothing-is-deferred) charges for a
finding on a reply is this: 41 hand-backs, across nine projects' transcripts, from 2026-10-17 20:59
to 2026-10-20 13:04 — the end stated as a time rather than a date because one more arrived while
this was being written. A restatement answering the blocking finding alone brought back **167 of
307 prose lines byte for byte**; one answering a reported density alongside it brought back **71 of
300**. On the *Completeness* arm alone, where the blocking finding is a single span either way, the
same split is 128 of 213 lines against 50 of 193. ⚠️ **What did not come back unchanged came back
reworded rather than dropped**: 263 of those 307 lines have a counterpart in the restatement that
says the same thing in different words, which is what costs the reader a second reading of a reply
they had already finished.

⛔ **So a reported finding was asked for after all, on every turn where something else blocked** —
against the division
[§ 8](../plugins/mjolnir/config/schema.md#the-reply-to-the-person-running-a-role) is held to here,
which is that only an asking answer spends a re-read. The answer listed both kinds under one ask,
and context handed back on a `Stop` is read by the writer whether or not the answer blocks, so the
one price the reporting kind was changed to stop paying was charged again by any turn carrying one
finding of each. ⚠️ **Half the hand-backs are that shape**: 29 of the 57 replies this arm hands
back, over the corpus the section below states, carry a reported density too. Measured on the reply
it was found on — one parked sentence blocking, an *Emphasis* density of 15 spans reported beside
it — the restatement came back with 2 emphasised spans, **1 of its 14 prose lines byte for byte**
and 9 carrying a reworded counterpart, and it dropped one of the two questions the first reply had
put to the person. A question lost in a restatement is visible to nobody: the corrected reply is
what the person reads, and it is green.

⛔ **Two things change, and neither is which findings block**, both under
[§ Nothing is deferred](../plugins/mjolnir/config/schema.md#nothing-is-deferred). The ask is
addressed to the findings that block it, with a reported one named *after* the sentence that asks
and under a line saying it is not what the correction is for. And what **corrected** means is
stated on the surface, in the section cited above, rather than reproduced here. ⚠️ **The second is
measured on a
hand-back that carried no density at all**: one parked clause blocked, the writer did the work the
clause had offered, and the reply came back with 3 of its 9 prose lines byte for byte and a
reworded counterpart for all nine — so the rewording is not the density arm's doing, and bounding
the ask alone would not have stopped it. ⚠️ **The bound is prose asked of the writer and held by
nothing**: the self-test holds every asking answer to carrying one of the two asks, and nothing
compares a correction to the reply it corrects. Stated because an unstated limit reads later as
coverage.

⛔ **The bound held, and the duplication did not go away** — which is the measurement behind what
[§ Nothing is deferred](../plugins/mjolnir/config/schema.md#nothing-is-deferred) now says a
correction is. The first hand-back after it was answered exactly as asked: of
the reply's 16 prose lines, **15 came back byte for byte**, one changed, and 226 characters
differed. The reader read **2,918 characters** a second time to be shown those 226, and reported
the same complaint that opened this section. ⚠️ **A diff is what makes a corrected re-send cheap,
and a session has none**: the terminal renders both replies in full, so a restatement costs its
reader the whole page whatever share of it is identical. Four hand-backs were reported as
duplication before this was read, and the bound improved three of them without closing one.

⛔ **So the correction asked for is as small as the finding**, which is
[§ Nothing is deferred](../plugins/mjolnir/config/schema.md#nothing-is-deferred)'s rule, held here
by the reach each blocking arm declares. A finding that names a span — a parked clause, a preamble
opening — asks for that span
and its replacement and forbids the reply being sent again; compression as the reply's *texture*
asks for the reply, having no span to name. ⚠️ **A mixed answer asks for the reply**, the span
fixes carried inside it, which is the dearer price and the safe direction. The two asks are two
strings, and `--self-test` holds every asking branch to carrying exactly one of them, each arm to
declaring a reach, and the person's own line to naming which was asked for — that last written
after a break that reverted it and reddened nothing.

- **Opening** blocks on one instance. It is the first thing read and the frame for everything under
  it, and a preamble form is a phrase rather than a judgement.
- **Length** reports every chain it finds and blocks only where the count is over a density of the
  reply's own prose lines: compression as the reply's *texture* rather than one line to restate. One
  chain is told to the person and asks the writer for nothing. ⚠️ That density is not the weakness
  the three below have — what it counts is a form the text either carries or does not, so the
  threshold decides whether a re-read is warranted rather than standing in for the rule.

- **Completeness** is the one row here whose rule is not § 8's: it holds the reply to
  [schema § Nothing is deferred](../plugins/mjolnir/config/schema.md#nothing-is-deferred), the
  surface's first rule, which already says that rule reaches a role's own reply. It blocks on a
  single span, which no other arm here does, and the price is deliberate: the alternative is the
  person reading parked work and having to say so, which is the thing the rule exists to spare
  them. ⚠️ **It shares the closed-list weakness of *Register* and *Uncertainty* and does not share
  their verdict** — a reworded parking passes, and what covers that is the reader, as it did
  before. The difference is what a hit means: a dramatic word is a tone, while a parking form is an
  act, and an act is worth the re-read a tone is not.
- ⚠️ **Four of its forms are named by a ruling rather than derived, and all four are matched only in
  their parking senses** — the second half by a ruling of the same date, 2026-10-20, reading the
  measurement below. A bare match hands a turn back over text that parks nothing, which is the
  re-read above paid for a finding that is not there, so what each form is matched in is the
  writer's **own** absence: an omission excused rather than filled, a section of work the reply
  carries rather than does, a gap stated in place of being closed.
- ⚠️ **The premise the first three were left bare on failed the next day.** They were held to be
  distinctive enough that a reply has no other use for them, and each is in fact this repository's
  own vocabulary for a mechanism: `deliberately` records a design intent, in nine of this document's
  own section headings and in § 4's word for a facet nobody configured; `open items` is what
  § Nothing is deferred's gate counts on a change; and `stated plainly` is § 8's Uncertainty row and
  the text of this check's own finding for it, so a reply relaying this check reddened on it. ⚠️ The
  first of the three is **measured on a reply** and the other two are **demonstrated against the
  shipped check** — a sentence this repository writes by the dozen, run through the arm — rather
  than waited for. `left` has that carve-out for the bare word, which is ordinary English for what
  a process or a merge did — *three trees left behind*.
- ⛔ **`left` had that carve-out in the third person only, and the first person was bare.** One of
  its alternatives matched `I left` as a token, so the word was carved out for what a sibling
  session did and not for what the writer did — and what a role's reply says about work it has done
  is in the first person: *I left the tree and released the claim*, *I left a review comment on the
  thread*. ⚠️ **Measured on the fourth hand-back**, on a reply reporting a file correctly left
  unchanged, the same day the other three forms were narrowed. The green plant that was meant to
  hold this carve-out asserted a sibling session's tree rather than the writer's own sentence, so it
  could not reach the alternative that was bare: a form is only carved out in the person its plant
  is written in. The first person is now read with the parked state it leaves behind — *left the
  second arm unfixed* — over the same bounded gap `stated plainly` is read across.
- ⛔ **The rest of this arm's false reds were measured over the corpus rather than waited for.**
  Each of the four narrowings above was paid for by a hand-back first, which is one false red per
  re-read, so the fifth was found by running the arm over the artifact it holds: **2,713 finished
  replies** in this project's own session transcripts, every assistant message carrying text and no
  tool call. 99 spans matched, across 27 distinct forms. ⚠️ **The majority are the acts the rule is
  for** — 39 are `say the word`, and the rest are offers, a section of work named and not done, and
  a figure asserted to stand — which is the result that makes the arm worth having. Four forms
  carried a second sense this repository writes constantly, and each is now read around the match:
  a heading of another artifact cited in double quotes, where a code span and a block quote were
  already carved out; an absence stated, which is what the rule asks for; § 10's own instruction to
  a role that cannot delete the tree it stands in, *say what is left to remove and where*; and a
  scope stated by declaration. ⚠️ **Two words are excluded from the parked state the word is read
  with, on that same measurement**: *on the same unresolved threads* is how a review's red runs are
  reported here, and *left untouched* is how items that already carried a label are, so `unresolved`
  and `untouched` match nothing, where `undone`, `unfixed`, `unaddressed` and `unfinished` do.
- Three further senses the same sweep measured are carved out rather than recorded as costs, each
  by the thing it names rather than by its wording: **work the surface reserves to the person**,
  read with the clause that governs it — *it isn't my claim, so I haven't touched it*, *that
  document is the close-out role's* — where the measured parking, *two things that follow, which I
  haven't touched*, carries no such clause and stays red; **an artifact's own decisions described**,
  read with its subject, where *the decisions the item left open* is the item's and *the two items I
  left open remain open* is the writer's; and **§ 10's handover of what a role cannot do**, matched
  by a closed list of what the surface reserves — the tree a session stands in, its branch, a
  priority nobody may derive. ⚠️ A parking that names one of those in the same sentence passes,
  which is this list's ruled direction.
- ⛔ **A count of what an arm raises is counted through the arm, not off its pattern.** The first
  measurement here counted raw matches, which reports spans the carve-outs already suppress and
  flatters every one of them. Read through the whole pipeline — the quoted blanking, the negation,
  the senses — this arm raises **62 spans and hands back 57 of the 482 replies** that end a turn, of
  2,901 text-only assistant messages on 2026-10-20, where the shape it shipped in raised 99 over
  every such message. ⚠️ What remains is the arm working: offers, a section of work named and not
  done, a figure asserted to stand, and `say the word` 36 times over. ⛔ **Which replies those 482
  are, and why the larger figure is not a hand-back rate, is the last entry under
  [§ What this check deliberately does not hold](#what-this-check-deliberately-does-not-hold).**
- ⛔ **One further carve-out was measured and rejected rather than shipped**, recorded so that it is
  not proposed a second time as though it were untested. The hand-back that occasioned the
  measurement above fired on `say the word` closing a reply that *had* asked its blocking question
  with three options and their costs, so the asking sense was a candidate for the same narrowing the
  four ruled forms got: the form read with a clause reserving the decision to the person — *your
  call*, *the choice is yours*, *one decision I can't make for you*. ⚠️ **The corpus refused it.**
  Of the 41 offer-form spans this project's replies carry, such a clause in the same line greens
  exactly **one**, none carries one in the line before, and the one it greens offers to lay the
  options out in a later reply, which is a parking in the shape of an ask. Read over the whole reply
  instead it greens four more, and every one of them is an offer of work the reply had finished
  without it: review threads nobody asked for, an assignee re-stamped, a delegated review pass, an
  ignore entry. So the form stays matched in every person and sense, and what a hand-back on it
  costs is bounded above rather than carved out here.
- ⚠️ **One false red is kept rather than closed, and it is kept knowingly**: `deliberately absent`
  is both the shape the ruling was measured on and § 4's own phrase for a facet carrying an
  `absent_reason`, word for word, so a reply writing the second is handed back. Nothing lexical
  separates them. ⛔ The direction the rest of the list errs in is the opposite one — a reworded
  parking passes — and `deliberately not written`, which two documents here use to state a limit,
  is excluded for that reason and misses a parking that would say it that way. The first-person
  narrowing errs in that same direction and is stated here rather than left to be read as coverage:
  *I left it alone* and *I left it unchanged* are a judgement as often as they are a parking, so
  neither state is matched, and a parking worded that way is missed.
- ⚠️ **Two of the sweep's own spans are the writer's to fix rather than this arm's**, and they are
  named so that a later sweep does not read them as the arm's defects: a ruled phrase cited in
  *emphasis* rather than in a code span is the writer's own voice by every convention here, so it
  reddens and should have been written in backticks; and a column header reading `what is left`
  over a count of a check's hits is a label whose sense nothing lexical separates from the parking.
  One span each.
- ⛔ **One of the forms is read with its answer rather than as a span**: a section of open items is
  a finding where it lists any, and not where it answers `None.` — the same heading text and the
  same answer the gate on the change's body holds that section to, so that a reply and a body
  answering one question do not answer it in two conventions. ⚠️ Found in the change that narrowed
  the rest: the heading alone had been a finding, which hands back a reply for carrying the very
  answer the convention asks for.
- Every form is planted in both directions, and the green plants are the sentences this repository
  actually writes: the shape each ruled form was named for stays red, while a design intent
  reported, a heading cited, a limit stated, the gate described, and this check's own finding
  relayed are each asserted to stay green. ⚠️ **In both persons, where a plant in one person was
  what let the first-person form ship bare**: the loop's own cleanup, a review comment left on a
  thread, and a file reported correctly unchanged are each asserted green in the first person, and
  the parked state the first person is now matched with is asserted red with and without an object
  between the two words. ⛔ **Each carve-out the sweep added is planted with the sentence that was
  in fact reddened**, and every one of them was verified by disabling the carve-out and watching its
  plant go red — the direction a carve-out has to be established in, since a green plant passes
  whether or not the mechanism it names is there. The negation carve-out carries a red plant too: a
  parking after the negator's own clause ends, *I did not finish the second arm, so next steps*,
  which is what keeps `nothing` from greening a reply that negates one thing and parks another.

⚠️ **A chain is two arrows sharing an operand, and sharing is not a token count.** The first form
read one or two tokens between the arrows as the shared operand, so
`FRESH` or `OURS` → write; `CHANGED` → report — two mappings that share nothing — was read as a
chain and handed a turn back. A clause between the arrows now says they are two mappings:
clause-ending punctuation, a dash, or a coordinator. A dot inside a token ends no clause, so a chain
of file paths is still a chain.

The other three are weaker in two different ways, and neither weakness is a threshold alone.
*Emphasis* is genuinely **computed** — a density derived from the reply's own length, so no word
list can be reworded past it, but the density is a proxy for "as a default texture" rather than
that rule. *Register* and *Uncertainty* are **forbidding** checks over closed word lists read at a
density: ⚠️ a synonym that is not on the list passes, which is precisely the *quoting* weakness
this document rules out elsewhere, and the lists cannot be completed because the thing forbidden
is a tone rather than a name. So all three report and none blocks. ⚠️ The densities are
deliberately not written down here — a number in prose is a copy that has to be kept in sync, and
the run prints its own.

**Blocking means handing the turn back, not refusing it.** The hook returns `decision: block` with
the findings as `additionalContext`, which the harness's documented contract makes the field the
writer reads back; the `reason` beside it is shown to the person instead. ⚠️ **It blocks at most
once per turn**, keyed on the harness's own turn id under `CLAUDE_PLUGIN_DATA`, because a hook that
also blocked the restatement would hold the session open on a judgement a forbidding check cannot
make. A payload carrying no turn at all cannot be guarded, so a finding that would have been handed
back is asked for anyway and the answer **says that it could not guard**, rather than returning the
same answer as a turn that has had its hand-back. ⚠️ **The marker records a hand-back and not a
fire.** While every answer asked for a restatement the two were the same event; once one of them
stopped asking, a density first in a turn would have spent that turn's one hand-back and the
blocking finding after it would have been told, falsely, that it had already had one.

⛔ **What costs the reader the reply a second time is asking for it, and `decision` is not what
decides that** — a statement about how
[schema § 8 → The reply to the person running a role](../plugins/mjolnir/config/schema.md#the-reply-to-the-person-running-a-role)
is held here, which is this document's half of that rule rather than the surface's. Context handed
back on a `Stop` is read by the writer whether or not the answer also
blocks, so for as long as every answer carried context, the two kinds in the table above were never
the two prices they read as. ⚠️ Measured over the sixteen answers this check has carried context on,
across thirteen sessions of a project with the plugin enabled: every one of them recorded
`preventedContinuation: false` — the two that set `decision: block` included — and every one was
followed by a further reply. Thirteen of the sixteen were a density that only reported, and fourteen
of the sixteen were *Emphasis* alone. In the shape before this was read, those density answers
closed on *the next reply is written knowing them* — a deferral stated by the guard that holds the
rule against deferring, which a session obeyed with a promise in place of a corrected reply; in the
shape after it, the one that fired brought the whole reply back for one line of bold.

**So an answer that does not block asks the writer for nothing, and tells the person instead.** The
findings reach whoever ran the role as the session message, named rather than counted, and the turn
ends there — which is the whole of what `reports` costs in the table above. Two answers still ask,
and both ask for the reply just sent to be corrected inside the same turn, because that is the
reply carrying the findings and
[*Nothing is deferred*](../plugins/mjolnir/config/schema.md#nothing-is-deferred) admits no deferred
work: the turn that is handed back, and a finding that would have been handed back on a payload the
guard could not be kept for. ⚠️ **What they ask to be sent is one of two strings** and not one
shared by both, by the reach rule above: the corrected span, or the reply. `--self-test` holds each
asking answer to carrying exactly one of them and to promising nothing about a later reply — and
holds the other two to carrying **neither** and no promise either, because dropping the ask is a
licence to defer unless what replaces it is silence towards the writer.

⛔ **What either of those two answers asks for is the blocking findings, and a reported one rides
along named as not that** — the two kinds of
[§ 8](../plugins/mjolnir/config/schema.md#the-reply-to-the-person-running-a-role)'s table kept apart
in the one place they are read. It is one list under the ask and a second after it, in that order,
and `--self-test` asserts the order on both answers and on a composed reply carrying one of each
kind: a reported finding ahead of the ask is a density asked for, which is the price the reporting
kind exists to not pay. ⚠️ **The person is told both regardless** — the `reason` beside the context
names the reported arms as reported, so a hand-back reports no less about a reply than the same
reply would have been told on a turn where nothing blocked. ⛔ **No channel here reaches the person
without reaching the writer**, which is why the bound is prose rather than an omission: the harness
injects both the context and the `reason` into the session, measured on the transcript of a
hand-back, so dropping a reported finding from the context would hide it from the person and leave
it in front of the writer anyway.

It derives what it can, for the reason the gate's own scripts do:

| Derived, at run time | Hardcoded |
|---|---|
| the property list, from the first column of the register's own table in the surface | the anchor of the subsection that table sits in |
| which properties are accounted for, by holding that list against the checks in both directions | the preamble forms, the chain form, the word lists and the densities |
| the self-test's own plants against the surface, from the table it just parsed | the markdown table and heading grammar |
| that the carrier still names this script, by reading `hooks.json` and resolving what it calls | the hook event's name, and the carrier's path |

A property added to the register's table with no check and no stated reason for having none
reddens `--self-test` at the moment the row is added. That is check 2's direction, one surface
over — and it runs in the direction nobody remembers to check by hand, because the failure
otherwise is a register that grew a clause and a hook that silently never held it. ⛔ Held and
excused are kept apart rather than unioned: a property excused *in part* must still be held in
part, so deleting the compression check does not leave the padding limit standing in for it. The
same discipline reaches the carrier — `hooks.json` naming another script, another event, or
nothing parseable at all leaves every check here green, so the gate resolves what the carrier
calls and asserts it is this script. See
[schema § 7](../plugins/mjolnir/config/schema.md#7-carrier) for the carrier axis itself.

### What this check deliberately does not hold

- **Structure.** Whether continuous prose was carrying enumerable facts is a judgement about the
  facts and not about the text: the same paragraph is correct prose or a withheld table depending
  on what it says. A reader covers it.
- **The padding half of Length.** Whether a sentence earns its place cannot be computed, and a
  length threshold would punish exactly the content the rule's own first clause protects. Only the
  compression half is held — which is also the distinction the rule turns on: shortening by
  selection against shortening by compression.
- **A chain whose operand is repeated across a clause.** `open → closed; closed → archived` shares
  an operand in meaning and is two mappings in form, and form is what a check reads. ⚠️ A finding
  missed rather than a finding invented, which is the direction the one check here that still hands
  turns back on a form has to err in.
- **A reported finding, in the reply it was found in.** Nothing is asked of the writer, so the
  reply the person has already read is the reply that stands. ⚠️ Measured on the same sixteen
  answers: three of the thirteen sessions carried two, and in one of those both were the same
  *Emphasis* density — the second after the first had been read and acknowledged in that session.
  So the ask the arm used to carry did not buy compliance either, and what it did buy was the
  re-read. ⛔ What is left unheld is a density that nothing fixes — stated plainly, because the
  alternative measured against it was a whole restatement for one line of bold, and an arm that
  costs nothing and holds nothing is not the same as one that holds something.
- **Whether the reply was a role's at all.** The hook fires on every reply in a session where this
  plugin is enabled, and nothing in a `Stop` payload says whether a role was running. So the
  register is held more widely than the surface states it — in the safe direction here, and stated
  because an unstated limit reads later as coverage. ⚠️ That direction is a property of this one
  rule rather than of hooks, so what a hook reads in place of a role is
  [#87](https://github.com/ragnor-rs/mjolnir/issues/87)'s to settle. It blocks nothing, and that is
  a finding rather than an omission: a guard is correct whether or not a role is running — a build
  slot contends regardless, and a check the host has already run for this code is wasted work
  regardless — so every hook role [#16](https://github.com/ragnor-rs/mjolnir/issues/16) measures
  keys on an event and a command, and passes its acceptance check without the ruling. The gap
  belongs to a rule whose **scope** is the loop rather than a command, which today is only this
  one. ⚠️ **The wider hold is where every hand-back has in fact been measured** — each of the three
  was on a reply in a project carrying no configuration of its own, so the remedy an asking answer
  names, work going under the current branch and pull request and item, named artifacts the project
  had none of. That is an argument for the arm's precision rather than for its reach: a reply
  answering a question about history owes no work, and nothing in the payload says so.
- **Every reply but the last of its turn.** A `Stop` payload carries one message, the turn's final
  one, so a reply the writer sends and then follows with a tool call is in no payload and is held to
  nothing — and a turn ending in a tool call carries no final message at all, which the hook answers
  with nothing rather than a guess. ⚠️ **It is most of the text a session produces.** Measured over
  this project's transcripts on 2026-10-20: **482 of 2,901** assistant messages carrying text and no
  tool call end their turn, and the other 2,419 are mid-turn text the hook never sees. ⛔ **The
  larger figure is the one the parking arm's own counts above were taken over**, so it cannot be
  read as a hand-back rate: five sixths of it could not have been handed back whatever the arm
  found. The carve-outs it bought stand either way — a sense wrongly matched is wrongly matched
  wherever the text sits — and the figures above are stated against the 482. ⚠️ **The restatement
  this section measures is itself an instance**: it ended in a tool call, so the reply the hook had
  asked for was never read by the hook that asked.
- **A reply repeating one already sent in the same turn**, which is what the limit above leaves
  open and is not closed by reaching for the transcript the payload names. ⚠️ **Measured, and the
  measurement is why**: of 327 turns in this project's transcripts carrying more than one reply, 4
  end on a reply that repeats at least half its prose lines from earlier in the turn, and 3 of those
  4 are the restatement this rule asks for rather than a repetition nobody asked for. ⛔ **And the
  one case this was measured on is invisible to any comparison of text**: a reply reported in full,
  a question went to the person through a tool, and the reply after the answer stated the same facts
  again in different words — every one of its five prose lines sits between 32% and 45% of its
  nearest counterpart, where a restatement of the same reply sits above 60%. What repeats is the
  content, which is the judgement *Structure* is already left to a reader for.
- **Code, a quotation, and — for the emphasis density only — a table.** A fenced block, an
  indented block and a quoted line are dropped from every check: they are not the writer's own
  prose, and sweeping them produced false reds on a pasted traceback and on quoting the person's
  own words back. Table rows are read by the word-list checks and **not** by the emphasis density,
  because a bolded term in a cell is the shape the Structure row asks for. So emphasis as a
  texture inside a table is held by nothing.
- **A failure before this script is running.** The hook fails open and names itself, but only once
  it has started: the harness's timeout, no interpreter on the path, or a syntax error in the file
  produces no output at all, and nothing in the session then says the reply was held to nothing.
  That residue cannot be closed from inside the hook, and what covers it is this run.
- **Its own failure.** ⛔ The hook **fails open** and says so: an internal error answers with a
  message naming itself, rather than with silence that reads as a reply in register, or with a
  non-zero exit that would break every turn — the same absence-is-not-an-answer rule
  [§ 2](../plugins/mjolnir/config/schema.md#2-code-host) states for the host's own runs.

## Prose line width: held on the gate for files, and nowhere for bodies

`tools/check_prose_width.py --self-test` runs in the `Prose width` workflow, with no credential
and no network. ⛔ The rule is
[schema § 8 → Prose line width](../plugins/mjolnir/config/schema.md#prose-line-width) and this
document states none of it: what is recorded here is the reach of the check, which is narrower
than the rule in one direction the rule itself does not mention.

What it holds: every tracked markdown file — documents, the README, the surface, the skills and
the configuration examples alike — against the width **this project's own configuration states**.
The script carries no number. It reads `language.prose_width` through the shared reader, so a
project that states another width, or states none, changes this gate's verdict by editing a
configuration and nothing else. The kind is **computed**, for that reason. A tree whose
configuration carries no width makes the check hold nothing, and it says so and reddens rather
than passing — the same rule the document checks apply to a glob that matches no file.

⚠️ **It plants both sides, as the reply-register check does.** Violations that must redden — an
overlong paragraph, an overlong list continuation, a tree with no width configured, a tree with
nothing tracked, a tracked file it cannot read, a frontmatter marker that never closes — and one
exemption plant per excluded kind, each of which must stay green. Each exemption was then verified
by **disabling its own exclusion** and watching that plant redden, because an exemption nothing can
fail is an exemption nobody checked, and an exemption list is exactly where a check quietly stops
holding anything. The run prints what it planted; no count of either is written down here.

⚠️ The plants are compared against the tree's **own** result rather than against zero. A whole-file
assertion reads every plant as red while one real overrun is still in the tree, which would make
the exemptions untestable precisely in the change that is removing those overruns — which is the
change that introduced them here.

### What this check deliberately does not hold

- **A body, a pull request or a review comment.** The half of the rule that is *procedure* — the
  half every adopting project inherits — is held by nobody. Those surfaces are not files, so this
  sweep cannot see them, and the gate that does read a pull request could only guess: a
  hard-wrapped body is distinguishable from a short one by heuristic alone — line breaks falling
  mid-sentence — which reddens on a deliberate break, a pasted quotation and a list. ⚠️ The cost is
  stated rather than papered over: the rendered half is a convention again, held by the writer,
  and the only thing standing behind it is that it costs nothing to follow.
- **Anything that is not markdown.** Measured when the width was ruled: this repository's Python
  carries tens of lines past the width and its longest is half as long again, so a sweep over code
  would have been a reformat of every script on day one. A programming language's line width is
  that language's business, and the comments inside a configuration example are annotation on a
  line of data rather than prose a reader reads straight through.
- **Whether a wrapped paragraph is wrapped *well*.** A line of twenty columns beside one of
  ninety-nine passes, because the rule is a ceiling and not a measure of raggedness. This is the
  *fidelity* limit the document checks have, one claim over.
- **A line made long by several short unbreakable runs.** Every run is set aside before the
  measurement, so a line of four code spans and a few words passes at well over the width while
  being perfectly breakable between them. ⚠️ Reproduced rather than reasoned about — a planted
  144-column line of that shape is not reported — and left open deliberately: the stricter
  reading, *one* run, reddens the ordinary citation line this repository carries by the dozen.
  Nothing in the tree is exempt by this route today, which was measured and is why the looser
  rule is the stated one rather than a discovered hole.
- **A document outside the repository.** The ordering document and the per-item working papers
  live in the session store outside every tree (§ 11), where `git ls-files` cannot reach them and
  no width is stated for them.
- **The width as a configured *value*.** The sweep that forbids a configured value from appearing
  in a carrier root reads every scalar a configuration states, and a number is not one of them: a
  width is a bare integer, and a sweep that matched one would redden on every count, threshold
  and year in the tree. What that leaves unguarded is a role's text stating a width instead of
  reading it — which no role does today, because the rule's reader is the writer of a document
  rather than a skill.

## The floor under file prose: held on the lines a change adds

`tools/check_prose_register.py --self-test` runs in the `Prose register` workflow with no
credential, and with the same network caveat the added-lines check below carries, from which it
imports its base derivation. ⛔ The rule is
[schema § 8 → The floor under prose a role writes into a file](../plugins/mjolnir/config/schema.md#the-floor-under-prose-a-role-writes-into-a-file),
and none of it is stated here: what this section records is how far each of the three arms gets,
and the measurement that decided each one.

**What it reads.** Every tracked markdown file, and the prose inside every tracked file whose
comments begin `#` — a script, a workflow, a configuration. ⛔ **The test is the rule's and the
file's extension decides nothing**, which is why the set is not the scripts alone: the arms were
written reading scripts and markdown, and the workflow added beside them in this same change was
unheld while carrying thirty lines of exactly the prose they are for. ⛔ **On the lines the change
adds**, which is the same carve-out and the same machinery as the check below: the diff, the merge
base and the markdown prose grammar are imported from it rather than stood up again, and the word
list and the emphasis grammar are imported from the reply's check. ⚠️ **The arms were measurable
before they were held**, which is why no sweep of the tree is part of this: over this repository at
`7584138`, 48 files carry 2,159 paragraphs the floor reaches, 4,337 of 15,315 lines of tracked
Python are prose by its test, and the three arms find what the two paragraphs below record.

| Arm | What it reads | Kind | On a finding |
|---|---|---|---|
| Restatement | Runs of words an added line repeats out of a document the file cites, quotations, code and the cited document's own headings aside | computed | **reddens**, naming the run and its length |
| Emphasis | Added prose lines in runs, against the position of each line's emphasised spans | computed | **reddens** where every line of a long enough run is marked past its opening |
| Uncertainty | The reply check's hedge list, over one paragraph of added prose, table rows included | forbidding, over a density | **reddens** |
| Every property of the floor is accounted for | The first column of the rule's own table | computed | **reddens** on a row with no arm |

**Why a run of words is a sound end of the padding clause, where the clause itself is not.** What
cannot be computed is whether a sentence earns its place — that is this repository's standing
position, recorded two sections up for the reply and unchanged here. What can be computed is a
narrower thing: this repository already holds that one fact has one home and that a document cites
it, so prose that reproduces a dozen of a cited document's words in a row has a home for those
words and is not it. ⚠️ **The arm is a copy detector and not a judge**: it says the words are in two
places, and which copy should go is still a writer's call.

⚠️ **The three numbers are set where this tree's own habit stops, and they live in the script.** A
dozen words, because that is where repetition stops being a coincidence of English: run over the
whole tree as though every line were added, the arm finds 155 such runs at a dozen words, 290 at
ten and 88 at fourteen — so nothing about the figure is a cliff, and it is set where a reader would
agree that two writers did not arrive there separately. Four lines for the emphasis arm, because
**none** of the tree's 1,268 paragraphs of that length carries a marked span past the opening of
every line, while the two that come closest are three lines long and are lists of defined terms.
One hedge per paragraph, because 36 paragraphs here carry one, two carry two, and none carries
three.

⚠️ **The 155 are concentrated where the item that asked for this predicted they would be**: 22 in
the reply-register check and 22 in the names sweep, both restating the document that records their
limits, and 21 in the surface against 18 in the document explaining it — the two that cite each
other. ⛔ Not one of them is refused by this change, because none is a line it adds; what they are
is the evidence that the arm holds a habit rather than a hypothesis.

⛔ **Emphasis is read past the opening of a line, and that is what keeps the arm off the shape the
Structure row of
[§ 8's own table](../plugins/mjolnir/config/schema.md#the-reply-to-the-person-running-a-role) asks
for.** A marked span that opens a line is a term being defined; a list of four such lines is four
marked lines and is not a texture. Both readings were measured and they agree on this tree — the
narrower one is what shipped, because an arm that hands back a build has to err toward the finding
it misses.

⚠️ **A table row answers to the word list and not to the density, which is the reply check's
division and is taken from it by parameter rather than by retyping.** Found in review of this
change: both kinds of arm had been given one unit, so a cell carrying two hedges was held by
nobody while a table of marked-up cells would have read as a texture. ⛔ **And the green plant for
that row exclusion lied once before it held** — with the header and the delimiter row counted as
added, they joined the run carrying no emphasis, the arm answered *not every line*, and the plant
passed with its own exclusion switched off.

⚠️ **Each arm has a planted violation and the fixture asserts its own premises**, since a plant
against a cited document proves nothing if the planted file does not in fact cite it: the run
prints that every planted file — one per kind the sweep reads — resolves the planted authority, and
that the sentence it restates is long enough for the arm to find. Every exclusion — the quotation,
the code span, the fence, a section named by its title, the added-lines carve-out itself, and the
two kinds of annotation — was verified by disabling it and watching its own plant redden. The
carve-outs with nothing to disable are labelled omissions instead, as the check below labels its
own.

⛔ **One hole was found by a plant rather than by reasoning**, and it is the reason the docstring
delimiter is dropped before anything else: read as text, a triple quote is an empty quotation
followed by an opening one, so the quotation carve-out swallowed every docstring in the tree while
the run reported green. A docstring is prose by
[the rule's own test](../plugins/mjolnir/config/schema.md#the-floor-under-prose-a-role-writes-into-a-file),
so that is the whole Python half held by nothing — and the plant for the habit the arm was built on
stayed green until that line existed.

### What this check deliberately does not hold

- **The padding clause itself, and the compression half beside it.** Whether a sentence earns its
  place is a judgement, and so is whether a passage was shortened by selection or by compression.
  The surface says so; what is held here is the one corner of the first that the authority rule
  already decides.
- **Structure.** Unheld for file prose exactly as it is for a reply, and for the same reason: the
  same paragraph is correct prose or a withheld table depending on what it says.
- **A restatement reworded.** The arm reads a verbatim run, so changing two words in the middle of
  a restated sentence passes it — which is the *quoting* weakness inverted, and a finding missed
  rather than invented. ⚠️ The reach is bounded the same way in a second direction: a document
  named by its bare file name, with no directory in front of it, is not resolved as a citation at
  all, because more than one tracked file can carry one name.
- **A paragraph with one unmarked line in it.** The emphasis arm asks for every line, so a
  five-line paragraph marked on four passes. The threshold is a proxy for *as a default texture*
  rather than that rule, which is the same limit the reply's own emphasis density carries.
- **A hedge the list does not carry.** The list is the reply check's, imported so that one
  rewording reaches both, and a synonym outside it passes. The thing forbidden is a tone, so no
  list completes.
- **A register and an audience.** A project nominates both, and what a nominated register asks of
  a document is held by nobody here — the floor is three properties of the text, and none of them
  is a register. That the README is in a persuasive register and every document beside it is in a
  reference one is a convention of this repository, stated where that page's reader is.
- **Prose outside a tracked file.** A work-item body, a pull request, a review comment and the
  ordering document are not files this sweep can see, so the floor reaches none of them — the same
  shape of gap the width rule has, and the same remedy: a writer.
- **A comment the test reads as annotation.** A trailing comment and a lone whole-line comment are
  out by rule, and a restatement written into one is missed. ⚠️ 137 lines of this tree are in that
  position, against 4,337 the test reads as prose.
- **A format with no comment syntax.** The three JSON files here — the hook carrier, the plugin
  manifest and the marketplace one — can hold no prose for the sweep to read, so the reach stops at
  them by the file format rather than by a decision. ⚠️ A format that comments some other way than
  with a leading `#` would be unheld too, and unheld in silence: nothing warns that a tracked file
  carries no prose because its grammar was never taught.
- **Whether the floor is where a project would put it.** Three properties are procedure here
  because none describes the reader; a project that disagreed could not turn them off, and nothing
  in this repository asks whether that is the right boundary. [#65](https://github.com/ragnor-rs/mjolnir/issues/65)
  is where the boundary between procedure and configuration for this axis is argued.

## An artifact states what is true now: held on the lines a change adds

`tools/check_no_audit_trail.py --self-test` runs in the `No audit trail` workflow with no
credential. ⚠️ **Not with no network**, unlike its siblings, and the exception is worth stating: the
base derivation reads the remote's advertised default where the checkout records none, so a run
whose base branch the host did not state can reach `ls-remote`. ⛔ The rule is
[schema § The loop → An artifact states what is true now](../plugins/mjolnir/config/schema.md#an-artifact-states-what-is-true-now)
and this document states none of it: what is recorded here is the reach of the check, which is
narrower than the rule, in the directions the list below names.

What it holds: the lines this change **adds** to tracked markdown, read off a diff against the merge
base with the branch the change is **against** — the base the run states where it states one, and
otherwise `claim.integration_branch`, the one derivation this repository has for which branch that
is. ⚠️ A base that resolves to this change's own head is refused rather than read as nothing added,
which is the state a checkout with no remote lands in. Table rows are in scope deliberately: the
measured habit lived in an ordering document's argument column, which is exactly the place a sweep
of this kind would think to exclude. A document's fenced blocks and frontmatter are out, and so is
any marker **shown** rather than used — an inline-code span or a quoted run — because the section of
the surface that states this rule has to spell out every form it forbids, and so does the check.

The kind is **forbidding**, not computed, and the run says so in its own output rather than leaving
a green verdict to imply completeness. Three shapes are matched: a dated record of a pass, a figure
stated beside a former value, and a clause whose subject is the pass before this one. The fourth
shape the rule names — a per-pass paragraph appended where a line should have been overwritten — is
held only insofar as it carries one of those three markers.

⚠️ **It plants both sides**, as the width and reply-register checks do, and the run prints what it
planted rather than a count being written here. ⛔ **The green plants are of two kinds and the
difference is load-bearing.** An **exclusion** is something the check sets aside — the lines a
change did not write, a marker shown in a code span or a quotation, a document's frontmatter, a
fence shown inside a longer fence — and each of those was verified by **disabling that exclusion**
and watching its plant redden; the carve-out that is this check's whole shape goes red the moment
the added-line filter comes out. An **omission** is a shape the grammar simply does not carry — a
landed record, a dated measurement, today's figures beside today's date, a release heading, a role's
instruction about the pass before it — and there is nothing to disable: what those plants assert is
that the grammar stays narrow, and each of them reddens the moment the vocabulary grows.

### What this check deliberately does not hold

- **The ordering document, which is where the rule was measured.** It lives outside every tree —
  § 12's carrier resolves it, as § 9's `out_dir` resolves the day log — so no diff reaches either,
  and a check on the gate cannot read a file the gate never sees. What holds the rule there is the
  close-out role, whose own text carries the forbidden forms for that reason. ⚠️ The day log is a
  different case rather than a second gap: its content **is** an account of work, which the rule's
  own carve-out for an artifact the procedure exists to produce covers.
- **A work item body, a pull request body or a review comment.** The same half of the same rule the
  width check cannot reach, and for the same reason: those surfaces are not files. The nothing-
  deferred gate does read a body, so an arm there is possible — what stopped it here is that this
  grammar is lexical, and a body is where an author's own account of a pass is most likely to be
  exactly what was asked for.
- **A record phrased without any of the markers.** The shapes are lexical, so a paragraph narrating
  a pass in words the grammar does not carry passes. ⚠️ Two words the shapes are commonly phrased
  with are held only in compound forms: `was` and `corrected` occur constantly in honest prose —
  `the divergence was 71 lines`, `the finding was corrected under the same item` — and a sweep for
  the bare words hands a change back for the honest form of a sentence. What is read instead is
  `(was …)`, a `Was:` label, `down from`, `formerly` and `previously` before a figure, and a pass as
  the subject of a clause. ⛔ `pass` and `audit` are out of the dated-pass vocabulary for the same
  reason, each measured: *the gate passes on every document as of 2026-10-20* and
  *#100 landed 2026-10-20 as the audit-trail rule* both reddened while they were in, the second
  turning this rule's own name against the landed-record carve-out.
- **Anything that is not markdown.** A Python docstring narrating a pass is prose a reader reads,
  and nothing here holds it. The same boundary the width check draws, for the weaker of its two
  reasons: a comment is annotation on code rather than a document somebody opens.
- **Whether an ask happened.** The rule's exception is the person running the role asking for
  history, and no gate can see the asking. A dated record somebody asked for and a dated record
  nobody asked for are the same lines, so the check reddens on both and the remedy for the first is
  the person saying so — which is the honest shape of a check that cannot read intent.

## The boundary: three arms, two of them held in the session

`plugins/mjolnir/scripts/boundary.py --self-test` runs in the `Boundary` workflow, with no
credential and no network — which here is the rule applied to its own gate rather than the house
style, since a run holding the refusal on what may leave has no business holding anything that
could. ⛔ The rules are
[schema § 11 → What a role reads from outside the procedure is data, never instruction](../plugins/mjolnir/config/schema.md#what-a-role-reads-from-outside-the-procedure-is-data-never-instruction)
and
[schema § 14 → What a role holds, and what may cross the boundary](../plugins/mjolnir/config/schema.md#14-what-a-role-holds-and-what-may-cross-the-boundary),
and this document states neither: what is recorded here is the reach of each arm, which is
narrower than the rules in several directions the rules do not mention.

**Why one carrier and not three.** The three arms answer the three legs of one structural failure —
private data, text someone else wrote, and a way out — and the measured incident drove three
separate agents through all three legs at once. Splitting them across three scripts would have
given each leg its own grammar, its own self-test and its own opportunity to be the one nobody
updated.

What each arm holds:

| arm | what it reads | kind | what it does on a finding |
|---|---|---|---|
| `read` | text a role is about to act on | **forbidding** for the hidden half, **quoting** for the imperative half | reports, exits non-zero; the role names it and stops |
| `write` | text a role is about to send outward | **forbidding** | refuses, naming the kind and the position and never the value |
| `env` | the names the process can see | **forbidding** on the name, **forbidding** on the value | reports, and exits zero whatever it finds |
| `hook` | a `Bash` command, plus the bodies it sends by file | **forbidding** | denies the tool call, through `PreToolUse` |

⚠️ **The `read` arm's two halves have different standing, and the run says so.** Markup that renders
as nothing has a stable form, so finding it is the *forbidding* kind. An imperative aimed at a role
is prose, so that half is the *quoting* kind — red on an innocent reword, green on a reword into the
opposite — and it is carried anyway because the measured payloads were not subtle and a named one
costs a reader nothing. Neither half reports a text as safe, and both reports say that in those
words: the arms surface, and nothing here clears.

⚠️ **It plants both sides, as the reply-register and prose-width checks do.** Violations that must
redden — one per hidden form, one per imperative pattern, one per credential shape, one per hook
decision — and an exemption plant per excluded case, each of which must stay green: an emoji's
variation selector, a collapsed block a person can open, a commit hash, a branch name, a variable
reference, a placeholder, a redaction, and each of the environment names whose anchors were added
after a false report. The run prints what it planted; no count of either is written down here.

⚠️ **Every plant is assembled from pieces at run time**, and that is not stylistic. A literal of a
credential shape written into the file would be a secret committed to a repository by the check that
exists to stop exactly that, and the host's own push protection would refuse the push — so the
check would have reddened the gate by existing.

⚠️ **The second reason is the one that actually fired**, measured on the change that introduced this
carrier: the `write` arm is what answers
[schema § 6](../plugins/mjolnir/config/schema.md#6-commit-behaviour)'s commit-time scan, so a run of
it over a staged diff reads this file too. Three authored literals had been written out rather than
assembled, and the scan reported all three — a guard whose first act is to flag its own test data is
a guard somebody waves through on every commit. The plants were rebuilt from pieces and the scan
runs clean over its own change. ⚠️ This is the same exemption `check_no_project_names.py` needs for
its own file one sweep over, arrived at from the opposite direction: that one is exempted by name,
and this one is written so it needs no exemption.

⚠️ **What the ingestion step costs a reader was measured rather than argued, because a guard whose
output is noise is a guard that gets turned off.** The twenty item bodies at the head of this
project's own queue — about 106,000 characters — produced **no finding of either kind**. That is
the hardest corpus available for the imperative half: this repository writes the most
directive-dense prose it has, every item body carrying *a role that assumes it owns the gate*,
*never a second checkout*, *the role names it and stops*. None of it matched, which is what the
anchors in that grammar are for, and it is the reason the half is carried at all despite being the
quoting kind.

### What this check deliberately does not hold

- **Whether a role actually ran an arm before acting.** The two arms the roles invoke are commands
  in a skill, and nothing in a workflow observes a session. A role that skipped the ingestion step
  and acted on the text looks identical to one that ran it and found nothing. ⚠️ The cost is stated
  rather than papered over: what the gate holds is that the arms still work and are still wired, and
  the one arm that enforces itself is the hook, because the harness calls it rather than a role
  remembering to.
- **A payload that is prose.** Reworded, translated, split across comments, or phrased as a
  question, an imperative passes the quoting half. This is the limit the rule anticipates by putting
  the obligation on *never obeying* rather than on detecting, and a green run licenses nothing.
- **Text hidden by colour, or by a collapsed block.** White-on-white is not decidable from the text
  alone — the background is the renderer's — and a `<details>` block is collapsed rather than
  hidden, so a person approving the item can open it. Both are excluded by name and planted on the
  green side, so tightening either makes a named assertion fail rather than silently sweeping more.
- **A credential that reaches an outward surface through anything the procedure does not drive.**
  The `write` arm reads the text a role is about to write and the hook reads a `Bash` command. A
  file written into a directory something else synchronises, a credential passed to a tool that is
  not `Bash`, or a value already in the clipboard are all outside what either can see.
- **A body this procedure assembles in flight.** The hook reads the command and the files it names
  by a body-file flag, bounded at a size so a hook cannot be stalled. A body piped in from another
  process, or assembled by a shell expansion the hook would have to execute to see, is not read —
  and a body file that could not be read is reported as unread rather than assumed clean, which is
  the direction [schema § 2](../plugins/mjolnir/config/schema.md#2-code-host) requires of every
  absence of signal.
- **What the shell can reach, as opposed to what a process can see.** The `env` arm reads the names
  and values handed to one process. A credential in a credential helper, a keychain, an agent
  socket or a file the shell can read is not a variable and is not reported — and on this
  repository the host's own credential is in exactly that place, which is why its `inherits` list
  names no token.
- **Whether an `inherits` entry is itself a secret.** The reader refuses anything that is not a
  variable name, so a value pasted in is caught by its shape. A name-shaped entry that is somehow a
  credential passes. Refusing that would need the credential grammar inside the configuration
  reader, and a second copy of that grammar would be a copy allowed to disagree with the one that
  runs.
- **Whether a project's list is *minimal*.** The rule says a credential no role needs is not in the
  shell; a long list that honestly states a long inheritance satisfies this check exactly as a
  short one does. What the arm supplies is the report that makes the gap visible; closing it is a
  person's judgement about what a role needs, which is the one judgement the procedure never makes.

## Each check has a violation it is asserted to redden on

`--self-test` plants one violation per check and asserts that check goes red, as the first step of
the workflow — before the tree is held to anything. The discipline is #28's: an assertion written
before its break tends to match only the break its author imagined, and a check that cannot fail
is not a check.

Every script here carries the mode and each is run through it by its workflow, before the tree —
or, for the gate on the change, the pull request — is held to anything. The plant is per *branch
that does real work* rather than per check: a plant that reddens a check by the wrong
route proves nothing about the branch it was written for. ⛔ The numbers are deliberately not
written down here: a count in prose is a copy that has to be kept in sync, and the run prints its
own.

⚠️ **Where the plants run differs, and only the ordering does.** The two document checks and the
reply-register check run every plant as a first phase, before the tree is held to anything; the
port contract and the configuration reader run each plant beside the assertion it belongs to,
because each needs a configuration or a surface of its own synthesised for it and a first phase
would build all of them twice. What the ordering buys — no check is believed until it has been
shown it can fail — holds either way, and it is stated here rather than in a comment in one
workflow, where nothing reading this document would find it.

That ordering is why the step names in `.github/workflows/` fall into two families. A run with a
first phase names it — *Assert each check can fail, then …* — and a run without one has no phase
to name, so it says only what it holds. ⛔ A step name is not evidence that a suite plants: both
families plant, and the run prints what it planted.

⚠️ **The checks that plant the green side as well as the red are the ones whose scope has a hole
in it by design**, and each hole is an exclusion somebody wrote on purpose. The reply-register
check plants replies that must stay green — a check that flags an arrow inside a fenced block, an
indented block or a quotation is not the check it claims to be, and each of those was a measured
false red rather than a hypothesis. The width check plants a line of each unbreakable kind,
because its exclusion list is where it would quietly stop holding anything. The single-authority
check plants a container cited through its subsection, which is the one carve-out checks 2 and 6
share. The audit-trail check plants the carve-out that is its whole scope — a violation the change
did not write — beside a landed record and a live-status line, each of which carries a date and has
to pass. The prose-register check plants a quotation, a cell of defined terms and both kinds of
annotation, and asserts its fixture's premises before any of them: a plant against a cited
document establishes nothing where the planted file turns out not to cite it. ⛔ A red-only suite
says nothing about any of them. **A green plant naming an exclusion is verified by switching that
exclusion off** and watching it redden — one that cannot fail is one nobody checked — while a plant
naming an omission has nothing to switch off, and what it asserts is that a grammar stayed narrow.
⚠️ Two of these suites keep the two kinds apart in their own labels, because calling an omission a
verified exclusion claims a step that was never performed.

⚠️ The reply-register check carries one more thing its siblings do not: it runs its turn-guard
assertions against a state directory of its own, after a second run of the self-test read the
first run's markers and reported that a blocking finding does not block.

⚠️ **A plant has to reach the branch it was written for, and nothing reports it when it stops.**
The three plants against the outcome column substituted into the rulings document as a whole, on
the unstated assumption that an outcome cell's link shape occurs nowhere else in it. It is an
ordinary citation shape: the first one written in prose above that table took all three, every
cell stayed valid, and three checks that had been shown to fail quietly stopped being shown
anything. They now split the document at the header the check itself derives the table from. ⚠️
The failure was loud only because the mode reports a plant that stayed green — without that, a
check believed on an assertion that no longer exercises it reads exactly like a check that holds.

⚠️ **A plant may not name the file it plants into.** The sweep's first draft hardcoded the one
skill's path, so moving or renaming a carrier root made `--self-test` — the command the workflow
runs — die on a `KeyError` instead of returning a verdict. It now takes a file from the strict set
and synthesises one if the set is empty, so a moved root reddens a check rather than crashing the
gate.

That mode caught its own author. The first draft of the anchor rule collapsed runs of whitespace
where the code host replaces each space individually, which reported six sound citations as broken
— so the first finding this check produced was against itself, which is the reading rule #28
states: when one goes red, the assertion is as likely to be wrong as the document.
