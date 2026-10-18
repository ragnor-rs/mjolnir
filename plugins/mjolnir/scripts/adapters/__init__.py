"""The installed implementations of the tracker port, one module per `tracker.kind`.

A module in this package **is** an install (§ 3): the port discovers what is here
rather than being told, so a kind whose module is absent reports "the adapter has
not been built yet" without anybody maintaining a second list that could disagree
with the directory. Nothing is imported eagerly -- `port.load_adapters()` does it
on the first capability query, which is also what keeps the port from importing a
module that imports the port.

⛔ **The contract names no tracker; these modules are where a tracker's name is
allowed to appear.** `port.py` holds itself to naming none, in either spelling,
and that check is what makes this package the only place a branch on a particular
tracker can live.
"""
