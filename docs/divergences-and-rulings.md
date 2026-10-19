# Divergences between the old copies, and how each was settled

Before this toolkit existed, each project carried its own copy of each process role, and **no two
copies of any role were identical**. One role ran 71 to 229 lines across its copies, another 99 to
247, a third 81 to 142. Line count that far apart is divergent behaviour, not formatting.

This document records what differed and which behaviour was kept. It exists because **every
divergence was resolved by a decision rather than by taking whichever copy was longest or most
recent**, and a decision nobody wrote down reads later as an oversight.

**This is the decision record, not the rule.** The binding statement of each ruling's outcome is
[`../plugins/mjolnir/config/schema.md`](../plugins/mjolnir/config/schema.md) — or, for a role
not yet extracted, **the numbered work item** that will carry it — and each ruling below names
where its outcome lives. Where this record and that statement disagree, this record is stale.

Those are the only two homes a ruling's outcome may have, and the `Single source of truth`
workflow holds the table to it: a cell naming a document instead is this record becoming a
second authority for the rule, and a cell naming an unnumbered work item cannot be resolved by
anyone asking whether the outcome has moved yet. One ruling below adds `the skill` **beside** a
section, for an outcome split between the surface and the skill that carries it; that is
permitted alongside a home and never instead of one.

Projects are referred to as A–F. Naming them is forbidden here.

---

## 1. Hard contradictions — opposite instructions, each held deliberately

Seven questions on which two copies gave opposite answers, each with a stated reason. None could
be resolved by preferring the longer or the newer file.

| # | Question | The positions found |
|---|---|---|
| 1 | Staging a commit | **Never stage everything**; name paths. Reason: parallel sessions, secrets, build output — against — **always stage everything**, never cherry-pick. Reason: no reviewer and no branch, so an unstaged file is simply missing next session. A third copy staged everything *unless* it would sweep unrelated artifacts |
| 2 | Commit message mechanism | A heredoc into a **temporary** path, committed from the file. Reason: a fixed path is a race between two sessions — against — **never a heredoc and never a file**, use repeated message flags. Reason: heredocs persist as literal permission-allowlist entries, with two upstream issue numbers cited. A third copy used a heredoc into a **fixed** path |
| 3 | Commit message style | Match the recent log's style — against — **do not read history for style cues**; concise wins regardless |
| 4 | Do rework and overhead count toward logged hours? | **No** — five exclusions, cutting hours *and* wording — against — **yes**, three exclusions, with overhead counting toward hours and merely absent from the wording |
| 5 | The half-hour rounding tie | An exact quarter rounds **down** — against — an exact quarter rounds **up** |
| 6 | May the bookkeeping role write to the tracker? | A full sweep including a terminal state — against — **only** the in-flight state — against — **no writes at all**: read, compare, report |
| 7 | A dirty tree at start | **Abort** — against — **report and continue**, because the branch goes in a fresh worktree so nothing here is touched |

Two structural observations shaped the rulings:

- **(1) and (2) interact.** Position A on both is coherent and so is position B on both, but A on
  staging with B on the message mechanism loses the multi-paragraph message entirely.
- **(4) and (5) are the same disagreement twice** — whether the log measures delivery or time
  spent. Deciding that once settles both. (5) matters additionally because one project's checker
  *enforces* the grid and would fail another project's files outright.
- **(6) was never really a contradiction.** It is the status-writer model, correctly configured
  three different ways. It belongs in configuration, and that is where it went.

## 2. One copy knew strictly more — keep the richer behaviour, port it everywhere

Each row is a correction somebody paid for once, present in one or two copies and absent from the
rest. **The value of extraction is mostly here**, not in the reduction in line count.

| Capability | Copies that had it | What the others lost |
|---|---|---|
| **Three-layer duplicate search** — keyword axes, a keyword-independent component sweep, semantic tiering by meaning, then a confidence-tiered human gate | 2 of 4 | Reworded duplicates. One copy cites the incident: an item created despite an existing one. Two copies had keyword search only |
| **Parent-not-duplicate detection** — the request is a *piece* of an open item, so it becomes a check item rather than a new item | 1 | A failure that "reads exactly like a clean duplicate check": the parent title is broad, the request is specific, and no query connects them |
| **Non-lossy update path** on a confirmed duplicate | 1 | — and it contradicts another copy, which mandates rewrite-never-append. Both stated reasons, so this became an eighth contradiction |
| **Multi-item decomposition** with an explicit confirmation of the split | 2 | One request silently becomes one item |
| **Push safety** — a bare push only where the branch tracks a remote of **the same name**, because a branch cut without disabling tracking tracks the base and a bare push can write to it | 1 of 5 | Three copies carried the unsafe form verbatim |
| **Pagination** — a first-page query is a ceiling, and the host CLI's paginate flag does **not** help, because it follows top-level pagination rather than a nested items connection. A round-100 total is the signature of an unfollowed cursor | 1 explained it, 1 warned without the mechanism, 2 had neither | Silent truncation of the board. Measured twice in one project |
| **An open pull request already populates the "what would close this" reference** | 1 | A sweep that asserts a merge which never happened |
| **Argument resolution** — a bare number, an item URL or a pull request URL, and an argument disagreeing with the branch is a stop reporting both values | 1 of 5 | Silently working on a different item than the one named |
| **CI-answer preconditions** — the tree is clean, a run exists for this commit, the run *executed steps* (a billing-suspended run fails in seconds having started none), and it concluded green | 1 | Treating absence of signal as green |
| **Query alias collision** — each field read in one query needs a unique alias or the query throws | 1 | Only bites when reading more than one field, which is why the others never hit it |
| **Verify the merge landed** — both success and refusal can print nothing, so read the state back from the item or the remote ref, never from the exit status | 1 | A merge that *had* landed, reported as not having |
| **Ancestry is trustworthy in one direction only** — a true answer proves content landed; a false answer proves nothing, because the base is rebased and hashes are rewritten | 1 | Reported five finished trees as carrying 9–20 unpushed commits |

## 3. Harness and connector facts, shareable verbatim

Present in one or two copies each, and true for every project:

- A sleep of two seconds or more is blocked at the start of a command.
- A skill's injected preamble differs from a command's injected title, so a rename silently breaks
  any matcher keyed on either.
- Entering a worktree accepts an arbitrary path only on a session's first entry.
- The working directory resets between calls, so an absolute root on every git invocation is
  mandatory.
- Those two are what
  [schema § 10 → Where a tree is created](../plugins/mjolnir/config/schema.md#where-a-tree-is-created-and-how-the-session-comes-to-be-in-it)
  reads: the second is why addressing a tree by path is not working in it, and the first is why
  the entering has to happen at the start of the role rather than whenever a write comes up.
- A worktree serves the skills **committed on its own branch** — for skills the project carries at
  `.claude/skills/`, so a tree cut before one existed does not have it. It does **not** hold for a
  skill shipped in a plugin: every session serves the single registered marketplace path, whichever
  worktree it runs in — measured 2026-10-17, see
  [*Working on the toolkit itself*](../README.md#working-on-the-toolkit-itself).
- A plugin's `skills/` directory is **discovered**, so the manifest's own inventory of it is read
  by nothing. Measured 2026-10-19 against a plugin installed under a config directory of its own:
  the list complete, one entry missing, the key absent altogether, and the key naming a directory
  that does not exist all served the same set. The key is therefore not carried here — a list
  allowed to disagree with what is built is the defect
  [schema § 3](../plugins/mjolnir/config/schema.md#the-trackerless-adapter-and-a-kind-with-no-implementation)
  refuses for adapters, one manifest over. It is recorded rather than merely deleted, because the
  obvious reading of an inventory key is that something needs it.
- Resolve today's date from the harness context, never from the shell.

---

## 4. The rulings

| # | Divergence | Ruling | Outcome lives in |
|---|---|---|---|
| 1 | Staging a commit | Per-project `staging: explicit \| all`. The parallel-session exception and the secret scan are **shared regardless** — every copy already had them; only the default differed | [schema § 6](../plugins/mjolnir/config/schema.md#6-commit-behaviour) |
| 2 | Commit message mechanism | **Repeated message flags, one per paragraph.** This dominates rather than trades off: no temp file so no race, no heredoc so no allowlist accumulation, and the trailer still parses | [schema § 6](../plugins/mjolnir/config/schema.md#6-commit-behaviour) |
| 3 | Commit message style | Concise by default; **do not read history for style**. Do read it for the trailer signature, which is a fact about the repository rather than a style | [schema § 6](../plugins/mjolnir/config/schema.md#6-commit-behaviour) |
| 4 | What the log measures | **Delivered work.** Rework and overhead leave the hours as well as the wording — the majority position, three copies to two | [schema § 9](../plugins/mjolnir/config/schema.md#9-day-log) |
| 5 | Rounding | Nearest half hour, exact quarter **down**, pairing with (4) since both cut one way. A third copy rounds to one decimal instead, so `round_to` and *whether a grid is enforced* are both configuration | [schema § 9](../plugins/mjolnir/config/schema.md#9-day-log) |
| 6 | Cut work | **Disclosed, not hidden** — a `Not billed (N h):` section, one figure on the heading and none per item, omitted rather than written empty. Bookkeeping and contractual time appear in neither section, having never bought hours. A synthesis of the three observed positions, not one of them | [schema § 9](../plugins/mjolnir/config/schema.md#9-day-log), the skill |
| 7 | Dirty tree at start | **Derived from the branch model, not configured.** Worktree mode reports and continues; in-place mode aborts. One axis already configured decides it, so it costs no setting — the derivation sits in § 6 and the key it reads in § 10, which this ruling predated: while that key was absent, two projects' own layers disagreed about which mode they were in | [schema § 6](../plugins/mjolnir/config/schema.md#6-commit-behaviour), [schema § 10](../plugins/mjolnir/config/schema.md#10-branch-model) |
| 8 | A duplicate at filing | **Rewrite the body** to what the work now is; no dated appends. Provenance goes in a comment where the tracker has them, otherwise in the run report | [schema § 3](../plugins/mjolnir/config/schema.md#a-duplicate-is-the-item-rewritten-never-a-second-item-filed), the skill |
| 9 | Invocation names | **Namespaced, no alias.** A project-level alias would be one file per project per skill, reintroducing in miniature the duplication this toolkit exists to delete. The namespace also makes a deliberate local override read as a *different* name rather than the same one, which matters because one skill name already denotes two unrelated roles | [schema § 7](../plugins/mjolnir/config/schema.md#invocation) |
| 10 | Deployment | **A thin skeleton only**: confirm intent and name the target, with an explicit go required for a live environment *for this deploy*; read-only preflight; invoke the project's own script; verify health; report what was rebuilt and what failed with its log tail. Hosts, services, secrets, build steps and tier selection stay local | #13, until extracted |
| 11 | Reading the host's answer, and what a failure is | **One subsection, read by every role that reads a run.** The four preconditions, a precondition's failure never being folded into the conclusion, an **environment failure consuming no fix cycle**, the cap on fix cycles, and watching rather than polling. It was written in the finishing role's skill while that role was the only reader; the reviewing role reads the same runs, and a rule stated in one role's skill is a second authority for the other | [schema § 2](../plugins/mjolnir/config/schema.md#reading-a-runs-answer-and-what-a-failure-is) |

### Where a ruling overrode a stated counter-argument

Recorded so the next reader does not take it for an oversight:

- **(5) overrides a copy that argues directly against rounding down** — "never round down to be
  safe: a deliberate under-statement is as wrong as an invented hour". It was chosen knowingly,
  and it pairs coherently with (4), since both cut one way.
- **(2) is the one ruling that overrides a *measured* claim** rather than a preference — two
  upstream issue numbers about permission-allowlist pollution, **not re-verified**. Repeated
  message flags are right either way, so nothing waits on it, but the probe is worth doing.
- **(10) is provisional.** It was settled on one copy read in full and five read structurally.
  Three of the six deploy copies run 210 to 372 lines, and "almost nothing survives extraction"
  is close to the truth for this role — but it should be reached by reading the rest.

### Further things that are configuration, not procedure

The **readiness gate**
([schema § 5](../plugins/mjolnir/config/schema.md#5-readiness-gate--an-ordered-predicate-list)),
the day log's **exclusion list**
([schema § 9](../plugins/mjolnir/config/schema.md#9-day-log)) and **what counts as done**
([schema § 13](../plugins/mjolnir/config/schema.md#13-what-counts-as-done--an-ordered-check-list-and-who-answers-each-check))
— each an ordered list of named checks drawn from a shared library rather than a fixed sequence. The
measurements are in `configuration-surface.md`. ⚠️ No count is carried in this heading any more: it
said *two* and the third arrived, which is the drift this record is supposed to catch rather than
demonstrate.

The last of the three carries one thing the first two do not, and it is the part a reader should not
take for a refinement: **a check states who answers it**, because two projects whose rule is
*a green gate is not done* split that rule differently — one needing a person at the keyboard, the
other needing a command the procedure runs itself and a checklist a person works. A single
human-answered flag would have been wrong for one of them in each direction.

## 5. What the last three day-log copies added

Read after the first design pass. None of it reverses a ruling; two items extend the surface.

- **Rounding has three positions, not two.** One copy rounds to **one decimal** rather than to a
  half hour at all, and its checker consequently has no grid assertion where two others do. So
  `round_to` and *whether the grid is enforced* are both configuration, with the enforcing
  assertion conditional on the first.
- **The exclusion list is configuration**, like the readiness predicates — see above.
- **A fifth independent instance of read-it-from-one-place.** A sixth turned up later, outside the
  process roles entirely — see `configuration-surface.md` — bringing it to six across five stores.
- **The stream set is configurable.** Four copies union four streams; one unions **five**, adding
  the code host's own item and review activity, on the grounds that review work "happens almost
  entirely on the host and leaves no other trace". The host-activity stream is available only
  where the host has an API for it.
- **Two of the five copies were git-ignored and could not be committed to their own
  repositories** — one because that repository sits in a client's organisation, one because it has
  a second collaborator and the skill reads private sources. **Extraction is the only route by
  which either project gets a shared, reviewable copy of that procedure at all**, which is a
  second and independent reason to extract, applying to the most-duplicated role of the nine.
- **One copy handles a case no other has**: the project is scoped but *not* scoped to one person,
  because a second collaborator commits to the same repository. Its rule is that an author filter
  belongs in the script, never a subtraction by hand. Hence `attribute_to`, absent by default.

## 6. What the five review copies added

Read when that role was reconciled. Its copies ran **92 to 295 lines**, and the spread is one
question: four delegated the review to a shared reviewing carrier and read no code themselves — one
of those four reads the changed-file *list* and nothing in it — while the fifth read the diff itself
and drove a browser against a running instance.

**Two hard contradictions, neither settled by majority:**

- **Who merges.** **Two** copies reach a merge, and one of those also moves the item and deletes the
  branch; of the other three, none mentions the merge at all. It was **settled by the boundary
  rather than by weighing the positions**: the finishing role already owns the merge, reading it
  back from state, the item's move and the tree's release, so a merging copy's last section is a
  second home for a role that had already landed. The reviewing role records; it never merges and
  never waives.
- **Who performs the review.** Ruled **both**, which is a synthesis and not one of the two
  positions. A delegated pass is invoked where the project has one, *and* the diff is read
  regardless, because a delegated pass that found nothing is not a verdict. ⚠️ **The accepted cost
  is that a project whose reviewer is a delegated pass now pays a diff read as well** — which is the
  cost the measurements below buy.

**The open question that role raised, now ruled.** Two copies enforce part of it through a hook
rather than carrying it as procedure, and ⚠️ **the two are not the halves the question said they
were** — the item's body split them across the copies, and both halves turn out to be **one** copy's
pair: it records the answer through a hook on the asking tool and refuses the merge where no record
exists for that repository and number. The other copy's hook is not the second half of that: it
holds every merge behind an unconditional ask that reads no record and that no review can silence.
The ruling is that **procedure produces a record and enforcement reads it** — which the first pair
is an instance of and the second is the case for, since enforcement reading nothing is what leaves
the asking to procedure. The role asks whether a person is going to look whether or not a hook is
installed, and says which of the two situations it was in; what refuses an act on the strength of
that record is #16's.

**What one or two copies knew and the rest lost** — the wording § 2 above is careful about, because
no single copy holds this whole list:

| Capability | Copies that had it | What the others lost |
|---|---|---|
| **The hand-over** — instructions somebody can follow, each item an act and an observation, with what is already known and which checkout a service is bound to | 1 of 5 | A summary of what would have been checked, handed to someone starting cold |
| **A document the change contradicts and does not update** is a finding against that change | 1, and a different one | A change landing against a stated behaviour nothing records any more |
| **The declinable inspection** — whether a person is going to look is asked, and the answer is what licenses a merge with nobody's eyes on the diff | 1 | Merging unasked, and holding a change nobody intends to look at — the same failure in two directions |
| **An empty check list has causes worth telling apart** | 1 | Absence of signal read as green. ⚠️ [schema § 2](../plugins/mjolnir/config/schema.md#2-code-host) bars the *conclusion* and enumerates different causes, so a workflow configured to skip an uninspected change is in neither it nor the role |
| **A local run of a command the host already ran adds nothing**, and its complement: a check no workflow mirrors is the one that *must* run locally | 2, each stating it in procedure **and** enforcing it in a hook | Either a shared machine spent twice for one answer, or a tier nothing ever runs |

**Measurements this repository contributed**, each from reviewing its own changes. ⚠️ **The last of
them is a mechanism rather than a rule**: four copies already forbade a force push, and what is new
is why an amend is refused and why the second commit costs nothing.

- **A latent defect scores as a non-defect.** Reviewing a change that *was* a gate, every
  independent scorer reproduced a real defect and every one returned the same middling confidence,
  for the same stated reason: verified, will be hit, but the tree is green today. Applied
  mechanically, the confidence cut would have reported *no issues found* on a new file carrying
  fourteen reproduced defects. So *real* and *firing* are separated and both reported, and **a
  reproduction is the score** — which removes the confidence number from the decision entirely.
  ⚠️ **The scorer count rests on a session record rather than on anything in the tree or on the
  host**, so it is not written here; the fourteen is on the change itself.
- **A probing reviewer needs an isolated copy.** Parallel verifiers told to probe in memory planted
  files into the live tree, whose branch is another session's claim. Naming the mechanism is what
  worked; *in memory or a scratch copy* was not enough.
- **A reviewer reads the head the host reports**, never the sha the session remembers: readers given
  a branch's first commit reported an already-retracted claim as live text.
- **A fix after the push is a second commit.** An amend and a force push is refused as destructive,
  and the second commit is the better record anyway.
- **A local check reads the working tree, which is not what a commit takes.** Edits a merge had
  staged, verified green by every local check and then edited again, were left out of the commit —
  so the gates had answered about a tree that never landed, and the pushed change carried a
  duplicate key its own reader resolves in silence. It is
  [schema § 10](../plugins/mjolnir/config/schema.md#which-tree-a-verdict-belongs-to)'s wrong-tree
  rule one level down, and the measurement is this role's own reconciliation.
- **Convergence is evidence about a finding, not about its reasoning.** Three of five independent
  readers agreed on one that was false; what their agreement established was that the surrounding
  prose did not say which project each clause referred to.
- **A delegated reviewing carrier inherits none of the delegating role's context**, which three
  copies had already discovered and written down — so every requirement a role places on a finding
  travels *in* the delegation rather than beside it.
- **A reproduction is the score**, which is the latent-defect measurement's consequence and is
  listed here because the role states it as a rule: the figures above are what it rests on.

**What a delegated review of the reconciliation recovered.** Five passes over the extracted role
found that it had dropped corrections one copy had paid for, and ⚠️ **the largest was structural
rather than a rule**: the role had no step that *executed* the change's plan, which four of the five
copies had — and with it went what counts as an observation, ticking only what was observed,
re-running from the top after a fix, never ticking an item that could not be run, and writing the
observation onto the item's own line. The second was that one copy asked **two** questions, who
*runs* the plan and who *looks* at the result, of which only the second is declinable; the
reconciliation had collapsed them into the declinable one. Both are now in the role, and the losses
that belong to the finishing role rather than this one — the squash subject's references,
retargeting dependents before deleting a branch, an item not advancing while a sibling change is
open, and an unreachable tracker holding the merge rather than being discovered after it — are in
that role, because a loss found by reviewing this change is this change's to repair wherever it
landed.

Two things needed no ruling because an existing one already struck them: **four** of the five copies
credited a tool as a co-author on the fix commit and **the same four** put a generated-by marker in
the comment they post, both barred by
[schema § 6](../plugins/mjolnir/config/schema.md#authorship-is-procedure-not-configuration); and
three different commit-message mechanisms appeared across the five, settled by ruling (2). ⚠️ **The
fifth copy carries no message template at all**, which is why it does neither — not a project that
had already adopted the rule.

## 7. Still open

- Read the remaining five deploy copies, to confirm or revise ruling (10).
- Probe whether the permission-allowlist defect behind ruling (2) still reproduces.
- Name the two `deliverables` roles apart. Proposed, not settled: one for the prose session
  summary, one for the billing-period line items. Nothing turns on the names beyond not merging
  the two roles.
- **Extract the day log's evidence script.** The procedure is shared as of now; the script is
  still each project's own, pointed at by `day_log.script`. That is transitional by design, so a
  project that has not been migrated keeps working — but the end state is one copy of the script
  too, with the day boundary, the stream set, the rounding, the ritual list and the chat patterns
  all read from configuration.
