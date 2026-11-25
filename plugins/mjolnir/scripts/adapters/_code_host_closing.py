#!/usr/bin/env python3
"""What the code host will close when one change lands, for the kinds it answers.

[`schema.md § 3 → What a merge closes`](../../config/schema.md#what-a-merge-closes-and-the-comparison-that-holds-it)
states the operation. Two kinds here reach it through the **same** host -- plain
issues, and a board whose cards are views over them -- so the document that asks,
the words that close and the shape of the answer live here once, for the reason
`_code_host_dependency.py` beside this one gives.

⛔ **Two readings, and neither stands in for the other.** The host states its own
list for a change, read from the body and from links made by hand, and that list
is the authority on them: a scan of the body is only what *explains* an entry.
⚠️ Measured on this repository: one body carrying a closing word beside a number
was not listed for it, so a scan taken as the verdict would have been wrong. A
**commit message** is on no such list and closes an item all the same once it
reaches the default branch, so those are scanned, and so is any text the merge
call itself supplies.

⛔ **The scan ignores negation because the host does.** That is the defect this
exists to show rather than an imprecision in the pattern.

The transport is the caller's, as it is in the sibling. ⚠️ The module name opens
with `_` so the port's discovery skips it.
"""

from __future__ import annotations

import os
import re
import sys

_SCRIPTS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _SCRIPTS not in sys.path:
    sys.path.append(_SCRIPTS)

import port  # noqa: E402

# ⛔ The whole `message` and never the host's headline, which it truncates: a
# reference past the cut would close an item this reading called untouched.
CLOSING_LIST_QUERY = """
query ClosingList($owner:String!, $name:String!, $number:Int!) {
  repository(owner:$owner, name:$name) {
    defaultBranchRef { name }
    pullRequest(number:$number) {
      baseRefName
      body
      closingIssuesReferences(first:100) {
        pageInfo { hasNextPage }
        nodes { number repository { nameWithOwner } }
      }
      commits(first:100) {
        pageInfo { hasNextPage }
        nodes { commit { oid message } }
      }
    }
  }
}
"""

# The words this host closes on, with each form of reference it resolves.
CLOSES = re.compile(
    r"\b(?:close[sd]?|fix(?:e[sd])?|resolve[sd]?)\b:?\s+"
    r"(?:https?://[^\s/]+/(?P<url>[\w.-]+/[\w.-]+)/issues/(?P<at>[0-9]+)"
    r"|(?P<repo>[\w.-]+/[\w.-]+)#(?P<far>[0-9]+)"
    r"|(?:#|GH-)(?P<near>[0-9]+))\b",
    re.IGNORECASE,
)


def item_in(repo: str, owner: str | None, number) -> str:
    """One item's identifier: bare in this repository, qualified in another."""
    if not owner or owner.casefold() == repo.casefold():
        return str(int(number))
    return f"{owner}#{int(number)}"


def mentions(repo: str, text: str, where: str, source: str | None = None) -> list[dict]:
    """Every closing phrase in one text, with the line it stands on."""
    found = []
    for match in CLOSES.finditer(text):
        start = text.rfind("\n", 0, match.start()) + 1
        end = text.find("\n", match.end())
        found.append({
            "item": item_in(
                repo,
                match["url"] or match["repo"],
                match["at"] or match["far"] or match["near"],
            ),
            "where": where,
            "source": source,
            "text": text[start:end if end >= 0 else len(text)].strip(),
        })
    return found


def _whole(connection, what: str) -> list[dict]:
    """One page's nodes, refused where the page is not all of them."""
    if not isinstance(connection, dict) or not isinstance(connection.get("nodes"), list):
        raise port.HostUnavailable(f"{what} did not come back as a list.")
    info = connection.get("pageInfo")
    if not isinstance(info, dict) or info.get("hasNextPage") is not False:
        raise port.HostUnavailable(
            f"{what} came back short, or without the host saying it is whole, so "
            "an item missing from it cannot be told from one nothing closes."
        )
    return connection["nodes"]


def closing_list(repo: str, change: int, repository, landing: tuple = ()) -> dict:
    """The operation's answer, shaped from the host's own `repository` object."""
    repository = repository if isinstance(repository, dict) else {}
    held = repository.get("pullRequest")
    if not isinstance(held, dict):
        raise port.HostUnavailable(
            f"the host answered no change #{change} in {repo}, so what merging it "
            "closes could not be read."
        )
    default = (repository.get("defaultBranchRef") or {}).get("name")
    base = held.get("baseRefName")
    if not default or not base:
        raise port.HostUnavailable(
            f"the host did not state the base of #{change} and the default branch "
            "both, and whether a reference closes anything rests on the two."
        )
    listed = []
    for node in _whole(
        held.get("closingIssuesReferences"), f"what merging #{change} closes"
    ):
        try:
            owner = node["repository"]["nameWithOwner"]
            listed.append(item_in(repo, owner, node["number"]))
        except (KeyError, TypeError, ValueError):
            raise port.HostUnavailable(
                f"an entry of what merging #{change} closes names no item."
            ) from None
    said = mentions(repo, held.get("body") or "", "body")
    for node in _whole(held.get("commits"), f"the commits of #{change}"):
        commit = (node or {}).get("commit") or {}
        if not isinstance(commit.get("message"), str):
            raise port.HostUnavailable(f"a commit of #{change} came back with no message.")
        said += mentions(repo, commit["message"], "commit", commit.get("oid"))
    for text in landing:
        said += mentions(repo, text, "landing")
    return {
        "change": change,
        "base": base,
        "default_branch": default,
        # A reference closes nothing until it reaches the default branch.
        "closes_on_merge": base == default,
        "listed": listed,
        "mentions": said,
    }
