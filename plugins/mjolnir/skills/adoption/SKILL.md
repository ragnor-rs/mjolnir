---
name: adoption
description: Answer whether this toolkit can replace a project's loop today, and name what is missing where it cannot — for the projects whose checkouts the invocation names, read from their live trees rather than from recollection. Use when asked if a project is ready to adopt the toolkit, which projects can be migrated, what a given project is still waiting on, or before starting a migration item.
argument-hint: "[<each target's checkout, and its tracker kind after a colon>]"
---

# Whether a project can adopt this procedure

Four facts per project, never averaged into one: whether the plugin **resolves** there, whether a
**configuration** exists that the shared reader accepts, what the **tracker port** answers for its
kind, and which of the loop's **roles** it carries against which this toolkit ships.

Which projects, and every value about them, arrive on the invocation. Nothing in this directory
names a project, a directory, a tracker or a path, by
[`§ Whether a project can adopt → Every per-project value arrives on the invocation`](../../config/schema.md#every-per-project-value-arrives-on-the-invocation).
A target left off the list is not reported as missing, because nothing here knows it exists.

The shared opening and reply rules are
[`§ 7`](../../config/schema.md#what-every-role-does-before-it-acts-and-how-it-reports)'s
subsection *What every role does before it acts, and how it reports*.

## 1. One read

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/skills/adoption/scripts/adoption.py" <path>[:<kind>] ... \
  --carriers <file> [--adapter-item <kind>=<n>] [--migration-items <n>,<n>] \
  [--candidate <name>=<file>]
```

About five seconds, most of it the host. Each target is a checkout path; a project's name is its
directory's own basename, so nothing is declared twice.

| argument | what it is for, and what happens without it |
|---|---|
| `<path>:<kind>` | the tracker kind to probe the port with, for a project that has written no configuration of its own. Omitted, the port is **not** probed and the run says so — it never guesses a kind |
| `--carriers` | the map saying what a carrier on a target's disk is, keyed by basename. ⛔ Omitted, **every** target's role axis is unestablished and the counts are floors — never a project carrying no roles |
| `--adapter-item` | the work item that builds that kind's adapter. Omitted, the line reads `none passed` rather than vanishing |
| `--migration-items` | the roots whose blocker closure is the critical path. Omitted, the section says no closure was walked |
| `--candidate` | a configuration drafted for a target, validated against **that project's** skills root and written nowhere |
| `--no-host` | drops the only network read — the closure and each adapter work item |
| `--self-test` | holds this check to the properties it claims and to the surface, standing its own trees up |

Run with no target at all, it reports exactly that, exits `2`, and measures nothing. An empty list
is a missing argument, never a backlog of zero projects that are all ready.

The work items are read out of the project this check is invoked in, which is § 1's skills root —
not out of the plugin's own tree, and not out of any target. A run from a project whose
configuration states a different code host reads that host.

Exit status is three-valued:

| | |
|---|---|
| `0` | every target is ready |
| `1` | at least one is not, and the report says what each is missing |
| `2` | something **could not be established** — which is not "not ready", and is never folded into it |

Read the report before concluding anything, and do not re-derive its figures by hand. Every number
comes from the trees, the reader, the port or the host.

## 2. Where each classification lives, and why that is two different places

A carrier this toolkit ships declares its own class in its own file — a skill in its `SKILL.md`, a
hook in its script — and nothing in this directory lists them, so a change that ships a carrier
cannot ship it unclassified. When the check reports one, the remedy is a line in the carrier's own
file, stated at
[`§ Whether a project can adopt → Which carriers are classified, and where`](../../config/schema.md#which-carriers-are-classified-and-where-each-classification-lives).

A carrier a *target* carries is classified by `--carriers`, which is that project's fact. A
project's own `carriers:` block is not this and cannot become it:
[`§ 7`](../../config/schema.md#7-carrier) states which roles a project carries and by which kind,
which says nothing about a basename on its disk, and a target that has written no configuration
would have no answer at all.

The two words a declaration may use are the loop's role keys and the classes, both closed and both
in `vocabulary.yaml` beside this file. That file names no project and no carrier, and the check
asserts the two sets are disjoint.

## 3. What the check will not tell you

- **Whether a role's *behaviour* survives.** It matches a role to a shipped carrier by name. Two
  carriers for one role mean the role is covered; they do not mean the shipped one does what the
  local one did. Only a migration item's own acceptance answers that, per project.
- **Whether the tracker kind you passed is right.** It prints what each project's own carriers
  name beside the kind the invocation gave — read the two together. A kind nobody tests is a kind
  nobody can be wrong about, and here it is typed by hand. Where the project has written its own
  configuration, the reader's kind wins and the argument is ignored.
- **What a project keeps local.** A carrier the map classifies outside the role set —
  project-local tooling, a guard, or something travelling beside the loop — is out of the loop's
  scope by declaration, not by measurement.

## 4. When it says `CANNOT ESTABLISH`

Each cause is a finding, not a run to retry:

- **No carrier map was passed.** The one cause whose remedy is the invocation rather than any
  tree, and the one the report must not name a project for: a target measured with no map has
  nothing wrong with it.
- **A carrier the map does not name.** The role counts become floors — an uncounted role reads as
  a role that does not exist. Name it in the map and run again.
- **A carrier whose name covers several roles.** The remedy is the opposite of the one above: the
  name is known and is more than one role, so naming it in the map can never answer it — the map
  says so with an `ambiguous:` entry and refuses to pick. What answers it is that project's own
  statement. Running again changes nothing, and a role it may be is neither covered nor unshipped
  until something says which.
- **A carrier this toolkit ships that declares nothing.** This refuses the check's own answer
  rather than any target's: every target's counts become floors while no target's verdict
  moves. The remedy is in the carrier's own file, per § 2 above.
- **The loop's size disagrees.** `schema.md`'s heading counts the roles in a word and the paragraph
  under it lists them; `vocabulary.yaml` declares a key per role. All three must agree, so a role
  added to the surface reddens this instead of being silently uncounted. Add the key.
- **A checkout or the host is missing.** Say so in the reply; do not report a project as not ready
  because its directory moved.

## 5. Narrowing a project's own gap

A target with no configuration is reported against a **probe** — the shipped example for the kind
the invocation passed — which answers the port's question and carries nobody's values. To get the
stronger answer, draft that project's configuration and name it on the invocation:

```bash
--candidate <target name>=<path to the draft>
```

The draft belongs outside this repository, for the reason the target list does: it carries a
project's own values. The check validates it with `config.load_text` against that project's skills
root, so the project's own tree is never written to and the reader's refusals arrive exactly as they
would after migration. Only a candidate or the project's own file counts as its facts; never read a
project fact off a probe.

## 6. The reply

The shape of the reply here:

- The verdict per project, in the order they were passed, in a table.
- Which targets were passed, so a verdict is never read as covering a project nobody named.
- For each, the shortest honest statement of what is missing — unshipped roles by name, the
  adapter's work item, the configuration's absence.
- The critical path's open items, as numbers with their titles.
- Anything the run could not establish, stated as such and not as a gap in the toolkit, including
  which of the causes in § 4 it was, since one of them is the invocation's and the rest are a
  tree's.
- No audit trail, by
  [`schema § The loop → An artifact states what is true now`](../../config/schema.md#an-artifact-states-what-is-true-now):
  a run's own account of what moved belongs nowhere.

## What this carrier is

```yaml
# carrier: beside
```

Read from this file and declared nowhere else, by
[`§ Whether a project can adopt`](../../config/schema.md#whether-a-project-can-adopt-this-procedure-at-all-and-the-check-that-answers-it)
— which is also what admits a carrier here that is no leg of the loop.
