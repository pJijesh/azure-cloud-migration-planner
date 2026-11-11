"""Command line interface: python -m migration_planner <command>."""

from __future__ import annotations

import argparse
import sys

from . import __version__
from .assumptions import template_text
from .errors import PlannerError
from .model import DISPOSITIONS
from .pipeline import (
    assessment_document,
    cost_document,
    cost_files,
    load_input,
    mermaid_text,
    run_cost,
    run_waves,
    waves_csv,
    waves_document,
    write_files,
)
from .report import render_plan
from .rules import default_rules_text, load_rules
from .serialise import assessment_csv, dumps


def _common(p, assumptions=False, waves=False):
    p.add_argument("input", help="inventory CSV, or an assessment.json written by the assess command")
    p.add_argument("--rules", help="rules JSON (see show-rules). Default: the built-in rules")
    p.add_argument("--as-of", help="date used to judge end of support, YYYY-MM-DD. Give one for reproducible output")
    p.add_argument("--overrides", help="CSV of human decisions: app_id, disposition, reason")
    p.add_argument("--allow-unknown-dependencies", action="store_true",
                   help="warn instead of failing when a dependency id is not in the inventory")
    p.add_argument("--out", default="output", help="folder for output files (default: output)")
    if waves:
        p.add_argument("--max-wave-size", type=int, help="override the wave size limit, in applications")
        p.add_argument("--fail-on-cycles", action="store_true", help="exit with status 3 if a circular dependency is found")
    if assumptions:
        p.add_argument("--assumptions", required=True, help="cost assumptions JSON (see show-assumptions-template)")


def build_parser():
    ap = argparse.ArgumentParser(
        prog="migration_planner",
        description="Recommend a migration disposition for each application, sequence waves from dependencies, "
                    "and compare run cost on premises and in Azure. A planning aid, not a substitute for Azure Migrate "
                    "discovery or a vendor quote.",
    )
    ap.add_argument("--version", action="version", version=f"migration_planner {__version__}")
    sub = ap.add_subparsers(dest="command", required=True)
    _common(sub.add_parser("assess", help="assign a disposition to each application, with reasons"))
    _common(sub.add_parser("waves", help="build migration waves from the dependency graph"), waves=True)
    _common(sub.add_parser("cost", help="compare run cost on premises and in Azure"), assumptions=True, waves=True)
    _common(sub.add_parser("plan", help="run assess, waves and cost, and write a Markdown plan"), assumptions=True, waves=True)
    sub.add_parser("show-rules", help="print the built-in rules as JSON, to copy and edit")
    sub.add_parser("show-assumptions-template", help="print a blank cost assumptions file")
    return ap


def _say(msg=""):
    print(msg)


def _assess_summary(assessed, warnings):
    counts = {d: sum(1 for a in assessed if a.disposition == d) for d in DISPOSITIONS}
    _say(f"Assessed {len(assessed)} applications: " + ", ".join(f"{n} {d}" for d, n in counts.items() if n))
    _say(f"{sum(1 for a in assessed if a.needs_review)} need a human decision.")
    for w in warnings:
        _say(f"warning: {w}")


def _waves_summary(plan):
    _say(f"{plan['wave_count']} wave(s) for {len(plan['placement'])} application(s); "
         f"{len(plan['cycles'])} circular dependency group(s).")
    for w in plan["warnings"]:
        _say(f"warning: {w}")


def _cost_summary(cost):
    r = cost["result"]
    cur = cost["currency"]
    be = r["break_even_month"]
    _say(f"{cost['horizon_years']} year cost: stay {cur} {r['stay']['total']:,.0f}, plan {cur} {r['migrate']['total']:,.0f}; "
         f"the plan is {cur} {abs(r['saving']):,.0f} {'cheaper' if r['saving'] >= 0 else 'dearer'}. "
         f"Break even: {'month ' + str(be) if be else 'not within the horizon'}.")
    for w in cost["warnings"]:
        _say(f"warning: {w}")


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return _run(args)
    except PlannerError as exc:
        print("error: the input could not be used:", file=sys.stderr)
        for p in exc.problems:
            print(f"  - {p}", file=sys.stderr)
        return 2


def _run(args) -> int:
    if args.command == "show-rules":
        sys.stdout.write(default_rules_text())
        return 0
    if args.command == "show-assumptions-template":
        sys.stdout.write(template_text())
        return 0

    rules = load_rules(args.rules)
    assessed, meta, warnings = load_input(args.input, args, rules)
    out = args.out

    if args.command == "assess":
        files = {"assessment.csv": assessment_csv(assessed), "assessment.json": dumps(assessment_document(assessed, meta, warnings))}
        _assess_summary(assessed, warnings)
        names = write_files(out, files)
        _say(f"Wrote {', '.join(names)} to {out}")
        return 0

    plan = run_waves(assessed, rules, getattr(args, "max_wave_size", None))
    status = 3 if (args.fail_on_cycles and plan["cycles"]) else 0

    if args.command == "waves":
        files = {"waves.csv": waves_csv(assessed, plan), "waves.json": dumps(waves_document(plan, meta)),
                 "waves.mmd": mermaid_text(plan, assessed)}
        _waves_summary(plan)
        names = write_files(out, files)
        _say(f"Wrote {', '.join(names)} to {out}")
        return status

    cost, _A, a_hash = run_cost(assessed, plan, args.assumptions)
    if args.command == "cost":
        files = cost_files(cost)
        files["cost.json"] = dumps(cost_document(cost, meta, a_hash))
        _cost_summary(cost)
        names = write_files(out, files)
        _say(f"Wrote {', '.join(names)} to {out}")
        return status

    # plan
    files = {
        "assessment.csv": assessment_csv(assessed),
        "assessment.json": dumps(assessment_document(assessed, meta, warnings)),
        "waves.csv": waves_csv(assessed, plan),
        "waves.mmd": mermaid_text(plan, assessed),
        "plan.md": render_plan(assessed, meta, warnings, plan, cost, rules),
    }
    files.update(cost_files(cost))
    combined = {
        "tool": "migration_planner",
        "version": __version__,
        "kind": "plan",
        "assessment": assessment_document(assessed, meta, warnings),
        "waves": waves_document(plan, meta),
        "cost": cost_document(cost, meta, a_hash),
    }
    files["plan.json"] = dumps(combined)
    _assess_summary(assessed, warnings)
    _waves_summary(plan)
    _cost_summary(cost)
    names = write_files(out, files)
    _say(f"Wrote {', '.join(names)} to {out}")
    return status
