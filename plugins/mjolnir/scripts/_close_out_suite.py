#!/usr/bin/env python3
"""What the closing-out role decides, held beside it.

⛔ **Every reading is driven through the port and over a real example**, not over a configuration
written here: a hand-built fixture is a second configuration, free to disagree with every one this
toolkit ships -- which is the contract suite's own rule, taken for the same reason.

⛔ **The tracker is a fake and not a mock.** It answers by *what was asked for* and records every
call, so the two properties that matter can be asserted as facts about the calls rather than as
expectations: that a pass finding nothing to change **writes nothing**, and that the role **never
writes a tier**.

⚠️ **The failure directions here are the quiet ones.** A dependency nothing could be asked about
reads exactly like no dependency; a landed item whose closing change went unread reads exactly like
one nothing closed; a grouping with no order between its places reads exactly like an ordering with
no violations. Each of those has a case of its own below, and each asserts the *reported* reading
rather than the absence of a crash.
"""

from __future__ import annotations

import io
import json
import os
import sys
import tempfile

_SCRIPTS = os.path.dirname(os.path.abspath(__file__))
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

import close_out  # noqa: E402
import config  # noqa: E402
import port  # noqa: E402

# The example every fixture starts from: the one that states § 40's `document` carrier, since that
# is the carrier whose grammar there is anything to parse. ⛔ Resolved by the carrier it states
# rather than by filename, so renaming an example does not silently take this suite off it.
A_PLACE, ANOTHER_PLACE = 1, 2

# The items the fixtures are written over. ⛔ Distinct integers throughout, and a blocker numbered
# above its dependent in one pair: a fixture whose numbers rose with its places would pass an
# implementation that compared numbers instead of places.
FIRST, SECOND, THIRD, LANDED = 11, 12, 13, 9

A_CHANGE, A_COMMIT = 40, "abcdef1234"


def _an_example_stating(carrier: str) -> str:
    for name in sorted(os.listdir(config.EXAMPLES)):
        if not name.endswith((".yaml", ".yml")):
            continue
        with open(os.path.join(config.EXAMPLES, name), encoding="utf-8") as handle:
            text = handle.read()
        loaded = config.load_text(text, config.EXAMPLES)
        if loaded.get(close_out.CARRIER) == carrier:
            return name
    raise AssertionError(f"no shipped example states `{close_out.CARRIER}: {carrier}`")


def _configuration(carrier: str, directory: str, **more) -> config.Config:
    name = _an_example_stating(carrier)
    with open(os.path.join(config.EXAMPLES, name), encoding="utf-8") as handle:
        loaded = config.load_text(handle.read(), config.EXAMPLES)
    record = loaded.data.setdefault("ordering", {}).setdefault("record", {})
    record["dir"] = directory
    for key, value in more.items():
        record[key] = value
    return loaded


class _Tracker:
    """A tracker that answers as the port's operations do, and records what was asked.

    `absent` names the operations whose capability this one does not have, which is how the stated
    fallback is reached without building a second adapter.
    """

    def __init__(self, items, blockers=None, closing=None, held=None, absent=()):
        self.items = list(items)
        self.blockers = dict(blockers or {})
        self.closing = dict(closing or {})
        self.held = list(held or [])
        self.absent = set(absent)
        self.asked: list[tuple] = []
        self.wrote: list[tuple] = []

    def _operations(self) -> dict:
        every = {
            "search_items": self._search,
            "read_blockers": self._read_blockers,
            "read_closing_change": self._closing,
            "grouping_items": self._grouping_items,
            "create_grouping": self._create_grouping,
            "set_labels": self._set_labels,
            "set_field": self._set_field,
        }
        return {name: call for name, call in every.items() if name not in self.absent}

    def port(self, configuration) -> port.Port:
        return port.Port(configuration, port.port_spec(), adapter=port.Adapter(self._operations()))

    # -- the reads

    def _search(self, terms=None, *, labels=None, limit=100):
        self.asked.append(("search_items", limit))
        return {"terms": terms, "labels": labels or [], "limit": limit,
                "at_limit": len(self.items) >= limit, "items": self.items}

    def _read_blockers(self, number):
        self.asked.append(("read_blockers", int(number)))
        return {"number": int(number),
                "blockers": [{"number": one, "state": "open"}
                             for one in self.blockers.get(int(number), [])]}

    def _closing(self, number):
        self.asked.append(("read_closing_change", int(number)))
        answer = self.closing.get(int(number)) or {}
        return {"number": int(number), "state": "closed",
                "change": answer.get("change"), "commit": answer.get("commit"),
                "merged": answer.get("change") is not None, "references": []}

    def _grouping_items(self, value, *, grouping):
        self.asked.append(("grouping_items", value))
        return {"grouping": (grouping or {}).get("name"), "value": value,
                "items": [one for one in self.items if one["number"] in self.held]}

    # -- the writes, recorded so a pass that makes one can be caught

    def _create_grouping(self, value, *, grouping):
        self.wrote.append(("create_grouping", value))
        return {"value": value, "created": True, "already": False}

    def _set_labels(self, number, labels):
        self.wrote.append(("set_labels", int(number), list(labels)))
        return {"number": int(number)}

    def _set_field(self, number, **kwargs):
        self.wrote.append(("set_field", int(number), kwargs))
        return {"number": int(number)}


def _items_of(configuration):
    """An item factory carrying *this example's* own status words (§ 4.2).

    ⛔ **Derived and never written here**, and that is a measured requirement rather than
    tidiness: the live set is what the port places short of the terminal role, so a fixture
    carrying a word the example does not map produces an empty live set and every reading below it
    then passes over nothing. ⚠️ Measured exactly that way -- the two carriers are shown by two
    examples whose status vocabularies differ, and a literal that fitted one emptied the other.
    """
    statuses = [one for one in (configuration.get("statuses") or []) if isinstance(one, dict)]
    live_word = next(one["name"] for one in statuses if one.get("role") == "initial")
    landed_word = next(one["name"] for one in statuses if one.get("role") == "terminal")

    def item(number: int, *, landed: bool = False, tier: str | None = None):
        return {
            "number": number,
            "title": f"an item, #{number}",
            "state": landed_word if landed else live_word,
            "labels": ([{"name": tier}] if tier else []),
            "url": f"https://e.invalid/an-owner/a-name/issues/{number}",
        }

    return item


def _a_record(path: str, rows: list[tuple[str, str]]) -> None:
    """An ordering document carrying one row table, written as a project writes one."""
    lines = [
        "# The order of work",
        "",
        "| row | issues | why |",
        "|---|---|---|",
    ]
    for label, cell in rows:
        lines.append(f"| {label} | {cell} | because |")
    with open(path, "w", encoding="utf-8") as handle:
        handle.write("\n".join(lines) + "\n")


def _ran(configuration, tracker, argv: list[str]) -> tuple[int, str]:
    """One run of the role's own entry point, with what it printed."""
    held, errors = io.StringIO(), io.StringIO()
    opened = tracker.port(configuration)
    real_load, real_port = close_out.reader.load, close_out.ports.Port
    close_out.reader.load = lambda *a, **k: configuration
    close_out.ports.Port = lambda *a, **k: opened
    try:
        sys.stdout, sys.stderr = held, errors
        code = close_out.main(argv)
    finally:
        sys.stdout, sys.stderr = sys.__stdout__, sys.__stderr__
        close_out.reader.load, close_out.ports.Port = real_load, real_port
    return code, held.getvalue() + errors.getvalue()


def self_test() -> int:  # noqa: PLR0915 -- one suite, read top to bottom
    failures = 0

    def check(label: str, condition: bool, detail: str = "") -> None:
        nonlocal failures
        if condition:
            print(f"  ok    {label}")
        else:
            failures += 1
            print(f"  FAIL  {label}{': ' + detail if detail else ''}")

    # --- the document carrier's grammar, which is procedure (§ 40) ------------
    #
    # ⛔ Only the issues cell places an item, and a label that is not an integer is a retired row.
    # Both arms in one table, because a parser that read the argument column would place items the
    # table deliberately only mentions.
    rows = close_out.rows_of(
        "| row | issues | why |\n|---|---|---|\n"
        f"| 1 | **#{FIRST}** → #{SECOND} | and #{THIRD} is mentioned here |\n"
        f"| — | **#{LANDED}** | ✅ landed |\n"
        f"| 2 | #{THIRD} | because |\n"
    )
    check(
        "the issues cell places an item and the argument column places none",
        sorted(rows) == [1, 2]
        and rows[1][1] == [FIRST, SECOND]
        and rows[2][1] == [THIRD],
        f"read {rows!r}",
    )
    check(
        "a label that is not an integer is a retired place and holds nothing",
        LANDED not in {one for _cell, held in rows.values() for one in held},
        f"read {rows!r}",
    )
    # ⛔ Three readings of a same-place edge and never two: reading order states nothing, so an
    # implementation that accepted it would report a notation gap as an order.
    for label, cell, expected in (
        ("an arrow between the two", f"#{FIRST} → #{SECOND}", "stated"),
        ("reading order alone", f"#{FIRST}, #{SECOND}", "reading"),
        ("the dependent written first", f"#{SECOND} → #{FIRST}", "contradicted"),
        ("one of the two absent", f"#{FIRST} alone", "contradicted"),
    ):
        check(
            f"a same-place edge with {label} reads as `{expected}`",
            close_out.same_place_order(cell, FIRST, SECOND) == expected,
            f"read {close_out.same_place_order(cell, FIRST, SECOND)!r}",
        )

    with tempfile.TemporaryDirectory() as store:
        configuration = _configuration(close_out.A_DOCUMENT, store, document="the-order.md")
        record = close_out.record_of(configuration)
        document, baseline = record["document"], record["baseline"]
        # ⛔ Derived and never configured, which is § 40's reason: the two cannot be pointed at
        # different places, and a pass that found no drift because they were is the failure.
        check(
            "the baseline is derived beside the record rather than configured",
            os.path.dirname(baseline) == os.path.dirname(document)
            and baseline.endswith(close_out.BASELINE),
            f"{baseline!r} beside {document!r}",
        )

        tier = str(configuration.get("work_item.priority.label_prefix")) + str(
            (configuration.get("work_item.priority.values") or ["top"])[0])
        an_item = _items_of(configuration)
        live = [an_item(FIRST, tier=tier), an_item(SECOND),
                an_item(THIRD, tier=f"{configuration.get('work_item.priority.label_prefix')}invented")]
        landed = an_item(LANDED, landed=True)

        # --- a pass with nothing to change writes nothing -------------------
        _a_record(document, [("1", f"**#{FIRST}** → #{SECOND}"), ("2", f"#{THIRD}")])
        before = open(document, encoding="utf-8").read()
        tracker = _Tracker([*live, landed], blockers={SECOND: [FIRST]})
        code, said = _ran(configuration, tracker, [])
        check(
            "a pass writes nothing: no baseline unless it is asked for, and the record untouched",
            not os.path.exists(baseline)
            and open(document, encoding="utf-8").read() == before,
            f"baseline {os.path.exists(baseline)}",
        )
        # ⛔ The ordinary outcome is **said**, not left to be read off the figures: a report that
        # only ever lists problems leaves *nothing wrong* and *a pass that stopped early* reading
        # alike. ⚠️ This fixture has a tier outside the stated set in it, so the clean arm is
        # asserted below on a backlog that carries none.
        clean = _Tracker([an_item(FIRST), an_item(SECOND)], blockers={SECOND: [FIRST]})
        _a_record(document, [("1", f"**#{FIRST}** → #{SECOND}")])
        code, quiet = _ran(configuration, clean, [])
        check(
            "a pass with nothing to change says so, and exits 0",
            code == 0 and "nothing to change" in quiet,
            f"exit {code}: {quiet}",
        )
        _a_record(document, [("1", f"**#{FIRST}** → #{SECOND}"), ("2", f"#{THIRD}")])
        # ⛔ The tier arm: an item outside the stated set is **named** and no tier is written. The
        # second half is a fact about the calls, which is the only form that holds it.
        check(
            "an item outside the stated tiers is named, and no tier is written",
            f"#{THIRD} priority:invented" in said
            and not [one for one in tracker.wrote if one[0] in ("set_labels", "set_field")],
            f"wrote {tracker.wrote!r}\n{said}",
        )
        check(
            "an item carrying no tier is counted as unranked rather than as the lowest",
            f"unranked           : [{SECOND}]" in said,
            said,
        )
        # ⛔ The landed record: the closing change and its commit, read through the port.
        check(
            "a landed item the record still places is named with its closing change",
            f"LANDED, still placed: #{LANDED}" not in said,
            "a landed item nothing places was reported as placed",
        )

        # --- coverage: unplaced, placed twice, landed-but-placed -------------
        _a_record(document, [
            ("1", f"**#{FIRST}** → #{SECOND}, #{LANDED}"),
            ("2", f"#{SECOND}"),
        ])
        tracker = _Tracker(
            [*live, landed],
            blockers={SECOND: [FIRST]},
            closing={LANDED: {"change": A_CHANGE, "commit": A_COMMIT}},
        )
        code, said = _ran(configuration, tracker, [])
        check(
            "an unplaced live item, an item placed twice and a landed item still placed are each named",
            f"UNPLACED           : [{THIRD}]" in said
            and f"PLACED TWICE       : {{{SECOND}: [1, 2]}}" in said
            and f"LANDED, still placed: #{LANDED}" in said
            and f"closed by #{A_CHANGE} `{A_COMMIT[:7]}`" in said,
            said,
        )
        check("and the pass reports that something needs an edit", code == 1, f"exit {code}")
        # ⛔ A tracker that cannot be asked what closed an item reports the change **unread** and
        # never *nothing closed it*, which is the quiet reading § 3's fallback exists for.
        unreadable = _Tracker(
            [*live, landed], blockers={SECOND: [FIRST]}, absent=("read_closing_change",))
        _code, said = _ran(configuration, unreadable, [])
        check(
            "a closing change that cannot be asked for is reported unread, not as none",
            "went unread" in said and "closed by #" not in said,
            said,
        )

        # --- the order, and the violation a record can state ----------------
        _a_record(document, [("1", f"#{SECOND}"), ("2", f"#{FIRST}, #{THIRD}")])
        tracker = _Tracker([*live], blockers={SECOND: [FIRST]})
        _code, said = _ran(configuration, tracker, [])
        check(
            "a blocker placed after its dependent is reported as a violation",
            f"VIOLATION          : #{FIRST} (row 2) blocks #{SECOND} (row 1)" in said,
            said,
        )
        _a_record(document, [("1", f"#{SECOND}, #{FIRST}")])
        tracker = _Tracker([*live], blockers={SECOND: [FIRST]})
        _code, said = _ran(configuration, tracker, [])
        check(
            "a same-place edge whose cell writes the dependent first is reported as contradicted",
            "CELL CONTRADICTS" in said,
            said,
        )

        # --- a dependency nothing could be asked about ----------------------
        _a_record(document, [("1", f"**#{FIRST}** → #{SECOND}"), ("2", f"#{THIRD}")])
        blind = _Tracker([*live], absent=("read_blockers",))
        _code, said = _ran(configuration, blind, [])
        check(
            "an item whose blockers could not be read is reported unreadable, never as having none",
            "UNREADABLE" in said and str(FIRST) in said,
            said,
        )

        # --- the drift, measured against a baseline and no modification time -
        tracker = _Tracker([*live], blockers={SECOND: [FIRST]})
        _code, _said = _ran(configuration, tracker, ["--stamp"])
        check("--stamp writes the baseline", os.path.exists(baseline))
        stamped = json.load(open(baseline, encoding="utf-8"))
        check(
            "the baseline holds the live set and the edges, which is what drift is read from",
            stamped.get("live") == sorted([FIRST, SECOND, THIRD])
            and [FIRST, SECOND] in [list(one) for one in stamped.get("edges") or []],
            json.dumps(stamped),
        )
        # An edge added and an edge removed between two passes, with no item's own modification
        # time involved anywhere: the fake carries none, so an implementation that consulted one
        # could not have answered at all.
        moved = _Tracker([*live], blockers={THIRD: [SECOND]})
        _code, said = _ran(configuration, moved, [])
        check(
            "a relation added and a relation removed since the baseline are both reported",
            f"relations added    : #{SECOND}→#{THIRD}" in said
            and f"relations removed  : #{FIRST}→#{SECOND}" in said,
            said,
        )
        # ⛔ The record changing under the pass is another session's residue: reported, with the
        # remedy named, and never repaired here.
        _a_record(document, [("1", f"**#{FIRST}** → #{SECOND}"), ("2", f"#{THIRD}, #{SECOND}")])
        _code, said = _ran(configuration, _Tracker([*live], blockers={SECOND: [FIRST]}), [])
        check(
            "a record that changed since the baseline is reported as another session's edit",
            "another session's edit" in said and "repair nothing" in said,
            said,
        )
        # ⛔ And the residue is reported as the placements that **moved**, with whose it is stated
        # as unestablished rather than guessed: neither carrier's record holds an author, so a
        # name here would be a fabricated attestation.
        check(
            "the placements another pass moved are named, and whose they are is unestablished",
            f"placements moved   : [{SECOND}]" in said
            and "whose they are is unestablished" in said
            and "leave them alone" in said,
            said,
        )

        # --- the queue, which is what § 12's command reads -------------------
        _a_record(document, [("1", f"#{SECOND}"), ("2", f"#{FIRST}, #{THIRD}")])
        tracker = _Tracker([*live], blockers={SECOND: [FIRST]})
        code, said = _ran(configuration, tracker, ["--queue"])
        check(
            "--queue prints the takeable items in the record's order and nothing else",
            said.split() == [str(FIRST), str(THIRD)],
            repr(said),
        )
        # ⚠️ The pass's own verdict is deliberately not carried out of this mode: that run has an
        # ordering violation in it, and a non-zero exit would read as *there is no queue*.
        check("and exits 0 even where the pass itself found something to edit", code == 0,
              f"exit {code}")

        # --- the bootstrap, and the record it must not overwrite -------------
        code, said = _ran(configuration, _Tracker([*live]), ["--bootstrap"])
        check(
            "--bootstrap on a project that already orders its backlog is refused by name",
            code == 2 and "already orders its backlog" in said,
            f"exit {code}: {said}",
        )
        os.remove(document)
        tracker = _Tracker([*live], blockers={SECOND: [FIRST], THIRD: [SECOND]})
        code, said = _ran(configuration, tracker, ["--bootstrap"])
        check(
            "--bootstrap with no record reports the layers, writes nothing, and says so",
            code == 1
            and "layers               : 3" in said
            and "nothing written" in said
            and not os.path.exists(document)
            and not tracker.wrote,
            f"exit {code}, wrote {tracker.wrote!r}:\n{said}",
        )
        # ⛔ And a pass over a record that is not there is a stop naming it, rather than a pass
        # over an empty ordering -- which would report every item unplaced and nothing wrong.
        code, said = _ran(configuration, _Tracker([*live]), [])
        check(
            "a pass with no record at all stops and names it",
            code == 2 and "does not exist yet" in said,
            f"exit {code}: {said}",
        )
        # ⛔ `--create` is the grouping carrier's half and is refused on a document, naming the
        # act that writes one instead: a create that fell through to a file would be this carrier
        # bringing a record into existence with nobody's approval.
        made = _Tracker([*live])
        code, said = _ran(configuration, made, ["--create", "--in", "anything"])
        check(
            "--create on a document record is refused, naming the act that writes one",
            code == 2 and "approved the ordering" in said and not made.wrote,
            f"exit {code}, wrote {made.wrote!r}: {said}",
        )

    # --- the grouping carrier ------------------------------------------------
    with tempfile.TemporaryDirectory() as store:
        configuration = _configuration(close_out.A_GROUPING, store)
        record = close_out.record_of(configuration)
        check(
            "the grouping carrier still names a directory, which is the baseline's",
            record["dir"] == store and "document" not in record,
            f"resolved {record!r}",
        )
        an_item = _items_of(configuration)
        live = [an_item(FIRST), an_item(SECOND), an_item(THIRD)]
        # ⛔ A pass given no value for the grouping is a **stop naming what it needs**: § 4.8's
        # `current` is read by nothing in the procedure, so a pass that went ahead would be
        # reading the order off whichever grouping the tracker answered with.
        code, said = _ran(configuration, _Tracker(live), [])
        check(
            "a grouping-carried record asked for with no value is a stop naming what it needs",
            code == 2 and "--in <value>" in said,
            f"exit {code}: {said}",
        )
        A_VALUE = "a time box"
        tracker = _Tracker(live, blockers={SECOND: [FIRST]}, held=[FIRST, SECOND])
        _code, said = _ran(configuration, tracker, ["--in", A_VALUE])
        check(
            "the value handed over is the one the port is asked with, not one composed here",
            ("grouping_items", A_VALUE) in tracker.asked,
            f"asked {tracker.asked!r}",
        )
        check(
            "coverage on the grouping carrier reads the grouping's membership through the port",
            any(one[0] == "grouping_items" for one in tracker.asked),
            f"asked {tracker.asked!r}",
        )
        check(
            "an item the grouping does not hold is reported unplaced",
            f"UNPLACED           : [{THIRD}]" in said,
            said,
        )
        # ⛔ The quiet reading this carrier would otherwise give: § 4.8 states no order between two
        # groupings, so *no violations* would be a check that never ran. Reported unavailable.
        check(
            "ordering violations on the grouping carrier are reported unavailable, not as zero",
            "ordering violations  : unavailable" in said
            and "ordering violations  : 0" not in said,
            said,
        )
        # ⛔ And the same absence refuses `--queue` rather than printing an order this mode cannot
        # justify: § 12's contract is *most takeable first*, and a queue read off a set with no
        # order in it would be the toolkit ordering the work on its own judgement.
        code, said = _ran(configuration, _Tracker(live, held=[FIRST]), ["--queue", "--in", A_VALUE])
        check(
            "--queue is refused where the record states no order between its places",
            code == 2 and "no queue for this mode to read out" in said,
            f"exit {code}: {said}",
        )
        # ⛔ The create is a **write through the port** and the report says which of the two
        # happened: one this call made, or one it found. A report saying *created* for both would
        # claim a write that did not happen.
        making = _Tracker(live)
        code, said = _ran(configuration, making, ["--create", "--in", A_VALUE])
        check(
            "--create brings the grouping into existence through the port, and says it did",
            code == 0
            and ("create_grouping", A_VALUE) in making.wrote
            and "created            : yes" in said,
            f"exit {code}, wrote {making.wrote!r}: {said}",
        )
        code, said = _ran(configuration, _Tracker(live), ["--create"])
        check(
            "--create with no value for the grouping is a stop naming what it needs",
            code == 2 and "--in <value>" in said,
            f"exit {code}: {said}",
        )

    # --- `--startable`, which reads no record at all -------------------------
    with tempfile.TemporaryDirectory() as store:
        configuration = _configuration(close_out.A_DOCUMENT, store, document="absent.md")
        an_item = _items_of(configuration)
        tracker = _Tracker(
            [an_item(FIRST), an_item(SECOND)], blockers={SECOND: [FIRST]})
        code, said = _ran(configuration, tracker, ["--startable"])
        check(
            "--startable answers with no record present, and says it is not an ordering",
            f"#{FIRST}" in said and f"#{SECOND}" not in said
            and "which items MAY be started" in said,
            f"exit {code}: {said}",
        )

    if failures:
        print(f"\n{failures} assertion(s) did not hold.")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(self_test())
