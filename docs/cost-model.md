# Cost model

The `cost` command compares the run cost over a horizon (default three years) of two scenarios:

- **Stay:** every application stays as it is on premises.
- **Plan:** the dispositions and waves from the assessment happen.

It contains **no prices**. Every number comes from the inventory or from a cost assumptions file that you write. The template has every value empty, and the command refuses to run until each required input is supplied. The worked example uses clearly labelled illustrative numbers and carries a banner in every output saying so.

```bash
python -m migration_planner show-assumptions-template > my-assumptions.json
# fill in every null from your own quotes, contracts and Azure Migrate output
python -m migration_planner cost inventory.csv --assumptions my-assumptions.json --as-of 2026-11-11
```

## How time works

The model runs month by month for `horizon_years` x 12 months.

1. Months 1 to `landing_zone_months`: the landing zone is built. Its one-off cost is spread across these months.
2. Wave k then occupies `months_per_wave` months (fractions are allowed and rounded cumulatively). Migration effort for the wave is spread across its months. **Cutover is at the end of the last month.**
3. From the month after cutover the application's Azure cost starts. Its on premises cost continues in full for `parallel_run_months`, then falls by `cost_removed_share`. The rest is stranded cost that does not go away because it is shared (hosting, hardware, contracts).
4. Retired applications are decommissioned in the window of wave 1. They stop costing money after that (apart from an optional archive cost).
5. Retained and already-SaaS applications cost the same in both scenarios.
6. Inflation steps up once a year, separately for on premises and Azure.

## Inputs

| Group | Input | Meaning |
|---|---|---|
| top | `horizon_years` | 1 to 10. Three by default |
| top | `discount_rate` | Optional. If set, present values and a discounted break-even are also reported |
| `timing` | `landing_zone_months`, `months_per_wave`, `parallel_run_months` | Programme speed |
| `on_prem` | `annual_cost_inflation` | Yearly rise in on premises run cost |
| `on_prem` | `cost_removed_share` | Share of an application's on premises cost that actually disappears once it has moved, from 0 to 1 |
| `on_prem` | `hardware_refresh_amount`, `hardware_refresh_month` | A refresh you would otherwise have to buy. It is avoided in proportion to the on premises cost already removed in that month |
| `azure` | `annual_cost_inflation` | Yearly change in Azure cost |
| `azure` | `run_cost_factor` | Azure annual run cost as a fraction of the application's current annual cost, per disposition. **The weakest input.** Replace it with Azure Migrate estimates where you have them |
| `azure` | `retire_archive_annual_per_app` | Cost of keeping archived data |
| `unit_costs` | `engineer_day_rate` | Cost of a day of migration effort, in your currency |
| `unit_costs` | `saas_per_user_per_year`, `saas_fixed_per_app_per_year` | Optional. For repurchase, Azure-side cost becomes users x per user cost plus the fixed amount |
| `migration_effort` | `days_per_app` by disposition, `criticality_multiplier` 1 to 5, `contingency` | One-off effort per application = days x multiplier x day rate x (1 + contingency) |
| `platform` | `landing_zone_one_off`, `landing_zone_annual`, `connectivity_annual`, `programme_management_one_off` | Costs of the platform itself. They apply to the plan only, and only if something moves |
| `other_costs` | list of `{label, kind, scenario, amount, month}` | A place for anything else you can estimate: training, data transfer, a support plan. `kind` is `one_off` or `annual`, `scenario` is `migrate`, `stay` or `both` |

The inventory can also carry an optional column `azure_annual_cost_estimate`. When present for an application, it replaces the run cost factor (and the per user rule) for that application.

## Outputs

- `cost_summary.csv`: totals, yearly totals, the final-year recurring cost, present values, category totals and the break-even month.
- `cost_monthly.csv`: every month, every category, both scenarios, and the cumulative difference.
- `cost_by_app.csv`: per application, with the method used for its Azure cost.
- `sensitivity.csv` and the section in `plan.md`: described below.
- `cost.json`: all of it, in one place.

Two figures deserve attention beyond the headline total:

- **Final-year recurring run cost.** A plan can cost more over three years because of one-off costs and parallel running, yet be cheaper to run once finished. Or it can be the reverse. The total alone hides this.
- **Break-even month.** The first month after which cumulative spend on the plan stays at or below cumulative spend on staying. "Not within the horizon" is a legitimate and common answer.

## Sensitivity

The assumptions are moved by 20 percent one at a time, and then all together in the unfavourable direction and all together in the favourable one:

| Assumption | Unfavourable to the plan |
|---|---|
| Current on premises run cost (the baseline you save from) | 20 percent lower |
| Azure run cost | 20 percent higher |
| Migration effort | 20 percent higher |
| Share of on premises cost actually removed | 20 percent lower (capped at 100 percent) |
| Months per wave | 20 percent longer |
| Landing zone and connectivity running cost | 20 percent higher |

Read the table for **which assumption moves the answer most**, and spend your effort verifying that one. In the worked example the largest swings come from the recorded on premises cost, the Azure run cost and the share of on premises cost actually removed. All three are estimates until measured.

## What is not modelled

The command prints these with every result, and they are the main reasons a real business case can differ:

- Data egress and data transfer charges.
- Licensing changes: reuse of existing licences (for example through Azure Hybrid Benefit), vendor uplifts for cloud use, true-ups, and licences that become unnecessary.
- Skills, training, hiring and any change in the cost or size of the IT team.
- Network: circuits and bandwidth beyond the single connectivity figure.
- Commitment discounts, support plans and enterprise agreement terms.
- Right-sizing, growth, seasonality and performance.
- Backup, disaster recovery and security tooling differences.
- Contract exit costs, data centre exit, and asset write-offs.
- Business disruption, downtime and the cost of delay or failure.
- Tax, VAT, currency and the accounting treatment of capital and operating spend.

Several can be added through `other_costs` if you can estimate them. If you cannot, say so in the business case.

## Warnings generated from your data

Counted as zero: applications with no `current_annual_cost`. Modelled as if successful: applications planned to move whose vendor support is not confirmed. Retained applications: no saving unless the shared costs behind them shrink. Programme longer than the horizon: costs after the horizon are not counted, which flatters the plan. And a plain statement when break-even is not reached.

## Hand-checked arithmetic

The tests include a two-application case worked by hand. With one application of 12,000 a year moving at a run cost factor of 0.5 and one application of 6,000 staying, a 36 month horizon, 10 days of effort at 500 per day, a 1,200 landing zone build and 1,200 a year platform running cost, the stay scenario costs 54,000 and the plan 46,700, a saving of 7,300, with break-even in month 18. These numbers are in `tests/test_cost.py` with the working.
