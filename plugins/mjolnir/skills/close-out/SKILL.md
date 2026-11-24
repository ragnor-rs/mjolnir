---
name: close-out
description: Bring a project's backlog, dependency relations and ordering record back into agreement after work has landed — one read of the live state, then the edits it names, with every judgement asked rather than taken. Use after a batch of items closes or is filed, at the end of a session, or when asked to update the ordering, check the relations, say what is takeable next, or bring a project to its first ordering.
argument-hint: "[--in <the grouping's own value, where the record is a grouping>]"
---

# Close out a batch

Four things have to agree: the **live set**, its **tiers**, the **dependency relations**, and the
**ordering record**. This role reads all four in one call, names every disagreement, makes the
edits that are mechanical, and ⛔ **asks about the ones that are judgement**.

⛔ **This role's key is `close_out`**, whatever this carrier is named — what
[`§ 7`](../../config/schema.md#7-carrier)'s `carriers` maps, and ⚠️ **the carrier's own name is a
different string by that section's rule**, so a key read for this role is that one and reading
another role's is the defect those keys exist against.

⛔ **Where the record lives is [`§ 40`](../../config/schema.md#40-the-record-a-projects-ordering-is-kept-in-and-what-brings-one-into-existence)
and is never assumed.** A project keeps its order of work in one of its tracker's own groupings or
in a document outside every tree, and ⛔ **neither spelling is in this file**: the reader resolves
the carrier and the command below reads it. A project whose record is `none` is a **stop with the
key named**, which is that section's own answer rather than a fault.

⛔ **And this role leaves no audit trail**, by
[`§ The loop → An artifact states what is true now`](../../config/schema.md#an-artifact-states-what-is-true-now)
and [`§ 40 → What a pass may not do`](../../config/schema.md#what-a-pass-may-not-do-whatever-the-carrier).
The record states the order that is true **now**; everything about the pass itself goes in the reply
(step 6). ⚠️ **The baseline is not an exception to that** — it holds the state drift is measured
from rather than an account of a pass.

## 1. Resolve, and say what was resolved

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/config.py"
```

⛔ **Say which project was resolved before anything else**, naming what
[`§ 1`](../../config/schema.md#the-skills-root-is-where-the-role-runs) lists there. Run from a
sibling project that has a configuration of its own, this role reads **that** backlog and edits
**that** project's record; the statement is the only thing that catches it.

⛔ **Read the `unavailable` list before acting on anything.** An entry there is a stated absence
rather than a fault, and a key named there that this role needs is a stop with the key named.

⛔ **Do not parse the configuration here.** A role that reads it itself is a second set of defaults,
and two sets drift apart with nothing noticing. Four things are read here and ⛔ **never copied into
this file**: where the record is kept, the tiers an ordering may carry
([`§ 4.6`](../../config/schema.md#46-priority)), what the tracker can be asked
([`§ 3`](../../config/schema.md#the-operations-and-what-an-absent-capability-does)), and whether
this role is mapped at all.

⚠️ **Where the record is a grouping, which grouping arrives on this role's invocation** —
[`§ 4.8`](../../config/schema.md#48-grouping--what-a-set-of-items-is-planned-into)'s `current` is
read by nothing in the procedure under either of its values, so the value is handed over with `--in`
and a pass given none **stops naming what it needs**. ⛔ Never resolved to whatever the tracker
answered with: an order read off the wrong time box is the one wrong answer that looks right.

## 2. One read

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/close_out.py"
```

⛔ **Read its whole report before touching anything**, and ⛔ **do not re-derive any of its figures
by hand** — a second derivation is a second answer. It reports, in one pass: the live set and its
tiers · the relations, acyclicity, and the items filed since the last pass with no relation either
way · coverage of the record, with every landed item it still places and that item's **closing
change and commit** · ordering violations and same-place edges, where the record states an order ·
what was filed, what landed and **which relations moved** since the baseline · the unblocked queue
in the record's own order.

Exit 1 means something needs an edit. ⚠️ **The drift block is the only way a relation change is
visible at all**: no tracker bumps an item's own modification time when an edge changes, so a query
keyed on one cannot see it and the baseline comparison can.

⛔ **Every absence in that report is an absence and never a zero**, which is
[`§ 11`](../../config/schema.md#a-report-names-what-it-could-not-establish) arriving in a reading:
an item whose blockers could not be asked for, a closing change the tracker holds nothing about, an
item no status maps, a read that filled its own bound. ⚠️ **Each of those goes in the reply as
unestablished** — a pass that reported them as nothing found is a pass that read less than it says.

### Which items may be started, with no record read

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/close_out.py" --startable
```

The *may* question alone: every live item whose blockers have all left the live set, grouped by the
tier [`§ 4.6`](../../config/schema.md#46-priority) carries. ⛔ **It reads no record and no
baseline**, so it is the one mode that answers for a project whose record does not exist yet.
⚠️ **It is not an ordering and must not be read as one** — which item to take next is
[`§ 12`](../../config/schema.md#12-ordering)'s answer, read from the record § 40 states.

### No ordering record yet

The read stops on a project that keeps none, because the four things that have to agree have nothing
to agree with. ⛔ **The stop is not a bootstrap**: a run taken from the wrong place can fail to find
a record that exists, and drafting on that stop writes a second ordering nobody reads. Check that
the record the stop names is the one this project states, then opt in:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/close_out.py" --bootstrap
```

It reads the same live state, ⛔ **writes nothing**, and reports where the record goes and the
relations' **layers** — layer 1 is what nothing live blocks, each later layer is what its own
blockers all sit above, and every item carries the blockers that hold it.

1. **Draft the ordering** from that report and from nothing recalled: the set being ordered with its
   figures, and a place per group of items with the argument for it.
2. ⛔ **A layer is not a place.** The layers are the hard constraints and a place is a yield
   subpriority inside them, which nothing derives — so every place carries its argument, and items
   whose relative order is yield share one, with the order written wherever the relations state one.
   This is the one pass that **creates** places; every placement in step 4 is into one that exists.
3. ⛔ **Summarise, then ask — the record comes into existence on approval and not before.** The
   ordering is the person's to approve, and the summary is the figures, the places with their
   one-line arguments, and every call that was judgement rather than a constraint. ⛔ Not the
   document's text, which is what the record is for.
4. On approval, bring the record into existence and run step 2's read against it. The coverage
   block is the check on the draft, and `--stamp` writes the first baseline.
   ⛔ **Where the record is a grouping, the create is the port's and nothing else's** — never a
   file beside the tracker, a grouping the tracker does not hold being one no later pass can read:

   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/close_out.py" --create --in <the grouping's value>
   ```

   ⚠️ **That act carries no approval of its own**, by
   [`§ 40`](../../config/schema.md#an-ordering-that-does-not-exist-yet-and-the-one-act-that-is-the-persons):
   what the person approves is an *order of work*, and a grouping is a named set. Placing items
   into it is the ordinary pass.

⛔ **A record brought into existence carries no account of having been drafted**, by the rule at the
top of this file.

## 3. Tiers — count, never infer

⛔ **The axis is [`§ 4.6`](../../config/schema.md#46-priority)'s and is restated nowhere here** —
the carrier, the values and their order, read by the command above and printed in its report. An
item carrying no tier is **unranked**, which is a legitimate state and not the lowest one.

⛔ **Never derive a tier from a place, a relation, or this report**, which is
[`§ 40`](../../config/schema.md#the-one-directory-why-it-is-marked-and-what-is-not-a-key-here)'s
rule: a place is yield and a relation is a hard constraint, and neither is importance.
⛔ **Raising or lowering a tier its author or the person running this already set is not this role's
call** — ask, with the options. Same for anything the report prints as outside the stated set.

⚠️ **Whether an unlabelled item is a tier's or nobody's is the project's question and not this
file's.** Where the project states a test for it, apply it and ⛔ **state the derivation in the
reply every time**; where it states none, ask.

## 4. Relations — the test, then the answer either way

For each item the report lists as **filed since the last pass with no relation**, run the
require-not-tolerate test against both the candidate blocker's *outcome* and its *acceptance
check*: does the dependent's acceptance pass without it? A plausible consumer is not a requiring
one — ⛔ **and a silent omission is ignorance, not tolerance**.

- **No relation** is an answer to state in the reply, not a blank.
- ⛔ A relation is written through the port's `link_dependency` and never as a line of prose in a
  body, which is [`§ 3 → An edge is a relation`](../../config/schema.md#an-edge-is-a-relation-and-a-body-keeps-the-reasoning-about-it).
- Where a place's argument turns on a relation that does **not** exist, the record says so as a
  standing fact — *this one is yield, not a constraint* — and never as the story of an edge somebody
  removed.

An item whose test was run and answered *no relation* is settled rather than pending, and is
recorded so later passes stop asking:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/close_out.py" --stamp --tested <the numbers>
```

## 5. The edits, and the whole backlog they cover

| the report says | the edit |
|---|---|
| `LANDED, still placed`, the only item in its place | retire the place, keeping its argument and the landing the report named |
| `LANDED, still placed`, sharing its place | take it out of the **membership** only, recording the landing in the place's argument and keeping that argument as the record of what it cost |
| `UNPLACED` | place it into a place the record **already has**, and argue it |
| `PLACED TWICE` | one place, and say which was wrong |
| `CELL CONTRADICTS` | the record says the opposite of the relations — fix one of them, and say which was wrong |
| `arrow absent` | write the order the relations already require; where that would claim an order the relations do not state, group instead and say what the grouping means |
| `VIOLATION` | a blocker placed after its dependent: move one, and argue it |

⛔ **Only the membership places an item.** Naming it in an argument places nothing.
⚠️ **Record the cost where a placement is forced or late** rather than letting it imply there is
none.

⛔ **The pass covers the whole backlog, not this session's share of it.** Who filed an item, and
whether it arrived from a parallel session, changes nothing: an item with no place, no tier answer
or an untested relation is unprocessed, and processing it is what this role is for.

⛔ **Another session's residue is reported and never repaired** — as the placements that moved, and
⛔ **whose it is as unestablished**, neither carrier's record carrying an author
([`§ 40`](../../config/schema.md#what-a-pass-may-not-do-whatever-the-carrier)). Several sessions
share one backlog and the record has no lock, which is a collision hazard rather than an ownership
rule, and it is handled by **how** the edit is made:

1. Re-read the place immediately before editing it, and check the report's own reading of the
   record against what you last saw. An item can be placed by its filer between two runs.
2. One surgical edit per place, never a rewrite of the record.
3. Re-run after editing. A sibling landing a change mid-pass shows up as a figure that moved.

Then the closing run, which also moves the baseline:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/close_out.py" --stamp
```

⚠️ **Exit must be 0.** If it is not, the pass is not finished — the remaining flag is either yours
to fix or a question for step 6.

## 6. The reply

Register, and the language, are
[`§ 8`](../../config/schema.md#the-reply-to-the-person-running-a-role)'s — the outcome in the first
sentence, then the facts, with a table where the content enumerates.

- what was resolved: the project, the record and its carrier;
- the figures after the final run — the live set, the relations, what is placed, what is in
  violation;
- every edit made, by place;
- ⛔ every reading that could not be established, **named rather than omitted**
  ([`§ 11`](../../config/schema.md#a-report-names-what-it-could-not-establish)): an item whose
  blockers went unread, a closing change the tracker holds nothing about, an item no status maps, a
  read that filled its bound, and the ordering question a grouping-carried record cannot be asked;
- every relation test run, with its answer **either way**;
- another session's residue, as the placements that moved, with ⛔ **whose it is stated as
  unestablished** rather than attributed;
- ⛔ anything that needs the person running this, **asked with the options**
  ([`§ Nothing is deferred`](../../config/schema.md#nothing-is-deferred)): a tier outside the stated
  set, a contradicted record, a place whose argument you cannot write, an ordering that has to be
  brought into existence. Nothing is noted for later — the pass is not finished while a question it
  raised is open.

## What this carrier is

```yaml
# carrier: close_out
```

⛔ **Read from this file and declared nowhere else**, by
[`§ Whether a project can adopt`](../../config/schema.md#whether-a-project-can-adopt-this-procedure-at-all-and-the-check-that-answers-it).
