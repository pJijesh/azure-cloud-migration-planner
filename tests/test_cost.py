import copy
import json

import pytest

from conftest import row
from migration_planner.assumptions import load_assumptions, template_text, validate_assumptions
from migration_planner.cost import Adjust, build_cost, run_model, _break_even
from migration_planner.errors import ValidationError
from migration_planner.waves import build_waves


def assumptions(**over):
    a = {
        "label": "test", "illustrative": True, "currency": "GBP", "horizon_years": 3, "discount_rate": None,
        "timing": {"landing_zone_months": 1, "months_per_wave": 1, "parallel_run_months": 0},
        "on_prem": {"annual_cost_inflation": 0, "cost_removed_share": 1.0, "hardware_refresh_amount": 0, "hardware_refresh_month": None},
        "azure": {"annual_cost_inflation": 0, "run_cost_factor": {"rehost": 0.5, "replatform": 0.5, "refactor": 0.5, "repurchase": 0.5},
                  "retire_archive_annual_per_app": 0},
        "unit_costs": {"engineer_day_rate": 500, "saas_per_user_per_year": None, "saas_fixed_per_app_per_year": None},
        "migration_effort": {"days_per_app": {"rehost": 10, "replatform": 10, "refactor": 10, "repurchase": 10, "retire": 2},
                             "criticality_multiplier": {"1": 1, "2": 1, "3": 1, "4": 1, "5": 1}, "contingency": 0},
        "platform": {"landing_zone_one_off": 1200, "landing_zone_annual": 1200, "connectivity_annual": 0, "programme_management_one_off": 0},
        "other_costs": [],
    }
    for k, v in over.items():
        if isinstance(v, dict) and isinstance(a.get(k), dict):
            a[k].update(v)
        else:
            a[k] = v
    return a


@pytest.fixture
def two_apps(make_assessed, rules):
    """A moves (rehost, 12000 a year). B stays on premises (6000 a year)."""
    assessed = make_assessed([
        row("A", current_annual_cost=12000),
        row("B", current_annual_cost=6000, os_or_platform="AIX 7.2"),
    ])
    assert [a.disposition for a in assessed] == ["rehost", "retain"]
    return assessed, build_waves(assessed, rules)


def test_one_year_by_hand(two_apps):
    # Months: 1 landing zone, 2 wave 1 (cutover at the end), Azure from month 3.
    # Stay: 12000 + 6000 = 18000.
    # Plan: A on premises months 1 to 2 = 2000; Azure 6000 a year for months 3 to 12 = 5000;
    #       effort 10 days x 500 = 5000; landing zone build 1200; platform running 1200 a year from month 2 = 1100; B 6000.
    assessed, plan = two_apps
    A = assumptions(horizon_years=1)
    r = run_model(assessed, plan, A)
    assert r["stay"]["total"] == pytest.approx(18000)
    cats = r["migrate"]["by_category"]
    assert cats["on_prem_run"] == pytest.approx(2000 + 6000)
    assert cats["azure_run"] == pytest.approx(5000)
    assert cats["migration_one_off"] == pytest.approx(5000)
    assert cats["platform_one_off"] == pytest.approx(1200)
    assert cats["platform_run"] == pytest.approx(1100)
    assert r["migrate"]["total"] == pytest.approx(20300)
    assert r["saving"] == pytest.approx(-2300)
    assert r["break_even_month"] is None


def test_three_years_and_break_even_by_hand(two_apps):
    # Stay 54000. Plan: A on premises 2000 + Azure 500 x 34 = 17000 + effort 5000 + landing zone 1200
    # + platform 100 x 35 = 3500 + B 18000 = 46700. Saving 7300.
    # Cumulative gap after month 2 is +6300 and falls by 400 a month, so it is last above zero in month 17: break even month 18.
    assessed, plan = two_apps
    r = run_model(assessed, plan, assumptions())
    assert r["stay"]["total"] == pytest.approx(54000)
    assert r["migrate"]["total"] == pytest.approx(46700)
    assert r["saving"] == pytest.approx(7300)
    assert r["cumulative_difference"][1] == pytest.approx(6300)
    assert r["cumulative_difference"][16] == pytest.approx(300)
    assert r["cumulative_difference"][17] == pytest.approx(-100)
    assert r["break_even_month"] == 18
    assert r["migrate"]["by_year"][0] == pytest.approx(2000 + 500 * 10 + 5000 + 1200 + 1100 + 6000)
    assert r["migrate"]["final_year_run_cost"] == pytest.approx(500 * 12 + 100 * 12 + 6000)
    assert r["stay"]["final_year_run_cost"] == pytest.approx(18000)


def test_parallel_run_and_stranded_cost_by_hand(two_apps):
    # 2 months of parallel running, and only 75 percent of A's on premises cost is removed afterwards.
    # A on premises: months 1 to 4 full (4000), months 5 to 36 at 25 percent: 250 x 32 = 8000.
    assessed, plan = two_apps
    A = assumptions(timing={"parallel_run_months": 2}, on_prem={"cost_removed_share": 0.75})
    r = run_model(assessed, plan, A)
    assert r["migrate"]["by_category"]["on_prem_run"] == pytest.approx(4000 + 8000 + 18000)


def test_inflation_steps_up_once_a_year(two_apps):
    assessed, plan = two_apps
    A = assumptions(on_prem={"annual_cost_inflation": 0.10}, azure={"annual_cost_inflation": 0.10})
    r = run_model(assessed, plan, A)
    # Stay: (18000) x (1 + 1.1 + 1.21)
    assert r["stay"]["total"] == pytest.approx(18000 * (1 + 1.1 + 1.21))
    # Azure: 500 a month from month 3, rising 10 percent each year: 10 months, 12 months, 12 months.
    assert r["migrate"]["by_category"]["azure_run"] == pytest.approx(500 * (10 + 12 * 1.1 + 12 * 1.21))


def test_hardware_refresh_is_avoided_in_proportion_to_cost_removed(two_apps):
    # A is a third of... A 12000 of 18000 total, 100 percent removed once moved, so two thirds of the refresh is avoided.
    assessed, plan = two_apps
    A = assumptions(on_prem={"hardware_refresh_amount": 9000, "hardware_refresh_month": 20})
    r = run_model(assessed, plan, A)
    assert r["stay"]["by_category"]["hardware_refresh"] == pytest.approx(9000)
    assert r["migrate"]["by_category"]["hardware_refresh"] == pytest.approx(3000)
    early = assumptions(on_prem={"hardware_refresh_amount": 9000, "hardware_refresh_month": 2})
    assert run_model(assessed, plan, early)["migrate"]["by_category"]["hardware_refresh"] == pytest.approx(9000)


def test_discounting_by_hand(two_apps):
    assessed, plan = two_apps
    r = run_model(assessed, plan, assumptions(horizon_years=1, discount_rate=0.12))
    expected = sum(m / 1.12 ** ((i + 1) / 12) for i, m in enumerate(r["stay"]["monthly"]))
    assert r["stay"]["npv"] == pytest.approx(expected)
    assert r["stay"]["npv"] < r["stay"]["total"]
    assert "npv" not in run_model(assessed, plan, assumptions())["stay"]


def test_other_costs_are_added_to_the_chosen_scenario(two_apps):
    assessed, plan = two_apps
    A = assumptions(other_costs=[
        {"label": "training", "kind": "one_off", "scenario": "migrate", "amount": 700, "month": 2},
        {"label": "support", "kind": "annual", "scenario": "stay", "amount": 1200, "month": 13},
    ])
    base = run_model(assessed, plan, assumptions())
    r = run_model(assessed, plan, A)
    assert r["migrate"]["total"] == pytest.approx(base["migrate"]["total"] + 700)
    assert r["stay"]["total"] == pytest.approx(base["stay"]["total"] + 100 * 24)


def test_repurchase_can_use_a_per_user_unit_cost(make_assessed, rules):
    assessed = make_assessed([row("A", notes="Vendor offers a SaaS version", end_of_support_date="2028-06-30", users=40, current_annual_cost=20000)])
    assert assessed[0].disposition == "repurchase"
    plan = build_waves(assessed, rules)
    A = assumptions(unit_costs={"saas_per_user_per_year": 300, "saas_fixed_per_app_per_year": 600})
    res = run_model(assessed, plan, A)
    assert res["per_app"][0]["azure_annual_cost"] == pytest.approx(40 * 300 + 600)
    assert res["per_app"][0]["azure_cost_method"] == "per user"


def test_a_supplied_azure_estimate_beats_the_factor(make_inventory, rules):
    from migration_planner.assess import assess_all
    from migration_planner.inventory import load_inventory
    from conftest import AS_OF, HEADER, write_csv

    r = dict(row("A", current_annual_cost=12000), azure_annual_cost_estimate="4000")
    p = write_csv(make_inventory([]).parent / "est.csv", [r], HEADER + ["azure_annual_cost_estimate"])
    apps, _ = load_inventory(p)
    assessed = assess_all(apps, rules, AS_OF)
    res = run_model(assessed, build_waves(assessed, rules), assumptions())
    assert res["per_app"][0]["azure_annual_cost"] == 4000
    assert res["per_app"][0]["azure_cost_method"] == "supplied estimate"


def test_retired_apps_stop_costing_after_the_first_window(make_assessed, rules):
    assessed = make_assessed([row("R", business_criticality=1, users=0, change_frequency="none", current_annual_cost=2400)])
    plan = build_waves(assessed, rules)
    A = assumptions(azure={"retire_archive_annual_per_app": 120})
    r = run_model(assessed, plan, A)
    # Window is month 2. On premises: months 1 to 2 = 400. Archive: 10 a month for months 3 to 36 = 340. Effort 2 days x 500.
    assert r["migrate"]["by_category"]["on_prem_run"] == pytest.approx(400)
    assert r["migrate"]["by_category"]["azure_run"] == pytest.approx(340)
    assert r["migrate"]["by_category"]["migration_one_off"] == pytest.approx(1000)
    assert r["migrate"]["by_category"]["platform_one_off"] == 0  # nothing moves, so no landing zone is built


def test_criticality_multiplier_and_contingency(make_assessed, rules):
    assessed = make_assessed([row("A", business_criticality=4, current_annual_cost=1000)])
    A = assumptions()
    A["migration_effort"]["criticality_multiplier"]["4"] = 1.5
    A["migration_effort"]["contingency"] = 0.2
    res = run_model(assessed, build_waves(assessed, rules), A)
    assert res["per_app"][0]["migration_effort_cost"] == pytest.approx(10 * 1.5 * 500 * 1.2)


def test_break_even_helper():
    assert _break_even([-1, -2]) == 1
    assert _break_even([5, 3, -1, -2]) == 3
    assert _break_even([5, 3, -1, 2, -4, -9]) == 5  # must stay below, so the first dip does not count
    assert _break_even([5, 3]) is None


def test_sensitivity_is_plus_and_minus_twenty_percent(two_apps):
    assessed, plan = two_apps
    A = assumptions()
    cost = build_cost(assessed, plan, A)
    base = cost["result"]
    rows = {(s["case"], s["direction"].split(" ")[0]): s for s in cost["sensitivity"]}
    adverse = rows[("Azure run cost", "adverse")]
    assert adverse["migrate_total"] == pytest.approx(base["migrate"]["total"] + 0.2 * 17000)
    assert rows[("Azure run cost", "favourable")]["migrate_total"] == pytest.approx(base["migrate"]["total"] - 0.2 * 17000)
    effort = rows[("Migration effort", "adverse")]
    assert effort["migrate_total"] == pytest.approx(base["migrate"]["total"] + 0.2 * 5000)
    on_prem = rows[("Current on premises run cost", "adverse")]
    # 20 percent lower recorded cost lowers the stay total by 20 percent and the plan's on premises spend with it.
    assert on_prem["stay_total"] == pytest.approx(54000 * 0.8)
    combined = {s["direction"]: s for s in cost["sensitivity"] if s["case"].startswith("All")}
    assert combined["all adverse"]["saving"] < base["saving"] < combined["all favourable"]["saving"]
    assert len(cost["sensitivity"]) == 14


def test_warnings_cover_the_important_limits(two_apps):
    assessed, plan = two_apps
    cost = build_cost(assessed, plan, assumptions())
    text = " ".join(cost["warnings"])
    assert "illustrative" in text and "retained application" in text
    assert any("egress" in n.lower() for n in cost["not_modelled"])
    assert any("licen" in n.lower() for n in cost["not_modelled"])
    assert any("skills" in n.lower() for n in cost["not_modelled"])
    assert any("network" in n.lower() for n in cost["not_modelled"])


def test_programme_longer_than_the_horizon_is_warned(make_assessed, rules):
    assessed = make_assessed([row("A", current_annual_cost=1000)])
    A = assumptions(horizon_years=1, timing={"landing_zone_months": 11, "months_per_wave": 3})
    cost = build_cost(assessed, build_waves(assessed, rules), A)
    assert any("beyond the 12 month horizon" in w for w in cost["warnings"])


def test_unconfirmed_vendor_support_and_missing_costs_are_warned(make_assessed, rules):
    assessed = make_assessed([row("A", vendor_supported_in_cloud="unknown", current_annual_cost="", business_criticality=2)])
    cost = build_cost(assessed, build_waves(assessed, rules), assumptions())
    text = " ".join(cost["warnings"])
    assert "no current_annual_cost" in text


def test_cost_is_deterministic(two_apps):
    assessed, plan = two_apps
    assert json.dumps(build_cost(assessed, plan, assumptions()), default=str) == json.dumps(build_cost(assessed, plan, assumptions()), default=str)


# ---- assumptions file handling -------------------------------------------------------------

def test_the_template_is_refused_until_inputs_are_supplied(tmp_path):
    p = tmp_path / "a.json"
    p.write_text(template_text(), encoding="utf-8")
    with pytest.raises(ValidationError) as exc:
        load_assumptions(p)
    text = "\n".join(exc.value.problems)
    assert "'timing.months_per_wave' is empty" in text
    assert "'unit_costs.engineer_day_rate' is empty" in text
    assert "'unit_costs.saas_per_user_per_year'" not in text  # optional
    assert "'discount_rate'" not in text  # optional


def test_a_complete_assumptions_file_validates():
    validate_assumptions(assumptions())


@pytest.mark.parametrize(
    "mutate,message",
    [
        (lambda a: a["on_prem"].update(cost_removed_share=1.5), "must be at most 1"),
        (lambda a: a["timing"].update(months_per_wave=0), "must be at least 1"),
        (lambda a: a["unit_costs"].update(engineer_day_rate="650"), "must be a number"),
        (lambda a: a["unit_costs"].update(engineer_day_rate=-1), "must be at least 0"),
        (lambda a: a["timing"].update(landing_zone_months=1.5), "whole number"),
        (lambda a: a.update(other_costs=[{"label": "x", "kind": "weekly", "scenario": "migrate", "amount": 1, "month": 1}]), "'kind'"),
        (lambda a: a["migration_effort"]["criticality_multiplier"].pop("5"), "criticality_multiplier.5' is empty"),
        (lambda a: a.update(horizon_years=0), "horizon_years"),
    ],
)
def test_bad_assumptions_are_rejected(mutate, message):
    a = copy.deepcopy(assumptions())
    mutate(a)
    with pytest.raises(ValidationError, match=message):
        validate_assumptions(a)


def test_assumptions_file_errors(tmp_path):
    with pytest.raises(ValidationError, match="not found"):
        load_assumptions(tmp_path / "none.json")
    p = tmp_path / "bad.json"
    p.write_text("{", encoding="utf-8")
    with pytest.raises(ValidationError, match="not valid JSON"):
        load_assumptions(p)
