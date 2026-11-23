---
name: cut-release
description: Turn landed work into a released version — the version asked for rather than derived, every file that carries one bumped from configuration without knowing the stack, a changelog written or refused to CI, the whole edit made together or not at all, and the go asked for where a package spends the version for ever. Use when asked to cut a release, bump the version, tag a version, write the changelog entry, or publish a version of this project.
argument-hint: "[<the version to cut>]"
---

# Cut a release

The outcome is **one version, written in every file this project says carries one**, with the
changelog written or its refusal named, and everything the release did not do — a tag nobody made,
a package nobody published, a grouping nobody closed — named in the reply.

⛔ **This role states no version scheme, no build file's syntax, no tag format, no registry and no
publishing command.** Every one of those is the project's, reached through what its configuration
states and never learned here, by
[`§ What the procedure models`](../../config/schema.md#what-the-procedure-models-and-what-it-only-names-and-calls).
⚠️ **Which is why no pattern, no replacement and no version-carrying file's path appears anywhere in
this file**: the one path below is this toolkit's own carrier, and it is the thing that reads a
project's instead.

⛔ **The facet is [`§ 34`](../../config/schema.md#34-the-files-that-carry-a-version-and-what-cutting-a-release-writes)
and this file states none of it again.** A copy of a rule here is a second authority allowed to
disagree with the one the reader performs.

⛔ **And it is not the deploy role.** That one names a target environment and is refused without an
explicit go for a live one; this one names a **version** and is refused without landed work to carry
it. The distinction is stated where both of them can read it, at
[`§ 34`](../../config/schema.md#34-the-files-that-carry-a-version-and-what-cutting-a-release-writes),
rather than in either role.

## 1. Resolve, and say what was resolved

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/config.py"
```

⛔ **Say which project was resolved before anything else**, as every role on this route does: run
from a sibling project with a configuration of its own, this role cuts **that** project's release
and edits files in **that** repository.

⛔ **Read the `unavailable` list before acting on anything.** A project stating `release.carrier:
none` is a **stop naming that key** — no file here carries a version, which
[`§ 34`](../../config/schema.md#34-the-files-that-carry-a-version-and-what-cutting-a-release-writes)
makes a stated configuration rather than a gap, and ⛔ **never an invitation to go looking for a
file that might.** ⚠️ **It is also not a statement that nobody releases this project**: somebody may
cut one by hand, which the configuration reports nothing about and neither does this role.

⚠️ **Which code root the files are in is § 1's**, and the carrier below resolves it: a project with
several roots has a release per root, and the reply names which one was edited.

## 2. Which version

**Named on the invocation** — the argument is the version, as the project writes it.

**Nothing named** — ⛔ **ask, showing what every file carries now.** The reading is the carrier's:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/release.py" --skills-root <the skills root>
```

What comes back is each file, which edit it takes, whether it is marked optional, and **the version
it carries at this moment** — read out of that file's own capture, which is the only thing this
route ever learns about a project's scheme.

- ⛔ **The version is never derived.** What the next one is depends on what landed, and no rule here
  has that as an input: a role that bumped a digit would be choosing a project's scheme for it.
  ⚠️ **Nor is the ask a formality** — show what landed since the version the files carry, so the
  person answering is choosing from evidence rather than confirming a guess.
- ⛔ **Two files disagreeing about the current version is a stop with both named**, not a majority
  to be taken: the carrier reports it, and a release cut over it writes one version where the
  project had two and hides which was right.
- ⚠️ **A file whose pattern matches nothing is the same stop**, and it is reported against the
  **pattern** rather than against the file — the file is there, and what is wrong is the
  configuration that describes it.

## 3. Landed work is the precondition, and this role does not assume it

⛔ **A release carries what has landed, and work that has not is not in it.** Which items those are
is read where a deploy's batch is read —
[`§ 33 → The batch`](../../config/schema.md#the-batch-and-the-two-ways-of-assembling-one-that-are-wrong)'s
rule rather than a second command here: **the tracker's answer and the project's own command,
neither alone**.

- ⛔ **Where the project states no such command, the batch is reported as unread** and never as
  empty, by [`§ 2`](../../config/schema.md#2-code-host)'s rule that absence of signal is not an
  answer. The release may still be cut; what the reply may not say is that it carried nothing.
- ⚠️ **An open change under the version being cut is a stop for the person**, naming it: a version
  that ships without it is a version whose number already means the wrong thing.

## 4. The plan, which writes nothing

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/release.py" plan \
  --skills-root <the skills root> --version <the version>
```

⛔ **Nothing is written by this step** — it reads the tree and says, per file, what the edit would
do and whether it can be made at all.

| what the plan says | what this step does |
|---|---|
| every file holds | go on to step 5 |
| a file is missing and marked optional | **nothing** — that is the flag working, and the reply names the file as skipped |
| a file is missing and is not marked | **stop**, with the file named |
| a pattern matches nothing, or matches two versions | **stop**, with the pattern named |
| the changelog already carries this version | **stop** — a release somebody started, which this role has no standing to finish |

⛔ **A stop here is earlier than any write, and that ordering is the rule rather than an
implementation detail**
([`§ 34`](../../config/schema.md#the-files-a-version-is-written-in-and-the-two-kinds-of-edit)): a
release with half its files bumped is worse than a release not cut, because the half that moved is
what every later reader believes.

## 5. Write the files, together

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/release.py" apply \
  --skills-root <the skills root> --version <the version>
```

⛔ **One call, and every file or none.** The carrier re-establishes the plan, composes each file's
new text, and only then writes — so a plan that stopped wrote nothing, and the reply reports the
files it named as written rather than the files it meant to write.

⚠️ **What this does not promise is atomicity against a crash**, which the carrier states in its own
report: the write can be interrupted between two files. ⛔ **So the reply names what was written**,
and a run that was interrupted is reported as that rather than as a release that did not happen.

## 6. The changelog, written or refused

⛔ **Where the project states that CI owns the changelog, this role writes none — and says so.**
That is the one absence on this route that changes what the procedure **does** rather than what it
reads
([`§ 34`](../../config/schema.md#the-changelog-ci-owns-which-inverts-the-role)), and a role that
wrote the file anyway would produce a conflict on every single release.

⛔ **Said rather than skipped silently.** A reply that does not mention the changelog reads as a
release that wrote one, and the person who then goes looking for the entry finds nothing and no
account of why.

**Where this role does write it**, the entry's language, register and audience are
[`§ 8`](../../config/schema.md#8-language-register-audience--per-artifact-not-per-project)'s, per
artifact — ⛔ **read there rather than defaulted here.** An entry for a user-facing release and one
for an internal version are different texts, and which this is is not this role's to decide.
⚠️ **A project stating nothing for that artifact has stated nothing**, so the entry is written to
`language.repo` and the reply says the register was unstated.

⛔ **And what goes in the entry is what landed, read off the batch in step 3** — never off the
diff's own shape, and never a sentence about the release having been cut, which is
[`§ An artifact states what is true now`](../../config/schema.md#an-artifact-states-what-is-true-now)
applied to the one artifact this role authors.

## 7. Ask, once, where the act is the person's

⛔ **One question, for this release, and `publishes_packages` is what decides whether it is put.**
The test is
[`§ The loop`](../../config/schema.md#what-carries-the-item-forward-and-where-it-stops-to-ask)'s —
whether the act is the person's — and
[`§ 34`](../../config/schema.md#what-a-release-publishes-and-what-this-section-does-not-carry) is
where this role reads the answer. ⛔ **An earlier go clears nothing**: an approval obtained for
another version is not one for this.

| the facet says | what this step does |
|---|---|
| `publishes_packages: true` | **asks**, and silence is not a yes: nothing is published, the files stay bumped, and the reply says the question went unanswered |
| `publishes_packages: false` | **does not ask** — nothing leaves this repository, and a question there is the interruption § The loop retired |

**Show, in the question:** the version, every file that was written, what the batch says the release
carries, and ⛔ **that a published version cannot be reused**, which is the whole of why the question
exists.

⛔ **The publishing command is the project's and is not composed here.** Where the project states
one, it is run; where it does not, the reply reports that the version is bumped and **nothing was
published**, naming it.

## 8. The tag, and what this role does not close

⛔ **The tag is the project's act and this role does not invent its format.** Where the project
states nothing about tagging, the reply says the version is written in the files and **no tag was
made** — never that the release is complete.

⚠️ **The tag is also not what step 7 asks about**, and that is stated rather than left as an
omission: a tag can be moved and a published artifact cannot
([`§ 34`](../../config/schema.md#what-a-release-publishes-and-what-this-section-does-not-carry)).
⛔ **Which is not a claim that a tag is reversible** — only that the irreversibility this route asks
about is measured on the registry.

⛔ **Closing whatever the release corresponds to is not this role's**, by the same section: it is
[`§ 4.8`](../../config/schema.md#48-grouping--what-a-set-of-items-is-planned-into)'s question, and
what this role owes is to **name the grouping it did not close** rather than to leave a reader
reading silence as a close.

## 9. The reply

Register and language are
[`§ 8`](../../config/schema.md#the-reply-to-the-person-running-a-role)'s — the outcome first, then
the facts, with a table where the content enumerates.

- **the verdict, first sentence** — cut · cut and not published · stopped, and on what;
- **the version, and the version it replaced** — ⛔ never the new one alone, which says nothing a
  reader can check against the files they meant;
- what was resolved — the project, the configuration file, and **which code root's files were
  edited**;
- **every file**, with what happened to it: written, skipped as optional and missing, or the thing
  that stopped it;
- **the changelog** — written, or ⛔ **refused because CI owns it**, named either way;
- **what the batch says the release carries**, and ⛔ **that the project's own command is its only
  source of candidates**, so that *nothing landed* and *nobody looked* are not one sentence;
- **whether the go was asked for and what it answered**, with `publishes_packages` named as the
  reason it was or was not;
- ⛔ **what the release did not do** — no tag made, nothing published, no grouping closed, work
  still open under this version;
- ⛔ anything that could not be established, **named rather than omitted**
  ([`§ 11`](../../config/schema.md#a-report-names-what-it-could-not-establish));
- ⛔ anything that needs the person running this, **asked with the options**
  ([`§ Nothing is deferred`](../../config/schema.md#nothing-is-deferred)): a version nobody chose,
  two files disagreeing about the current one, a file the configuration names and the tree does not.
  Nothing is noted for later.

## What this carrier is

```yaml
# carrier: release
```

⛔ **Read from this file and declared nowhere else**, by
[`§ Whether a project can adopt`](../../config/schema.md#whether-a-project-can-adopt-this-procedure-at-all-and-the-check-that-answers-it).
