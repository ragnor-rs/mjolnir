#!/usr/bin/env python3
"""One read of the backlog, the relations and the ordering record, with the drift named.

Reports, in one pass: the live set and its tiers, the dependency relations, acyclicity, coverage of
the ordering record, ordering violations where the record states an order, the landed items the
record still places, the unblocked queue, and -- against the baseline the last completed pass
wrote -- what was filed, what landed, and which relations were added or removed since.

  close_out.py              read and report; the baseline is left alone
  close_out.py --stamp      same, then write the baseline as the new one
  close_out.py --queue      the takeable items and nothing else, in record order, one per line
  close_out.py --startable  which items MAY be started, from the tracker and the configuration
                            alone -- no record, no baseline. Not an ordering
  close_out.py --bootstrap  the one run that proceeds with no record: report the live state and
                            the relations' layers so an ordering can be drafted, and write nothing
  close_out.py --create     the grouping carrier's half of that: the grouping brought into
                            existence through the port, which is the one write about it

`--queue` is what a project's `ordering.command` (§ 12) names: that facet fixes the output -- the
takeable items, most takeable first, one identifier per line -- and leaves where the order came
from to whoever states it, which is `ordering.record` (§ 40).

⛔ **Every value is the configuration's and every read is the port's.** No tracker is named here, no
path is composed, and the record's own directory is resolved through the reader -- which is what
lets § 28's private layer answer it for a project that may not commit the value.

Exit 0 when nothing needs an edit, 1 when something does -- and 1 from `--bootstrap`, where the
ordering record itself is the edit the run is reporting.
"""

from __future__ import annotations

import argparse
import collections
import hashlib
import io
import json
import os
import re
import stat
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

import config as reader  # noqa: E402 -- the one reader of the surface and of every project
import port as ports  # noqa: E402 -- the one way to a tracker (§ 3)

# § 40's keys, spelled once each. ⛔ Read through the reader rather than out of the file, so a
# project that resolves `dir` from § 28's private layer is answered and one that cannot is refused
# with the key named -- which is the one place an absent layer can be reported to somebody who
# can fix it.
RECORD = "ordering.record"
CARRIER = f"{RECORD}.carrier"
GROUPING = f"{RECORD}.grouping"
DIR = f"{RECORD}.dir"
DOCUMENT = f"{RECORD}.document"

A_GROUPING, A_DOCUMENT, NOTHING = "grouping", "document", "none"

# The baseline's name, derived from the record rather than configured: § 40 states why there is no
# key for it, and the derivation is what makes the two impossible to point at different places.
BASELINE = ".ordering-baseline.json"

# § 4.2's role whose word means the item is off the backlog. The live set is what has not reached
# it, asked through the port because the mapping is the port's (§ 4.2).
TERMINAL = "terminal"

# The bound on one read of the backlog. ⛔ Carried rather than left to a tracker's own default,
# which cuts a long backlog short with nothing saying so, and the answer's own `at_limit` is
# reported: a set that exactly fills the bound is indistinguishable from one the bound cut.
BACKLOG_LIMIT = 1000

# The document carrier's grammar. ⛔ Procedure and not configuration, by § 40: a project that could
# reword it is a project whose ordering the shared role cannot read.
#
#   the row table opens at a header row whose first cell is `row`;
#   a row's label is an integer, and any other first cell is a retired row the parser skips;
#   the **issues cell** is the second one, and it alone places an item;
#   an item is a `#` and digits, and an arrow between two of them states their order.
ROW_HEADER = re.compile(r"^\|\s*row\s*\|", re.IGNORECASE)
AN_ITEM = re.compile(r"#(\d+)")
AN_ARROW = ("→", "->")


class Stop(Exception):
    """Something this pass reads did not answer, with the key or the operation named."""


# --- what the configuration says -------------------------------------------


def record_of(configuration) -> dict:
    """§ 40's record, resolved -- or the stop a project that states none produces.

    ⛔ **The directory is read under both carriers**, the baseline needing a place to stand
    whichever carrier the record itself is on, and a read that cannot be answered is a **stop with
    the key named** rather than a pass that measures no drift.
    """
    carrier = configuration.get(CARRIER)
    if carrier == NOTHING:
        raise Stop(
            f"`{CARRIER}` is `none`, so this project keeps no ordering record for this role to "
            "bring into agreement with its backlog. The project's own stated reason is: "
            f"{configuration.get(f'{RECORD}.absent_reason')!r} (§ 40)."
        )
    if carrier not in (A_GROUPING, A_DOCUMENT):
        raise Stop(
            f"`{CARRIER}` is {carrier!r}, which is not a carrier § 40 states. The reader refuses "
            "that where the configuration is read, so this pass is standing on a surface it does "
            "not recognise."
        )
    try:
        directory = configuration.get(DIR)
    except reader.ConfigError as error:
        raise Stop(
            f"`{DIR}` could not be resolved -- {error}. It carries § 28's `# private` mark, so a "
            "project that keeps the value outside its repository is answered from that layer and "
            "a machine without the layer is refused here rather than measured as having no drift."
        ) from error
    if not str(directory or "").strip():
        raise Stop(
            f"`{DIR}` is empty under `{CARRIER}: {carrier}`, so the baseline a pass measures "
            "drift against has nowhere to stand (§ 40)."
        )
    directory = os.path.expanduser(str(directory).strip())
    out = {"carrier": carrier, "dir": directory, "baseline": os.path.join(directory, BASELINE)}
    if carrier == A_DOCUMENT:
        name = str(configuration.get(DOCUMENT) or "").strip()
        if not name:
            raise Stop(f"`{DOCUMENT}` is empty under `{CARRIER}: {carrier}` (§ 40).")
        out["document"] = os.path.join(directory, name)
        out["names"] = name
    else:
        out["grouping"] = str(configuration.get(GROUPING) or "").strip()
        out["names"] = out["grouping"]
    return out


def directory_missing(record: dict) -> bool:
    """Whether the record's directory is absent -- and a stop where that cannot be established.

    ⛔ Asked by `stat` and not by `isdir`, which answers *no* for a directory behind a parent that
    cannot be read: an absence and a question nobody could ask have different remedies (§ 40).
    """
    try:
        held = os.stat(record["dir"])
    except FileNotFoundError:
        return True
    except OSError as error:
        raise Stop(
            f"`{DIR}` resolves to {record['dir']}, which could not be read -- {error}. Whether a "
            "record is there is unestablished (§ 40)."
        ) from error
    if not stat.S_ISDIR(held.st_mode):
        raise Stop(f"`{DIR}` resolves to {record['dir']}, which is not a directory (§ 40).")
    return False


def said_of_missing(record: dict) -> str:
    """The one wording of an absent directory, for the stop and for `--bootstrap` alike."""
    return (
        f"`{DIR}` resolves to {record['dir']}, and that directory is not there. The record and "
        "its baseline may exist elsewhere -- on another machine, under another account, or where "
        "the value pointed before -- so check the value first"
    )


def tiers_of(configuration) -> tuple[str | None, list[str]]:
    """§ 4.6's axis: (the label prefix where the tier is a label, the acceptable tiers).

    ⛔ Read and never written. An item outside the set is **named** and nothing here adds or raises
    a tier: a tier is importance and a place in the ordering is yield, which is § 40's own rule.
    ⚠️ The prefix is `None` where the carrier is not a label, and the tier is then read off the
    item's own field rather than off its labels.
    """
    values = [str(one) for one in (configuration.get("work_item.priority.values") or [])]
    if configuration.get("work_item.priority.carrier") != "label":
        return None, values
    prefix = str(configuration.get("work_item.priority.label_prefix") or "")
    return prefix, [f"{prefix}{value}" for value in values]


def tier_of(item: dict, prefix: str | None, field: str | None) -> str | None:
    """The tier one item carries, or `None` for an item carrying none.

    ⚠️ `None` is **unranked** rather than the lowest tier, which is § 4.6's own reading: an item
    outside the axis is a legitimate state, and a count that folded it into the bottom tier would
    report a backlog as ranked.
    """
    if prefix is not None:
        carried = [
            str(label.get("name") if isinstance(label, dict) else label)
            for label in (item.get("labels") or [])
        ]
        found = [one for one in carried if one.startswith(prefix)]
        return found[0] if found else None
    if field:
        value = (item.get("fields") or {}).get(field)
        return str(value) if value not in (None, "") else None
    return None


# --- what the tracker says -------------------------------------------------


def _answered(outcome, what: str):
    """One port outcome's result, or the stop its absence or its failure produces.

    ⛔ Three readings and never two (§ 3): an operation that **failed** is the host not answering,
    an operation whose capability is **absent** takes its stated fallback, and neither is an empty
    answer. A pass that folded either into *nothing there* would report a clean backlog.
    """
    if outcome.failed:
        raise Stop(f"{what} could not be read -- {outcome.detail}")
    if not outcome.performed:
        raise Stop(f"{what} cannot be asked of this tracker -- {outcome.detail}")
    return outcome.result


def backlog(tracker, *, limit: int = BACKLOG_LIMIT) -> dict:
    """Every item the tracker holds, placed against § 4.2's terminal role.

    ⛔ **Across every state**, which is `search_items`' own contract: an item that landed is what
    the coverage check needs in order to say a record still places it, so a read narrowed to the
    open ones would answer *nothing to retire* for a record holding every landing there has been.

    ⛔ **The live set is what is short of the terminal role**, asked through the port because the
    role-to-word mapping is the port's -- and ⚠️ **an item nobody could place is reported rather
    than counted either way**, which is § 2's absence-of-signal rule arriving in a count.
    """
    answer = _answered(tracker.invoke("search_items", limit=limit), "this project's backlog") or {}
    items = list(answer.get("items") or [])
    placed = tracker.short_of(TERMINAL, items)
    by_number = {}
    for item in items:
        number = item.get("number")
        if number is not None:
            by_number[int(number)] = item
    # ⛔ The identifier is the key the port's own report uses, not the one a tracker's answer
    # carries: `short_of` places items and names each by whichever identifier shape its
    # implementation answered with, under one key. A reader that took the tracker's field name
    # here placed every item and then found none of them -- the two halves of one read
    # disagreeing, with an empty live set as the symptom.
    live = sorted(int(one["item"]) for one in placed.get("short") or [] if one.get("item"))
    landed = sorted(
        int(one["item"])
        for one in placed.get("placed") or []
        if one.get("item") and int(one["item"]) not in set(live)
    )
    return {
        "items": by_number,
        "live": live,
        "landed": landed,
        "unplaced_state": placed.get("unanswered") or [],
        "at_limit": bool(answer.get("at_limit")),
        "limit": answer.get("limit", limit),
        "detail": placed.get("detail"),
    }


def relations(tracker, numbers: list[int]) -> tuple[list[tuple[int, int]], list[int]]:
    """Every `(blocker, dependent)` edge among `numbers`, and the items that could not be asked.

    ⛔ **Through `read_blockers`, item by item, and never off a tracker's own word for the
    relation** (§ 3). An adapter is free to answer more cheaply than one call per item; what this
    may not do is name the field.

    ⛔ **An item whose blockers could not be read is returned as unreadable rather than as an item
    with none.** A dependency nothing could be asked about reads exactly like no dependency, which
    is the one failure direction that matters in a graph.
    """
    edges: list[tuple[int, int]] = []
    unreadable: list[int] = []
    for number in numbers:
        outcome = tracker.invoke("read_blockers", str(number))
        if outcome.failed or not outcome.performed:
            unreadable.append(number)
            continue
        for blocker in (outcome.result or {}).get("blockers") or []:
            held = blocker.get("number")
            if held is not None:
                edges.append((int(held), number))
    return sorted(set(edges)), unreadable


def closed_by(tracker, number: int) -> dict:
    """The change that closed one item and the commit it landed as, or what went unread.

    ⚠️ A tracker that cannot be asked leaves the landed record naming the item and reporting the
    change **unread**, which is that operation's own stated fallback -- never *no change closed
    it*, and never the newest change on a branch.
    """
    outcome = tracker.invoke("read_closing_change", str(number))
    if outcome.failed or not outcome.performed:
        return {"number": number, "change": None, "commit": None, "unread": outcome.detail}
    answer = outcome.result or {}
    return {
        "number": number,
        "change": answer.get("change"),
        "commit": answer.get("commit"),
        "unread": None,
    }


# --- the relations, as constraints -----------------------------------------


def layers(live: list[int], edges: list[tuple[int, int]]) -> tuple[list[list[int]], list[int]]:
    """The relations' own constraints: (the layers, whatever no layer can take).

    Layer 1 is what nothing live blocks, and each later layer is what its own blockers all sit
    above. ⛔ **A layer is not a place in an ordering**: the order *inside* one is yield and
    nothing here derives it, which is § 40's rule on the write side.

    ⚠️ The second answer is acyclicity: whatever no layer can take is in or behind a cycle, which
    is exactly the set a topological pass cannot order.
    """
    blockers: dict[int, set[int]] = collections.defaultdict(set)
    live_set = set(live)
    for blocker, dependent in edges:
        if blocker in live_set and dependent in live_set:
            blockers[dependent].add(blocker)
    found: list[list[int]] = []
    settled: set[int] = set()
    left = set(live)
    while left:
        layer = sorted(one for one in left if not blockers[one] - settled)
        if not layer:
            break
        found.append(layer)
        settled |= set(layer)
        left -= set(layer)
    return found, sorted(left)


# --- the document carrier --------------------------------------------------


def rows_of(text: str) -> dict[int, tuple[str, list[int]]]:
    """`the row's label -> (its issues cell, the items that cell places)`.

    ⛔ **Only the issues cell places an item.** Naming one in the argument column places nothing,
    which is what keeps a row's reasoning free to mention an item it does not hold.
    ⛔ **A label that is not an integer is a retired row and is skipped**, which is how a row
    whose work has landed stays readable without still placing anything.
    """
    rows: dict[int, tuple[str, list[int]]] = {}
    inside = False
    for line in text.splitlines():
        if ROW_HEADER.match(line):
            inside = True
            continue
        if not inside:
            continue
        if not line.startswith("|"):
            break
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) < 2 or not cells[0].isdigit():
            continue
        rows[int(cells[0])] = (cells[1], [int(one) for one in AN_ITEM.findall(cells[1])])
    return rows


def same_place_order(cell: str, blocker: int, dependent: int) -> str:
    """How one cell states the order a same-place edge needs. Three readings:

    `stated`       -- the blocker is written first with an arrow between the two. Nothing to do.
    `reading`      -- the blocker is written first with no arrow, so the order is implied only.
                      ⛔ A notation gap and not an order: reading order states nothing.
    `contradicted` -- the dependent is written first, so the cell says the opposite of the graph.

    ⛔ **A cell naming only one of the two reads as `contradicted` as well**, which is stated
    because it is a fourth case folded into a third: the pair is same-place by the placements this
    same cell produced, so a cell that does not name both is one whose text and whose membership
    disagree -- and the permissive reading of that is an order nobody wrote.
    """
    first: dict[int, int] = {}
    for match in AN_ITEM.finditer(cell):
        first.setdefault(int(match.group(1)), match.start())
    if blocker not in first or dependent not in first:
        return "contradicted"
    low, high = first[blocker], first[dependent]
    if low > high:
        return "contradicted"
    between = cell[low:high]
    return "stated" if any(arrow in between for arrow in AN_ARROW) else "reading"


# --- the grouping carrier --------------------------------------------------


def grouping_places(tracker, record: dict, value: str | None) -> dict[int, tuple[str, list[int]]]:
    """The one grouping's membership, in the same shape a row table resolves to.

    ⛔ One place and not several: § 40's `grouping` names *the* grouping the order is kept in, so
    coverage here asks whether an item is in it rather than which of many it is in.

    ⛔ **The grouping's own value arrives on this role's invocation**, which is § 4.8's `current`
    rule and not a choice here: the tracker's own mark for the open one is read by the filing role
    alone, so that holds under either value of that key. ⚠️ A pass given none is a **stop naming
    what it needs**, never a pass over whichever grouping the tracker happened to answer with --
    an order read off the wrong time box is the one wrong answer that looks right.
    """
    if not str(value or "").strip():
        raise Stop(
            f"this project keeps its order of work in the grouping {record['grouping']!r}, and "
            "which grouping -- which time box, which release -- arrives on this role's "
            "invocation: under either value of § 4.8's `current` this role reads no tracker's "
            "mark for it. Name it with `--in <value>`."
        )
    answer = _answered(
        tracker.items_in(record["grouping"], str(value).strip()),
        f"the items in the grouping {record['grouping']!r}",
    ) or {}
    held = [
        int(one["number"])
        for one in answer.get("items") or []
        if one.get("number") is not None
    ]
    return {0: (str(answer.get("value") or record["grouping"]), sorted(held))}


def places_of(tracker, record: dict, value: str | None = None
              ) -> tuple[dict[int, tuple[str, list[int]]], str | None]:
    """`(the places, what could not be read)` -- one shape for both carriers.

    ⛔ **The carrier decides, and the pass that reads the answer does not branch again.** What
    differs between a row table and a grouping is where the membership comes from; everything after
    this -- coverage, the order, the landed record, the drift -- is the same reading.
    """
    if record["carrier"] == A_GROUPING:
        return grouping_places(tracker, record, value), None
    try:
        with open(record["document"], encoding="utf-8") as handle:
            return rows_of(handle.read()), None
    except FileNotFoundError:
        return {}, (
            f"no {record['names']} in {record['dir']} -- the ordering record for this project "
            "does not exist yet, so there is nothing holding the backlog and the relations to each "
            "other. Draft it with `--bootstrap` (§ 40)."
        )
    except OSError as error:
        return {}, f"{record['document']} could not be read -- {error}"


def states_an_order(record: dict) -> bool:
    """Whether the record's places are ordered with respect to one another.

    ⛔ **A row table does and a grouping does not**, and that is § 4.8's shape rather than a
    limitation chosen here: a grouping is a set an item is planned into and the surface states no
    order between two of them, so *a blocker placed later than its dependent* is a question only
    the document carrier can be asked. ⚠️ Reported as unavailable rather than answered, which is
    § 11's rule: a check with nothing to compare is not a check that passed.
    """
    return record["carrier"] == A_DOCUMENT


# --- the baseline ----------------------------------------------------------


def digest_of(path: str) -> str | None:
    try:
        with open(path, "rb") as handle:
            return hashlib.sha256(handle.read()).hexdigest()[:12]
    except OSError:
        return None


def read_baseline(path: str) -> dict | None:
    try:
        with open(path, encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, ValueError):
        return None


def write_baseline(path: str, state: dict) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(state, handle, indent=1, sort_keys=True)
        handle.write("\n")


# --- the readings a pass reports -------------------------------------------


def report_tiers(configuration, items: dict, live: list[int]) -> list[tuple[int, str]]:
    """The tiers, counted and never inferred. Returns the items outside the stated set."""
    prefix, acceptable = tiers_of(configuration)
    field = configuration.get("work_item.priority.field") if prefix is None else None
    counted: collections.Counter = collections.Counter()
    outside, unranked = [], []
    for number in live:
        tier = tier_of(items.get(number) or {}, prefix, field)
        counted[tier or "unranked"] += 1
        if tier is None:
            unranked.append(number)
        elif tier not in acceptable:
            outside.append((number, tier))
    print("  tiers              : " + ", ".join(
        f"{name} {count}" for name, count in sorted(counted.items())))
    # ⚠️ *Unranked* and never *none*: § 4.6 reads an item carrying no value as outside the axis
    # rather than at the bottom of it, so a count labelled one way beside a line labelled the
    # other reads as two different figures.
    print(f"  unranked           : {unranked}  (a legitimate state)")
    if outside:
        print(
            f"  ⛔ OUTSIDE {', '.join(acceptable) or 'the stated set'}: "
            + ", ".join(f"#{number} {tier}" for number, tier in outside)
            + "   — ask; never add or raise a tier to close the gap"
        )
    return outside


def report_relations(items: dict, live: list[int], edges, unreadable, baseline, tested):
    """The relations, acyclicity, and the items whose require-not-tolerate test is unrun."""
    live_edges = [(b, n) for b, n in edges if b in set(live) and n in set(live)]
    print(f"relations            : {len(edges)}   live (blocker still live): {len(live_edges)}")
    if unreadable:
        print(f"  ⛔ UNREADABLE       : {unreadable}  — asked and not answered, never read as none")
    strata, behind = layers(live, edges)
    print("acyclic              : "
          + ("YES" if not behind else f"NO — {len(behind)} item(s) in or behind a cycle"))
    if behind:
        print(f"  IN OR BEHIND CYCLE : {behind}")
    # Edge-free is a legitimate and common state, so what is flagged is scoped to what is new: an
    # item filed since the baseline with no relation either way is the one whose test is unrun.
    touched = {one for pair in edges for one in pair}
    isolated = [one for one in live if one not in touched]
    if baseline is None:
        print(f"  isolated (no edge) : {len(isolated)}  — scoped to new filings once a baseline exists")
        fresh = []
    else:
        fresh = [one for one in isolated if one not in baseline and one not in tested]
        print(f"  isolated (no edge) : {len(isolated)}, of them filed since the last pass: "
              + (f"{fresh}  — apply the require-not-tolerate test to each, then say the answer"
                 if fresh else "none"))
    return strata, behind, isolated, fresh


def _placement(places: dict) -> dict[int, list[int]]:
    """`the item -> every place that holds it`, which is coverage read item-first."""
    found: dict[int, list[int]] = collections.defaultdict(list)
    for label, (_cell, numbers) in places.items():
        for number in numbers:
            found[number].append(label)
    return found


def report_coverage(tracker, record, places, live, landed):
    """Every live item placed exactly once, and every landed item the record still places."""
    placement = _placement(places)
    unplaced = [one for one in live if one not in placement]
    twice = {one: where for one, where in placement.items() if len(where) > 1}
    still = sorted(one for one in placement if one not in set(live) and one in set(landed))
    print(f"placed               : {len(live) - len(unplaced)}/{len(live)}")
    if unplaced:
        print(f"  UNPLACED           : {unplaced}  — place each into a place the record already has")
    if twice:
        print(f"  PLACED TWICE       : {twice}")
    for number in still:
        landing = closed_by(tracker, number)
        where = placement[number][0]
        others = [one for one in places[where][1] if one != number and one in set(live)]
        said = (
            f"closed by #{landing['change']} `{(landing['commit'] or '')[:7]}`"
            if landing["change"] is not None else
            f"its closing change went unread — {landing['unread'] or 'the tracker holds none'}"
        )
        print(f"  LANDED, still placed: #{number} in {record['carrier']} place {where} — {said}")
        if others:
            print(f"      shared with {others} → take #{number} out of the membership, keeping the "
                  "place's own argument as the record of what it cost")
        else:
            print(f"      the only item in its place → retire the place, keeping its argument")
    return placement, unplaced, twice, still


def report_order(record, places, placement, live, edges):
    """A blocker placed after its dependent, and a same-place edge the record does not order."""
    if not states_an_order(record):
        print("ordering violations  : unavailable — the record is a grouping, and the surface "
              "states no order between two of them (§ 4.8, § 40)")
        return [], {}
    violations, same = [], []
    live_set = set(live)
    for blocker, dependent in edges:
        if blocker not in live_set or dependent not in live_set:
            continue
        where_b, where_n = placement.get(blocker), placement.get(dependent)
        if not where_b or not where_n:
            continue
        if min(where_b) > min(where_n):
            violations.append((blocker, min(where_b), dependent, min(where_n)))
        elif min(where_b) == min(where_n):
            same.append((blocker, dependent, min(where_b)))
    print(f"ordering violations  : {len(violations)}")
    for blocker, at_b, dependent, at_n in sorted(violations):
        print(f"  VIOLATION          : #{blocker} (row {at_b}) blocks #{dependent} (row {at_n})")
    readings: dict[str, list] = collections.defaultdict(list)
    for blocker, dependent, where in same:
        readings[same_place_order(places[where][0], blocker, dependent)].append(
            (blocker, dependent, where))
    print(f"same-place edges     : {len(same)}  "
          + ", ".join(f"{name} {len(found)}" for name, found in sorted(readings.items())))
    for blocker, dependent, where in sorted(readings["contradicted"]):
        print(f"  ⛔ CELL CONTRADICTS : row {where}: #{blocker} blocks #{dependent}, and the cell "
              f"writes #{dependent} first")
    for blocker, dependent, where in sorted(readings["reading"]):
        print(f"  arrow absent       : row {where}: #{blocker} → #{dependent}, order implied by "
              "reading order only")
    return violations, readings


def report_drift(record, baseline, state, live, edges):
    """What was filed, what landed, and which relations moved -- the one reading no query answers.

    ⛔ **Measured against a baseline a pass wrote, and never against a modification time**: no
    tracker bumps an item's own when a relation changes, so a query keyed on one cannot see an edge
    that was added or removed. ⚠️ That is the whole reason the baseline exists.
    """
    if baseline is None:
        print("\nsince last pass      : no baseline yet — run with --stamp to write the first one")
        return
    was_live = set(baseline.get("live") or [])
    was_edges = {tuple(edge) for edge in baseline.get("edges") or []}
    now_edges = set(edges)
    print(f"\nsince {baseline.get('at', 'the last pass')} (the baseline the last stamped pass wrote):")
    shown = lambda found: ", ".join(f"#{b}→#{n}" for b, n in sorted(found)) or "none"
    gone = was_edges - now_edges
    print(f"  filed              : {sorted(set(live) - was_live) or 'none'}")
    print(f"  no longer live     : {sorted(was_live - set(live)) or 'none'}")
    print(f"  relations added    : {shown(now_edges - was_edges)}")
    # An edge also disappears when its dependent leaves the live set; that is the item landing
    # rather than a relation anybody removed, and only the first list is a graph edit to account
    # for.
    print(f"  relations removed  : {shown(one for one in gone if one[1] in set(live))}")
    print(f"  edges off with a landing: {shown(one for one in gone if one[1] not in set(live))}")
    # ⛔ Another session's residue, reported as the placements that moved and never repaired
    # (§ 40). ⚠️ **Whose it is cannot be established from the record**, and that is stated rather
    # than guessed: neither a document outside version control nor a grouping a tracker holds
    # carries an author, so what is nameable is *which* placements changed under this pass and not
    # who changed them. Naming a session would be a fabricated attestation.
    was_places = {int(one): set(where) for one, where in (baseline.get("places") or {}).items()}
    now_places = {int(one): set(where) for one, where in (state.get("places") or {}).items()}
    moved = sorted(
        one for one in set(was_places) | set(now_places)
        if was_places.get(one, set()) != now_places.get(one, set())
    )
    if moved:
        print(f"  placements moved   : {moved}  — ⛔ another pass's edits: report them and leave "
              "them alone. The record carries no author, so whose they are is unestablished")
    if record["carrier"] == A_DOCUMENT:
        was = baseline.get("record_sha")
        if was not in (None, state.get("record_sha")):
            print("  ⚠️ the record changed since that pass — another session's edit, whose it is "
                  "unestablished. ⛔ Re-read before editing, and repair nothing (§ 40)")


# --- the modes -------------------------------------------------------------


def startable(configuration, tracker) -> int:
    """Which items MAY be started, from the tracker and § 4.6 alone.

    ⛔ **Not an ordering, and the output says so.** What this answers is the *may* question --
    every live item all of whose blockers have left the live set -- grouped by the tier § 4.6
    carries. Which of them to take next is § 12's answer, and § 40's record is where the argument
    for that order lives. ⚠️ **It reads no record and no baseline**, which is what makes it the one
    mode that answers for a project whose record does not exist yet.
    """
    held = backlog(tracker)
    edges, unreadable = relations(tracker, held["live"])
    live = set(held["live"])
    blocked = {n for b, n in edges if b in live}
    ready = [one for one in held["live"] if one not in blocked]
    prefix, acceptable = tiers_of(configuration)
    field = configuration.get("work_item.priority.field") if prefix is None else None
    by_tier: dict[str | None, list[int]] = collections.defaultdict(list)
    for number in ready:
        by_tier[tier_of(held["items"].get(number) or {}, prefix, field)].append(number)
    print(f"tracker              : {configuration.get('tracker.kind')}   "
          "(the port, and nothing outside this project's configuration)")
    print(f"startable now        : {len(ready)} of {len(held['live'])} live — every blocker landed")
    if held["at_limit"]:
        print(f"  ⚠️ AT THE BOUND     : the read filled its bound of {held['limit']}, so this "
              "answer may be short")
    if unreadable:
        print(f"  ⛔ UNREADABLE       : {unreadable}  — blockers asked for and not answered")

    def show(label: str, numbers: list[int], note: str = "") -> None:
        for number in numbers:
            title = str((held["items"].get(number) or {}).get("title") or "")
            print(f"  {label:<14}  #{number}  {title[:58]}{note}")

    for tier in acceptable:
        show(tier, sorted(by_tier.get(tier, [])))
    for tier in sorted(one for one in by_tier if one is not None and one not in acceptable):
        show("⛔ " + tier, sorted(by_tier[tier]), "   — a tier the facet does not carry")
    # Last, and never folded into the lowest tier: § 4.6 reads an item carrying no value as
    # unranked, so the order this prints in is arrival and not rank.
    show("unranked", sorted(by_tier.get(None, [])))
    print("\n⚠️ which items MAY be started. Which to take next is the ordering facet's answer "
          "(§ 12), read from the record § 40 states.")
    return 1 if any(
        one is not None and one not in acceptable for one in by_tier
    ) or unreadable else 0


def bootstrap(configuration, tracker, record) -> int:
    """The one run that proceeds with no record: what an ordering would have to order.

    ⛔ **Writes nothing.** Under the document carrier the ordering is drafted, summarised and
    written once the person running the role has approved it; under the grouping carrier the
    grouping is created through the port. Either way a place in the ordering is **yield**, which
    nothing derives, so a run that wrote one would be ordering the work on this toolkit's own
    judgement (§ 12, § 40).
    """
    if directory_missing(record):
        print(f"⚠️ DIRECTORY MISSING : {said_of_missing(record)}. Where this is the project's "
              "first ordering, the directory is created with the record (§ 40).\n")
    held = backlog(tracker)
    edges, unreadable = relations(tracker, held["live"])
    print(f"record               : {record['carrier']} — {record['names']}")
    if record["carrier"] == A_DOCUMENT:
        print(f"  to be written at   : {record['document']}")
    else:
        print("  to be created      : with `--create --in <value>`, which is the port's own "
              "`create_grouping` and nowhere else")
    print(f"live items           : {len(held['live'])}")
    if held["at_limit"]:
        print(f"  ⚠️ AT THE BOUND     : the read filled its bound of {held['limit']}")
    report_tiers(configuration, held["items"], held["live"])
    strata, behind, _isolated, _fresh = report_relations(
        held["items"], held["live"], edges, unreadable, None, set())
    print(f"\nlayers               : {len(strata)}  — the relations' own constraints; "
          "⛔ a layer is not a place, and the order inside one is yield to argue")
    blockers: dict[int, set[int]] = collections.defaultdict(set)
    for blocker, dependent in edges:
        blockers[dependent].add(blocker)
    for rank, layer in enumerate(strata, 1):
        print(f"  layer {rank} ({len(layer)} item{'s' if len(layer) != 1 else ''})")
        for number in layer:
            held_by = sorted(blockers[number] & set(held["live"]))
            behind_it = ("← " + ", ".join(f"#{one}" for one in held_by) + "  ") if held_by else ""
            title = str((held["items"].get(number) or {}).get("title") or "")
            print(f"      #{number}  {behind_it}{title[:60]}")
    if behind:
        print(f"  unorderable        : {behind}  — break the cycle before placing any of them")
    print("\n⛔ nothing written. Summarise this, and bring the record into existence only once the "
          "person running this has approved the ordering.")
    return 1


def create(configuration, tracker, record, value: str | None) -> int:
    """The grouping carrier's half of bringing an ordering into existence (§ 40).

    ⛔ **A write through the port and nowhere else.** A grouping the tracker does not hold is one
    no `grouping_items` can read, so a record kept anywhere but the tracker would be an ordering
    the next pass cannot find -- which is why § 40 states this act as the port's.

    ⚠️ **No approval of its own**, which is § 40's own division: what carries an approval is
    *writing an order of work*, and a grouping is a named set. What goes into it is the role's
    ordinary pass.
    """
    if record["carrier"] != A_GROUPING:
        raise Stop(
            f"`--create` brings one of § 4.8's groupings into existence, and this project's record "
            f"is a {record['carrier']}. A document is written by the role once the person running "
            "it has approved the ordering, which is `--bootstrap` and then the write (§ 40)."
        )
    if not str(value or "").strip():
        raise Stop("`--create` needs the grouping's own value: name it with `--in <value>`.")
    answer = _answered(
        tracker.create_in(record["grouping"], str(value).strip()),
        f"the grouping {record['grouping']!r}",
    ) or {}
    print(f"record               : {record['carrier']} — {record['names']}")
    print(f"  value              : {answer.get('value')}")
    # ⚠️ Said apart, because the two are different facts: one this call made, and one it found.
    # A report that said *created* for both would claim a write that did not happen.
    print("  created            : "
          + ("yes" if answer.get("created") else "no — the tracker already held it"))
    print("\n⛔ nothing is in it yet. The ordinary pass is what places items, and a place in the "
          "ordering is yield (§ 40).")
    return 0


def pass_over(configuration, tracker, record, *, stamp: bool, tested: set[int],
              value: str | None = None, quiet: bool = False) -> tuple[int, list[int]]:
    """One read of the backlog, the relations and the record. Returns (the exit, the queue)."""
    # ⛔ Before either carrier's record is read: an absent directory is an absent *baseline* on
    # both, and a pass that went ahead would report no drift for want of anything to compare.
    if directory_missing(record):
        raise Stop(
            f"{said_of_missing(record)}. Where this is the project's first ordering, run "
            "`--bootstrap` and then create the directory (§ 40)."
        )
    places, unread = places_of(tracker, record, value)
    if unread is not None:
        raise Stop(unread)
    held = backlog(tracker)
    edges, unreadable = relations(tracker, held["live"])
    baseline = read_baseline(record["baseline"])
    state = {
        "live": held["live"],
        "edges": [list(edge) for edge in edges],
        # Where each item was placed, so a pass can say **which** placements moved under it.
        # ⛔ Carried because the record has no author: a file outside version control and a
        # grouping a tracker holds neither say who edited them, so what another session's residue
        # can be reported *as* is the placements that changed -- never a name.
        "places": {str(one): sorted(where) for one, where in _placement(places).items()},
        "record_sha": digest_of(record.get("document", "")) if record["carrier"] == A_DOCUMENT
        else None,
    }
    known = set(baseline.get("live") or []) if baseline else None
    settled = set(baseline.get("tested") or []) if baseline else set()
    settled |= tested
    carried = (baseline or {}).get("carried") or {}
    if known is not None:
        # Anything a stamped pass left unresolved stays *new* for the checks scoped to new
        # filings, or stamping over a residue would hide it from every later run.
        known -= (set(carried.get("unplaced") or []) | set(carried.get("isolated") or [])) - settled

    print(f"record               : {record['carrier']} — {record['names']}")
    if record["carrier"] == A_DOCUMENT:
        print(f"  at                 : {record['document']}  sha {state['record_sha']}")
    print(f"live items           : {len(held['live'])}")
    if held["at_limit"]:
        print(f"  ⚠️ AT THE BOUND     : the read filled its bound of {held['limit']}, so every "
              "figure below may be short")
    if held["unplaced_state"]:
        print(f"  ⛔ UNPLACED STATE   : {held['unplaced_state']}  — items no status here maps, "
              "counted as neither live nor landed")
    outside = report_tiers(configuration, held["items"], held["live"])
    _strata, behind, isolated, fresh = report_relations(
        held["items"], held["live"], edges, unreadable, known, settled)
    placement, unplaced, twice, still = report_coverage(
        tracker, record, places, held["live"], held["landed"])
    violations, readings = report_order(record, places, placement, held["live"], edges)
    report_drift(record, baseline, state, held["live"], edges)

    # Printed in the record's own order, because that order is the whole answer to *which item is
    # next* and the starting role reads this as its queue. An item with no place has no order to be
    # read in, so it sorts and prints last rather than ahead of the first place.
    def place_of(number: int):
        where = placement.get(number)
        return min(where) if where else None

    live_set = set(held["live"])
    blocked = {n for b, n in edges if b in live_set}
    ready = sorted(
        (one for one in held["live"] if one not in blocked),
        key=lambda one: (place_of(one) is None, place_of(one) or 0, one),
    )
    if not quiet:
        print(f"\nunblocked now        : {len(ready)}")
        for number in ready:
            where = place_of(number)
            title = str((held["items"].get(number) or {}).get("title") or "")
            print(f"  place {'—' if where is None else where!s:>3}  #{number}  {title[:66]}")

    dirty = bool(
        unplaced or twice or still or violations or behind or outside or unreadable
        # ⚠️ Read with a default, because the grouping carrier returns no readings at all: the
        # order is unavailable there, and an index into an empty answer would make a pass over
        # that carrier die where its verdict belongs.
        or readings.get("contradicted") or held["unplaced_state"]
    )
    residue = sorted(
        (set(carried.get("unplaced") or []) | set(carried.get("isolated") or []))
        & (set(unplaced) | set(isolated)) - settled
    )
    if residue and not quiet:
        print(f"\ncarried unresolved   : {residue}  — flagged by an earlier pass and still open")
    # ⛔ Said outright rather than left to be read off the figures: a pass with nothing to change
    # is the ordinary outcome, and a report that only ever lists problems leaves *no problems* and
    # *a pass that stopped early* reading alike (§ 11). ⚠️ It states what the pass found and never
    # that the ordering is right -- which is yield, and nobody's but the person's to judge.
    if not dirty and not quiet:
        print("\nnothing to change    : the live set, the tiers, the relations and the record "
              "agree. ⛔ Nothing written, this line included")
    if stamp:
        state.update({
            "at": "stamped",
            "clean": not dirty,
            # Residue left behind, so a stamp cannot bury it: these stay *new* next run.
            "carried": {"unplaced": unplaced, "isolated": fresh},
            "tested": sorted(settled & live_set),
        })
        write_baseline(record["baseline"], state)
        if not quiet:
            print(f"\nbaseline written     : {record['baseline']}"
                  + ("  ⚠️ written while not clean" if dirty else ""))
    return (1 if dirty else 0), ready


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--root", default=".", help="the skills root; defaults to the working one")
    parser.add_argument("--in", dest="value", default="",
                        help="the grouping's own value where the record is a grouping — which "
                             "time box, which release. § 4.8's `current` is read by nothing in "
                             "the procedure, so this arrives here under either of its values")
    parser.add_argument("--stamp", action="store_true",
                        help="write the baseline as the new one after reporting")
    parser.add_argument("--tested", default="",
                        help="the items whose require-versus-tolerate test was run and answered "
                             "'no edge'; recorded on --stamp so they stop being re-flagged")
    parser.add_argument("--queue", action="store_true",
                        help="print the takeable items in the record's order, one per line, and "
                             "nothing else")
    parser.add_argument("--startable", action="store_true",
                        help="which items MAY be started, from the tracker and the priority facet "
                             "alone — no record is read, and this is not an ordering")
    parser.add_argument("--bootstrap", action="store_true",
                        help="report the live state and the relations' layers for a project whose "
                             "record does not exist yet, and write nothing")
    parser.add_argument("--create", action="store_true",
                        help="bring the grouping the record names into existence, through the "
                             "port — the grouping carrier's half of the bootstrap")
    parser.add_argument("--self-test", action="store_true", help="this module's own suite")
    args = parser.parse_args(argv)
    if args.self_test:
        return self_test()
    tested = {int(one) for one in re.findall(r"\d+", args.tested)}
    try:
        configuration = reader.load(args.root, check_paths=False)
    except (reader.ConfigError, OSError) as error:
        print(f"the reader refused this project -- {error}", file=sys.stderr)
        return 2
    tracker = ports.Port(configuration, ports.port_spec())
    try:
        if args.startable:
            # ⛔ Before the record is resolved, which is the whole of what this mode is for: the
            # *may* question is answered by the tracker and § 4.6, so a project whose record does
            # not exist yet must not be a refusal here.
            # ⛔ `--create` is in this list because it is a **write**: every other mode refuses the
            # flags that have nothing to act on, and the one flag left out of this guard was the
            # one whose omission is silent -- a pass asked to bring a grouping into existence
            # reported a startable set, exited 0 and created nothing.
            if args.stamp or args.tested or args.queue or args.bootstrap or args.create:
                raise Stop("--startable answers from the tracker alone and writes nothing, so "
                           "--stamp, --tested, --queue, --bootstrap and --create have nothing to "
                           "act on")
            return startable(configuration, tracker)
        record = record_of(configuration)
        # ⚠️ On the error stream, so `--queue`'s output stays the items and nothing else.
        stale = configuration.harness_derived_directories().get(DIR)
        if stale:
            print(f"⚠️ {stale}", file=sys.stderr)
        if args.create:
            if args.stamp or args.tested or args.queue or args.bootstrap:
                raise Stop("--create makes one write about the grouping and reads no record, so "
                           "--stamp, --tested, --queue and --bootstrap have nothing to act on")
            return create(configuration, tracker, record, args.value)
        if args.bootstrap:
            if args.stamp or args.tested or args.queue:
                raise Stop("--bootstrap writes nothing, so --stamp, --tested and --queue have "
                           "nothing to act on here")
            places, unread = places_of(tracker, record, args.value)
            # ⛔ **An ordering exists where the record places something, which is one reading for
            # both carriers and never a branch here.** A row table that is not there resolves to no
            # places at all, but a grouping always resolves to its own single place -- empty or not
            # -- so a test on the places themselves refused **every** bootstrap on that carrier,
            # telling a project whose ordering does not exist yet that it already orders its
            # backlog. ⚠️ A place that holds nothing is not an order of work: it is the set this
            # mode exists to report the layers of.
            if unread is None and any(held for _cell, held in places.values()):
                raise Stop(
                    f"this project already orders its backlog in {record['names']!r}, and "
                    "nothing here overwrites one. Run without --bootstrap (§ 40)."
                )
            return bootstrap(configuration, tracker, record)
        if args.queue:
            if args.stamp or args.tested:
                raise Stop("--queue reports a queue and writes nothing, so --stamp and --tested "
                           "have nothing to act on here")
            # ⛔ Refused where the record states no order between its places, rather than printed
            # from whatever order the items happened to come back in. § 12's contract is *most
            # takeable first*, and a queue this mode could not justify would be this toolkit
            # ordering the work on its own judgement -- which is the one judgement § 12 says is
            # never the toolkit's. ⚠️ A project whose record is a grouping states its own
            # `ordering.command` against its tracker's rank; this mode is not it.
            if not states_an_order(record):
                raise Stop(
                    f"this project keeps its order of work in the grouping {record['names']!r}, "
                    "and § 4.8 states no order between two groupings — so there is no queue for "
                    "this mode to read out. What `ordering.command` names on such a project is a "
                    "command against the tracker's own rank (§ 12, § 40)."
                )
            # The report is suppressed rather than made conditional on a flag threaded through
            # every print: a consumer reading this as data gets the items and nothing else, and a
            # second printing path would be a second answer to one question.
            #
            # ⚠️ The pass's own verdict is deliberately not carried out of this mode. A run exits 1
            # on drift, and a consumer asking *which item is next* has no use for that: the queue
            # it was handed is correct either way, and a non-zero exit would read as *there is no
            # queue*. What the exit answers here is whether the queue could be produced, which is
            # what § 12 says a consumer reads.
            # ⛔ The stream that was there is what is put back, never `sys.__stdout__`: a caller
            # that had already redirected this -- a suite, a role capturing a run -- would
            # otherwise have its own capture replaced by the process's original, and the queue
            # would print somewhere nobody is reading.
            held, standing = io.StringIO(), sys.stdout
            try:
                sys.stdout = held
                _exit, ready = pass_over(
                    configuration, tracker, record, stamp=False, tested=tested,
                    value=args.value, quiet=True)
            finally:
                sys.stdout = standing
            for number in ready:
                print(number)
            return 0
        exit_code, _ready = pass_over(
            configuration, tracker, record, stamp=args.stamp, tested=tested, value=args.value)
        return exit_code
    except Stop as stop:
        print(f"stopped: {stop}", file=sys.stderr)
        return 2


def self_test() -> int:
    """This module's suite, which lives in the module beside it."""
    from _close_out_suite import self_test as suite  # noqa: PLC0415 -- imported where it is run
    return suite()


if __name__ == "__main__":
    sys.exit(main())
