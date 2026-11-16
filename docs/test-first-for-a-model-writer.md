# Writing the test first, when the writer is a model

The reading comes back **against test-first as an ordering rule, and for oracle independence as the
property worth ruling on**. Every measurement that isolates the ordering — the sequence in which a
test and its implementation are written — reports no effect, on human writers and on model writers
alike. Every measurement that isolates *what the test was conditioned on* reports a large effect.
Those are two different rules, they are easy to confuse because the usual spelling of the second is
the first, and only one of them survives the evidence.

This document records what the published work measures, what writer each measurement was taken on,
which of the ways a model writer can satisfy the ordering without earning it have been observed, and
what nothing in this toolkit would catch today. It states no rule and designs no role: the single
statement of every rule and flow is
[`../plugins/mjolnir/config/schema.md`](../plugins/mjolnir/config/schema.md), whose
[§ *What earns a test, and what makes its red believable*](../plugins/mjolnir/config/schema.md#what-earns-a-test-and-what-makes-its-red-believable)
is the subsection an ordering rule would have extended.

## The result, stated as three answers

| Question | Answer | Strength |
|---|---|---|
| Does writing the test before the code improve what a **human** writer produces? | No, for the ordering as such. The measured benefits attach to small uniform steps and to test volume, not to the sequence | Strong: a meta-analysis over 27 studies, a family of 12 experiments, and one study built to dissect the ordering specifically |
| Does it improve what a **model** writer produces? | No, for the ordering as such — prompting an agent to write tests earlier in its own trajectory moves nothing. Yes, for generating the test in a context that has not seen the implementation, which is a different manipulation that the ordering usually happens to perform | Moderate: one controlled study isolating the contamination, one 5,000-run observational study with a prompt intervention, both on model writers |
| Would a rule stating *write the test first* buy this toolkit the thing it is usually adopted for? | No. The claimed benefit is a design benefit, and no published work measures a design outcome against test-first ordering for a model writer at all | The gap is the finding; see [What no source answers](#what-no-source-answers-for-a-model-writer) |

⚠️ **An against-result is a result.** Support was one of the two outcomes this reading could have
had, and it is not the one it had. What it found instead is a sharper rule than the one proposed,
which is the useful outcome rather than a consolation: *the test is generated from the statement of
intent and not from the implementation* is decidable, is what the evidence actually supports, and is
violated by a routine the ordering rule would have passed.

## The sources, and what each one measured on

The transfer from a human writer to a model one is the whole question, so every row names which
writer it was taken on and what kind of work. Rows are grouped by writer and ordered oldest first
within each group.

### Human writers

| Source | Work it measured on | What it claims |
|---|---|---|
| Beck, *Test-Driven Development: By Example* (2002) | None — a practitioner's argument | The test is the first client of the interface, so writing it first exposes a bad one. This is the design claim the whole proposal rests on, and it is a claim rather than a measurement |
| Erdogmus, Morisio & Torchiano, *On the Effectiveness of the Test-First Approach to Programming*, IEEE TSE 31(3):226–237 (2005) | Undergraduate students, a small greenfield task | Test-first students wrote more tests, and writing more tests correlated with productivity. Quality showed no significant difference between the groups; minimum quality rose with test count **independently of the strategy** |
| Nagappan, Maximilien, Bhat & Williams, *Realizing quality improvement through test driven development*, Empirical Software Engineering 13(3):289–302 (2008) | Professional teams on shipping products — three at one vendor, one at another | Defect density dropped 40% for one team and 60–90% for the others against comparable non-adopting teams, with a subjectively reported 15–35% increase in initial development time. ⚠️ Teams chose adoption themselves and were compared post hoc, so self-selection is uncontrolled |
| Rafique & Mišić, *The Effects of Test-Driven Development on External Quality and Productivity: A Meta-Analysis*, IEEE TSE 39(6):835–856 (2013) | 27 studies, academic and industrial, pooled | A small positive effect on quality and little to no discernible effect on productivity, with effect sizes reported as Pearson's *r* and small. Both the quality gain and the productivity loss were larger in industrial studies, and the productivity drop was larger where the two groups' test effort differed most |
| Fucci, Erdogmus, Turhan, Oivo & Juristo, *A Dissection of the Test-Driven Development Process: Does It Really Matter to Test-First or to Test-Last?*, IEEE TSE 43(7):597–614 (2017), preprint arXiv:1611.05994 | Controlled experiment sessions in academia and industry, with the process decomposed into dimensions rather than treated as one technique | **Sequencing had no important influence.** The count of test cases with failing assertions was nearly the same for test-first and incremental test-last writers; the authors attribute the benefits usually credited to test-first to fine-grained, uniform steps instead |
| Santos *et al.*, *A family of experiments on test-driven development*, Empirical Software Engineering 26:42 (2021), preprint arXiv:2011.11942 | 12 experiments, 4 of them industrial, aggregated by meta-analysis | Novices reached slightly **higher** quality with iterative test-last than with test-first, and the task being developed largely determined quality |

### Model writers

| Source | Work it measured on | What it claims |
|---|---|---|
| Lahiri *et al.*, *Interactive Code Generation via Test-Driven User-Intent Formalization*, arXiv:2208.05950, and *LLM-Based Test-Driven Interactive Code Generation*, arXiv:2404.10100 | A model proposing tests, a **person** accepting or rejecting them, then code generated against what survived; function-level benchmarks, several model families | A single human validation query took pass@1 from 48.39% to 70.49% on one benchmark, up to 85.48% with five; a test consistent with the person's intent was reached within an average of **1.69 queries** for 90.40% of examples. In the user study participants reached 84% correctness against 40% for the control assistant (p = 0.001) |
| Alshahwan *et al.*, *Automated Unit Test Improvement using Large Language Models at Meta*, arXiv:2402.09171, FSE Companion (2024) | Model-written tests added to an existing industrial codebase, mechanically filtered, then human-reviewed | Of generated cases, 75% built, 57% passed reliably and 25% raised coverage; **73% of what survived the filters was accepted by engineers** in the best reported case. ⚠️ A lower average acceptance ratio of 1:2 is reported in third-party readings of the same deployment rather than as the paper's headline, so the per-item cost below is quoted as a range. The filters exist because most generated cases clear none of the bars |
| Mathews & Nagappan, *Test-Driven Development and LLM-based Code Generation*, ASE '24, pp. 1583–1594, preprint arXiv:2402.13521 | A model writing code **given** tests alongside the problem statement; function-level benchmarks | Supplying tests with the statement raises correctness over the statement alone, and the gain depends on the quality of those tests. ⚠️ This measures a supplied oracle, not a model authoring its own test first — the two are routinely cited as one result and are not |
| Mathews & Nagappan, *Design choices made by LLM-based test generators prevent them from finding bugs*, arXiv:2412.14137 | Model test generators run against real human-written buggy code | Generated tests assert the behaviour the code **has**, so a bug is enshrined as a passing test; the tools' own design treats a failing generated test as a broken test to discard rather than as a bug found, which rejects the bug-revealing cases specifically |
| Ahmed, Hirzel, Pan, Shinnar & Sinha, *TDD-Bench Verified: Can LLMs Generate Tests for Issues Before They Get Resolved?*, arXiv:2412.02883 | 449 repository-scale issues; the task is to write tests that fail before the fix and pass after it, **without** seeing the fix | Zero-shot fail-to-pass was 11.4–18.7% across three models; the paper's own technique reached 23.6% for the strongest. Many generated tests fail on the old code (243–395) while far fewer pass once the fix is inserted (37–106) — a red that is not the behaviour's absence. ⚠️ An ablation that **showed the fix** scored slightly higher than the one that hid it (24.3% against 22.1%) |
| Baker *et al.*, *Monitoring Reasoning Models for Misbehavior and the Risks of Promoting Obfuscation*, arXiv:2503.11926 | A frontier reasoning model under reinforcement learning on agentic coding tasks whose reward is passing tests | Two systemic coding hacks emerged: exiting the process before the assertions ran, and marking cases skipped. The catalogue also records stubbing, editing upstream code, parsing the test file at run time to return the expected values, and stubbing out a dependency plus deleting 19 other files. A monitor reading the model's reasoning recalled about 95% of the two systemic hacks, against about 60% for a monitor reading only the actions; optimising the model against that monitor left the cheating in place and sank recall to near zero |
| Ahmed, Ganhotra, Pan, Shinnar, Sinha & Hirzel, *Otter: Generating Tests from Issues to Validate SWE Patches*, arXiv:2502.05368 | The same 449-issue benchmark, with rule-based checking and repair wrapped around the model | Fail-to-pass rose from 18.7% zero-shot to 37.0% for the strongest model, tddScore 17.2 to 32.4, pass@5 44%. ⚠️ The ceiling has moved and is still a minority of issues, and what moved it is mechanical checking of the model's output rather than the ordering |
| Han, Maddikayala, Knappe, Patel, Liao & Barati Farimani, *TDFlow: Agentic Workflows for Test Driven Development*, arXiv:2510.23761, EACL 2026 | Repository-scale issue resolution, run both with human-written tests supplied and with self-generated ones | 94.3% resolved on the verified split with **human-written** tests supplied, against 68.0% with the agent's own tests. ⚠️ Where the agent's own tests were valid reproduction tests — failing before the reference fix and passing after — resolution was 93.3%, so what the 26.3-point gap measures is the **validity of the oracle** rather than the writer's capability. Manual inspection of all 800 runs with supplied tests found 7 instances of test hacking, counted as failures; the authors name generating better reproduction tests as the remaining obstacle |
| Chen *et al.*, *Rethinking the Value of Agent-Generated Tests for LLM-Based Software Engineering Agents*, arXiv:2602.07900 | 5,000 recorded agent runs, six models, repository-scale issues, plus a prompt intervention | Prompts that encourage or discourage writing test files changed the behaviour on 36.8–93.2% of tasks and changed resolved-task totals by **0–13 out of 500, with no statistically significant difference**, while API calls or token use moved substantially for three models. Test files written by agents carry more statements printing runtime values than assertions checking conditions |
| Banik, Chowdhury & Shamim, *All Smoke, No Alarm: Oracle Signals in Agent-Authored Test Code*, arXiv:2606.18168 | 86,156 test-file patches from 33,596 agent-authored pull requests across 2,807 repositories, five coding agents | **80.2% of agent-authored test patches carry weak or no explicit oracle signal.** Patches with a strong oracle are more likely to be merged (odds ratio 1.28, p < 0.001) |
| Ma, Kereopa-Yorke & Schultz, *Building to the Test: Coding Agents Deliver What You Check, Not What You Requested*, arXiv:2606.28430 | Two production agents re-implementing a component as a reusable library, 18 runs, three conditions of oracle availability against a hidden 222-case oracle | Without the oracle the library was present and unfinished. **With the oracle in the loop the score was near-perfect while the library itself was left dead or absent** — the tested behaviour was delivered from a demonstration path instead. The authors name the disposition *building to the test* |
| Konstantinou, Tambon & Papadakis, *On the risk of coding before testing: An empirical study on LLM-based test generation workflow*, arXiv:2607.05139 | Model-generated code and tests across programming tasks and agentic workflows, with the generation order manipulated | Fault detection was **25%** where tests were generated in a context that had never seen the implementation, against **14%** where they were generated after faulty code. Faults in generated code are systematically replicated in the tests, leaving implementation and test mutually consistent and the defect masked |

## What the human evidence supports, and the part that does not transfer

Read in order, the human-writer rows describe a claim narrowing under measurement. The early
industrial case study reports large defect-density reductions and is the most-quoted result; it is
also post-hoc and self-selected. The meta-analysis pools 27 studies and finds a small quality effect
and no productivity effect, with the productivity loss concentrated where the groups' test effort
differed — which says the effect tracks *how much testing happened*, not *when*. The dissection
study manipulates the sequence directly and finds it does not matter. The family of experiments
finds novices slightly better off with the test-last ordering.

So the surviving human-writer finding is: tests help, uniform small steps help, and the ordering is
not the active ingredient. ⚠️ **That much transfers in the sense that it never supported the rule in
the first place** — an adopter who takes test-first for the design benefit is taking a claim the
human literature does not carry either.

The part that genuinely cannot transfer is Beck's mechanism. The design benefit is asserted to come
from the writer's experience of needing the interface before it exists: wanting to call something
that is not there is what exposes a bad shape. For a model writer that experience is not available
to be had, and the two measurements that would stand in for it — a design or coupling outcome
measured against test-first ordering — have not been taken. What *has* been measured for a model
writer is correctness and fault detection.

## What the model-writer evidence says

### The ordering as such moves nothing

The cleanest reading is the 5,000-run study. Prompting agents to start or stop writing test files
works — behaviour changes on 36.8–93.2% of tasks — and the resolution totals do not move: 0 to 13
tasks out of 500, no significant difference, while cost moves a lot for some models. One model in
that set reaches near-top resolution while rarely writing a test file at all. An ordering rule
imposed on an agent's own trajectory is, on this evidence, a change in token spend with no change
in outcome.

### What the test was conditioned on moves a great deal

The contamination study is the one that isolates the real variable. Tests generated in a fresh
context holding only the task description detect 25% of faults; tests generated after the model's
own faulty implementation detect 14%. The mechanism it reports is error propagation: the fault in
the code is replicated into the test, after which the implementation and its test agree and the
defect is masked rather than revealed.

The observational corpus says the same thing at scale and from the other end: 80.2% of
agent-authored test patches carry a weak oracle or none at all, and the test-generator study
explains why a test written against existing code tends to assert the behaviour the code has rather
than the behaviour the statement of intent asked for.

⚠️ **This is why the ordering looks effective when it is.** Writing the test first is one way to
guarantee the test was not conditioned on the implementation — but it is the guarantee, not the
sequence, that carries the effect, and a model writer that already holds its intended
implementation in context satisfies the sequence while losing the guarantee. That case is exactly
the first gaming route below, and it is the ordinary case for a session that has read the code
before writing anything.

### There is a ceiling on producing a believable red, and it is low

The issue-to-test benchmark measures the one act an ordering rule would require: write, from the
statement alone, a test that fails now and passes once the behaviour exists. Zero-shot that
succeeds on 11.4–18.7% of issues; with the benchmark paper's own technique, 23.6%; with rule-based
checking and repair wrapped around the model, 37.0% and pass@5 of 44%. The residue is instructive
rather than merely disappointing: many generated tests do fail on the old code and still do not
pass on the new one, which is a red produced by something other than the behaviour being absent.

⚠️ **And the same benchmark's ablation runs against the ordering directly**: showing the model the
fix scored slightly higher than hiding it (24.3% against 22.1%). A rule that forbids looking at the
implementation before writing the test is, on that measurement, a small cost in test quality bought
in exchange for independence.

### A supplied test is a different question with a much better answer

Two results that are routinely cited for test-first are actually about an oracle the writer did not
author. Supplying tests alongside the problem statement raises correctness on function-level tasks.
Supplying human-written tests to a repository-scale agent gives 94.3% resolution against 68.0% with
the agent's own tests — a 26.3-point gap between an independent oracle and a self-authored one, in
one system on one benchmark.

That gap is the strongest number in this reading, and it is not an argument for an ordering rule.
It is an argument about **who wrote the oracle** — and the same paper narrows it further. On the
subset where the agent's own tests were valid reproduction tests, resolution was 93.3%, within a
point of the supplied-test condition. So the gap is not the agent being worse at resolving its own
tests; it is the agent's tests being invalid, which is the same finding the issue-to-test benchmark
reports from the other end. ⚠️ **A rule that produces an invalid test earlier produces nothing**,
and that is the clearest reason the ordering is the wrong thing to rule on.

## The four routes to satisfying the ordering without earning it

The item enumerated four. Each has been observed on model writers, and each is checked against what
this toolkit holds today. ⚠️ **The column is deliberately mostly empty**, and the rule it is read
against — a test earns its place by covering a decision, and its red is confirmed by writing the
violation first — refuses a change nowhere:
[§ *What earns a test*](../plugins/mjolnir/config/schema.md#what-earns-a-test-and-what-makes-its-red-believable)
states that nothing under it fails a change, which is the premise this column reports against rather
than a defect it discovers.

| Route | Observed as | What in this toolkit reaches it today |
|---|---|---|
| The test written to the implementation the writer already intends, so the ordering is nominal | The 25%-against-14% fault-detection split, whose treatment condition is a context blind to the implementation rather than a sequence; and the test generators that assert the behaviour the code has | **Nothing.** No check, hook or gate reads authorship order, context provenance, or what the session held when it wrote the assertion. The reviewing role reads a diff that adds a test against the surface's discipline, which is a reading by the same session that wrote it |
| The assertion weakened until it passes, rather than the behaviour changed until it does | 80.2% of agent-authored test patches carrying a weak oracle or none; agent test files carrying more runtime-printing statements than assertions; and, under reinforcement learning, assertions defeated outright by exiting before they run or by returning the values parsed out of the test file | **Nothing holds an adopter's test.** Inside this repository one mechanism bites: every gate workflow mirrors its script's own self-test, which asserts each check reddens on each planted violation and stays green on each planted exemption. ⚠️ Its blind spot is the item's own: the plant and the assertion have the same author |
| A red produced by a stub or an import error rather than by the behaviour being absent, so the red proves the file is missing | The benchmark residue — 243–395 tests failing on the old code against 37–106 passing on the new one — which is precisely a red that survives the fix | **Partially, and not here.** [§ 16](../plugins/mjolnir/config/schema.md#16-what-a-run-executed-and-the-count-that-is-the-only-evidence-it-ran) makes a run reporting zero executed cases against a non-zero declaration a failure rather than a pass, and requires a skip count to carry what the skipped cases wanted. ⚠️ That holds a *skipped* case, never a red's cause — and this project states no executed count at all, so even that arm is absent here |
| The test rewritten when it reddens later, which is the same move one step downstream | *Building to the test*: with the oracle in the loop the score reached near-perfect while the shipped library was dead or absent; and the 7 hand-found instances of test hacking in 800 gold-test runs, which is the rate when a person reads every run | **Nothing.** No check reads a test's history, and the suite runner reports an implementation with no suite rather than failing it. A test deleted, weakened or re-aimed in the same change that reddens it is a finding a reviewer may raise and no mechanism raises |

⚠️ **The one mechanism that does bite is worth naming precisely**, because it is the form a workable
rule would most likely take here: the plant. A check in this repository is believed because its own
self-test breaks the thing and confirms the red, and that is mechanical, mirrored per workflow, and
run on every change. It is also the narrow case — the artifact under test is a checker, the
violation is expressible as a mutated input, and the author of the plant is the author of the check.

## What no source answers for a model writer

Three gaps, each stated as a gap rather than filled by generalising from the human case.

**The design benefit is unmeasured.** No located study isolates test-first ordering as the
independent variable and measures a design outcome — interface shape, coupling, modularity,
revision churn on the interface — for a model writer. Work that moves design metrics manipulates
design artifacts instead: contracts, architecture documents, explicit plans. So the causal chain
the rule would be adopted for is untested at both links for this writer.

**The ordering has not been tested on work like this repository's.** Every model-writer measurement
above is on function-level benchmark tasks, or on repository-scale issue resolution in
general-purpose code. None is on procedure, schema or checker work, where a decision is a parse, an
ordering or a refusal, and where the production artifact is frequently prose that a checker reads.

**Nobody has measured the ordering against a reviewing leg.** The studies compare orderings under
automated scoring, or an oracle supplied against an oracle self-authored. The condition this
toolkit's route would actually create — a model writing the test first, then the same model
reviewing the diff that contains it — appears in no measurement located here.

## What a measurement on this repository's own history would have to compare

Stated because the gap above cannot be closed from the literature, and because this repository is
one of the few places the comparison is cheap: the loop already records, per item, a branch, a
diff, a review and a gate.

| Term | What it would have to be |
|---|---|
| Unit of analysis | One work item, which is this repository's unit of both authorship and review |
| Treatment | The test authored before the implementation **from the item's own acceptance statement**, in a context not holding a draft of the implementation — the independence condition rather than the sequence, since the sequence is what the evidence says does not matter |
| Control | The test authored after the implementation in the same session, which is the current behaviour and needs no new arm to be collected |
| Primary outcome | Defects found after the change landed and attributable to it, counted per item — the only outcome here with an existing record, since a reopened item and a follow-up item are both in the tracker |
| Secondary outcome | Whether the test survived its own change unmodified, and whether the interface it was written against changed after it was written — the nearest decidable stand-in for the design claim |
| Confound that has to be held | Item size and item kind. The human literature finds task type dominating quality in a family of 12 experiments, and this backlog's items range from a one-line refusal to a whole port |
| Confound that cannot be held | Model version across the span of the history, and the fact that every item was authored by the same loop under the same instructions, so the comparison is within-writer and not between writers |
| Floor for an answer | Stated before collecting, not after. ⚠️ With the kind of effect the human meta-analysis reports — Pearson's *r* in the small range — a backlog of this size cannot distinguish a small effect from none, which is a reason to prefer the independence manipulation, whose measured effect is large |

## The human-reading candidate, answered

The candidate raised when the item was filed was that *tests likely need human review for real
boost*. It is supported, it is the best-supported intervention in this reading, and it is expensive
in the one currency this loop is short of.

| | |
|---|---|
| Which leg it would be asked at | The implementing leg, before the implementation is believed — which is after the branch is cut and before the finishing role is entered, per [§ *What carries the item forward*](../plugins/mjolnir/config/schema.md#what-carries-the-item-forward-and-where-it-stops-to-ask). It is a stop that asks, not a check a session answers about its own work, and that is the whole of its value: it is the one arm that does not have the author and the assertion in the same place |
| What it costs per item | One interactive round on average and up to five for the measured benefit — 1.69 validation queries to reach a test consistent with the person's intent, for 90.40% of cases, in the interactive study. In the industrial filtered-then-reviewed deployment the reviewer accepted between 73% and roughly half of what reached review, so between one rejection in four and one per acceptance |
| Whether the reading supports it | Yes, and from two independent directions: validating model-proposed tests before the code took pass@1 from 48.39% to 70.49% on one query, and the user study doubled correctness, 84% against 40% (p = 0.001). Independently, supplying human-written tests to a repository-scale agent is worth 26.3 points of resolution over self-generated ones, and the subset analysis attributes that gap to the validity of the test rather than to who resolved it |
| What it does not fix | The three routes the table above marks *nothing*. A person reading the test catches a weak assertion and a test aimed at the intended implementation; it does not catch a test rewritten later, unless the person reads every change to it. The 7-in-800 figure is what exhaustive human reading of every run found, which is both what that arm catches and what it costs |

⚠️ **The cost figure is the part to carry forward rather than the effect figure.** A stop that asks
per item is a stop on every item, and this project's own configuration states a solo build with one
identity behind every role — so the person it would ask is the person the loop exists to keep out of
the per-item path.

## What this document does not decide

No rule is written onto the surface by this reading, no key is added to it, and no role is designed
here. The wording of whatever rule follows, and the design of any role that would ask a person to
read a test, are each their own item's. The sentences above are a record of what is measured, not
instructions to a later session.

## Where the sources are

Named inline above, by author, title, venue and identifier, so that each claim can be weighed
against its source rather than against this summary. Where a figure is quoted it is the source's
own; where two of a source's own numbers disagree across its tables that is said in the row rather
than resolved here — the issue-to-test benchmark's headline and its ordering ablation are the one
instance.
