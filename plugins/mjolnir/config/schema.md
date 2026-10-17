# The configuration surface

Every per-project fact the shared procedure needs, named once. A project states these in
`.claude/mjolnir.yaml`, relative to its **skills root**. The procedure reads them; it never
names a value itself.

**This file is the single statement of every rule and flow of the shared procedure.** The
documents under `docs/` explain why the surface has this shape and record how each divergence
was settled; the work items track what is not yet built. None of them is a second authority —
where another text appears to state a rule, the binding form is the section here that it cites.

⛔ **That claim is held mechanically, not by review.** A gate on every change asserts that every
citation of this file resolves, that every section here is motivated by at least one document,
that every ruling's outcome lives here or in a named work item, and that no document states a
binding rule without citing the section that binds it. What no check can establish is
**fidelity** — whether a paraphrase elsewhere still matches the section it cites — because a
check that quotes a sentence back at the text it came from goes red on an innocent reword and
green when a claim is reworded into its opposite. So a document paraphrases as little as it can
and cites instead, and a reviewer covers the rest. The checks, and what each deliberately leaves
alone, are in [`docs/single-source-of-truth.md`](../../../docs/single-source-of-truth.md).

**The boundary this file defends:** a fact that cannot be expressed here is either procedure —
in which case it belongs in a skill — or a project-specific skill that stays in that project.
It is never a special case in the toolkit.

**Absence is a configuration, not a gap.** Four of these facets have a real absent case. A
facet that is deliberately absent carries `absent_reason` and, where one exists, `revisit_when`:
a stated decision with a trigger rather than an unset value. A skill must run against a config
whose tracker is `none`, and must not report that as a broken install.

**Where the values live.** No value in this file appears anywhere under `skills/`. The
`examples/` directory beside it holds whole configurations for each tracker and is data rather
than procedure — it is the one place in the toolkit where a concrete status word or label prefix
is written down, and it is excluded from the "names no particular project" search by being
examples of a shape rather than any project's facts.

---

## The file itself

```yaml
version: 1
```

One key is not a facet. `version` states which revision of this surface a configuration was
written against, so a reader of an older file can tell a deliberately absent facet from one that
did not exist yet. It is the only key that describes the file rather than the project, and it is
the only key every configuration carries unconditionally.

## The loop — nine roles

File a work item · gate it into committed work · start it · finish it · review it · deploy ·
log the day · keep the session's books · produce deliverables. Two utilities travel beside the
loop without being part of it.

A project maps a subset — an absent role is a legitimate configuration, not a partial install;
one adopting project runs a single role. Each role's carrier (skill, command or hook) is §7's
axis.

Gating is a role of its own, not a step of filing or of starting: it owns the date and the
estimate (§4.3), and starting never re-runs it — re-gating recomputes a commitment somebody may
already have been given.

**The surface has five independent axes, not three:** the work-item tracker (§3), the code host
(§2), the code root (§1), each role's carrier (§7), and language/register/audience per artifact
(§8). The measurements that forced each to be independent are in
[`docs/configuration-surface.md`](../../../docs/configuration-surface.md).

## 1. Roots — three independent paths

```yaml
roots:
  skills: "."              # where this config lives; default "."
  code: "."                # the path every git and gh call addresses
  code_is_own_repo: false  # true when `code` is a separate repository from `skills`
```

⛔ **The code root is configured, never inferred.** `git rev-parse --show-toplevel` from the
skills root is wrong wherever these differ, and a `gh` call that inherits the working directory
addresses the wrong repository — both having done something plausible first. Every `git` and
`gh` invocation in the shared procedure names its root explicitly.

`code_is_own_repo: true` is the case where the code is a git-ignored subdirectory that is its
own repository, possibly under a different owner, and not a submodule. Branches, pull requests
and CI then belong to the inner repository and the engagement material to the outer. A skill
stops rather than proceeding when a `code` root that should exist does not — a fresh clone of
the outer repository does not have it.

## 2. Code host

```yaml
host:
  kind: github
  repo: "OWNER/NAME"       # stated, never inherited from the working directory
  checks:                  # the host's own runs, keyed by workflow name — never job name
    - workflow: "…"
      mirrors: "<local command>"   # the local command whose verdict this run duplicates
      triggers: "<base pattern>"   # what starts it: a pull-request base pattern, or every push
      paths: ["…"]                 # path filters; omitted when the workflow runs on every change
```

Independent of the tracker. A project may keep its cards in one system and its code in another.

**`checks` is the single statement of the host's workflows and jobs** — which runs exist, which
local command each one mirrors, what triggers it, and which paths it watches. Every consumer reads
it and none carries the facts itself: the finishing role's CI-answer preconditions, and the guards
that refuse a local check the host has already run. The facet is mandatory on a project whose host
runs anything; `checks: []` is the one legitimate absence and means every verdict is local.

⛔ **The mapping is configured, never inferred.** A run's name does not say which local command it
duplicates, so no consumer derives the map from the host at run time — the host is read only for
live state: which runs exist for this commit, and how each concluded.

⚠️ **The key is the workflow name, never the job name.** Two unrelated workflows named their job
identically, and a job-keyed map refused a build on the strength of a check that only validated a
title.

⛔ **Absence of signal is not an answer.** A conflicted pull request produces zero runs; a
billing-suspended run fails in seconds having started no steps; a path-filtered workflow
legitimately runs nothing on a change outside its paths. An empty or silent check list reads as
*no answer* — never as green, and never as coverage.

## 3. Tracker port

```yaml
tracker:
  kind: github-projects | jira | trello | none
```

The shared procedure names **the port and never a tracker**. Each `kind` carries its own block;
see `examples/`. Three properties of the port the procedure depends on:

- **Capabilities are queried, not assumed.** Comment, delete-a-checklist-item,
  set-labels-atomically and assign-a-member are each unavailable on at least one tracker. The
  procedure has a stated fallback per absence and does not fail. Where comments are impossible,
  a gate result is written into the item's description instead.
- **Closing is declarative on one tracker and imperative on another.** `link_for_close` and
  `advance_on_merge` are separate capabilities, either of which may be absent: a keyword in a
  pull request body closes the item on merge in one system; another needs an explicit
  transition and no keyword; a third has no link at all and the item moves separately.
- **A write may be forbidden by policy rather than by capability.**

```yaml
tracker:
  policy:
    forbid_on_item: [source_code, credentials, hosting_details, file_paths, branch_names]
```

A tracker that is a third-party service holding someone else's material may bar these from ever
reaching a card. Where a fact is barred, it goes in the run report instead.

## 4. Work-item facets

### 4.1 Type

```yaml
work_item:
  type:
    carrier: native | label | none
    label_prefix: "type:"        # when carrier is label
    values: [bug, feature, task]
    absent_reason: "…"           # required when carrier is none
```

Native on one tracker, absent on another — a user-owned repository on one host has no issue
types at all. The procedure asks for "the type" without knowing which carrier answers.

```yaml
  type_branch_prefix:
    bug: bugfix
    feature: feature
```

The branch prefix is a **function of type**, and its range differs between projects — two
values in some, five in others, with one type resolving to one of two prefixes by a stated
test. A map, never a boolean.

### 4.2 Status — an ordered set of `(name, role, writer)`

```yaml
statuses:
  - { name: "…", role: initial,     writer: procedure }
  - { name: "…", role: in_flight,   writer: procedure }
  - { name: "…", role: code_landed, writer: automation }
  - { name: "…", role: deployed,    writer: deploy }
  - { name: "…", role: accepted,    writer: orderer }
  - { name: "…", role: terminal,    writer: deploy }
  - { name: "…", role: dropped,     writer: procedure }
```

Roles: `initial`, `ready`, `in_flight`, `code_landed`, `deployed`, `accepted`, `terminal`,
`dropped`. **A project maps a subset; an absent role is legitimate.** Vocabularies differ in
length and in meaning, not merely in wording.

⛔ **The writer is what makes this correct rather than merely configurable.** The procedure asks
the port to advance to a *role*, and is **refused** when the configured writer is not
`procedure`. Writers observed: `procedure`, `automation` (off a merge), `deploy`, `orderer` (the
person who ordered the work), `sweep` (a mechanical path-based test needing no judgement).

`writer: never` is supported and is the strictest real case: a project whose tracker credential
is a person's own account, where every write reads as that person speaking, so the procedure
writes nothing at all and reports instead.

### 4.3 Estimate

```yaml
work_item:
  estimate:
    carrier: field | label | card_value | none
    unit: points | hours
    values: [1, 2, 5, 8, 13]
    label_prefix: "E:"           # when carrier is label
    band: top                    # when each rung is the top of a band
    absent_reason: "…"           # required when carrier is none
    revisit_when: "…"
```

Four carriers observed, plus a deliberate absence. `carrier: none` with a stated reason is a
first-class setting; an unset carrier is a misconfiguration.

⛔ **One rule here is procedure, not configuration, and holds everywhere:** an estimate is a
bound written before the work, and a logged hour is a measurement written after. **Never move a
number between them in either direction** — an item re-sized to match the day is a time log
leaking onto the board, and an estimate copied into a log is a plan reported as work.

### 4.4 Template

```yaml
work_item:
  template:
    carrier: file | none
    dir: ".claude/templates"
    by_type: { bug: "…", feature: "…" }
    sections:                    # semantic name -> this template's own heading
      outcome: "…"
      acceptance: "…"
      reproduction: "…"
```

The procedure names the **semantic** sections it depends on — `outcome`, `acceptance`,
`reproduction` — and each template declares which of its own headings fills each. That keeps the
heading text, and its language, out of the procedure while letting the procedure still check a
section is present and tick its items later.

## 5. Readiness gate — an ordered predicate list

```yaml
readiness:
  - { check: state_is,          roles: [initial],  stop: "…" }
  - { check: no_open_blockers,                     stop: "…" }
  - { check: field_present,     field: "…",        stop: "…" }
  - { check: label_absent,      label: "…",        stop: "…" }
  - { check: ref_exists,        ref: "…",          stop: "…" }
  - { check: queue_position,    ahead_allowed: 0,  stop: "…" }
```

The copies this was reconciled from **share no single check**, so a fixed sequence would be
wrong for every project. Checks are drawn from a shared library: `state_is`, `no_open_blockers`,
`field_present`, `label_absent`, `ref_exists`, `queue_position`, `assignee_matches_role`.

- ⛔ **The list runs whole.** An item with four problems hears about four, rather than being
  bounced once per round trip.
- **A dependency's bar depends on what the dependency produced.** A code dependency is satisfied
  when its code is on the integration branch; a non-code dependency only when it is finished.
  Requiring the stronger bar of both stops every dependent item.

```yaml
    on_fail: flag | stop_quietly
```

- **Some failures are not defects.** An item that is correct and merely early, or one whose
  board automation did not fire, stops without being flagged. A gate that flags those flags an
  item whose author has nothing to fix.

## 6. Commit behaviour

```yaml
commit:
  staging: explicit | all
  trailer: none | read_from_history | "<literal trailer line>"
```

### Authorship is procedure, not configuration

⛔ **The only author is the code host's authenticated user.** That user is the author and the
committer. **No tool, assistant, model or generator is recorded as an author, a committer or a
co-author, and no generated-by marker appears in a commit message or a pull request body.** A
person who actually worked on the change may be credited; nothing else may.

This is not a per-project preference and there is no setting that turns it off. The reasons are
that attribution is a claim about who is answerable for a change, that a tool in the contributor
graph of every repository it touched is noise rather than provenance, and that the record of which
tool produced what belongs in the session transcript rather than in permanent history.

⚠️ **`trailer: read_from_history` is the trap.** It reads the signature *in use*, and history that
already carries a tool trailer will hand one straight back — which quietly reinstates the thing
this rule removes. Where history carries one, **it is not a signature**: treat `none` as the
answer and do not copy it forward.

⛔ **The rule binds what is written from now on, and nothing else. Existing history is left
alone.** A project adopting this will usually have a past full of tool trailers; that past stays as
it is. Rewriting it means a history rewrite and a force-push per repository, which breaks every
existing clone and defeats ancestry checks — a cost out of all proportion to tidying a contributor
graph. So the rule is **not** an invariant over history and must never be read as licence to
rewrite it. The only thing it asks of the past is that `read_from_history` not mistake it for a
signature.

- `staging` is the only part of this section that is configuration. **Two rules are shared
  regardless**, because every copy already carried them and only the default differed: the
  parallel-session exception (another session live, or status showing files this session never
  touched ⇒ stage explicit paths and name what was left alone), and the secret-and-client-material
  scan that stops rather than commits.
- **The message is written with repeated `-m`, one per paragraph.** No temporary file, so no race
  between two sessions; no heredoc, so no permission-allowlist accumulation; a trailer, where a
  project has a legitimate one, still parses as a final paragraph.
- **Concise by default, and history is not read for style cues.**
- **A dirty tree at start is not configured** — it follows from the branch model. Worktree mode
  reports it, states plainly that nothing was stashed or moved, and continues; in-place mode
  aborts.

### The pull request title and body

Like authorship, this is procedure rather than configuration — the per-project facts it reads are
already stated elsewhere: the repository (§1, §2), the closing capability (§3), the language and
register (§8).

- **The body is a summary and a test plan, and the plan is driven rather than published.**
- **The closing reference is whatever `link_for_close` (§3) says** — a keyword in the body on one
  tracker, a bracketed number in the title and never a hash on another, and legitimately absent on
  a third, where the item moves separately and neither title nor body carries a closing form.
- **Title and body are written in the repository's language and register (§8)** — which one
  project's split-by-audience rule makes different from its tracker's.
- **The authorship rule above binds the pull request as it binds the commit**: no generated-by
  marker, no tool credited.

**The reconciled shape of the summary and the test plan is transitional.** It still lives in the
five copies of the finishing role, and extracting that role moves the shape into its skill. The
rules above are the part already shared; nothing in a copy that contradicts them survives the
extraction.

## 7. Carrier

```yaml
carriers:
  day_log: skill             # skill | command | hook
  start: command
```

A role's carrier is an axis beside its name. One project's whole loop is slash commands rather
than skills, so a sweep of skill directories undercounts it by six roles. Configure the carrier
independently of the role, or a migration declares that project done with most of it still
local.

## 8. Language, register, audience — per artifact, not per project

```yaml
language:
  work_item: ru
  repo: en
  artifacts:
    day_log:   { language: en, register: business,  audience: "…" }
    deliverables: { language: ru, register: technical, audience: "…" }
```

One project writes its cards in one language and its repository in another and states the split
is by audience; its branch slug must be a **translation** of the item title, never a
transliteration. Another writes the day log in a technical register for itself where a third
writes it in a business register for someone outside the build. These are three settings, not
one.

## 9. Day log

```yaml
day_log:
  out_dir: "$TMPDIR/<project>"
  day_start: "05:00"
  round_to: 0.5
  round_ties: down | up
  enforce_grid: true
  script: "<path to the evidence script>"
  streams: [sessions, commits, telegram, meetings, host_activity]
  attribute_to: null
  exclusions: [contractual, other_projects, log_upkeep, rework, overhead]
  extra_exclusions:
    - { name: "…", rule: "…" }
  sections: billed_only | billed_and_not_billed
  evidence:
    chat_patterns: []
    chat_exclude: []
    mixed_chats: []
    calendars: []
```

- `round_to` and `enforce_grid` are **separate** settings. Three positions were observed: a half
  hour with the grid asserted, a half hour with ties going the other way, and one decimal with no
  grid assertion at all. The default is `0.5` with `round_ties: down` and `enforce_grid: true`.
- `exclusions` is an **ordered list of named exclusions** drawn from a shared library, which a
  project may extend through `extra_exclusions`. The default set above is a decision — the log
  measures delivered work, so rework and overhead leave the hours as well as the wording — not
  the only possible set.
- `attribute_to` is absent by default. Set it where the repository has more than one committer
  and the log is one person's: an author filter belongs in the script, never a subtraction by
  hand.
- `host_activity` is available only where the code host has an API for it. On a project whose
  review work happens almost entirely on the host and leaves no other trace, omitting it
  under-measures the day.

**`script` is transitional.** It points at the project's own evidence script for now, so the
procedure can be shared before the script is. Extracting the script into the plugin is the next
piece of this role; until then, `script` is how a project that has not been migrated keeps
working.

## 10. Invocation

Roles are addressed **namespaced, with no alias** — `/<plugin>:<role>`.

Procedure rather than configuration: there is no setting that turns it off. A project-level alias
would be one file per project per role, which reintroduces in miniature the duplication this
toolkit exists to delete. The namespace also makes a deliberate local override read as a
*different* name rather than the same one — which matters, because one role name in the original
copies denoted two unrelated roles.

⚠️ **A role's carrier changes the string the harness injects**, and anything matching on it
breaks silently: a command expands into a transcript record carrying its own title, a skill
injects a preamble naming its directory. A matcher that must key on one of those asserts both
directions, and §7 is the axis it reads.
