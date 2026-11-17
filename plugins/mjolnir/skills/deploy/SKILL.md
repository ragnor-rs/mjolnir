---
name: deploy
description: Put what has landed onto one of the project's own deploy targets and move the items it carried — the target read from configuration rather than from its name, a preflight that writes nothing, one go for this deploy, the project's own invocation, the delivery read from what the run printed rather than from how it exited, and a batch assembled from the tracker and narrowed by the project's own command, a release's grouping held to the role its items must already stand in, and the grouping marked released or the step handed to a person. Use when asked to deploy, to release, to ship to staging or production, to publish a batch, or to put the current branch on an environment.
argument-hint: "[<the target's name>]"
---

# Deploy to one of this project's targets

The outcome is a target carrying what was deployed, **read back rather than reported off an exit
status**, and every item the deploy carried moved exactly one role forward — with everything it did
not carry, did not verify and did not finish named in the reply.

⛔ **This role states no host, no service, no credential, no build step and no health check.** Every
one of those is the project's, reached through what its target states and never learned here, by
[`§ What the procedure models`](../../config/schema.md#what-the-procedure-models-and-what-it-only-names-and-calls).
⚠️ **Measured over every deploying carrier in the survey and found local in all of them**, which is
why this role is short and the copies it was extracted from are not.

⛔ **The facet is [`§ 33`](../../config/schema.md#33-the-deploy-targets-and-what-reaching-one-invokes)
and this file states none of it again.** A copy of a rule here is a second authority allowed to
disagree with the one the reader performs.

## 1. Resolve, and say what was resolved

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/config.py"
```

⛔ **Say which project was resolved before anything else**, as every role on this route does: run
from a sibling project with a configuration of its own, this role deploys **that** project.

⛔ **Read the `unavailable` list before acting on anything.** A project stating `deploy: []` is a
**stop naming that key** — it deploys nothing through this procedure, which
[`§ 33`](../../config/schema.md#33-the-deploy-targets-and-what-reaching-one-invokes) makes a stated
configuration rather than a gap, and ⛔ **never an invitation to improvise a command**.

⚠️ **What the shell holds is reported by the starting role once per item** and is not re-read here;
what this role does report is every value it could not establish, which is step 10.

## 2. Which target

**Named on the invocation** — the argument is the target's `name`, and a name the facet does not
carry is a stop listing the names it does.

**Nothing named** — ⛔ **ask, with the targets as the options.** A project carrying one target still
gets the question, because the ask in step 5 is about *this deploy* and a target chosen silently is
a deploy nobody named. ⚠️ **A target is not picked by what it is called**: whether it is live is the
entry's own `not_live`, read there and never inferred, and the reply says which the entry stated.

What the item side of this is comes from the port, and its absences carry their own fallbacks:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/port.py"
```

⛔ **Take each absent operation's stated fallback and improvise none**
([`§ 3`](../../config/schema.md#the-operations-and-what-an-absent-capability-does)). Where
`read_item` is unavailable the batch is reported unverified rather than assembled from what the
command alone said; where `set_state` is unavailable every move is reported for whoever makes it.

## 3. Preflight, which writes nothing

⛔ **Nothing is staged, nothing is checked out and nothing on any machine is touched.** The rule and
its one measured exception are
[`§ 33 → What runs before the target is confirmed`](../../config/schema.md#what-runs-before-the-target-is-confirmed-and-what-it-may-not-do);
what this step does is run it.

- **What is about to be invoked is established first**, and the resolution is the reader's rather
  than this role's:

  ```bash
  python3 "${CLAUDE_PLUGIN_ROOT}/scripts/config.py" \
    --command "<the entry's command>" --command-root "<the entry's command_root>"
  ```

  What comes back is what to run, the directory to run it in and whether that directory is there —
  ⛔ **and a root reached through a form alone comes back `unestablished` rather than absent**, which
  is reported against the root and never retried at the code root. For a dispatch the same question
  is whether the workflow is one [`§ 2`](../../config/schema.md#2-code-host)'s `checks` carries and
  whether the host's own registry answers for it. ⛔ **Absent either way is a stop with the thing
  named**, and it comes **before** the target is confirmed rather than after.
- **Every `requires` the entry states is read.**
  [`§ 16`](../../config/schema.md#16-what-a-run-executed-and-the-count-that-is-the-only-evidence-it-ran)
  states what that list is; what this step does is report each as present or **named as absent**.
  ⛔ **An absent one is never worked around** — a store the repository may not hold is
  [`§ 28`](../../config/schema.md#28-a-configured-value-a-repository-may-not-hold)'s shape, and a
  file written empty in its place is worse than no deploy.
- **The tree is read and left alone.** What is uncommitted is reported, and
  [`§ 10`](../../config/schema.md#which-tree-a-verdict-belongs-to)'s rule decides what a verdict
  taken here is about. ⚠️ **Several sessions may share one checkout**, so a preflight that staged
  anything would be staging somebody else's work.
- ⚠️ **A command target may contend on something the project declared exclusive**
  ([`§ 10`](../../config/schema.md#exclusive-resources)). A refusal there is a place to come back
  for rather than a failure: the deploy is retried once one frees, and the reply says it waited.

## 4. The batch, and what the item side of it is

⛔ **Two sources and neither alone is the batch**, by
[`§ 33 → The batch`](../../config/schema.md#the-batch-and-the-two-ways-of-assembling-one-that-are-wrong):
the entry's `batch` command names the candidates, and each candidate's **role is read from the
tracker at the point it is advanced** in step 8 — never from a value read here.

- Run the command, read the identifiers it printed, and ⛔ **say in the reply that it is the only
  source of candidates**, so that *nothing owed* and *nobody looked* are not one sentence.
- A candidate the tracker does not answer about is reported **unanswered**, never dropped.
- ⛔ **An entry whose `advances` is `none` still has a batch worth reporting** where the project
  states a command, and has none where it does not — in which case the reply says the deploy
  carried no readable set rather than that it carried nothing.

**And where the entry names a grouping, the publishing set is read here too** — the set
[`§ 33 → Publishing a grouping`](../../config/schema.md#publishing-a-grouping-and-the-precondition-that-holds-the-whole-target)
narrows the advance to and holds the precondition over:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/port.py" \
  --in-grouping "<the entry's grouping>" --argument "<the grouping's own value>"
```

- ⛔ **Which value is [`§ 4.8`](../../config/schema.md#48-grouping--what-a-set-of-items-is-planned-into)'s
  `current`, and never a guess**: a grouping the tracker marks as the open one is read, and one a
  project holds several of at once **arrives on this role's invocation** — so a target naming such a
  grouping with no value handed over is a stop asking for it, not a pick.
- ⛔ **A grouping that could not be read is reported unread, never as holding nothing.** § 3's
  fallback for the operation says what happens instead, and ⚠️ **an unread set and an empty set are
  the same list** — which is why the reply says which it was rather than how long it was.
- ⛔ **An item in the batch the grouping does not hold is named and not advanced**, and an item the
  grouping holds that the batch never named is named too: the batch stays the only source of
  candidates, and the grouping is what narrows them.

**And the precondition, where the entry states one** — ⛔ **read before step 5's go and not after
it**, a release held by an unaccepted item being a release nobody should have been asked about:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/port.py" \
  --short-of "<the entry's requires_role>" --in-grouping "<the entry's grouping>"
```

- ⛔ **Where the entry names no grouping the same question is asked over the batch's own
  candidates** — `--short-of <role> --argument <each identifier>`, which is § 33's other arm and not
  a weaker form of this one.
- ⛔ **Anything short holds the whole target and nothing is invoked.** The reply names **every** such
  item with the role it stands in, never the first, and ⛔ **the remedy is not this role's**: § 4.2
  maps that role to a status somebody else writes, so the stop is reported and the deploy ends.
- ⛔ **An item the answer could not place is a stop too**, by
  [`§ 11`](../../config/schema.md#a-report-names-what-it-could-not-establish): a release held by an
  item nobody could place reads exactly like a release held by nothing.
- **A target stating `requires_role: none` has no precondition and this reads nothing**, which is a
  stated configuration rather than a check that passed.

**And what the changes in the batch owe the target is collected here**, where
[`§ 20`](../../config/schema.md#20-the-sections-a-pull-request-body-must-carry) puts it: a section
one role writes and this one collects out of every change the batch carries. ⛔ **Collected now and
run in step 7**, never before the go — and a project whose `body_sections` is `[]` has nothing to
collect, which is a stated configuration.

## 5. Ask, once, where the act is the person's

⛔ **One question, for this deploy, and the entry's `not_live` is what decides whether it is put.**
The test is
[`§ The loop`](../../config/schema.md#what-carries-the-item-forward-and-where-it-stops-to-ask)'s —
whether the act is the person's — and
[`§ 33`](../../config/schema.md#which-target-and-what-makes-one-live) is where this role reads the
answer. ⛔ **An earlier go clears nothing**: an approval obtained for another ref, another input or
another batch is not one for this.

| the entry says | what this step does |
|---|---|
| `not_live: false` | **asks**, and silence is not a yes: nothing happens, and the reply says the question went unanswered |
| `not_live: true` | **does not ask** — the session is the only user of what it is about to touch, and a question there is the interruption § The loop retired |
| any target reached by `dispatch` | **asks regardless**, because § 29's refusal sits on the operation and reads no facet |

**Show, in the question:** the target and that the entry states it live, what is being deployed,
every item in the batch, every candidate step 4 could not place, and every preparation step still
owed.

⛔ **A go that goes to the port carries what it is for.** Where the shape is `dispatch`, the port
refuses a go that does not name this workflow, this ref and every input — and ⛔ **the words are
never composed to satisfy it**, which would be filling in a form rather than having an approval.

## 6. Invoke what the target states

⛔ **Whichever shape `invoke` states, and this role chooses none of them**
([`§ 33`](../../config/schema.md#the-three-shapes-a-target-is-reached-by)). ⚠️ **No count of them
is written here**, the alternation being the statement.

| the entry says | what happens here |
|---|---|
| `command` | the command is run **whole**, in the root the entry names; nothing is prefixed to it and nothing is read out of it |
| `dispatch` | the run is asked for through the port, against the entry's `ref` and carrying its `inputs` |
| `by_hand` | ⛔ **nothing is run.** The workflow, the ref and every input are handed over, and the reply reports **no deploy made** |

⚠️ **A dispatch made inside the port is not a shell call**, so the rails that read one — § 19's and
§ 21's — never saw it. ⛔ **Stated rather than relied on**: the go in step 5 is what stands in that
place, which is why it is asked for every target.

## 7. Verify, then run what step 4 collected

⛔ **What came back is not what was delivered.** A command that exited zero, a build the host
reported successful and a run that concluded green are each a fact about the invocation —
[`§ 29`](../../config/schema.md#a-dispatch-is-the-only-write-and-it-carries-its-own-go) states it
for a dispatch and
[`§ 33`](../../config/schema.md#what-a-deploy-verifies-and-what-it-reports) states it for this role.
What a run delivered is read from its **log**, through the port's own operation, and reported
**unverified** where there is none.

- **What is read is the project's and is named rather than described.** Where the verification is a
  suite, which tiers ran is
  [`§ 31`](../../config/schema.md#31-test-tiers--what-each-one-needs-before-it-can-run-at-all)'s
  classification and launching them is not this role's: ⛔ **report which ran, by name**, and report
  one that skipped as *the gate did not run* rather than as *the gate passed*.
- **Then run the preparation step 4 collected**, in whatever order the project's own record gives.
  ⛔ **A command finishing is not a step finishing**: anything that queues work has barely started
  when the command exits, so it is judged on progress and reported as still running with the
  readings it was judged on.
- ⛔ **A preparation step that failed holds the items resting on it** rather than the deploy. The
  target is deployed either way; what is withheld is the move, and the reply says which items and
  what they wait on.

## 8. Advance the batch

⛔ **An entry whose `advances` is `none` moves nothing, and this step does not run.** The batch is
still reported — what the deploy carried is a fact about the deploy — and ⛔ **the reply says the
target writes nothing on an item** rather than leaving a reader to read silence as a failed move.

⛔ **Otherwise: only the items step 4 put in the batch, and only once step 7 came out clean for
each.** The move goes through the port, asked for as a **role** and never as a status word, and this
role asks as the writer the deploy is:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/port.py" \
  --advance-to "<the entry's advances>" --argument "<the item>" --as-writer deploy
```

⛔ **That flag is the only route to the move, and naming the operation underneath it is refused** —
the writer guard sits inside the role resolution, so an invocation that named `set_state` would be
writing a status word this role chose, which is what
[`§ 3`](../../config/schema.md#3-tracker-port) forbids a role twice over.

- ⛔ **Each item's current role is read where it is advanced**, which is
  [`§ 32`](../../config/schema.md#32-a-status-that-moves-backwards)'s rule and the reason a reading
  taken in step 4 is not reused: a step backwards can land between the two.
- An item whose role is not the one this target's advance is made from is **named and not moved**.
- ⛔ **A refusal naming another writer is the configuration working**, not an obstacle: the move is
  reported for that writer to make, and nothing is written.
- ⛔ **An item the tracker already holds at the role this target advances to, or past it, is named
  and left alone** — the move a merge's automation made and the move this target makes are different
  edges, and writing the second over the first is the double transition
  [`§ 33 → Publishing a grouping`](../../config/schema.md#publishing-a-grouping-and-the-precondition-that-holds-the-whole-target)
  rules out. ⛔ **Which items those are is read and not judged**, by the same question the
  precondition is asked with, aimed at this target's own `advances`:

  ```bash
  python3 "${CLAUDE_PLUGIN_ROOT}/scripts/port.py" \
    --short-of "<the entry's advances>" --argument "<each item in the batch>"
  ```

  Everything it reports **short** is an item to advance; everything it placed and did not report
  short is already at that role or past it, and is named rather than written to. ⚠️ **An item it
  could not place is advanced by nothing and reported unplaced** — the same direction the
  precondition takes, for the same reason.
- ⛔ **Nothing else about an item is touched.** Not its text, not a label, not a date — which is
  [`§ An artifact states what is true now`](../../config/schema.md#an-artifact-states-what-is-true-now)
  answered by the wrong party if it were.

## 9. Mark the grouping released, where the entry publishes one

⛔ **A target whose `publishes` is `false` marks nothing, and this step does not run** — the reply
says the target publishes no grouping rather than leaving silence to be read as a mark that failed.

⛔ **Otherwise the mark goes through the port, and the writer read is
[`§ 4.8`](../../config/schema.md#48-grouping--what-a-set-of-items-is-planned-into)'s `closed_by`
and never a status's**:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/port.py" \
  --mark-released "<the entry's grouping>" --argument "<the grouping's own value>" \
  --as-writer deploy
```

⛔ **That flag is the only route to the mark, and naming the operation underneath it is refused** —
the writer guard sits inside the resolution, exactly as step 8's does for a status.

- ⛔ **The two writers are honoured independently**: a close refused for its writer says nothing
  about the items, and items refused for theirs say nothing about the close. The reply reports both.
- ⛔ **Where the capability is absent the run names the step and the grouping it is about, by the
  value this deploy read, continues, and the reply records the grouping as still open.** That is
  [`§ 3`](../../config/schema.md#the-operations-and-what-an-absent-capability-does)'s stated
  fallback and ⛔ **never a grouping reported as marked**, nor a step dropped in silence — it is the
  one write that tells everybody else the release happened. ⚠️ **No address is composed for it**:
  where a person goes to mark it is the tracker's own fact, which
  [`the boundary`](../../config/schema.md#what-the-procedure-models-and-what-it-only-names-and-calls)
  bars this role from inventing.
- ⛔ **After step 8 and not before it.** A grouping marked released over items that did not move is
  a release announced for work the tracker still shows as unreleased.

## 10. The reply

Register and language are
[`§ 8`](../../config/schema.md#the-reply-to-the-person-running-a-role)'s — the outcome first, then
the facts, with a table where the content enumerates.

- **the verdict, first sentence** — deployed · deployed with items held · deployed with the grouping
  still open · handed over · stopped, and on what;
- **the target by name, and whether the entry states it live** — ⛔ never the name alone, which says
  nothing a reader can check against the entry they meant;
- what was resolved — the project, the configuration file, and the code root this target's
  invocation runs against;
- **what was invoked**, in the shape the entry states, and for `by_hand` ⛔ **that no deploy was
  made** along with everything handed over;
- **how the delivery was established** — what was read, and from where. ⛔ Never an exit status
  standing in for it;
- **every item advanced**, and **every item in the batch that was not**, with what held it —
  ⛔ including every item left alone because the tracker already held it at or past that role;
- **every candidate the batch command named that the tracker answered differently about**, and
  ⛔ **that the command is the batch's only source of candidates**;
- **the grouping this target was scoped to, and whether it was read** — ⛔ never its length alone,
  an unread set and an empty one being the same list; the value it was read at, and where that value
  came from (the tracker's own mark, or this role's invocation);
- **whether the grouping was marked released** — marked, **refused** with the writer named, or
  ⛔ **still open with the step and the address handed over**, which is the capability absence and
  not a failure. ⚠️ Reported beside the items' own outcome and never folded into it: the two writers
  are read independently;
- **the precondition, where the entry states one** — the role required, and ⛔ **every item short of
  it with the role it stands in**, plus every item the answer could not place. Where the entry
  states `requires_role: none`, that there was none rather than that one passed;
- **every preparation step collected** — which change it came from, and whether it ran, is still
  running with its readings, or is owed;
- ⛔ **what was not verified**, named rather than omitted
  ([`§ 11`](../../config/schema.md#a-report-names-what-it-could-not-establish)): every skipped
  scenario, every tier that did not run, and everything a log did not cover;
- ⛔ **what the deploy left standing** — a version spent, a branch ahead of what the target serves,
  work queued behind the command that queued it;
- ⛔ anything that needs the person running this, **asked with the options**
  ([`§ Nothing is deferred`](../../config/schema.md#nothing-is-deferred)): a target that could not
  be chosen, a precondition nobody can supply, a batch nothing could assemble. Nothing is noted for
  later.
