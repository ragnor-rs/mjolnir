# How the single-authority claim is held

[`../plugins/mjolnir/config/schema.md`](../plugins/mjolnir/config/schema.md) declares itself the
single statement of every rule and flow, and this document and its sibling explain or record
without being a second authority. This document states none of the rules either. It records what
the gate checks, which kind of check each one is, and — the part worth reading — what it
deliberately does not check.

The check is `tools/check_single_source.py`, run by the `Checks` workflow on every pull request
and every push to the default branch, and stated in this repository's own `host.checks`.

## Why this is a check rather than a convention

Every other duplication in this backlog is one the toolkit exists to delete. This one is the
toolkit's own. Four stores describe the procedure here — the schema, this document, the two
beside it, and the issue bodies — and all but the first are explicitly not authorities. Nothing
held them to that. A rule restated in a document, a section nothing motivates, a ruling pointing
at a home its outcome has since left: each reads as fine in review, and each is the defect this
repository was built to call a defect.

Three were in the tree when the check was written, which is the argument for it:

- `version` was in all five configurations and declared nowhere in the schema — a key every
  adopter writes, that the single statement of the surface did not name. It is now
  [schema § The file itself](../plugins/mjolnir/config/schema.md#the-file-itself).
- One ruling's outcome lived in the README, which stated that rule citing no schema section, so
  the README was a second authority for exactly one rule. It is now
  [schema § 10](../plugins/mjolnir/config/schema.md#10-invocation), which the README cites.
- Two rulings pointed at "the filing role's work item" and "the deploy role's work item" with no
  number, so nothing could resolve whether the outcome had moved. They now name #7 and #13.

## The three kinds, and why one of them is absent

[Work item #28](https://github.com/ragnor-rs/mjolnir/issues/28) classifies the checks themselves,
from two independent implementations that reached the same conclusion: **computed** checks derive
the property and cannot be fooled by a reword; **forbidding** checks assert a name or pattern must
not appear, and are sound when the thing forbidden is stable; **quoting** a sentence back at the
file it came from fails in both directions. Every check below is one of the first two.

| # | Check | Kind |
|---|---|---|
| 0 | Every markdown document that may cite the schema has a declared role in the script | forbidding |
| 1 | Every `schema.md#…` citation resolves to a real heading | computed |
| 2 | Every `##`-level schema section is cited by at least one document | computed |
| 3 | Every ruling's outcome cell resolves, to the schema or to a numbered work item | computed |
| 4 | A ⛔ paragraph in a document carries a schema citation | forbidding |
| 5 | Every configuration's top-level key set equals the one the schema declares | computed |

Check 2 is the one that does the most work, because it runs in the direction nobody remembers to
check by hand: a section added to the schema with nothing recording why it has that shape fails
the build at the moment it is added, rather than being noticed a year later by someone wondering
whether it is load-bearing.

Check 4 is scoped to the README and `docs/`, not to `skills/`. That is the schema's own boundary:
a fact that cannot be expressed on the surface is either procedure, in which case it belongs in a
skill, or a project-specific skill. A skill therefore states procedure for its own role
legitimately, and the hazard there is a *value* rather than a rule —
[#19](https://github.com/ragnor-rs/mjolnir/issues/19)'s sweep.

## The check must not become one more copy of the principles

⛔ A check that hardcoded "nine roles", "five axes", "four facets with absent cases" would have to
be edited on every change to
[`schema.md`](../plugins/mjolnir/config/schema.md) — this repository's own thesis violated in its
own gate, and a copy that has to be kept in sync is the defect rather than the maintenance burden.

So the script **derives every expectation from the schema at run time** and hardcodes grammar
only:

| Derived, at run time | Hardcoded |
|---|---|
| the section list, from the headings | markdown heading syntax |
| the anchor set, from the same | the code host's slug rule |
| the key vocabulary, from the fenced blocks | yaml top-level key syntax |
| the citation targets, from the anchors | the citation and outcome-cell forms |
| | the binding marker, and which document plays which role |

Adding a section to the schema grows what the script expects with no edit to the script, and
check 2 reddens until a document motivates it. Deleting one shrinks it the same way. **The only
thing that forces an edit is a change of grammar** — a new marker, a new citation form, a new
kind of document — and that residue is made loud rather than silent by check 0: a document added
under `docs/` with no declared role fails the build instead of being quietly skipped.

This is [#28](https://github.com/ragnor-rs/mjolnir/issues/28)'s own finding applied here, and the
sixth instance of the pattern counted in
[`configuration-surface.md`](configuration-surface.md#the-strongest-argument-for-extraction-is-not-borrowed):
the graph a machine walks and the statement a person maintains are deliberately one thing, read
from one place.

## What it deliberately does not check

Stated, because an unstated limit reads later as coverage.

- **Fidelity.** Whether a document's paraphrase still matches the section it cites is the
  *quoting* kind: red on an innocent reword, green when a claim is reworded into its opposite.
  No check here attempts it. It stays a reviewer's job, which is why a document paraphrases as
  little as it can and cites instead.
- **Issue state.** Check 3 resolves the *form* of a work-item cell, not whether that issue is
  still open. Reading the tracker needs a credential, and per
  [#50](https://github.com/ragnor-rs/mjolnir/issues/50) this workflow holds none of any kind. So
  a ruling whose work item landed without its outcome moving into the schema is caught by a
  reader, not by the gate — the one gap in check 3 worth knowing about.
- **Key subtrees.** Check 5 holds the top level only. Per-tracker blocks live in `examples/` by
  the schema's own
  [§ 3](../plugins/mjolnir/config/schema.md#3-tracker-port), so a deeper comparison would need an
  exception per tracker kind. A bounded check that is sound beats a deep one that needs
  carve-outs, and `tracker.labels` being undeclared is the known consequence.
- **Issues and pull requests.** The fourth store is not a file and cannot be swept from a gate,
  which is the same reason [#19](https://github.com/ragnor-rs/mjolnir/issues/19) records for
  lettering projects A–F in the documentation.

## Each check has a violation it is asserted to redden on

`--self-test` plants one violation per check and asserts that check goes red, as the first step of
the workflow — before the tree is held to anything. The discipline is #28's: an assertion written
before its break tends to match only the break its author imagined, and a check that cannot fail
is not a check.

That mode caught its own author. The first draft of the anchor rule collapsed runs of whitespace
where the code host replaces each space individually, which reported six sound citations as broken
— so the first finding this check produced was against itself, which is the reading rule #28
states: when one goes red, the assertion is as likely to be wrong as the document.
