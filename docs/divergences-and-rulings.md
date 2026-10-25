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
  any matcher keyed on either. There is a third entry path and it is named differently again; what
  each path and each hook event carries about a role was measured across both carriers and is
  stated at
  [schema § 7 → What a hook can establish about the role it is running under](../plugins/mjolnir/config/schema.md#what-a-hook-can-establish-about-the-role-it-is-running-under).
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
  [*What a session actually serves*](working-on-the-toolkit.md#what-a-session-actually-serves).
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
| 10 | Deployment | **A thin skeleton only**: confirm intent and name the target, with an explicit go required for a live environment *for this deploy*; read-only preflight; invoke the project's own script; verify health; report what was rebuilt and what failed with its log tail. Hosts, services, secrets, build steps and tier selection stay local — this role's instances of the boundary at [schema § What the procedure models](../plugins/mjolnir/config/schema.md#what-the-procedure-models-and-what-it-only-names-and-calls), which is where the rule is stated | #13, until extracted |
| 11 | Reading the host's answer, and what a failure is | **One subsection, read by every role that reads a run.** The four preconditions, a precondition's failure never being folded into the conclusion, an **environment failure consuming no fix cycle**, the cap on fix cycles, and watching rather than polling. It was written in the finishing role's skill while that role was the only reader; the reviewing role reads the same runs, and a rule stated in one role's skill is a second authority for the other | [schema § 2](../plugins/mjolnir/config/schema.md#reading-a-runs-answer-and-what-a-failure-is) |
| 12 | What `version` is for, and when it moves | **Retired**, as `roots.skills` was, and a configuration still declaring it is refused with the key named. Requiredness and the absent case are marked beside each key, so a configuration states its decision or is refused — leaving the revision nothing to separate. It had never moved through a run of changes that each made an older configuration unreadable ([the measurement](configuration-surface.md#the-revision-key-never-moved-and-the-markers-took-its-job)) | [schema § The file itself](../plugins/mjolnir/config/schema.md#the-file-itself) |
| 13 | The unit-testing discipline | **Procedure, on the surface.** Four rules, each written in one of the six instructions files — two of them for the one rule two state — and read by no role: a test is a ceiling rather than a floor, fakes over mocks with the seam named, the violation written first and the red confirmed, and values asserted rather than key sets. A coverage figure, a case-file naming, a layout and the suffix marking a tier stay local and are **named** as local, by the boundary at [schema § What the procedure models](../plugins/mjolnir/config/schema.md#what-the-procedure-models-and-what-it-only-names-and-calls). ⚠️ Settled against the reviewing role's own text and a per-project pointer, the first by the same reasoning as (11) — [the measurement](configuration-surface.md#the-unit-tier-six-files-of-rulings-and-no-role-reading-any-of-them) | [schema § The loop — nine roles](../plugins/mjolnir/config/schema.md#what-earns-a-test-and-what-makes-its-red-believable) |
| 14 | A workflow that runs more than one check | **Nested under the entry, keyed by nothing.** An entry states one `mirrors` or the `jobs` that mirror several, never both, and a list inside one `mirrors` is refused — the tolerance that shape had before. The collision argument that makes the map a workflow's and never a job's is a collision *across* workflows, and it does not reach inside an entry: a job's id is unique in its own file by the host's grammar, and the only name anything is keyed on is still the workflow's. ⛔ `paths` sits at the level the workflow file states it at, inherited and overridden by neither. And the generator half, which the same question asks one direction over: a generated gate takes a file of its own, an installer never appends a job to a workflow it did not write, and a file that already exists is a stop | [schema § 2 → A workflow whose jobs mirror more than one command](../plugins/mjolnir/config/schema.md#a-workflow-whose-jobs-mirror-more-than-one-command) |
| 15 | What a trigger states about an event | **The event, the types of it, and the ref — one grammar.** Types sit inside the pattern, a second event kind is a second member of the list, and an omitted clause means the workflow's event block states no `types:` key rather than the host's default set for that event. An empty clause and a blank type inside one are refused, the way a blank `mirrors` and a blank path glob are. ⛔ The event vocabulary stays the host's: the facet enumerates no events and holds no name against one — `pull_request_review_thread` is a webhook and not a trigger, and what refuses it is the host as the file loads. The pattern itself is still held to nothing, a trigger a consumer cannot read being no answer about the run rather than a configuration to reject — [the measurement](configuration-surface.md#one-entrys-two-events-and-the-types-the-pattern-could-not-carry) | [schema § 2 → What a trigger states](../plugins/mjolnir/config/schema.md#what-a-trigger-states-the-event-the-types-of-it-and-the-ref) |
| 16 | What a consumer answers about a mirrored run | **Four values, and only one of them is coverage.** `reached` names the run whose conclusion is worth reading and ⛔ **is never green** — how it concluded is the four preconditions' and the host's. `out of scope`, `no answer` and `unreadable` each read as *run it here*, and ⛔ **are reported as themselves rather than folded into one**, their remedies differing: a conflicted change produces no run, and a reader told *no checks, go ahead* is sent to run a suite whose result cannot land. ⚠️ The one direction that is not fail-closed is a command two entries mirror, where `reached` outranks the rest — a run that reaches the change exists, so there is something to read. ⚠️ Ruled now because the facet acquired its first consumer, and the fourth value is what #39 asked for before it was closed as a duplicate of #33 | [schema § 2 → Reading a run's answer](../plugins/mjolnir/config/schema.md#reading-a-runs-answer-and-what-a-failure-is) |
| 17 | What a hook refuses, and on what | **A record, never a reading — and the record's own form is the surface's.** Two of the three projects running process hooks enforce the merge, and ⛔ **they are not two halves of one design**: one keys an answer by repository and number and refuses a merge where none exists, the other holds every merge behind an ask that reads no record and that no review can silence. The first is extracted, because the second cannot be satisfied and so is argued with. ⛔ The guard is held on whether the question **reached a person**, not on whether one read the diff, which is not a property a machine can establish; `unanswered` is an answer, and a guard never reads the answer written by the act it guards. ⛔ The direction a guard fails in is procedure and not a per-guard setting: a reversible act proceeds with the answer saying nothing was held, an irreversible one is refused naming what could not be established — § The loop's own split for an ask nothing answered. And the lease's count is a **sum** of the resource's own and the leases too young for it to have seen them, never a maximum, which let a third holder through a cap of two. ⚠️ `waive_review` is marked procedure: the switch an adopting project reaches for first — [the measurement](configuration-surface.md#the-enforcement-half-three-keys-and-the-rest-procedure) | [schema § 7 → What a hook refuses](../plugins/mjolnir/config/schema.md#what-a-hook-refuses-and-the-record-it-reads), [schema § 7 → Which direction a guard fails in](../plugins/mjolnir/config/schema.md#which-direction-a-guard-fails-in), [schema § 7 → A lease on an exclusive resource](../plugins/mjolnir/config/schema.md#a-lease-on-an-exclusive-resource-and-the-exit-paths-that-release-it) |
| 18 | What holds the facet to the files it describes, and how a definition is read | **Held mechanically wherever the definitions are files a reader can open, with three answers and no edit.** Name, triggers and paths each compared in both directions, since a rename shows as an entry naming no run *and* a run no entry names, and a one-way comparison reports half of it; the jobs dimension one way only, a job no member names being the form's own ordinary case. A dimension that cannot be established is reported as itself and never as agreement; `checks: []` is *no subject* only where the host defines nothing, an empty facet with definitions behind it being this facet at its most drifted; and neither side is ever written, which side is wrong not being a check's to say. ⛔ A definition is read through the YAML parser the configuration reader already depends on, rather than through the line-anchored pattern the item asking for this carried: a hand-written subset reader is a second parser for one format, and the direction it is wrong in is drift reported on a correct entry — red forever with no edit that clears it. What the pattern's measurement buys is kept as an **enforced** budget on an adversarial read that fails the run, not as a note beside it. ⚠️ The cost of the parser is one quirk: `on` is a boolean in the YAML version it implements, so the host's own key arrives under `True` | [schema § 2 → The facet against the host's own definitions](../plugins/mjolnir/config/schema.md#the-facet-against-the-hosts-own-definitions) |
| 19 | What an install does in a project that configures nothing | **Nothing, and one invitation.** A hook is addressed by its event and by no name, so an install reaches every project the person who installed it opens, and the measured cost of that is an enforcement report on every command in a project that states nothing — the arm reading *no configuration* and *a configuration it could not parse* as one answer. ⛔ So every carrier asks one question before it does anything, through the shared reader rather than by testing a path of its own, and answers nothing where the project states none: no refusal, no report, and nothing in the session's context. ⛔ **Absent and unreadable stay two answers.** A file that is there and does not resolve is the project's own facts badly written, so the reversible direction of the fail rule still reports it — which is what obliges a suite to plant both, and makes a plant pointed at an absent file an assertion about a route no session takes. ⛔ **One message is exempt**, at the event that opens a session and on the channel that reaches a person rather than the writer: an install nobody is told about is an install nobody adopts, so the invitation names the file to write and the document its keys are stated in, and a second message on any other event breaks the rule rather than using the exception. ⚠️ Scoped to what fires on an event and not to the whole install — a role is addressed by name, and whoever invokes one is owed the answer that its project configures nothing. ⚠️ What it gives up is stated rather than discovered: the outward credential hold, the merge guard and the no-deferral hand-back are all off in an unadopted project, which is the project none of them was ever configured for | [schema § 7 → A hook in a project that states no configuration](../plugins/mjolnir/config/schema.md#a-hook-in-a-project-that-states-no-configuration) |
| 20 | What a spend guard refuses, and on what reading of the call | **The command position, and never the text of the call.** One project has the guard and two more have the shape, and ⛔ the correction it carries is the reason it is extracted rather than rewritten: an earlier version grepped the raw command and refused a text edit whose prose contained a script path, and a guard that blocks honest work is a guard somebody turns off. So a call is split on the shell's own separators, leading assignments and a wrapper are stripped, **every** command position is matched rather than the outermost one — which also keeps a paid command spelled like a wrapper guardable — and a flag's value is never read as the command, the measurement this toolkit's other guards already carry. ⛔ `args_match` is load-bearing and not sugar: two of the three instances invoke their paid tier through the same binary as their cheap suites, so the command decides nothing. ⛔ The approval is a key because it varies — frequent legitimate uses in one instance, a metered release in another — while the parse varies in no project, and `per_invocation` is the default because a go that outlived its call would be a go for calls nobody saw; what an unanswered ask becomes is the harness's, and that is where *unsupervised* is decided. ⚠️ A configuration that is there and does not resolve leaves the call held to nothing rather than refused, which is the one case the fail-direction rule does not settle by itself: a broken configuration cannot say whether the call is a spend at all, and the refusing arm would refuse the edit that repairs it. ⚠️ The one price the harness volunteers — a resumed session's cache write — is read against a stated bar and reported as **no figure** where it is absent, never as free; it does not generalise into a meter, and no key states a budget — [the measurement](configuration-surface.md#the-spend-half-three-instances-and-the-key-that-is-not-sugar) | [schema § 19](../plugins/mjolnir/config/schema.md#19-a-command-that-spends-and-the-supervision-it-is-refused-without), [schema § 19 → The command position](../plugins/mjolnir/config/schema.md#the-command-position-and-why-the-whole-call-is-not-one), [schema § 19 → What an approval is per](../plugins/mjolnir/config/schema.md#what-an-approval-is-per-and-the-one-price-stated-before-a-turn-runs) |
| 21 | Where the host's jobs run, and what a run cancelled in the queue means | **A statement on the surface, and four readings of a conclusion.** One project's host account carries its own runners, and a job asking for the host kind's default label there **never starts at all** — so a generated gate carrying the default is a check that never reports, replacing one that did. ⛔ `host.runner` states the label, the account's capacity and one job's budget, defaults none of them, and is **omitted** where the kind's own default is the answer. ⛔ **The default itself stays off the surface**, by the argument that keeps the event vocabulary off it, and the price is a stated limit: a project writing no block has nothing for the drift comparison to hold its files to. ⚠️ The capacity is beside the budget because the same account's runners take **one job at a time**, which makes a budget a *queue* budget — a short job at the back of the line is cancelled having never started. Hence the conclusion reading: ⛔ **failed · no answer, never started · no answer, superseded — read the newer run · green**, with only the first about the change and only the last coverage, and the two no-answer readings told apart because one is waited for and the other is read somewhere else. ⚠️ The same measurement **prices** ruling 14's one-workflow-per-command rather than overturning it: each checkout is also a place in the line | [schema § 2 → Where the host's jobs run](../plugins/mjolnir/config/schema.md#where-the-hosts-jobs-run), [schema § 2 → Reading a run's answer](../plugins/mjolnir/config/schema.md#reading-a-runs-answer-and-what-a-failure-is) |
| 22 | What a guard does before a command that could reach a live machine | **Puts it to whoever would answer the prompt, or refuses it where nobody would.** One project carries the guard — two inline deny guards when #16 measured it, a hook with a test matrix beside it by the time it was extracted — and ⛔ **the load-bearing line is the verdict rule rather than the match**: a mode a person answers gets the ask, a mode that answers its own prompts gets the refusal, and an unrecognised mode is read as the second, because a prompt the session can clear on its own behalf is not approval. A guard that always asks enforces nothing unattended; one that always denies is one somebody turns off. ⛔ **The list is inverted**: what is named is every machine that is *not* live, so the live one is reached by a name in no list and the default is to prompt — a guard listing what is forbidden goes quiet the day somebody adds a second alias. ⛔ **And the names live outside every working tree**, the repository carrying the mechanism and the machine carrying the names, with a machine that has no list yet one where every name reads as live. ⚠️ `local_names` is the one list on the surface, and the test that admits it is whether a name identifies *another* machine. ⚠️ The parse is not restated: the command position is ruling 20's, imported rather than copied, and what this facet adds is the machine read out of the arguments — the first plain word, with a flag the project names as taking a separate word skipped, which is why those flags are per entry rather than procedure — [the measurement](configuration-surface.md#the-live-half-one-guard-and-the-two-lists-that-are-not-interchangeable) | [schema § 21](../plugins/mjolnir/config/schema.md#21-a-command-that-could-open-a-session-on-a-live-machine), [schema § 21 → Which verdict](../plugins/mjolnir/config/schema.md#which-verdict-and-who-would-answer-the-prompt), [schema § 21 → The machines named](../plugins/mjolnir/config/schema.md#the-machines-named-are-the-ones-that-are-not-live), [schema § 21 → The four ways it fails closed](../plugins/mjolnir/config/schema.md#the-four-ways-it-fails-closed) |
| 23 | What a pull request title opens with, and what refuses one that does not | **One fact on the surface, composed once, and a generated workflow that enforces it.** One project carries the gate — a few lines of YAML grepping the title for a leading work-item reference — and it is process with no product in it, which is the extraction test every role item applies. ⛔ The form it enforces was stated **nowhere**: a third fact beside § 6's body shape and § 3's closing form, and ⚠️ **distinct from that closing form on the very project carrying the gate**, where the closing reference rides in the body while the title's closes nothing. So `host.pull_request_title` states one reference, whether more than one may appear in sequence, and the base refs a title is held on — ⛔ **all three where the block is stated and none defaulted**, `repeated` because that project closes **two items at once** and a form encoding exactly one refuses what the finishing role legitimately writes, `into` because it holds titles on its release branches alone and a key nobody wrote would have been coverage nobody asked for. ⛔ **The arrangement is procedure** — references abutting, then one space, then the rest — derived from the one project measured, a separator key with one observation behind it being a facet invented rather than found. ⛔ **So are the event types**: without `edited` a title fixed in place never re-runs and the refusal stands on a title that no longer exists. ⚠️ The gate **mirrors no local command**, there being no local counterpart to a field only the host carries, so ruling 16's reading leaves it out of every mirrored command and the guard on an already-run command refuses nothing on its account | [schema § 2 → What a pull request title opens with](../plugins/mjolnir/config/schema.md#what-a-pull-request-title-opens-with) |
| 24 | What a guard does about a branch that has fallen behind its base | **It reports, and the firing points decide that rather than a preference.** Falling behind is a state somebody else's merge produced, so at both points one project measured the check running — the turn's end, and after a merge — there is no call in hand to refuse, which is why the fail-direction ruling (17) does not reach this one. ⛔ **The reading is by patch and never by ancestry or by a count of commits**: § 2 above records ancestry's false answer costing five finished trees read as carrying 9–20 unpushed commits, and a count of the base's commits is the same answer reached by arithmetic — both of them call a branch whose base was rewritten behind by as many commits as were rewritten, and the plant computes both beside the reading that ships. ⛔ **The base's head is read from the remote and not from this tree's view of it**, the tracking ref being stale exactly at the merge the second point exists for; a head the remote reports and the tree does not hold is *behind* with the figure unestablished, never *level*. ⛔ **No key states a figure the count is held against** — *N commits behind* is a judgement rather than a fact a role reads, which is the boundary test rather than a refusal, so the figure is reported and the person reads it. ⚠️ A project that publishes no base is **silent** while a base that cannot be reached is **unestablished**, which is ruling 19's absent-against-unreadable split one subsection over: a report every turn that there is nothing to report is how a guard comes to be switched off. ⚠️ Ruled now because it is the one role in #16's measured inventory of the enforcement half that #16's own acceptance check does not reach | [schema § 7 → A branch that has fallen behind its base](../plugins/mjolnir/config/schema.md#a-branch-that-has-fallen-behind-its-base-and-the-two-points-it-is-reported-at) |

| 25 | What carries a work item's priority, and what the one gate check that reads it reads | **A facet of its own, comparable by an ordered list, written by whoever the project says and derived by nobody.** Three projects carry a convention and no two are the same — A a four-value prefixed label axis on a board, C the tracker's own priority field, F a single prefixed label for its top tier alone — while B's filing role takes the same `high \| medium \| low` argument the other two take and has nowhere on its board to put it, which is the absent case with a working loop around it rather than a gap in one. ⛔ **`values` is the comparability**, ordered most important first and stated for every carrier including `native`: the check reading this facet asks whether work ranking above an item is ahead of it, which is a question about two items rather than one, and an adapter asked to rank its own tracker's words would be inventing the order rather than reading it. A's colours carry the same order and nothing that reads a tracker sees a colour. ⛔ **An item carrying no value is unranked and never the lowest** — F's axis leaves everything below its top tier bare, and this repository's own axis states outright that a missing label does not mean the work is unimportant — so the check reports itself unanswered rather than passed. ⛔ **No role derives a tier**, `procedure` meaning a role writes the value it was handed and never one it worked out, and ⛔ **a value already on the item is never rewritten**, which is A's own rule about a card in flight and § 4.5's rule about a date the item already states. ⛔ **And the check belongs to this facet rather than to the ordering**: `queue_position` reads § 4.6, a project configuring it while the facet is absent is refused naming the facet's own stated reason, and § 12 answers which item to *offer* instead — two questions, either of which a project may configure without the other. ⚠️ The tier-to-date arithmetic stays out: A turns its tier into a due date through a four-row table, no second project was found to have one, and § 4.5 is unchanged by the tier having a key — [the measurement](configuration-surface.md#the-work-item-facets-and-the-absent-case) | [schema § 4.6](../plugins/mjolnir/config/schema.md#46-priority), [schema § 12](../plugins/mjolnir/config/schema.md#12-ordering) |

### Where a ruling overrode a stated counter-argument

Recorded so the next reader does not take it for an oversight:

- **(5) overrides a copy that argues directly against rounding down** — "never round down to be
  safe: a deliberate under-statement is as wrong as an invented hour". It was chosen knowingly,
  and it pairs coherently with (4), since both cut one way.
- **(2) is the one ruling that overrides a *measured* claim** rather than a preference — two
  upstream issue numbers about permission-allowlist pollution, **not re-verified**. Repeated
  message flags are right either way, so nothing waits on it, but the probe is worth doing.
- **(12) overrides the key's own stated purpose**, which was to let a reader tell a facet absent by
  decision from one that did not exist when the file was written. The override is that the purpose
  was met elsewhere rather than abandoned — by the requiredness and `absent_reason` markers — and
  what it knowingly gives up is a diagnostic on a stale file, stated on the surface beside the
  retirement rather than left for an adopter to discover.
- **(14) withdraws a tolerance that was deliberate.** A `mirrors` holding a list of commands was
  accepted knowingly, by a change that needed the collision check to read whatever an entry
  mirrored rather than to hold nothing, and the reader said in as many words that it promised
  nothing about the shape this ruling would land. What the ruling takes is the second way of
  stating one fact; what it gives back is the per-command job and filter that the list could not
  carry. A configuration written the tolerated way stops loading, which is the cost and is stated
  on the surface beside the refusal rather than left to be met.
- **(15) was ruled while the key had no consumer, and (16) gave it one in the next change** — so
  the *yet* below has been spent rather than left standing. What reads a type now is the facet's
  consumer, which matches a trigger's clause against the change's own event type and reports *no
  answer* where that type was never established; the drift check the ruling rests on is still
  #49. ⚠️ Nothing in the ruling turned out to want revisiting: the richer key is what the consumer
  parses, and the dimension it would otherwise have had to call undeterminable is one it answers.
- **(15) extended a key no consumer read at the time**, and the counter-argument is on the
  surface: the
  guard asking whether the host already runs a command does not read a type, and the finishing
  role's question — does a run exist for *this commit* — is answered the same way by a run an
  `edited` event fired. Recording the limit instead would have been a legitimate outcome on that
  reading. What decided against it is the consumer that writes a **verifier** rather than data: a
  drift check comparing this facet to the workflow files, left with a dimension the facet cannot
  express, can only report drift on a correct entry, report green on one it has proven incomplete,
  or declare the dimension undeterminable — and each of the three is worse than the key being
  richer. ⚠️ What the ruling rests on is **one entry**: every other workflow in this repository
  states no `types:` key at all.
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
said *two* and what counts as done arrived, which is the drift this record is supposed to catch
rather than demonstrate.

What counts as done carries one thing the readiness gate and the exclusion list do not, and it is
the part a reader should not take for a refinement: **a check states who answers it.** What forced
that — two projects splitting one rule in ways a single human-answered flag would have got wrong in
opposite directions — is the measurement, and it stays where the measurements are.

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
