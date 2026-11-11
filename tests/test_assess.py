import json
from datetime import date

import pytest

from conftest import AS_OF, row, write_csv
from migration_planner.assess import (
    add_months,
    apply_overrides,
    eos_status_of,
    has_keyword,
    load_overrides,
)
from migration_planner.errors import ValidationError
from migration_planner.rules import load_rules, validate_rules

CASES = [
    # (label, row overrides, disposition, in_scope)
    ("plain supported package", {}, "rehost", True),
    ("already SaaS", {"technology": "SaaS (CRM)"}, "retain", False),
    ("unused and low criticality", {"business_criticality": 1, "users": 2, "change_frequency": "none"}, "retire", True),
    ("notes say superseded", {"business_criticality": 2, "notes": "Superseded by the new system"}, "retire", True),
    ("vendor will not support cloud", {"vendor_supported_in_cloud": "no"}, "retain", True),
    ("support ended, vendor supports cloud", {"end_of_support_date": "2024-01-01"}, "replatform", True),
    ("custom code changed often", {"technology": "Custom application (.NET)", "change_frequency": "high"}, "replatform", True),
    ("custom code with architecture limits", {"technology": "Custom application", "change_frequency": "high", "notes": "A monolith that cannot scale"}, "refactor", True),
    ("database", {"technology": "Database (SQL Server)"}, "replatform", True),
    ("file server", {"technology": "File server"}, "replatform", True),
    ("platform that is not a standard VM", {"os_or_platform": "AIX 7.2"}, "retain", True),
    ("critical and vendor support unknown", {"business_criticality": 5, "vendor_supported_in_cloud": "unknown"}, "retain", True),
    ("tied to shop floor equipment", {"notes": "Controls the PLC on line 2"}, "retain", True),
    ("licence tied to a hardware dongle", {"licence_model": "perpetual, hardware dongle"}, "retain", True),
    ("vendor has a SaaS version", {"notes": "Vendor offers a SaaS version", "end_of_support_date": "2028-06-30"}, "repurchase", True),
]


@pytest.mark.parametrize("label,overrides,expected,in_scope", CASES, ids=[c[0] for c in CASES])
def test_known_dispositions(make_assessed, label, overrides, expected, in_scope):
    a = make_assessed([row("A1", **overrides)])[0]
    assert a.disposition == expected, (a.scores, a.reasons)
    assert a.in_scope is in_scope


def test_exact_scores_for_a_plain_supported_package(make_assessed):
    a = make_assessed([row("A1")])[0]
    # baseline rehost 2, plus R07 (vendor supports cloud) +1 rehost +1 replatform, plus R14 refactor -4.
    assert a.scores == {"rehost": 3, "replatform": 1, "refactor": -4, "repurchase": 0, "retire": 0, "retain": 0}
    assert (a.runner_up, a.margin, a.confidence) == ("replatform", 2, "medium")
    assert [r.split("[")[-1][:3] for r in a.reasons] == ["R07", "R14"]


def test_ties_are_broken_by_the_configured_order_and_flagged(make_assessed):
    a = make_assessed([row("A1", vendor_supported_in_cloud="no")])[0]
    assert a.scores["retain"] == a.scores["repurchase"] == 3
    assert a.disposition == "retain"
    assert "tie_broken_by_order" in a.flags and a.needs_review and a.confidence == "low"
    assert any("same" in r for r in a.reasons)


def test_unknown_vendor_support_needs_review_and_gives_an_action(make_assessed):
    a = make_assessed([row("A1", vendor_supported_in_cloud="unknown", business_criticality=5)])[0]
    assert a.needs_review and "vendor_support_unknown" in a.flags
    assert any("in writing" in x for x in a.actions)


def test_actions_are_not_shown_for_retire(make_assessed):
    a = make_assessed([row("A1", business_criticality=1, users=0, vendor_supported_in_cloud="no", change_frequency="none")])[0]
    assert a.disposition == "retire"
    assert "vendor_no_cloud_support" not in a.flags
    assert not any("vendor position" in x for x in a.actions)


def test_dependents_are_counted(make_assessed):
    rows = [row("A1"), row("A2", dependencies="A1"), row("A3", dependencies="A1"), row("A4", dependencies="A1"),
            row("A5", dependencies="A1"), row("A6", dependencies="A1")]
    a = {x.app.app_id: x for x in make_assessed(rows)}
    assert a["A1"].dependents_count == 5
    assert any("[R23" in r for r in a["A1"].reasons)


def test_end_of_support_boundaries():
    assert eos_status_of(None, AS_OF, 12) == "none"
    assert eos_status_of(AS_OF, AS_OF, 12) == "past"
    assert eos_status_of(date(2027, 11, 11), AS_OF, 12) == "soon"
    assert eos_status_of(date(2027, 11, 12), AS_OF, 12) == "later"


def test_add_months_clamps_to_month_end():
    assert add_months(date(2026, 1, 31), 1) == date(2026, 2, 28)
    assert add_months(date(2026, 11, 11), 14) == date(2028, 1, 11)


def test_keyword_matching_is_whole_word_and_allows_plurals():
    assert has_keyword("Runs the PLC gateway", "plc")
    assert has_keyword("drives label printers", "label printer")
    assert not has_keyword("a plcx thing", "plc")
    assert not has_keyword("finance", "nas")


def test_assessment_is_deterministic(make_assessed):
    rows = [row("A2", dependencies="A1"), row("A1")]
    one = [(a.app.app_id, a.scores, a.reasons) for a in make_assessed(rows)]
    two = [(a.app.app_id, a.scores, a.reasons) for a in make_assessed(list(reversed(rows)))]
    assert one == two


def test_overrides_replace_the_disposition_and_keep_the_audit_trail(make_assessed, tmp_path):
    assessed = make_assessed([row("A1"), row("A2")])
    ov = tmp_path / "ov.csv"
    ov.write_text("app_id,disposition,reason\nA1,retain,Owner wants it left alone until the audit\n", encoding="utf-8")
    apply_overrides(assessed, load_overrides(ov))
    a1 = assessed[0]
    assert a1.disposition == "retain" and a1.overridden and "overridden" in a1.flags
    assert a1.reasons[0].startswith("Human decision: retain. Rules proposed rehost.")
    assert assessed[1].disposition == "rehost"


def test_override_errors(make_assessed, tmp_path):
    ov = tmp_path / "ov.csv"
    ov.write_text("app_id,disposition,reason\nA1,teleport,\nA1,retain,ok\n", encoding="utf-8")
    with pytest.raises(ValidationError) as exc:
        load_overrides(ov)
    text = "\n".join(exc.value.problems)
    assert "teleport" in text and "reason is required" in text and "more than once" in text
    ov.write_text("app_id,disposition,reason\nZZZ,retain,because\n", encoding="utf-8")
    with pytest.raises(ValidationError, match="ZZZ"):
        apply_overrides(make_assessed([row("A1")]), load_overrides(ov))


def test_custom_rules_file_changes_the_outcome(make_assessed, tmp_path):
    rules = load_rules()
    rules["baseline"]["rehost"] = 0
    rules["baseline"]["retain"] = 10
    path = tmp_path / "rules.json"
    path.write_text(json.dumps(rules), encoding="utf-8")
    loaded = load_rules(path)
    from migration_planner.assess import assess_all
    from migration_planner.inventory import load_inventory

    inv = write_csv(tmp_path / "i.csv", [row("A1")])
    apps, _ = load_inventory(inv)
    assert assess_all(apps, loaded, AS_OF)[0].disposition == "retain"


@pytest.mark.parametrize(
    "mutate,message",
    [
        (lambda r: r["rules"][0]["when"].update(field="colour"), "unknown field 'colour'"),
        (lambda r: r["rules"][1].update(points={"teleport": 1}), "unknown disposition 'teleport'"),
        (lambda r: r["rules"][1]["when"].update(op="resembles"), "unknown operator 'resembles'"),
        (lambda r: r["rules"][1].pop("reason"), "plain-English 'reason'"),
        (lambda r: r["rules"][2].update(id="R01"), "duplicate rule id"),
        (lambda r: r["settings"].update(tie_break_order=["rehost"]), "tie_break_order"),
        (lambda r: r["waves"].pop("max_wave_size"), r"missing setting\(s\): max_wave_size"),
    ],
)
def test_bad_rules_are_rejected_with_a_readable_message(mutate, message):
    rules = load_rules()
    mutate(rules)
    with pytest.raises(ValidationError, match=message):
        validate_rules(rules, "test rules")


def test_rules_file_that_is_not_json(tmp_path):
    p = tmp_path / "r.json"
    p.write_text("{not json", encoding="utf-8")
    with pytest.raises(ValidationError, match="not valid JSON"):
        load_rules(p)


def test_every_default_rule_has_a_reason_and_a_unique_id():
    rules = load_rules()
    ids = [r["id"] for r in rules["rules"]]
    assert len(ids) == len(set(ids))
    assert all(r["reason"].strip() for r in rules["rules"])
