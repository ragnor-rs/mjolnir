---
name: deploy
description: Put what has landed onto one of the project's own deploy targets and move the items it carried — the target read from configuration rather than from its name, a preflight that writes nothing, one go for this deploy, the project's own invocation, the delivery read from what the run printed rather than from how it exited, a batch assembled from the tracker and narrowed by the project's own command, the steps the batch's own changes owe performed where each one is placed — the ones owed before the script holding the invocation and the ones owed after it holding only the items resting on them — a release's grouping held to the role its items must already stand in, and the grouping marked released or the step handed to a person. Use when asked to deploy, to release, to ship to staging or production, to publish a batch, or to put the current branch on an environment.
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

⛔ **And which repository the act is in is the entry's `code_root`**, by
[`§ 33 → Which repository a target's act happens in`](../../config/schema.md#which-repository-a-targets-act-happens-in)
— read off the target and ⛔ **never off the item, the branch or the first of § 1's roots**. Every
call below that addresses a repository names it: the command root resolved in step 3, the workflow
and the ref a dispatch is made against, and the runs read in step 7. ⚠️ **Where the project carries
one repository the entry states none**, which is that subsection's own rule, and what every call
names is the one root there is.

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
  python3 "${CLAUDE_PLUGIN_ROOT}/scripts/config.py" --root "<the entry's code_root>" \
    --command "<the entry's command>" --command-root "<the entry's command_root>"
  ```

  What comes back is what to run, the directory to run it in and whether that directory is there —
  ⛔ **and a root reached through a form alone comes back `unestablished` rather than absent**, which
  is reported against the root and never retried at the code root. For a dispatch the same question
  is whether the workflow is one [`§ 2`](../../config/schema.md#2-code-host)'s `checks` carries and
  whether the host's own registry answers for it. ⛔ **Absent either way is a stop with the thing
  named**, and it comes **before** the target is confirmed rather than after.

  ⚠️ **`--root` is what the entry's `code_root` is for and the flag is omitted where it states
  none.** [§ 1](../../config/schema.md#a-command-root-is-not-a-code-root) states a command root
  relative to one repository, so on a project with two the reader **refuses** a read of the block
  that names no root — measured on the shipped two-root example, where this was the first command
  of this step and it stopped, with the value that would have answered it in no file.
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
- ⛔ **And where the entry carries a live data step, its own plan is taken here** — read-only, by
  § 35's own carrier, because *establish what is about to be invoked before the target is
  confirmed* reaches those commands exactly as it reaches the entry's:

  ```bash
  python3 "${CLAUDE_PLUGIN_ROOT}/scripts/live_data.py" plan --target "<the entry's name>"
  ```

  ⛔ **It runs none of them**, which is what keeps this inside the preflight. ⚠️ **It exits 3 where
  this target writes no live data**, which is the ordinary case rather than a failure: the deploy is
  exactly what § 33 states, step 5a does not run, and the reply says the target states no step
  rather than that the step found nothing to do. ⛔ **A step the configuration could not be read for
  is a stop before the go**, named with the key.

## 4. The batch, what the item side of it is, and what the changes owe

**4a. The batch.** ⛔ **Two sources and neither alone is the batch**, by
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

- ⛔ **The grouping's own value arrives on this role's invocation, and never by a guess** —
  ⚠️ **under either value of
  [`§ 4.8`](../../config/schema.md#48-grouping--what-a-set-of-items-is-planned-into)'s `current`,
  because the read that key's other arm describes is performed by nothing**
  ([`§ 33`](../../config/schema.md#publishing-a-grouping-and-the-precondition-that-holds-the-whole-target)
  states that limit). So an invocation that named a grouping and no value is a **stop asking for the
  value**, with the options where the project's own records name them — and the port refuses it
  against that key rather than against an argument list, which is the message to report.
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

**4b. What the changes in the batch owe this target**, where
[`§ 20`](../../config/schema.md#20-the-sections-a-pull-request-body-must-carry) puts it: a section
one role writes and this one collects out of every change the batch carries. ⛔ **Collected here
and performed where each entry's `when` puts it** —
[`§ 33`](../../config/schema.md#what-a-change-in-the-batch-owes-this-target-and-where-the-step-falls)
states which, and this file chooses neither. A project whose `body_sections` is `[]` has nothing to
collect, which is a stated configuration rather than a change that owed nothing.

⛔ **The reading is the gate's own and is never made by eye**, which is what the collecting mode of
the shipped checker is for: whether a section states work or closes with the project's *nothing*
answer turns on a normalisation — a list marker, a trailing period, the emphasis a body wraps a
line in, its case — and a role reading the section itself is a second grammar, free to disagree with
the run that held the same body on the host.

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/check_body_sections.py" --collect \
  --body-file <the change's body, as the host holds it> --skills-root <the skills root>
```

- **It is no verdict about the change** and its status is not one: the gate is what holds a body,
  and a section it reports `unheld` is that run's answer to give rather than this one's.
  ⛔ **An `unheld` section is a step this role cannot establish either way**
  ([`§ 11`](../../config/schema.md#a-report-names-what-it-could-not-establish)), reported as that
  and never as answered — ⚠️ **and which bodies read that way is the gate's own list and is not
  copied here**, a second statement of it in a role being free to disagree with the run.
- **It exits 3 where the project states no section**, which is the stated absence and not a run
  that found nothing.
- ⛔ **One change at a time, and every change in the batch.** A step is owed by one change, so a
  reading taken over fewer changes than the batch carries is a step nobody collected.

**Then the `before` steps are performed, and this is the last thing that happens before the go.**
⛔ **Nothing is invoked while one stands unperformed**, by § 33's own table:

| the entry says | what this step does |
|---|---|
| `answered_by: procedure` | runs what the section states, as the section states it, and reports what it printed — ⚠️ **no key places a step's own command**, so a section stating one states where it runs ([`§ 33`](../../config/schema.md#what-a-change-in-the-batch-owes-this-target-and-where-the-step-falls)) |
| `answered_by: human` | ⛔ **asks**, showing the step, the change it came out of and the target — and ⛔ **silence is not a yes**: the step stays unperformed |

- ⛔ **The ask here is not step 5's go and is put before it**, which is § 33's rule rather than this
  file's: a go authorizes an act and this answer attests work that either happened or did not, and
  ⚠️ **a target stating `not_live: true` is asked for no go at all** while its changes may still owe
  a `human` step.
- ⛔ **A step left unanswered stops the deploy with the step and its change named**, and the reply
  reports it as unperformed rather than as a deploy that failed. ⚠️ **Nothing is retried and nothing
  is assumed**: the one thing this role must never do is read a step it could not get an answer
  about as a step nobody needed.
- ⛔ **A `procedure` step that failed stops the deploy too**, and for the same reason the row above
  gives: what it was going to prepare is not there, and the invocation is what would discover that
  on a live machine.
- **The `after` steps are not performed here** and are carried to step 7, which is where § 33 puts
  them — reported now so that step 5's ask shows what the deploy still owes once it has run.

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
every item in the batch, every candidate step 4a could not place, and ⛔ **every `after` step the
deploy will still owe once it has run** — the `before` ones having been performed or stopped on in
step 4b, so a go reached at all is a go over a target nothing is holding.

⛔ **A go that goes to the port carries what it is for.** Where the shape is `dispatch`, the port
refuses a go that does not name this workflow, this ref and every input — and ⛔ **the words are
never composed to satisfy it**, which would be filling in a form rather than having an approval.

## 5a. The live data step, where the target carries one

⛔ **The facet is [`§ 35`](../../config/schema.md#35-the-live-data-step-a-deploy-performs-and-the-rails-it-is-performed-under)
and this file states none of it again**, for the reason it restates no part of § 33. ⛔ **And the
ordering is not performed here either**: a role free to reach the write before the dump has been
read back is a role with no rail at all, so the sequence is the carrier's and this step asks it.

⛔ **The plan was taken in step 3 and is not taken again here.** § 33 puts establishing what is
about to be invoked **before** the target is confirmed, and this step's commands are no different: a
rehearsal that is not there has to stop the deploy earlier than the go rather than after a dump has
already been taken.

- ⛔ **Lettered rather than numbered because its position is the configuration's.** `order` states
  which side of step 6 the whole of this step falls on — `before_invoke` runs it here, and
  `after_invoke` runs it once step 6 has come back. ⛔ **Neither is this role's to choose**, and
  ⚠️ **a role that read the pending writes to decide would be judging whether the new code requires
  the schema**, which is that project's knowledge of its own code.
- ⛔ **The order taken is named in the go below**, so the person rules on it rather than discovering
  it. The configured value is what this role proposes.

**The preparation, which stops on its own:**

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/live_data.py" prepare --target "<the entry's name>"
```

- ⛔ **A non-zero exit is a stop for the deploy and not for the step**, and the carrier names which
  of the sequence it stopped at. Nothing after it runs and step 6 is not reached.
- ⛔ **The rehearsal's output is read**, which is what the step is for: a role that ran it and
  parsed nothing performed a ritual. ⚠️ **A target stating no rehearsal is reported as *no
  rehearsal*** and never as a clean one, and the go below is asked with that said.
- ⚠️ **The carrier reads no word out of that output** — § 35 makes the exit status the verdict —
  so what the output says is a **person's** reading and this role carries it to them verbatim.

**Then the go, which is a second ask and is not § 33's:**

⛔ **Asked here because the evidence did not exist when step 5's question was put**: a verified dump
and a rehearsal's output. The test is
[`§ The loop`](../../config/schema.md#what-carries-the-item-forward-and-where-it-stops-to-ask)'s —
the write cannot be taken back — and ⛔ **no key turns it off**, `apply_by` deciding only who runs
the command once it is recorded.

**Show, in the question:** the target, that the entry states it live, the dump's path or name and
that it was read back, the rehearsal's output **whole** or that there was none, the order being
taken and that it is the configured one, and who the entry says performs the write.

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/live_data.py" apply --target "<the entry's name>" \
  --given "<their answer, in their words>"
```

⚠️ **The flag is `--given`, which is this toolkit's own word for an answer a gate reads back** —
and not the shorter spelling, which the names check reads as the build tool of the same name and
refuses the whole command. A false refusal renamed around rather than argued with.

- ⛔ **The go is handed over as they wrote it and is never composed to satisfy the carrier.** It
  refuses one that names neither the target nor the rehearsal's verdict, and ⚠️ **that refusal is
  reported rather than worked around**: a role that filled in the wording would have a form and not
  an approval.
- ⛔ **Silence is not a yes.** Nothing is invoked, the deploy stays unmade, and the reply says the
  question went unanswered.
- ⛔ **Where `apply_by` is `person` the carrier makes no write and hands the command over**, and the
  reply reports **no apply made** in those words — § 33's `by_hand` one level down.
- ⛔ **Where the write ran and failed, what the store is left holding is named rather than
  omitted**, along with the dump a recovery reads. ⚠️ A command that exited zero is still a fact
  about the invocation and not about the store.

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

⛔ **Every call to the runs port names the entry's own repository**, which is the `--root` flag
carrying what the entry's `code_root` states and omitted where it states none — the dispatch here,
and the conclusion and the log read in step 7.
[`§ 29`](../../config/schema.md#29-the-hosts-run-operations)'s kind sits in a block a root may
narrow, and the slug a dispatch is made against is
[`§ 1`](../../config/schema.md#a-projects-code-is-not-always-one-repository)'s per-root fact: on a
project with two repositories, a dispatch naming neither would be made against whichever the port
answered with.

## 7. Verify, then perform the `after` steps step 4b collected

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
  classification and launching them is not this role's but the reviewing one's
  ([`§ The loop`](../../config/schema.md#what-carries-the-item-forward-and-where-it-stops-to-ask)):
  ⛔ **report which ran, by name**, and report
  one that skipped as *the gate did not run* rather than as *the gate passed*.
- **Then the `after` steps, and only those** — the `before` ones were performed in step 4b, and
  ⛔ **a step placed `after` is never brought forward to here from there or the other way round**,
  the place being the entry's own fact. In whatever order the project's own record gives, and
  ⛔ **after the delivery has been read** rather than beside it: a step that prepares nothing for
  the invocation has no reason to run before the invocation is known to have landed.
- **The same two answerers as step 4b**, read off the entry: `procedure` runs what the section
  states, and ⛔ **`human` asks** — ⚠️ **asked here even on a target stating `not_live: true`**,
  since the go that would have carried the question is one such a target is never asked for.
  ⛔ **A command finishing is not a step finishing**: anything that queues work has barely started
  when the command exits, so it is judged on progress and reported as still running with the
  readings it was judged on.
- ⛔ **An `after` step that failed, or that nothing answered, holds the items resting on it** rather
  than the deploy — which is
  [`§ 33`](../../config/schema.md#what-a-change-in-the-batch-owes-this-target-and-where-the-step-falls)'s
  second row rather than this file's choice, the act being one nothing can take back. The target is
  deployed either way; what is withheld is the move, and the reply says which items and what they
  wait on.
- ⛔ **The answer is recorded with the step and the change it came out of, and never inferred from
  the deploy having succeeded.** What the record is here is the reply —
  ⚠️ **no guard reads it**, which § 33 states rather than this file, so a reader weighing the
  deploy is reading this role's own report and nothing stronger.

## 8. Advance the batch

⛔ **An entry whose `advances` is `none` moves nothing, and this step does not run.** The batch is
still reported — what the deploy carried is a fact about the deploy — and ⛔ **the reply says the
target writes nothing on an item** rather than leaving a reader to read silence as a failed move.

⛔ **Otherwise: only the items step 4a put in the batch, and only once step 7 came out clean for
each** — which includes every `after` step that item's own change owes. The move goes through the
port, asked for as a **role** and never as a status word, and this role asks as the writer the
deploy is:

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
  taken in step 4a is not reused: a step backwards can land between the two.
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
- what was resolved — the project, the configuration file, and ⛔ **which of
  [`§ 1`](../../config/schema.md#a-projects-code-is-not-always-one-repository)'s repositories this
  target's act is in, read off the entry's own `code_root`** and named with the repository slug it
  resolved to. ⚠️ **Where the project carries one, that it states none and there is one answer** —
  a reply naming the project alone has said nothing about which half of a two-repository project
  was written to;
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
- **every step collected out of a change** — the section it came from and which change, where its
  entry placed it, who its entry says answers it, and whether it ran, is still running with its
  readings, was answered, or is **unperformed**. ⛔ **Unanswered is reported as unanswered**, never
  as a step nobody needed, and ⛔ **a section the collecting reading reported `unheld` is reported
  as a step this role could not establish either way**;
- ⛔ **what a `before` step stopped, where one did** — the step, the change, and that nothing was
  invoked, which is not a deploy that failed; and ⛔ **which items an `after` step is holding**,
  with what each waits on;
- ⛔ **what was not verified**, named rather than omitted
  ([`§ 11`](../../config/schema.md#a-report-names-what-it-could-not-establish)): every skipped
  scenario, every tier that did not run, and everything a log did not cover;
- ⛔ **the live data step, where the target carries one** — that the dump was verified and by what,
  whether a rehearsal ran at all, what its output was read as, which order was taken and whether
  the configured one was overruled, and whether the write ran or was handed over. ⚠️ **A target
  stating no step says so**, by
  [`§ 35`](../../config/schema.md#35-the-live-data-step-a-deploy-performs-and-the-rails-it-is-performed-under),
  rather than being left out of a reply a reader then reads as a deploy that wrote nothing;
- ⛔ **what the deploy left standing** — a version spent, a branch ahead of what the target serves,
  work queued behind the command that queued it, and ⛔ **what a live store is left holding** where
  the write ran and failed;
- ⛔ anything that needs the person running this, **asked with the options**
  ([`§ Nothing is deferred`](../../config/schema.md#nothing-is-deferred)): a target that could not
  be chosen, a precondition nobody can supply, a batch nothing could assemble. Nothing is noted for
  later.
