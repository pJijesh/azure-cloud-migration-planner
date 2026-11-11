"""Read and validate the application inventory CSV.

All problems are collected and reported together, with line numbers, so a bad file can be fixed
in one pass.
"""

from __future__ import annotations

import csv
import re
from datetime import date
from pathlib import Path

from .errors import ValidationError
from .model import (
    CHANGE_VALUES,
    INVENTORY_FIELDS,
    OPTIONAL_FIELDS,
    SENSITIVITY_VALUES,
    VENDOR_VALUES,
    App,
)

REQUIRED_NON_BLANK = ("app_id", "name", "business_criticality")
_YES_NO = {"y": "yes", "yes": "yes", "n": "no", "no": "no", "unknown": "unknown", "": "unknown"}


def parse_date(text: str) -> date:
    """Parse an ISO date (YYYY-MM-DD). Raises ValueError with a readable message."""
    try:
        return date.fromisoformat(text)
    except ValueError:
        raise ValueError(f"'{text}' is not a date in YYYY-MM-DD form") from None


def _number(text: str, what: str, problems: list, where: str, integer: bool = False):
    cleaned = re.sub(r"[\s,£$€]", "", text)
    if cleaned == "":
        return None
    try:
        value = float(cleaned)
    except ValueError:
        problems.append(f"{where}: {what} '{text}' is not a number")
        return None
    if value < 0:
        problems.append(f"{where}: {what} '{text}' must not be negative")
        return None
    if integer:
        if value != int(value):
            problems.append(f"{where}: {what} '{text}' must be a whole number")
            return None
        return int(value)
    return value


def load_inventory(path, allow_unknown_dependencies: bool = False):
    """Return (apps, warnings). Raises ValidationError listing every problem found."""
    path = Path(path)
    if not path.is_file():
        raise ValidationError(f"inventory file not found: {path}")
    try:
        text = path.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError:
        raise ValidationError(f"{path.name}: not valid UTF-8 text. Save the CSV as UTF-8.") from None

    problems: list[str] = []
    warnings: list[str] = []
    reader = csv.DictReader(text.splitlines(keepends=True))
    if reader.fieldnames is None:
        raise ValidationError(f"{path.name}: the file is empty")
    headers = [h.strip().lower() for h in reader.fieldnames]
    reader.fieldnames = headers
    missing = [f for f in INVENTORY_FIELDS if f not in headers]
    if missing:
        raise ValidationError(
            f"{path.name}: missing column(s): {', '.join(missing)}. "
            f"Expected columns: {', '.join(INVENTORY_FIELDS)}"
        )
    known = set(INVENTORY_FIELDS) | set(OPTIONAL_FIELDS)
    extra = [h for h in headers if h not in known]
    if extra:
        warnings.append(f"Ignored unrecognised column(s): {', '.join(extra)}")

    apps: list[App] = []
    raw_deps: dict[str, list[str]] = {}
    seen: dict[str, int] = {}
    for row in reader:
        line = reader.line_num
        if all((v or "").strip() == "" for v in row.values()):
            continue
        cell = {k: (v or "").strip() for k, v in row.items() if k is not None}
        app_id = cell["app_id"]
        where = f"line {line} ({app_id or 'no app_id'})"
        for name in REQUIRED_NON_BLANK:
            if cell[name] == "":
                problems.append(f"{where}: {name} is required")
        if app_id:
            if re.search(r"[;,\s]", app_id):
                problems.append(f"{where}: app_id must not contain spaces, commas or semicolons")
            if app_id in seen:
                problems.append(f"{where}: app_id '{app_id}' already used on line {seen[app_id]}")
            else:
                seen[app_id] = line

        crit = _number(cell["business_criticality"], "business_criticality", problems, where, True)
        if crit is not None and not 1 <= crit <= 5:
            problems.append(f"{where}: business_criticality {crit} must be between 1 and 5")
            crit = None
        users = _number(cell["users"], "users", problems, where, True)
        cost = _number(cell["current_annual_cost"], "current_annual_cost", problems, where)
        estimate = _number(
            cell.get("azure_annual_cost_estimate", ""), "azure_annual_cost_estimate", problems, where
        )

        eos = None
        if cell["end_of_support_date"]:
            try:
                eos = parse_date(cell["end_of_support_date"])
            except ValueError as exc:
                problems.append(f"{where}: end_of_support_date: {exc}")

        vendor = _YES_NO.get(cell["vendor_supported_in_cloud"].lower())
        if vendor is None:
            problems.append(
                f"{where}: vendor_supported_in_cloud '{cell['vendor_supported_in_cloud']}' "
                f"is not one of {', '.join(VENDOR_VALUES)}"
            )
            vendor = "unknown"
        sensitivity = cell["data_sensitivity"].lower()
        if sensitivity and sensitivity not in SENSITIVITY_VALUES:
            problems.append(
                f"{where}: data_sensitivity '{cell['data_sensitivity']}' "
                f"is not one of {', '.join(SENSITIVITY_VALUES)}"
            )
            sensitivity = ""
        change = cell["change_frequency"].lower()
        if change and change not in CHANGE_VALUES:
            problems.append(
                f"{where}: change_frequency '{cell['change_frequency']}' "
                f"is not one of {', '.join(CHANGE_VALUES)}"
            )
            change = ""

        deps = []
        for d in cell["dependencies"].split(";"):
            d = d.strip()
            if d and d not in deps:
                deps.append(d)
        raw_deps[app_id] = deps

        apps.append(
            App(
                app_id=app_id,
                name=cell["name"],
                owner=cell["owner"],
                business_criticality=crit if crit is not None else 0,
                users=users,
                technology=cell["technology"],
                os_or_platform=cell["os_or_platform"],
                end_of_support_date=eos,
                vendor_supported_in_cloud=vendor,
                data_sensitivity=sensitivity,
                dependencies=tuple(deps),
                current_annual_cost=cost,
                change_frequency=change,
                licence_model=cell["licence_model"],
                notes=cell["notes"],
                azure_annual_cost_estimate=estimate,
                line=line,
            )
        )

    if not apps and not problems:
        problems.append(f"{path.name}: the inventory has no applications")

    ids = {a.app_id for a in apps}
    for a in apps:
        where = f"line {a.line} ({a.app_id})"
        kept = []
        for d in a.dependencies:
            if d == a.app_id:
                warnings.append(f"{where}: lists itself as a dependency; ignored")
            elif d not in ids:
                msg = f"{where}: dependency '{d}' is not in the inventory"
                if allow_unknown_dependencies:
                    warnings.append(msg + "; ignored")
                else:
                    problems.append(msg + " (use --allow-unknown-dependencies to continue without it)")
            else:
                kept.append(d)
        a.dependencies = tuple(sorted(kept))

    if problems:
        raise ValidationError(problems)
    apps.sort(key=lambda a: a.app_id)
    return apps, warnings
