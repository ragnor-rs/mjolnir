"""The installed implementations of the host's run operations port.

One module per `host.runs.kind`. A module here states a `KIND` and an `ADAPTER`
and **is** an install; the rule and its reasoning are
[`schema.md § 3`](../../config/schema.md#the-trackerless-adapter-and-a-kind-with-no-implementation),
which [`§ 29`](../../config/schema.md#29-the-hosts-run-operations) holds this port
to rather than restating -- and this package points at rather than copying.

Three things true of this directory and stated nowhere else:

  * ⛔ **A host client's own vocabulary belongs here and nowhere else in the
    toolkit.** A subcommand, a dispatch flag, the shape of a run listing, the
    field a step count is read out of: the contract beside this package reads an
    operation list and a fallback off the surface and knows no host by name, and
    the roles that drive a run name the port rather than a client. This package
    is the exemption that makes those two keepable -- and it is the exemption the
    sweep in `tools/` was taught to leave alone while forbidding the same call
    under `skills/` and in a hook.
  * ⛔ **§ 29 states that every operation but the dispatch writes nothing, and
    this package is where that is held.** A module here routes every call through
    one place that says whether it writes, and its own suite asserts that a
    listing, a conclusion and a log make no writing call while the dispatch makes
    one. An implementation is where a property of what a call declares about
    itself can be shown at all.
  * ⚠️ **Which port a module answers for is which directory it sits in**, and
    there is deliberately no `PORT` name in a module here -- the sibling packages'
    rule, for the reason they state: a declaration would be a second statement of
    what the directory already carries, and the one way it could be wrong is the
    way nothing could catch.

⚠️ **Importing the contract from here is a cycle, broken by when rather than by
whether**, exactly as in the sibling packages: a module here imports the port for
`Adapter`, and the port imports this package during discovery, so discovery is
deferred to the first capability query.
"""
