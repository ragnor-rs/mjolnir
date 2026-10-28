# Building itself with itself

[Work item #27](https://github.com/ragnor-rs/mjolnir/issues/27) asks this repository to run the loop
it ships, and requires every piece that could not be built that way to be named as hand-built. This
is that record.

It holds the part that stays true. **What the loop carries here today is derived rather than written
down** — the command is in the last section. A list of carriers in prose would be a second statement
of something the tree already answers, and it would be wrong the next time a role lands.

## The three pieces that could not use the loop

Each is something every role runs *through*, so no role could run before it existed. That is the
whole of the bootstrap — not three pieces picked for being difficult.

| piece | landed | why nothing could have carried it |
|---|---|---|
| the configuration reader | `d5b001a`, [#75](https://github.com/ragnor-rs/mjolnir/pull/75) | every role resolves its project through this one reader, so until it existed there was no configuration for a role to read |
| the `github-issues` adapter | `4cd0e39`, [#116](https://github.com/ragnor-rs/mjolnir/pull/116) | every tracker operation a role performs goes through the port, and this repository's own tracker had nothing registered behind it |
| the first carrier of the issue loop, its starting half | `e9e8e0f`, [#107](https://github.com/ragnor-rs/mjolnir/pull/107) | the role that starts a work item cannot be started by the role that starts a work item |

⚠️ **The third row names the *issue* loop, and the distinction is not cosmetic.** The day-log
carrier shipped in this repository's first commit, `6410f34` — so the earliest carrier of any role
of the loop was never hand-built in this sense at all; it predates the loop it belongs to. ⚠️ **It
also carried the longest absence**: its evidence script stayed each project's own while the
procedure was already shared, so the role resolved this project and stopped. That transition is
closed — the script is the plugin's, one copy, and every value it reads is configured.

The port those operations go through is
[`schema.md § 3`](../plugins/mjolnir/config/schema.md#3-tracker-port); the carrier each role is
addressed by is [`schema.md § 7`](../plugins/mjolnir/config/schema.md#7-carrier).

⚠️ **The order is the part worth knowing, because it was not the predicted one.** #27 was written
expecting the reader, then the adapter, then one loop skill, with everything after them going
through the loop. What happened instead: the reader, then a long run of surface and gate work by
hand, then the starting half as a project-local prototype, then the finishing and filing roles — and
the adapter, named second, landed *after* all three carriers of the issue loop already existed. So
the bootstrap is a
phase rather than a sequence of three, and the adapter is hand-built in the sense that mattered:
nothing could file, move or read an item through the port while the implementation behind it was
being written.

## A carrier that exists is not evidence that it ran

⚠️ Two different facts, and only the second one says a loop is running. A carrier can sit in the
tree while item after item is started by hand, and nothing in the tree would differ — the starting
half landed with [#107](https://github.com/ragnor-rs/mjolnir/pull/107) well before any of this.

Nothing in the tree records that distinction and no check holds it: whether a role was invoked or
performed by hand is a fact about a session's transcript rather than about the repository. So this
document speaks for the instances below and for no others, per
[`schema.md § 11`](../plugins/mjolnir/config/schema.md#a-report-names-what-it-could-not-establish) —
an unstated limit reads later as coverage.

### The one item the loop ran whole on

[#134](https://github.com/ragnor-rs/mjolnir/issues/134) (*"The loop has never run whole on a single
item, and the record claims it for none"*) went through the shipped carriers and through nothing
else, and it is closed by [#135](https://github.com/ragnor-rs/mjolnir/pull/135) (*"Record the one
item the loop ran whole on, and what it did not touch"*), which is the change this paragraph landed
in. It was filed for that purpose: [#27](https://github.com/ragnor-rs/mjolnir/issues/27) asks for
one such instance, and the only shape that satisfies a condition about an item traversing the loop
is an item that traverses it — which is why it is an item of its own rather than a line in #27.

**What ran.** Filing wrote the item, its label and its relation; starting ran the readiness gate
whole and took the claim by publishing the ref; finishing took the branch to an open change; the
reviewing role conducted the review and drove the gate; and a second finishing pass merged it.
⚠️ **The interleave is not this record's invention and not this run's choice** — that finishing is
entered twice with the review between its passes, and what the second pass owes beyond the merge, is
[`schema.md § The loop`](../plugins/mjolnir/config/schema.md#the-loop--ten-roles)'s, stated there
once.

⛔ **These carriers are not the loop, and this document does not say which ones are missing.** Which
roles this project carries is [`schema.md § 7`](../plugins/mjolnir/config/schema.md#7-carrier)'s
facet, and the command in the last section derives the set from it; naming the remainder here would
be a copy that goes stale the first time a carrier lands — the same prohibition that section already
carries, and one the README records as having drifted once already.

**Two capabilities were absent as it ran, and each took the fallback
[`§ 3`](../plugins/mjolnir/config/schema.md#the-operations-and-what-an-absent-capability-does)
states rather than being worked around.**

- `search_items` — ⚠️ absent from the plugin the session served rather than from this tracker. The
  implementation landed on #27's branch, which had not merged, and a plugin registered from a
  directory serves that directory's checked-out branch; so the filing role queried the capability,
  found it absent and asked before writing, which is exactly its stated fallback. The duplicate
  check is therefore reported as not performed by the role — the queries that *were* run came from
  the unmerged branch's own implementation and are named as separate evidence rather than as the
  role's check.
- `checklist_read` — absent because plain issues have no check-item object. The filing role
  therefore has no answer about #27's checklist, and the parent relation that governed #134's
  filing was established from #27's acceptance conditions in its body instead.

⚠️ **#27's own start was run through the starting role too**, on the same day and before #134
existed. It is a weaker instance than the one above and is recorded as such: one role, not the loop.

### The duplicate check, run against the live host

The `search_items` bullet above is why the filing role's duplicate check went **unperformed** as #134
ran. The implementation landed with [#136](https://github.com/ragnor-rs/mjolnir/pull/136), and the
check has since been run against the live host under
[#7](https://github.com/ragnor-rs/mjolnir/issues/7), the item that owns the filing role.

**It was run for a real request rather than as a rehearsal:** whether anything in this backlog
already owns *the reader does not hold `work_item.type.values`, `work_item.template.by_type` and
`work_item.type_branch_prefix` to each other*. The layers are the filing role's; the operation they
go through, in both the shapes this one needed, is
[`schema.md § 3`](../plugins/mjolnir/config/schema.md#the-operations-and-what-an-absent-capability-does)'s.

| layer | what was asked | what it reached |
|---|---|---|
| the keyword axes | 11 queries, over the surface, action, object and symptom axes | 75 distinct items |
| the keyword-independent sweep | 4 sweeps with no terms at all, each bounded at 100 and none at its bound | 87 distinct items |
| the two together | — | 21 items the sweep reached that no keyword query did |

**The outcome was no duplicate and nothing filed.** The governing candidate was
[#99](https://github.com/ragnor-rs/mjolnir/issues/99) (*"A tracker block missing the keys its kind
requires is accepted"*), tiered Medium: the same defect class — a configuration this reader accepts
and should refuse — carried on a different key, so doing it leaves the request with everything still
to do.

⚠️ **What this instance does not show**
([`schema.md § 11`](../plugins/mjolnir/config/schema.md#a-report-names-what-it-could-not-establish)).
The sweep is not what caught #99 — an action-axis query reached it as well — so this measures the
sweep *widening* coverage by 21 items, never the sweep being the only layer that could have found
the candidate that mattered. And the layers were driven through the port by hand under this item
rather than by the filing role being invoked — the distinction this section's opening draws, and the
weaker side of it.

### The cross-check that needed a configuration this repository does not have

The filing role holds an item's type against the template its body uses, and this repository carries
**neither** facet — both absent by decision, with the reasons the reader reports. So the mismatch
path had no configuration here to run against, and
[#114](https://github.com/ragnor-rs/mjolnir/pull/114) (*"File a work item from one copy, with the
duplicate search the richest copy had"*) recorded it as stated-but-unexercised when the role landed.

⚠️ **That turned out to be weaker than it read.** A probe skills root is enough: this project's own
configuration with the two facets swapped in — a type over two values, and a `file` template with
`by_type` and the `sections` map of
[`schema.md § 4.4`](../plugins/mjolnir/config/schema.md#44-template) — resolves with both facets
carried and neither in the reader's `unavailable` list. ⛔ **Nothing in this repository's own
configuration was changed to get there**, which is the point: a facet this project does not carry is
still exercisable, and the absent case stays the one that runs here.

One request body was typed twice, so a stop is attributable to the cross-check and to nothing else:
typed as the feature, whose template declares no reproduction, the body's reproduction section
put it against the defect template and the check **stopped**, naming both; typed as the defect, the
same body agreed with the template its type selects and the check **passed**. The probe's own prefix
map makes the consequence concrete rather than quoted — the two types take different prefixes, so
the unstopped run would have branched a defect under the feature's.

⚠️ **What this instance does not show either**
([`schema.md § 11`](../plugins/mjolnir/config/schema.md#a-report-names-what-it-could-not-establish)).
The write was never entered on the passing run — the probe's tracker block still addresses this
backlog and a probe does not write to it, so the cross-check being upstream of the write is why
nothing was lost, and this instance says nothing about filing. And it is the role's prose performed
and reported rather than a test asserting it.

## The absent facets this repository depends on

The surface's absent cases are argued for elsewhere; here they are load-bearing rather than
theoretical, which is a different kind of evidence than an example configuration can give.

- **`day_log.ritual_retired` is stated empty on purpose.** Every command name in this
  repository's own transcripts is either on the shared script's closed bookkeeping list or is
  work — the loop's roles, and this project's `close-out` and `adoption-readiness` — so nothing
  bookkeeping has been retired here. ⚠️ **Measured rather than assumed**, by reading the
  `<command-name>` tags out of the store, which is the only way that claim can be made. The
  reader names the emptiness, because the failure it guards is a total that is quietly *high*:
  a project whose history does carry a command it no longer has, and which says nothing, counts
  every one of those turns as work. The key is
  [`schema.md § 9`](../plugins/mjolnir/config/schema.md#9-day-log)'s.
- **This project's tracker has no `in_flight` status at all**, because plain issues are open or
  closed. So *an absent status role is legitimate* is not an assertion by the surface's author: it
  is a property the toolkit's own repository runs on, and
  [`schema.md § 4.2`](../plugins/mjolnir/config/schema.md#42-status--an-ordered-set-of-name-role-writer)
  is where the roles are stated.

## What the loop carries here, derived

```bash
python3 .claude/skills/adoption-readiness/scripts/readiness.py <this checkout>:github-issues \
  --adapter-item github-issues=27 --no-host
```

It reads the loop's size off the surface, then reports which roles the plugin ships, which ones this
project carries locally, and which of those are still unshipped — the target is an argument, so the
command above names this checkout rather than carrying a path.

⛔ No figure it prints is copied into this document. The loop is stated once, in
[`schema.md § The loop`](../plugins/mjolnir/config/schema.md#the-loop--ten-roles), and a count
beside it here would drift the moment a role lands.
