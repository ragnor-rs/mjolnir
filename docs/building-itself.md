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
**#27's own start was run through it** rather than by hand, which is the one instance this record
can speak for.

Nothing in the tree records that distinction and no check holds it: whether a role was invoked or
performed by hand is a fact about a session's transcript rather than about the repository. So this
document claims it for no item, per
[`schema.md § 11`](../plugins/mjolnir/config/schema.md#a-report-names-what-it-could-not-establish) —
an unstated limit reads later as coverage.

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
