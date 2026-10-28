"""The installed implementations of the day log's destination port.

One module per `day_log.destination.kind`. A module here states a `KIND` and an
`ADAPTER` and **is** an install; the rule and its reasoning are
[`schema.md § 3`](../../config/schema.md#the-trackerless-adapter-and-a-kind-with-no-implementation),
which [`§ 26`](../../config/schema.md#26-the-day-logs-destination-port) holds this
port to rather than restating -- and this package points at rather than copying.

Two things true of this directory and stated nowhere else:

  * ⛔ **A store's own vocabulary belongs here and nowhere else in the toolkit.**
    A file name, a cell reference, a worklog endpoint: the contract beside this
    package reads an operation list and a fallback off the surface and knows no
    store by name, and the day-log role names the port rather than a path. This
    package is the exemption that makes those two keepable. ⚠️ **Held by reading
    and not by a check**, unlike the tracker half: that sweep reddens on a kind
    word the surface states, and this port's kinds are ordinary English -- `file`
    is in `__file__` and in every sentence about a file. The limit is stated here
    rather than left for somebody to find out by trusting it.
  * ⚠️ **Which port a module answers for is which directory it sits in**, and
    there is deliberately no `PORT` name in a module here. A declaration would be
    a second statement of a fact the directory already carries, and the one way it
    could be wrong -- a module answering for the port it is not filed under -- is
    the way nothing could catch.

⚠️ **Importing the contract from here is a cycle, broken by when rather than by
whether**, exactly as in the sibling package: a module here imports the port for
`Adapter`, and the port imports this package during discovery, so discovery is
deferred to the first capability query.
"""
