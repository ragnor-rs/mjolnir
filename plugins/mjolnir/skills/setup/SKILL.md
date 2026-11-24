---
name: setup
description: Write a project's configuration by asking for it rather than by hand — the question set derived from the toolkit's own surface, the code host and the tracker interrogated for what can be read, a menu wherever a vocabulary is published, an absence captured as a stated decision, a value a repository may not hold routed outside it, and the file edited key by key rather than re-rendered. Use when adopting the toolkit in a project that states no configuration yet, when asked to configure a project, to set up mjolnir here, to write or fix `.claude/mjolnir.yaml`, or to answer a facet a role reported as unavailable.
argument-hint: "[<the skills root to configure, where it is not this directory>]"
---

# Write a project's configuration

**One file is what adopting this toolkit costs a project, and this role is how that file gets
written.** ⛔ **What this role is, what it may not do, and every property of asking it is held to
are
[`§ What a project is asked`](../../config/schema.md#what-a-project-is-asked-and-the-one-file-the-answers-are-written-into)'s**,
and ⛔ **this file carries no copy of any of it** — read that section, then this one. What this file
adds is the order the steps run in, which command answers each, and what to do with each answer.

⛔ **The question set is not here and is not anywhere else either.** It is derived from the
surface's own key inventory when the carrier runs, which is that section's first rule: a facet the
surface states and no question reaches is a **bug in the carrier**, reported by its own suite, and
never a facet this role asks a person to hand-write.

⛔ **This role writes one file, and a second only where
[`§ 28`](../../config/schema.md#28-a-configured-value-a-repository-may-not-hold) applies.** It
writes nothing to the tracker and nothing to the code host: every reading it takes is a read, and a
step that labelled, filed or moved anything would be adopting a project by changing it.

⚠️ **The artifacts the toolkit generates are a different step**, by that section's own split, and
this role waits on none of them — so a project configured here is configured whether or not
anything has been installed into it yet.

## 1. Say what state the project is in

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/configure.py" --skills-root <skills-root>
```

⛔ **Say which project was resolved before anything else**, naming what
[`§ 1`](../../config/schema.md#the-skills-root-is-where-the-role-runs) lists there. Run from a
sibling project that has a configuration of its own, this role would interrogate **that** project's
host and write **that** project's file; the statement is the only thing that catches it.

What comes back is the whole state this role acts on: whether a configuration is there at all, what
the interrogation could read, how many questions stand, and what the carrier's own coverage walk
says. ⛔ **Read `coverage` first and stop on anything in it** — an entry there is a facet the
surface states and the carrier does not reach, which makes every answer below incomplete in a way
no question would reveal.

⚠️ **A project that states no configuration is the ordinary case here** and is reported rather than
refused: it is what this role is for. A project that already has one is the other ordinary case —
the questions that stand are then the facets it has not addressed, and § What a project is asked's
editing rule is what keeps the rest of its file untouched.

## 2. The interrogation, in two passes rather than one

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/configure.py" interrogate --skills-root <skills-root> \
  --answers <the answers so far, where there are any>
```

⛔ **Two passes, and the order is the rule rather than an optimisation.** The code host can be read
from a tree alone; a tracker cannot be reached until the keys that **address** it have been
answered — which tracker it is, and the project, board or site within it. ⚠️ So the first run
reports the tracker's vocabularies as unestablished *because nothing has been answered yet*, and
that is not a failure: it is run again once the addressing questions are answered, and the
vocabularies arrive then.

⛔ **Every reading is reported, the ones that could not be taken included**
([`§ 11`](../../config/schema.md#a-report-names-what-it-could-not-establish)), and ⛔ **an
unestablished reading is never read as the thing it looked for being absent** — a label listing the
host did not answer is not a repository with no labels. Each one turns into a question instead.

⚠️ **What a tracker publishes is a menu and not an answer**, by § What a project is asked's third
property: the question is still put, with the published set as its options.

## 3. The questions, asked in the surface's own order

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/configure.py" questions --skills-root <skills-root> \
  --answers <the answers so far, where there are any>
```

Each question carries its key, the section of the surface that states it, whether it is required and
under which condition, its menu where there is one and where that menu came from, its default where
the surface marks one, and whether its value is one a repository may not hold.

- ⛔ **Ask them, and compose neither the set nor the order here.** The order is the surface's own,
  which is the order a person reads those keys in; a set composed in this file would be a second
  statement of the surface, free to disagree with the one the carrier derives.
- ⛔ **A menu is offered as a menu** and never as a free-text field, which is that section's fifth
  property. Where the menu came from the tracker, say so: the person is choosing which of their own
  tracker's words this project means.
- ⛔ **A default is offered as the default**, and silence takes it. A key the surface marks none for
  has no default to offer, and silence there is a question still open rather than an answer.
- ⛔ **A facet answered as absent is asked for its reason in the same breath**, and for the trigger
  that would revisit it where one exists. An absence is a stated decision here; the carrier refuses
  to write one without its reason, so an answer taken without it comes back as a refusal later.
- ⛔ **A question about a value a repository may not hold says so when it is put.** The answer is
  routed to § 28's own file, and the person needs to know that before they give it rather than
  after.
- ⛔ **Nothing is defaulted on a person's behalf and no question is carried forward**
  ([`§ Nothing is deferred`](../../config/schema.md#nothing-is-deferred)): a facet nobody answered
  is a facet this pass asks about, in the form that section states, and the pass is not finished
  while a question it raised is open.

⚠️ **Where a question's answer makes another one meaningful, it is asked next rather than in order**
— which tracker it is before the keys that address that tracker, the branch model before the
directory its trees sit under. That is the conditional requiredness the question already carries,
read rather than guessed.

## 4. Write it

Put the answers in one block, keyed exactly as the configuration is, and hand the file over:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/configure.py" write --skills-root <skills-root> \
  --answers <the answers> --dry-run
```

⛔ **The plan first, then the write.** Nothing is written unless every answer holds, and a run with
`--dry-run` reports exactly what the write would do. Drop the flag to perform it.

- ⛔ **A refusal is a refusal.** The report names every key that is short, and all of them at once
  rather than one per round trip. Answer them and run again; nothing is written in between.
- ⛔ **A key the carrier could not place in a file that already exists is named rather than
  appended**, and the report says which. That is a key for a person to put in by hand — appending it
  blind would state it twice, and the reader resolves one of the two copies.
- ⛔ **Read what it says it changed.** A configured project whose answers are already in the file is
  reported as unchanged, with nothing written at all; a file that is not there is rendered whole and
  carries the generation's own marker.
- ⚠️ **A second run leaves the tree byte-identical**, which is asserted on the bytes by the
  carrier's suite rather than reported by the run — so re-running this role is safe and the report
  is not what makes it so.

**Where a marker has to come out** — a plugin being retired, or a file a person is taking over:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/configure.py" unmark --skills-root <skills-root>
```

⛔ **The marker and never the file.** Removing a project's configuration is removing its adoption,
which is a person's act and not this role's.

## 5. The reply

Register, and the language, are
[`§ 8`](../../config/schema.md#the-reply-to-the-person-running-a-role)'s — the outcome in the first
sentence, then the facts, with a table where the content enumerates.

- what was resolved — the skills root, the configuration path, and whether a file was already there;
- **every reading the interrogation took and what each one answered** — read, stated as none, or
  unestablished — ⛔ **the unestablished ones named rather than omitted**, since those are the keys
  that became questions;
- what was written: the file, the keys it changed, and § 28's own file where one was written, with
  ⛔ **the count of values routed there and never the values themselves**;
- ⛔ **which questions were asked and what each was answered**, so that a later pass reading this
  can tell a facet somebody decided from one nobody reached;
- ⛔ **every facet answered as absent, with its stated reason** — an absence reported as a blank is
  the one reading this whole role exists to prevent;
- ⛔ **anything that could not be established, named rather than omitted**
  ([`§ 11`](../../config/schema.md#a-report-names-what-it-could-not-establish)), which has no quiet
  form: a reading that failed, a key that could not be placed, a coverage entry;
- ⛔ **what the project can now do, and what it still cannot.** A configuration this role wrote is
  one the reader accepts; which roles of the loop it maps is `carriers`' own answer, and a role a
  project did not map is a legitimate configuration rather than a partial install
  ([`§ 7`](../../config/schema.md#7-carrier)) — so the reply names the roles that are now addressable
  and says that the rest are unmapped by decision;
- ⛔ **anything that needs the person running this, asked with the options**
  ([`§ Nothing is deferred`](../../config/schema.md#nothing-is-deferred)): a question whose answer
  they alone hold, a key that could not be placed, a facet whose absent case they have to decide.

⛔ **And where the configuration is now written, say what comes next rather than leaving it to
whoever reads this later**: the artifacts the toolkit writes into a repository are a step of their
own, invoked by name, and it waits on nothing this role answered.

## What this carrier is

```yaml
# carrier: beside
```

⛔ **Read from this file and declared nowhere else**, by
[`§ Whether a project can adopt`](../../config/schema.md#whether-a-project-can-adopt-this-procedure-at-all-and-the-check-that-answers-it).
