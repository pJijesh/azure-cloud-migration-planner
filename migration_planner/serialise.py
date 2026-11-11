"""Turn results into deterministic JSON and CSV, and read an assessment back from JSON."""

from __future__ import annotations

import csv
import io
import json
from datetime import date

from .errors import ValidationError
from .model import DISPOSITIONS, App, Assessed

CSV_APP_COLUMNS = (
    "app_id", "name", "owner", "business_criticality", "users", "technology", "os_or_platform",
    "end_of_support_date", "vendor_supported_in_cloud", "data_sensitivity", "dependencies",
    "current_annual_cost", "change_frequency", "licence_model", "notes",
)


def dumps(obj) -> str:
    return json.dumps(obj, indent=2, ensure_ascii=False) + "\n"


def csv_text(header, rows) -> str:
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(header)
    for r in rows:
        w.writerow(r)
    return buf.getvalue()


def app_to_dict(app: App) -> dict:
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
        "dependencies": list(app.dependencies),
        "current_annual_cost": app.current_annual_cost,
        "change_frequency": app.change_frequency,
        "licence_model": app.licence_model,
        "notes": app.notes,
        "azure_annual_cost_estimate": app.azure_annual_cost_estimate,
    }


def assessed_to_dict(a: Assessed) -> dict:
    d = app_to_dict(a.app)
    d.update(
        {
            "tech_class": a.tech_class,
            "eos_status": a.eos_status,
            "dependents_count": a.dependents_count,
            "disposition": a.disposition,
            "in_scope": a.in_scope,
            "confidence": a.confidence,
            "needs_review": a.needs_review,
            "overridden": a.overridden,
            "scores": a.scores,
            "runner_up": a.runner_up,
            "margin": a.margin,
            "flags": a.flags,
            "reasons": a.reasons,
            "actions": a.actions,
        }
    )
    return d


def assessment_csv(assessed) -> str:
    header = list(CSV_APP_COLUMNS) + [
        "tech_class", "eos_status", "dependents_count", "disposition", "in_scope", "confidence",
        "needs_review", "overridden",
    ] + [f"score_{d}" for d in DISPOSITIONS] + ["runner_up", "margin", "flags", "reasons", "actions"]
    rows = []
    for a in assessed:
        d = app_to_dict(a.app)
        row = [";".join(d[c]) if c == "dependencies" else _blank(d[c]) for c in CSV_APP_COLUMNS]
        row += [a.tech_class, a.eos_status, a.dependents_count, a.disposition, "yes" if a.in_scope else "no",
                a.confidence, "yes" if a.needs_review else "no", "yes" if a.overridden else "no"]
        row += [a.scores[x] for x in DISPOSITIONS]
        row += [a.runner_up, _blank(a.margin), ";".join(a.flags), " | ".join(a.reasons), " | ".join(a.actions)]
        rows.append(row)
    return csv_text(header, rows)


def _blank(v):
    return "" if v is None else v


def assessed_from_dict(d: dict, source: str) -> Assessed:
    try:
        eos = date.fromisoformat(d["end_of_support_date"]) if d["end_of_support_date"] else None
        app = App(
            app_id=d["app_id"], name=d["name"], owner=d["owner"],
            business_criticality=int(d["business_criticality"]), users=d["users"],
            technology=d["technology"], os_or_platform=d["os_or_platform"], end_of_support_date=eos,
            vendor_supported_in_cloud=d["vendor_supported_in_cloud"], data_sensitivity=d["data_sensitivity"],
            dependencies=tuple(d["dependencies"]), current_annual_cost=d["current_annual_cost"],
            change_frequency=d["change_frequency"], licence_model=d["licence_model"], notes=d["notes"],
            azure_annual_cost_estimate=d.get("azure_annual_cost_estimate"),
        )
        if d["disposition"] not in DISPOSITIONS:
            raise ValidationError(f"{source}: {app.app_id}: disposition '{d['disposition']}' is not one of {', '.join(DISPOSITIONS)}")
        return Assessed(
            app=app, tech_class=d["tech_class"], eos_status=d["eos_status"], dependents_count=d["dependents_count"],
            disposition=d["disposition"], in_scope=bool(d["in_scope"]), scores=d["scores"], runner_up=d["runner_up"],
            margin=d["margin"], confidence=d["confidence"], needs_review=bool(d["needs_review"]),
            reasons=list(d["reasons"]), flags=list(d["flags"]), actions=list(d["actions"]),
            overridden=bool(d.get("overridden", False)),
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise ValidationError(f"{source}: an application record is incomplete or malformed ({exc!r})") from None
