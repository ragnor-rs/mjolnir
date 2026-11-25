#!/usr/bin/env python3
"""The code host's own item types, for the kinds it answers.

[`schema.md § 4.1`](../../config/schema.md#41-type) states the rule. Two kinds here
reach the types through the **same** host -- plain issues, and a board whose cards
are views over them -- so the documents that ask and the refusals live here once,
for the reason `_code_host_dependency.py` beside this one gives.

⚠️ **Asked of the repository and never of its owner.** The host states types above
the repository and answers for one all the same, whoever owns it -- and a type the
owner has disabled comes back listed, so the flag is read.

⛔ **Read through the host's query interface rather than the client's own field
list.** A client too old to know the field refuses the whole call, which would take
every other fact about the item down with it.

The transport is the caller's, as it is in the siblings. ⚠️ The module name opens
with `_` so the port's discovery skips it.
"""

from __future__ import annotations

import os
import sys

_SCRIPTS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _SCRIPTS not in sys.path:
    sys.path.append(_SCRIPTS)

import port  # noqa: E402

CARRIER = "work_item.type.carrier"
NATIVE = "native"
TYPE = "work_item.type"

TYPES_QUERY = """
query IssueTypes($owner:String!, $name:String!) {
  repository(owner:$owner, name:$name) {
    issueTypes(first:100) {
      pageInfo { hasNextPage }
      nodes { name isEnabled }
    }
  }
}
"""

TYPE_QUERY = """
query TypeOf($owner:String!, $name:String!, $number:Int!) {
  repository(owner:$owner, name:$name) {
    issue(number:$number) { issueType { name } }
  }
}
"""


def carried(configuration) -> bool:
    """Whether this project's type is the host's own (§ 4.1)."""
    return configuration.get(CARRIER) == NATIVE


def _repository(call, query: str, repo: str, *more: str) -> dict:
    owner, name = repo.split("/")
    answer = call(["api", "graphql", "-f", f"query={query}",
                   "-f", f"owner={owner}", "-f", f"name={name}", *more])
    errors = answer.get("errors") if isinstance(answer, dict) else None
    data = answer.get("data") if isinstance(answer, dict) else None
    found = data.get("repository") if isinstance(data, dict) else None
    if errors or not isinstance(found, dict):
        raise port.HostUnavailable(
            f"the host answered no item type reading for {repo}: "
            f"{errors or 'no repository came back'}. An unreadable answer is not "
            "the same as no type."
        )
    return found


def types_of(call, repo: str) -> list[str]:
    """The types an item in this repository can be given, in the host's order.

    Empty where the host states none. ⛔ A list that claims another page is refused
    rather than returned short: the missing half would be refused by name at the
    next filing, as types the host does not know.
    """
    found = _repository(call, TYPES_QUERY, repo)
    if "issueTypes" not in found:
        raise port.HostUnavailable(
            f"the host answered for {repo} with no item types field at all, so "
            "whether it states any could not be told."
        )
    stated = found["issueTypes"]
    if stated is None:
        return []
    if not isinstance(stated, dict) or not isinstance(stated.get("nodes"), list):
        raise port.HostUnavailable(
            f"the host answered {stated!r} for the item types of {repo}, which is "
            "not a list of them."
        )
    if (stated.get("pageInfo") or {}).get("hasNextPage"):
        raise port.HostUnavailable(
            f"the item types of {repo} came back with more to read, in a shape "
            "asked for in one page. Refused rather than returned short."
        )
    return [
        one["name"] for one in stated["nodes"]
        if isinstance(one, dict) and isinstance(one.get("name"), str)
        and one["name"] and one.get("isEnabled")
    ]


def type_of(call, repo: str, number: int) -> str | None:
    """The type one item carries, or `None` where it carries none."""
    issue = _repository(
        call, TYPE_QUERY, repo, "-F", f"number={int(number)}"
    ).get("issue")
    # ⛔ The key is required: an answer without it would read as *no type*.
    if not isinstance(issue, dict) or "issueType" not in issue:
        raise port.HostUnavailable(
            f"the host answered no type reading for #{number} in {repo}, which is "
            "not the same as an item carrying none."
        )
    held = issue["issueType"]
    if held is None:
        return None
    if not isinstance(held, dict) or not isinstance(held.get("name"), str):
        raise port.HostUnavailable(
            f"the host answered {held!r} as the type of #{number} in {repo}."
        )
    return held["name"]


def flags(call, configuration, repo: str, wanted: str | None) -> list[str]:
    """What the create call carries for the type a filing states.

    ⛔ Every refusal here comes before the write, so a refused filing leaves
    nothing on the tracker.
    """
    if wanted is None:
        return []
    if not carried(configuration):
        raise port.ConfigError(
            CARRIER,
            f"is `{configuration.get(CARRIER)}`, and this filing states the native "
            f"type `{wanted}`. § 4.1 puts a type on one carrier, so a native one "
            "written here would be a second statement of it.",
        )
    known = types_of(call, repo)
    if wanted not in known:
        raise port.ConfigError(
            TYPE,
            f"`{wanted}` is not an item type the host states for {repo}. It states: "
            f"{', '.join(known) or 'none'}. Nothing was filed.",
        )
    return ["--type", wanted]


def hold(item: dict, wanted: str | None) -> dict:
    """The created item, where it came back carrying the type asked for."""
    if wanted is not None and item.get("type") != wanted:
        raise port.HostUnavailable(
            f"item #{item.get('number')} was created and came back with type "
            f"{item.get('type')!r} where {wanted!r} was asked for. The item exists, "
            "so this is reported rather than retried: a second create would file "
            "the work twice."
        )
    return item


def vocabulary(call, repo) -> dict:
    """The type vocabulary, in `read_vocabulary`'s shape. `repo` is called here."""
    try:
        slug = repo()
        names = types_of(call, slug)
    except (port.ConfigError, port.HostUnavailable) as error:
        return {
            "answer": port.VOCABULARY_UNESTABLISHED,
            "values": None,
            "because":
                f"the host's item types could not be read: {error}. ⛔ Not read as "
                "a host with no types",
        }
    return {
        "answer": port.VOCABULARY_READ if names else port.VOCABULARY_NONE,
        "values": names,
        "because":
            f"{len(names)} native item type(s) on {slug}. ⚠️ The host stating them "
            "is not this project carrying its type in them, which is § 4.1's to state"
            if names else
            f"{slug} states no item type an item could be given",
    }
