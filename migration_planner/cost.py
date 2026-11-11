"""Three year (or N year) run cost comparison: stay on premises versus follow the plan.

The model works month by month. Nothing in it is a price: every number comes from the user's
assumptions file or the inventory. Rules of the model, in plain terms:

* Landing zone work comes first (landing_zone_months). Wave k then occupies months_per_wave months.
  Migration effort for a wave is spread over its months and the cutover is at the end of the last one.
* After cutover the application's Azure cost starts. Its on premises cost carries on in full for
  parallel_run_months, then falls by cost_removed_share (the rest is stranded cost that does not go away).
* Retired applications are decommissioned in the same window as wave 1 and then stop costing money
  (apart from an optional archive cost).
* Retained and already-SaaS applications cost the same in both scenarios.
* Platform costs (landing zone, connectivity, programme management) apply only to the migration scenario.
* Inflation steps up once a year. The hardware refresh is avoided in proportion to the share of
  on premises cost already removed in that month.
"""

from __future__ import annotations

from dataclasses import dataclass

from .model import MIGRATING

ONE_OFF_CATEGORIES = ("migration_one_off", "platform_one_off", "other_one_off", "hardware_refresh")
CATEGORIES = (
    "on_prem_run",
    "azure_run",
    "platform_run",
    "other_recurring",
    "migration_one_off",
    "platform_one_off",
    "other_one_off",
    "hardware_refresh",
)

NOT_MODELLED = [
    "Data egress and data transfer charges, including moving data into Azure and traffic between Azure and the remaining on premises estate.",
    "Licensing changes: whether existing licences can be reused (for example through Azure Hybrid Benefit), vendor uplifts for cloud use, true-ups, and the cost of any licences that become unnecessary.",
    "Skills, training, hiring and any change in the size or cost of the IT team. People cost is only included where it is inside the supplied unit costs.",
    "Network: new or upgraded circuits, internet breakout and bandwidth needed for hybrid running, beyond the single connectivity figure supplied.",
    "Commitment discounts (reservations, savings plans), support plans and enterprise agreement terms, unless already reflected in the run cost factors you supplied.",
    "Right-sizing, growth, seasonality and performance. Azure run cost follows the factors supplied, not a measured sizing.",
    "Backup, disaster recovery and security tooling differences between today and Azure, unless included in the factors or in 'other_costs'.",
    "Exit costs on existing contracts, early termination fees, data centre or lease exit, and one-off write-offs of assets.",
    "Business disruption, downtime, lost productivity and the cost of delay or failure.",
    "Tax, VAT, foreign exchange and the accounting treatment of capital and operating spend.",
]


@dataclass
class Adjust:
    """Multipliers used by the sensitivity analysis. All 1.0 means the assumptions as supplied."""

    onprem_cost: float = 1.0
    azure_run: float = 1.0
    effort: float = 1.0
    removed_share: float = 1.0
    months_per_wave: float = 1.0
    platform_run: float = 1.0


def _r(x: float) -> float:
    return round(x + 0.0, 2)


def _azure_annual(a, A, adj):
    """Annual Azure run cost for one migrating application, and the method used."""
    app = a.app
    if app.azure_annual_cost_estimate is not None:
        return app.azure_annual_cost_estimate * adj.azure_run, "supplied estimate"
    per_user = A["unit_costs"].get("saas_per_user_per_year")
    if a.disposition == "repurchase" and per_user is not None and app.users is not None:
        fixed = A["unit_costs"].get("saas_fixed_per_app_per_year") or 0
        return (app.users * per_user + fixed) * adj.azure_run, "per user"
    # The run cost factor is applied to the recorded cost, not to a what-if scaled cost, so that the
    # "current on premises cost" sensitivity moves only the on premises side.
    p = app.current_annual_cost or 0
    return p * A["azure"]["run_cost_factor"][a.disposition] * adj.azure_run, "factor"


def _effort_cost(a, A, adj):
    e = A["migration_effort"]
    days = e["days_per_app"].get(a.disposition, 0) or 0
    mult = e["criticality_multiplier"][str(a.app.business_criticality)]
    return days * mult * A["unit_costs"]["engineer_day_rate"] * (1 + e["contingency"]) * adj.effort


def run_model(assessed, plan, A, adj: Adjust | None = None) -> dict:
    adj = adj or Adjust()
    H = A["horizon_years"] * 12
    lz = A["timing"]["landing_zone_months"]
    mpw_eff = A["timing"]["months_per_wave"] * adj.months_per_wave
    par = A["timing"]["parallel_run_months"]
    removed = min(1.0, A["on_prem"]["cost_removed_share"] * adj.removed_share)
    i_on, i_az = A["on_prem"]["annual_cost_inflation"], A["azure"]["annual_cost_inflation"]
    rate = A.get("discount_rate")

    wave_of = {m: p["wave"] for m, p in plan["placement"].items()}
    migrating = [a for a in assessed if a.app.app_id in wave_of]
    retiring = [a for a in assessed if a.disposition == "retire" and a.in_scope]
    others = [a for a in assessed if a not in migrating and a not in retiring]

    max_wave = max(wave_of.values(), default=1)
    ends = [lz]  # ends[k] is the last month of wave k; ends[0] is the end of the landing zone work
    for k in range(1, max_wave + 1):
        ends.append(max(ends[-1] + 1, lz + int(k * mpw_eff + 0.5)))

    def window(k):
        return ends[k - 1] + 1, ends[k]

    retire_start, retire_end = window(1)
    last_cutover = max([window(wave_of[a.app.app_id])[1] for a in migrating], default=0)
    programme_end = max(last_cutover, retire_end if retiring else 0, lz)
    programme_end = max(programme_end, 1)

    stay = {c: [0.0] * H for c in CATEGORIES}
    mig = {c: [0.0] * H for c in CATEGORIES}
    per_app = []
    total_p = sum((a.app.current_annual_cost or 0) * adj.onprem_cost for a in assessed)

    def on_f(m):
        return (1 + i_on) ** ((m - 1) // 12)

    def az_f(m):
        return (1 + i_az) ** ((m - 1) // 12)

    removal_month = {}  # app_id -> first month in which its on premises cost has fallen
    for a in assessed:
        P = (a.app.current_annual_cost or 0) * adj.onprem_cost
        rec = {
            "app_id": a.app.app_id,
            "name": a.app.name,
            "disposition": a.disposition,
            "wave": wave_of.get(a.app.app_id, ""),
            "cutover_month": "",
            "on_prem_annual_cost": P,
            "azure_annual_cost": 0.0,
            "azure_cost_method": "",
            "migration_effort_cost": 0.0,
            "stay_total": 0.0,
            "migrate_run_total": 0.0,
        }
        app_stay = app_mig_run = 0.0
        if a in migrating:
            k = wave_of[a.app.app_id]
            start, end = window(k)
            A_year, method = _azure_annual(a, A, adj)
            E = _effort_cost(a, A, adj)
            rec.update(cutover_month=end, azure_annual_cost=A_year, azure_cost_method=method, migration_effort_cost=E)
            removal_month[a.app.app_id] = end + par + 1
            for m in range(1, H + 1):
                base = P / 12 * on_f(m)
                stay["on_prem_run"][m - 1] += base
                app_stay += base
                factor = 1.0 if m <= end + par else 1.0 - removed
                mig["on_prem_run"][m - 1] += base * factor
                app_mig_run += base * factor
                if m > end:
                    az = A_year / 12 * az_f(m)
                    mig["azure_run"][m - 1] += az
                    app_mig_run += az
                if start <= m <= end:
                    mig["migration_one_off"][m - 1] += E / (end - start + 1)
        elif a in retiring:
            E = _effort_cost(a, A, adj)
            archive = A["azure"]["retire_archive_annual_per_app"] * adj.azure_run
            rec.update(cutover_month=retire_end, azure_annual_cost=archive, azure_cost_method="archive", migration_effort_cost=E)
            removal_month[a.app.app_id] = retire_end + 1
            for m in range(1, H + 1):
                base = P / 12 * on_f(m)
                stay["on_prem_run"][m - 1] += base
                app_stay += base
                factor = 1.0 if m <= retire_end else 1.0 - removed
                mig["on_prem_run"][m - 1] += base * factor
                app_mig_run += base * factor
                if m > retire_end:
                    az = archive / 12 * az_f(m)
                    mig["azure_run"][m - 1] += az
                    app_mig_run += az
                if retire_start <= m <= retire_end:
                    mig["migration_one_off"][m - 1] += E / (retire_end - retire_start + 1)
        else:
            for m in range(1, H + 1):
                base = P / 12 * on_f(m)
                stay["on_prem_run"][m - 1] += base
                mig["on_prem_run"][m - 1] += base
                app_stay += base
                app_mig_run += base
        rec["stay_total"] = app_stay
        rec["migrate_run_total"] = app_mig_run
        per_app.append(rec)

    # Platform and programme costs exist only if something actually moves.
    plat = A["platform"]
    if migrating or retiring:
        if migrating:
            lz_span = max(lz, 1)
            for m in range(1, min(lz_span, H) + 1):
                mig["platform_one_off"][m - 1] += plat["landing_zone_one_off"] / lz_span
            run_annual = (plat["landing_zone_annual"] + plat["connectivity_annual"]) * adj.platform_run
            for m in range(lz + 1, H + 1):
                mig["platform_run"][m - 1] += run_annual / 12 * az_f(m)
        for m in range(1, min(programme_end, H) + 1):
            mig["platform_one_off"][m - 1] += plat["programme_management_one_off"] / programme_end

    # Hardware refresh avoided in proportion to on premises cost already removed.
    hw, hm = A["on_prem"]["hardware_refresh_amount"], A["on_prem"].get("hardware_refresh_month")
    if hw and hm and hm <= H:
        stay["hardware_refresh"][hm - 1] += hw
        gone = sum(
            (a.app.current_annual_cost or 0) * adj.onprem_cost
            for a in assessed
            if a.app.app_id in removal_month and hm >= removal_month[a.app.app_id]
        )
        fraction = removed * gone / total_p if total_p else 0.0
        mig["hardware_refresh"][hm - 1] += hw * (1 - fraction)

    for item in A.get("other_costs", []):
        for scen, store in (("stay", stay), ("migrate", mig)):
            if item["scenario"] not in (scen, "both"):
                continue
            start = int(item["month"])
            if item["kind"] == "one_off":
                if start <= H:
                    store["other_one_off"][start - 1] += item["amount"]
            else:
                for m in range(start, H + 1):
                    store["other_recurring"][m - 1] += item["amount"] / 12

    def summarise(cats):
        monthly = [sum(cats[c][m] for c in CATEGORIES) for m in range(H)]
        recurring = [monthly[m] - sum(cats[c][m] for c in ONE_OFF_CATEGORIES) for m in range(H)]
        out = {
            "monthly": monthly,
            "total": sum(monthly),
            "by_year": [sum(monthly[y * 12:(y + 1) * 12]) for y in range(H // 12)],
            "final_year_run_cost": sum(recurring[-12:]),
            "by_category": {c: sum(cats[c]) for c in CATEGORIES},
            "categories": cats,
        }
        if rate is not None:
            out["npv"] = sum(monthly[m] / (1 + rate) ** ((m + 1) / 12) for m in range(H))
        return out

    s_stay, s_mig = summarise(stay), summarise(mig)
    diff = []
    cum = 0.0
    for m in range(H):
        cum += s_mig["monthly"][m] - s_stay["monthly"][m]
        diff.append(cum)
    be = _break_even(diff)
    be_disc = None
    if rate is not None:
        d2, cum = [], 0.0
        for m in range(H):
            cum += (s_mig["monthly"][m] - s_stay["monthly"][m]) / (1 + rate) ** ((m + 1) / 12)
            d2.append(cum)
        be_disc = _break_even(d2)
    saving = s_stay["total"] - s_mig["total"]
    return {
        "months": H,
        "stay": s_stay,
        "migrate": s_mig,
        "saving": saving,
        "saving_pct": (saving / s_stay["total"] * 100) if s_stay["total"] else 0.0,
        "break_even_month": be,
        "break_even_month_discounted": be_disc,
        "cumulative_difference": diff,
        "per_app": per_app,
        "timing": {
            "landing_zone_months": lz,
            "months_per_wave": A["timing"]["months_per_wave"] * adj.months_per_wave,
            "parallel_run_months": par,
            "last_cutover_month": last_cutover,
            "programme_end_month": programme_end,
            "retire_window": [retire_start, retire_end] if retiring else None,
            "wave_windows": {k: list(window(k)) for k in sorted(set(wave_of.values()))},
        },
        "counts": {
            "migrating": len(migrating),
            "retiring": len(retiring),
            "unchanged": len(others),
        },
    }


def _break_even(cum_diff):
    """First month after which the migration scenario stays at or below the stay scenario.

    cum_diff[m] is cumulative (migrate minus stay). Returns None if it is still above at the end.
    """
    last_above = -1
    for i, v in enumerate(cum_diff):
        if v > 1e-9:
            last_above = i
    if last_above == len(cum_diff) - 1:
        return None
    return last_above + 2


SENSITIVITY = (
    ("Current on premises run cost", "onprem_cost", 0.8, 1.2),
    ("Azure run cost", "azure_run", 1.2, 0.8),
    ("Migration effort", "effort", 1.2, 0.8),
    ("Share of on premises cost actually removed", "removed_share", 0.8, 1.2),
    ("Months per wave (programme speed)", "months_per_wave", 1.2, 0.8),
    ("Landing zone and connectivity running cost", "platform_run", 1.2, 0.8),
)


def sensitivity(assessed, plan, A, base) -> list:
    """Plus and minus 20 percent on each key assumption, one at a time, then all adverse and all favourable."""
    rows = []

    def row(label, direction, adj):
        r = run_model(assessed, plan, A, adj)
        rows.append(
            {
                "case": label,
                "direction": direction,
                "stay_total": r["stay"]["total"],
                "migrate_total": r["migrate"]["total"],
                "saving": r["saving"],
                "saving_change_vs_base": r["saving"] - base["saving"],
                "break_even_month": r["break_even_month"],
            }
        )

    for label, attr, adverse, favourable in SENSITIVITY:
        row(label, f"adverse ({_pct(adverse)})", Adjust(**{attr: adverse}))
        row(label, f"favourable ({_pct(favourable)})", Adjust(**{attr: favourable}))
    adv = {attr: adverse for _, attr, adverse, _ in SENSITIVITY}
    fav = {attr: favourable for _, attr, _, favourable in SENSITIVITY}
    row("All of the above together", "all adverse", Adjust(**adv))
    row("All of the above together", "all favourable", Adjust(**fav))
    return rows


def _pct(mult: float) -> str:
    p = round((mult - 1) * 100)
    return f"{'+' if p > 0 else ''}{p}%"


def build_cost(assessed, plan, A) -> dict:
    base = run_model(assessed, plan, A)
    warnings = []
    if A.get("illustrative"):
        warnings.append("These assumptions are marked illustrative. The figures are not real prices and must not be used for a decision.")
    missing_cost = sorted(a.app.app_id for a in assessed if a.app.current_annual_cost is None)
    if missing_cost:
        warnings.append(f"{len(missing_cost)} application(s) have no current_annual_cost and are counted as zero: {', '.join(missing_cost)}.")
    unconfirmed = sorted(
        a.app.app_id for a in assessed if a.app.app_id in plan["placement"] and a.app.vendor_supported_in_cloud != "yes"
    )
    if unconfirmed:
        warnings.append(
            f"{len(unconfirmed)} application(s) are planned to move although vendor support in the cloud is not confirmed "
            f"({', '.join(unconfirmed)}). Their cost is modelled as if the move succeeds as planned."
        )
    retained = [a for a in assessed if a.disposition == "retain" and a.in_scope]
    if retained:
        warnings.append(
            f"{len(retained)} retained application(s) stay on premises and cost the same in both scenarios. "
            f"Any saving depends on the shared costs behind them (hosting, hardware, licences) actually shrinking."
        )
    per_user = A["unit_costs"].get("saas_per_user_per_year")
    repurchased = [a for a in assessed if a.disposition == "repurchase" and a.app.app_id in plan["placement"]]
    if repurchased and per_user is None:
        warnings.append("Repurchased applications use the run cost factor because no saas_per_user_per_year was supplied.")
    if not plan["placement"] and not base["counts"]["retiring"]:
        warnings.append("Nothing is planned to move or retire, so the two scenarios are identical.")
    if base["timing"]["programme_end_month"] > base["months"]:
        warnings.append(
            f"The programme runs to month {base['timing']['programme_end_month']}, beyond the {base['months']} month horizon. "
            f"Costs after the horizon are not counted, which flatters the migration scenario."
        )
    if base["break_even_month"] is None:
        warnings.append(f"The migration scenario does not break even within {A['horizon_years']} years on these assumptions.")
    methods = {}
    for r in base["per_app"]:
        if r["azure_cost_method"]:
            methods[r["azure_cost_method"]] = methods.get(r["azure_cost_method"], 0) + 1
    sens = sensitivity(assessed, plan, A, base)
    return {
        "currency": A["currency"],
        "horizon_years": A["horizon_years"],
        "illustrative": bool(A.get("illustrative")),
        "label": A.get("label", ""),
        "discount_rate": A.get("discount_rate"),
        "result": base,
        "azure_cost_methods": dict(sorted(methods.items())),
        "sensitivity": sens,
        "warnings": warnings,
        "not_modelled": list(NOT_MODELLED),
    }
