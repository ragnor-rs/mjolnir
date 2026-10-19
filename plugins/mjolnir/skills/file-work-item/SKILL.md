---
name: file-work-item
description: Turn a request into well-formed work items — decomposed, checked against everything the tracker already holds, written to the project's own template, and related to what they block. Use when asked to file, create or open an issue, card or task, or to turn a request or a chat log into tracked work.
argument-hint: "[priority]"
---

# File a work item

Produces **tracked work items, or a reasoned refusal to produce one**. Filing is the cheapest step
of the loop and the one whose mistakes are hardest to undo: a duplicate sits open forever beside
the item it duplicates, and a body with no acceptance condition is a note that every later role has
to guess at.

Read the project's configuration first, by running the shared reader:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/config.py"
```

⛔ **Say which project was resolved before reading anything else**, naming what
[`config/schema.md § 1`](../../config/schema.md#the-skills-root-is-where-the-role-runs) lists there
— the reader reports each item, and the skills root is the directory this role was invoked in.
⚠️ Invoked anywhere else, this role resolves whichever project has a configuration there and files
into **that** project's tracker. Saying it is the only thing that makes the mistake visible, and it
is one sentence.

⛔ **Do not parse that file here.** A skill that reads the configuration itself is a second set of
defaults, and two sets drift apart without anything noticing. Every type, template, label, language
and policy below comes from the reader's output; this file holds the procedure and none of the
values.

Then read what the tracker can actually do:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/port.py"
```

⛔ **Take each absent operation's stated fallback from that output, and never improvise one.** The
fallbacks are
[`§ 3`](../../config/schema.md#the-operations-and-what-an-absent-capability-does)'s and are stated
there once; restating any of them here would be a second statement allowed to disagree. ⚠️ **An
absence is a configuration, not a fault** — a project may run with no tracker at all, and this role
still produces a body and a report.

⛔ **Read the `unavailable` list before acting**, and name in the reply any entry that bears on
filing: a facet absent by decision changes what this role writes, and reads nothing like a facet
nobody configured.

## 0. The request is the input, and noticing is not a request

⛔ **This role runs on an explicit request to file and on nothing else.** Deciding that something
*deserves* an item is not that request: work noticed in passing is named in the reply and stops
there.

The request should already be in the session — a chat log, a bug report, a finding quoted out of a
document, a gap found while reading. If it is not, ask for it rather than reconstructing one.

⚠️ **A question is not a work item.** A request that is an open question or a proposal belongs in
the conversation with whoever asked it; say so and stop. Filing it converts somebody's uncertainty
into a commitment nobody made.

`$ARGUMENTS` may carry a priority. Where the project's tracker carries one, it is set from there;
where it does not, the reader says so and the argument is reported as unused rather than silently
dropped.

## 1. One request is often several items

Pull out of the request what has to be done, why, any stated constraint, and the nature of the
work. Then split it into the **smallest independently-shippable units**: granular items are easier
to estimate, to review and to deduplicate, and one broad item hides duplicates inside itself and
stalls.

⛔ **Present the split and have it confirmed before anything is written.** Skip the question only
where the request is unambiguously one item. Without this step one request silently becomes one
item, which is the failure that makes every later duplicate check useless — the duplicate is inside
the item nobody split.

Sections 2–6 then run **once per confirmed item**. Report them together at the end.

## 2. The duplicate check — three layers, then a gate

**This is the one search this role performs, so it is performed whole.** One keyword net misses
reworded duplicates, and the cost is paid once and permanently.

⛔ **Record every query and its hit count**, for the reply. "Nothing found" is a claim, and it is
reviewable only if the queries behind it are visible.

⛔ **Never filter by state.** An item that is closed, done or rejected still answers the question:
an idea raised and dropped is exactly the duplicate worth finding, and it is the one a default
query hides. Where the tracker holds archived items behind a separate flag, that is a second pass,
not an option.

⚠️ **Where `search_items` is unavailable, its absence governs this whole section** rather than
weakening one layer of it. Take what it does from the table and do exactly that — it is the one
fallback this role's outcome turns on, which is why it is named here and not described.

**2a. Keyword axes — derive the queries, never improvise synonyms.** Decompose the request into
four axes and derive terms per axis:

| Axis | What it names |
|---|---|
| Surface | the screen, module, flow or area the work touches |
| Action | the verb — what is added, removed, changed, made faster |
| Object | the noun the action targets |
| Symptom | for a defect only: the observed failure |

Aim for at least one query per populated axis, plus one per genuine synonym. Terms go in
`language.work_item` ([`§ 8`](../../config/schema.md#8-language-register-audience--per-artifact-not-per-project))
first, with latin technical names supplemented where the item language is not latin — a term
nobody writes on items finds nothing.

**2b. The keyword-independent sweep.** Pull items with **no keyword at all** and read every title
against the request: filtered by the request's own area where the tracker can filter by a field,
and otherwise the most recently updated, bounded and with the bound reported. ⛔ **This layer is
not optional and it is the one that gets dropped** — it is the only layer that can catch a
duplicate whose wording shares nothing with the request, which is what a reworded duplicate is.

**2c. Tier by meaning, not by shared words.** Pool 2a and 2b, drop the repeats, and read each
promising candidate's own body before judging it:

| Tier | Test |
|---|---|
| High | the same user-visible outcome, or the same defect |
| Medium | plausibly the same; scope or wording differs enough to be unsure |
| Low | the same area, a genuinely distinct change |

**Scale mismatch is judged here, and it cuts both ways.** A candidate that is a **broader umbrella**
which would merely absorb this request is **not** a duplicate: file the granular item and relate it.
Candidates that are **smaller pieces already covering the request** mean this request is too broad:
file only the genuinely missing piece, never an item overarching the ones that exist.

**2d. Then gate the write.** ⛔ **Any candidate above Low stops this role and puts the question to
whoever asked**, each presented with its identifier, title, state, tier, a one-line reason, and the
relationship from § 3. **Updating the existing item is the recommended answer and goes first** on a
High-tier candidate: a second item describing work somebody already recorded is the mistake this
step exists to prevent, and the one nobody notices afterwards, because both items read reasonably
on their own.

⛔ **Only a search that came back empty on every query — and no open item whose acceptance the
request would serve — files without asking.** Say so in one line, naming both halves: that is the
claim the reply is making.

## 3. The three relationships, and the parent case that reads like a clean check

- **Duplicate — the same outcome or the same defect.** The existing item is **rewritten** to what
  the work now is, per
  [`§ 3`](../../config/schema.md#a-duplicate-is-the-item-rewritten-never-a-second-item-filed), and
  sections 4–6 do not run for it. ⚠️ **Reworded, differently scoped, or classified under another
  area is still the same work** — the test is whether doing one leaves the other with nothing to
  do, never whether the two read alike.
- **Parent — the request is a *piece* of an item that is already open**, named in its body, its
  acceptance condition or its checklist. ⛔ **The default is a check item on the parent, not a new
  item.** A child restates a promise the parent already made: both then sit open, both read as
  work nobody did, and closing the child does not close the condition. Add the check item, say
  which parent and which condition it serves, and stop — sections 4–6 do not run.
- **Contradiction — the request conflicts with what an open item states.** Stop and resolve it
  before anything is written.

⚠️ **The parent case is the one that gets misread, and it reads exactly like a duplicate check
coming back clean:** the parent's title is broad, the request is specific, and no query connects
them. ⛔ **So before concluding there is no duplicate, read the acceptance conditions and
checklists of every open item the request could belong under.** A condition nobody has met yet is a
parent, and the wording will not match — a condition states an outcome where a request states a
task.

⚠️ **Where the checklist capabilities are unavailable**, the parent outcome takes their stated
fallbacks — the read and the write have different ones. ⛔ **This step turns on the read's**, so
take it from the table literally: concluding there is no parent because a checklist could not be
read is the exact failure this section exists to prevent.

**A child item is the exception and it needs a reason said out loud:** the piece is independently
shippable, somebody else owns it, or it is large enough that the parent cannot be sized while it is
inside. ⛔ **"It is easier to track separately" is not one of those** — that is what the parent's
checklist is for. Where a child is genuinely right, the relation is recorded at both ends in § 5.

## 4. Type, template, and the body

**The type** comes from [`§ 4.1`](../../config/schema.md#41-type)'s carrier, whichever that is —
native on one tracker, a label on another, absent on a third. Ask for "the type" and let the
reader's output say what answers it.

**The template is the project's data, and this role renders it.**
[`§ 4.4`](../../config/schema.md#44-template) names the **semantic** sections the procedure depends
on — the outcome, the acceptance condition, the reproduction — and each template declares which of
its own headings fills each. ⛔ **Never invent a heading where the template declares one.** The
heading text, and its language, are the project's; what this role requires is that the semantic
sections be present and filled.

⛔ **The type and the template the body uses must agree, and a mismatch stops.** Nothing downstream
refuses one: it surfaces later as a branch under the wrong prefix, and a branch name is the thing
nobody goes back and corrects. State both values in the stop.

⛔ **Read which template a body uses from which semantic sections it carries, never from the heading
text** — [`§ 4.4`](../../config/schema.md#44-template) states why the text cannot tell two
templates apart.

**Both facets have an absent case, and filing works in it.** Where no carrier states a type, there
is no type to cross-check and the reply says so rather than reporting a check that passed. Where
there is no template at all, this role writes the semantic sections under headings it chooses in
the item's own language — the outcome and the acceptance condition are the procedure's, not the
template's, and an item that states neither is a note rather than work.

**The body is written to be validated by whoever ordered the work**, not by whoever will do it. The
acceptance condition is the whole point of the item: work can only be rejected against what was
agreed when it was assigned, so a vague condition now is protection given away.

⛔ **Observe `tracker.policy.forbid_on_item`**
([`§ 3`](../../config/schema.md#a-write-forbidden-by-policy-rather-than-by-capability)). Where a
class of fact is barred from reaching an item, it goes in the reply instead. ⚠️ The instinct that
defeats this is always *this detail is genuinely useful context* — it usually is, and the item works
without it.

**Language, register and audience are per artifact**
([`§ 8`](../../config/schema.md#8-language-register-audience--per-artifact-not-per-project)). The
item is written in `language.work_item` — headings included — whatever language the request arrived
in. Only what is not prose stays as it is: product and technology names, URLs, file and branch
names, and identifiers cited from elsewhere.

⚠️ **A citation of another document owes two parts** — the source, named or linked, and the cited
item's own title verbatim. A bare locator names no item and an unattributed quote names no source.
An identifier is owed only where the source has one.

## 5. Write it, and record the relations

Write the item through `create_item`. ⚠️ **An item exists the moment that call returns**: a later
label, relation or field call that fails leaves an item that is on the tracker and incomplete, not
absent. Say that, and fix it — never retry the create.

Then set what the project carries, each through its own operation, taking the stated fallback where
a capability is absent: the labels, the assignee, and the relations below.

**Relations are recorded through `link_dependency`, in the tracker, never as a line of prose in the
body** — except where that capability is absent, which is the one case its fallback allows.

⛔ **Restate the direction in plain language before writing it.** "B cannot ship until A is done"
means B is blocked by A. Terse phrasing is ambiguous in both readings, and a misread direction costs
a remove-and-recreate round trip.

⛔ **A relation is between the work, never between the branches.** The test: could this item be
built and accepted if the other did not exist? A stacked change, a branch cut off another branch,
an agreed merge order — all of that is sequencing, and none of it is a relation. ⚠️ The cost is not
cosmetic: a readiness gate refuses an item whose blocker is still open, so a merge order written up
as a relation turns finished work into work that reads as blocked.

⚠️ **Tolerating and requiring are different, and the test is each consumer's own acceptance
condition** ([`§ Nothing is deferred`](../../config/schema.md#nothing-is-deferred)). An item every
consumer can be built *tolerating* is not a blocker, and recording it as one stops work that
nothing is waiting on.

## 6. Verify, and report

Read each item back rather than trusting the write. Check the body rendered, the semantic sections
are present and filled, the type and the template agree, every label the project requires is
attached, the item is in the configured language throughout, and every relation reads correctly
from **both** ends — the reverse end is a write to a different item, so it is the one most easily
skipped.

⚠️ **Read the language check literally, against the fetched text.** Where the request arrived in
another language, one heading or one acceptance condition slips through in it, and nobody catches it
later because the item looks finished.

Then report, in the register
[`§ 8`](../../config/schema.md#the-reply-to-the-person-running-a-role) states:

- what was resolved — the root, the configuration file, the repository and the tracker;
- every item filed or rewritten, with its identifier and title;
- **the duplicate-search coverage**: every query with its hit count, the sweep in 2b and its bound,
  and every candidate above Low with its tier and its relationship. Where a candidate was found and
  an item was filed anyway, name it, the relationship, and the grounds — that is the decision this
  report exists to record;
- **on the parent outcome**: the check item written, the parent, and the condition it serves — and
  that no item was filed, said plainly;
- every relation written, and which other items were edited to carry the reverse end;
- the type and the template used, or that the project carries neither;
- **every fallback taken**, naming the operation and what it did instead;
- anything barred by policy, and anything that could not be established.

⛔ **A question this role cannot answer is asked, not noted**
([`§ Nothing is deferred`](../../config/schema.md#nothing-is-deferred)): the question, the options,
what each costs, and which is recommended. The pass is not finished while a question it raised is
open, and a gap written up thoroughly still reads as diligence while leaving the work undone.
