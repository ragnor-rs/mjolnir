---
name: close-out
description: Bring this project's backlog, dependency graph and execution plan back into agreement after work has landed — one read of the live state, then the edits it names. Use after a batch of issues closes or is filed, at the end of a session, or when asked to update the plan, check the graph, say what is takeable next, or draft the ordering document for a project that has none yet.
---

# Close out a batch

Four things have to agree: the **open set**, its **`P:` labels**, the **dependency relations**, and
the **row table** in the execution plan. This role reads all four in one call, names every
disagreement, makes the edits that are mechanical, and **asks** about the ones that are judgement.

⛔ **Run it from the primary checkout**, not from a branch worktree. The plan is one file outside
the repository and has no lock; a worktree has no reason to be writing it.

⛔ **This role leaves no audit trail.** The plan states what is true now — rows, arguments, counts.
It never records what a pass did, what it corrected, what a figure used to be, when a notation
changed, or who filed what. No dated revalidation paragraphs, no "was", no "previously", no
"re-derived rather than recalled", no ✅-with-a-date beyond the landed record a row already carries.
A stale line is **replaced**, not annotated. Everything about the pass itself goes in the reply
(§ 7), which is read once and kept nowhere.

## 1. One read

```bash
python3 .claude/skills/close-out/scripts/plan-status.py
```

Takes about a second: the whole graph arrives in one GraphQL call (`Issue.blockedBy`), which
returns what polling `dependencies/blocked_by` per issue returns. ⛔ **Read its report before
touching anything**, and ⛔ **do not re-derive any of its figures by hand** — a second derivation
is a second answer.

It reports: open count and `P:` tiers · relations, acyclicity, edge-free new filings · coverage of
the row table with every landed-but-still-placed issue and **the exact edit shape its row needs** ·
ordering violations · same-row edges split into *stated*, *reading order only* and *contradicted* ·
what was filed, what landed and which relations were added or removed since the last stamped pass ·
the unblocked queue in row order.

Exit 1 means something needs an edit. The `since the last pass` block is the only cheap way to see
a **relation** change: a dependency edit bumps no `updated_at`, so `GET /issues?since=` cannot find
it, and the snapshot diff can.

### No ordering document yet

The read refuses on a store that holds none, because the four things that have to agree have
nothing to agree with. ⛔ **The refusal is not a bootstrap**: a run from a branch worktree resolves
a *different* store, where a plan is absent for a reason that is not "this project has none", so a
draft taken on that refusal writes a second ordering nobody reads. Check that the store the refusal
names is the primary checkout's, then opt in:

```bash
python3 .claude/skills/close-out/scripts/plan-status.py --bootstrap
```

It reads the same live state, ⛔ **writes nothing**, and reports the path the document goes to and
the graph's **layers** — layer 1 is what nothing live blocks, each later layer is what its own
blockers all sit above, and every item carries the blockers that hold it.

1. **Draft the document** from that report and from nothing recalled: the title, the set being
   ordered with its figures, § 6's live-status line, and the row table.
2. ⛔ **A layer is not a row.** The layers are the hard constraints and a row is a yield
   subpriority inside them, which nothing derives — so every row carries its argument in the why
   column, and items whose relative order is yield share a row, with an arrow wherever the graph
   states an order. This is the one pass that **creates** rows; every placement in § 4 is into a
   row that already exists.
3. ⛔ **Summarise, then ask — the file is written on approval and not before.** The ordering is the
   person's to approve, and the summary is the figures, the rows with their one-line arguments, and
   every call that was judgement rather than a constraint. ⛔ Not the document's text, which is what
   the file is for.
4. On approval, write it at the path the report named and run § 1's read against it. The coverage
   block is the check on the draft — `N/N placed`, zero ordering violations, every same-row edge
   carrying an arrow — and § 6's `--stamp` sets the first baseline.

⛔ **A drafted document carries no account of having been drafted**, by the rule at the top of this
file: it states the ordering that is true now.

## 2. Priority — count, never infer

`P: Highest`, `P: High`, or none. None is a legitimate state; **below `P: High` is not**, because
the plan's ordering is a yield subpriority *inside* `P: Highest`.

**The call on an item filed unlabelled is delegated to this role.** The test is one question: **is
this item work for one of the target projects?** If yes, `P: Highest`; if it serves this
repository's own loop instead, no label, which is not a demotion. ⛔ State the derivation in the
reply every time, in one sentence.

⛔ **Never derive a label from a row, a relation, or this report.** A row is yield and a relation is
a hard constraint; neither is a priority. A label arriving after an ordering moves no row.
⛔ **Raising or lowering a label its author or the person running this already set is not
delegated** — ask, with the options. Same for anything the script prints as `BELOW P: High`.

## 3. Relations — the test, then the answer either way

For each issue the report lists as **filed since the last pass with no edge**, run the
require-not-tolerate test against both the candidate blocker's *outcome* and its *acceptance
check*: does the dependent's acceptance check pass without it? A plausible consumer is not a
requiring one — ⛔ and a silent bullet is ignorance, not tolerance.

- **No edge** is an answer to state in the reply, not a blank.
- An edge is a **dependency relation** through the API, never a `Depends-on` line in a body.
- Where a row's argument turns on an edge that does **not** exist, the row says so as a standing
  fact — "this one is yield, not a constraint" — and not as the story of an edge that was removed.

## 4. The plan edits

| the report says | the edit |
|---|---|
| `LANDED, still placed`, sole issue in its row | retire the row: `\| — \|` label, `✅ **landed \`<sha>\`, <date>**`, keep the why |
| `LANDED, still placed`, shared row | remove it from the **issues cell** only; record `✅ **#N landed \`<sha>\`**` in the why, keeping the row's argument as the record of what it cost |
| `UNPLACED` | place it in an **existing** row, and argue it in the why column |
| `CELL CONTRADICTS` | the cell says the opposite of the graph — fix the cell or the graph, and say which was wrong |
| `arrow absent` | write the arrow the relations already require; where a chain would claim order the graph does not, group instead and say in the why column what the grouping means |
| `ordering violations` | a blocker below its dependent: move one, and argue it |

⛔ **A row label must be an integer** — the parser skips any other first cell, so there is no `8b`.
A new rank means renumbering every row below or using an existing row.
⛔ **Only the issues cell places an issue.** Naming it in the why column places nothing.
⚠️ **Record the cost where a row is forced or late** rather than letting the placement imply there
is none.
⚠️ One surgical edit per row. The file has no lock, and a rewrite loses a sibling's line.

## 5. Every open item, whoever filed it

⛔ **The pass covers the whole backlog, not this session's share of it.** Who filed an item, and
whether it arrived from a parallel session, changes nothing: an item with no row, no tier answer or
an untested relation is unprocessed, and processing it is what the role is for. Leaving one for its
filer is how a backlog ends up with items nobody is looking at.

⚠️ Several sessions write the plan, and it has no lock. That is a collision hazard, not an
ownership rule, and it is handled by *how* the edit is made rather than by declining to make it:

1. Re-read the row immediately before editing it, and check `last written` in the report against
   what you last saw. An item can be placed by its filer between two runs — re-reading costs a
   second and a duplicate row costs a pass.
2. One surgical edit per row, never a rewrite of the table or the file.
3. Re-run after editing. A sibling landing a change mid-pass shows up as a figure that moved.

An item whose relation test you ran and answered "no edge" is settled rather than pending: record
it so later passes stop asking.

```bash
python3 .claude/skills/close-out/scripts/plan-status.py --stamp --tested <n>
```

## 6. Bring the plan's own prose current, then stamp

Three facts at the top of the plan go stale on every landing and the script reads none of them: the
`N open issues: …` line, `Landed since:`, and the live-status line. ⛔ **Overwrite each in place**
with the figures from the report — never decrement by hand, never add a second statement beside the
old one, never date the change. The live-status line is one sentence and holds the five figures:

```
**Live as of <date>: N open, R relations, acyclic, N/N placed, zero ordering violations,
U unblocked, S same-row edges all carrying an arrow.**
```

Then the closing run, which also moves the baseline:

```bash
python3 .claude/skills/close-out/scripts/plan-status.py --stamp
```

⚠️ Exit must be 0. If it is not, the pass is not finished — the remaining flag is either yours to
fix or a question for § 7.

## 7. The reply

Reference register: what changed, what it cost, what needs the person running this. A short table
beats prose.

- the four figures after the final run — open, relations, placed, violations;
- every edit made, by row;
- ⛔ anything that needs a decision, **asked with the options** — a label below `P: High`, a
  contradicted cell, a row whose argument you cannot write. Nothing is deferred and nothing is noted as
  "to do later": the pass is not finished while a question it raised is open.
