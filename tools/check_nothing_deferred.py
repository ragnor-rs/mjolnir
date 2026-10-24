#!/usr/bin/env python3
"""Hold a pull request to the rule that nothing is deferred.

The surface states it: a work item is delivered whole, a role that reaches a
question it cannot answer asks rather than noting it, and no change merges with
an open item against it -- not a review finding, not a still-open list in a
body, not a deferral marker, not a paragraph of known costs. The part this
script exists for is the next sentence of that rule: **the statement is read
back, never asserted.** A pull request claiming completeness in prose is the
same claim the defect this rule is about already makes.

So the items are counted where they were raised. Two places carry them and both
are read here:

  * **the body**, which states its open items in a section of its own, and
  * **the threads on the change**, whose resolution the host records rather
    than the author describing it.

That second one is why this gate holds a token scope where its siblings hold
none. What the scope is, what it buys, and what it measurably did not buy on
this repository's history are stated once, in
docs/single-source-of-truth.md#the-gate-on-the-change-nothing-is-deferred, and
are not repeated here or in the workflow file.

Measured on this repository, which is what made the rule procedure: a pull
request merged carrying its own list of unresolved items in its body and review
findings answered nowhere. Every one had been surfaced, written down, and then
shipped -- the deferral was visible and nothing refused it.

What it hardcodes is grammar, in the same sense its siblings do: the heading a
body states its open items under, the form of a `none` answer, the marker
words, and the shape of an unticked list item. ⛔ **The first two stay here,
and that is a ruling rather than an omission.** The configured body-section
facet beside this one is a list a project may stop stating, and this section
is one no project may stop carrying -- so carrying its heading there would make
the rule configurable, which the rule's own precedence refuses. ⚠️ **What is
shared is the grammar and not the heading**: how a section is found in a body
is the toolkit's one implementation, imported below, and both gates read a
section the same way.

Usage:
    check_nothing_deferred.py              hold this change to the rule
    check_nothing_deferred.py --self-test  assert every check reddens on each of
                                           its planted violations, then hold the
                                           change
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request

# The toolkit's own body-section grammar, imported rather than re-implemented.
# ⚠️ The path is derived from this file's own location, so a run from a
# worktree reads that tree's module rather than the primary checkout's -- the
# failure that otherwise prints a convincing verdict about a file nobody is
# editing.
_PLUGIN_SCRIPTS = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "plugins", "mjolnir", "scripts",
)
if _PLUGIN_SCRIPTS not in sys.path:
    sys.path.insert(0, _PLUGIN_SCRIPTS)

import check_body_sections as body_sections  # noqa: E402

# --- the grammar -----------------------------------------------------------
#
# Form, not content. Every one of these is a shape a body or a diff has, and
# none of them is a fact about this project.

# The section a body states its open items under, and the answer that closes
# it. An ATX heading at any level, matched on its text alone and without regard
# to case, because the level and the casing a body puts it at are formatting.
# The spellings below are what a refusal quotes back, so what the gate asks for
# and what the documents state are one string rather than two.
#
# ⚠️ This is a grammar the gate publishes, not a property it derives, so it
# reddens on a reword -- `Open questions` is not this heading and `Nothing
# outstanding.` is not this answer. That is why it is a *forbidding* check in
# the document's table rather than a computed one, and why making the two
# strings configuration, in the repository's own language, is #51's.
HEADING_TEXT = "Open items"
NO_OPEN_ITEMS_ANSWER = "None."
OPEN_ITEMS = HEADING_TEXT.lower()
NO_OPEN_ITEMS = {NO_OPEN_ITEMS_ANSWER.lower(), NO_OPEN_ITEMS_ANSWER.lower().rstrip(".")}

HEADING = re.compile(r"^\s{0,3}(#{1,6})\s+(.*?)\s*#*\s*$")
UNTICKED = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+\[ \]\s*(?P<text>.*)")

# A line under the heading that carries no claim: blank, a horizontal rule, a
# single-line comment the host does not render. Stripping these is what lets a
# body answer `- None.` or close the section with a rule and still be read as
# having answered, rather than as listing the rule as an open item.
NOISE = re.compile(r"^\s*(?:-{3,}|\*{3,}|_{3,}|<!--.*-->)?\s*$")
LIST_MARKER = re.compile(r"^(?:[-*+]|\d+[.)])\s+")

# A deferral marker, in the one form that is unambiguous: the word carrying a
# colon or an argument list. A bare mention -- `TODO` in a sentence about this
# rule, or in a comment quoting a status vocabulary -- is prose, and sweeping
# prose for these words would redden on a reworded sentence. `TODO` already
# occurs innocently in this tree for exactly that reason; the other two
# spellings occur nowhere, and carrying them costs nothing and covers the two
# markers a migrating project is most likely to arrive with.
MARKER = re.compile(r"\b(TODO|FIXME|XXX)\s*[:(]")

# A remedy with no owner, in prose. ⛔ Every form here names *who* is missing
# rather than *what* is: a line saying a thing is absent states a limit, and a
# line saying nobody owns the cure defers it. The counts that drew the line are
# in the check's own docstring.
#
# ⚠️ A closed list, which is the quoting weakness this repository rules out
# elsewhere, and safe in the direction that matters here: a reworded deferral
# passes and leaves a finding missed, never a finding invented -- and the finding
# missed is one the person reading the diff can still raise, while a false red
# hands back a change over the honest form of a sentence.
UNOWNED = re.compile(
    r"\bno(?:\s+\w+)?\s+item\s+owns\b"
    r"|\bnobody\s+owns\b|\bowned\s+by\s+(?:nobody|no\s?one)\b"
    r"|\bno\s+(?:item|issue|change|role)\s+(?:owns|carries)\s+(?:it|this|that)\b"
    r"|\bno(?:body| one) has (?:built|written|wired|carried) (?:it|this|that)\b"
    r"|\b(?:somebody|someone) (?:should|has to|will have to|would have to)\b"
    r"|\bis (?:left|parked) (?:to|for) (?:a )?"
    r"(?:later|future|another|somebody|someone|whoever)\b"
    r"|\b(?:a|the|some) (?:later|future) (?:item|change|pass) "
    r"(?:will|would|can|could) (?:carry|cover|do|fix)\b",
    re.I,
)

# Only added lines are read. A marker this change did not write is somebody
# else's item and not a reason to refuse this merge.
DIFF_ADDED = re.compile(r"^\+(?!\+\+)(?P<text>.*)$")

API = "https://api.github.com"
PAGE = 100

THREADS_QUERY = """
query($owner: String!, $name: String!, $number: Int!, $after: String) {
  repository(owner: $owner, name: $name) {
    pullRequest(number: $number) {
      body
      reviewThreads(first: 100, after: $after) {
        pageInfo { hasNextPage endCursor }
        nodes {
          isResolved
          isOutdated
          path
          line
          comments(first: 1) { nodes { body } }
        }
      }
    }
  }
}
"""


class Unreadable(Exception):
    """The change could not be read at all, which is not a verdict about it."""


# --- the change ------------------------------------------------------------


class Change:
    """One pull request, in memory, so a violation can be planted into it."""

    def __init__(self, number: int | None, body: str | None, threads: list[dict],
                 added: list[tuple[str, str]], unread: list[str] | None = None):
        self.number = number
        self.body = body
        self.threads = threads
        self.added = added
        # Files the host returned without a patch, so check 4 can report what
        # it did not read instead of reporting green over it.
        self.unread = list(unread or [])

    def copy(self) -> "Change":
        return Change(
            self.number,
            self.body,
            [dict(thread) for thread in self.threads],
            list(self.added),
            list(self.unread),
        )

    def sections(self, name: str) -> list[list[str]]:
        """Every section under the heading named, in document order.

        ⛔ **The grammar is the toolkit's and not a second copy of it.** What a
        body section is -- an ATX heading at any level, matched on its text
        alone, with fenced blocks skipped and every match returned rather than
        the first -- is one implementation, in the module this delegates to,
        and the reasons each of those rules exists are stated there. Two
        parsers for one grammar is the defect this repository deletes
        everywhere else, and the heading this gate reads is the heading that
        module's own gate reads.
        """
        if self.body is None:
            return []
        return body_sections.sections(self.body, name)


# --- reading the change off the host ---------------------------------------


def _token() -> str:
    """The automatic token in a run; the person's own when run by hand."""
    for name in ("GITHUB_TOKEN", "GH_TOKEN"):
        if os.environ.get(name):
            return os.environ[name]
    try:
        out = subprocess.run(
            ["gh", "auth", "token"], capture_output=True, text=True, check=True
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        raise Unreadable(
            "no token: set GITHUB_TOKEN, or authenticate the host's CLI. This gate reads "
            "the threads on the change, which needs read access to pull requests."
        ) from exc
    return out.stdout.strip()


def _request(url: str, token: str, payload: dict | None = None) -> tuple[dict | list, dict]:
    data = json.dumps(payload).encode() if payload is not None else None
    request = urllib.request.Request(
        url,
        data=data,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "Content-Type": "application/json",
            "User-Agent": "nothing-deferred",
        },
    )
    try:
        with urllib.request.urlopen(request) as response:
            return json.loads(response.read().decode()), dict(response.headers)
    except urllib.error.HTTPError as exc:
        raise Unreadable(f"{url}: the host answered {exc.code} {exc.reason}.") from exc
    except urllib.error.URLError as exc:
        raise Unreadable(f"{url}: the host could not be reached ({exc.reason}).") from exc


def _where() -> tuple[str, str, int]:
    """Which repository and which pull request, from the run or from the branch.

    In a run the event payload already names all three. By hand, the slug comes
    from this project's own configuration through the one reader -- never from
    the working directory, which § 1 of the surface forbids for the same reason
    -- and the number from the branch.
    """
    event = os.environ.get("GITHUB_EVENT_PATH")
    if event and os.path.exists(event):
        with open(event, encoding="utf-8") as handle:
            payload = json.load(handle)
        pull = payload.get("pull_request") or {}
        repository = payload.get("repository") or {}
        number = pull.get("number")
        owner = (repository.get("owner") or {}).get("login")
        name = repository.get("name")
        if not (number and owner and name):
            raise Unreadable(
                "the event payload names no pull request. This gate runs on pull requests, "
                "and a run that cannot name one has no answer about it."
            )
        return owner, name, int(number)

    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, os.path.join(root, "plugins", "mjolnir", "scripts"))
    try:
        import config as reader  # noqa: PLC0415  -- the one reader, not a second parser
    except ImportError as exc:
        raise Unreadable(f"the configuration reader could not be imported: {exc}") from exc
    try:
        configuration = reader.load(root)
        slug = configuration.get("host.repo")
        code_root = configuration.code_root
    except Exception as exc:  # the reader names the key it refused
        raise Unreadable(f"the configuration could not be read: {exc}") from exc
    if not slug or "/" not in slug:
        raise Unreadable("the configuration states no `host.repo`, so there is nothing to ask.")
    owner, _, name = slug.partition("/")

    # ⛔ The repository, the directory and the branch are each named rather
    # than inherited. § 1 forbids inferring the code root, and a `gh` call
    # that takes the working directory's remote reads the wrong repository on
    # a fork -- a verdict about a different change, in the direction that
    # answers. ⚠️ The branch has to be passed too: `pr view` infers it from the
    # checkout, and naming `--repo` is what turns that inference off, so the
    # two cannot both be left implicit and cannot both be named either.
    try:
        branch = subprocess.run(
            ["git", "-C", code_root, "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True, text=True, check=True,
        ).stdout.strip()
        out = subprocess.run(
            ["gh", "pr", "list", "--repo", slug, "--head", branch, "--state", "open",
             "--json", "number", "--jq", ".[0].number"],
            capture_output=True, text=True, check=True,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        raise Unreadable(
            f"the host could not be asked for a pull request on `{slug}`: {exc}"
        ) from exc
    if not out.stdout.strip():
        raise Unreadable(
            f"no open pull request for `{branch}` on `{slug}`. The rule is held against a "
            "pull request, so this check has no answer until one exists -- which is not "
            "the same as green."
        )
    return owner, name, int(out.stdout.strip())


def _threads(owner: str, name: str, number: int, token: str) -> tuple[str | None, list[dict]]:
    """Body and every thread, following the cursor.

    ⚠️ A first page is a ceiling. A review that ran long is exactly the change
    this gate is for, so stopping at the first hundred threads would go green
    on the pull requests that need it most.
    """
    body: str | None = None
    threads: list[dict] = []
    after = None
    while True:
        payload = {
            "query": THREADS_QUERY,
            "variables": {"owner": owner, "name": name, "number": number, "after": after},
        }
        answer, _ = _request(f"{API}/graphql", token, payload)
        if answer.get("errors"):
            raise Unreadable(f"the host refused the query: {answer['errors']}")
        pull = (((answer.get("data") or {}).get("repository") or {}).get("pullRequest"))
        if pull is None:
            raise Unreadable(f"pull request {number} was not found.")
        body = pull.get("body")
        page = pull["reviewThreads"]
        for node in page["nodes"]:
            comments = (node.get("comments") or {}).get("nodes") or [{}]
            threads.append({
                "resolved": bool(node.get("isResolved")),
                "outdated": bool(node.get("isOutdated")),
                "path": node.get("path") or "the change",
                "line": node.get("line"),
                "first": " ".join((comments[0].get("body") or "").split()),
            })
        if not page["pageInfo"]["hasNextPage"]:
            return body, threads
        after = page["pageInfo"]["endCursor"]


# The host stops listing a change's files here, and a change that reaches it
# has files nothing read.
FILE_CEILING = 3000


def _added_whole(entry: dict) -> list[tuple[str, str]] | None:
    """Every line of an added file, from the checkout, or None if it is not one.

    ⛔ `status == "added"` is the whole of the licence. A file the host reports
    as modified has lines this change did not write, and reading it whole would
    hand somebody else's marker to this change — the one thing the added-lines
    rule exists to prevent. A file that is not in the tree, or is not text,
    answers None and stays unread rather than being read as empty.
    """
    if entry.get("status") != "added":
        return None
    path = entry.get("filename")
    if not path or not os.path.isfile(path):
        return None
    try:
        with open(path, encoding="utf-8") as handle:
            return [(path, line) for line in handle.read().splitlines()]
    except (OSError, UnicodeDecodeError):
        return None


def _added(owner: str, name: str, number: int,
           token: str) -> tuple[list[tuple[str, str]], list[str]]:
    """(path, added line) for every line this change writes, and what went unread.

    ⚠️ The host omits `patch` for a binary file, for a diff over its per-file
    size limit, and for everything past its file ceiling. Those files are
    returned as the second value rather than skipped: a marker in a file
    nothing read is not an absence of markers, and absence of signal is not an
    answer.

    ⛔ **With one exception, and it is exact rather than a relaxation.** Where
    the host says a file was **added** and supplies no patch for it, every line
    of that file in the checkout is a line this change writes — there is no
    earlier version for any of them to have come from. So the file is read from
    the tree and the answer is the same one the patch would have given, which
    is why this does not weaken the added-lines rule the way reading a
    *modified* file whole would. ⚠️ Measured on a change adding one module of
    some sixteen hundred lines: the host supplied no patch for it, and the gate
    reported a file nothing read on a change that had deferred nothing.
    """
    out: list[tuple[str, str]] = []
    unread: list[str] = []
    page = 1
    while True:
        files, _ = _request(
            f"{API}/repos/{owner}/{name}/pulls/{number}/files?per_page={PAGE}&page={page}", token
        )
        for entry in files:
            patch = entry.get("patch")
            if patch is None:
                whole = _added_whole(entry)
                if whole is None:
                    unread.append(entry["filename"])
                else:
                    out.extend(whole)
                continue
            for line in patch.splitlines():
                match = DIFF_ADDED.match(line)
                if match:
                    out.append((entry["filename"], match.group("text")))
        if len(files) < PAGE:
            return out, unread
        if page * PAGE >= FILE_CEILING:
            unread.append(
                f"everything past the host's {FILE_CEILING}-file ceiling"
            )
            return out, unread
        page += 1


def read_change() -> Change:
    owner, name, number = _where()
    token = _token()
    body, threads = _threads(owner, name, number, token)
    added, unread = _added(owner, name, number, token)
    return Change(number, body, threads, added, unread)


# --- the checks ------------------------------------------------------------
#
# Each returns a list of problems, and each has at least one planted violation
# below that it is asserted to go red on -- one per branch that does real work,
# because a plant that reddens a check by the wrong route proves nothing about
# the branch it was written for.


def check_the_change_was_read(change: Change) -> list[str]:
    """⛔ The number cannot be checked here: `_where()` returns an int or raises.

    An unresolvable pull request is reported by the `Unreadable` handler in
    `main()`, which is the only branch that can carry it, and a clause here
    for the same fact would be a second mechanism with the live one dead.
    What is reachable is an empty body -- the host returns `""` over GraphQL,
    never null -- and that is what this holds.
    """
    if not change.body:
        return [
            "the pull request has no body at all. A change states what it carries; an "
            "empty body states nothing, and cannot state that nothing is open."
        ]
    return []


def check_the_body_states_its_open_items(change: Change) -> list[str]:
    if not change.body:
        return []
    found = change.sections(OPEN_ITEMS)
    if not found:
        return [
            f"the body carries no `{HEADING_TEXT}` section. The statement that every item "
            "raised against this change is resolved is what the gate reads back, so a body "
            "that does not make it is not ready — write the section, and answer it "
            f"`{NO_OPEN_ITEMS_ANSWER}` where nothing is open."
        ]
    if len(found) > 1:
        return [
            f"the body carries {len(found)} `{HEADING_TEXT}` sections. One of them answers and "
            "the others are unread, whichever rule picks — so a body that answers once and "
            "lists items further down reads as answered. State it once."
        ]
    content = [line.rstrip() for line in found[0] if not NOISE.match(line)]
    text = " ".join(" ".join(content).split())
    bare = LIST_MARKER.sub("", text).strip("*_` ").strip()
    if bare.lower() in NO_OPEN_ITEMS:
        return []
    if not content:
        return [
            f"the body's `{HEADING_TEXT}` section is empty. An empty section is not an "
            f"answer: list what is open, or answer `{NO_OPEN_ITEMS_ANSWER}`."
        ]
    return [
        f"the body's `{HEADING_TEXT}` section carries {len(content)} line(s) that are not "
        f"the answer `{NO_OPEN_ITEMS_ANSWER}`, and no change merges with an open item "
        "against it:"
    ] + [f"    {line.strip()}" for line in content]


def check_no_thread_is_unresolved(change: Change) -> list[str]:
    problems = []
    for thread in change.threads:
        if thread["resolved"]:
            continue
        where = thread["path"]
        if thread.get("line"):
            where = f"{where}:{thread['line']}"
        stale = " (on an outdated diff, and still raised)" if thread["outdated"] else ""
        problems.append(f"{where}{stale}: unresolved — {thread['first'][:120]}")
    return problems


def check_no_unticked_item_in_the_body(change: Change) -> list[str]:
    """Fenced blocks are skipped here too, and for the same reason as above:
    a body illustrating the shape this gate forbids must not be refused for
    illustrating it."""
    problems = []
    fenced = False
    for line in (change.body or "").splitlines():
        if line.lstrip().startswith("```"):
            fenced = not fenced
            continue
        if fenced:
            continue
        match = UNTICKED.match(line)
        if match:
            problems.append(
                f"the body carries an unticked item: {match.group('text').strip()[:120]}"
            )
    return problems


def check_no_unowned_remedy_added(change: Change) -> list[str]:
    """Work a line names and nobody owns, anywhere in the diff.

    ⛔ The arm above reads a marker, which is a form a writer reaches for
    knowingly. This one reads the form the rule was measured escaping through:
    prose. A change whose `Open items` section read exactly `None.` and whose
    run of this script was green shipped a deferral as a clause in a document --
    *a carrier for the check, which no item owns today* -- which is work named,
    owned by nobody, and sitting where no gate looked.

    ⚠️ **The grammar is the unowned half and not the unfinished half.** Prose
    that merely says something is absent -- *not yet built*, *would need the
    credential grammar*, *still needs an answer* -- is this repository's ordinary
    way of stating a limit, and nine such lines were counted in tracked text
    before this arm was written. Sweeping those hands back a change for the
    honest form of the sentence. What reddens is a remedy with no owner, which is
    the half that defers.

    ⚠️ The remedy is usually **deletion** rather than filing: a cure nobody
    measured is not a measured gap, and a limit stated without one is the honest
    form of the same sentence.
    """
    problems = []
    for path, line in change.added:
        if path in EXEMPT:
            continue
        match = UNOWNED.search(line)
        if match:
            problems.append(
                f"{path}: this change adds work with no owner — {match.group(0).strip()!r} in "
                f"{line.strip()[:120]}"
            )
    return problems


def check_no_deferral_marker_added(change: Change) -> list[str]:
    problems = [
        f"{path}: the host supplied no patch for this file, so nothing below read it. "
        "A marker in a file nothing read is not an absence of markers."
        for path in change.unread
    ]
    for path, line in change.added:
        if path in EXEMPT:
            continue
        match = MARKER.search(line)
        if match:
            problems.append(
                f"{path}: this change adds a {match.group(1)} marker — {line.strip()[:120]}"
            )
    return problems


# The files that necessarily write the markers down, for the same reason this
# sweep exempts itself: a check that forbids a form has to spell that form out,
# and has to plant it to prove the arm fires. ⚠️ **The list is closed and short
# -- a marker in any other tool or script is read**, which `tools/` being where
# further scripts land makes load-bearing rather than theoretical. Both halves
# are asserted below: the whole-change fixture carries a marker in an exempt
# file and stays green, and a plant puts one in a sibling tool and reddens.
#
# ⛔ The second entry earned the exemption the same way the first did. Its arm
# holds a role's reply to naming no work the turn does not do, the marker is one
# of the forms it forbids, and the casing is its grammar -- `re.I` over the whole
# pattern matched the ordinary English noun, so a plant in the marker's own
# casing is what asserts the narrowing. Without the exemption that plant could
# not be written, and the arm would ship with nothing holding it.
EXEMPT = frozenset({
    "tools/" + os.path.basename(__file__),
    "plugins/mjolnir/scripts/check_reply_defers_nothing.py",
})


CHECKS = [
    ("the change was read", check_the_change_was_read),
    ("the body states its open items", check_the_body_states_its_open_items),
    ("no thread on the change is unresolved", check_no_thread_is_unresolved),
    ("no unticked item in the body", check_no_unticked_item_in_the_body),
    ("no deferral marker added by the change", check_no_deferral_marker_added),
    ("no work added with no owner", check_no_unowned_remedy_added),
]


# --- the planted violations ------------------------------------------------
#
# A fixture rather than the live change, so the assertions hold with no network
# and say the same thing on every branch.

WHOLE = Change(
    number=1,
    body=(
        "Closes #0.\n\n"
        "One reader resolves the configuration, applies the defaults the surface marks, "
        "and refuses what the surface does not allow.\n\n"
        "### Test plan\n\n"
        "- [x] the self-test is green\n\n"
        "```markdown\n"
        "## Open items\n\n"
        "None.\n"
        "- [ ] the shape this gate refuses\n"
        "```\n\n"
        "## Open items\n\n"
        "- None.\n\n"
        "---\n"
    ),
    threads=[{"resolved": True, "outdated": False, "path": "a.py", "line": 3, "first": "Answered."}],
    # A marker in this file is exempt and a line in a sibling tool is not;
    # the first half is asserted by this fixture staying green.
    # ⛔ The three lines below are the honest form of a limit, taken from lines
    # this repository already carries, and they are in the whole-change fixture
    # so the green side of the unowned-remedy arm is asserted rather than
    # assumed: each says a thing is absent and none says nobody owns the cure.
    # Widening the arm to the unfinished half reddens this fixture, which is the
    # assertion that the carve-out is load-bearing.
    added=[("a.py", "    return value"),
           ("tools/" + os.path.basename(__file__), "    # TODO: the forms this file forbids"),
           ("docs/configuration-surface.md",
            "the one derivation measured runs from a priority the surface does not yet carry"),
           ("plugins/mjolnir/scripts/port.py",
            "    # sweep above forbids -- and would need editing every time an"),
           ("plugins/mjolnir/skills/review/SKILL.md",
            "still needs an answer on the thread, and a thread nobody replied to is an open "
            "question.")],
    unread=[],
)

# The shape this rule was written against, reproduced rather than described: a
# body that surfaces what it knows is unfinished, under a heading that reads as
# diligence, and merges anyway. It reddens because it never states its open
# items, which is the claim the gate reads back.
THE_MEASURED_SHAPE = (
    "Closes #0.\n\n"
    "### Worth a reviewer's attention\n\n"
    "- **A new dependency**, which the workflow pins.\n"
    "- One line runs to 125 characters and cannot wrap.\n"
    "- The strict half of the sweep is largely unexercised until the hooks land.\n"
)


def _plant_body(body: str):
    def apply(change: Change) -> Change:
        change.body = body
        return change

    return apply


def _plant_no_body(change: Change) -> Change:
    change.body = ""
    return change


def _plant_unresolved_thread(change: Change) -> Change:
    change.threads.append({
        "resolved": False, "outdated": False, "path": "a.py", "line": 7,
        "first": "This reads the wrong root.",
    })
    return change


def _plant_unresolved_outdated_thread(change: Change) -> Change:
    change.threads.append({
        "resolved": False, "outdated": True, "path": "a.py", "line": None,
        "first": "Raised against a line this branch has since moved.",
    })
    return change


def _plant_marker(path: str, text: str):
    def apply(change: Change) -> Change:
        change.added.append((path, text))
        return change

    return apply


def _plant_unread_file(change: Change) -> Change:
    change.unread.append("assets/large.bin")
    return change


VIOLATIONS = [
    ("the change was read", "an empty body", _plant_no_body),
    ("the body states its open items", "the measured shape: open items under another heading",
     _plant_body(THE_MEASURED_SHAPE)),
    ("the body states its open items", "a section listing what is open",
     _plant_body("## Open items\n\n- The wrap rule is unenforced here.\n")),
    ("the body states its open items", "a section answered with anything but none",
     _plant_body("## Open items\n\nSee the thread above.\n")),
    ("the body states its open items", "an answer with an open item written after it",
     _plant_body("## Open items\n\nNone.\n\nThe hook is not wired yet.\n")),
    ("the body states its open items", "an empty section", _plant_body("## Open items\n\n")),
    ("the body states its open items", "a second section further down",
     _plant_body("## Open items\n\nNone.\n\n## Notes\n\nx\n\n## Open items\n\n- open\n")),
    ("the body states its open items", "a section quoted in a fence and never stated",
     _plant_body("## Notes\n\n```markdown\n## Open items\n\nNone.\n```\n")),
    ("no thread on the change is unresolved", "an unresolved thread", _plant_unresolved_thread),
    ("no thread on the change is unresolved", "an unresolved thread on an outdated diff",
     _plant_unresolved_outdated_thread),
    ("no unticked item in the body", "an unticked item",
     _plant_body("## Open items\n\nNone.\n\n- [ ] drive it in the running application\n")),
    ("no deferral marker added by the change", "a marker with a colon",
     _plant_marker("b.py", "    # TODO: narrow this once the facet lands")),
    ("no deferral marker added by the change", "a marker with an argument list",
     _plant_marker("b.py", "    // FIXME(someone): the wrong root")),
    ("no deferral marker added by the change", "a marker in a sibling tool, which is not exempt",
     _plant_marker("tools/check_single_source.py", "    # XXX: skip this for now")),
    ("no deferral marker added by the change", "a file the host supplied no patch for",
     _plant_unread_file),
    # ⛔ The measured clause itself, byte for byte from the change that shipped
    # it, rather than a paraphrase of it: a plant written in this file's own
    # words would hold the grammar to the grammar.
    ("no work added with no owner", "the measured clause: a cure nobody owns, in a document",
     _plant_marker("docs/building-itself.md",
                   "what would make it the latter is a carrier for the check, which no item "
                   "owns today")),
    ("no work added with no owner", "a remedy handed to an unnamed person",
     _plant_marker("docs/x.md", "Somebody should narrow the arm once the facet lands.")),
    ("no work added with no owner", "work parked on a later change",
     _plant_marker("plugins/mjolnir/config/schema.md",
                   "The second half is left for a later item.")),
    ("no work added with no owner", "a future change named as the owner",
     _plant_marker("docs/x.md", "A later change will carry the sweep arm.")),
]


def run(change: Change) -> dict[str, list[str]]:
    return {name: check(change) for name, check in CHECKS}


def self_test() -> int:
    by_name = dict(CHECKS)
    uncovered = [name for name, _ in CHECKS if not any(n == name for n, _, _ in VIOLATIONS)]
    for name in uncovered:
        print(f"  NO PLANTED VIOLATION   {name}")
    failures = len(uncovered)

    # A check that cannot pass is as useless as one that cannot fail, and an
    # over-broad body rule would redden every honest pull request alike.
    whole = [p for found in run(WHOLE).values() for p in found]
    if whole:
        print(f"  RED ON A WHOLE CHANGE  {len(whole)} problem(s): {whole[0]}")
        failures += 1
    else:
        print("  green on               a change that carries nothing open")

    for name, label, plant in VIOLATIONS:
        if by_name[name](plant(WHOLE.copy())):
            print(f"  red on                 {name}: {label}")
        else:
            print(f"  STAYED GREEN           {name}: {label}")
            failures += 1

    # ⛔ The one carve-out in how a change's added lines are read, asserted in
    # both directions and at the function that decides it. A file the host
    # reports **added** and supplies no patch for is read whole from the
    # checkout, every line of it being a line this change writes; a file it
    # reports **modified** stays unread, because reading that one whole would
    # hand somebody else's marker to this change.
    import tempfile as _tempfile
    with _tempfile.TemporaryDirectory() as root:
        was = os.getcwd()
        try:
            os.chdir(root)
            with open("an-added-file.py", "w", encoding="utf-8") as handle:
                handle.write("one = 1\ntwo = 2\n")
            for label, entry, expected in (
                ("an added file with no patch is read whole from the checkout",
                 {"status": "added", "filename": "an-added-file.py"},
                 [("an-added-file.py", "one = 1"), ("an-added-file.py", "two = 2")]),
                ("a modified file with no patch stays unread",
                 {"status": "modified", "filename": "an-added-file.py"}, None),
                ("an added file that is not in the tree stays unread",
                 {"status": "added", "filename": "a-file-that-is-not-there.py"}, None),
            ):
                if _added_whole(entry) == expected:
                    print(f"  held                   {label}")
                else:
                    print(f"  DID NOT HOLD           {label}: {_added_whole(entry)!r}")
                    failures += 1
        finally:
            os.chdir(was)

    if failures:
        print(f"\n{failures} assertion(s) did not hold. A check that cannot fail is not a check.")
    return 1 if failures else 0


def main(argv: list[str]) -> int:
    unknown = [a for a in argv if a != "--self-test"]
    if unknown:
        print(f"unrecognised argument(s): {' '.join(unknown)}\n\n{__doc__}")
        return 2

    if "--self-test" in argv:
        print(f"Asserting each check reddens on its planted violations ({len(VIOLATIONS)}):")
        if self_test():
            return 1
        print()

    try:
        change = read_change()
    except Unreadable as exc:
        print(f"  FAIL  the change was read\n\n  - {exc}")
        return 1

    results = run(change)
    problems = [p for found in results.values() for p in found]
    for name, found in results.items():
        print(f"  {'FAIL' if found else 'ok  '}  {name}")
    if problems:
        print(f"\nPull request #{change.number} carries open items:\n")
        for problem in problems:
            print(f"  - {problem}")
        print(
            "\nNothing is deferred: a question this change cannot answer is asked, with its "
            "options, and work belonging to a different outcome is a separate numbered item "
            "filed before the merge."
        )
        return 1
    print(f"\nPull request #{change.number} carries no open item: nothing was deferred.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
