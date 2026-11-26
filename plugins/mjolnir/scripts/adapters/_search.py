"""What a search covers, read once for every implementation.

[`schema.md § 3`](../../config/schema.md#what-a-search-covers-and-what-it-says-it-did-not)
states that a project says which texts a query's terms are matched in and which
fields a query may filter on, and that every answer names what it searched and
what it did not. The reading of those two keys lives **here** rather than in an
implementation, for `_policy`'s reason: four implementations carrying one reading
are four statements allowed to disagree.

⛔ **The reading is here; the query is not.** How a text is matched -- a native
clause, a qualifier, a substring over a text read beside the item -- is each
tracker's own, and so is the refusal's wording where it names what the tracker
cannot do. What is shared is which texts were asked for, which of them this
implementation reaches, and the two lists the answer carries.

⚠️ The module name opens with `_` so the port's discovery skips it: a module in
`adapters/` that names no kind is refused rather than skipped, which is right for
an implementation and wrong for a reading four of them share.
"""

from __future__ import annotations

import os
import sys

_SCRIPTS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _SCRIPTS not in sys.path:
    sys.path.append(_SCRIPTS)

from config import ConfigError  # noqa: E402

TEXTS_KEY = "tracker.search.texts"
FIELDS_KEY = "tracker.search.fields"


def _stated(configuration, key: str):
    return configuration.get(key) if configuration is not None else None


def coverage(configuration, *, reachable: tuple, default: tuple, terms: bool) -> tuple:
    """The texts this search matches terms in, and the stated ones it cannot.

    `reachable` is what this implementation can search at all, and `default` is
    what it searched before the key existed -- which is what an absent key keeps.
    ⛔ **Where every stated text is out of reach, a query with terms is refused**:
    matched in nothing, it answers with nothing, and that reads as a tracker
    holding no such item. A query with no terms matches no text, so it is not.
    """
    stated = _stated(configuration, TEXTS_KEY)
    if stated is None:
        return list(default), []
    searched = [text for text in stated if text in reachable]
    missed = [text for text in stated if text not in reachable]
    if terms and not searched:
        raise ConfigError(
            TEXTS_KEY,
            f"states {', '.join(stated)}, and this tracker can search none of them "
            f"(it reaches {', '.join(reachable)}). A query's terms matched in "
            "nothing answer with no items, which cannot be told from a tracker "
            "holding no such item -- so the search is refused rather than run.",
        )
    return searched, missed


def stated_fields(configuration) -> list[str]:
    """The fields the project lets a query filter on beyond the implementation's."""
    return [str(name) for name in (_stated(configuration, FIELDS_KEY) or [])]


def unqueryable(name: str, why: str) -> ConfigError:
    """The one refusal for a field a query cannot ask about, keyed on the list."""
    return ConfigError(
        FIELDS_KEY,
        f"covers the field `{name}`, and {why} An empty answer is what a field "
        "nothing carries looks like, so a field nothing could ask about is refused "
        "rather than answered with no items.",
    )


def not_admitted(name: str, builtin: tuple) -> ConfigError:
    """A field asked for that neither the implementation nor the list admits."""
    own = ", ".join(builtin) if builtin else "none"
    return ConfigError(
        f"tracker.operations.search_items.{name}",
        f"is not a field a query here filters on. The implementation's own are: "
        f"{own}; anything else is admitted by naming it in `{FIELDS_KEY}`. It is "
        "refused rather than answered with the items that do not match.",
    )


def holds(value, wanted) -> bool:
    """Whether a field's value answers the value asked for.

    A field holding several values answers when any one of them is the value --
    each member compared as itself or, for a member the tracker shapes as a
    structure, by the name it carries.
    """
    if isinstance(value, list):
        return any(holds(member, wanted) for member in value)
    if isinstance(value, dict):
        return any(value.get(key) == wanted for key in ("name", "value", "title"))
    return value == wanted


def term_in(words: list[str], texts: list[str]) -> bool:
    """Every term a substring of some searched text, whatever the case."""
    lowered = [(text or "").lower() for text in texts]
    return all(any(word in text for text in lowered) for word in words)


def reported(answer: dict, searched: list[str], missed: list[str]) -> dict:
    """The answer with its coverage stated, which every implementation carries."""
    answer["texts_searched"] = list(searched)
    answer["texts_not_searched"] = list(missed)
    return answer

