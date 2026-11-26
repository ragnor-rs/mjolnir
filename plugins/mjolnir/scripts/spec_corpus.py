#!/usr/bin/env python3
"""Read a project's specification corpus at the ref the item's version maps to.

The rule is `plugins/mjolnir/config/schema.md § 39`, which states it and carries
the argument behind it. Neither is restated here.

⛔ Every value is **read from the configuration**: the corpus globs, the part of
it read whole, and which of § 4.8's groupings the ref is named after. No path, no
subtree name and no branch pattern of any project is written in this file, and a
project whose `spec_corpus.carrier` is `none` has no subject here -- which is
reported as ⛔ **no corpus is configured** and never as *no contradiction was
found*, those being a verdict and the absence of a subject for one.

⛔ **Nothing is checked out.** The read is `ls-tree` and `show` at a ref, so the
working tree does not move: under § 10 the tree a session stands in belongs to
some other item, and a checkout here would move a tree a parallel session is
working in. The suite below asserts the negative rather than the file promising
it.

⛔ **Three outcomes and never two**, which is the whole of what this module is
careful about:

  AT_THE_VERSION the version's own branch resolved in this clone, and the corpus
                 read there is the copy that governs;
  FALLBACK       that branch does not exist, so the integration branch was read
                 instead. ⚠️ **Correct, and reported on every run that takes
                 it** -- a corpus written for a later version otherwise reads as
                 the governing one and the run gives no sign (§ 39);
  UNREAD         the branch exists on the remote and is not in this clone, so
                 nothing was read. ⛔ **Never folded into the fallback**: that
                 arm is for a version that does not exist, and reporting this
                 one as it would read the governing copy's absence from a clone
                 as the version's absence from the project.

⚠️ It needs no credential and no stack. It reaches the remote for one question
-- whether the version's branch is there at all -- and reads objects only out of
the clone.

⚠️ **What it prints is as large as the corpus the project configured**, the
load-bearing documents arriving whole: that is what the filing role has to read,
and `load_bearing` is the key that bounds it. ⛔ **Nothing here caps the output
instead**, a truncated specification being the reading § 39 exists to prevent one
step further on -- so a project whose corpus is large names this command in
§ 22's own list, where a bound is a project's statement rather than a carrier's
guess.

⛔ **Which role is reading is stated on the invocation** (`--role`, the filing
role where none is named). The filing role reads wherever a corpus is carried;
the starting and implementing roles read only where the project names them in
`spec_corpus.while_working.roles`, and a role it does not name is answered with
a fourth statement -- ⛔ **not asked**, which is neither *no corpus is
configured* nor a verdict about one (§ 39). For those two roles the corpus is
narrowed to `while_working.files` where the project states it: a document is
loaded only where it matches both lists, so the narrowing never widens.

Usage:
    spec_corpus.py --version V [--keyword W ...] [--role file|start|implement]
                                  the corpus that governs V, and what it says
    spec_corpus.py --self-test    assert each outcome against repositories built
                                  for it, then stop

Exit status: 0 the answer was produced, 2 the configuration could not be read or
the invocation carries no version under a live carrier.
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import claim  # noqa: E402 -- the one derivation of the integration branch (§ 10)
import config as reader  # noqa: E402 -- the one reader, never a second parser
from documents import glob_regex  # noqa: E402 -- § 38's glob semantics, stated once

AT_THE_VERSION, FALLBACK, UNREAD = "at_the_version", "fallback", "unread"
# ⛔ Not an outcome of the read but the absence of one: the project carries a
# corpus and does not have this role read it (§ 39).
NOT_ASKED = "not_asked"
FILING, ROLES = "file", ("file", "start", "implement")

REMOTE = "origin"


class CorpusError(Exception):
    """A stop this module names, rather than a traceback a caller reads."""


def governed(path: str, globs) -> bool:
    """Whether one repository-relative path is in a glob list.

    ⛔ `glob_regex` is imported rather than written again: § 39 states its globs
    as § 38's, so the two are one semantics and a copy here would be free to
    disagree about whether `*` crosses a separator.
    """
    return any(glob_regex(glob).match(path) for glob in globs)


def _git(root, *args, check=True):
    return claim.git(root, *args, check=check)


def _resolvable(root, ref: str) -> str | None:
    """The sha `ref` resolves to **in this clone**, or None.

    ⛔ The remote-tracking ref first and the local branch second, which is the
    order the reading needs rather than git's own: a project's own branch for a
    released version may be stale in a checkout somebody has been working in,
    and what governs is what the remote holds.

    ⛔ **Those two candidates and no third, so what is composed is a branch.**
    § 4.8's `ref_prefix` composes a ref `grouping_ref_exists` looks for among
    the remote's **heads**, so a branch is what the facet means throughout.
    ⚠️ **The first form carried a bare-revision candidate as well and it was two
    defects, not a convenience**: a tag would have resolved here and then been
    reported *fallback* by the arm beside this one, which reads heads only — the
    two answers § 39 is written to keep apart, reached through a candidate
    nothing on the surface asks for; and a `ref_prefix` leaving the composed
    name a revision expression would have resolved the working tree's own
    commit and called it the version's copy.
    """
    for candidate in (f"refs/remotes/{REMOTE}/{ref}", f"refs/heads/{ref}"):
        proc = _git(root, "rev-parse", "--verify", "--quiet", f"{candidate}^{{commit}}",
                    check=False)
        if proc.returncode == 0 and proc.stdout.strip():
            return proc.stdout.strip()
    return None


def _on_the_remote(root, ref: str) -> bool:
    """Whether the remote advertises `ref`, with no remote reading as *no*.

    ⚠️ A project with no remote at all is the local-only case § 10 derives, and
    there the clone is the whole of the namespace -- so a ref that did not
    resolve above does not exist, and the fallback is the right arm rather than
    `UNREAD`.
    """
    if not claim.remote_url(root, REMOTE):
        return False
    try:
        return claim.remote_ref_sha(root, REMOTE, ref) is not None
    except claim.ClaimError:
        # ⛔ A remote that could not be reached is **not** a ref that is absent:
        # reporting it as absent would take the fallback and produce a verdict
        # about the wrong copy, so it is reported as the unread arm instead.
        return True


def _blob(root, ref: str, path: str) -> str | None:
    proc = _git(root, "show", f"{ref}:{path}", check=False)
    return proc.stdout if proc.returncode == 0 else None


def _paths_at(root, ref: str) -> list[str]:
    proc = _git(root, "ls-tree", "-r", "--name-only", ref, check=False)
    if proc.returncode != 0:
        raise CorpusError(
            f"the ref `{ref}` resolved and then could not be listed: "
            f"{proc.stderr.strip() or proc.stdout.strip()}"
        )
    return [line for line in proc.stdout.splitlines() if line]


def _term(word: str) -> re.Pattern:
    """One keyword as a pattern, bounded where the word is one a boundary fits.

    ⚠️ Bounded for § 38's measured reason one facet over: an unbounded term
    matches inside a longer word, so a request about *auth* would report a hit
    in every document mentioning an author.
    """
    if re.fullmatch(r"[\w-]+", word):
        return re.compile(rf"(?<![\w-]){re.escape(word)}(?![\w-])", re.I)
    return re.compile(re.escape(word), re.I)


def read_corpus(root, facet: dict, version: str | None, keywords=(),
                role: str = FILING) -> dict:
    """The corpus that governs `version`, and which of the three outcomes it is.

    `facet` is the block `config.Config.spec_corpus` hands back, or `None` where
    the project carries none. ⛔ Taken as an argument rather than resolved here,
    which is `documents.read_subject`'s division for the same reason: the suite
    drives every arm without standing a configuration up, and the one resolution
    of the facet stays in the reader.
    """
    if facet is None:
        # ⛔ The absent subject, and the one answer this module must never give
        # instead. § 39 states the pair; `contradiction` is `None` here rather
        # than `False` so that a caller rendering it cannot print *none found*.
        return {
            "carried": False,
            "outcome": None,
            "ref": None,
            "asked_for": None,
            "load_bearing": [],
            "matched": [],
            "corpus": [],
            "contradiction": None,
        }

    if role not in facet.get("readers", [FILING]):
        # ⛔ The project carries a corpus and does not have this role read it.
        # Nothing was opened, so -- like the absent subject above -- there is no
        # verdict here and `contradiction` stays `None`.
        return {
            "carried": True,
            "outcome": NOT_ASKED,
            "role": role,
            "ref": None,
            "asked_for": None,
            "load_bearing": [],
            "matched": [],
            "corpus": [],
            "contradiction": None,
        }

    if not version:
        raise CorpusError(
            "no version was named, and the corpus is read at the ref the item's "
            "version maps to (§ 39). Under § 4.8 the grouping's value arrives on "
            "the invocation -- and, for the starting and implementing roles, is "
            "the value the item carries -- so a run with none has no ref to read "
            "at, and the copy it would fall back to is the one that reads as "
            "current while governing nothing."
        )

    prefix = facet.get("ref_prefix") or ""
    asked_for = f"{prefix}{version}"

    sha = _resolvable(root, asked_for)
    if sha:
        outcome, ref = AT_THE_VERSION, asked_for
    elif _on_the_remote(root, asked_for):
        return {
            "carried": True,
            "outcome": UNREAD,
            "ref": None,
            "asked_for": asked_for,
            "grouping": facet.get("grouping"),
            "load_bearing": [],
            "matched": [],
            "corpus": [],
            "contradiction": None,
        }
    else:
        outcome = FALLBACK
        ref = claim.integration_branch(root, REMOTE)
        if not _resolvable(root, ref):
            raise CorpusError(
                f"the version's branch `{asked_for}` does not exist and the "
                f"integration branch `{ref}` does not resolve in this clone "
                "either, so there is no copy of the corpus to read (§ 39)."
            )

    # ⛔ The narrowing is an intersection with the corpus and never a second
    # corpus: a glob reaching outside `files` loads nothing outside it (§ 39).
    narrowed_to = facet.get("narrowed_to") if role != FILING else None
    corpus = [
        path for path in _paths_at(root, ref)
        if governed(path, facet["files"])
        and (narrowed_to is None or governed(path, narrowed_to))
    ]
    whole, rest = [], []
    for path in corpus:
        (whole if governed(path, facet["load_bearing"]) else rest).append(path)

    terms = [(word, _term(word)) for word in keywords]
    load_bearing = [
        {"path": path, "text": _blob(root, ref, path) or ""} for path in whole
    ]
    matched = []
    for path in rest:
        text = _blob(root, ref, path) or ""
        hits = sorted(word for word, pattern in terms if pattern.search(text))
        if hits:
            matched.append({"path": path, "keywords": hits, "text": text})

    return {
        "carried": True,
        "outcome": outcome,
        "role": role,
        "narrowed_to": narrowed_to,
        "ref": ref,
        "asked_for": asked_for,
        "grouping": facet.get("grouping"),
        "load_bearing": load_bearing,
        "matched": matched,
        "corpus": corpus,
        # ⛔ Never answered here. Whether the request contradicts the corpus is a
        # reading of prose and the filing role's to make; what this module owes
        # is the text that reading is made against, and which copy it came from.
        "contradiction": None,
    }


def render(answer: dict, reason: str | None = None) -> str:
    """The report, with the outcome in its first line (§ 8)."""
    out = []
    if not answer["carried"]:
        out.append(
            "⛔ No specification corpus is configured (`spec_corpus.carrier: "
            "none`), so none was read and nothing here is a verdict about one. "
            "⚠️ This is the absence of a subject and not a finding: whether the "
            "request agrees with a specification is **unanswered**."
        )
        if reason:
            out.append("")
            out.append(f"The project's own stated reason: {' '.join(reason.split())}")
        return "\n".join(out)

    if answer["outcome"] == NOT_ASKED:
        out.append(
            f"⛔ This project does not have the `{answer['role']}` role read its "
            "specification corpus (`spec_corpus.while_working.roles`), so none "
            "was read. ⚠️ A corpus is configured and was not opened: whether the "
            "item agrees with it is **unanswered**, and nothing here is a verdict "
            "about it (§ 39)."
        )
        return "\n".join(out)

    if answer["outcome"] == UNREAD:
        out.append(
            f"⛔ The corpus was **not read**. The branch `{answer['asked_for']}` "
            "exists on the remote and is not in this clone, so no copy of the "
            "corpus was opened — and this is not the fallback, which is for a "
            "version that does not exist (§ 39)."
        )
        out.append("")
        out.append(
            f"To read it, fetch that ref and ask again: "
            f"`git fetch {REMOTE} {answer['asked_for']}`."
        )
        return "\n".join(out)

    if answer["outcome"] == FALLBACK:
        out.append(
            f"⚠️ Read at `{answer['ref']}` — the **fallback**. The branch "
            f"`{answer['asked_for']}` does not exist, so the integration branch "
            "was read instead. ⛔ That is correct and it is not the copy that "
            "governs the version: anything written for a later version is in "
            "what follows (§ 39)."
        )
    else:
        out.append(
            f"Read at `{answer['ref']}`, which is the copy that governs "
            f"`{answer['asked_for']}`."
        )

    out.append("")
    narrowed = answer.get("narrowed_to")
    out.append(
        f"The corpus at that ref carries {len(answer['corpus'])} document(s)"
        + (f", narrowed for the `{answer['role']}` role to "
           f"{', '.join(f'`{glob}`' for glob in narrowed)}" if narrowed else "")
        + f": {len(answer['load_bearing'])} read whole, "
        f"{len(answer['matched'])} matched on the request's keywords."
    )
    if not answer["corpus"]:
        out.append(
            "⛔ No document of the corpus is at that ref. That is a corpus with "
            "nothing in it at this version and **not** a specification that "
            "agrees with the request."
        )
    for entry in answer["load_bearing"]:
        out.append("")
        out.append(f"--- {entry['path']} (read whole)")
        out.append(entry["text"].rstrip())
    for entry in answer["matched"]:
        out.append("")
        out.append(f"--- {entry['path']} (matched: {', '.join(entry['keywords'])})")
        out.append(entry["text"].rstrip())
    out.append("")
    out.append(
        "⛔ Whether the request contradicts any of this is **unanswered here**: "
        f"it is a reading of prose and the `{answer.get('role', FILING)}` role's "
        "to make, against the text above and the ref it came from."
    )
    return "\n".join(out)


# --- self-test ---------------------------------------------------------------


def _repo(where: str, name: str) -> str:
    root = os.path.join(where, name)
    os.makedirs(os.path.join(root, "spec", "requirements"))
    subprocess.run(["git", "init", "-q", "-b", "main", root], check=True,
                   capture_output=True)
    # ⛔ An identity with no at-sign in it, because the names gate forbids an
    # address **anywhere** in the tree and a fixture identifies nobody. ⚠️ Not a
    # way round that gate: git never required an address, and `user.email` with
    # no at-sign commits exactly as well -- measured, the identity recorded as
    # `A Fixture <fixture>`. What the gate forbids is gone rather than hidden.
    for key, value in (("user.email", "fixture"), ("user.name", "A Fixture")):
        subprocess.run(["git", "-C", root, "config", key, value], check=True,
                       capture_output=True)
    return root


def _write(root: str, path: str, text: str) -> None:
    at = os.path.join(root, path)
    os.makedirs(os.path.dirname(at), exist_ok=True)
    with open(at, "w", encoding="utf-8") as handle:
        handle.write(text)


def _commit(root: str, message: str) -> None:
    subprocess.run(["git", "-C", root, "add", "-A"], check=True, capture_output=True)
    subprocess.run(["git", "-C", root, "commit", "-qm", message], check=True,
                   capture_output=True)


def _a_facet(**overrides) -> dict:
    facet = {
        "files": ["spec/**/*.md"],
        "load_bearing": ["spec/requirements/**/*.md"],
        "grouping": "release_scope",
        "ref_prefix": "release/",
    }
    facet.update(overrides)
    return facet


def self_test() -> int:
    import tempfile

    failures = 0

    def check(label: str, condition: bool, detail: str = "") -> None:
        nonlocal failures
        if condition:
            print(f"  ok    {label}")
        else:
            failures += 1
            print(f"  FAIL  {label}{': ' + detail if detail else ''}")

    print("§ 39, the corpus and which copy of it governs:")

    # ⛔ Collected across every arm below and asserted at the end, because the
    # claim is about **every** answer this module gives rather than about the
    # two arms whose own assertions happened to mention it: whether the request
    # contradicts the corpus is the filing role's reading, so no outcome may
    # come back carrying a verdict about it. ⚠️ `None` and not `False` -- a
    # caller rendering `False` prints *none found*, which is the one wrong
    # answer available here.
    verdicts = []

    def answered(answer: dict) -> dict:
        verdicts.append((answer.get("outcome"), answer.get("contradiction")))
        return answer

    # The absent subject, which is the arm whose wrong answer is a verdict.
    answer = answered(read_corpus(".", None, "9.0"))
    check("a project with no corpus reports no subject rather than a verdict",
          answer["carried"] is False and answer["contradiction"] is None,
          f"{answer}")
    said = render(answer, reason="a wiki holds it")
    check("and the report says no corpus is configured",
          "No specification corpus is configured" in said, said)
    check("⛔ and never that nothing contradicts the request",
          "no contradiction" not in said.lower(), said)
    check("and it carries the project's own reason rather than a gloss",
          "a wiki holds it" in said, said)

    with tempfile.TemporaryDirectory() as where:
        root = _repo(where, "a-project")
        _write(root, "spec/requirements/one.md", "# Requirements\n\nAs it is now.\n")
        _write(root, "spec/screens/login.md", "# Login\n\nThe login screen now.\n")
        _commit(root, "the corpus as it is now")
        subprocess.run(["git", "-C", root, "branch", "release/9.0"], check=True,
                       capture_output=True)
        # The version's own copy, which differs from the tree's: the whole of
        # what this facet is for is that the first is read and not the second.
        subprocess.run(["git", "-C", root, "checkout", "-q", "release/9.0"], check=True,
                       capture_output=True)
        _write(root, "spec/requirements/one.md",
               "# Requirements\n\nAs it stood for nine.\n")
        _write(root, "spec/screens/login.md",
               "# Login\n\nThe login screen with a passkey.\n")
        _commit(root, "the corpus as it stood for nine")
        subprocess.run(["git", "-C", root, "checkout", "-q", "main"], check=True,
                       capture_output=True)
        # ⛔ A branch that is neither, and a dirty tree: the acceptance § 39 is
        # written against is a read taken while the session stands somewhere
        # else entirely.
        subprocess.run(["git", "-C", root, "checkout", "-q", "-b", "feature/other"],
                       check=True, capture_output=True)
        _write(root, "spec/requirements/one.md", "# Requirements\n\nUncommitted.\n")

        before = {
            "head": _git(root, "rev-parse", "HEAD").stdout.strip(),
            "branch": _git(root, "rev-parse", "--abbrev-ref", "HEAD").stdout.strip(),
            "status": _git(root, "status", "--porcelain").stdout,
            "working": open(os.path.join(root, "spec/requirements/one.md"),
                            encoding="utf-8").read(),
        }

        answer = answered(read_corpus(root, _a_facet(), "9.0", keywords=["passkey"]))
        check("the ref read is the version's own, composed from the grouping's prefix",
              answer["outcome"] == AT_THE_VERSION and answer["ref"] == "release/9.0",
              f"{answer['outcome']} at {answer['ref']!r}")
        check("the load-bearing document is the version's copy, not the tree's",
              [entry["path"] for entry in answer["load_bearing"]]
              == ["spec/requirements/one.md"]
              and "stood for nine" in answer["load_bearing"][0]["text"],
              f"{answer['load_bearing']}")
        check("⛔ and not the uncommitted text the tree carries",
              "Uncommitted" not in answer["load_bearing"][0]["text"],
              f"{answer['load_bearing']}")
        check("the rest of the corpus is matched on the request's keywords",
              [entry["path"] for entry in answer["matched"]]
              == ["spec/screens/login.md"],
              f"{answer['matched']}")

        after = {
            "head": _git(root, "rev-parse", "HEAD").stdout.strip(),
            "branch": _git(root, "rev-parse", "--abbrev-ref", "HEAD").stdout.strip(),
            "status": _git(root, "status", "--porcelain").stdout,
            "working": open(os.path.join(root, "spec/requirements/one.md"),
                            encoding="utf-8").read(),
        }
        check("⛔ nothing was checked out: the branch, the head and the tree are "
              "as they were", before == after,
              f"{before} -> {after}")

        # ⛔ The same negative on a **clean** tree, and it is not a repetition.
        # ⚠️ Measured by planting a checkout into the read: on the dirty tree
        # above, git refuses a plain `checkout` because it would overwrite the
        # local change -- so that plant reported green and the arm it was
        # written for was reached only by a *forcing* checkout. A clean tree is
        # where a plain one succeeds, which is what gives this pair its teeth.
        subprocess.run(["git", "-C", root, "checkout", "-q", "--", "."], check=True,
                       capture_output=True)
        clean_before = {
            "head": _git(root, "rev-parse", "HEAD").stdout.strip(),
            "branch": _git(root, "rev-parse", "--abbrev-ref", "HEAD").stdout.strip(),
            "status": _git(root, "status", "--porcelain").stdout,
            "working": open(os.path.join(root, "spec/requirements/one.md"),
                            encoding="utf-8").read(),
        }
        read_corpus(root, _a_facet(), "9.0", keywords=["passkey"])
        clean_after = {
            "head": _git(root, "rev-parse", "HEAD").stdout.strip(),
            "branch": _git(root, "rev-parse", "--abbrev-ref", "HEAD").stdout.strip(),
            "status": _git(root, "status", "--porcelain").stdout,
            "working": open(os.path.join(root, "spec/requirements/one.md"),
                            encoding="utf-8").read(),
        }
        check("⛔ and nothing is checked out on a clean tree either, where a "
              "checkout would have succeeded", clean_before == clean_after,
              f"{clean_before} -> {clean_after}")
        check("the clean tree really was clean, or the arm above asserts the dirty one twice",
              clean_before["status"] == "", f"{clean_before['status']!r}")
        # ⛔ Dirty again, because the arms below assert against the uncommitted
        # text: the fallback arm's teeth are that the text it reports is the
        # integration branch's and not the tree's.
        _write(root, "spec/requirements/one.md", "# Requirements\n\nUncommitted.\n")

        # ⛔ A branch and not any revision that happens to resolve. ⚠️ Planted as
        # a **tag** at the version's own commit with no branch of that name: a
        # bare-revision candidate resolves it, and the arm that decides the
        # unread outcome reads heads only — so the two would disagree and the
        # report would say *fallback* about a copy that is right there. The tag
        # is named with the prefix the facet composes, so nothing but the
        # candidate list decides the answer.
        subprocess.run(["git", "-C", root, "tag", "release/8.0", "release/9.0"],
                       check=True, capture_output=True)
        answer = answered(read_corpus(root, _a_facet(), "8.0"))
        check("a tag the composed name resolves to is not read as the version's branch",
              answer["outcome"] != AT_THE_VERSION, f"{answer['outcome']}")
        check("and the arm it does take is the one its own branch reading supports",
              answer["outcome"] == FALLBACK, f"{answer['outcome']}")

        # A keyword that is a prefix of a word in the corpus, which is the false
        # hit an unbounded term produces.
        answer = answered(read_corpus(root, _a_facet(), "9.0", keywords=["pass"]))
        check("a keyword is held to a word boundary", answer["matched"] == [],
              f"{answer['matched']}")

        # ⛔ The fallback, and the arm that must speak.
        answer = answered(read_corpus(root, _a_facet(), "9.1"))
        check("a version whose branch does not exist falls back",
              answer["outcome"] == FALLBACK, f"{answer['outcome']}")
        check("and the ref reported is the one actually read",
              answer["ref"] == "feature/other", f"{answer['ref']!r}")
        said = render(answer)
        check("⚠️ and the report says so rather than reading as the version's copy",
              "fallback" in said.lower() and "release/9.1" in said, said)
        check("and the text it carries is the fallback's, which is what it warns about",
              "Uncommitted" not in said and "as it is now" in said.lower(), said)

        # `load_bearing: []` is a project reaching every document by keyword.
        answer = answered(read_corpus(root, _a_facet(load_bearing=[]), "9.0",
                                      keywords=["passkey"]))
        check("an empty load-bearing list reads nothing whole",
              answer["load_bearing"] == [], f"{answer['load_bearing']}")
        check("and every document of the corpus is then keyword-matched",
              [entry["path"] for entry in answer["matched"]]
              == ["spec/screens/login.md"],
              f"{answer['matched']}")

        # A corpus whose globs match nothing at that ref: reported as that, and
        # ⛔ never as a specification that agrees.
        answer = answered(read_corpus(root, _a_facet(files=["elsewhere/**/*.md"]), "9.0"))
        check("a corpus matching nothing at the ref comes back empty",
              answer["corpus"] == [], f"{answer['corpus']}")
        said = render(answer)
        check("⛔ and the report says so rather than that nothing contradicts",
              "No document of the corpus is at that ref" in said
              and "no contradiction" not in said.lower(), said)

        # ⛔ § 39's working roles. A role the project does not name reads
        # nothing and says so -- in words that are neither the absent subject's
        # nor a verdict's.
        answer = answered(read_corpus(root, _a_facet(), "9.0", role="start"))
        check("a working role the project does not name reads nothing",
              answer["outcome"] == NOT_ASKED and answer["corpus"] == [],
              f"{answer['outcome']}")
        said = render(answer)
        check("and the report says the role is not asked, naming the key",
              "does not have the `start` role read" in said
              and "while_working.roles" in said, said)
        check("⛔ and says neither that no corpus is configured nor that nothing contradicts",
              "No specification corpus is configured" not in said
              and "no contradiction" not in said.lower(), said)
        # ⛔ An item carrying no version, in a project that has this role read
        # nothing: answered as before, and never the missing-version stop --
        # which would stop every start of a project that never opted in.
        try:
            answer = answered(read_corpus(root, _a_facet(), None, role="start"))
        except CorpusError as error:
            answer = {"outcome": f"stopped: {error}"}
        check("a role the project does not name, asked with no version, is not asked "
              "rather than stopped", answer["outcome"] == NOT_ASKED, f"{answer['outcome']}")

        named = _a_facet(readers=["file", "start", "implement"])
        answer = answered(read_corpus(root, named, "9.0", keywords=["passkey"],
                                      role="implement"))
        check("a working role the project names reads the version's own copy",
              answer["outcome"] == AT_THE_VERSION and answer["ref"] == "release/9.0"
              and answer["role"] == "implement",
              f"{answer['outcome']} at {answer['ref']!r}")
        check("and the report names which copy it read",
              "release/9.0" in render(answer), render(answer))

        # The narrowing: an intersection with the corpus, never a widening.
        narrowed = _a_facet(readers=["file", "start"],
                            narrowed_to=["spec/requirements/**/*.md", "elsewhere/**"])
        _write(root, "elsewhere/outside.md", "# Outside\n\npasskey\n")
        _commit(root, "a document outside the corpus")
        answer = answered(read_corpus(root, narrowed, "9.0", keywords=["passkey"],
                                      role="start"))
        check("a narrowed role loads only what both lists match",
              answer["corpus"] == ["spec/requirements/one.md"]
              and answer["matched"] == [],
              f"{answer['corpus']} / {[e['path'] for e in answer['matched']]}")
        check("⛔ and a narrowing glob reaching outside the corpus loads nothing outside it",
              not any(path.startswith("elsewhere/") for path in answer["corpus"]),
              f"{answer['corpus']}")
        check("and the report says the read was narrowed",
              "narrowed for the `start` role" in render(answer), render(answer))
        answer = answered(read_corpus(root, narrowed, "9.0", keywords=["passkey"]))
        check("the filing role is not narrowed by the working roles' list",
              [entry["path"] for entry in answer["matched"]] == ["spec/screens/login.md"]
              and answer["narrowed_to"] is None,
              f"{answer['corpus']}")
        answer = answered(read_corpus(
            root, _a_facet(readers=["file", "start"], narrowed_to=["elsewhere/**"]),
            "9.0", role="start"))
        said = render(answer)
        check("⛔ a narrowing matching nothing at the ref is an empty corpus, not agreement",
              answer["corpus"] == [] and "No document of the corpus is at that ref" in said
              and "no contradiction" not in said.lower(), said)

        # No version under a live carrier is a stop and not a fallback.
        try:
            read_corpus(root, _a_facet(), None)
            stopped = None
        except CorpusError as error:
            stopped = str(error)
        check("a run naming no version stops rather than falling back",
              stopped is not None and "no version" in stopped, f"{stopped!r}")

    # ⛔ The third outcome, which needs a remote that advertises a ref this clone
    # does not hold. ⚠️ Built with a single-branch clone rather than by deleting
    # a ref, so the shape is the one a real checkout arrives in.
    with tempfile.TemporaryDirectory() as where:
        origin = _repo(where, "origin")
        _write(origin, "spec/requirements/one.md", "# Requirements\n\nMain.\n")
        _commit(origin, "main's corpus")
        subprocess.run(["git", "-C", origin, "branch", "release/9.0"], check=True,
                       capture_output=True)
        clone = os.path.join(where, "a-clone")
        subprocess.run(
            ["git", "clone", "-q", "--single-branch", "--branch", "main", origin, clone],
            check=True, capture_output=True,
        )
        answer = answered(read_corpus(clone, _a_facet(), "9.0"))
        check("a ref on the remote that this clone does not hold is reported unread",
              answer["outcome"] == UNREAD, f"{answer['outcome']}")
        check("⛔ and never as the fallback, which would be a verdict on another copy",
              answer["ref"] is None and answer["contradiction"] is None,
              f"{answer}")
        said = render(answer)
        check("and the report names the ref and the one command that would fetch it",
              "release/9.0" in said and "git fetch" in said, said)
        check("⛔ and says it is not the fallback",
              "not the fallback" in said, said)

    # ⛔ The claim that covers every answer rather than the two arms that
    # happened to mention it: no outcome carries a verdict about whether the
    # request contradicts the corpus, that reading being the filing role's.
    # ⚠️ The reached set is asserted too — a collector nothing fed would make
    # the claim vacuously true, which is this suite's own no-op-plant rule.
    reached = {outcome for outcome, _ in verdicts}
    check(
        "every outcome this module gives is reached by the arms above",
        reached == {None, AT_THE_VERSION, FALLBACK, UNREAD, NOT_ASKED},
        f"reached {sorted(str(name) for name in reached)}",
    )
    check(
        "⛔ and not one of them carries a verdict about a contradiction",
        all(stated is None for _, stated in verdicts),
        f"{[(outcome, stated) for outcome, stated in verdicts if stated is not None]}",
    )

    if failures:
        print(
            f"\n{failures} assertion(s) did not hold. A read that cannot say which "
            "copy it took is a read whose green says nothing."
        )
    return 1 if failures else 0


def main(argv: list) -> int:
    parser = argparse.ArgumentParser(
        description="Read a project's specification corpus at the ref its version maps to.",
    )
    parser.add_argument(
        "--skills-root",
        default=".",
        help="the root the configuration is resolved relative to (§ 1)",
    )
    parser.add_argument(
        "--version",
        help="the value the item carries for the grouping the corpus is read at (§ 4.8)",
    )
    parser.add_argument(
        "--keyword",
        action="append",
        default=[],
        dest="keywords",
        help="one term from the request; repeatable",
    )
    parser.add_argument(
        "--role",
        choices=ROLES,
        default=FILING,
        help="the role reading the corpus; the filing role where none is named (§ 39)",
    )
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv)

    if args.self_test:
        return self_test()

    try:
        resolved = reader.load(args.skills_root)
        facet = resolved.spec_corpus
        reason = resolved.get(f"{reader.SPEC_CORPUS_KEY}.absent_reason")
        answer = read_corpus(resolved.code_root, facet, args.version, args.keywords,
                             role=args.role)
    except reader.ConfigError as error:
        # ⛔ `str(error)` and not the key beside it: that exception already opens
        # its message with its own key, so a caller composing the pair prints
        # the key twice and reads as two refusals.
        print(str(error), file=sys.stderr)
        return 2
    except (CorpusError, claim.ClaimError) as error:
        print(str(error), file=sys.stderr)
        return 2
    print(render(answer, reason if facet is None else None))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
