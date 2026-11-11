"""Rule-based disposition engine.

Every application starts with the baseline points. Each rule that matches adds or subtracts points
for some of the six dispositions, and records a plain-English reason. The disposition with the most
points wins. Nothing here is hidden: the scores, the rules that fired and the margin are all output.
"""

from __future__ import annotations

import calendar
import csv
import re
from datetime import date
from pathlib import Path

from .errors import ValidationError
from .model import DISPOSITIONS, Assessed

NONE_TEXT = "not recorded"


def add_months(d: date, months: int) -> date:
    index = d.month - 1 + months
    year, month = d.year + index // 12, index % 12 + 1
    return date(year, month, min(d.day, calendar.monthrange(year, month)[1]))


def has_keyword(text: str, keyword: str) -> bool:
    """Whole-word (or whole-phrase) match, case-insensitive. A plural ending is accepted."""
    pattern = r"(?<![a-z0-9])" + re.escape(keyword.lower()) + r"(?:s|es)?(?![a-z0-9])"
    return re.search(pattern, text.lower()) is not None


def tech_class_of(technology: str, rules: dict) -> str:
    for entry in rules["tech_classes"]:
        if any(has_keyword(technology, k) for k in entry["keywords"]):
            return entry["class"]
    return rules["default_tech_class"]


def eos_status_of(eos: date | None, as_of: date, soon_months: int) -> str:
    if eos is None:
        return "none"
    if eos <= as_of:
        return "past"
    if eos <= add_months(as_of, soon_months):
        return "soon"
    return "later"


def _facts(app, tech_class, eos_status, dependents, rules) -> dict:
    return {
        "app_id": app.app_id,
        "name": app.name,
        "owner": app.owner,
        "business_criticality": app.business_criticality,
        "users": app.users,
        "technology": app.technology,
        "os_or_platform": app.os_or_platform,
        "end_of_support_date": app.end_of_support_date.isoformat() if app.end_of_support_date else "",
        "vendor_supported_in_cloud": app.vendor_supported_in_cloud,
        "data_sensitivity": app.data_sensitivity,
        "dependencies": ";".join(app.dependencies),
        "current_annual_cost": app.current_annual_cost,
        "change_frequency": app.change_frequency,
        "licence_model": app.licence_model,
        "notes": app.notes,
        "tech_class": tech_class,
        "eos_status": eos_status,
        "dependents_count": dependents,
        "dependencies_count": len(app.dependencies),
        "text": f"{app.notes} {app.technology}".lower(),
        "platform_text": f"{app.os_or_platform} {app.technology}".lower(),
    }


def _norm(v):
    return v.lower() if isinstance(v, str) else v


def eval_cond(cond: dict, facts: dict, rules: dict) -> bool:
    if "all" in cond:
        return all(eval_cond(c, facts, rules) for c in cond["all"])
    if "any" in cond:
        return any(eval_cond(c, facts, rules) for c in cond["any"])
    actual, op = facts[cond["field"]], cond["op"]
    if op == "is_blank":
        return actual is None or actual == ""
    if op == "not_blank":
        return not (actual is None or actual == "")
    value = cond["value"]
    if op == "eq":
        return _norm(actual) == _norm(value)
    if op == "ne":
        return _norm(actual) != _norm(value)
    if op == "in":
        return _norm(actual) in [_norm(v) for v in value]
    if op == "not_in":
        return _norm(actual) not in [_norm(v) for v in value]
    if op in ("lt", "lte", "gt", "gte"):
        if actual is None or isinstance(actual, str):
            return False
        return {"lt": actual < value, "lte": actual <= value, "gt": actual > value, "gte": actual >= value}[op]
    if op == "contains_any":
        words = rules["keywords"][value[1:]] if isinstance(value, str) else value
        return any(has_keyword(str(actual or ""), w) for w in words)
    raise AssertionError(f"unhandled operator {op}")  # validate_rules prevents this


class _Safe(dict):
    def __missing__(self, key):
        return "{" + key + "}"


def _fmt_points(points: dict) -> str:
    parts = []
    for d in DISPOSITIONS:
        if d in points and points[d] != 0:
            p = points[d]
            p = int(p) if float(p).is_integer() else p
            parts.append(f"{d} {'+' if p > 0 else ''}{p}")
    return ", ".join(parts)


def _clean(n):
    return int(n) if float(n).is_integer() else n


def assess_app(app, dependents, rules, as_of, tie_order=None):
    settings = rules["settings"]
    tech_class = tech_class_of(app.technology, rules)
    eos_status = eos_status_of(app.end_of_support_date, as_of, settings["eos_soon_months"])
    facts = _facts(app, tech_class, eos_status, dependents, rules)
    text_facts = _Safe({k: (NONE_TEXT if v in (None, "") else v) for k, v in facts.items()})
    text_facts["eos_soon_months"] = settings["eos_soon_months"]

    scores = {d: rules["baseline"][d] for d in DISPOSITIONS}
    reasons, flags, actions = [], [], []
    fired = []
    forced = None
    for rule in rules["rules"]:
        if not eval_cond(rule["when"], facts, rules):
            continue
        fired.append(rule)
        points = rule.get("points", {})
        for d, p in points.items():
            scores[d] += p
        text = rule["reason"].format_map(text_facts)
        effect = _fmt_points(points)
        if "force" in rule and forced is None:
            forced = rule["force"]
            effect = f"decides: {rule['force']['disposition']}"
        reasons.append(f"{text} [{rule['id']}{': ' + effect if effect else ''}]")

    scores = {d: _clean(v) for d, v in scores.items()}
    order = settings["tie_break_order"]
    ranked = sorted(DISPOSITIONS, key=lambda d: (-scores[d], order.index(d)))
    tie = forced is None and scores[ranked[0]] == scores[ranked[1]]
    in_scope = True
    if forced:
        disposition = forced["disposition"]
        in_scope = forced.get("in_scope", True)
        runner_up, margin, confidence = "", None, "high"
    else:
        disposition = ranked[0]
        runner_up = ranked[1]
        margin = _clean(scores[ranked[0]] - scores[ranked[1]])
        if margin >= settings["confidence_high_margin"]:
            confidence = "high"
        elif margin >= settings["confidence_medium_margin"]:
            confidence = "medium"
        else:
            confidence = "low"
    if tie:
        flags.append("tie_broken_by_order")
        reasons.append(
            f"Two dispositions scored the same, so the tie was broken by the configured order. "
            f"Treat {disposition} and {runner_up} as equally open."
        )
    # Flags and next steps are shown only when they matter to the chosen disposition.
    for rule in fired:
        if disposition in rule.get("ignore_for_dispositions", []):
            continue
        if rule.get("flag") and rule["flag"] not in flags:
            flags.append(rule["flag"])
        if rule.get("action") and rule["action"] not in actions:
            actions.append(rule["action"])
    needs_review = confidence == "low" or tie
    for rule in fired:
        if rule.get("review") and (forced or rule.get("points", {}).get(disposition, 0) != 0):
            needs_review = True
    return Assessed(
        app=app,
        tech_class=tech_class,
        eos_status=eos_status,
        dependents_count=dependents,
        disposition=disposition,
        in_scope=in_scope,
        scores=scores,
        runner_up=runner_up,
        margin=margin,
        confidence=confidence,
        needs_review=needs_review,
        reasons=reasons,
        flags=flags,
        actions=actions,
    )


def assess_all(apps, rules, as_of):
    dependents = {a.app_id: 0 for a in apps}
    for a in apps:
        for d in a.dependencies:
            dependents[d] += 1
    return [assess_app(a, dependents[a.app_id], rules, as_of) for a in sorted(apps, key=lambda a: a.app_id)]


def load_overrides(path) -> dict:
    """Read a CSV of human decisions: app_id, disposition, reason."""
    path = Path(path)
    if not path.is_file():
        raise ValidationError(f"overrides file not found: {path}")
    problems, out = [], {}
    reader = csv.DictReader(path.read_text(encoding="utf-8-sig").splitlines(keepends=True))
    headers = [h.strip().lower() for h in (reader.fieldnames or [])]
    reader.fieldnames = headers
    for col in ("app_id", "disposition", "reason"):
        if col not in headers:
            raise ValidationError(f"{path.name}: missing column '{col}' (needs app_id, disposition, reason)")
    for row in reader:
        line = reader.line_num
        app_id = (row.get("app_id") or "").strip()
        disp = (row.get("disposition") or "").strip().lower()
        reason = (row.get("reason") or "").strip()
        if not (app_id or disp or reason):
            continue
        if disp not in DISPOSITIONS:
            problems.append(f"{path.name} line {line}: disposition '{disp}' is not one of {', '.join(DISPOSITIONS)}")
        if not reason:
            problems.append(f"{path.name} line {line}: a reason is required for every override")
        if app_id in out:
            problems.append(f"{path.name} line {line}: '{app_id}' is overridden more than once")
        out[app_id] = (disp, reason)
    if problems:
        raise ValidationError(problems)
    return out


def apply_overrides(assessed, overrides: dict, source: str = "overrides"):
    ids = {a.app.app_id for a in assessed}
    unknown = sorted(set(overrides) - ids)
    if unknown:
        raise ValidationError([f"{source}: app_id '{u}' is not in the inventory" for u in unknown])
    for a in assessed:
        if a.app.app_id not in overrides:
            continue
        disp, reason = overrides[a.app.app_id]
        original = a.disposition
        a.reasons.insert(0, f"Human decision: {disp}. Rules proposed {original}. Reason given: {reason} [override]")
        a.disposition = disp
        a.overridden = True
        if disp != "retain":
            a.in_scope = True
        a.needs_review = False
        if "overridden" not in a.flags:
            a.flags.append("overridden")
    return assessed
