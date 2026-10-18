"""The installed implementations of the tracker port, one module per `tracker.kind`.

A module here states a `KIND` and an `ADAPTER` and **is** an install; the rule
and its reasoning are
[`schema.md § 3`](../../config/schema.md#3-tracker-port), which this package
points at rather than restating.

Two things true of this directory and stated nowhere else:

  * ⛔ **A tracker's name belongs here and nowhere else in the toolkit.** The
    contract holds itself to naming none, in either spelling, and its self-test
    fails on a branch that does. This package is the exemption that makes the
    rule keepable.
  * ⚠️ **Importing the contract from here is a cycle, broken by when rather
    than by whether.** A module in this package imports the port for `Adapter`,
    and the port imports this package during discovery -- so discovery is
    deferred to the first capability query. Under `port.py --self-test` the
    contract runs as `__main__` and `import port` loads it a second time, which
    means `port.ADAPTERS` and `__main__.ADAPTERS` are different objects. Nothing
    reads the registry by module name today; anything that starts to must call
    `port.load_adapters()` rather than read `port.ADAPTERS`, which is the one
    place this has already gone wrong.
"""
