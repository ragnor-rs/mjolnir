---
name: adoption-readiness
description: Answer whether mjolnir can replace an adoption target's loop today, and name what is missing where it cannot — for the projects whose checkouts the invocation names, read from their live trees rather than from recollection. Use when asked if a project is ready to adopt mjolnir, which projects can be migrated, what a given project is still waiting on, or before starting a migration item.
---

# Adoption readiness

Four facts per project, never averaged into one: whether the plugin **resolves** there, whether a
**configuration** exists that the shared reader accepts, what the **tracker port** answers for its
kind, and which of the loop's **roles** it carries against which the plugin ships.

⛔ **WHICH PROJECTS, AND EVERY VALUE ABOUT THEM, ARRIVE ON THE INVOCATION.** Nothing in this
directory names a project, a directory, a tracker or a path — that is what lets it be tracked under
a carrier root, where the strictest rule in the repository applies (README.md § Conventions, held by
`tools/check_no_project_names.py`). The list lives with whoever runs the check, and ⚠️ **the answer
is only as good as the list they pass**: a target left off the invocation is not reported as missing,
because nothing here knows it exists.

## 1. One read

```bash
python3 .claude/skills/adoption-readiness/scripts/readiness.py <path>[:<kind>] ... \
  [--adapter-item <kind>=<n>] [--migration-items <n>,<n>] [--candidate <name>=<file>]
```

About five seconds, most of it the host. Each target is a checkout path; a project's name is its
directory's own basename, so nothing is declared twice.

| argument | what it is for, and what happens without it |
|---|---|
| `<path>:<kind>` | the tracker kind to probe the port with, for a project that has written no configuration of its own. Omitted, the port is **not** probed and the run says so — it never guesses a kind |
| `--adapter-item` | the work item that builds that kind's adapter. Omitted, the line reads `none passed` rather than vanishing |
| `--migration-items` | the roots whose `blocked_by` closure is the critical path. Omitted, the section says no closure was walked |
| `--candidate` | a configuration drafted for a target, validated against **that project's** skills root and written nowhere |
| `--no-host` | drops the only network read — the closure and each adapter work item |

⛔ **Run with no target at all and it reports exactly that**, exits `2`, and measures nothing. An
empty list is a missing argument, never a backlog of zero projects that are all ready.

Exit status is three-valued and the third value is the point:

| | |
|---|---|
| `0` | every target is ready |
| `1` | at least one is not, and the report says what each is missing |
| `2` | something **could not be established** — which is not "not ready", and is never folded into it |

⛔ **Read the report before concluding anything, and do not re-derive its figures by hand.** Every
number comes from the trees, the reader, the port or the host; a second derivation is a second
answer.

## 2. What the script will not tell you

- **Whether a role's *behaviour* survives.** It matches a role to a shipped carrier by name. Two
  carriers for one role mean the role is covered; they do not mean the shipped one does what the
  local one did. Only #21's acceptance answers that, per project.
- **Whether the tracker kind you passed is right.** It prints what each project's own carriers
  name beside the kind the invocation gave — read the two together. A kind nobody tests is a kind
  nobody can be wrong about, and here it is typed by hand. Where the project has written its own
  configuration, the reader's kind wins and the argument is ignored.
- **What a project keeps local.** A carrier classified `utility`, `guard` or `beside` is out of the
  loop's scope by declaration, not by measurement.

## 3. When it says `CANNOT ESTABLISH`

Three causes, and each is a real finding rather than a run to retry:

- **A carrier nothing classifies.** The role counts become floors — an uncounted role reads as a
  role that does not exist. Classify it in `vocabulary.yaml` under `carriers:` and run again.
- **The loop's size disagrees.** `schema.md`'s heading counts the roles in a word and the paragraph
  under it lists them; `vocabulary.yaml` declares a key per role. All three must agree, so a role
  added to the surface reddens this instead of being silently uncounted. Add the key.
- **A checkout or the host is missing.** Say so in the reply; do not report a project as not ready
  because its directory moved.

## 4. Narrowing a project's own gap

A target with no configuration is reported against a **probe** — the shipped example for the kind
the invocation passed — which answers the port's question and carries nobody's values. To get the
stronger answer, draft that project's configuration and name it on the invocation:

```bash
--candidate <target name>=<path to the draft>
```

⛔ **The draft belongs outside this repository**, for the reason the target list does: it carries a
project's own values. The script validates it with `config.load_text` against **that project's**
skills root, so the project's own tree is never written to and the reader's refusals arrive exactly
as they would after migration. Only a candidate or the project's own file counts as its facts — ⛔
never read a project fact off a probe.

## 5. The reply

§ 8's register, and the shape it asks for here:

- The verdict per project, in the order they were passed, in a table.
- ⛔ **Which targets were passed**, so a verdict is never read as covering a project nobody named.
- For each, the shortest honest statement of what is missing — unshipped roles by name, the
  adapter's work item, the configuration's absence.
- The critical path's open items, as numbers with their titles.
- ⛔ Anything the run could not establish, stated as such and not as a gap in the toolkit.
- ⛔ No audit trail: what changed since a previous run belongs nowhere, because this report states
  only what is true now.
