---
name: finish
description: Take a finished branch to a landed pull request — the commit, the push, the pull request, the host's answer about it, the merge read back from state, the work item's own move, and the tree released. Use when asked to finish a work item, open or land its pull request, or merge the branch for an item.
argument-hint: "[<item number, item url, or pull request url>]"
---

# Finish a work item

The outcome is three facts, and each is **read back rather than asserted**: the change is merged,
the item has moved, and the tree is released. Everything below is ordered so that nothing
irreversible happens before the thing that would have stopped it.

⚠️ **Four of the steps below were in one copy of this role and in none of the other four**, and
each is marked where it falls. They are not refinements: in every one of them the obvious
procedure reports the opposite of what happened.

## 1. Resolve, and say what was resolved

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/config.py"
```

⛔ **Say which project was resolved before anything else**, naming what
[`config/schema.md § 1`](../../config/schema.md#the-skills-root-is-where-the-role-runs) lists
there. The reader reports each item, so this costs a sentence. Run from a sibling project that has
a configuration of its own, this role resolves **that** project and merges into **that**
repository, having done something plausible first; the statement is the only thing that catches it.

⛔ **Do not parse the configuration here.** A role that reads it itself is a second set of
defaults, and two sets drift apart with nothing noticing.

⛔ **Read the `unavailable` list before acting on anything.** An entry there is a stated absence
rather than a fault, and a key named there that this role needs is a stop with the key named.

Five things are read here and ⛔ **never copied into this file**: the staging and trailer rules the
commit runs under, the branch model that decides which tree every step after this one addresses,
the host's own runs and what each of them mirrors, the closing capability behind the port, and the
language and register the pull request is written in. Each has a section of the surface and this
file cites it.

Throughout, `<work-root>` is the tree the work is in — which
[`§ 10`](../../config/schema.md#where-the-work-happens) decides and this file does not — and every
`git` call names it, per § 1.

## 2. The argument and the branch must agree

The argument resolves three ways, and all three reach the same thing: **one item number**. A bare
number is the number; an item's address and a pull request's address each carry it in the last path
segment.

⛔ **An argument that disagrees with the branch is a stop that prints both values.** Not a
preference for one of them and not a question — the two readings are *finish the item I named* and
*finish the branch I am standing on*, and a role that picks one silently finishes work nobody asked
it to. ⚠️ **This is the first of the four**: without it, one copy worked on a different item than
the one it was given and said nothing.

| what the invocation carries | what the role does |
|---|---|
| nothing | the branch is the statement, and the number is read out of its name |
| an argument agreeing with the branch | proceed |
| an argument disagreeing with the branch | ⛔ stop, printing the argument's number and the branch's |
| an argument with no branch to check it against | proceed on the argument, and say that nothing confirmed it |

Where neither the argument nor the branch states a number, the port's `item_number` fallback
([`§ 3`](../../config/schema.md#the-operations-and-what-an-absent-capability-does)) is the answer
and it is a stop: a role with no number does not invent one.

## 3. The commit

Entirely [`§ 6`](../../config/schema.md#6-commit-behaviour)'s — staging, the message mechanism, the
style, and the authorship rule that
[binds every author field](../../config/schema.md#authorship-is-procedure-not-configuration). This
file states none of it and the configuration supplies the part that varies.

A dirty tree here is **derived** from the branch model rather than configured, which is § 6's
derivation over [`§ 10`](../../config/schema.md#10-branch-model)'s key. Report what was found,
state plainly that nothing was stashed or moved, and leave it alone.

## 4. The push, and the upstream hazard

⛔ **Check the branch's upstream before any push.** A branch cut without tracking disabled tracks
the **base**, so a bare push writes to the base — and three of the five copies carried that unsafe
form verbatim. ⚠️ **The cut is the starting role's and the push is this one's**, which is why the
check belongs here: whichever role cut the branch, this is the role that would write to the base.

```bash
git -C <work-root> rev-parse --abbrev-ref --symbolic-full-name @{upstream}
```

- **No upstream** is the wanted state. The first push names its own remote branch explicitly and
  sets tracking then.
- **An upstream pointing at the base** is the hazard. Clear it before pushing, and say in the reply
  that it was found set.

## 5. The pull request

The rules are [`§ 6 → The pull request title and
body`](../../config/schema.md#the-pull-request-title-and-body) — the summary and the driven test
plan, the closing reference being whatever the port's `link_for_close` says, the language and
register, the authorship rule, and the body being held to [*Nothing is
deferred*](../../config/schema.md#nothing-is-deferred). ⛔ **This file does not restate any of
them.** What it carries is the **shape** those rules leave open, which is the part that lived in
the five copies:

**The summary** is what changed and why it is the answer to the item — not a list of the files
touched, which the diff already states better. One paragraph, where one will do.

**The test plan is driven, not published.** Every line is something that was actually run, carrying
its verdict and ⛔ **the tree it ran in**, which is
[`§ 10`](../../config/schema.md#which-tree-a-verdict-belongs-to)'s rule: a check run where another
tree's build is bound answers about code this branch does not contain, in the direction that
passes. A step that was not run is written as not run. A plan of steps a reader *could* take is the
published kind and is worth nothing.

**The open items section states that there are none, and that statement is read back.** By
*Nothing is deferred* the count is taken where the items were raised — this body, and every thread
on the change the host can report unresolved — and the gate refuses the merge while one stands. ⛔
**A role does not write that section by believing itself**; it writes what the count returned.

## 6. The host's answer about the change

⛔ **Four preconditions, in order, and all four are required before any of this reads as green.**
⚠️ **The second of the four:** one copy had these and the other four treated silence as success.

1. the tree is clean;
2. a run exists **for this commit** — not for the branch, and not for an earlier push;
3. the run **executed steps**;
4. it concluded green.

⛔ **Absence of signal is not green, and it is not a failure either — it is no answer**, which is
[`§ 2`](../../config/schema.md#2-code-host)'s rule and the reason precondition 3 exists separately
from 4. A run whose billing is suspended fails in seconds having started no step, and a conflicted
pull request produces no run at all. ⚠️ **No checks reported** is almost always the second of
those, and reads as *nothing to wait for* to anyone who has not been told.

Which runs should exist, which local command each one mirrors, and which paths each watches are
`host.checks`'s to state ([`§ 2`](../../config/schema.md#2-code-host)) — ⛔ **never this file's, and
never derived from what the host happens to report.** A run's name does not say which command it
duplicates.

⛔ **Never sleep, and watch rather than poll.** The host's own client blocks until the runs settle,
which costs nothing and cannot miss a transition between two polls:

```bash
gh pr checks <number> --watch
```

⛔ **A cap of three fix cycles, then stop and ask**, with the options and what each costs. A fourth
attempt at the same red check is a role that has stopped learning from the answer, and the person
running it can see something the check cannot say.

## 7. The merge, and reading it back

⛔ **Read the merge back from state. Never from the exit status.** ⚠️ **The third of the four:**
both success and refusal can print nothing, and one copy reported a merge that *had* landed as not
having.

```bash
gh pr view <number> --json state,mergedAt,mergeCommit
```

⚠️ **Measured, and the sharpest form of the same rule:** asking for the branch to be deleted as
part of the merge, run from the tree that holds that branch, **lands the merge and then fails on
the deletion** — a non-zero exit for an operation that succeeded. A role trusting the status
retries a merge that is already in.

⛔ **Ancestry answers in one direction only.** ⚠️ **The fourth of the four.** A true answer proves
the content landed; a false answer proves **nothing**, because a squashed or rebased merge rewrites
the commits and the branch's tip is then in no ancestry of the base. Trusting the false answer
reported five finished trees as carrying nine to twenty unpushed commits. So ancestry may confirm a
landing and may never contradict one — which is why the state read above, and not this, is what
settles whether the change is in.

## 8. The item's move

⛔ **Through the port, and never through a tracker.** The two operations are separate and either
capability may be absent: a reference in the body that closes the item on merge, and the tracker's
own automation moving it off the merge.

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/port.py"
```

[`§ 3`](../../config/schema.md#the-operations-and-what-an-absent-capability-does) states each
operation's fallback and the port reports which one was taken. ⛔ **An absence is not an error and
nothing here improvises one** — where the closing reference is unavailable the body carries none
and the item moves separately; where the advance is unavailable the role asks for it; where that is
unavailable too, the move is **reported for whoever does make it**. Say which fallback was taken,
rather than reporting the item as moved.

## 9. Release the tree

What is released once the work has landed is [`§ 10`](../../config/schema.md#10-branch-model)'s,
and a project's own setup and teardown are its `mechanics` pointer — ⛔ **named here, never
absorbed.** Where it is null there is nothing to run, and that is an answer.

⛔ **Confirm the landing from the host before removing anything**, per § 7 — the tree and the
branch are the only copies of the work until the merge is read back.

⚠️ **A tree takes everything git does not track with it, and nothing records what that was.** Read
those files out before the removal or lose them; this is also why
[`§ 11`](../../config/schema.md#the-store-and-when-an-in-tree-store-is-safe) refuses an uncommitted
in-tree store under this branch model. ⛔ **A role cannot remove the tree it is standing in**: say
what is left to remove and where, rather than reporting a release that did not happen.

## 10. The reply

Register, and the language, are
[`§ 8`](../../config/schema.md#the-reply-to-the-person-running-a-role)'s — the outcome in the first
sentence, then the facts, with a table where the content enumerates.

- the three read-back facts: the merge, the item's move, the release — each with what was read
  rather than what was attempted;
- every precondition of § 6 that ran, and its verdict;
- which port fallback was taken, where one was;
- ⛔ anything that could not be established, **named rather than omitted** —
  [`§ 11`](../../config/schema.md#a-report-names-what-it-could-not-establish)'s rule, which has no
  quiet form;
- ⛔ anything needing the person running this, **asked with the options**. The pass is not finished
  while a question it raised is open.
