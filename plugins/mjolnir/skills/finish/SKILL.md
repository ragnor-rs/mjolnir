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

Six things are read here and ⛔ **never copied into this file**: the staging and trailer rules the
commit runs under, the branch model that decides which tree every step after this one addresses,
the host's own runs and what each of them mirrors, **how a pull request lands here and what deletes
the branch once it has**, the closing capability behind the port, and the language and register the
pull request is written in. Each has a section of the surface and this file cites it.

Throughout, `<work-root>` is the tree the work is in — which
[`§ 10`](../../config/schema.md#where-the-work-happens) decides and this file does not — and every
`git` call names it, per § 1. ⚠️ **`§ N` always names a section of the surface, never one of this
file**; the steps below are referred to by number, because the surface has a § 6 and a § 7 of its
own and a bare number would resolve to the wrong one.

## 2. The argument and the branch must agree

The argument resolves three ways and each has to reach **one item number** — which is ⛔ **not the
same number as the change's**:

| the argument | where the item number comes from |
|---|---|
| a bare number | the argument itself; it is the item's own |
| an item's address | its last path segment |
| a **change's** address | ⛔ the host's record of what that change closes — **never** the last path segment, which is the *change's* number |

⛔ **The last two are not one rule, and collapsing them resolves the wrong object.** ⚠️ **Measured
on this repository:** a change's address ended in 132 while the item it closes was 76, and 132 was
a live item of its own — so the plausible reading finishes an item nobody named. ⛔ **That is why the
resolution is corrected here rather than left to the stop below**, which only catches the arm with
a branch to disagree with and never the arm that proceeds on the argument alone. ⚠️ On a tracker
whose keys are not integers a path segment is never an item key at all.

⛔ **Reading what a change closes is a capability and not a given**
([`§ 3`](../../config/schema.md#the-operations-and-what-an-absent-capability-does)). Where it is
unavailable this role says so and **asks** for the item number rather than deriving one — the same
answer `item_number`'s own fallback gives below.

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

⛔ **Four preconditions, in order, and all four are required before any of this reads as green** —
[`§ 2 → Reading a run's answer`](../../config/schema.md#reading-a-runs-answer-and-what-a-failure-is),
which states them, what a precondition's failure may not be reported as, and what separates an
environment failure from a finding. ⛔ **This file restates none of it**: the reviewing role reads
the same runs, and a rule written in one role's skill is a second authority for the other. ⚠️ **The
second of the four:** one copy of this role had those preconditions and the other four treated
silence as success.

Which runs should exist, which local command each one mirrors, and which paths each watches are
`host.checks`'s to state ([`§ 2`](../../config/schema.md#2-code-host)) — ⛔ **never this file's, and
never derived from what the host happens to report.** A run's name does not say which command it
duplicates.

Watching rather than polling is the same subsection's:

```bash
gh pr checks <number> --watch
```

⛔ **A red answer is not this role's to fix.** The fix loop is the reviewing role's at
[`skills/review/`](../review/), whose subject is a finding, and the cap on it is § 2's above rather
than either role's; what this role owes is to **not merge** while a red stands, and to say which
precondition failed. A finishing pass that starts fixing is the review happening with none of its
record kept.

## 7. The merge, and reading it back

⛔ **Four things are established before the merge, because each of them is cheap now and expensive
after.** Every one was in a single copy of a role and in none of the rest, and ⛔ **this step is
ordered so that nothing irreversible happens before the thing that would have stopped it** —
which the last of the four is the measured violation of.

1. ⛔ **Whether anything is based on this branch.** Retarget-on-merge does **not** fire reliably:
   deleting the head branch **closes** every change based on it instead of moving it to this one's
   base. ⚠️ **Recovering one is not a reopen** — a host refuses to reopen a change whose base ref no
   longer exists, so the branch has to be pushed back at its old tip, the change reopened,
   retargeted, and the branch deleted again. **Retarget the dependents first, then delete.**
2. ⛔ **That the merge target is the change's own base**, which is not necessarily the default
   branch. A change based on the wrong one is a mistake to report, not to merge.
3. ⛔ **That the tree is clean here too.** Asking for the branch to be deleted moves the working
   tree off it, so [`§ 6`](../../config/schema.md#6-commit-behaviour)'s dirty-tree derivation
   applies at the merge and not only at the commit. ⚠️ **That reason holds only where this role
   asks for the deletion**, which [`§ 2`](../../config/schema.md#how-a-pull-request-lands)'s
   `delete_branch` decides; the precondition stands either way, a dirty tree at the merge being
   worth establishing before an irreversible act whoever deletes the branch.
4. ⛔ **That the tracker answers at all.** ⚠️ **A merge whose item never moved is invisible work**,
   and step 8 is where that is discovered — after the irreversible act. So the port is reached for
   a read **before** the merge, and an unreachable tracker holds it; `§ 3`'s fallback covers a
   capability that is *absent*, which is a different thing from a host that is not answering.

⛔ **The method is named in the merge call and read from the configuration, never inferred** —
[`§ 2 → How a pull request lands`](../../config/schema.md#how-a-pull-request-lands), which states
the values, why no reader derives one from the shape of the integration branch, and what the key
does *not* restate. ⚠️ **No count of them is carried here**: the surface accepts a value added to
that alternation without its reader changing, so a number in this file would be wrong by the next
one, green. ⛔ **The stated method is checked against what the host permits before the
merge, and that check runs one way only**: a method the host forbids is a stop naming both, while a
host permitting more than the project lands by is the ordinary case and no finding. ⚠️ **It is one
read more, and of the repository rather than of the change** — a pull request carries no
merge-permission field, so nothing read in step 6 answers it.

⛔ **Who deletes the branch is that section's `delete_branch` and is not this role's to decide.**
Under `procedure` this role asks for the deletion; under `host` it must **not**, the host's own
switch having already done it, and a second attempt is refused on a ref that is gone; under
`never` neither acts. ⚠️ **The key is about the remote ref** — the local branch and the tree are
step 9's release regardless of it. ⚠️ **So under the two values that delete nothing here, the
deletion is simply never asked for**, and under `procedure` a deletion asked for *as part of the
merge* takes the local branch with it: that is step 9's release arriving early, not a second act,
and the dirty-tree precondition above is why it is established first.

⛔ **Read the merge back from state. Never from the exit status.** ⚠️ **The third of the four
single-copy steps:** both success and refusal can print nothing, and one copy reported a merge that
*had* landed as not having.

```bash
gh pr view <number> --json state,mergedAt,mergeCommit
```

⚠️ **Measured, and the sharpest form of the same rule:** asking for the branch to be deleted as
part of the merge, run from the tree that holds that branch, **lands the merge and then fails on
the deletion** — a non-zero exit for an operation that succeeded. A role trusting the status
retries a merge that is already in. ⛔ **So how far it got is read rather than inferred from the
error, which can be absent entirely**: the change's own state *and* whether the branch ref still
exists on the remote, which is the second half of the read-back and the only thing that says
whether the server-side deletion happened. Then finish whatever those two say is left.

**Under `method: squash`, the subject of what lands is this role's to pass.** ⛔ **The squash
subject carries the references, and a host appends none of them to a subject it was given.** Where
the project's convention puts the item's number, or the change's own, in the subject line of what
lands, ⛔ **that subject is passed explicitly** — a host adds the change reference only to a
subject it generates itself, and omitting the subject on a one-commit branch squashes under *that
commit's* message instead, dropping the item reference. ⚠️ **No title check can catch either**: it
reads the change, and the squash happens after it passed. The subject is permanent on the
integration branch, so this is also the last chance to correct a title that overstates what the
change does. ⚠️ **Under any method that is not `squash` there is no such subject to pass** — the
branch's own commit messages are what lands — so the title is corrected on the change itself or
not at all.

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

⛔ **An item carrying more than one change does not advance until all of them have landed.** One
copy carried this and the rest moved the item on the first merge, which says the item's work is in
when a sibling change is still open. ⚠️ **The count is taken after this merge rather than before
it** — the change just merged no longer answers, and one that reports itself still open is one the
merge did not complete. ⛔ **Match the item's own reference rather than searching for its number**:
a host's search normalises away the punctuation a convention relies on, so a branch whose name
contains those digits answers a search for a different item entirely. Where a sibling is open,
**leave the item where it is and name the open changes in the reply.**

## 9. Release the tree

What is released once the work has landed is [`§ 10`](../../config/schema.md#10-branch-model)'s,
and a project's own setup and teardown are its `mechanics` pointer — ⛔ **named here, never
absorbed.** Where it is null there is nothing to run, and that is an answer.

⛔ **Confirm the landing from the host before removing anything**, per step 7 above — the tree and
the branch are the only copies of the work until the merge is read back. ⚠️ **What this step
releases is the tree and the local branch**, which no host setting reaches; the remote ref was
step 7's, under
[`§ 2`](../../config/schema.md#how-a-pull-request-lands)'s `delete_branch`.

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
  rather than what was attempted, and for the merge **both** reads: the change's state and whether
  the branch ref is gone;
- every one of § 2's preconditions that ran, and its verdict;
- which of step 7's four pre-merge establishments held, and what each found — the dependents, the
  base, the tree, and whether the tracker answered;
- the method the merge was performed with and that it was read rather than inferred, with what the
  host was found to permit; and which of the three `delete_branch` arms applied, so that a remote
  ref still standing reads as the configuration rather than as a deletion that failed;
- which port fallback was taken, where one was, and any sibling change that is holding the item
  where it is;
- ⛔ anything that could not be established, **named rather than omitted** —
  [`§ 11`](../../config/schema.md#a-report-names-what-it-could-not-establish)'s rule, which has no
  quiet form;
- ⛔ anything needing the person running this, **asked with the options**. The pass is not finished
  while a question it raised is open.
