# How the single-authority claim is held

[`../plugins/mjolnir/config/schema.md`](../plugins/mjolnir/config/schema.md) declares itself the
single statement of every rule and flow, and this document and its sibling explain or record
without being a second authority. This document states none of the rules either. It records what
the gate checks, which kind of check each one is, and — the part worth reading — what it
deliberately does not check.

The check is `tools/check_single_source.py`, run by the `Checks` workflow on every pull request
and every push to the default branch, and stated in this repository's own `host.checks`.

The same workflow runs a second script, `tools/check_no_project_names.py`, which holds a
different claim — that this repository names no other project, and that nothing carrying
procedure carries a value. It is recorded in [its own section](#the-second-sweep-naming-no-other-project)
below, because the two claims share this document's discipline of stating every limit and not
its subject.

## Why this is a check rather than a convention

Every other duplication in this backlog is one the toolkit exists to delete. This one is the
toolkit's own. The procedure is described in the schema, in the README, in the three documents
under `docs/`, in each shipped skill, and in the issue bodies — and only the schema is an
authority. Nothing held the rest to that. A rule restated in a document, a section nothing
motivates, a ruling pointing at a home its outcome has since left: each reads as fine in review,
and each is the defect this repository was built to call a defect.

Three were in the tree when the check was written, which is the argument for it:

- `version` was in all five configurations and declared nowhere in the schema — a key every
  adopter writes, that the single statement of the surface did not name. It is now
  [schema § The file itself](../plugins/mjolnir/config/schema.md#the-file-itself).
- One ruling's outcome lived in the README, which stated that rule citing no schema section, so
  the README was a second authority for exactly one rule. It is now
  [schema § 7 → Invocation](../plugins/mjolnir/config/schema.md#invocation), which the README
  cites. It sits as a subsection of the carrier axis rather than as a tenth numbered section,
  because every numbered section is a configuration facet opening with a `yaml` block and this
  is procedure — the same placement the authorship rule has under § 6.
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
| 2 | Every `##`-level schema section is cited by at least one document | `##` only, not `###` | computed |
| 3 | Every ruling's outcome cell resolves, and its § number and its link agree | the `Outcome lives in` column | computed |
| 4 | A ⛔ statement carries a citation naming a **section** | documents that explain or record | forbidding |
| 5 | Every configuration's top-level key set equals the one the schema declares | top level only | computed |

Check 2 is the one that does the most work, because it runs in the direction nobody remembers to
check by hand: a section added to the schema with nothing recording why it has that shape fails
the build at the moment it is added, rather than being noticed a year later by someone wondering
whether it is load-bearing. ⚠️ It holds `##` sections only. Two `###` subsections are motivated by
no document today and the gate is green on them, so the direction is enforced one level less
deeply than it reads.

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

## The check must not become one more copy of the principles

⛔ A check that hardcoded "nine roles", "five axes", "four facets with absent cases" would have to
be edited on every change to the surface whose
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
- **Issue state.** Check 3 resolves the *form* of a work-item cell, not whether that issue is
  still open. Reading the tracker needs a token scope, and per
  [#50](https://github.com/ragnor-rs/mjolnir/issues/50) this workflow is granted none: its
  `permissions` are empty and the checkout is told to persist no credential. So a ruling whose
  work item landed without its outcome moving into the schema is caught by a reader, not by the
  gate — the one gap in check 3 worth knowing about, and a deliberate trade against holding a
  credential to close it.
- **Key subtrees.** Check 5 holds the top level only. Per-tracker blocks live in `examples/` by
  the schema's own
  [§ 3](../plugins/mjolnir/config/schema.md#3-tracker-port), so a deeper comparison would need an
  exception per tracker kind. A bounded check that is sound beats a deep one that needs
  carve-outs, and `tracker.labels` being undeclared is the known consequence.
- **Issues and pull requests.** That store is not a file and cannot be swept from a gate at all,
  which is the same reason [#19](https://github.com/ragnor-rs/mjolnir/issues/19) records for
  lettering projects A–F in the documentation.
- **Configurations outside the globs.** A configuration added where `CONFIG_GLOBS` does not look
  is skipped. Check 0's loud-residue argument covers documents; for configurations the guard
  asserts only that each glob matched something, which catches a moved directory but not a new
  one somewhere else.

## The second sweep: naming no other project

The convention in the README — that this repository names no *other* project and that nothing
under `skills/` carries a value — says the **search is the check** rather than a reading of the
procedure. `tools/check_no_project_names.py` is that search, as the second job of the same
workflow. Every check in it is of the *forbidding* kind, so the whole script stands or falls on
whether the thing forbidden has a stable form.

Two scopes. The repository-wide one looks for what identifies someone else's project; the strict
one — `skills/` and `hooks/`, never the whole tree — looks for a value, a tracker or a stack in
text that is supposed to be procedure.

| # | Check | Scope | Kind |
|---|---|---|---|
| 0 | No repository but this one's is named, as a URL, an install-command argument or a `repo:` value | every tracked text file | forbidding |
| 1 | No path under a home directory | same | forbidding |
| 2 | No address | same | forbidding |
| 3 | No identifier that resolves on a tracker — a Jira key, a Trello object id, either service's URL | same | forbidding |
| 4 | The strict set matched a file at all | `skills/`, `hooks/` | computed |
| 5 | No tracker is named | the strict set | forbidding |
| 6 | No package manager, task runner, build tool, checker, manifest or lockfile; no directory change prefixing a command, no directory flag, no absolute path | the strict set | forbidding |
| 7 | No value any configuration supplies | the strict set | forbidding |

**Two rules are what make a forbidding sweep of prose sound**, and they are the part worth reading:

1. **A stack token counts only inside a code span or a fenced block.** `make`, `go`, `task`,
   `just`, `stack`, `bundle`, `mix` and `pod` are ordinary English words in prose and unambiguous
   commands in a code span. A sweep of prose for them would redden on a reworded sentence, which
   is the *quoting* failure this document already rules out.
2. **A value counts only as a whole code span or a whole quoted string.** A value written as a
   value stands alone in its span. So `` `In Progress` `` is a status word and `"CI went green"`
   — quoted in the day-log skill as an example of what not to write — is not a workflow name; and
   a status vocabulary of `open` and `closed` does not forbid the word "opening".

It derives what it can, for the reason stated above about the check not becoming one more copy:

| Derived, at run time | Hardcoded |
|---|---|
| the one permitted slug, from `host.repo` in this project's own configuration | the host-URL, address and tracker-identifier grammars |
| the tracker names, from the surface's `kind` alternatives and every configuration's declared kind | the closed list of stack tool names |
| the forbidden value set, from the configurations themselves | which leaf keys of a configuration carry a project's fact |
| the file list, from `git ls-files` | the code-span and quoted-string forms of rules 1 and 2 |

Reading the forbidden values out of the configurations is what makes the acceptance item's pair
work in opposite directions: **a new example configuration adds to what is forbidden under
`skills/` instead of tripping anything, and a status word added to a skill reddens the build.**
Both were measured rather than reasoned about.

### Three exceptions, encoded rather than assumed

A literal reading of the convention would forbid all three, so each is in the script:

- **`config/examples/`** is whole example configurations and is data rather than procedure. It is
  the one place a concrete status word or label prefix is written down — the surface's own
  [boundary](../plugins/mjolnir/config/schema.md#the-configuration-surface) — and it is where the
  sweep reads the forbidden set *from*. The strict set asserts that nothing under `skills/`
  carries a value regardless.
- **This repository's own slug**, derived rather than listed. Removing `host.repo` from the
  configuration reddens the build rather than quietly permitting every slug, which is one of the
  planted violations.
- **The public plugin cited as prior art.** It is an artifact rather than a project in scope, and
  it sits in a one-entry table in the script with its reason beside it, so a second entry means
  editing that table and saying why. Emptying the table reddens the build on the live citation —
  measured, so the carve-out is known to be load-bearing rather than decorative.

`docs/` is deliberately outside the strict set: it quotes the measurements the surface was derived
from and has to keep naming the build tool that reported a cached pass as work done. A rule that
forbade a tool name in a measurement would forbid the evidence. `tools/` is outside it too — a
script that forbids a list of tokens necessarily writes every one of them down.

### What this sweep deliberately does not check

- **A bare slug in prose.** `owner/repo` and `docs/single-source-of-truth.md` have the same shape,
  so the sound forms are the URL, the install-command argument and the `repo:` value. A workflow's
  `uses: actions/checkout@v4` is a third shape it does not read, and a slug written bare in a
  sentence is a reviewer's catch.
- **A person's name, a bare label, a milestone title, an assignee handle, a service name.** None
  has a stable form, and forbidding a list of them would be a list to keep in sync. This is the
  same reason projects are lettered A–F in the documentation: the convention is held by what the
  documents *don't* contain, and the counts carry the argument instead.
- **A language interpreter.** `python3` is on no list, and `python3 <day_log.script>` in the
  day-log skill is the one live instance of one. ⚠️ Whether a configured script is a path the
  procedure prefixes with an interpreter, or a command the procedure merely runs, is
  [#65](https://github.com/ragnor-rs/mjolnir/issues/65)'s and
  [#66](https://github.com/ragnor-rs/mjolnir/issues/66)'s ruling about what configuration carries.
  This check does not pre-empt it by reddening, so until that lands the interpreter named in a
  skill is a known hole — stated, because an unstated limit reads later as coverage.
- **`hooks/`.** It is declared as a strict root and matches no file today; the hooks that enforce
  the loop are [#16](https://github.com/ragnor-rs/mjolnir/issues/16). The run prints each declared
  root that swept nothing rather than reporting green over it, and check 4 fails if the strict set
  empties altogether.
- **Issues and pull requests**, for the same reason check 3 above cannot read issue state: that
  store is not a file, the workflow holds no credential, and a reviewer covers it.

## Each check has a violation it is asserted to redden on

`--self-test` plants one violation per check and asserts that check goes red, as the first step of
the workflow — before the tree is held to anything. The discipline is #28's: an assertion written
before its break tends to match only the break its author imagined, and a check that cannot fail
is not a check.

Both scripts carry the mode and both are run through it by the workflow: 13 planted violations for
the single-authority checks, 21 for the sweep. The count is above the number of checks in each
because the plant is per *branch that does real work* — a plant that reddens a check by the wrong
route proves nothing about the branch it was written for.

That mode caught its own author. The first draft of the anchor rule collapsed runs of whitespace
where the code host replaces each space individually, which reported six sound citations as broken
— so the first finding this check produced was against itself, which is the reading rule #28
states: when one goes red, the assertion is as likely to be wrong as the document.
