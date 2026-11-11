"""Render the Markdown plan. Output is plain text and deterministic."""

from __future__ import annotations

from . import __version__
from .model import DISPOSITIONS

DISPOSITION_MEANING = {
    "rehost": "move as it is to Azure virtual machines",
    "replatform": "move with limited changes, for example to a managed database or file service",
    "refactor": "change the code to suit the cloud",
    "repurchase": "replace with a different product, usually SaaS",
    "retire": "switch off",
    "retain": "keep where it is, or already SaaS",
}


def money(x, cur):
    sign = "-" if x < -0.5 else ""
    return f"{sign}{cur} {abs(x):,.0f}"


def _cell(text) -> str:
    return str(text).replace("|", "/").replace("\n", " ")


def _table(header, rows) -> list:
    out = ["| " + " | ".join(header) + " |", "|" + "|".join("---" for _ in header) + "|"]
    for r in rows:
        out.append("| " + " | ".join(_cell(c) for c in r) + " |")
    return out


def render_plan(assessed, meta, assess_warnings, plan, cost, rules) -> str:
    L = []
    cur = cost["currency"] if cost else ""
    by_id = {a.app.app_id: a for a in assessed}
    L.append("# Azure migration plan")
    L.append("")
    if cost and cost["illustrative"]:
        L.append("> **Illustrative cost assumptions.** The cost figures in this plan come from placeholder numbers, not from quotes or "
                 "an Azure Migrate assessment. They show how the model works and must not be used for a decision.")
        L.append("")
    L.append("> **Planning aid only.** This plan comes from a rule-based tool working on the inventory it was given. It does not replace "
             "Azure Migrate discovery and assessment, a vendor quote, or the judgement of the application owners. Cost results are only as "
             "good as the inputs.")
    L.append("")
    L.append("## Inputs")
    L.append("")
    rows = [
        ["Inventory", f"{meta['inventory_file']} (sha256 {meta['inventory_sha256'][:12]})"],
        ["Rules", f"sha256 {meta['rules_sha256'][:12]}"],
        ["Assessed as at", meta["as_of"]],
        ["Tool version", __version__],
    ]
    if meta.get("overrides_file"):
        rows.append(["Human overrides", f"{meta['overrides_file']} (sha256 {meta['overrides_sha256'][:12]})"])
    if cost:
        rows.append(["Cost assumptions", cost["label"] or "supplied file"])
    L += _table(["Item", "Value"], rows)
    L.append("")

    L.append("## Summary")
    L.append("")
    counts = {d: 0 for d in DISPOSITIONS}
    costs = {d: 0.0 for d in DISPOSITIONS}
    for a in assessed:
        counts[a.disposition] += 1
        costs[a.disposition] += a.app.current_annual_cost or 0
    rows = [[d, DISPOSITION_MEANING[d], counts[d], f"{costs[d]:,.0f}"] for d in DISPOSITIONS]
    rows.append(["total", "", len(assessed), f"{sum(costs.values()):,.0f}"])
    L += _table(["Disposition", "Meaning", "Applications", "Current annual cost"], rows)
    L.append("")
    review = [a for a in assessed if a.needs_review]
    L.append(f"{len(assessed)} applications assessed. {len(review)} need a human decision before the plan is relied on "
             f"(listed below). {plan['wave_count']} migration wave(s) are proposed for "
             f"{sum(w['size'] for w in plan['waves'])} application(s), and {len(plan['cycles'])} circular dependency group(s) were found.")
    if cost:
        r = cost["result"]
        be = r["break_even_month"]
        L.append("")
        L.append(
            f"On the assumptions supplied, following the plan costs {money(abs(r['saving']), cur)} "
            f"({abs(r['saving_pct']):.1f} percent) {'less' if r['saving'] >= 0 else 'more'} than staying as is over {cost['horizon_years']} years "
            f"({money(r['migrate']['total'], cur)} against {money(r['stay']['total'], cur)}). "
            + (f"Cumulative cost breaks even in month {be}." if be else "Cumulative cost does not break even within the horizon.")
            + f" Recurring run cost in the final year is {money(abs(r['migrate']['final_year_run_cost'] - r['stay']['final_year_run_cost']), cur)} "
            f"{'lower' if r['migrate']['final_year_run_cost'] <= r['stay']['final_year_run_cost'] else 'higher'} on the plan."
        )
    L.append("")

    L.append("## Decisions that need a human")
    L.append("")
    if not review:
        L.append("None. Every decision was clear-cut on the rules. That does not remove the need to confirm them with owners.")
    else:
        rows = []
        for a in review:
            why = []
            if a.confidence == "low":
                why.append("close call")
            if "tie_broken_by_order" in a.flags:
                why.append("tie")
            why += [f for f in a.flags if f not in ("tie_broken_by_order", "overridden")]
            rows.append([a.app.app_id, a.app.name, a.disposition, a.confidence, ", ".join(why), " ".join(a.actions)])
        L += _table(["ID", "Application", "Proposed", "Confidence", "Why it needs review", "Suggested next step"], rows)
    L.append("")

    L.append("## Dispositions")
    L.append("")
    rows = []
    for a in assessed:
        top = f"{a.disposition} {a.scores[a.disposition]}" if a.runner_up else "set by rule"
        nxt = f"{a.runner_up} {a.scores[a.runner_up]}" if a.runner_up else ""
        rows.append([a.app.app_id, a.app.name, a.app.business_criticality, a.disposition + (" (override)" if a.overridden else ""),
                     a.confidence, top, nxt])
    L += _table(["ID", "Application", "Criticality", "Disposition", "Confidence", "Score", "Runner-up"], rows)
    L.append("")
    L.append("Scores are the sum of the rule points for each disposition. The reasons for every decision are in the appendix.")
    L.append("")

    L.append("## Waves")
    L.append("")
    s = plan["settings"]
    L.append(f"Settings: at most {s['max_wave_size']} applications per wave; applications with criticality "
             f"{s['critical_min_criticality']} or higher are not placed before wave {s['critical_min_wave']}; "
             f"a dependency is placed in an earlier wave than the application that needs it"
             + (" or the same wave." if s["allow_dependency_in_same_wave"] else "."))
    L.append("")
    if not plan["waves"]:
        L.append("No application is proposed for migration.")
    else:
        rows = []
        for w in plan["waves"]:
            mix = ", ".join(f"{n} {d}" for d, n in w["by_disposition"].items()) or "none"
            rows.append([w["wave"], w["size"], mix, w["max_criticality"] or "", ", ".join(w["shared_services"]) or "none",
                         w["cross_boundary_links_after_wave"]])
        L += _table(["Wave", "Apps", "Mix", "Highest criticality", "Shared services", "Links across the on premises and Azure boundary after the wave"], rows)
        L.append("")
        for w in plan["waves"]:
            L.append(f"### Wave {w['wave']}")
            L.append("")
            if not w["apps"]:
                L.append("No application. Use this wave to prove the landing zone.")
            for m in w["apps"]:
                a = by_id[m]
                tags = []
                if plan["placement"][m]["shared_service"]:
                    tags.append("shared service")
                if plan["placement"][m]["cycle_group"]:
                    tags.append(plan["placement"][m]["cycle_group"])
                dep = f"; depends on {', '.join(a.app.dependencies)}" if a.app.dependencies else ""
                L.append(f"- {m} {a.app.name}: {a.disposition}, criticality {a.app.business_criticality}"
                         + (f" ({', '.join(tags)})" if tags else "") + dep)
            L.append("")
    if plan["not_scheduled"]:
        L.append("### Not in the waves")
        L.append("")
        for m, why in plan["not_scheduled"].items():
            L.append(f"- {m} {by_id[m].app.name}: {why}")
        L.append("")
    if plan["warnings"]:
        L.append("### Dependency warnings")
        L.append("")
        for w in plan["warnings"]:
            L.append(f"- {w}")
        L.append("")

    if cost:
        r = cost["result"]
        L.append("## Cost comparison")
        L.append("")
        L.append(f"Currency: {cur}. Horizon: {cost['horizon_years']} years. "
                 + (f"Discount rate: {cost['discount_rate']:.1%}. " if cost["discount_rate"] is not None else "No discounting. ")
                 + "Nothing here is a price list: every figure is derived from the inventory and the assumptions file.")
        L.append("")
        rows = [["Total over the horizon", money(r["stay"]["total"], cur), money(r["migrate"]["total"], cur), money(r["migrate"]["total"] - r["stay"]["total"], cur)]]
        for y in range(cost["horizon_years"]):
            rows.append([f"Year {y + 1}", money(r["stay"]["by_year"][y], cur), money(r["migrate"]["by_year"][y], cur),
                         money(r["migrate"]["by_year"][y] - r["stay"]["by_year"][y], cur)])
        rows.append(["Recurring run cost in the final year", money(r["stay"]["final_year_run_cost"], cur),
                     money(r["migrate"]["final_year_run_cost"], cur),
                     money(r["migrate"]["final_year_run_cost"] - r["stay"]["final_year_run_cost"], cur)])
        if "npv" in r["stay"]:
            rows.append(["Present value", money(r["stay"]["npv"], cur), money(r["migrate"]["npv"], cur),
                         money(r["migrate"]["npv"] - r["stay"]["npv"], cur)])
        L += _table(["Measure", "Stay on premises", "Follow the plan", "Difference (plan minus stay)"], rows)
        L.append("")
        be = r["break_even_month"]
        disc = ""
        if cost["discount_rate"] is not None:
            bd = r["break_even_month_discounted"]
            disc = f" On a discounted basis: {'month ' + str(bd) if bd else 'not within the horizon'}."
        L.append(f"Break even: {'month ' + str(be) if be else 'not within the horizon'}."
                 + disc
                 + " It is the first month after which cumulative spend on the plan stays at or below cumulative spend on staying.")
        L.append("")
        L.append("The final-year recurring figure matters as much as the total: a plan can cost more over the horizon yet be cheaper to run once the migration is finished, or the reverse.")
        L.append("")
        L.append("### Where the money goes")
        L.append("")
        names = {
            "on_prem_run": "On premises run cost", "azure_run": "Azure run cost (and archive)", "platform_run": "Landing zone and connectivity running cost",
            "other_recurring": "Other recurring costs supplied", "migration_one_off": "Migration effort", "platform_one_off": "Landing zone build and programme management",
            "other_one_off": "Other one-off costs supplied", "hardware_refresh": "Hardware refresh",
        }
        rows = [[names[c], money(r["stay"]["by_category"][c], cur), money(r["migrate"]["by_category"][c], cur)] for c in names
                if r["stay"]["by_category"][c] or r["migrate"]["by_category"][c]]
        L += _table(["Category", "Stay on premises", "Follow the plan"], rows)
        L.append("")
        t = r["timing"]
        L.append(f"Timing used: landing zone {t['landing_zone_months']} month(s), then {t['months_per_wave']:g} month(s) per wave, "
                 f"{t['parallel_run_months']} month(s) of parallel running after each cutover. The last cutover is in month {t['last_cutover_month']}.")
        L.append("")
        L.append("### Sensitivity")
        L.append("")
        L.append("Each key assumption moved by 20 percent, one at a time, then all together. A case is adverse when it makes the plan look worse.")
        L.append("")
        rows = [[x["case"], x["direction"], money(x["saving"], cur), money(x["saving_change_vs_base"], cur),
                 x["break_even_month"] if x["break_even_month"] is not None else "none"] for x in cost["sensitivity"]]
        L += _table(["Assumption", "Change", "Saving over horizon", "Change in saving", "Break-even month"], rows)
        L.append("")
        L.append("### Warnings about these figures")
        L.append("")
        for w in cost["warnings"]:
            L.append(f"- {w}")
        L.append("")
        L.append("### What is not modelled")
        L.append("")
        for w in cost["not_modelled"]:
            L.append(f"- {w}")
        L.append("")

    L.append("## Warnings from reading the inventory")
    L.append("")
    if assess_warnings:
        for w in assess_warnings:
            L.append(f"- {w}")
    else:
        L.append("None.")
    L.append("")

    L.append("## Appendix: reasons for every decision")
    L.append("")
    for a in assessed:
        L.append(f"### {a.app.app_id} {a.app.name}")
        L.append("")
        if a.runner_up:
            L.append(f"Disposition: **{a.disposition}** (score {a.scores[a.disposition]}, runner-up {a.runner_up} {a.scores[a.runner_up]}, "
                     f"confidence {a.confidence})."
                     + (" A human decision overrides this." if a.overridden else ""))
        else:
            L.append(f"Disposition: **{a.disposition}** (decided by rule, confidence {a.confidence}).")
        L.append("")
        for reason in a.reasons:
            L.append(f"- {reason}")
        if not a.reasons:
            L.append("- No rule fired. The baseline applied.")
        if a.actions:
            L.append("")
            L.append("Next steps: " + " ".join(a.actions))
        L.append("")
    return "\n".join(L).rstrip() + "\n"
