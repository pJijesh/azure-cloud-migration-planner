"""Regenerate the parts of the documentation that are built from data.

* docs/disposition-rules.md: the rule table between the markers, from migration_planner/default_rules.json
* docs/landing-zone-readiness.md: from docs/landing-zone-readiness.csv

Run `python tools/build_docs.py` to write, or `python tools/build_docs.py --check` to fail if a file is stale.
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from migration_planner.model import DISPOSITIONS  # noqa: E402
from migration_planner.rules import load_rules  # noqa: E402

START, END = "<!-- rules-table:start -->", "<!-- rules-table:end -->"
AREA_ORDER = ["Billing and tenant", "Resource organisation", "Identity", "Network", "Security", "Governance",
              "Monitoring", "Backup and DR", "Cost management", "Automation", "Operating model"]
AREA_ABOUT = {
    "Billing and tenant": "Who pays, and which directory the estate belongs to.",
    "Resource organisation": "Management groups, subscriptions, naming, tags and regions.",
    "Identity": "How people and workloads sign in and what they may do.",
    "Network": "Addressing, connectivity, name resolution, filtering and segmentation.",
    "Security": "Baseline, posture management, keys, logging and incident response.",
    "Governance": "Policy, standards, decision rights and guard rails.",
    "Monitoring": "Visibility, alerting and patching.",
    "Backup and DR": "Recovery objectives, backup, restore tests, disaster recovery and rollback.",
    "Cost management": "Budgets, tags, review, licences and commitments.",
    "Automation": "Infrastructure as code and runbooks.",
    "Operating model": "Skills, support and migration tooling.",
}


def _cond(c) -> str:
    if "all" in c:
        return " and ".join(_cond(x) for x in c["all"])
    if "any" in c:
        return " or ".join(_cond(x) for x in c["any"])
    op = {"eq": "=", "ne": "is not", "lt": "<", "lte": "<=", "gt": ">", "gte": ">=", "in": "is one of",
          "not_in": "is not one of", "contains_any": "mentions any of", "is_blank": "is blank", "not_blank": "is not blank"}[c["op"]]
    if c["op"] in ("is_blank", "not_blank"):
        return f"`{c['field']}` {op}"
    v = c["value"]
    if isinstance(v, list):
        v = ", ".join(str(x) for x in v)
    return f"`{c['field']}` {op} {v if not str(v).startswith('@') else '`' + v + '`'}"


def _points(rule) -> str:
    if "force" in rule:
        return f"decides: {rule['force']['disposition']} (out of scope)" if rule["force"].get("in_scope") is False else f"decides: {rule['force']['disposition']}"
    parts = []
    for d in DISPOSITIONS:
        p = rule.get("points", {}).get(d)
        if p:
            parts.append(f"{d} {'+' if p > 0 else ''}{p}")
    return ", ".join(parts)


def render_rules_table() -> str:
    rules = load_rules()
    lines = ["| ID | Rule | When | Points | Reason given in the output |", "|---|---|---|---|---|"]
    for r in rules["rules"]:
        reason = r["reason"].replace("|", "/")
        lines.append(f"| {r['id']} | {r['name']} | {_cond(r['when'])} | {_points(r)} | {reason} |")
    lines.append("")
    base = ", ".join(f"{d} {v}" for d, v in rules["baseline"].items() if v)
    lines.append(f"Baseline points before any rule: {base}.")
    lines.append("")
    lines.append("Keyword lists used by the rules (whole words, case-insensitive, a plural ending is accepted):")
    lines.append("")
    for name, words in rules["keywords"].items():
        lines.append(f"- `{name}`: {', '.join(words)}")
    lines.append("")
    lines.append("Technology classes, matched in this order against `technology` (first match wins; anything else is `other`):")
    lines.append("")
    for e in rules["tech_classes"]:
        lines.append(f"- `{e['class']}`: {', '.join(e['keywords'])}")
    return "\n".join(lines)


def build_rules_doc(current: str) -> str:
    i, j = current.index(START), current.index(END)
    return current[: i + len(START)] + "\n\n" + render_rules_table() + "\n\n" + current[j:]


def load_checklist():
    with open(ROOT / "docs" / "landing-zone-readiness.csv", newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def render_checklist() -> str:
    rows = load_checklist()
    out = [
        "# Landing zone readiness checklist",
        "",
        "<!-- Generated from landing-zone-readiness.csv by tools/build_docs.py. Edit the CSV, not this file. -->",
        "",
        "A landing zone is the prepared Azure environment that workloads move into: tenant and billing, subscriptions, identity, network, "
        "security, monitoring, backup, governance and cost controls. Microsoft's Azure landing zone guidance groups the design work into "
        "design areas, shown in the second column of the CSV. This checklist is organised by the topics a migration programme has to "
        "answer, and each item says which wave it has to be done before.",
        "",
        "How to use it: copy [landing-zone-readiness.csv](landing-zone-readiness.csv), fill `owner`, `status` (not started, in progress, done, "
        "not applicable) and `notes`, and review it at each wave gate. An item marked done needs the evidence named beside it.",
        "",
        "Timing values: **pilot wave** (before the first workload moves), **first production wave**, **each wave** (repeat for every wave), "
        "**programme end**.",
        "",
        "It is a starting list, not an exhaustive design. Compare it with Microsoft's current landing zone guidance and with your own "
        "security and regulatory requirements. See [sources and verification](sources-and-verification.md).",
        "",
    ]
    for area in AREA_ORDER:
        items = [r for r in rows if r["area"] == area]
        if not items:
            continue
        out += [f"## {area}", "", AREA_ABOUT[area], ""]
        for r in items:
            out.append(f"- [ ] **{r['id']}** {r['check']} *Needed before: {r['needed_before']}.* Why: {r['why_it_matters']} Evidence: {r['evidence_to_collect']}")
        out.append("")
    return "\n".join(out).rstrip() + "\n"


def main(argv) -> int:
    check = "--check" in argv
    targets = {
        ROOT / "docs" / "disposition-rules.md": build_rules_doc((ROOT / "docs" / "disposition-rules.md").read_text(encoding="utf-8")),
        ROOT / "docs" / "landing-zone-readiness.md": render_checklist(),
    }
    stale = []
    for path, text in targets.items():
        if not path.exists() or path.read_text(encoding="utf-8") != text:
            stale.append(path.name)
            if not check:
                path.write_text(text, encoding="utf-8", newline="\n")
    if check and stale:
        print("stale: " + ", ".join(stale) + ". Run python tools/build_docs.py", file=sys.stderr)
        return 1
    print("up to date" if check else "wrote " + ", ".join(p.name for p in targets))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
