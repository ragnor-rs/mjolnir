---
name: start
description: Take a work item — the next one this project's ordering makes available, or one named on the invocation — run the readiness gate whole, claim it, and cut its branch into its own tree. Use when asked to start an issue, take the next item, pick up the next piece of work, or cut a branch for an item.
---

# Start a work item

Four things happen in one pass and in this order: the configuration is **resolved** and said out
loud, the item is **chosen**, the gate runs **whole**, and the claim is taken **by cutting the
branch**. Nothing after the cut belongs to this role.

⛔ **Run it from the shared checkout** — § 10's term for the one every tree is cut from, and here
the one the registered marketplace path serves, so it stays on the integration branch while an item
is in flight beside it. Running the role there is not *working* in it, which is the separate
question § 10 answers per project.

⚠️ **This is the hand-built half of the role, not the shipped one.** What it reads that no key
defines, and what the shipped role owes, are in § 7. Read that before treating anything here as
the procedure.

## 1. Resolve, and say what was resolved

```bash
python3 plugins/mjolnir/scripts/config.py
```

One read, before anything acts. It prints the root it stood in, the file it found there, the
repository that file addresses, and the configuration itself. ⛔ **Name those three in the reply
before the first write** — a role run from a sibling project that has a configuration of its own
resolves *that* project and proceeds, and the statement is the only thing that catches it.

Four parts of the configuration are read here and ⛔ **never copied into this file**: the branch
prefix per item type, the branch model, the readiness list, and the staging and trailer rules the
first commit on the branch will run under.

## 2. Which item

**Named on the invocation** — the argument is the item, and it still goes through § 3 and § 4
unchanged. An item named by someone who wants it started is not an item exempt from the gate.

**Nothing named** — take the next one the ordering makes available:

```bash
python3 .claude/skills/close-out/scripts/plan-status.py
```

Its `unblocked now` block is the queue, already in row order. ⛔ **Read the queue; never re-derive
it.** A second derivation is a second answer, and the ordering lives in one document with its
argument beside it.

- ⛔ **Row order is the whole answer to *which*.** Not the label tier, not the relation count, not
  the position in the backlog. The ordering is a yield subpriority argued in the plan; a label is
  never a row and a row is never a label, in either direction.
- The first candidate in row order whose claim is free (§ 4) is the item. A candidate whose claim
  is taken is skipped silently — that is the convention working, not a problem.
- A row holding several items offers them in the order the row's arrow states. Reading order
  states nothing.

## 3. The gate, run whole

Run the configured readiness list in order, ⛔ **all of it, then report** — an item with four
problems hears about all four rather than being bounced once per round trip. The list, each
check's stop message and each check's flagged-or-quiet behaviour are the configuration's; the
semantics are
[`schema.md § 5`](../../../plugins/mjolnir/config/schema.md#5-readiness-gate--an-ordered-predicate-list),
which this file names and does not restate.

- A check this project does not configure is **absent**, not defaulted to passing. Report the list
  that ran, not a verdict with no list behind it.
- A failure that is not a defect stops **quietly**: an item that is correct and merely early has
  nothing for its author to fix.
- ⛔ **Stop means stop.** A gate that is argued with is not a gate; the reply states which
  predicates failed and what each wants.

Where the plan's report already answers a predicate — the item's state, and whether anything it
depends on is still live — read it from there rather than asking the host twice.

## 4. The claim is the branch

**Cutting the branch is the claim.** Measured rather than assumed: `git worktree add` with `-b` on
a branch name that already exists fails **before creating the directory**, so the host needs no
write for the claim to be atomic, and every session on this machine can see it through
`git worktree list`.

The branch name is `(prefix, number, slug)`:

| part | where it comes from |
|---|---|
| prefix | the per-type table in the configuration, read in § 1 — a function of the item's type, never a literal in this file |
| number | the item's own number |
| slug | the item's title, slugged — and a **translation** where the item's language differs from the repository's, never a transliteration ([`schema.md § 8`](../../../plugins/mjolnir/config/schema.md#8-language-register-audience--per-artifact-not-per-project)) |

```bash
git -C <code-root> worktree add <tree> -b <prefix>/<number>-<slug>
git -C <code-root> worktree list
```

⛔ **Both arguments come from somewhere rather than from this file.** `<code-root>` is what § 1
resolved — § 1 is why `git` names its root instead of inheriting a working directory — and
`<tree>` is where this project puts a tree, which is the third of § 7's three unread values.

- **Refused** ⇒ the item is taken. Auto-picked: go back to § 2 and take the next candidate. Named:
  stop and say who holds it is unknowable from here — the branch says *taken*, never *by which
  session*.
- ⛔ **Never `--force`, and never a second checkout of a branch already checked out somewhere.**
  Git refuses the second checkout by name, and that refusal is a stop: the session holding it may
  be mid-task. Work in the tree that holds it or not at all.
- Before cutting, a cheap pre-filter avoids pointless attempts —
  `git -C <code-root> branch --list "*<number>-*"` and
  `git -C <code-root> ls-remote --heads origin "*<number>-*"`, since a sibling session may have
  pushed a branch this machine has never had. ⚠️ Measured, because the pattern rule is easy to get
  backwards: a slashless pattern is matched against the ref's tail, so `*<number>-*` finds
  `<prefix>/<number>-<slug>` without the prefix being known — which is the point, since the prefix
  is a configured value. The attempt is still the authority; the filter only saves one.
- ⛔ **An orphaned claim is not takeable by this role.** A branch whose tree no live process has as
  its cwd, with no commits ahead of the integration branch, looks exactly like one a session is
  about to commit into. **Ask**, with the two readings stated. Improvising the judgement is how two
  sessions end up on one item.

**Then make the claim visible off this machine**, which the branch cannot do:

```bash
gh issue edit <number> --add-assignee @me
```

⚠️ Every session here authenticates as the same user, so the assignee carries *taken* and nothing
more. It is the half a session on another machine can read; the branch is the half that is atomic.
Neither replaces the other.

## 5. The tree, and the push hazard

- The new tree is **where the work happens**; the shared checkout is not worked in while an item is
  in flight. Which of the two the procedure addresses after the gate is the branch model's to say,
  and § 1 read it.
- A project's own setup and teardown for a tree are its `mechanics` pointer — **named, never
  absorbed**. Where it is null there is nothing to run, and that is an answer.
- ⛔ **Check the new branch's upstream before any push, rather than assuming the cut cleared it.**
  A branch cut without tracking disabled tracks the **base**, and then a bare push writes to the
  base. One measured copy of this role carried the safe form and three carried the unsafe one.

```bash
git -C <tree> rev-parse --abbrev-ref --symbolic-full-name @{upstream}
```

A branch with no upstream is the wanted state: the first push names its own remote branch
explicitly and sets tracking then. An upstream pointing at the base is the hazard — clear it
before pushing, and say in the reply that it was found set.

## 6. The reply

Reference register: the outcome in the first sentence, then the facts. A short table beats prose.

- what was resolved — root, configuration file, repository;
- the item, and **why it** — the row it holds, and every candidate skipped ahead of it with the
  reason (claim taken, gate stopped);
- every predicate that ran and its verdict, including the quiet ones;
- the branch, the tree, and the upstream check;
- ⛔ anything that needs the person running this, **asked with the options**. An orphaned claim, a
  stop whose remedy is a decision, an item whose type has no prefix. Nothing is noted for later:
  the pass is not finished while a question it raised is open.

## 7. What this prototype is not

⚠️ **Three things it reads that no key defines**, stated so none of them later reads as covered:

1. **The ordering.** `unblocked now` comes from the close-out role's one read, and the row table it
   parses is a document outside every tree. A role shipped from the plugin cannot reach either — so
   *which item is next* has to arrive through the port, which is the half of the parallel-work
   question that is still open, together with the priority a queue check reads.
2. **Where a tree is created.** The branch model states whether a second tree may exist and whether
   the shared one is ever worked in; it states no location, and `mechanics` is setup and teardown
   rather than a path. So `<tree>` in § 4 resolves to this repository's standing convention, which
   is carried in the ordering document and is a value nothing reads.
3. **The claim itself.** That cutting the branch *is* the claim, that the assignee is its
   off-machine half, and that an orphaned one is escalated rather than taken, are a convention this
   repository measured and wrote down. The carrier, the writer, the release and the
   live-versus-orphaned test are unsettled on the surface.

⚠️ **No tracker operation runs here beyond the assignee write.** This project's tracker has no
implementation registered behind the port, so every operation reports its stated fallback. A
project whose port is live routes § 4's visible half through the port instead, and this file is not
the place that difference gets hard-coded.
