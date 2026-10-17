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
none. It is the narrowest the host offers -- read access to pull requests, with
the checkout still told to persist nothing -- and the trade is stated in
docs/single-source-of-truth.md rather than left as a quiet exception. Without
it a finding raised in review is invisible here, and an item no gate can see
reads as resolved.

Measured on this repository, which is what made the rule procedure: a pull
request merged carrying its own list of unresolved items in its body and review
findings answered nowhere. Every one had been surfaced, written down, and then
shipped -- the deferral was visible and nothing refused it.

What it hardcodes is grammar, in the same sense its siblings do: the heading a
body states its open items under, the form of a `none` answer, the marker
words, and the shape of an unticked list item. Making the first two
configuration -- a body-section gate an adopting project installs, with the
headings read from its own configuration and its own language -- is #51's, and
this script is the one implementation that item would call.

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

# --- the grammar -----------------------------------------------------------
#
# Form, not content. Every one of these is a shape a body or a diff has, and
# none of them is a fact about this project.

# The section a body states its open items under, and the only answer that
# closes it. A heading at any level, matched on its text alone and without
# regard to case, because the level and the casing a body puts it at are
# formatting. The spellings below are what a refusal quotes back, so what the
# gate asks for and what the documents state are one string rather than two.
HEADING_TEXT = "Open items"
NO_OPEN_ITEMS_ANSWER = "None."
OPEN_ITEMS = HEADING_TEXT.lower()
NO_OPEN_ITEMS = {NO_OPEN_ITEMS_ANSWER.lower(), NO_OPEN_ITEMS_ANSWER.lower().rstrip(".")}

HEADING = re.compile(r"^\s{0,3}(#{1,6})\s+(.*?)\s*#*\s*$")
UNTICKED = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+\[ \]\s*(?P<text>.*)")

# A deferral marker, in the one form that is unambiguous: the word carrying a
# colon or an argument list. A bare mention -- `TODO` in a sentence about this
# rule, or in a comment quoting a status vocabulary -- is prose, and sweeping
# prose for these words would redden on a reworded sentence. Both spellings
# already live in this tree for exactly that innocent reason.
MARKER = re.compile(r"\b(TODO|FIXME|XXX)\s*[:(]")

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

    def __init__(self, number: int | None, body: str | None,
                 threads: list[dict], added: list[tuple[str, str]]):
        self.number = number
        self.body = body
        self.threads = threads
        self.added = added

    def copy(self) -> "Change":
        return Change(
            self.number,
            self.body,
            [dict(thread) for thread in self.threads],
            list(self.added),
        )

    def section(self, name: str) -> list[str] | None:
        """The lines under the heading named, or None where there is no such heading.

        Runs to the next heading of any level, so a body that states its open
        items and then carries on about something else is read correctly.
        """
        if self.body is None:
            return None
        out: list[str] | None = None
        for line in self.body.splitlines():
            match = HEADING.match(line)
            if match:
                title = match.group(2).strip().strip("*_`:").strip().lower()
                if title == name:
                    out = []
                    continue
                if out is not None:
                    break
                continue
            if out is not None:
                out.append(line)
        return out


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
        slug = reader.load(root).get("host.repo")
    except Exception as exc:  # the reader names the key it refused
        raise Unreadable(f"the configuration could not be read: {exc}") from exc
    if not slug or "/" not in slug:
        raise Unreadable("the configuration states no `host.repo`, so there is nothing to ask.")
    owner, _, name = slug.partition("/")

    try:
        out = subprocess.run(
            ["gh", "pr", "view", "--json", "number", "--jq", ".number"],
            capture_output=True, text=True, check=True, cwd=root,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        raise Unreadable(
            "no pull request for this branch. The rule is held against a pull request, so "
            "this check has no answer until one exists -- which is not the same as green."
        ) from exc
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


def _added(owner: str, name: str, number: int, token: str) -> list[tuple[str, str]]:
    """(path, added line) for every line this change writes, following pages."""
    out: list[tuple[str, str]] = []
    page = 1
    while True:
        files, _ = _request(
            f"{API}/repos/{owner}/{name}/pulls/{number}/files?per_page={PAGE}&page={page}", token
        )
        for entry in files:
            for line in (entry.get("patch") or "").splitlines():
                match = DIFF_ADDED.match(line)
                if match:
                    out.append((entry["filename"], match.group("text")))
        if len(files) < PAGE:
            return out
        page += 1


def read_change() -> Change:
    owner, name, number = _where()
    token = _token()
    body, threads = _threads(owner, name, number, token)
    return Change(number, body, threads, _added(owner, name, number, token))


# --- the checks ------------------------------------------------------------
#
# Each returns a list of problems, and each has at least one planted violation
# below that it is asserted to go red on -- one per branch that does real work,
# because a plant that reddens a check by the wrong route proves nothing about
# the branch it was written for.


def check_the_change_was_read(change: Change) -> list[str]:
    problems = []
    if change.number is None:
        problems.append(
            "no pull request was resolved, so nothing below holds anything. Absence of "
            "signal is not an answer, and it is never green."
        )
    if change.body is None:
        problems.append(
            "the pull request has no body at all. A change states what it carries; an "
            "empty body states nothing and cannot state that nothing is open."
        )
    return problems


def check_the_body_states_its_open_items(change: Change) -> list[str]:
    if change.body is None:
        return []
    lines = change.section(OPEN_ITEMS)
    if lines is None:
        return [
            f"the body carries no `{HEADING_TEXT}` section. The statement that every item "
            "raised against this change is resolved is what the gate reads back, so a body "
            "that does not make it is not ready — write the section, and answer it "
            f"`{NO_OPEN_ITEMS_ANSWER}` where nothing is open."
        ]
    content = [line.rstrip() for line in lines if line.strip()]
    answer = " ".join(" ".join(content).split()).lower()
    if answer in NO_OPEN_ITEMS:
        return []
    if not content:
        return [
            f"the body's `{HEADING_TEXT}` section is empty. An empty section is not an "
            "answer: state what is open, or state that nothing is."
        ]
    return [
        f"the body's `{HEADING_TEXT}` section carries {len(content)} open item(s), and "
        "no change merges with one against it:"
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
    problems = []
    for line in (change.body or "").splitlines():
        match = UNTICKED.match(line)
        if match:
            problems.append(
                f"the body carries an unticked item: {match.group('text').strip()[:120]}"
            )
    return problems


def check_no_deferral_marker_added(change: Change) -> list[str]:
    problems = []
    for path, line in change.added:
        if path == SELF:
            continue
        match = MARKER.search(line)
        if match:
            problems.append(
                f"{path}: this change adds a {match.group(1)} marker — {line.strip()[:120]}"
            )
    return problems


# The one file that necessarily writes the markers down, for the same reason
# its sibling sweep exempts itself: it spells out every form it forbids. The
# exemption is this file and no other, so a marker in any other tool is read.
SELF = "tools/" + os.path.basename(__file__)


CHECKS = [
    ("the change was read", check_the_change_was_read),
    ("the body states its open items", check_the_body_states_its_open_items),
    ("no thread on the change is unresolved", check_no_thread_is_unresolved),
    ("no unticked item in the body", check_no_unticked_item_in_the_body),
    ("no deferral marker added by the change", check_no_deferral_marker_added),
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
        "## Open items\n\n"
        "None.\n"
    ),
    threads=[{"resolved": True, "outdated": False, "path": "a.py", "line": 3, "first": "Answered."}],
    added=[("a.py", "    return value")],
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


def _plant_no_pull_request(change: Change) -> Change:
    change.number = None
    return change


def _plant_no_body(change: Change) -> Change:
    change.body = None
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


def _plant_marker(text: str):
    def apply(change: Change) -> Change:
        change.added.append(("b.py", text))
        return change

    return apply


VIOLATIONS = [
    ("the change was read", "no pull request resolved", _plant_no_pull_request),
    ("the change was read", "a body-less pull request", _plant_no_body),
    ("the body states its open items", "the measured shape: open items under another heading",
     _plant_body(THE_MEASURED_SHAPE)),
    ("the body states its open items", "a section listing what is open",
     _plant_body("## Open items\n\n- The wrap rule is unenforced here.\n")),
    ("the body states its open items", "a section answered with anything but none",
     _plant_body("## Open items\n\nSee the thread above.\n")),
    ("the body states its open items", "an empty section", _plant_body("## Open items\n\n")),
    ("no thread on the change is unresolved", "an unresolved thread", _plant_unresolved_thread),
    ("no thread on the change is unresolved", "an unresolved thread on an outdated diff",
     _plant_unresolved_outdated_thread),
    ("no unticked item in the body", "an unticked item",
     _plant_body("## Open items\n\nNone.\n\n- [ ] drive it in the running application\n")),
    ("no deferral marker added by the change", "a marker with a colon",
     _plant_marker("    # TODO: narrow this once the facet lands")),
    ("no deferral marker added by the change", "a marker with an argument list",
     _plant_marker("    // FIXME(someone): the wrong root")),
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
