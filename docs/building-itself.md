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
carrier shipped in this repository's first commit, `6410f34` — so the earliest carrier of any of
the nine roles was never hand-built in this sense at all; it predates the loop it belongs to. It
is excluded here for the reason the `day_log.script` bullet below gives: the one role whose
carrier shipped first is the one role this project cannot run.

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

**In the order the surface states, not one this record chose.** Filing wrote the item, its label and
its relation; starting ran the readiness gate whole and took the claim by publishing the ref;
finishing took the branch to an open change; the reviewing role then conducted the review and drove
the gate; and the second finishing pass merged it and released the tree. That finishing is entered
twice with the review between its passes is
[`schema.md § The loop`](../plugins/mjolnir/config/schema.md#the-loop--nine-roles)'s, stated there
once.

⛔ **These carriers are not the loop.** Gating, deploying, session bookkeeping and producing
deliverables have no carrier in this project at all, and the day-log role has one it cannot run, for
the reason the `day_log.script` bullet below gives. The whole set is
[`schema.md § The loop`](../plugins/mjolnir/config/schema.md#the-loop--nine-roles)'s; what this
paragraph is for is that the instance above not be read as coverage of it.

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

## The absent facets this repository depends on

The surface's absent cases are argued for elsewhere; here they are load-bearing rather than
theoretical, which is a different kind of evidence than an example configuration can give.

- **`day_log.script` is unset on purpose.** The evidence script is not extracted
  ([#15](https://github.com/ragnor-rs/mjolnir/issues/15)) and this repository has no local copy to
  point at, so the day-log role resolves the project, reads the reader's `unavailable` list, reports
  that it cannot run and stops — rather than running a command with a null in it. The key is
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
[`schema.md § The loop`](../plugins/mjolnir/config/schema.md#the-loop--nine-roles), and a count
beside it here would drift the moment a role lands.
