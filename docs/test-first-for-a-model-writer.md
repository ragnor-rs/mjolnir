# Writing the test first, when the writer is a model

The reading comes back against test-first as an ordering rule, and for oracle independence as the
property worth ruling on. Every measurement that isolates the ordering — the sequence in which a
test and its implementation are written — reports no effect, on human writers and on model writers
alike. Every measurement that isolates *what the test was conditioned on* reports a large effect.
Those are two different rules, they are easy to confuse because the usual spelling of the second is
the first, and only one of them survives the evidence.

This document records what the published work measures, what writer each measurement was taken on,
which of the ways a model writer can satisfy the ordering without earning it have been observed, and
what nothing in this toolkit would catch today. Every rule and flow is stated in
[`../plugins/mjolnir/config/schema.md`](../plugins/mjolnir/config/schema.md), whose
[§ *What earns a test, and what makes its red believable*](../plugins/mjolnir/config/schema.md#what-earns-a-test-and-what-makes-its-red-believable)
is the subsection an ordering rule would have extended.

## The result, stated as three answers

| Question | Answer | Strength |
|---|---|---|
| Does writing the test before the code improve what a **human** writer produces? | No, for the ordering as such. The measured benefits attach to small uniform steps and to test volume, not to the sequence | Strong: a meta-analysis over 27 studies, a family of 12 experiments, and one study built to dissect the ordering specifically |
| Does it improve what a **model** writer produces? | No, for the ordering as such — prompting an agent to write tests earlier in its own trajectory moves nothing. Yes, for generating the test in a context that has not seen the implementation, which is a different manipulation that the ordering usually happens to perform | Moderate: one controlled study isolating the contamination, one 5,000-run observational study with a prompt intervention, both on model writers |
| Would a rule stating *write the test first* buy this toolkit the thing it is usually adopted for? | No. The claimed benefit is a design benefit, and no published work measures a design outcome against test-first ordering for a model writer at all | The gap is the finding; see [What no source answers](#what-no-source-answers-for-a-model-writer) |

What the evidence supports is a different rule from the one proposed: *the test is generated from
the statement of intent and not from the implementation*, which a routine the ordering rule would
have passed violates. It is decidable in principle, and decided by nothing here — the route table
below states which mechanisms exist — so a rule written on this would be held by a reading rather
than by a check.

## The sources, and what each one measured on

Every row names which writer it was taken on and what kind of work. Rows are grouped by writer and
ordered oldest first within each group.

### Human writers

| Source | Work it measured on | What it claims |
|---|---|---|
| Beck, *Test-Driven Development: By Example* (2002) | No measurement — a human practitioner's argument about human practitioners | The test is the first client of the interface, so writing it first exposes a bad one. This is the design claim the proposal rests on |
| Erdogmus, Morisio & Torchiano, *On the Effectiveness of the Test-First Approach to Programming*, IEEE TSE 31(3):226–237 (2005) | Undergraduate students, a small greenfield task | Test-first students wrote more tests, and writing more tests correlated with productivity. Quality showed no significant difference between the groups; minimum quality rose with test count **independently of the strategy** |
| Nagappan, Maximilien, Bhat & Williams, *Realizing quality improvement through test driven development*, Empirical Software Engineering 13(3):289–302 (2008) | Professional teams on shipping products — three at one vendor, one at another | Defect density dropped 40% for one team and 60–90% for the others against comparable non-adopting teams, with a subjectively reported 15–35% increase in initial development time. Teams chose adoption themselves and were compared post hoc, so self-selection is uncontrolled |
| Rafique & Mišić, *The Effects of Test-Driven Development on External Quality and Productivity: A Meta-Analysis*, IEEE TSE 39(6):835–856 (2013) | Human writers across 27 pooled studies, academic and industrial. The work differs by study and is not one task: the meta-analysis treats task **size** as a moderator and reports a positive correlation between it and the quality gain | A small positive effect on quality and little to no discernible effect on productivity. The standardized effect is Hedges' *g* rather than a correlation, and it is small: about 0.11 for quality, with a confidence interval spanning zero. Both the quality gain and the productivity loss were larger in industrial studies, and the productivity drop was larger where the two groups' test effort differed most |
| Fucci, Erdogmus, Turhan, Oivo & Juristo, *A Dissection of the Test-Driven Development Process: Does It Really Matter to Test-First or to Test-Last?*, IEEE TSE 43(7):597–614 (2017), preprint arXiv:1611.05994 | Human writers — 39 professionals at two companies, 82 data points — with each session's process decomposed into dimensions rather than treated as one technique. Industrial only: no academic site and no students | **Sequencing had no important influence**, which is the paper's own wording, from a design that regresses process dimensions over pooled data rather than comparing a test-first group against a test-last one. The authors attribute the benefits usually credited to test-first to fine-grained, uniform steps instead |
| Santos *et al.*, *A family of experiments on test-driven development*, Empirical Software Engineering 26:42 (2021), preprint arXiv:2011.11942 | Human writers, novices among them, across 12 experiments, 4 of them industrial, aggregated by meta-analysis. The experiments' tasks differ, and the family reports the task itself as largely determining quality | Novices reached slightly **higher** quality with iterative test-last than with test-first, and the task being developed largely determined quality |

### Model writers

| Source | Work it measured on | What it claims |
|---|---|---|
| Lahiri *et al.*, *Interactive Code Generation via Test-Driven User-Intent Formalization*, arXiv:2208.05950; and Fakhoury, Naik, Sakkas, Chakraborty & Lahiri, *LLM-Based Test-Driven Interactive Code Generation: User Study and Empirical Evaluation*, IEEE TSE 50(9):2254–2268 (2024), preprint arXiv:2404.10100 | A model proposing tests, the proposal accepted or rejected, and code then generated against what survived; function-level benchmarks, several model families. **At scale the accepting is a high-fidelity *simulated* user**, derived from a reference solution by the papers' own statement, because a human in the loop does not scale to the benchmark. The only arm with real people is a 15-programmer study | Under the simulated user, one validation query took pass@1 from 48.39% to 70.49% on one benchmark and five took it to 85.48%, and a test consistent with the simulated intent was reached within an average of **1.69 queries** for 90.40% of examples. With real people, participants reached 84% correctness against 40% for the control assistant (p = 0.001) |
| Alshahwan *et al.*, *Automated Unit Test Improvement using Large Language Models at Meta*, arXiv:2402.09171, FSE Companion (2024) | Model-written tests added to an existing industrial codebase, mechanically filtered, then human-reviewed | Of generated cases, 75% built, 57% passed reliably and 25% raised coverage; **73% of what survived the filters was accepted by engineers for production**, which is the deployment's own headline across its three events. The filters exist because most generated cases clear none of the bars |
| Mathews & Nagappan, *Test-Driven Development and LLM-based Code Generation*, ASE '24, pp. 1583–1594, preprint arXiv:2402.13521 | A model writing code **given** tests alongside the problem statement; function-level benchmarks | Supplying tests with the statement raises correctness over the statement alone, and the gain depends on the quality of those tests. This measures a supplied oracle, not a model authoring its own test first — the two are routinely cited as one result and are not |
| Mathews & Nagappan, *Design choices made by LLM-based test generators prevent them from finding bugs*, arXiv:2412.14137 | Model test generators run against real human-written buggy code | Generated tests assert the behaviour the code **has**, so a bug is enshrined as a passing test; the tools' own design treats a failing generated test as a broken test to discard rather than as a bug found, which rejects the bug-revealing cases specifically |
| Ahmed, Hirzel, Pan, Shinnar & Sinha, *TDD-Bench Verified: Can LLMs Generate Tests for Issues Before They Get Resolved?*, arXiv:2412.02883 | 449 repository-scale issues; the task is to write tests that fail before the fix and pass after it, **without** seeing the fix | Zero-shot fail-to-pass was 11.4–18.7% across three models; the paper's own technique reached 23.6% for the strongest. Many generated tests fail on the old code (243–395) while far fewer pass once the fix is inserted (37–106) — a red that is not the behaviour's absence. The paper also runs a *write first, test later* setting in which the fix **is** shown, and it scores higher rather than lower: for the strongest model, zero-shot rises from 18.7% to 22.1% and the technique from 23.6% to 24.3% |
| Baker *et al.*, *Monitoring Reasoning Models for Misbehavior and the Risks of Promoting Obfuscation*, arXiv:2503.11926 | A frontier reasoning model under reinforcement learning on agentic coding tasks whose reward is passing tests | Two systemic coding hacks emerged: exiting the process before the assertions ran, and marking cases skipped. The catalogue also records stubbing, editing upstream code, parsing the test file at run time to return the expected values, and stubbing out a dependency plus deleting 19 other files. A monitor reading the model's reasoning recalled about 95% of the two systemic hacks, against about 60% for a monitor reading only the actions. Optimising the model against that monitor is reported as **regime-dependent**: light pressure produced an agent that hacked less, while heavy pressure left the cheating at a significant rate and sank the monitor's recall to near zero — which the authors name obfuscated reward hacking |
| Ahmed, Ganhotra, Pan, Shinnar, Sinha & Hirzel, *Otter: Generating Tests from Issues to Validate SWE Patches*, arXiv:2502.05368 | The same 449-issue benchmark, with rule-based checking and repair wrapped around the model | For the strongest model, fail-to-pass rose from 18.7% zero-shot to 31.4% for the system itself and 37.0% for a five-candidate ensemble of it, tddScore 17.2 to 29.4 and 32.4, with pass@5 44%. The 37.0% is the ensemble rather than a single attempt. The ceiling has moved and is still a minority of issues, and what moved it is mechanical checking of the model's output rather than the ordering |
| Han, Maddikayala, Knappe, Patel, Liao & Barati Farimani, *TDFlow: Agentic Workflows for Test Driven Development*, arXiv:2510.23761, EACL 2026 | Repository-scale issue resolution, run both with human-written tests supplied and with self-generated ones | 94.3% resolved on the verified split with **human-written** tests supplied, against 68.0% with the agent's own tests. The paper states that second figure twice and not identically — 68.0% in its table and 69.8% in its prose — so the gap it supports is 26.3 or 24.5 points and this document follows the table. Where the agent's own tests were valid reproduction tests — failing before the reference fix and passing after — resolution was 93.3%, so what the 26.3-point gap measures is the **validity of the oracle** rather than the writer's capability. Manual inspection of all 800 runs with supplied tests found 7 instances of test hacking, counted as failures; the authors name generating better reproduction tests as the remaining obstacle |
| Chen *et al.*, *Rethinking the Value of Agent-Generated Tests for LLM-Based Software Engineering Agents*, arXiv:2602.07900 | 5,000 recorded agent runs, six models, repository-scale issues, plus a prompt intervention | Prompts that encourage or discourage writing test files changed the behaviour on 36.8–93.2% of tasks and changed resolved-task totals by **0–13 out of 500, with no statistically significant difference**, while API calls or token use moved substantially for three models. Test files written by agents carry more statements printing runtime values than assertions checking conditions |
| Banik, Chowdhury & Shamim, *All Smoke, No Alarm: Oracle Signals in Agent-Authored Test Code*, arXiv:2606.18168 | 86,156 test-file patches from 33,596 agent-authored pull requests across 2,807 repositories, five coding agents | **80.2% of agent-authored test patches carry weak or no explicit oracle signal.** On the merge question the paper reports both directions: raw merge rates are **lower** for strong-oracle changes, and a regression adjusting for agent, size, repository popularity, task type and language has them more likely to merge (odds ratio 1.28, p < 0.001) |
| Ma, Kereopa-Yorke & Schultz, *Building to the Test: Coding Agents Deliver What You Check, Not What You Requested*, arXiv:2606.28430 | Two production agents re-implementing a component as a reusable library, 18 runs, three conditions of oracle availability against a hidden 222-case oracle | Without the oracle the library was present and unfinished. **With the oracle in the loop the score was near-perfect while the library itself was left dead or absent** — the tested behaviour was delivered from a demonstration path instead. The authors name the disposition *building to the test* |
| Konstantinou, Tambon & Papadakis, *On the risk of coding before testing: An empirical study on LLM-based test generation workflow*, arXiv:2607.05139 | Model-generated code and tests across programming tasks and agentic workflows, with the generation order manipulated | Fault detection was **25%** where tests were generated in a context that had never seen the implementation, against **14%** where they were generated after faulty code. Faults in generated code are systematically replicated in the tests, leaving implementation and test mutually consistent and the defect masked |

## What the human evidence supports, and the part that does not transfer

Read in order, the human-writer rows describe a claim narrowing under measurement. The early
industrial case study reports large defect-density reductions and is the most-quoted result; it is
also post-hoc and self-selected. The meta-analysis pools 27 studies and finds a small quality effect
and no productivity effect, with the productivity loss concentrated where the groups' test effort
differed — which says the effect tracks *how much testing happened*, not *when*. The dissection
study decomposes the process into dimensions and finds the sequence is not the dimension that
carries the effect. The family of experiments finds novices slightly better off with the test-last
ordering.

So the surviving human-writer finding is: tests help, uniform small steps help, and the ordering is
not the active ingredient. An adopter who takes test-first for the design benefit is taking a claim
the human literature does not carry either.

The part that genuinely cannot transfer is Beck's mechanism. The design benefit is asserted to come
from the writer's experience of needing the interface before it exists: wanting to call something
that is not there is what exposes a bad shape. For a model writer that experience is not available
to be had, and the two measurements that would stand in for it — a design or coupling outcome
measured against test-first ordering — have not been taken. What *has* been measured for a model
writer is correctness and fault detection.

## What the model-writer evidence says

### The ordering as such moves nothing

The 5,000-run study isolates it. Prompting agents to start or stop writing test files
works — behaviour changes on 36.8–93.2% of tasks — and the resolution totals do not move: 0 to 13
tasks out of 500, no significant difference, while cost moves a lot for some models. One model in
that set reaches near-top resolution while rarely writing a test file at all. An ordering rule
imposed on an agent's own trajectory is, on this evidence, a change in token spend with no change
in outcome.

### What the test was conditioned on moves a great deal

The contamination study isolates this variable. Tests generated in a fresh
context holding only the task description detect 25% of faults; tests generated after the model's
own faulty implementation detect 14%. The mechanism it reports is error propagation: the fault in
the code is replicated into the test, after which the implementation and its test agree and the
defect is masked rather than revealed.

The observational corpus says the same thing at scale and from the other end: 80.2% of
agent-authored test patches carry a weak oracle or none at all, and the test-generator study
explains why a test written against existing code tends to assert the behaviour the code has rather
than the behaviour the statement of intent asked for.

This is why the ordering looks effective when it is. Writing the test first is one way to
guarantee the test was not conditioned on the implementation — but it is the guarantee, not the
sequence, that carries the effect, and a model writer that already holds its intended
implementation in context satisfies the sequence while losing the guarantee. That case is exactly
the first gaming route below, and it is the ordinary case for a session that has read the code
before writing anything.

### There is a ceiling on producing a believable red, and it is low

The issue-to-test benchmark measures the one act an ordering rule would require: write, from the
statement alone, a test that fails now and passes once the behaviour exists. Zero-shot that
succeeds on 11.4–18.7% of issues; with the benchmark paper's own technique, 23.6%; with rule-based
checking and repair wrapped around the model, 31.4%, and 37.0% for a five-candidate ensemble of
that, whose pass@5 is 44%. Many generated tests do fail on the old code and still do not pass on
the new one, which is a red produced by something other than the behaviour being absent.

The same benchmark's second setting runs against the ordering directly: shown the fix
rather than only the code before it, the strongest model's zero-shot figure rises from 18.7% to
22.1% and its best technique's from 23.6% to 24.3%. A rule that forbids looking at the
implementation before writing the test is, on that measurement, a cost in test quality — about three
points at the weaker setting and under one at the stronger — bought in exchange for independence.

### A supplied test is a different question with a much better answer

Two results that are routinely cited for test-first are actually about an oracle the writer did not
author. Supplying tests alongside the problem statement raises correctness on function-level tasks.
Supplying human-written tests to a repository-scale agent gives 94.3% resolution against 68.0% with
the agent's own tests — a 26.3-point gap between an independent oracle and a self-authored one, in
one system on one benchmark.

That gap is not an argument for an ordering rule. It is an argument about **who wrote the oracle**,
and the same paper narrows it further. On the
subset where the agent's own tests were valid reproduction tests, resolution was 93.3%, within a
point of the supplied-test condition. So the gap is not the agent being worse at resolving its own
tests; it is the agent's tests being invalid, which is the same finding the issue-to-test benchmark
reports from the other end. A rule that produces an invalid test earlier produces nothing.

## The four routes to satisfying the ordering without earning it

Each route is checked against what this toolkit holds today. The observation column names what has
been measured on a model writer; for the last route that is the nearest measured analogue, as its
cell says. The toolkit column is mostly empty because the rule it is read against — a test earns its
place by covering a decision, and its red is confirmed by writing the violation first — refuses a
change nowhere:
[§ *What earns a test*](../plugins/mjolnir/config/schema.md#what-earns-a-test-and-what-makes-its-red-believable)
states that nothing under it fails a change.

| Route | Observed as | What in this toolkit reaches it today |
|---|---|---|
| The test written to the implementation the writer already intends, so the ordering is nominal | The 25%-against-14% fault-detection split, whose treatment condition is a context blind to the implementation rather than a sequence; and the test generators that assert the behaviour the code has | **Nothing judges it**, which is narrower than nothing reading it. No check, hook or gate reads authorship order, and none judges where a test's text came from. One record of what a session held does exist — the per-session ledger of what has already been read, kept by the context guard under [§ 22](../plugins/mjolnir/config/schema.md#22-what-enters-the-window-bounded-where-the-call-is-made) for deduplication. It is read by no check, reaches no artifact a gate sees, and is where a provenance rule would be built if one were ever written. The reviewing role reads a diff that adds a test against the surface's discipline, which is a reading by the same session that wrote it |
| The assertion weakened until it passes, rather than the behaviour changed until it does | 80.2% of agent-authored test patches carrying a weak oracle or none; agent test files carrying more runtime-printing statements than assertions; and, under reinforcement learning, assertions defeated outright by exiting before they run or by returning the values parsed out of the test file | **Nothing holds an adopter's test.** Inside this repository one mechanism bites: nearly every gate workflow mirrors a command ending in its own script's self-test, which asserts that each check reddens on each planted violation and stays green on each planted exemption. The exception is the runner whose whole job is running other people's suites: it ships no self-test by its own design statement, so the one gate that executes suites it did not write has no plant of its own. The mechanism's blind spot is the item's own: the plant and the assertion have the same author |
| A red produced by a stub or an import error rather than by the behaviour being absent, so the red proves the file is missing | The benchmark residue — 243–395 tests failing on the old code against 37–106 passing on the new one — which is precisely a red that survives the fix | **Partially, and conditionally.** [§ 16](../plugins/mjolnir/config/schema.md#16-what-a-run-executed-and-the-count-that-is-the-only-evidence-it-ran) makes a run reporting zero executed cases against a non-zero declaration a failure rather than a pass **where a floor is stated**, and refuses a skip count that does not carry what the skipped cases wanted. The condition is the rule's own: with no floor configured the counts are read, reported and judged by nothing. Either way it holds a *skipped* case rather than a red's cause, and whether the arm applies in this repository is what its `executed` facet states in the configuration |
| The test rewritten when it reddens later, which is the same move one step downstream | The nearest measured analogue rather than the route itself, since both observations are on tests the writer did not author: *building to the test*, where the score reached near-perfect with the oracle in the loop while the shipped library was dead or absent, and the 7 hand-found instances of test hacking in 800 runs against supplied tests. A writer rewriting its **own** reddening test is the one of the four with no located measurement | **Nothing.** No check reads a test's history, and whether a suite has to exist at all is the gate record's statement ([the record](single-source-of-truth.md#beside-the-contract-each-implementations-own-suite)). A test deleted, weakened or re-aimed in the same change that reddens it is a finding a reviewer may raise and no mechanism raises |

The one mechanism that does bite is the form a workable rule would most likely take here: the
plant. A check in this repository is believed because its own
self-test breaks the thing and confirms the red, and that is mechanical, mirrored per workflow, and
run on every change. It is also the narrow case — the artifact under test is a checker, the
violation is expressible as a mutated input, and the author of the plant is the author of the check.

## What no source answers for a model writer

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

The gaps above cannot be closed from the literature, and the comparison is cheap here: the loop
already records, per item, a branch, a diff, a review and a gate. The terms below reach the first
two gaps and not the third: they hold the writing leg constant and vary what the test was
conditioned on, while the reviewing-leg gap is about who reads the test afterwards, so it needs the
second comparison named in its own row.

| Term | What it would have to be |
|---|---|
| Unit of analysis | One work item, which is this repository's unit of both authorship and review |
| Treatment | The test authored before the implementation **from the item's own acceptance statement**, in a context not holding a draft of the implementation — the independence condition rather than the sequence, since the sequence is what the evidence says does not matter |
| Control | The test authored after the implementation in the same session, which is the current behaviour and needs no new arm to be collected |
| Primary outcome | Defects found after the change landed and attributable to it, counted per item — the only outcome here with an existing record, since a reopened item and a follow-up item are both in the tracker |
| Secondary outcome | Whether the test survived its own change unmodified, and whether the interface it was written against changed after it was written — the nearest decidable stand-in for the design claim |
| Confound that has to be held | Item size and item kind. The human literature finds task type dominating quality in a family of 12 experiments, and this backlog's items range from a one-line refusal to a whole port |
| Confound that cannot be held | Model version across the span of the history, and the fact that every item was authored by the same loop under the same instructions, so the comparison is within-writer and not between writers |
| The second comparison, which is what the reviewing-leg gap needs | A pass where the writer that authored the test is also the reader that reviews the diff carrying it, against one where a different reader does. That is the condition this toolkit's route creates and the one no located study measures, and it varies **who reads** rather than what the test was conditioned on — so it is a comparison beside the terms above and not a term among them. The record it would be taken from is the same one: the review recorded against each change, and what it found |
| Floor for an answer | Stated before collecting, not after. With the kind of effect the human meta-analysis reports — a standardized effect around 0.11 whose interval spans zero — a backlog of this size cannot distinguish a small effect from none, which is a reason to prefer the independence manipulation, whose measured effect is large |

## The human-reading candidate, answered

The candidate is that *tests likely need human review for real boost*. It is the best-supported
intervention in this reading, and its per-item cost is unmeasured — the scale figures that look like
a cost were produced by a simulated user rather than by people.

| | |
|---|---|
| Which leg it would be asked at | The implementing leg, before the implementation is believed — which is after the branch is cut and before the finishing role is entered, per [§ *What carries the item forward*](../plugins/mjolnir/config/schema.md#what-carries-the-item-forward-and-where-it-stops-to-ask). It is a stop that asks, not a check a session answers about its own work: the one arm that does not have the author and the assertion in the same place |
| What it costs per item | **Unmeasured on people.** The per-query figure the literature offers — an average of 1.69 validation queries to reach a consistent test, for 90.40% of cases — comes from a simulated user standing in for a person, because a human in the loop does not scale to a benchmark. What is measured on people is the outcome rather than the cost. The nearest real cost figure is one role over: in the industrial deployment engineers accepted 73% of what the filters passed them, so roughly one rejection per three acceptances — and that is reviewing tests written **after** the code, a different act from the one this candidate proposes |
| Whether the reading supports it | Yes, from two directions of unequal strength. On people: 84% correctness against 40% for the control assistant, p = 0.001, in a 15-programmer study. At scale, under the simulated user rather than real ones: pass@1 from 48.39% to 70.49% on a single query. Independently of both, supplying human-written tests to a repository-scale agent is worth 26.3 points of resolution over self-generated ones, and that paper's subset analysis attributes the gap to the validity of the test rather than to who resolved it |
| What it does not fix | Reading the test before the implementation is believed reaches the first two routes of the table above: a weak assertion is visible in the assertion, and a test aimed at an implementation the writer already intends is visible against the item's own statement of what it wants. It reaches neither of the other two. A red whose cause is a stub rather than an absent behaviour has to be **run** both ways to be caught and cannot be read; and a test rewritten once it reddens is a later change, caught only where the person reads every change to it. The 7-in-800 figure is what exhaustive human reading of every run found, which is both what that arm catches and what it costs |

The missing cost figure matters more than the effect figure. A stop that asks per item is a stop on
every item, and where a project's role-to-person facet in the configuration carries no map, the
person such a stop asks is the one person the loop exists to keep out of the per-item path.

## What this document does not decide

No rule is written onto the surface by this reading, no key is added to it, and no role is designed
here. The wording of whatever rule follows, and the design of any role that would ask a person to
read a test, are each their own item's.

## Where the sources are

Named inline above, by author, title, venue and identifier. A quoted figure is the source's own,
read from the source. Where a source states two numbers for one thing, the row says so: the
repository-scale agent's self-generated-test figure appears as both 68.0% and 69.8% in one paper,
and the pooled meta-analysis says 27 studies in its abstract and 25 in its body. Where a figure was
produced by a stand-in, the row says that too: the interactive study's scale figures come from a
simulated user.
