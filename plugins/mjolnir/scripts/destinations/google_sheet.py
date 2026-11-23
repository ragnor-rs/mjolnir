#!/usr/bin/env python3
"""A day's entry as one row of a spreadsheet, behind the destination port.

The kind the **reading** half of this port was stated for. A file store answers
`read_hours` by listing a directory and parsing each entry; a spreadsheet already
holds a column of figures over a column of days, which is what a period's
consumer sums -- and what the day-log role's own cross-day validation reads.

What it implements, and what it decided along the way:

  * **Every operation § 26 states**, `locate` included. ⛔ But `locate` answers
    with the **place inside the store** and never with the store's identifier:
    that identifier is marked `# private`, and § 28 keeps a private value out of
    every report. A tab and a row say where the entry landed to whoever can
    already reach the sheet, and say nothing to whoever cannot.
  * **The sheet's shape is the project's**, so the three columns are resolved
    against the tab's own header row rather than fixed by position. ⛔ Every way
    that resolution fails is a refusal naming the key -- a header word the sheet
    does not carry, a word two columns carry, two roles landing on one column --
    because the alternative is a figure written into whichever cell happened to
    be third, which reads as a run that worked.
  * ⛔ **Values, never formulas, in both directions.** The write is `RAW`, so the
    sheet stores the figure § 9 produced and neither parses nor re-rounds it; the
    read asks for what was *entered* rather than for what is displayed, so a
    summing formula in the hours cell is an **unreadable** day and never the
    number it currently shows. A total read off a formula is a second statement
    of the period, and a stale one is a wrong invoice.
  * **A day is addressed by the date cell's own text and never by a row's
    position.** A row is appended at the end, a person sorts the tab, and
    position stops meaning anything -- so every operation finds its row by
    reading the day out of the cell.
  * ⛔ **Nothing holds a spreadsheet against two writers**, and this adapter
    reports rather than pretends. There is no exclusive create here -- the thing
    `append_day`'s `open(path, "x")` gives the file kind next door -- so the
    append reads the day back and **fails naming both rows** where it finds two.
    One entry per day is a property this kind can report on and not one it can
    hold, and § 26's doubled total is what a silent second row becomes.
  * ⚠️ **A numeric date cell is a row this kind cannot place, and that is stated
    rather than guessed at.** A sheet somebody already keeps holds real dates,
    which come back as serial numbers; the epoch those count from is a property
    of the spreadsheet that this host's API does not publish, so placing one into
    a day would be a guess about which day somebody's hours belong to. It goes in
    `read_hours`'s `unplaced` -- reported, never swept past, and never counted as
    a day of the period.

**The credential is the shell's and the address is the configuration's.** § 14
holds a credential out of every configured value and names the variable instead,
which is how a kind behind a service is reachable at all; the identifier of the
sheet is an address a project may not be able to commit, so § 26 marks it
`# private` and § 28's layer answers it.

⛔ **Every guard sits above the transport seam**, which is the lesson the tracker
implementations already paid for: a sheet id that is blank, a column mapping that
does not resolve and a shell holding no token all read as *the call went out and
the host answered* when the check lives inside the function a suite replaces.
"""

from __future__ import annotations

import datetime
import json
import os
import re
import socket
import sys
import urllib.error
import urllib.parse
import urllib.request

# The package's parent, appended rather than prepended: this module is imported
# as `destinations.google_sheet`, so the contract beside it is not otherwise on
# the path, and putting it first would shadow a standard-library name.
_SCRIPTS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _SCRIPTS not in sys.path:
    sys.path.append(_SCRIPTS)

import port  # noqa: E402

KIND = "google-sheet"

# The configuration keys this kind is addressed and shaped by. ⛔ The prefix is
# read off the port's own marker rather than written out, so these are the leaves
# alone -- a second spelling of the block would be free to disagree with § 26.
SHEET = "sheet"
TAB = "tab"
COLUMNS = "columns"

# The three roles a column plays. ⛔ The surface's, and the project's words are
# what the configuration maps onto them: this is the closed list the mapping is
# resolved against, and a fourth role would be a surface change rather than a
# line here.
DATE, HOURS, DESCRIPTION = "date", "hours", "description"
ROLES = (DATE, HOURS, DESCRIPTION)

# How a day is written in the date cell. ⚠️ The same spelling the file kind next
# door uses, and for the same reason: a day this store cannot name again is an
# entry written and permanently invisible.
DAY = "%Y-%m-%d"

# ⛔ What the writer may write as hours, which is **the reader's own grammar**.
# The rule, and the failure it is against, are the file kind's and are stated
# there: a value written that this store cannot read back is a day reported
# recorded and reported unreadable for ever after.
_WRITABLE_HOURS = re.compile(r"^[0-9]+(?:\.[0-9]+)?$")

# A cell whose content is a formula rather than a value. ⚠️ Read off what was
# *entered*, which is why this is a prefix test on text and not an inspection of
# a computed number: with the host asked for formulas, a formula arrives as its
# own source.
_FORMULA = "="

# The host, its version, and how long a call may take. ⚠️ Written out here
# because this is the one place in the toolkit a store may be named (the package
# beside this file states that rule), and nowhere else reaches them.
API = "https://sheets.googleapis.com/v4/spreadsheets"
TIMEOUT = 30

# The variable the credential arrives in. ⛔ A **name**, which is the whole of
# what § 14 permits: the project writes this in `environment.inherits` and the
# shell carries the value.
TOKEN_VARIABLE = "GOOGLE_SHEETS_TOKEN"

# The statuses this host's answers are read apart by, and the sentinel for a call
# that never reached it. ⛔ `UNREACHED` is not an HTTP status and is negative for
# that reason: a call that went nowhere and a host that answered are the two
# § 26 forbids reading as one another.
UNREACHED = -1
UNAUTHORISED = (401, 403)
NOT_FOUND = 404
RATE_LIMITED = 429

# The configuration the port last handed down, and the only place one comes from.
# ⛔ Never resolved here and never from the working directory: which project's
# sheet is addressed is § 1's skills root to decide and the port's to pass.
_bound = None


def bind(configuration) -> None:
    """Take the configuration for the operation about to run.

    `Port.invoke` calls this before every operation, so it is per call rather
    than per process and switching projects needs no reset.
    """
    global _bound
    _bound = configuration


# The directory this module sits in, which is the whole of what declares which
# port it answers for. ⛔ Derived and never written as a port's name, for the
# reason the package beside this file states. Read off the path rather than off
# `__package__` so it holds when this file is run directly as well.
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


def _key(leaf: str) -> str:
    """One of this kind's keys, for a refusal to name.

    ⛔ A refusal about a **call** never comes through here and names the
    operation list instead, which is the discipline the file kind's own one-key
    version of this states: a `ConfigError`'s key is contractually the thing to
    go and edit.
    """
    return f"{_prefix()}.{leaf}"


def _operations(operation: str) -> str:
    """Where § 26 states what an operation is asked for.

    The key a refusal about a **call** carries, rather than a configuration path
    no project could edit to fix it.
    """
    return f"{_prefix()}.operations.{operation}"


def _configured(leaf: str, what: str) -> str:
    """One configured string, refused rather than defaulted or coerced.

    ⚠️ `sheet` reaches this through § 28's layer where the project lists it, and
    that is `Config.get`'s business rather than this adapter's: what arrives here
    is a value either way, and the refusals below are the same for both.
    """
    if _bound is None:
        raise port.ConfigError(
            _spec().name,
            "was asked for an operation before the port bound a configuration to "
            "it. Every operation is reached through `Port.invoke`, which binds "
            "first; a direct call bypasses the one place the project is stated.",
        )
    stated = _bound.get(_key(leaf))
    if not stated:
        raise port.ConfigError(
            _key(leaf),
            f"is not set, so this kind has no {what}. § 26 states the key is not "
            "required -- a project that maps no `day_log` carrier needs no store "
            "-- so a project that does map one states it.",
        )
    # ⛔ A string, and said so rather than handed on. A number or a list reaches
    # the request builder as a `TypeError` out of the operation, which is the raw
    # traceback this package refuses to hand a role.
    if not isinstance(stated, str):
        raise port.ConfigError(
            _key(leaf),
            f"is {stated!r}, which is not a {what}. § 26 states this key as a "
            "string, and a value of another shape addresses nothing.",
        )
    return stated


def _sheet() -> str:
    """The spreadsheet's own identifier.

    ⛔ Read and never reported. § 28 keeps a private value out of every report,
    so this reaches the request's URL and nothing else -- which is why `_shown`
    below quotes a call without it and why `locate` answers with a tab and a row.
    """
    return _configured(SHEET, "spreadsheet to address")


def _tab() -> str:
    return _configured(TAB, "tab to put a row in")


def _columns() -> dict[str, str]:
    """The project's own header word per role, refused rather than part-read.

    ⛔ All three or none. A mapping missing one role cannot address three cells,
    and the one direction this must not take is resolving the two it has and
    writing the third wherever: § 26's rule, and the failure it names is a figure
    in the description column reading as a run that worked.
    """
    if _bound is None:
        raise port.ConfigError(
            _spec().name,
            "was asked for an operation before the port bound a configuration to "
            "it. Every operation is reached through `Port.invoke`, which binds "
            "first; a direct call bypasses the one place the project is stated.",
        )
    stated = _bound.get(_key(COLUMNS))
    if not isinstance(stated, dict) or not stated:
        raise port.ConfigError(
            _key(COLUMNS),
            f"is {stated!r}, and this kind is addressed by a mapping from each of "
            f"{', '.join(f'`{role}`' for role in ROLES)} to the header word that "
            "column carries in the sheet. § 26 makes the sheet's shape the "
            "project's, so there is no layout to fall back to.",
        )
    missing = [role for role in ROLES if not str(stated.get(role) or "").strip()]
    if missing:
        raise port.ConfigError(
            _key(COLUMNS),
            f"states no header word for {', '.join(f'`{role}`' for role in missing)}, "
            "so this kind cannot address that column. A mapping short of a role is "
            "not a narrower mapping -- it is one whose missing column a write would "
            "have to choose, which § 26 forbids outright.",
        )
    unknown = sorted(set(stated) - set(ROLES))
    if unknown:
        raise port.ConfigError(
            _key(COLUMNS),
            f"carries {', '.join(f'`{role}`' for role in unknown)}, which is no "
            f"role § 26 states. The roles are the surface's closed list "
            f"({', '.join(f'`{role}`' for role in ROLES)}) and the words beside "
            "them are the project's; a fourth role is a surface change rather "
            "than a key a project may add.",
        )
    return {role: str(stated[role]).strip() for role in ROLES}


def _credentials() -> str:
    """The authorisation header value, from the environment.

    ⛔ A failure rather than an absence, which is § 3's rule the tracker
    implementations are already held to: a shell holding no token is a store that
    cannot be reached, never a capability this kind lacks.
    """
    token = os.environ.get(TOKEN_VARIABLE)
    if not token:
        raise port.HostUnavailable(
            f"the shell holds no `{TOKEN_VARIABLE}`, so no call to this "
            "spreadsheet could be made. § 14 states that the project names the "
            "variable in `environment.inherits` rather than carrying a value, and "
            "§ 26 declares no key for a credential at all."
        )
    return f"Bearer {token}"


def _day(day: str) -> str:
    """The day as this store writes it, refusing anything else.

    ⛔ Parsed rather than interpolated. A caller handing over `2026-1-5`, a
    timestamp or a word would otherwise be written into a date cell no later read
    places -- an entry recorded and permanently invisible, which is the one
    failure a store silently has.
    """
    try:
        return datetime.date.fromisoformat(str(day)).strftime(DAY)
    except ValueError:
        raise port.ConfigError(
            _operations("read_day"),
            f"was given {day!r} as a day, which is not written `{DAY}`. An entry "
            "is addressed by the day § 9 measured, and a day this store cannot "
            "write would land in a cell nothing later reads.",
        ) from None


def _placed(cell) -> str | None:
    """The day a date cell states, where this store could have written it.

    ⛔ Held to the **writer's** own spelling and not to what a date parser
    accepts, which is the file kind's rule beside its own file names:
    `date.fromisoformat` takes `20260304` and `2026-W10-1`, neither of which this
    store ever writes, and a cell normalising to a different day would have the
    read looking for a row that is not there.

    ⚠️ `None` for a numeric cell too, and that is the stated limit rather than an
    oversight -- the module docstring says why a serial number is not placed.
    """
    if not isinstance(cell, str):
        return None
    named = cell.strip()
    try:
        day = datetime.date.fromisoformat(named)
    except ValueError:
        return None
    return day.strftime(DAY) if day.strftime(DAY) == named else None


# --- the one seam -----------------------------------------------------------


def _shown(method: str, path: str, params: dict | None = None) -> str:
    """One call as a person could re-run it, carrying neither secret nor address.

    ⛔ Every failure below quotes the call, and on this store **both** things § 14
    and § 28 keep out of a report would otherwise be in that string: the token
    travels in a header, and the spreadsheet's identifier is in the URL's path.
    So what is quoted is the method and the part of the path after the sheet --
    which is the range, the tab and the operation, and is what tells somebody
    what was asked.
    """
    query = urllib.parse.urlencode(params or {}, doseq=True)
    return f"{method} …/{path.lstrip('/')}" + (f"?{query}" if query else "")


def _urlopen_request(
    method: str,
    path: str,
    params: dict | None = None,
    body: dict | None = None,
    *,
    sheet: str = "",
    auth: str = "",
) -> tuple[int, str]:
    """One HTTP call, answering with its status rather than raising on one.

    ⛔ The status is **in the answer**, which is what lets a caller tell a body,
    the host's own `404` and a call that never reached the host apart without a
    second path that bypasses the first.

    ⛔ **The address and the credential are handed in, not resolved here.** This
    function is a *seam*, so a guard inside it is a guard every other transport
    walks past -- the lesson the tracker implementations record, and the reason
    `_call` above resolves both before anything is sent.
    """
    query = urllib.parse.urlencode(params or {}, doseq=True)
    url = f"{API}/{urllib.parse.quote(sheet, safe='')}/{path.lstrip('/')}"
    url += f"?{query}" if query else ""
    data = None if body is None else json.dumps(body).encode("utf-8")
    request = urllib.request.Request(url, data=data, method=method)
    request.add_header("Authorization", auth)
    request.add_header("Accept", "application/json")
    if data is not None:
        request.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT) as answer:
            return answer.status, answer.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as error:
        # The host answered, and its answer is the status. The body is read
        # because this host explains a refusal in it -- which range was rejected,
        # which tab is not there -- and that text is what a failure quotes.
        return error.code, error.read().decode("utf-8", "replace")
    except urllib.error.URLError as error:
        return UNREACHED, f"{type(error.reason).__name__}: {error.reason}"
    except (TimeoutError, socket.timeout):
        return UNREACHED, f"timed out after {TIMEOUT}s"


# The one seam. ⛔ Named rather than left as a call this module makes directly:
# what earns a test here is a parse, a column resolution or a guard over this
# host's answers, and every one of those is unreachable from a suite that cannot
# answer as the host. Rebound for the length of a case and restored, never for a
# process.
TRANSPORT = _urlopen_request


def _call(method: str, path: str, *, params: dict | None = None, body: dict | None = None):
    """One host call whose answer is a body, with every other outcome a failure.

    ⛔ `port.HostUnavailable` rather than a class of this module's: the port turns
    it into a `failed` outcome, and a role must be able to tell a broken call from
    a missing capability without knowing which store answered.
    """
    sheet, auth = _sheet(), _credentials()
    shown = _shown(method, path, params)
    status, text = TRANSPORT(method, path, params, body, sheet=sheet, auth=auth)
    if status == UNREACHED:
        raise port.HostUnavailable(f"`{shown}` never reached the host: {text}")
    if status == RATE_LIMITED:
        raise port.HostUnavailable(
            f"`{shown}` was rate limited by the host ({text.strip() or 'no body'}). "
            "That is this credential's own budget rather than anything about the "
            "day, and a role must not read it as a store with nothing in it."
        )
    if status in UNAUTHORISED:
        raise port.HostUnavailable(
            f"`{shown}` was refused as unauthorised (HTTP {status}). On this host "
            "that is one answer for two facts -- the token does not carry the "
            "scope, or this credential cannot see the spreadsheet -- and neither "
            "is a period nobody worked."
        )
    if status == NOT_FOUND:
        raise port.HostUnavailable(
            f"`{shown}` answered {NOT_FOUND}. The spreadsheet or the tab is not "
            "there, or is not visible to this credential; § 26 holds a store that "
            "cannot be reached apart from a store with nothing in it, so this is "
            "never an empty period."
        )
    if status >= 400:
        raise port.HostUnavailable(
            f"`{shown}` failed with HTTP {status}: {text.strip() or 'no body'}"
        )
    if not text.strip():
        # ⚠️ An answer rather than a fault: this host answers a write with a
        # summary body, and parsing an empty one to `None` would have the next
        # `.get` raise where an outcome belongs.
        return None
    try:
        return json.loads(text)
    except ValueError as error:
        raise port.HostUnavailable(
            f"`{shown}` answered something that is not JSON ({error}), so the "
            "answer could not be read at all -- which is not the same as its "
            "being empty."
        ) from None


# --- the tab, read once per operation ---------------------------------------


def _a1(tab: str, span: str = "") -> str:
    """One A1 range naming a tab, with the tab's own quoting.

    ⛔ A tab's name may carry a space, a quote or an exclamation mark, each of
    which A1 notation reads as syntax. Single-quoting it and doubling any quote
    inside is this notation's own escape, and a tab passed through unquoted is a
    range the host either refuses or resolves to a different tab.
    """
    quoted = "'" + tab.replace("'", "''") + "'"
    return f"{quoted}!{span}" if span else quoted


class Grid:
    """One read of the tab: its header row, its rows, and the resolved columns.

    ⛔ **Read once per operation and never cached across calls.** Two sessions of
    one project share this sheet, so a grid held between operations is a grid that
    says a day is free after somebody else recorded it -- which is the second row
    `append_day` exists to report.
    """

    # The header row is the tab's first row. ⚠️ Fixed rather than configured: a
    # sheet whose words are not in the first row is a sheet this kind refuses by
    # name through the resolution below, which is the refusal § 26 asks for, and a
    # configured header offset would be a fourth key for a layout the mapping
    # already addresses.
    HEADER = 0

    def __init__(self, rows: list[list], columns: dict[str, str], tab: str):
        self.rows = rows
        self.tab = tab
        self.header = rows[self.HEADER] if rows else []
        self.at = _resolve(self.header, columns, tab)
        self.body = rows[self.HEADER + 1:]

    def cell(self, row: list, role: str):
        """One cell of a row, or `None` where the row is short of it.

        ⚠️ This host truncates a row at its last non-empty cell, so a row whose
        description is blank comes back two cells long. A short row is ordinary
        and is not a row this kind cannot read.
        """
        index = self.at[role]
        return row[index] if index < len(row) else None

    def rows_for(self, day: str) -> list[tuple[int, list]]:
        """Every row whose date cell places that day, with its own row number.

        ⛔ Every one and not the first. Two rows for one day is the failure this
        kind can only report, so whatever finds a day has to see both.

        ⚠️ The number is the sheet's own, counting from one and including the
        header, because that is what somebody reads off the left-hand margin.
        """
        return [
            (index + self.HEADER + 2, row)
            for index, row in enumerate(self.body)
            if _placed(self.cell(row, DATE)) == day
        ]


def _resolve(header: list, columns: dict[str, str], tab: str) -> dict[str, int]:
    """Which column each role sits in, refusing every way that cannot be answered.

    ⛔ Three refusals and no fourth outcome, each naming the key: a word the sheet
    does not carry, a word two of its columns carry, and two roles landing on one
    column. § 26's rule, and the direction every one of them errs in is *refuse*
    rather than *write into a default column*.

    ⚠️ Matched case-insensitively after stripping, which widens what resolves
    without widening what is accepted: an ambiguity the looser match creates is
    the second refusal below rather than a column picked out of two.
    """
    words = [str(cell).strip().casefold() for cell in header]
    at: dict[str, int] = {}
    for role, word in columns.items():
        wanted = word.casefold()
        found = [index for index, cell in enumerate(words) if cell == wanted]
        if not found:
            raise port.ConfigError(
                _key(COLUMNS),
                f"maps `{role}` to {word!r}, and the header row of tab "
                f"{tab!r} carries no such column (it carries "
                f"{', '.join(repr(str(cell)) for cell in header) or 'nothing'}). "
                "§ 26 refuses a sheet whose columns do not match what is "
                "configured rather than writing into whichever cell is there.",
            )
        if len(found) > 1:
            raise port.ConfigError(
                _key(COLUMNS),
                f"maps `{role}` to {word!r}, which the header row of tab "
                f"{tab!r} carries in {len(found)} columns. Which of them holds "
                "the day's value cannot be answered, and a write that picked one "
                "would put the figure in a column nothing reads back.",
            )
        at[role] = found[0]
    taken: dict[int, str] = {}
    for role in ROLES:
        other = taken.get(at[role])
        if other is not None:
            raise port.ConfigError(
                _key(COLUMNS),
                f"maps `{other}` and `{role}` onto one column of tab {tab!r} "
                f"({columns[other]!r} and {columns[role]!r}). An entry occupies "
                "three cells, so two roles on one column is a mapping that loses "
                "one of § 9's two values at every write.",
            )
        taken[at[role]] = role
    return at


def _grid() -> Grid:
    """The tab as it stands, with its columns resolved.

    ⛔ The columns and the tab are read **before** the call, so a mapping that
    cannot resolve and a tab that is not stated are refusals this adapter makes
    rather than requests it sends.
    """
    tab, columns = _tab(), _columns()
    # ⚠️ Formulas rather than values, which is the rule in both directions: what
    # is wanted is what somebody entered, so a summing cell arrives as its own
    # source and is reported unreadable instead of answering with a total. ⛔ And
    # rows rather than columns, because a row is the entry.
    answer = _call(
        "GET",
        f"values/{urllib.parse.quote(_a1(tab), safe='')}",
        params={"valueRenderOption": "FORMULA", "majorDimension": "ROWS"},
    ) or {}
    rows = answer.get("values")
    if rows is None:
        # ⚠️ A tab nobody has written to yet answers with no `values` key at all.
        # That is a store with nothing in it, which § 26 holds apart from a store
        # that could not be reached -- and the unreachable arm has already raised
        # in `_call` above.
        rows = []
    if not isinstance(rows, list):
        raise port.HostUnavailable(
            f"the host answered about tab {tab!r} with {type(rows).__name__} "
            "where a list of rows belongs, so the tab could not be read at all -- "
            "which is not the same as its being empty."
        )
    normalised = [row if isinstance(row, list) else [row] for row in rows]
    if not normalised:
        raise port.ConfigError(
            _key(COLUMNS),
            f"cannot be resolved against tab {tab!r}, which holds no header row "
            "at all. § 26 makes the sheet's shape the project's and the mapping "
            "is read against that shape, so an empty tab is a sheet this kind "
            "refuses rather than one it lays out.",
        )
    return Grid(normalised, columns, tab)


def _render(day: str, hours, description: str, operation: str) -> list:
    """One entry's three cells, refusing hours this store could not read back.

    ⛔ Held to `_WRITABLE_HOURS`'s own grammar rather than to a type, which is the
    file kind's rule and the same measured failure: a negative, an exponent, a
    comma for a decimal point or anything a caller passes as text all format
    perfectly well and then read back as a row present with no hours.

    ⛔ **And the description is held to not opening a formula.** A cell beginning
    `=` is a formula to this host whatever the write asked for on the hours, and a
    description a person pasted a leading `=` into would be stored as one -- read
    back as a cell this kind cannot place and, where the sheet can evaluate it,
    as a value nobody wrote.
    """
    written = f"{hours}"
    if not _WRITABLE_HOURS.match(written):
        raise port.ConfigError(
            _operations(operation),
            f"was given {hours!r} as the day's hours, which this store cannot "
            "read back: it writes and reads a cell carrying a number with an "
            "optional decimal part. An entry written with anything else is one "
            "this store would report as unreadable for ever after reporting the "
            "day recorded.",
        )
    text = str(description).strip()
    if text.startswith(_FORMULA):
        raise port.ConfigError(
            _operations(operation),
            f"was given a description opening {_FORMULA!r}, which this host "
            "stores as a formula. § 26 has this kind write values and never "
            "formulas, and a described day whose cell is a formula is a cell "
            "nobody can read back as what was written.",
        )
    return [day, written, text]


def _row_values(grid: Grid, cells: list, over: list | None = None) -> list:
    """The entry's three cells placed in the sheet's own column order.

    ⛔ Padded to the rightmost mapped column and no further. A row this kind
    writes carries nothing in a column the project keeps for itself -- a project
    code, a ticket -- and a write that ran to the end of the header would blank
    every one of them.

    ⛔ **And a column between two mapped ones keeps what it holds.** `over` is the
    row being rebuilt, and without it every unmapped cell inside the written span
    would go out as empty: the mapped columns are not contiguous in a sheet
    somebody already keeps, so a rebuild would blank the project's own column for
    the one day it rebuilt. ⚠️ Absent on an append, where there is no row yet and
    an empty cell is what is there.
    """
    width = max(grid.at[role] for role in ROLES) + 1
    row: list = list(over or [])[:width]
    row += [""] * (width - len(row))
    for role, value in zip(ROLES, cells):
        row[grid.at[role]] = value
    return row


# --- the operations ---------------------------------------------------------
#
# Each takes what the day-log role already has and returns what it can say out
# loud. None of them reads a capability: being here *is* the declaration (§ 3).


def read_day(day: str) -> dict | None:
    """The entry recorded for that day, or `None` where there is none.

    ⛔ `None` only for a day no row places. A row that is there and whose hours
    cannot be read comes back **with `hours: None`** and the cell's own text,
    because an unreadable entry is not an absent one -- and a caller that read the
    two the same way would append beside a row it could not parse.

    ⛔ **Two rows for one day is reported here rather than resolved.** This kind
    cannot hold the sheet against a second writer, so the read is what sees it:
    `rows` carries both numbers and `hours` is `None`, which is the one answer
    that is neither a figure nobody wrote nor a day that looks free.
    """
    wanted = _day(day)
    grid = _grid()
    found = grid.rows_for(wanted)
    if not found:
        return None
    numbers = [number for number, _ in found]
    if len(found) > 1:
        return {
            "day": wanted,
            "tab": grid.tab,
            "rows": numbers,
            "hours": None,
            "description": None,
            "unreadable": (
                f"rows {', '.join(str(number) for number in numbers)} of tab "
                f"{grid.tab!r} each claim {wanted}, so this day's hours are not "
                "one figure. Nothing holds a spreadsheet against two writers "
                "(§ 26); a second row is a person's to remove."
            ),
        }
    number, row = found[0]
    cell = grid.cell(row, HOURS)
    hours, unreadable = _hours_in(cell, number, grid.tab)
    description = grid.cell(row, DESCRIPTION)
    return {
        "day": wanted,
        "tab": grid.tab,
        "rows": numbers,
        "hours": hours,
        "description": "" if description is None else str(description),
        "unreadable": unreadable,
    }


def _hours_in(cell, number: int, tab: str) -> tuple[float | None, str | None]:
    """A cell's hours, or why this store cannot read them.

    ⛔ Three ways a cell is unreadable and none of them is zero hours: a formula,
    text no number parses out of, and nothing there at all. § 26 states that a day
    the store holds and cannot read is reported as that, never as zero -- the
    direction a billing consumer pays for.
    """
    if cell is None or (isinstance(cell, str) and not cell.strip()):
        return None, (
            f"row {number} of tab {tab!r} places the day and carries no hours "
            "cell, so this day's figure is absent rather than zero"
        )
    if isinstance(cell, str) and cell.strip().startswith(_FORMULA):
        return None, (
            f"row {number} of tab {tab!r} carries {cell.strip()!r} in the hours "
            "column, which is a formula. § 26 has this kind read what was "
            "entered: a formula is a second statement of the period and its "
            "displayed total is not this day's recorded hours"
        )
    if isinstance(cell, bool):
        # ⚠️ Before the numeric arm, because `bool` is an `int` in this language
        # and `True` would otherwise read as one hour.
        return None, (
            f"row {number} of tab {tab!r} carries {cell!r} in the hours column, "
            "which is not a figure this store wrote"
        )
    if isinstance(cell, (int, float)):
        return float(cell), None
    written = str(cell).strip()
    if not _WRITABLE_HOURS.match(written):
        return None, (
            f"row {number} of tab {tab!r} carries {written!r} in the hours "
            "column, which this store cannot read as a number with an optional "
            "decimal part"
        )
    return float(written), None


def append_day(day: str, hours, description: str) -> dict:
    """Record one day's two values, refusing a day already recorded.

    ⛔ **The read before and the read after are both load-bearing, and for
    different reasons.** The one before is § 26's rule that `read_day` decides
    which write is asked for. The one after is this kind's own: there is no
    exclusive create on a spreadsheet, so two sessions can each see a free day and
    each append -- and the only honest thing available is to look, and to **fail**
    naming both rows where there are two.

    ⚠️ Which makes the failure a report about the store rather than about this
    call: the row this call wrote is there, and so is somebody else's. A person
    removes one.
    """
    wanted = _day(day)
    grid = _grid()
    standing = grid.rows_for(wanted)
    if standing:
        raise port.ConfigError(
            _operations("append_day"),
            f"was asked to record {wanted}, which row "
            f"{', '.join(str(number) for number, _ in standing)} of tab "
            f"{grid.tab!r} already holds. § 26 has `read_day` decide which write "
            "is asked for, and a row appended beside one that is there is two "
            "rows claiming the same hours. Ask for a replacement.",
        )
    cells = _render(wanted, hours, description, "append_day")
    _call(
        "POST",
        f"values/{urllib.parse.quote(_a1(grid.tab), safe='')}:append",
        params={"valueInputOption": "RAW", "insertDataOption": "INSERT_ROWS"},
        body={"values": [_row_values(grid, cells)]},
    )
    after = _grid().rows_for(wanted)
    numbers = [number for number, _ in after]
    if len(after) != 1:
        raise port.HostUnavailable(
            f"{wanted} was appended to tab {grid.tab!r} and reads back as "
            f"{len(after)} row(s)"
            + (f" ({', '.join(str(number) for number in numbers)})" if numbers else "")
            + ". Nothing holds a spreadsheet against two writers, so a second "
            "session recording the same day lands beside this one -- and one of "
            "them is a person's to remove before any period is read."
        )
    return {"day": wanted, "tab": grid.tab, "rows": numbers, "hours": float(hours)}


def replace_day(day: str, hours, description: str) -> dict:
    """Rebuild the day's entry whole, over the row that places it.

    ⛔ Whole and never a patch: all three cells are written every time, so a
    rebuild with a shorter description leaves no tail of the longer one behind.
    ⚠️ **Whole means the entry's three cells and not the row**, which is the one
    place this differs from the file kind: a project's own column beside them is
    not part of § 9's entry, and blanking it would be a rebuild writing over
    something no role recorded.

    ⛔ **A day no row places is appended rather than refused**, which is this
    port's own shape one operation over: `read_day` decides which write a role
    asks for, and a replacement asked for a day that is not there is a day to
    record rather than an error -- the file kind writes its file either way for
    the same reason.

    ⛔ **And two rows for one day is refused rather than rebuilt.** Which of them
    is the entry cannot be answered here, so rewriting one would leave the other
    standing and report the day rebuilt.
    """
    wanted = _day(day)
    grid = _grid()
    found = grid.rows_for(wanted)
    if len(found) > 1:
        raise port.ConfigError(
            _operations("replace_day"),
            f"was asked to rebuild {wanted}, which rows "
            f"{', '.join(str(number) for number, _ in found)} of tab "
            f"{grid.tab!r} each claim. Which of them is the entry cannot be "
            "answered, and rewriting one would leave the other standing while "
            "reporting the day rebuilt. A person removes one.",
        )
    if not found:
        # ⚠️ Through the append rather than beside it, which re-reads the tab: a
        # second session that recorded this day between the two reads is refused
        # there, where a write composed here would have put a row beside theirs.
        return append_day(day, hours, description)
    cells = _render(wanted, hours, description, "replace_day")
    number, standing = found[0]
    # ⛔ The range is the mapped span and the values are sliced to match it. The
    # span starts at the leftmost mapped column, so a row padded from column A
    # and sent whole would be written one or more cells to the right of where it
    # belongs -- and a project's own column would get a cell of § 9's entry.
    offset = min(grid.at[role] for role in ROLES)
    span = (
        f"{_column_name(offset)}{number}:"
        f"{_column_name(max(grid.at[role] for role in ROLES))}{number}"
    )
    values = _row_values(grid, cells, over=standing)
    _call(
        "PUT",
        f"values/{urllib.parse.quote(_a1(grid.tab, span), safe='')}",
        params={"valueInputOption": "RAW"},
        body={"values": [values[offset:]]},
    )
    return {"day": wanted, "tab": grid.tab, "rows": [number], "hours": float(hours)}


def _column_name(index: int) -> str:
    """A zero-based column index as A1 notation names it.

    ⛔ Base twenty-six with no zero digit, which is why this is a loop and not a
    single division: column 26 is `AA` rather than `A0`, and the obvious
    arithmetic puts the twenty-seventh column at `BA`.
    """
    name = ""
    number = index + 1
    while number:
        number, remainder = divmod(number - 1, 26)
        name = chr(ord("A") + remainder) + name
    return name


def read_hours(first: str, last: str) -> dict:
    """Each day's stated hours between two days, both ends included.

    ⛔ Per day and never a total, with the days this store holds and could not
    read named beside the ones it could. § 26's rule: a consumer that summed what
    it could parse would under-report a period and nothing would say so.

    ⛔ `unreadable` is keyed by **day** and holds only days inside the period, so a
    consumer may read it as *of the period I was asked about, these I could not
    read*. A row this store cannot place in a day at all goes in `unplaced`, keyed
    by its row number: it may be the entry a period is missing, so it is reported
    rather than swept past, but it cannot be known to fall inside the range.
    """
    start, end = _day(first), _day(last)
    if start > end:
        raise port.ConfigError(
            _operations("read_hours"),
            f"was asked for {start} to {end}, which ends before it begins. A "
            "period read backwards would come back empty, which reads exactly "
            "like a period nobody worked.",
        )
    grid = _grid()
    hours: dict[str, float] = {}
    unreadable: dict[str, str] = {}
    unplaced: dict[str, str] = {}
    # ⛔ Collected per day before anything is answered, because a second row for a
    # day is what makes that day unreadable -- and a loop that wrote each figure
    # as it found it would answer with whichever row came last.
    seen: dict[str, list[tuple[int, list]]] = {}
    for index, row in enumerate(grid.body):
        number = index + Grid.HEADER + 2
        cell = grid.cell(row, DATE)
        day = _placed(cell)
        if day is None:
            if all(
                value is None or (isinstance(value, str) and not value.strip())
                for value in row
            ):
                # ⚠️ A wholly empty row is not a row that could not be placed. A
                # person leaves a blank line between months, and reporting each
                # one would make every period come back partly unreadable for
                # ever -- which § 26 names as the failure that has a consumer
                # stopping on an answer that was complete.
                continue
            unplaced[str(number)] = (
                f"the date cell carries {cell!r}, which is no day this store "
                f"writes (`{DAY}`)"
            )
            continue
        seen.setdefault(day, []).append((number, row))
    for day, rows in sorted(seen.items()):
        if day < start or day > end:
            continue
        if len(rows) > 1:
            unreadable[day] = (
                f"rows {', '.join(str(number) for number, _ in rows)} of tab "
                f"{grid.tab!r} each claim this day, so its hours are not one "
                "figure"
            )
            continue
        number, row = rows[0]
        figure, why = _hours_in(grid.cell(row, HOURS), number, grid.tab)
        if figure is None:
            unreadable[day] = why
            continue
        hours[day] = figure
    return {
        "first": start,
        "last": end,
        "hours": hours,
        "unreadable": unreadable,
        "unplaced": unplaced,
    }


def locate(day: str) -> str:
    """Where that day's entry is, named as the place inside the store.

    ⛔ **The tab and the row, never the spreadsheet's identifier.** That
    identifier is marked `# private` and § 28 keeps a private value out of every
    report; a role says this out loud, and a report goes somewhere the
    configuration does not. What a tab and a row give whoever can already reach
    the sheet is the entry; what they give whoever cannot is nothing.

    ⛔ Writes nothing and creates nothing. A role says this out loud, which is a
    read.
    """
    wanted = _day(day)
    grid = _grid()
    found = grid.rows_for(wanted)
    where = f"tab {grid.tab!r}"
    if not found:
        return f"{where}, no row for {wanted} yet"
    if len(found) > 1:
        return (
            f"{where}, rows {', '.join(str(number) for number, _ in found)} — "
            f"two rows claim {wanted}"
        )
    return f"{where}, row {found[0][0]}"


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
    absent case, the writer refusal. These are this store's own: the column
    resolution and each of its refusals, values rather than formulas in both
    directions, a rebuild that writes three cells and no more, the second row
    nothing can hold out, and a row this kind cannot place.
    """
    from destinations import _google_sheet_suite as suite

    return suite.self_test()


if __name__ == "__main__":
    sys.exit(self_test())
