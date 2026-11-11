"""Glue between the loaders, the engines and the output files."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from datetime import date
from pathlib import Path

from . import __version__
from .assess import apply_overrides, assess_all, load_overrides
from .assumptions import load_assumptions
from .cost import build_cost
from .errors import ValidationError
from .inventory import load_inventory, parse_date
from .model import DISPOSITIONS
from .rules import load_rules, rules_hash
from .serialise import assessed_from_dict, assessed_to_dict, assessment_csv, csv_text, dumps
from .waves import build_waves, waves_mermaid


def _sha(path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def resolve_as_of(as_of_arg, rules):
    """Return (date, warnings). An explicit date keeps results reproducible."""
    if as_of_arg:
        try:
            return parse_date(as_of_arg), []
        except ValueError as exc:
            raise ValidationError(f"--as-of: {exc}") from None
    default = rules["settings"].get("default_as_of")
    if default:
        return parse_date(default), []
    return date.today(), [
        "No --as-of date was given, so today's date was used to judge end of support. "
        "Pass --as-of YYYY-MM-DD to make results reproducible."
    ]


def summarise(assessed) -> dict:
    counts = Counter(a.disposition for a in assessed)
    cost = {d: 0.0 for d in DISPOSITIONS}
    for a in assessed:
        cost[a.disposition] += a.app.current_annual_cost or 0
    return {
        "applications": len(assessed),
        "in_scope": sum(1 for a in assessed if a.in_scope),
        "needs_review": sum(1 for a in assessed if a.needs_review),
        "by_disposition": {d: counts[d] for d in DISPOSITIONS},
        "current_annual_cost_by_disposition": {d: round(cost[d], 2) for d in DISPOSITIONS},
    }


def assess_inventory(path, rules, as_of, overrides_path=None, allow_unknown=False):
    apps, warnings = load_inventory(path, allow_unknown)
    assessed = assess_all(apps, rules, as_of)
    if overrides_path:
        apply_overrides(assessed, load_overrides(overrides_path), Path(overrides_path).name)
    meta = {
        "inventory_file": Path(path).name,
        "inventory_sha256": _sha(path),
        "overrides_file": Path(overrides_path).name if overrides_path else None,
        "overrides_sha256": _sha(overrides_path) if overrides_path else None,
        "rules_sha256": rules_hash(rules),
        "as_of": as_of.isoformat(),
    }
    return assessed, meta, warnings


def load_input(path, args, rules):
    """Accept an inventory CSV (assessed on the fly) or an assessment JSON from the assess command."""
    p = Path(path)
    if not p.is_file():
        raise ValidationError(f"input file not found: {p}")
    if p.suffix.lower() == ".json":
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ValidationError(f"{p.name}: not valid JSON ({exc})") from None
        if not isinstance(data, dict) or data.get("kind") != "assessment" or "apps" not in data:
            raise ValidationError(f"{p.name}: this is not an assessment file written by the assess command")
        assessed = [assessed_from_dict(d, p.name) for d in data["apps"]]
        ids = {a.app.app_id for a in assessed}
        for a in assessed:
            bad = [d for d in a.app.dependencies if d not in ids]
            if bad:
                raise ValidationError(f"{p.name}: {a.app.app_id} depends on unknown id(s) {', '.join(bad)}")
        return assessed, dict(data["inputs"]), list(data.get("warnings", []))
    as_of, notes = resolve_as_of(getattr(args, "as_of", None), rules)
    assessed, meta, warnings = assess_inventory(
        p, rules, as_of, getattr(args, "overrides", None), getattr(args, "allow_unknown_dependencies", False)
    )
    return assessed, meta, notes + warnings


def assessment_document(assessed, meta, warnings) -> dict:
    return {
        "tool": "migration_planner",
        "version": __version__,
        "kind": "assessment",
        "inputs": meta,
        "summary": summarise(assessed),
        "warnings": warnings,
        "apps": [assessed_to_dict(a) for a in assessed],
    }


def waves_csv(assessed, plan) -> str:
    by_id = {a.app.app_id: a for a in assessed}
    header = ["wave", "app_id", "name", "disposition", "business_criticality", "shared_service", "cycle_group", "depends_on", "status"]
    rows = []
    for m, p in plan["placement"].items():
        a = by_id[m]
        rows.append([p["wave"], m, a.app.name, a.disposition, a.app.business_criticality,
                     "yes" if p["shared_service"] else "no", p["cycle_group"], ";".join(a.app.dependencies), "scheduled"])
    rows.sort(key=lambda r: (r[0], r[1]))
    for m, why in plan["not_scheduled"].items():
        a = by_id[m]
        rows.append(["", m, a.app.name, a.disposition, a.app.business_criticality, "", "", ";".join(a.app.dependencies), f"not scheduled: {why}"])
    return csv_text(header, rows)


def waves_document(plan, meta) -> dict:
    return {"tool": "migration_planner", "version": __version__, "kind": "waves", "inputs": meta, **plan}


def cost_files(cost) -> dict:
    """Return {filename: text} for the cost outputs."""
    res = cost["result"]
    cur = cost["currency"]
    H = res["months"]
    r2 = lambda x: f"{x:.2f}"  # noqa: E731
    cats = list(res["stay"]["categories"])
    summary_rows = [
        ["total_cost_over_horizon", r2(res["stay"]["total"]), r2(res["migrate"]["total"]), r2(res["migrate"]["total"] - res["stay"]["total"])],
    ]
    for y in range(H // 12):
        summary_rows.append([f"year_{y + 1}", r2(res["stay"]["by_year"][y]), r2(res["migrate"]["by_year"][y]),
                             r2(res["migrate"]["by_year"][y] - res["stay"]["by_year"][y])])
    summary_rows.append(["final_year_recurring_run_cost", r2(res["stay"]["final_year_run_cost"]), r2(res["migrate"]["final_year_run_cost"]),
                         r2(res["migrate"]["final_year_run_cost"] - res["stay"]["final_year_run_cost"])])
    if "npv" in res["stay"]:
        summary_rows.append(["present_value_at_discount_rate", r2(res["stay"]["npv"]), r2(res["migrate"]["npv"]), r2(res["migrate"]["npv"] - res["stay"]["npv"])])
    for c in cats:
        summary_rows.append([f"category_{c}", r2(res["stay"]["by_category"][c]), r2(res["migrate"]["by_category"][c]),
                             r2(res["migrate"]["by_category"][c] - res["stay"]["by_category"][c])])
    summary_rows.append(["break_even_month", "", res["break_even_month"] if res["break_even_month"] is not None else "not within horizon", ""])
    files = {
        "cost_summary.csv": csv_text(["measure", f"stay_on_premises_{cur}", f"follow_plan_{cur}", f"difference_{cur}"], summary_rows),
    }
    header = ["month", "stay_total", "plan_total", "difference", "cumulative_difference"]
    header += [f"stay_{c}" for c in cats] + [f"plan_{c}" for c in cats]
    rows = []
    for m in range(H):
        row = [m + 1, r2(res["stay"]["monthly"][m]), r2(res["migrate"]["monthly"][m]),
               r2(res["migrate"]["monthly"][m] - res["stay"]["monthly"][m]), r2(res["cumulative_difference"][m])]
        row += [r2(res["stay"]["categories"][c][m]) for c in cats]
        row += [r2(res["migrate"]["categories"][c][m]) for c in cats]
        rows.append(row)
    files["cost_monthly.csv"] = csv_text(header, rows)
    header = ["app_id", "name", "disposition", "wave", "cutover_month", "on_prem_annual_cost", "azure_annual_cost",
              "azure_cost_method", "migration_effort_cost", "stay_total", "plan_run_total"]
    rows = [[p["app_id"], p["name"], p["disposition"], p["wave"], p["cutover_month"], r2(p["on_prem_annual_cost"]),
             r2(p["azure_annual_cost"]), p["azure_cost_method"], r2(p["migration_effort_cost"]), r2(p["stay_total"]),
             r2(p["migrate_run_total"])] for p in res["per_app"]]
    files["cost_by_app.csv"] = csv_text(header, rows)
    header = ["case", "direction", "stay_total", "plan_total", "saving", "saving_change_vs_base", "break_even_month"]
    rows = [[s["case"], s["direction"], r2(s["stay_total"]), r2(s["migrate_total"]), r2(s["saving"]),
             r2(s["saving_change_vs_base"]), s["break_even_month"] if s["break_even_month"] is not None else "not within horizon"]
            for s in cost["sensitivity"]]
    files["sensitivity.csv"] = csv_text(header, rows)
    return files


def cost_document(cost, meta, assumptions_hash) -> dict:
    res = cost["result"]

    def compact(s):
        return {k: (round(v, 2) if isinstance(v, float) else v) for k, v in s.items()
                if k not in ("monthly", "categories", "by_year", "by_category")} | {
            "by_year": [round(x, 2) for x in s["by_year"]],
            "by_category": {k: round(v, 2) for k, v in s["by_category"].items()},
        }

    return {
        "tool": "migration_planner",
        "version": __version__,
        "kind": "cost",
        "inputs": {**meta, "assumptions_sha256": assumptions_hash},
        "currency": cost["currency"],
        "horizon_years": cost["horizon_years"],
        "illustrative": cost["illustrative"],
        "label": cost["label"],
        "discount_rate": cost["discount_rate"],
        "stay": compact(res["stay"]),
        "plan": compact(res["migrate"]),
        "saving": round(res["saving"], 2),
        "saving_pct": round(res["saving_pct"], 1),
        "break_even_month": res["break_even_month"],
        "break_even_month_discounted": res["break_even_month_discounted"],
        "timing": res["timing"],
        "counts": res["counts"],
        "azure_cost_methods": cost["azure_cost_methods"],
        "sensitivity": [{k: (round(v, 2) if isinstance(v, float) else v) for k, v in s.items()} for s in cost["sensitivity"]],
        "warnings": cost["warnings"],
        "not_modelled": cost["not_modelled"],
    }


def run_assess(args, rules):
    assessed, meta, warnings = load_input(args.input, args, rules)
    return assessed, meta, warnings


def run_waves(assessed, rules, max_wave_size=None):
    plan = build_waves(assessed, rules, max_wave_size)
    return plan


def run_cost(assessed, plan, assumptions_path):
    A, h = load_assumptions(assumptions_path)
    return build_cost(assessed, plan, A), A, h


def mermaid_text(plan, assessed):
    return waves_mermaid(plan, assessed)


def write_files(out_dir, files: dict) -> list:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    for name in sorted(files):
        (out / name).write_text(files[name], encoding="utf-8", newline="\n")
    return sorted(files)
