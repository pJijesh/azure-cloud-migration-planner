"""Load and validate the cost assumptions file.

The template that ships with the package has every number empty. The model refuses to run until
each required input has been supplied, so a number never appears in a result that nobody chose.
"""

from __future__ import annotations

import hashlib
import json
from importlib import resources
from pathlib import Path

from .errors import ValidationError

TEMPLATE_HINT = "Run 'python -m migration_planner show-assumptions-template' for a blank template."


def template_text() -> str:
    return resources.files("migration_planner").joinpath("default_assumptions_template.json").read_text(encoding="utf-8")


def _num(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _get(d, path):
    cur = d
    for part in path.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return None, False
        cur = cur[part]
    return cur, True


def validate_assumptions(a: dict, name: str = "assumptions") -> None:
    problems: list[str] = []

    def need(path, low=None, high=None, integer=False, optional=False):
        value, present = _get(a, path)
        if value is None:
            if not optional:
                problems.append(f"'{path}' is empty. Supply a value from your own data. {TEMPLATE_HINT}")
            return
        if not _num(value):
            problems.append(f"'{path}' must be a number, not {value!r}")
            return
        if integer and value != int(value):
            problems.append(f"'{path}' must be a whole number")
        if low is not None and value < low:
            problems.append(f"'{path}' is {value} but must be at least {low}")
        if high is not None and value > high:
            problems.append(f"'{path}' is {value} but must be at most {high}")

    if not isinstance(a, dict):
        raise ValidationError(f"{name}: the top level must be a JSON object")
    if not isinstance(a.get("currency"), str) or not a.get("currency"):
        problems.append("'currency' must be a short text label such as GBP")
    need("horizon_years", 1, 10, integer=True)
    need("discount_rate", -0.5, 1, optional=True)
    need("timing.landing_zone_months", 0, 60, integer=True)
    need("timing.months_per_wave", 1, 60)
    need("timing.parallel_run_months", 0, 36, integer=True)
    need("on_prem.annual_cost_inflation", -0.5, 1)
    need("on_prem.cost_removed_share", 0, 1)
    need("on_prem.hardware_refresh_amount", 0)
    hw, _ = _get(a, "on_prem.hardware_refresh_amount")
    if _num(hw) and hw > 0:
        need("on_prem.hardware_refresh_month", 1, (a.get("horizon_years") or 10) * 12, integer=True)
    else:
        need("on_prem.hardware_refresh_month", 1, optional=True, integer=True)
    need("azure.annual_cost_inflation", -0.5, 1)
    for d in ("rehost", "replatform", "refactor", "repurchase"):
        need(f"azure.run_cost_factor.{d}", 0)
    need("azure.retire_archive_annual_per_app", 0)
    need("unit_costs.engineer_day_rate", 0)
    need("unit_costs.saas_per_user_per_year", 0, optional=True)
    need("unit_costs.saas_fixed_per_app_per_year", 0, optional=True)
    for d in ("rehost", "replatform", "refactor", "repurchase", "retire"):
        need(f"migration_effort.days_per_app.{d}", 0)
    for c in ("1", "2", "3", "4", "5"):
        need(f"migration_effort.criticality_multiplier.{c}", 0.01)
    need("migration_effort.contingency", 0, 2)
    for k in ("landing_zone_one_off", "landing_zone_annual", "connectivity_annual", "programme_management_one_off"):
        need(f"platform.{k}", 0)

    others = a.get("other_costs", [])
    if not isinstance(others, list):
        problems.append("'other_costs' must be a list")
    else:
        for i, item in enumerate(others):
            w = f"other_costs[{i}]"
            if not isinstance(item, dict):
                problems.append(f"{w} must be an object")
                continue
            if not item.get("label"):
                problems.append(f"{w}: 'label' is required")
            if item.get("kind") not in ("one_off", "annual"):
                problems.append(f"{w}: 'kind' must be one_off or annual")
            if item.get("scenario") not in ("migrate", "stay", "both"):
                problems.append(f"{w}: 'scenario' must be migrate, stay or both")
            if not _num(item.get("amount")) or item.get("amount") < 0:
                problems.append(f"{w}: 'amount' must be a number of zero or more")
            month = item.get("month")
            if not _num(month) or month != int(month) or month < 1:
                problems.append(f"{w}: 'month' must be a whole number of 1 or more (the month the cost starts)")
    if problems:
        raise ValidationError([f"{name}: {p}" for p in problems])


def load_assumptions(path):
    path = Path(path)
    if not path.is_file():
        raise ValidationError(f"cost assumptions file not found: {path}")
    raw = path.read_text(encoding="utf-8-sig")
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValidationError(f"{path.name}: not valid JSON ({exc})") from None
    validate_assumptions(data, path.name)
    return data, hashlib.sha256(raw.encode("utf-8")).hexdigest()
