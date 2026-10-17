# How the single-authority claim is held

[`../plugins/mjolnir/config/schema.md`](../plugins/mjolnir/config/schema.md) declares itself the
single statement of every rule and flow, and this document and its sibling explain or record
without being a second authority. This document states none of the rules either. It records what
the gate checks, which kind of check each one is, and — the part worth reading — what it
deliberately does not check.

The check is `tools/check_single_source.py`, run by the `Checks` workflow on every pull request
and every push to the default branch, and stated in this repository's own `host.checks`.

A second script, `tools/check_no_project_names.py`, holds a different claim — that this repository
names no other project, and that nothing carrying procedure carries a value. It runs in its own
`Names no other project` workflow, and is stated in `host.checks` as its own entry: a
`host.checks` entry states one mirrored command, so a second job of `Checks` would have been a
second command with nowhere on the surface to live. It is recorded in
[its own section](#the-second-sweep-naming-no-other-project) below, because the two claims share
this document's discipline of stating every limit and not its subject.

`plugins/mjolnir/scripts/check_reply_register.py` holds the register of a role's reply, and it is
the one here that does not run on the gate at all. It is in
[its own section](#the-replys-register-held-in-the-session-not-on-the-gate) too, and for the same
reason: whatever holds a claim here states what it leaves alone. ⚠️ No count of these scripts is
written down, here or anywhere — a count in prose is a copy, and three open changes were each
adding themselves to this document as "the third" when it was.

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
| 2 | Every `##`-level schema section is cited by at least one document | `##` only, not `###` | computed |
| 3 | Every ruling's outcome cell resolves, and its § number and its link agree | the `Outcome lives in` column | computed |
| 4 | A ⛔ statement carries a citation naming a **section** | documents that explain or record | forbidding |
| 5 | Every configuration's top-level key set equals the one the schema declares | top level only | computed |

Check 2 is the one that does the most work, because it runs in the direction nobody remembers to
check by hand: a section added to the schema with nothing recording why it has that shape fails
the build at the moment it is added, rather than being noticed a year later by someone wondering
whether it is load-bearing. ⚠️ It holds `##` sections only, so a `###` subsection that no
document motivates passes — and some do today, including a ⛔ rule of its own. The direction is
enforced one level less deeply than it reads. No number is given here on purpose: a count of them
is a fact about the schema, and a copy of it in this document would go stale on the next
subsection either way, green.

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
   rule 1: they would shift the pairing of every span after them.

It derives what it can, for the reason stated above about the check not becoming one more copy:

| Derived, at run time | Hardcoded |
|---|---|
| the one permitted slug, from `host.repo` in this project's own configuration | the host-URL, address and tracker-identifier grammars |
| the tracker names, from the `kind` alternatives of the surface's **tracker block** and every configuration's declared kind | the closed list of stack tool names |
| the forbidden value set, from the configurations themselves — this project's own included | which leaf keys of a configuration carry a project's fact |
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
- **The public plugin cited as prior art.** It is an artifact rather than a project in scope, and
  it sits in a one-entry table in the script with its reason beside it, so a second entry means
  editing that table and saying why. Emptying the table reddens the build on the live citation —
  measured, so the carve-out is known to be load-bearing rather than decorative.

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
- **A bare all-caps value inside an example configuration**, per the first exception above. The
  residue is narrow — an example whose status words are upper-case — and the alternative was
  dropping `OWNER/REPO` and `KEY` out of the placeholder set.
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

## Beside the document checks: the tracker port's own contract

⚠️ No count of the scripts is carried here. The two above hold a document claim and are what this
document was written for; the rest hold a module or a rule — `plugins/mjolnir/scripts/config.py`,
the configuration reader, whose own checks are its work item's; the reply-register hook recorded
in the next section; and the port contract recorded in this one. Each carries its own workflow and
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

- **That an adapter is correct.** No implementation is installed yet — the three are their own
  work items — so the available-capability branch is proved against a double that implements a
  subset, not against a tracker. What the contract holds is the shape: a declared operation is
  performed by the implementation, an undeclared one falls back.
- **Any module but the contract.** `plugins/*/scripts/` sits outside the sweep's strict set,
  which that sweep argues in stack terms — an implementation is written in some language and
  saying so names the toolkit's stack rather than a project's. It gives no reason to exempt a
  module from the *tracker*-name rule; that exemption is an artifact of the strict set being
  path-shaped. So the contract asserts the rule of **itself**, and nothing holds the reader beside
  it or an adapter module to come — where a kind's name is legitimate anyway. A carrier root,
  where a role's text lives, is still swept by check 6 above, which is the half of this that
  matters for a shared role.
- **That a fallback is the right fallback.** Whether writing a gate result into a description is
  what a project wants where comments are impossible is a judgement the measurement behind it
  carries, not something a check can read. This is the *fidelity* limit one claim over.

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
| Length | No text is compressed into an arrow chain — two arrows sharing an operand | forbidding | **blocks**, once per turn |
| Emphasis | Emphasised spans against the reply's own prose line count | computed | reports |
| Register | A closed list of dramatic words, and exclamations, over a density | forbidding, over a density | reports |
| Uncertainty | A closed list of hedges, over a density | forbidding, over a density | reports |
| Structure | — | — | nothing; see below |

**What blocks, and why the rest does not.** The first two forbid a thing whose form is stable and
whose presence is the defect: a preamble form is a phrase, and a chain is two arrows sharing an
operand. A finding there is a fact about the text, so it hands the turn back.

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
make. A payload carrying no turn at all cannot be guarded, so it reports and **says that it could
not guard** rather than returning the same answer as a turn that has had its hand-back.

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
- **Whether the reply was a role's at all.** The hook fires on every reply in a session where this
  plugin is enabled, and nothing in a `Stop` payload says whether a role was running. So the
  register is held more widely than the surface states it — in the safe direction here, and stated
  because an unstated limit reads later as coverage. ⚠️ That direction is a property of this one
  rule rather than of hooks, and it does not survive the next one:
  [#87](https://github.com/ragnor-rs/mjolnir/issues/87) is where a hook's own role is settled, and
  it blocks [#16](https://github.com/ragnor-rs/mjolnir/issues/16), whose guards and leases are
  **wrong** rather than merely wide when they fire outside their role.
- **A reply that was never sent as text.** A turn that ends in a tool call carries no final
  message, and the hook answers nothing rather than guessing.
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

## Each check has a violation it is asserted to redden on

`--self-test` plants one violation per check and asserts that check goes red, as the first step of
the workflow — before the tree is held to anything. The discipline is #28's: an assertion written
before its break tends to match only the break its author imagined, and a check that cannot fail
is not a check.

Every script here carries the mode and each is run through it by its workflow, and the plant is
per *branch that does real work* rather than per check — a plant that reddens a check by the wrong
route proves nothing about the branch it was written for. ⛔ The numbers are deliberately not
written down here: a count in prose is a copy that has to be kept in sync, and the run prints its
own.

⚠️ **Where the plants run differs, and only the ordering does.** The two document checks run every
plant as a first phase, before the tree is held to anything; the port contract runs each plant
beside the assertion it belongs to, because each needs a configuration or a surface of its own
synthesised for it and a first phase would build all of them twice. What the ordering buys — no
check is believed until it has been shown it can fail — holds either way, and it is stated here
rather than in a comment in one workflow, where nothing reading this document would find it.

⚠️ **The reply-register check's plants carry two things its siblings' do not**, because what it
holds afterwards is a rule rather than a tree. It plants replies that must stay **green** as well
as ones that must redden — a check that flags an arrow inside a fenced block, an indented block or
a quotation is not the check it claims to be, and each of those was a measured false red rather
than a hypothesis. And it runs its turn-guard assertions against a state directory of its own,
after a second run of the self-test read the first run's markers and reported that a blocking
finding does not block.

⚠️ **A plant may not name the file it plants into.** The sweep's first draft hardcoded the one
skill's path, so moving or renaming a carrier root made `--self-test` — the command the workflow
runs — die on a `KeyError` instead of returning a verdict. It now takes a file from the strict set
and synthesises one if the set is empty, so a moved root reddens a check rather than crashing the
gate.

That mode caught its own author. The first draft of the anchor rule collapsed runs of whitespace
where the code host replaces each space individually, which reported six sound citations as broken
— so the first finding this check produced was against itself, which is the reading rule #28
states: when one goes red, the assertion is as likely to be wrong as the document.
