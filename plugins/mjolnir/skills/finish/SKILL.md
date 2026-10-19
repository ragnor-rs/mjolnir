---
name: finish
description: Take a finished branch to a landed pull request — the commit, the push, the pull request, the host's answer about it, what this project counts as done and who answers each of those checks, the merge read back from state, the work item's own move, and the tree released. Use when asked to finish a work item, open or land its pull request, or merge the branch for an item.
argument-hint: "[<item number, item url, or pull request url>]"
---

# Finish a work item

The outcome is three facts, and each is **read back rather than asserted**: the change is merged,
the item has moved, and the tree is released. Everything below is ordered so that nothing
irreversible happens before the thing that would have stopped it — ⛔ **and what licenses the first
of the three is not this role's judgement** but the project's own statement of what counts as done
([`§ 13`](../../config/schema.md#13-what-counts-as-done--an-ordered-check-list-and-who-answers-each-check)),
one of whose checks may be a person's to answer and not this role's.

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
the host's own runs and what each of them mirrors, **what this project counts as done and who
answers each of those checks**, the closing capability behind the port, and the language and
register the pull request is written in. Each has a section of the surface and this file cites it.

Throughout, `<work-root>` is the tree the work is in — which
[`§ 10`](../../config/schema.md#where-the-work-happens) decides and this file does not — and every
`git` call names it, per § 1. ⚠️ **`§ N` always names a section of the surface, never one of this
file**; the steps below are referred to by number, because the surface has a § 6 and a § 7 of its
own and a bare number would resolve to the wrong one.

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

## 7. What counts as done

⛔ **A green gate is not a definition of done, and which checks are is the project's statement** —
[`§ 13`](../../config/schema.md#13-what-counts-as-done--an-ordered-check-list-and-who-answers-each-check),
read in step 1. ⛔ **This file states none of it**: which checks there are, who answers each one,
what each one's failure wants and what order they stand in are all configuration, and what that
order *means* is § 13's. An empty list is an answer and not a gap — completion is then the merge and
step 6's verdict, and the reply says so.

- ⛔ **Run it whole**, the way the starting role runs the readiness gate on the way in
  ([`§ 5`](../../config/schema.md#5-readiness-gate--an-ordered-predicate-list)): every check asked,
  every verdict reported, and a change failing two of them hears about both.
- ⛔ **A check carrying a command is run here and never handed over**, with the command and ⛔ **the
  tree it ran in** — [`§ 10`](../../config/schema.md#which-tree-a-verdict-belongs-to), the same rule
  step 5's test plan is held to. ⚠️ **A check the host already runs is a misconfiguration rather
  than a duplicate to skip**: the reader refuses it, naming the check and the workflow, so meeting
  one here is a stop with the configuration named and not something to work around.
- ⛔ **A check whose answerer is a person is not this role's to answer, and reading the diff is not
  an answer to it.** Read whatever record already exists — the reviewing role writes one for its own
  two questions, [`skills/review/`](../review/), and those are not these checks — or hand the check
  over with its own stop message and the state the change is in.
- ⛔ **And the answer that comes back is written down by this role, on the change, naming who
  answered and what they saw.** ⚠️ **This is the step that is easy to drop**, because the answer
  arrives in conversation and reads as received: a verdict living only in this reply is one the next
  pass cannot read ([`§ 11`](../../config/schema.md#a-role-boundary-is-a-window-boundary-and-the-artifact-is-what-crosses-it)),
  and § 13 asks for a record rather than a report. ⛔ **Nothing is ticked on the strength of an
  answer that was not recorded** — which is the same rule the reviewing role states for a plan item,
  one list over.
- ⛔ **A check that could not be answered is reported as unanswered, never as passed.**
  [`§ 11`](../../config/schema.md#a-report-names-what-it-could-not-establish), and the direction
  that matters: a check nobody could ask reads exactly like a check that passed.
- ⛔ **The order is what decides whether the next step happens.** A check standing before `merged`
  that failed, or that nothing could answer, is a **stop** — the merge does not happen, and the
  reply names which check and what it wants.
- ⛔ **`merged` is answered by step 8, and a check standing *after* it is answered once that read-back
  is in** — then reported with the rest, by the same rules as the ones before it. ⚠️ **The list is
  therefore walked twice where anything follows `merged`**, and a pass that walks it once has not
  asked those checks at all while its reply claims every check: § 13 permits entries on either side
  of `merged`, which is the whole reason it is a member of the list rather than the frame.

⛔ **Stopping here is not a failed pass and is not reported as one.** The change is not finished
yet, and ⛔ **what is left is named rather than summarised**. Which near misses read as finished to
whoever just produced them is
[`§ 13`](../../config/schema.md#in-progress-is-not-done-and-a-role-that-stops-mid-list-says-what-is-left)'s
own list, and this file does not carry a second copy of it.

## 8. The merge, and reading it back

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
   applies at the merge and not only at the commit.
4. ⛔ **That the tracker answers at all.** ⚠️ **A merge whose item never moved is invisible work**,
   and step 9 is where that is discovered — after the irreversible act. So the port is reached for
   a read **before** the merge, and an unreachable tracker holds it; `§ 3`'s fallback covers a
   capability that is *absent*, which is a different thing from a host that is not answering.

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

⛔ **The squash subject carries the references, and a host appends none of them to a subject it was
given.** Where the project's convention puts the item's number, or the change's own, in the subject
line of what lands, ⛔ **that subject is passed explicitly** — a host adds the change reference only
to a subject it generates itself, and omitting the subject on a one-commit branch squashes under
*that commit's* message instead, dropping the item reference. ⚠️ **No title check can catch
either**: it reads the change, and the squash happens after it passed. The subject is permanent on
the integration branch, so this is also the last chance to correct a title that overstates what
the change does.

⛔ **Ancestry answers in one direction only.** ⚠️ **The fourth of the four.** A true answer proves
the content landed; a false answer proves **nothing**, because a squashed or rebased merge rewrites
the commits and the branch's tip is then in no ancestry of the base. Trusting the false answer
reported five finished trees as carrying nine to twenty unpushed commits. So ancestry may confirm a
landing and may never contradict one — which is why the state read above, and not this, is what
settles whether the change is in.

⛔ **Then take step 7's list up where it continues past `merged`.** That state read is what answers
`merged`, so every check standing after it is answerable now and is asked here — never left for a
reply to claim.

## 9. The item's move

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

## 10. Release the tree

What is released once the work has landed is [`§ 10`](../../config/schema.md#10-branch-model)'s,
and a project's own setup and teardown are its `mechanics` pointer — ⛔ **named here, never
absorbed.** Where it is null there is nothing to run, and that is an answer.

⛔ **Confirm the landing from the host before removing anything**, per step 8 above — the tree and
the branch are the only copies of the work until the merge is read back.

⚠️ **A tree takes everything git does not track with it, and nothing records what that was.** Read
those files out before the removal or lose them; this is also why
[`§ 11`](../../config/schema.md#the-store-and-when-an-in-tree-store-is-safe) refuses an uncommitted
in-tree store under this branch model. ⛔ **A role cannot remove the tree it is standing in**: say
what is left to remove and where, rather than reporting a release that did not happen.

## 11. The reply

Register, and the language, are
[`§ 8`](../../config/schema.md#the-reply-to-the-person-running-a-role)'s — the outcome in the first
sentence, then the facts, with a table where the content enumerates.

- the three read-back facts: the merge, the item's move, the release — each with what was read
  rather than what was attempted, and for the merge **both** reads: the change's state and whether
  the branch ref is gone;
- every one of § 2's preconditions that ran, and its verdict;
- **every check the project's done list carries**, by name, with its verdict, who answered it and
  — for one carrying a command — the command and the tree it ran in; ⛔ every check that could not
  be answered said as unanswered, and an empty list said as empty rather than passed over;
- which of step 8's four pre-merge establishments held, and what each found — the dependents, the
  base, the tree, and whether the tracker answered;
- which port fallback was taken, where one was, and any sibling change that is holding the item
  where it is;
- ⛔ anything that could not be established, **named rather than omitted** —
  [`§ 11`](../../config/schema.md#a-report-names-what-it-could-not-establish)'s rule, which has no
  quiet form;
- ⛔ anything needing the person running this, **asked with the options**. The pass is not finished
  while a question it raised is open.
