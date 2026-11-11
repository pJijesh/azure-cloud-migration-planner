"""Load and validate the rules file. The default rules ship with the package as JSON."""

from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from importlib import resources
from pathlib import Path

from .errors import ValidationError
from .inventory import parse_date
from .model import DISPOSITIONS, INVENTORY_FIELDS

DERIVED_FIELDS = (
    "tech_class",
    "eos_status",
    "dependents_count",
    "dependencies_count",
    "text",
    "platform_text",
)
FIELDS = tuple(INVENTORY_FIELDS) + DERIVED_FIELDS
OPS = ("eq", "ne", "in", "not_in", "lt", "lte", "gt", "gte", "contains_any", "is_blank", "not_blank")
SECTIONS = ("settings", "baseline", "keywords", "tech_classes", "default_tech_class", "rules", "waves")
WAVE_KEYS = (
    "max_wave_size",
    "critical_min_criticality",
    "critical_min_wave",
    "shared_service_min_dependents",
    "shared_service_classes",
    "min_wave_by_disposition",
    "allow_dependency_in_same_wave",
)


def default_rules_text() -> str:
    return resources.files("migration_planner").joinpath("default_rules.json").read_text(encoding="utf-8")


def load_rules(path=None) -> dict:
    """Return a validated rules dictionary. Sections present in a user file replace the defaults."""
    rules = json.loads(default_rules_text())
    if path is not None:
        path = Path(path)
        if not path.is_file():
            raise ValidationError(f"rules file not found: {path}")
        try:
            user = json.loads(path.read_text(encoding="utf-8-sig"))
        except json.JSONDecodeError as exc:
            raise ValidationError(f"{path.name}: not valid JSON ({exc})") from None
        if not isinstance(user, dict):
            raise ValidationError(f"{path.name}: the top level must be a JSON object")
        unknown = [k for k in user if k not in SECTIONS and k not in ("version", "description")]
        if unknown:
            raise ValidationError(f"{path.name}: unknown section(s): {', '.join(unknown)}")
        for key in SECTIONS:
            if key in user:
                rules[key] = user[key]
    validate_rules(rules, path.name if path else "default rules")
    return rules


def rules_hash(rules: dict) -> str:
    canonical = json.dumps(rules, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _validate_cond(cond, where, keywords, problems):
    if not isinstance(cond, dict):
        problems.append(f"{where}: a condition must be an object")
        return
    if "all" in cond or "any" in cond:
        key = "all" if "all" in cond else "any"
        items = cond[key]
        if not isinstance(items, list) or not items:
            problems.append(f"{where}: '{key}' needs a non-empty list of conditions")
            return
        for c in items:
            _validate_cond(c, where, keywords, problems)
        return
    field, op = cond.get("field"), cond.get("op")
    if field not in FIELDS:
        problems.append(f"{where}: unknown field '{field}'")
    if op not in OPS:
        problems.append(f"{where}: unknown operator '{op}' (use one of {', '.join(OPS)})")
        return
    if op in ("is_blank", "not_blank"):
        return
    if "value" not in cond:
        problems.append(f"{where}: operator '{op}' needs a value")
        return
    value = cond["value"]
    if op == "contains_any":
        if isinstance(value, str):
            if not value.startswith("@") or value[1:] not in keywords:
                problems.append(f"{where}: keyword list '{value}' is not defined under keywords")
        elif not (isinstance(value, list) and all(isinstance(v, str) for v in value)):
            problems.append(f"{where}: contains_any needs a list of words or an @keyword list name")
    elif op in ("in", "not_in"):
        if not isinstance(value, list):
            problems.append(f"{where}: operator '{op}' needs a list")
    elif op in ("lt", "lte", "gt", "gte"):
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            problems.append(f"{where}: operator '{op}' needs a number")


def validate_rules(rules: dict, name: str = "rules") -> None:
    problems: list[str] = []
    settings = rules.get("settings", {})
    for key in ("eos_soon_months", "confidence_high_margin", "confidence_medium_margin"):
        v = settings.get(key)
        if isinstance(v, bool) or not isinstance(v, int) or v < 0:
            problems.append(f"settings.{key} must be a whole number of zero or more")
    order = settings.get("tie_break_order")
    if not isinstance(order, list) or sorted(order) != sorted(DISPOSITIONS):
        problems.append("settings.tie_break_order must list each of the six dispositions exactly once")
    default_as_of = settings.get("default_as_of")
    if default_as_of is not None:
        try:
            parse_date(str(default_as_of))
        except ValueError as exc:
            problems.append(f"settings.default_as_of: {exc}")

    baseline = rules.get("baseline", {})
    if sorted(baseline) != sorted(DISPOSITIONS) or not all(
        isinstance(v, (int, float)) and not isinstance(v, bool) for v in baseline.values()
    ):
        problems.append("baseline must give a number for each of the six dispositions")

    keywords = rules.get("keywords", {})
    for key, words in keywords.items():
        if not (isinstance(words, list) and all(isinstance(w, str) and w for w in words)):
            problems.append(f"keywords.{key} must be a list of words")
    for i, entry in enumerate(rules.get("tech_classes", [])):
        if not (isinstance(entry, dict) and entry.get("class") and isinstance(entry.get("keywords"), list)):
            problems.append(f"tech_classes[{i}] needs 'class' and a 'keywords' list")

    seen = set()
    for i, rule in enumerate(rules.get("rules", [])):
        rid = rule.get("id") if isinstance(rule, dict) else None
        where = f"rule {rid or '#' + str(i + 1)}"
        if not isinstance(rule, dict) or not rid:
            problems.append(f"{where}: every rule needs an 'id'")
            continue
        if rid in seen:
            problems.append(f"{where}: duplicate rule id")
        seen.add(rid)
        if not rule.get("reason"):
            problems.append(f"{where}: every rule needs a plain-English 'reason'")
        if "when" not in rule:
            problems.append(f"{where}: missing 'when'")
        else:
            _validate_cond(rule["when"], where, keywords, problems)
        points = rule.get("points", {})
        for d, p in points.items():
            if d not in DISPOSITIONS:
                problems.append(f"{where}: unknown disposition '{d}' in points")
            elif isinstance(p, bool) or not isinstance(p, (int, float)):
                problems.append(f"{where}: points for '{d}' must be a number")
        force = rule.get("force")
        if force is not None:
            if not isinstance(force, dict) or force.get("disposition") not in DISPOSITIONS:
                problems.append(f"{where}: 'force' needs a valid disposition")
        ign = rule.get("ignore_for_dispositions", [])
        if not isinstance(ign, list) or any(d not in DISPOSITIONS for d in ign):
            problems.append(f"{where}: 'ignore_for_dispositions' must list dispositions")
        if not points and force is None:
            problems.append(f"{where}: needs 'points' or 'force'")

    waves = rules.get("waves", {})
    missing = [k for k in WAVE_KEYS if k not in waves]
    if missing:
        problems.append(f"waves: missing setting(s): {', '.join(missing)}")
    else:
        for key in ("max_wave_size", "critical_min_criticality", "critical_min_wave", "shared_service_min_dependents"):
            v = waves[key]
            if isinstance(v, bool) or not isinstance(v, int) or v < 1:
                problems.append(f"waves.{key} must be a whole number of 1 or more")
        if isinstance(waves["critical_min_criticality"], int) and waves["critical_min_criticality"] > 5:
            problems.append("waves.critical_min_criticality must be between 1 and 5")
        for d, w in waves["min_wave_by_disposition"].items():
            if d not in DISPOSITIONS or isinstance(w, bool) or not isinstance(w, int) or w < 1:
                problems.append(f"waves.min_wave_by_disposition: '{d}': {w} is not valid")
    if problems:
        raise ValidationError([f"{name}: {p}" for p in problems])


def copy_rules(rules: dict) -> dict:
    return deepcopy(rules)
