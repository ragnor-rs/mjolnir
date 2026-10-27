#!/usr/bin/env python3
"""A day's entry as one text file in a directory, behind the destination port.

The cheapest store there is, and the one a project has before it has anywhere
else to put an entry. It is also the kind § 26 defaults to, which is the whole
reason this adapter exists first: a project that states no destination has to
keep writing exactly what the day-log role wrote before that port existed, and an
adapter nothing stands on is an adapter whose holes are nobody's problem.

What it implements, and what it deliberately does not:

  * **Every operation § 26 states.** A directory can be appended to, read back,
    rewritten whole, swept across a range and named, so none of the five is a
    capability this store lacks. ⛔ No count of them is carried here: the list is
    closed and stated once, in § 26, and a number here would be wrong the next
    time it grows.
  * **`append_day` refuses a day that is already recorded**, rather than writing
    beside it. § 26 makes `read_day` what decides which of the two writes is
    asked for, and an append that silently became a second entry is the doubled
    total that section names. The refusal is a `ConfigError` on the role's own
    call and not a `HostUnavailable`: the store is fine and the call was wrong.
  * **`replace_day` unlinks and writes**, never opens for update. § 26's rule is
    that a rebuilt entry is rebuilt whole, and an in-place write leaves whatever
    the rebuild did not think to touch -- a shorter description over a longer one
    leaves the tail of the longer.
  * **`read_hours` answers per day and never with a total**, and names the days it
    found and could not read beside the ones it could. § 26's rule, and the one
    place this store can quietly under-report: a day whose hours line a person
    edited into something unparsable is not zero hours, and a consumer summing
    what it could parse would lose it with nothing saying so.
  * **`locate` names the path and does not create it.** A role says where an entry
    landed, which is a read; creating the directory there would mean a report had
    written something.

**The entry's own shape is this kind's and is stated once, here.** § 9 fixes
*what* an entry carries -- the hours and the description, and nothing else -- and
§ 26 fixes *that* a file store addresses by directory; how those two values sit in
a text file is neither section's business and is `_ENTRY` below. ⚠️ **It is
written and parsed by one statement**, so a reworded label is reworded for both
halves at once; the suite plants a hand-edited entry to show the read can fail at
all.

⛔ **The directory is expanded here and nowhere earlier.** § 11 has the reader
store a `dir` as written and expand nothing, a value naming a shell variable
being expanded by the role's own command -- and once the destination is a port,
this adapter *is* that command. Expanding it in the reader would resolve one
session's environment into a value another session reads.

⛔ **Nothing is written inside a repository.** § 9's rule, enforced here rather
than trusted: a configured directory that resolves inside the code root is refused
with the key named, because a `.gitignore` that holds back one pattern lets an
entry under any other name reach a commit -- and hours in a tracked file is what
that rule exists to stop.
"""

from __future__ import annotations

import datetime
import os
import re
import sys

# The package's parent, appended rather than prepended: this module is imported
# as `destinations.file`, so the contract beside it is not otherwise on the path,
# and putting it first would shadow a standard-library name.
_SCRIPTS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _SCRIPTS not in sys.path:
    sys.path.append(_SCRIPTS)

import port  # noqa: E402

KIND = "file"

# The configuration key this adapter is addressed by. ⛔ Read from the port rather
# than written out: the prefix is the port's own, so a second spelling here would
# be free to disagree with the marker § 26 states it on.
OUT_DIR = "out_dir"

# One day's file. ⚠️ The stem is what § 9 wrote before this port existed and is
# unchanged on purpose -- a project that states no destination gets the same path
# it always got, which is the acceptance condition this adapter was built for.
# The glob is derived from the same two halves, so a rename cannot leave the
# sweep reading files the writer no longer produces.
STEM = "day-report-"
SUFFIX = ".txt"
DATE = "%Y-%m-%d"

# How the two values sit in the file. ⛔ One statement for the write and the read:
# the label is substituted into the first and matched by the second, so there is
# no second spelling to drift. ⚠️ The read is deliberately looser than the write
# -- any spacing, any case -- because a person who opens an entry and corrects a
# figure is the expected author of the text being parsed, and § 26 has what comes
# back out of the store treated as data rather than as this adapter's own output.
HOURS_LABEL = "Hours worked"
_ENTRY = "{label}: {hours}\n\n{description}\n"
_HOURS_LINE = re.compile(
    rf"^\s*{re.escape(HOURS_LABEL)}\s*:\s*(?P<hours>[0-9]+(?:\.[0-9]+)?)\s*$",
    re.IGNORECASE | re.MULTILINE,
)

# The configuration the port last handed down, and the only place one comes from.
# ⛔ Never resolved here, and never from the working directory: which project's
# day a store holds is § 1's skills root to decide and the port's to pass, and a
# process serving more than one project would otherwise pin every later day to the
# first one's directory.
_bound = None


def bind(configuration) -> None:
    """Take the configuration for the operation about to run.

    `Port.invoke` calls this before every operation, so it is per call rather
    than per process and switching projects needs no reset.
    """
    global _bound
    _bound = configuration


# The directory this module sits in, which is the whole of what declares which
# port it answers for. ⛔ Derived and never written as a port's name: the package
# beside this file states that a module here carries no `PORT` of its own, because
# a second statement of it could be wrong in the one way nothing catches -- a
# module filed under one package answering for another. Read off the path rather
# than off `__package__` so it holds when this file is run directly as well.
_PACKAGE = os.path.basename(os.path.dirname(os.path.abspath(__file__)))


def _spec():
    """This port's declaration, resolved by the directory this module sits in."""
    for spec in port.surface_ports().values():
        if spec.package == _PACKAGE:
            return spec
    raise port.ConfigError(
        f"{_PACKAGE}/{os.path.basename(__file__)}",
        "sits in a package no `# port:` marker names, so which port it answers "
        "for cannot be resolved. A module's own directory is what declares that "
        "(§ 26), and no port on the surface is read out of this one.",
    )


def _prefix() -> str:
    """The configuration block this port's keys sit under."""
    return _spec().prefix


def _key(name: str = OUT_DIR) -> str:
    """The dotted path of one of this kind's keys, for a refusal to name."""
    return f"{_prefix()}.{name}"


def _code_roots() -> list[str]:
    """Every repository this configuration addresses, absolutely.

    ⛔ Every one of them and not `code_root`. § 1 lets a project state a
    collection, where that property has no one answer -- and the question below is
    whether the directory is inside *any* repository the project names, which a
    single answer could not ask.
    """
    views = getattr(_bound, "views", None) or {}
    roots = [view.code_root for view in views.values()]
    # ⛔ The **real** path of each, because the comparison below is what keeps an
    # entry out of a tracked file and a lexical comparison is not a comparison of
    # places. A root reached through a link is the same repository.
    return [os.path.realpath(root) for root in roots or [_bound.code_root]]


def _directory() -> str:
    """The directory this day's entry lands in, expanded and checked.

    Two refusals, each naming the key: no directory configured, and a directory
    inside a code root. ⚠️ Both are `ConfigError` rather than `HostUnavailable` --
    § 26 states the key is not required, so an absent one is a configuration this
    adapter cannot act on and never a store that failed.
    """
    if _bound is None:
        raise port.ConfigError(
            f"{_prefix()}.implementations.file",
            "was asked for an operation before the port bound a configuration to "
            "it. Every operation is reached through `Port.invoke`, which binds "
            "first; a direct call bypasses the one place the project is stated.",
        )
    stated = _bound.get(_key())
    if not stated:
        raise port.ConfigError(
            _key(),
            "is not set, so this kind has no directory to write an entry into. "
            "§ 26 states the key is not required -- a project that maps no "
            "`day_log` carrier needs no store -- so a project that does map one "
            "states it.",
        )
    resolved = os.path.abspath(os.path.expanduser(os.path.expandvars(stated)))
    # ⛔ The code roots and not the working directory: a role runs from a tree and
    # addresses a project, so the question is whether the configured directory is
    # inside a repository this configuration names (§ 1).
    #
    # ⛔ And asked of the **real** path on both sides. `abspath` normalises `..`
    # and resolves no link at all, so a directory reaching a code root through a
    # symlink was accepted and an entry would have landed inside the repository --
    # measured, with `locate` naming a path under the temp root whose real path was
    # in the checkout. What is returned is still the path the project wrote, since
    # that is the address a report names and the one a person recognises.
    real = os.path.realpath(resolved)
    for root in _code_roots():
        if real == root or real.startswith(root + os.sep):
            through = "" if real == resolved else f" by way of {real!r}"
            raise port.ConfigError(
                _key(),
                f"resolves to {resolved!r}, which is inside the code root "
                f"{root!r}{through}. § 9 keeps an entry out of every tracked "
                "file, and a directory inside the repository puts one a "
                "`git add -A` away from a commit whatever the ignore file says.",
            )
    return resolved


def _path(day: str) -> str:
    """One day's file inside the configured directory."""
    return os.path.join(_directory(), f"{STEM}{_day(day)}{SUFFIX}")


def _day(day: str) -> str:
    """The day as this store names it, refusing anything else.

    ⛔ Parsed rather than interpolated. A caller handing over `2026-1-5`, a
    timestamp or a word would otherwise name a file that no sweep below matches
    and no later read finds -- an entry written and permanently invisible, which
    is the one failure a store silently has.
    """
    try:
        return datetime.date.fromisoformat(str(day)).strftime(DATE)
    except ValueError:
        raise port.ConfigError(
            _key("day"),
            f"was given {day!r}, which is not a day written `{DATE}`. An entry is "
            "addressed by the day § 9 measured, and a day this store cannot name "
            "would be written to a file nothing later reads.",
        ) from None


def _make(directory: str) -> None:
    try:
        os.makedirs(directory, exist_ok=True)
    except OSError as error:
        raise port.HostUnavailable(
            f"`{directory}` could not be created ({error.strerror}), so nothing "
            "was recorded"
        ) from None


def _render(hours, description: str) -> str:
    return _ENTRY.format(
        label=HOURS_LABEL, hours=hours, description=str(description).strip()
    )


# --- the operations ---------------------------------------------------------
#
# Each takes what the day-log role already has and returns what it can say out
# loud. None of them reads a capability: being here *is* the declaration (§ 3).


def read_day(day: str) -> dict | None:
    """The entry recorded for that day, or `None` where there is none.

    ⛔ `None` only for a file that is not there. A file that is there and whose
    hours cannot be parsed comes back **with `hours: None`** and the text, because
    an unreadable entry is not an absent one -- and a caller that read the two the
    same way would append beside an entry it could not parse.
    """
    path = _path(day)
    if not os.path.exists(path):
        return None
    try:
        with open(path, encoding="utf-8") as handle:
            text = handle.read()
    except OSError as error:
        raise port.HostUnavailable(
            f"`{path}` exists and could not be read ({error.strerror})"
        ) from None
    found = _HOURS_LINE.search(text)
    return {
        "day": _day(day),
        "path": path,
        "hours": float(found.group("hours")) if found else None,
        "description": text[found.end() :].strip() if found else text.strip(),
        "text": text,
    }


def append_day(day: str, hours, description: str) -> dict:
    """Record one day's two values, refusing a day already recorded."""
    standing = read_day(day)
    if standing is not None:
        raise port.ConfigError(
            _key(),
            f"already holds an entry for {_day(day)} at `{standing['path']}`. "
            "§ 26 has `read_day` decide which write is asked for, and an append "
            "beside an entry that is already there is two entries claiming the "
            "same hours. Ask for a replacement.",
        )
    path = _path(day)
    _make(os.path.dirname(path))
    try:
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(_render(hours, description))
    except OSError as error:
        raise port.HostUnavailable(
            f"`{path}` could not be written ({error.strerror}), so the day was "
            "not recorded"
        ) from None
    return {"day": _day(day), "path": path, "hours": hours}


def replace_day(day: str, hours, description: str) -> dict:
    """Rebuild the day's entry whole, unlinking whatever was there.

    ⛔ Unlink and write, never an update in place: § 26's rule, and the failure it
    names is specific -- a rebuilt entry shorter than the one it replaces leaves
    the tail of the old one behind, which reads as part of the new description.
    """
    path = _path(day)
    _make(os.path.dirname(path))
    try:
        if os.path.exists(path):
            os.unlink(path)
        with open(path, "x", encoding="utf-8") as handle:
            handle.write(_render(hours, description))
    except OSError as error:
        raise port.HostUnavailable(
            f"`{path}` could not be rebuilt ({error.strerror})"
        ) from None
    return {"day": _day(day), "path": path, "hours": hours}


def read_hours(first: str, last: str) -> dict:
    """Each day's stated hours between two days, both ends included.

    ⛔ Per day and never a total, with the days this store holds and could not
    read named beside the ones it could. § 26's rule: a consumer that summed what
    it could parse would under-report a period and nothing would say so.
    """
    start, end = _day(first), _day(last)
    if start > end:
        raise port.ConfigError(
            _key("range"),
            f"was asked for {start} to {end}, which ends before it begins. A "
            "period read backwards would come back empty, which reads exactly "
            "like a period nobody worked.",
        )
    directory = _directory()
    hours: dict[str, float] = {}
    unreadable: dict[str, str] = {}
    if not os.path.isdir(directory):
        # ⚠️ Not an error and not an empty answer either: a directory that is not
        # there holds no entry, and the caller is told which range was asked about
        # so it can tell that from a range of days nobody logged.
        return {"first": start, "last": end, "hours": hours, "unreadable": unreadable}
    try:
        entries = sorted(os.listdir(directory))
    except OSError as error:
        raise port.HostUnavailable(
            f"`{directory}` could not be listed ({error.strerror}), so no period "
            "could be read"
        ) from None
    for entry in entries:
        if not entry.startswith(STEM) or not entry.endswith(SUFFIX):
            continue
        day = entry[len(STEM) : -len(SUFFIX)]
        try:
            day = datetime.date.fromisoformat(day).strftime(DATE)
        except ValueError:
            # A file whose name is this store's shape and whose day is not a day.
            # ⛔ Reported rather than skipped: it may be the entry the period is
            # missing, and a sweep that dropped it would answer short.
            unreadable[entry] = "the file name carries no day this store can read"
            continue
        if day < start or day > end:
            continue
        read = read_day(day)
        if read is None or read["hours"] is None:
            unreadable[day] = (
                f"`{read['path'] if read else entry}` states no "
                f"`{HOURS_LABEL}` line this store can read"
            )
            continue
        hours[day] = read["hours"]
    return {"first": start, "last": end, "hours": hours, "unreadable": unreadable}


def locate(day: str) -> str:
    """Where that day's entry is, whether or not it is there yet.

    ⛔ Creates nothing. A role says this out loud, which is a read, and a report
    that made a directory would have written something.
    """
    return _path(day)


ADAPTER = port.Adapter(binder=bind, operations={
    "append_day": append_day,
    "read_day": read_day,
    "replace_day": replace_day,
    "read_hours": read_hours,
    "locate": locate,
})


def self_test() -> int:
    """This implementation's own decisions, held beside it.

    What the contract's suite holds is the contract -- the operation list, the
    absent case, the writer refusal. These are this store's own: the path § 9
    fixed, a rebuild that leaves one entry, a hand-edited entry that is reported
    rather than counted as nothing, and the two directories that are refused.
    """
    from destinations import _file_suite as suite

    return suite.self_test()


if __name__ == "__main__":
    sys.exit(self_test())
