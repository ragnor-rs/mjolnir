#!/usr/bin/env python3
"""One read of the backlog, the graph and the execution plan, with the drift named.

Reports, in one pass: the live set and its `P:` tiers, the dependency relations, acyclicity,
coverage of the plan's row table, ordering violations, same-row edges with the arrow check,
the unblocked queue, and — against the snapshot the last completed pass stamped — what was
filed, what landed, and which relations were added or removed since.

The whole graph arrives in one GraphQL call (`Issue.blockedBy`), which returns what polling
`dependencies/blocked_by` per issue returns at a fraction of the calls.

  plan-status.py            read and report; the snapshot is left alone
  plan-status.py --stamp    same, then write the snapshot as the new baseline

Every value is derived rather than written down: the repository from the working tree's own
remote, the plan and its snapshot from the session store this tree resolves to. Override any of
them with --repo, --plan, --snapshot.

Exit 0 when nothing needs an edit, 1 when coverage, ordering or acyclicity is off.
"""
import argparse
import collections
import glob
import hashlib
import json
import os
import re
import subprocess
import sys

TIERS = ("P: Highest", "P: High")
PLAN_GLOB = "execution-plan-*.md"
SNAPSHOT_NAME = ".plan-snapshot.json"

GRAPH_QUERY = """
query($owner:String!, $name:String!, $cursor:String) {
  repository(owner:$owner, name:$name) {
    issues(first:100, after:$cursor) {
      pageInfo { hasNextPage endCursor }
      nodes {
        number title closed
        labels(first:20) { nodes { name } }
        blockedBy(first:50) { nodes { number closed } }
      }
    }
  }
}
"""

LANDING_QUERY = """
query($owner:String!, $name:String!, $number:Int!) {
  repository(owner:$owner, name:$name) {
    issue(number:$number) {
      title
      closedByPullRequestsReferences(first:5, includeClosedPrs:true) {
        nodes { number mergeCommit { oid } }
      }
    }
  }
}
"""


def gh(args, cwd=None):
    p = subprocess.run(["gh"] + args, capture_output=True, text=True, cwd=cwd)
    if p.returncode != 0:
        raise SystemExit(f"gh {' '.join(args)} failed: {p.stderr.strip()}")
    return p.stdout


def working_tree():
    """The tree this run belongs to, which is also what the session store is keyed on."""
    found = subprocess.run(["git", "rev-parse", "--show-toplevel"],
                           capture_output=True, text=True).stdout.strip()
    if not found:
        raise SystemExit(f"{os.getcwd()} is not inside a working tree, so neither the repository "
                         "nor the session store can be derived — run from the checkout, or pass "
                         "--repo and --plan")
    return found


def session_store():
    """Where the harness keeps this tree's session files: the tree's path, separators folded."""
    return os.path.join(os.path.expanduser("~"), ".claude", "projects",
                        working_tree().replace(os.sep, "-"))


def resolve_plan():
    """The one ordering document in the session store. Refuses on none and on several."""
    store = session_store()
    found = sorted(glob.glob(os.path.join(store, PLAN_GLOB)))
    if not found:
        raise SystemExit(f"no {PLAN_GLOB} in {store} — pass --plan")
    if len(found) > 1:
        raise SystemExit(f"{len(found)} plans in {store}; name one with --plan:\n  "
                         + "\n  ".join(os.path.basename(f) for f in found))
    return found[0]


def resolve_repo():
    """The repository this tree pushes to, read off the tree rather than written down."""
    tree = working_tree()   # first, so its message is what a run outside a checkout reports
    return gh(["repo", "view", "--json", "nameWithOwner", "-q", ".nameWithOwner"], cwd=tree).strip()


def graphql(query, **variables):
    args = ["api", "graphql", "-f", f"query={query}"]
    for key, value in variables.items():
        flag = "-F" if isinstance(value, int) else "-f"
        args += [flag, f"{key}={value}"]
    body = json.loads(gh(args))
    if "errors" in body:
        raise SystemExit("graphql: " + json.dumps(body["errors"]))
    return body["data"]


def live(repo):
    """The live items, their labels, and blocked_by over the live subgraph — one call per 100."""
    owner, name = repo.split("/")
    issues, cursor = {}, None
    while True:
        page = graphql(GRAPH_QUERY, owner=owner, name=name,
                       **({"cursor": cursor} if cursor else {}))["repository"]["issues"]
        for node in page["nodes"]:
            if node["closed"]:
                continue          # a terminal item is not part of the set being ordered
            issues[node["number"]] = {
                "title": node["title"],
                "labels": [l["name"] for l in node["labels"]["nodes"]],
                "blocked_by": [(b["number"], b["closed"]) for b in node["blockedBy"]["nodes"]],
            }
        if not page["pageInfo"]["hasNextPage"]:
            return issues
        cursor = page["pageInfo"]["endCursor"]


def landing(repo, number):
    """The pull request that closed an issue and its merge commit, for the plan's landed record."""
    owner, name = repo.split("/")
    issue = graphql(LANDING_QUERY, owner=owner, name=name, number=number)["repository"]["issue"]
    if issue is None:
        return None, None, None
    nodes = issue["closedByPullRequestsReferences"]["nodes"]
    if not nodes:
        return issue["title"], None, None
    merge = nodes[-1]["mergeCommit"]
    return issue["title"], nodes[-1]["number"], (merge or {}).get("oid")


def plan_rows(path):
    """Row label -> (issues cell, issue numbers). Only the issues cell places an issue."""
    rows, inside = {}, False
    with open(path) as handle:
        for line in handle:
            if line.startswith("| row |"):
                inside = True
                continue
            if not inside:
                continue
            if not line.startswith("|"):
                break
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if len(cells) < 2 or not cells[0].isdigit():
                continue  # `| — |` and every other non-integer label is a retired row
            rows[int(cells[0])] = (cells[1], [int(n) for n in re.findall(r"#(\d+)", cells[1])])
    return rows


def same_row_order(cell, blocker, dependent):
    """How this row's issues cell states the order a same-row edge needs. Three values:

    `stated`     — the blocker is written first with an arrow between the two. Nothing to do.
    `reading`    — the blocker is written first but with no arrow: the order is implied only.
                   A notation gap: reading order states nothing, so the arrow gets written.
    `contradicted` — the dependent is written first. The cell says the opposite of the graph.
    """
    first = {}
    for match in re.finditer(r"#(\d+)", cell):
        first.setdefault(int(match.group(1)), match.start())
    if blocker not in first or dependent not in first:
        return "contradicted"
    lo, hi = first[blocker], first[dependent]
    if lo > hi:
        return "contradicted"
    return "stated" if ("→" in cell[lo:hi] or "->" in cell[lo:hi]) else "reading"


def digest(path):
    with open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()[:12]


def load_snapshot(path):
    try:
        with open(path) as handle:
            return json.load(handle)
    except (OSError, ValueError):
        return None


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repo", default=None, help="default: this tree's own repository")
    ap.add_argument("--plan", default=None, help=f"default: the one {PLAN_GLOB} in the session store")
    ap.add_argument("--snapshot", default=None, help="default: beside the plan")
    ap.add_argument("--stamp", action="store_true",
                    help="write the snapshot as the new baseline after reporting")
    ap.add_argument("--tested", default="",
                    help="issue numbers whose require-versus-tolerate test was run and answered "
                         "'no edge'; recorded on --stamp so they stop being re-flagged")
    args = ap.parse_args()
    tested_now = {int(n) for n in re.findall(r"\d+", args.tested)}
    args.repo = args.repo or resolve_repo()
    args.plan = args.plan or resolve_plan()
    args.snapshot = args.snapshot or os.path.join(os.path.dirname(args.plan), SNAPSHOT_NAME)

    issues = live(args.repo)
    live_items = sorted(issues)
    rows = plan_rows(args.plan)
    snapshot = load_snapshot(args.snapshot)
    baseline = set(snapshot.get("items", [])) if snapshot else None
    # Anything a stamped pass left unresolved stays "new" for the checks that scope to new
    # filings, or stamping over a residue would hide it from every later run.
    carried = snapshot.get("carried", {}) if snapshot else {}
    # An item whose test was run and answered "no edge" is settled; it is not a pending question.
    tested = set(snapshot.get("tested", [])) | tested_now
    if baseline is not None:
        baseline -= (set(carried.get("unplaced", []))
                     | set(carried.get("isolated_new", []))) - tested
    placement = collections.defaultdict(list)
    for row, (_cell, numbers) in rows.items():
        for number in numbers:
            placement[number].append(row)

    edges = sorted((b, n) for n in live_items for b, _closed in issues[n]["blocked_by"])
    live_edges = sorted((b, n) for n in live_items
                        for b, closed in issues[n]["blocked_by"] if not closed)

    print(f"plan                 : {args.plan}")
    print(f"  last written       : {subprocess.run(['stat', '-f', '%Sm', args.plan], capture_output=True, text=True).stdout.strip()}  sha {digest(args.plan)}")
    print(f"live items           : {len(live_items)}")

    # --- priority tiers: counted, never inferred, never fixed here ---
    tiers = collections.Counter()
    offenders, unlabelled = [], []
    for number in live_items:
        labels = [l for l in issues[number]["labels"] if l.startswith("P: ")]
        tier = labels[0] if labels else "none"
        tiers[tier] += 1
        if tier == "none":
            unlabelled.append(number)
        elif tier not in TIERS:
            offenders.append((number, tier))
    print("  P: tiers           : " + ", ".join(
        f"{tier} {count}" for tier, count in sorted(tiers.items())))
    print(f"  unlabelled         : {unlabelled}  (a legitimate state)")
    if offenders:
        print("  ⛔ BELOW P: High    : " + ", ".join(f"#{n} {t}" for n, t in offenders)
              + "   — ask; never add or raise a label to close the gap")

    # --- the graph ---
    print(f"relations (all)      : {len(edges)}   live (blocker still live): {len(live_edges)}")
    adj = collections.defaultdict(list)
    indeg = collections.Counter()
    for b, n in live_edges:
        adj[b].append(n)
        indeg[n] += 1
    queue = [n for n in live_items if indeg[n] == 0]
    seen = 0
    while queue:
        node = queue.pop()
        seen += 1
        for nxt in adj[node]:
            indeg[nxt] -= 1
            if indeg[nxt] == 0:
                queue.append(nxt)
    cyclic = seen != len(live_items)
    print(f"acyclic              : {'YES' if not cyclic else f'NO — {len(live_items) - seen} issues in or behind a cycle'}")
    if cyclic:
        print(f"  IN OR BEHIND CYCLE : {sorted(set(live_items) - set(n for n in live_items if indeg[n] <= 0))}")
    # Edge-free is a legitimate and common state, so this is scoped to what is new: an issue
    # filed since the baseline with no relation either way is the one that needs the test run.
    no_relation = [n for n in live_items
                   if not issues[n]["blocked_by"] and not any(b == n for b, _ in edges)]
    if baseline is None:
        print(f"  isolated (no edge) : {len(no_relation)}  — scoped to new filings once a baseline exists")
    else:
        fresh = [n for n in no_relation if n not in baseline and n not in tested]
        print(f"  isolated (no edge) : {len(no_relation)}, of them filed since the last pass: {fresh or 'none'}"
              + ("  — apply the require-not-tolerate test to each, then say the answer" if fresh else ""))

    # --- coverage of the row table ---
    unplaced = [n for n in live_items if n not in placement]
    twice = {n: r for n, r in placement.items() if len(r) > 1}
    closed_placed = sorted(n for n in placement if n not in live_items)
    print(f"placed               : {len(live_items) - len(unplaced)}/{len(live_items)}")
    if unplaced:
        print(f"  UNPLACED           : {unplaced}  — place into an existing row; a row label must be an integer")
    if twice:
        print(f"  PLACED TWICE       : {twice}")
    for number in closed_placed:
        row = placement[number][0]
        others = [n for n in rows[row][1] if n != number and n in live_items]
        title, pr, sha = landing(args.repo, number)
        short = (sha or "")[:7]
        print(f"  LANDED, still placed: #{number} in row {row}"
              + (f" — closed by #{pr} `{short}`" if pr else " — no closing pull request found"))
        if others:
            print(f"      shared row (also {others}) → remove #{number} from the issues cell and"
                  f" record `✅ **#{number} landed \\`{short}\\`**` in the why column, keeping the row's argument")
        else:
            print(f"      sole issue in the row → retire it: `| — | **#{number}** — ✅ **landed \\`{short}\\`, <date>** | <keep the why> |`")

    # --- ordering ---
    violations, same_row = [], []
    for b, n in live_edges:
        rb, rn = placement.get(b), placement.get(n)
        if rb is None or rn is None:
            continue
        if min(rb) > min(rn):
            violations.append((b, min(rb), n, min(rn)))
        elif min(rb) == min(rn):
            same_row.append((b, n, min(rb)))
    print(f"ordering violations  : {len(violations)}")
    for b, rb, n, rn in sorted(violations):
        print(f"  VIOLATION          : #{b} (row {rb}) blocks #{n} (row {rn})")
    verdicts = collections.defaultdict(list)
    for b, n, r in same_row:
        verdicts[same_row_order(rows[r][0], b, n)].append((b, n, r))
    print(f"same-row edges       : {len(same_row)}  "
          + ", ".join(f"{k} {len(v)}" for k, v in sorted(verdicts.items())))
    for b, n, r in sorted(verdicts["contradicted"]):
        print(f"  ⛔ CELL CONTRADICTS : row {r}: #{b} blocks #{n}, and the cell writes #{n} first")
    for b, n, r in sorted(verdicts["reading"]):
        print(f"  arrow absent       : row {r}: #{b} → #{n}, order implied by reading order only")

    # --- the snapshot diff: the only cheap way to see a relation change ---
    if snapshot is None:
        print("\nsince last pass      : no snapshot yet — run with --stamp to set the baseline")
    else:
        was_live = set(snapshot.get("items", []))
        was_edges = {tuple(e) for e in snapshot.get("edges", [])}
        print(f"\nsince {snapshot.get('at', 'the last pass')} (snapshot of the last stamped pass):")
        show = lambda es: ", ".join(f"#{b}→#{n}" for b, n in sorted(es)) or "none"
        gone = was_edges - set(edges)
        print(f"  filed              : {sorted(set(live_items) - was_live) or 'none'}")
        print(f"  no longer live     : {sorted(was_live - set(live_items)) or 'none'}")
        print(f"  relations added    : {show(set(edges) - was_edges)}")
        # An edge also disappears when its dependent closes; that is the issue landing, not a
        # relation anybody removed, and only the first list is a graph edit to account for.
        print(f"  relations removed  : {show(e for e in gone if e[1] in issues)}")
        print(f"  edges off with a landing: {show(e for e in gone if e[1] not in issues)}")
        if snapshot.get("plan_sha") not in (None, digest(args.plan)):
            print("  ⚠️ the plan file changed since that pass — possibly a sibling session; re-read before editing")

    # --- what is takeable ---
    ready = sorted(n for n in live_items
                   if not any(not closed for _b, closed in issues[n]["blocked_by"]))
    print(f"\nunblocked now        : {len(ready)}")
    for number in ready:
        row = min(placement.get(number, [-1]))
        print(f"  row {row!s:>3}  #{number}  {issues[number]['title'][:66]}")

    dirty = bool(violations or unplaced or twice or closed_placed or cyclic or offenders
                 or verdicts["contradicted"])
    still_carried = sorted((set(carried.get("unplaced", []) + carried.get("isolated_new", []))
                            & (set(unplaced) | set(no_relation))) - tested)
    if still_carried:
        print(f"\ncarried unresolved   : {still_carried}  — flagged by an earlier pass and still open")
    if args.stamp:
        with open(args.snapshot, "w") as handle:
            json.dump({
                "at": subprocess.run(["date", "-u", "+%Y-%m-%dT%H:%M:%SZ"],
                                     capture_output=True, text=True).stdout.strip(),
                "items": live_items,
                "edges": [list(e) for e in edges],
                "rows": {str(n): r for n, r in placement.items()},
                "plan_sha": digest(args.plan),
                "clean": not dirty,
                # Residue left behind, so a stamp cannot bury it: these stay "new" next run.
                "carried": {
                    "unplaced": unplaced,
                    "isolated_new": [n for n in no_relation
                                     if (baseline is None or n not in baseline) and n not in tested],
                },
                "tested": sorted(tested & set(live_items)),
            }, handle, indent=1)
        print(f"\nsnapshot stamped     : {args.snapshot}"
              + ("  ⚠️ stamped while not clean" if dirty else ""))
    return 1 if dirty else 0


if __name__ == "__main__":
    sys.exit(main())
