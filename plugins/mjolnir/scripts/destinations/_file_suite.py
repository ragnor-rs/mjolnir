#!/usr/bin/env python3
"""The file destination's own decisions, held against a real directory.

What the contract's suite holds is the contract -- the operation list, the absent
case, a kind of `none`. This holds what the implementation beside it decided, and
each of those is reachable only by writing files: the path § 9 fixed, a rebuild
that leaves one entry, a hand-edited entry reported rather than counted as
nothing, a period read per day, and the two directories that are refused.

⛔ **Every write lands in a temporary directory the suite makes and removes**, and
the configuration is built over it. Nothing here touches the project's own store:
an entry written beside a real one would be a day this repository's own log claims
and nobody worked.

⚠️ **The port is what every call goes through**, never the module's functions
directly. The adapter resolves no project for itself, so a direct call would
bypass the one place a configuration is bound -- and the suite would be exercising
a path no role takes.

Usage:
    _file_suite.py    hold the file destination to its own decisions
"""

from __future__ import annotations

import os
import sys
import tempfile

_SCRIPTS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _SCRIPTS not in sys.path:
    sys.path.append(_SCRIPTS)

import config  # noqa: E402
import port  # noqa: E402
from destinations import file as implementation  # noqa: E402

# The port this suite drives. ⚠️ Written out, which a suite may do about the thing
# it is a suite for -- what is read off the surface is the port's *section*, its
# operation list and its prefix, every one of them through `port.port_spec` below.
PORT = "day_log.destination.kind"

# Two days far enough apart that a range can exclude one. ⚠️ Fixed rather than
# taken from the clock: a suite whose fixture is today is a suite whose failures
# depend on when it ran.
A_DAY = "2026-03-04"
NEXT_DAY = "2026-03-05"
A_LATER_DAY = "2026-04-01"


def _configuration(out_dir: str, root: str, more: dict | None = None) -> config.Config:
    """A whole example, pointed at a temporary directory and a temporary root.

    Taken from the examples rather than written here, for the reason the
    contract's own suite gives: a fixture written by hand is a second
    configuration, free to disagree with every one this toolkit ships.
    """
    name = sorted(
        entry for entry in os.listdir(config.EXAMPLES) if entry.endswith((".yaml", ".yml"))
    )[0]
    with open(os.path.join(config.EXAMPLES, name), encoding="utf-8") as handle:
        loaded = config.load_text(handle.read(), config.EXAMPLES)
    spec = port.port_spec(PORT)
    node = loaded.data
    for part in spec.prefix.split("."):
        node = node.setdefault(part, {})
    node["kind"] = implementation.KIND
    node[implementation.OUT_DIR] = out_dir
    # ⛔ The code root is pointed somewhere real and separate, because one of the
    # refusals below is about a directory *inside* it: a fixture whose root was
    # the examples directory would make that plant depend on where this repository
    # happens to sit.
    loaded.data["roots"] = {"code": root}
    for view in loaded.views.values():
        view.data["roots"] = {"code": root}
    # ⛔ A **collection** of roots where one is asked for. § 1 lets a project state
    # several and the adapter's containment check is written for exactly that --
    # "every one of them and not `code_root`" -- so a fixture that can only
    # produce one root leaves that loop asserted by nothing: replacing it with the
    # single `code_root` left the whole suite green.
    for name, path in (more or {}).items():
        loaded.data["roots"][name] = path
        loaded.views[name] = config.Config(
            dict(loaded.data, roots={"code": path}),
            loaded.skills_root,
            loaded.facts,
            root_key=name,
        )
    return loaded


def _entries_for(store: str, day: str) -> list[str]:
    """Every file in the store that is an entry for one day.

    ⛔ Derived from the implementation's own two halves rather than spelled, so a
    rename reddens the one assertion that holds the path byte for byte and not
    every assertion that happens to mention a file name.
    """
    return sorted(
        entry
        for entry in os.listdir(store)
        if entry.startswith(implementation.STEM)
        and entry.endswith(implementation.SUFFIX)
        and day in entry
    )


def _port(out_dir: str, root: str, more: dict | None = None) -> port.Port:
    return port.Port(_configuration(out_dir, root, more), port.port_spec(PORT))


def self_test() -> int:
    failures = 0

    def check(label: str, condition: bool, detail: str = "") -> None:
        nonlocal failures
        if condition:
            print(f"  ok    {label}")
        else:
            failures += 1
            print(f"  FAIL  {label}{': ' + detail if detail else ''}")

    def refused(call) -> str | None:
        """The key a call refuses on, or what it did instead.

        ⛔ Every exception and not only `ConfigError`. Measured while planting
        against this suite: removing the hours grammar left `float('6,5')` raising
        `ValueError`, and removing the address type check left `expandvars`
        raising `TypeError` -- each of them a real regression, and each killed the
        run with a traceback **before** the assertion that exists for it, so both
        plants read as green. A guard this suite holds must be able to redden a
        line rather than end the report.
        """
        try:
            call()
        except config.ConfigError as error:
            return error.key
        except Exception as error:  # noqa: BLE001 -- see the docstring
            return f"<raised {type(error).__name__}: {error}>"
        return None

    def refused_message(call) -> str:
        """What a refusal said, for the assertions that are about its wording."""
        try:
            call()
        except Exception as error:  # noqa: BLE001 -- a message, whatever it was
            return str(error)
        return ""

    with tempfile.TemporaryDirectory() as workspace:
        root = os.path.join(workspace, "repository")
        store = os.path.join(workspace, "store")
        os.makedirs(root)
        here = _port(store, root)
        spec = port.port_spec(PORT)

        # Every operation § 26 states is implemented, asserted as a **relation**
        # against the surface's own list rather than as a count or a list of
        # names: a number here would be wrong the next time the section grows.
        check(
            "this store implements every operation the surface states",
            all(here.implements(operation) for operation in here.stated),
            f"absent: {sorted(o for o in here.stated if not here.implements(o))!r}",
        )

        # ⛔ The path § 9 fixed, byte for byte. This is the acceptance condition a
        # project that states no destination is owed, and it is the one assertion
        # here that must never be relaxed to a pattern.
        where = here.invoke("locate", A_DAY)
        check(
            "an entry's path is the directory, the stem, the day and the suffix",
            where.result == os.path.join(store, f"day-report-{A_DAY}.txt"),
            f"located {where.result!r}",
        )
        check(
            "and locating creates nothing",
            not os.path.exists(store),
            f"{store} was created by a read",
        )

        # Nothing recorded yet, which is `None` and not an entry with no hours.
        check(
            "a day with no entry reads as none at all",
            here.invoke("read_day", A_DAY).result is None,
        )

        recorded = here.invoke("append_day", A_DAY, 6.5, "Wrote the thing.")
        check("a day is recorded", recorded.performed, str(recorded))
        check(
            "and lands at the path `locate` named",
            os.path.exists(where.result),
            f"{where.result!r} is not there",
        )
        read = here.invoke("read_day", A_DAY).result
        check(
            "and reads back as the two values it was given",
            read is not None
            and read["hours"] == 6.5
            and read["description"] == "Wrote the thing.",
            f"read {read!r}",
        )
        # ⛔ Over the values the writer can actually be handed, and not one
        # one-decimal float. ⚠️ Zero is the one that matters most: a day off is a
        # legitimate entry, and a store that could not read `0` back would report
        # every one of them unreadable.
        for given, expected in ((0, 0.0), (8, 8.0), (0.25, 0.25), (12.75, 12.75)):
            day = "2026-05-%02d" % (int(given) + 2)
            here.invoke("replace_day", day, given, f"Recorded as {given}.")
            back = here.invoke("read_day", day).result
            check(
                f"hours written as {given!r} read back as {expected!r}",
                back is not None and back["hours"] == expected,
                f"read {back and back['hours']!r}",
            )
        # ⛔ And a value this store could not read back is refused at the write.
        # Measured: a comma for a decimal point formatted perfectly, the write
        # reported the day recorded, and every later period read it as a day whose
        # hours could not be read -- with nothing between the two saying so.
        for given in ("6,5", "six", -2, float("inf"), "6 h"):
            at = refused(lambda h=given: here.invoke("append_day", "2026-06-01", h, "x"))
            check(
                f"hours written as {given!r} is refused at the write, naming the operation",
                at == f"{spec.prefix}.operations.append_day",
                f"reported {at!r}",
            )
        check(
            "and no entry was left behind by any of those",
            here.invoke("read_day", "2026-06-01").result is None,
            "a refused write recorded something",
        )
        # ⛔ A description whose own text looks like the hours line reads back
        # whole, and the day's hours stay the day's. The reader takes the first
        # matching line anywhere in the entry, so this is the shape where a
        # description could be read as the figure somebody is invoiced for.
        here.invoke("replace_day", A_DAY, 6.5, f"{implementation.HOURS_LABEL}: 3")
        back = here.invoke("read_day", A_DAY).result
        check(
            "a description that looks like an hours line does not become the hours",
            back["hours"] == 6.5
            and back["description"] == f"{implementation.HOURS_LABEL}: 3",
            f"read {back!r}",
        )
        # ⛔ And a hand-edited entry whose label is not first still reads with its
        # description. § 26 has what comes back out treated as somebody's text, and
        # the description used to be *everything after* the label -- so moving the
        # hours to the end read the description as empty, which the documented redo
        # would then write back as an entry with no description at all.
        with open(where.result, "w", encoding="utf-8") as handle:
            handle.write(f"Wrote it by hand.\n\n{implementation.HOURS_LABEL}: 4.5\n")
        back = here.invoke("read_day", A_DAY).result
        check(
            "a hand-edited entry with its hours last keeps its description",
            back["hours"] == 4.5 and back["description"] == "Wrote it by hand.",
            f"read {back!r}",
        )
        here.invoke("replace_day", A_DAY, 7.0, "Wrote it again, shorter.")

        # ⛔ The acceptance condition § 26 states for every adapter: a rebuilt day
        # leaves **one** entry. Proved by rebuilding a day already recorded and
        # counting what the directory holds, rather than by reading the file --
        # the failure this is about is a second file beside the first.
        rebuilt = here.invoke("replace_day", A_DAY, 7.0, "Wrote it again, shorter.")
        check("a recorded day is rebuilt", rebuilt.performed, str(rebuilt))
        # ⛔ Counted, and counted **for that day**. The assertion claims a rebuild
        # leaves one entry; listing the whole store proved the path contract a
        # second time instead, which the one assertion above already holds byte for
        # byte -- and it reddened on any other day being present, which is a
        # property of the fixture rather than of the rebuild.
        check(
            "and the rebuild leaves one entry for that day",
            len(_entries_for(store, A_DAY)) == 1,
            f"the store holds {_entries_for(store, A_DAY)!r} for it",
        )
        read = here.invoke("read_day", A_DAY).result
        check(
            "which carries the new values and no tail of the old",
            read["hours"] == 7.0
            and read["description"] == "Wrote it again, shorter."
            and "Wrote the thing." not in read["text"],
            f"read {read!r}",
        )

        # ⛔ And an append over a recorded day is refused rather than written
        # beside it, which is the doubled total § 26 names.
        over = refused(lambda: here.invoke("append_day", A_DAY, 1.0, "Again."))
        check(
            "an append over a day already recorded is refused, naming the operation",
            over == f"{spec.prefix}.operations.append_day",
            f"reported {over!r}",
        )
        check(
            "and the store still holds one entry for it",
            len(_entries_for(store, A_DAY)) == 1,
            f"the store holds {_entries_for(store, A_DAY)!r} for it",
        )

        # A period, per day and never a total.
        here.invoke("append_day", NEXT_DAY, 3.0, "Half a day.")
        here.invoke("append_day", A_LATER_DAY, 8.0, "A month later.")
        period = here.invoke("read_hours", A_DAY, NEXT_DAY).result
        check(
            "a period answers per day, both ends included",
            period["hours"] == {A_DAY: 7.0, NEXT_DAY: 3.0},
            f"read {period['hours']!r}",
        )
        check(
            "and a day outside it is not in the answer",
            A_LATER_DAY not in period["hours"],
            f"read {period['hours']!r}",
        )
        check(
            "and the answer carries no total for a consumer to read as one",
            "total" not in period and "sum" not in period,
            f"answered {sorted(period)!r}",
        )
        check(
            "and nothing in that range was unreadable",
            period["unreadable"] == {},
            f"reported {period['unreadable']!r}",
        )
        backwards = refused(lambda: here.invoke("read_hours", NEXT_DAY, A_DAY))
        check(
            "a period read backwards is refused rather than answered empty",
            backwards == f"{spec.prefix}.operations.read_hours",
            f"reported {backwards!r}",
        )
        # ⛔ The earlier end is held as well as the later one. Every planted day
        # sat at or after the range's start, so mutating the filter to drop its
        # `day < start` half left the suite green -- a period would have answered
        # with every day before it as well.
        later = here.invoke("read_hours", NEXT_DAY, A_LATER_DAY).result
        check(
            "a day before the period's first day is not in the answer",
            A_DAY not in later["hours"] and NEXT_DAY in later["hours"],
            f"read {later['hours']!r}",
        )

        # ⛔ A day the store holds and cannot read is named, never counted as
        # nothing. Planted by rewriting an entry the way a person correcting a
        # figure by hand would -- which is § 26's rule that what comes back out of
        # a store is data rather than this adapter's own output.
        with open(os.path.join(store, f"day-report-{NEXT_DAY}.txt"), "w", encoding="utf-8") as handle:
            handle.write("three and a half hours, roughly\n\nHalf a day.\n")
        period = here.invoke("read_hours", A_DAY, NEXT_DAY).result
        check(
            "an entry whose hours cannot be read is named as unreadable",
            NEXT_DAY in period["unreadable"],
            f"reported {period['unreadable']!r}",
        )
        check(
            "and is not in the hours it answers with, as zero or otherwise",
            NEXT_DAY not in period["hours"],
            f"read {period['hours']!r}",
        )
        check(
            "while the day beside it still answers",
            period["hours"] == {A_DAY: 7.0},
            f"read {period['hours']!r}",
        )
        # And the same entry read on its own is an entry with no hours rather than
        # no entry: a caller that read the two the same way would append beside it.
        edited = here.invoke("read_day", NEXT_DAY).result
        check(
            "an unreadable entry read on its own is present with no hours",
            edited is not None and edited["hours"] is None,
            f"read {edited!r}",
        )
        at = refused(lambda: here.invoke("append_day", NEXT_DAY, 3.0, "Half a day."))
        check(
            "so an append over it is still refused",
            at == f"{spec.prefix}.operations.append_day",
            f"reported {at!r}",
        )
        # ⛔ A file whose name is this store's shape and whose day is not a day is
        # reported rather than skipped: it may be the entry a period is missing.
        with open(os.path.join(store, "day-report-the-other-day.txt"), "w", encoding="utf-8") as handle:
            handle.write("Hours worked: 2\n\nSomething.\n")
        period = here.invoke("read_hours", A_DAY, A_LATER_DAY).result
        check(
            "a file named with no readable day is reported, not swept past",
            "day-report-the-other-day.txt" in period["unplaced"],
            f"reported {period['unplaced']!r}",
        )
        # ⛔ And reported **apart from the days**, which is what lets a consumer
        # read `unreadable` as *of this period*. A file nothing can place cannot
        # be known to fall inside the range, so counted among the days it made a
        # fully readable period come back partly unreadable -- measured, and a
        # consumer that stops on a non-empty `unreadable` would have refused to
        # answer about a period it could read completely.
        check(
            "and never among the days, which are the period's own",
            "day-report-the-other-day.txt" not in period["unreadable"],
            f"reported {period['unreadable']!r}",
        )
        clean = here.invoke("read_hours", A_LATER_DAY, A_LATER_DAY).result
        check(
            "so a period this store can read whole comes back with nothing unreadable",
            clean["hours"] == {A_LATER_DAY: 8.0} and clean["unreadable"] == {},
            f"read {clean!r}",
        )
        # ⛔ A name this store would never write is not placed either, however
        # well a date parser reads it. `date.fromisoformat` takes the basic form,
        # so this file used to normalise onto a canonical name, send the read
        # looking for a file that is not there, and report that day as holding no
        # readable hours line -- a false reason, pointing at the wrong fix.
        with open(os.path.join(store, "day-report-20260401.txt"), "w", encoding="utf-8") as handle:
            handle.write("Hours worked: 2\n\nThe same day, written compactly.\n")
        compact = here.invoke("read_hours", A_DAY, A_LATER_DAY).result
        check(
            "a day written in a form this store never writes is unplaced, not misread",
            "day-report-20260401.txt" in compact["unplaced"]
            and compact["hours"].get(A_LATER_DAY) == 8.0,
            f"read hours={compact['hours']!r} unplaced={compact['unplaced']!r}",
        )

        # ⛔ A day this store cannot name is refused before anything is written,
        # rather than writing a file no later read finds.
        # ⚠️ The refusal is taken once and then asserted, rather than re-invoked
        # inside the detail: `check`'s arguments are evaluated eagerly, so the old
        # shape ran a second write on every green pass -- and reported `locate`'s
        # answer in the detail for an assertion about `append_day`, which is the
        # wrong call's verdict printed on the one line a failure is read from.
        # ⚠️ `20260304` is deliberately not here: a caller handing that over gets
        # it normalised onto the one name this store writes, which is findable. It
        # is only a *file already named* that way which cannot be placed, since
        # normalising it sends the read somewhere the file is not.
        for given in ("2026-3-4", "yesterday", "2026-03-04T10:00"):
            at = refused(lambda day=given: here.invoke("append_day", day, 1.0, "x"))
            check(
                f"a day written {given!r} is refused, naming the operation list",
                at == f"{spec.prefix}.operations",
                f"reported {at!r}",
            )

    # The two directories that are refused, each in a workspace of its own so the
    # refusal is the only thing that could have stopped a write.
    with tempfile.TemporaryDirectory() as workspace:
        root = os.path.join(workspace, "repository")
        os.makedirs(root)
        spec = port.port_spec(PORT)
        # ⛔ No directory stated, which § 26 keeps unrequired and this adapter
        # therefore refuses at the first operation with the key named.
        unset = _port("", root)
        check(
            "no directory stated is refused at the operation, naming the key",
            refused(lambda: unset.invoke("locate", A_DAY))
            == f"{spec.prefix}.{implementation.OUT_DIR}",
            f"reported {refused(lambda: unset.invoke('locate', A_DAY))!r}",
        )
        # ⛔ A directory inside the repository, which § 9 forbids outright. ⚠️ The
        # plant is a path *under* the root rather than the root itself, that being
        # the shape a project would actually write.
        inside = _port(os.path.join(root, "logs"), root)
        at = refused(lambda: inside.invoke("append_day", A_DAY, 1.0, "x"))
        check(
            "a directory inside the code root is refused, naming the key",
            at == f"{spec.prefix}.{implementation.OUT_DIR}",
            f"reported {at!r}",
        )
        check(
            "and nothing was written there",
            not os.path.exists(os.path.join(root, "logs")),
            "the refusal came after the directory was made",
        )
        # ⛔ Through a **link** as well, which is the half a lexical comparison
        # misses. Measured on this change: `abspath` resolves no symlink, so a
        # store addressed through one landed inside the checkout and `locate`
        # named a path under the temp root whose real path was in the repository.
        # Hours in a tracked file is exactly what this refusal exists to stop.
        linked = os.path.join(workspace, "a-link-into-the-repository")
        os.symlink(root, linked)
        through = _port(os.path.join(linked, "logs"), root)
        at = refused(lambda: through.invoke("append_day", A_DAY, 1.0, "x"))
        check(
            "a directory reaching the code root through a link is refused too",
            at == f"{spec.prefix}.{implementation.OUT_DIR}",
            f"reported {at!r}",
        )
        check(
            "and nothing was written through it either",
            not os.path.exists(os.path.join(root, "logs")),
            "the refusal came after the directory was made",
        )
        # ⛔ Every code root and not the first, which is `_code_roots`'s whole
        # reason to exist. ⚠️ The fixture states a collection, since a
        # single-rooted one leaves that loop asserted by nothing: replacing it
        # with the one `code_root` left the suite green.
        second = os.path.join(workspace, "another-repository")
        os.makedirs(second)
        several = _port(os.path.join(second, "logs"), root, more={"other": second})
        at = refused(lambda: several.invoke("append_day", A_DAY, 1.0, "x"))
        check(
            "a directory inside the second of several code roots is refused",
            at == f"{spec.prefix}.{implementation.OUT_DIR}",
            f"reported {at!r}",
        )
        # And the green side of that scope: a directory beside the repository is
        # accepted, so the refusal above is about being inside one rather than
        # about this adapter refusing every path.
        beside = _port(os.path.join(workspace, "beside"), root)
        check(
            "a directory beside the code root is accepted",
            beside.invoke("append_day", A_DAY, 1.0, "Outside the tree.").performed,
        )
        # ⛔ And the variable a project writes is expanded here, which is what § 11
        # leaves to the role's own command. ⚠️ The variable is **this suite's own**
        # and is set for the call rather than borrowed from the environment: a plant
        # on a name the machine happens to hold is a plant that answers differently
        # on a machine that does not — and the two names a reader reaches for first
        # are a home directory, which the sweep in `tools/` forbids naming, and the
        # temp root, which is not set everywhere this runs.
        variable = "MJOLNIR_FILE_SUITE_STORE"
        os.environ[variable] = os.path.join(workspace, "named-by-a-variable")
        try:
            named = _port(os.path.join(f"${variable}", "store"), root)
            located = named.invoke("locate", A_DAY).result
        finally:
            os.environ.pop(variable, None)
        check(
            "a directory naming a shell variable is expanded by this adapter",
            located == os.path.join(workspace, "named-by-a-variable", "store",
                                    f"day-report-{A_DAY}.txt"),
            f"located {located!r}",
        )
        # ⛔ And the near miss that fires on most machines: a variable nothing
        # sets. `expandvars` leaves the name **literally**, so this project's own
        # `$TMPDIR/…` addresses a directory called `$TMPDIR` under wherever the
        # process stood -- on Linux, in a container, in a cron shell. ⚠️ The
        # variable is this suite's own and is removed before the call, so the
        # assertion is about expansion failing rather than about what the machine
        # happens not to carry.
        # ⚠️ The path is **absolute apart from the variable**, or the refusal below
        # would be the next one's: an unexpanded name at the front makes the whole
        # value relative, so the plant passed against an adapter that had lost this
        # guard entirely and kept the other. Measured.
        os.environ.pop(variable, None)
        unset_variable = _port(os.path.join(workspace, f"${variable}", "store"), root)
        at = refused(lambda: unset_variable.invoke("locate", A_DAY))
        check(
            "a directory naming a variable nothing sets is refused, not joined",
            at == f"{spec.prefix}.{implementation.OUT_DIR}",
            f"reported {at!r}",
        )
        check(
            "and the refusal names the variable, which is the sentence that fixes it",
            variable in str(
                refused_message(lambda: unset_variable.invoke("locate", A_DAY))
            ),
            "the refusal did not name it",
        )
        # ⛔ And an address that is not one. A relative directory resolves against
        # whatever the process is standing in, so one configuration addresses a
        # different store per tree -- and under the worktree branch model that is
        # the ordinary case, with `read_day` then answering *not recorded* for a
        # day the store beside it holds and the role appending a second entry.
        relative = _port(os.path.join("day-logs", "here"), root)
        at = refused(lambda: relative.invoke("locate", A_DAY))
        check(
            "a relative directory is refused rather than joined onto the cwd",
            at == f"{spec.prefix}.{implementation.OUT_DIR}",
            f"reported {at!r}",
        )
        # ⛔ And a value that is not a directory at all, which reached the path
        # machinery as a `TypeError` out of the operation -- the raw traceback this
        # package refuses to hand a role.
        mistyped = _port(5, root)
        at = refused(lambda: mistyped.invoke("locate", A_DAY))
        check(
            "a directory stated as a number is refused, naming the key",
            at == f"{spec.prefix}.{implementation.OUT_DIR}",
            f"reported {at!r}",
        )

    # ⛔ A rebuild that fails leaves the entry that was there, and never nothing.
    # ⚠️ Planted by taking write permission off the **store** once the entry exists,
    # which is the one shape that fails between the two halves of a rebuild without
    # injecting anything: unlink-then-create left the day with no entry at all and
    # reported that the store could not be reached -- which § 26 defines as the old
    # entry standing, so the report told somebody their entry survived at the one
    # moment it had just been deleted.
    with tempfile.TemporaryDirectory() as workspace:
        root = os.path.join(workspace, "repository")
        store = os.path.join(workspace, "store")
        os.makedirs(root)
        here = _port(store, root)
        here.invoke("append_day", A_DAY, 6.5, "The entry that must survive.")
        # ⛔ The write is made to fail, rather than the directory sealed. A sealed
        # store fails the **unlink** too, so the old entry survived either way and
        # the plant passed against the very shape it exists to refuse -- measured.
        # What discriminates is a failure that lands after an unlink would have
        # succeeded, which is what shadowing the module's `open` produces.
        def _no_space(*args, **kwargs):
            raise OSError(28, "No space left on device")

        implementation.open = _no_space
        try:
            outcome = here.invoke("replace_day", A_DAY, 7.0, "A rebuild that cannot land.")
        finally:
            del implementation.open
        check(
            "a rebuild whose write fails comes back failed",
            outcome.failed and not outcome.performed,
            f"got {str(outcome)!r}",
        )
        standing = here.invoke("read_day", A_DAY).result
        check(
            "and the entry that was there is still there, with its own values",
            standing is not None
            and standing["hours"] == 6.5
            and standing["description"] == "The entry that must survive.",
            f"read {standing!r}",
        )
        check(
            "and no half-written file is left beside it",
            sorted(os.listdir(store)) == [f"day-report-{A_DAY}.txt"],
            f"the store holds {sorted(os.listdir(store))!r}",
        )

    # ⛔ A period read against a store that is not a store. ⚠️ This is the gap that
    # hid the worst defect in this adapter: `isdir` answers `False` for a directory
    # nobody has created and for an address naming a regular file, a dangling link
    # or a directory behind an unreadable parent -- and `read_hours` answered all
    # of them with a well-formed empty period. A billing consumer would have read
    # that as a period nobody worked. § 26's own fallback for the operation is that
    # the consumer has **no answer** and stops.
    with tempfile.TemporaryDirectory() as workspace:
        root = os.path.join(workspace, "repository")
        os.makedirs(root)
        # An address that is a regular file.
        occupied = os.path.join(workspace, "not-a-directory")
        with open(occupied, "w", encoding="utf-8") as handle:
            handle.write("a file where a store was configured\n")
        held = _port(occupied, root).invoke("read_hours", A_DAY, A_LATER_DAY)
        check(
            "a period read against an address that is a file comes back failed",
            held.failed and not held.performed,
            f"got {str(held)!r}",
        )
        # A link that points nowhere.
        dangling = os.path.join(workspace, "points-nowhere")
        os.symlink(os.path.join(workspace, "never-existed"), dangling)
        gone = _port(dangling, root).invoke("read_hours", A_DAY, A_LATER_DAY)
        check(
            "and against a link that points nowhere, also failed",
            gone.failed and not gone.performed,
            f"got {str(gone)!r}",
        )
        # ⛔ And the green side of the same scope, or the two above would pass on an
        # adapter that simply refused every period: a store nobody has written to
        # yet is an **answer**, with the range named and no hours in it.
        fresh = _port(os.path.join(workspace, "nothing-written-yet"), root)
        empty = fresh.invoke("read_hours", A_DAY, A_LATER_DAY)
        check(
            "while a store nobody has written to yet answers with an empty period",
            empty.performed
            and empty.result["hours"] == {}
            and empty.result["first"] == A_DAY,
            f"got {str(empty)!r}",
        )

    # ⛔ A store that cannot be reached, which is the one outcome held apart from
    # every absence above: the capability is present and the call did not go
    # through, so the port answers `failed` with the store's own words and the day
    # is **not** reported as recorded. Planted by taking write permission off the
    # directory rather than by a double, because what is being held is this
    # adapter turning an operating-system failure into the contract's own
    # exception.
    with tempfile.TemporaryDirectory() as workspace:
        root = os.path.join(workspace, "repository")
        sealed = os.path.join(workspace, "sealed")
        os.makedirs(root)
        os.makedirs(sealed)
        os.chmod(sealed, 0o500)
        try:
            unreachable = _port(os.path.join(sealed, "store"), root)
            outcome = unreachable.invoke("append_day", A_DAY, 4.0, "Nowhere to put it.")
            # ⚠️ Asserted as *the plant took* before asserting the behaviour. Run
            # as a user the mode does not bind -- root -- the write succeeds and
            # this whole block would otherwise report green on a plant that never
            # fired, which is the one failure a permission-based plant has.
            #
            # ⛔ And **reported** rather than failed where the mode does not bind.
            # A directory mode says nothing to uid 0, so counting that as a failure
            # turns every container runner red with a message about a plant rather
            # than about the code -- a gate reddening on the environment it ran in.
            # The environment is asserted first, and the block is skipped with the
            # reason named.
            binds = os.geteuid() != 0
            if not binds:
                print(
                    "  ----  a store that cannot be reached: not asserted, this "
                    "process is uid 0 and a directory mode does not bind it"
                )
            elif outcome.performed:
                check(
                    "the sealed directory really refused the write",
                    False,
                    "the write went through on a process the mode should bind, so "
                    "this plant asserts nothing about a store that cannot be "
                    "reached",
                )
            if binds and not outcome.performed:
                check(
                    "a store that cannot be reached comes back failed, not as an absence",
                    outcome.failed and outcome.detail != unreachable.fallback("append_day"),
                    f"got {str(outcome)!r}",
                )
                check(
                    "and the report carries the store's own words",
                    "could not be created" in outcome.detail
                    or "could not be written" in outcome.detail,
                    f"got {outcome.detail!r}",
                )
                check(
                    "while the capability still reads as present",
                    unreachable.implements("append_day"),
                )
                check(
                    "and nothing was recorded",
                    not os.path.exists(os.path.join(sealed, "store")),
                    "the store was created despite the refusal",
                )
        finally:
            # ⛔ Restored before the directory is removed: a mode the cleanup
            # cannot traverse leaves the temporary tree behind on every run.
            os.chmod(sealed, 0o700)

    if failures:
        print(f"\n{failures} assertion(s) did not hold.")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(self_test())
