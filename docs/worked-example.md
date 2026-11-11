# Worked example: Wexcombe Group

A fictional manufacturing and distribution group with 42 applications, built to exercise the tool. All names, owners and numbers are invented. The cost assumptions are illustrative placeholders, not prices.

Files: [`examples/inventory.csv`](../examples/inventory.csv), [`examples/cost-assumptions.json`](../examples/cost-assumptions.json), and the generated outputs in [`examples/output/`](../examples/output/), including the full [`plan.md`](../examples/output/plan.md).

```bash
python -m migration_planner plan examples/inventory.csv \
  --assumptions examples/cost-assumptions.json \
  --as-of 2026-11-11 --out examples/output
```

## What the inventory contains

| Feature | Applications |
|---|---|
| ERP (application tier and database) | APP008, APP009 |
| Finance applications | APP011 consolidation, APP013 treasury, APP014 old fixed asset register |
| File servers | APP015 to APP017, and a drawings vault APP018 |
| A legacy application on an unsupported operating system | APP021 (vendor no longer trading, Windows Server 2008 R2 era) |
| SaaS already in use | APP012 payroll, APP040 CRM, APP041 email and collaboration |
| Circular dependencies | APP026 and APP027 (warehouse and transport); APP032, APP033, APP034 (pricing, contracts, customer data) |
| Unknown vendor support status | APP014 (old register), APP035 (demand planning), APP037 (credit control) |
| Shop floor and warehouse equipment | APP019 gateway, APP020 MES, APP028 scanners, APP029 label printing |
| Shared platform services | APP001 to APP007 |
| Retirement candidates | APP014, APP039 (old intranet) |

End-of-support dates for Windows Server and SQL Server versions in the file are taken from Microsoft's published lifecycle pages (checked 11 November 2026, to within a day because of the time zone the page displays). They are used as inventory data. They are not a statement about any real estate.

## Dispositions

| Disposition | Applications | Current annual cost |
|---|---|---|
| rehost | 21 | 893,500 |
| replatform | 9 | 291,000 |
| refactor | 1 | 46,000 |
| repurchase | 1 | 18,000 |
| retire | 2 | 11,500 |
| retain | 8 | 459,000 |

19 of the 42 need a human decision. Cases worth reading in the appendix of the plan:

- **APP009 ERP database** is replatform with a margin of 3: support for its SQL Server version has ended (+3), databases suit a managed service (+3).
- **APP021 furnace scheduling** scores a tie between retain and repurchase (5 each): the vendor will not support the cloud, support ended years ago, and it writes files for the shop floor gateway. The tie is broken towards retain, flagged, and the reasons list both. The example [overrides file](../examples/overrides.example.csv) shows an owner deciding to retire it instead.
- **APP035 demand planning** and **APP037 credit control** have unknown vendor support. Neither is allowed a confident answer, and each carries the action "ask the vendor in writing".
- **APP020 MES, APP028 scanners and APP024 CAD licence server** are retained on thin margins because of site-bound equipment and a dongle licence. Each needs a latency test or a licence conversation before the decision is final.
- **APP030 customer portal** is refactor because the notes describe a monolith that struggles at peak, and the code is changed often. The tool still keeps refactor out of wave 1 and advises sizing it as its own project.
- **APP012, APP040, APP041** are already SaaS and are out of scope.

## Waves

Eight waves for 32 applications, at most eight applications per wave.

| Wave | Contents |
|---|---|
| 1 | Three low-criticality pilots: the ERP test environment, the costing database and the public website |
| 2 | APP001 directory services alone. It is critical, so it cannot be in wave 1, and everything depends on it |
| 3 | Other shared services (DNS and DHCP, certificate authority, backup, print), the ERP database and three more |
| 4 | Monitoring, SFTP and EDI gateway, head office file server |
| 5 | ERP application tier, drawings vault |
| 6 | The warehouse and transport loop, the pricing, contracts and customer data loop, and four others |
| 7 | Finance and reporting applications, the customer portal, BI and credit control |
| 8 | Demand planning, which waits for BI |

Things a reviewer should challenge:

- The **ERP database moves in wave 3 and the ERP application tier in wave 5**. For two waves the application tier on premises talks to its database across the hybrid link. Strict "dependencies first" ordering produces this. Group them (set `allow_dependency_in_same_wave`, or override one of them) or test the link before accepting. The boundary link counts in the plan show 24 links crossing after wave 3.
- **Two circular groups** are each scheduled in a single wave, with a warning that names the loop.
- **Retained applications** (the shop floor gateway, MES, CAD licence server and scanner service) depend on moved ones. The plan lists each pair, because those links stay for good.
- Wave 2 holds a single application. That is the critical rule and the dependency structure at work, and it is worth saying so to the programme board rather than hiding it.

## Cost on illustrative assumptions

Three year horizon, GBP, discount rate 5 percent, run cost factors of 0.85 (rehost), 0.70 (replatform), 0.60 (refactor) and 0.80 (repurchase), 90 percent of on premises cost removed, 3 months of landing zone work then 2 months per wave. All invented.

| Measure | Stay on premises | Follow the plan | Difference |
|---|---|---|---|
| Total over three years | GBP 5,766,030 | GBP 6,300,291 | GBP 534,260 dearer |
| Year 3 recurring run cost | GBP 1,859,270 | GBP 1,797,439 | GBP 61,832 cheaper |
| Present value | GBP 5,344,065 | GBP 5,874,175 | GBP 530,110 dearer |

On these made-up numbers the plan does not break even within three years, yet is cheaper to run by year 3. This is a common shape: one-off costs, parallel running and stranded cost come first, and the run-rate benefit arrives late. If every key assumption moved in the plan's favour at once, break-even would arrive in month 21. If every one moved against it, the plan would cost about GBP 1.9 million more. The example is meant to show how to read a result like this, not to suggest what a real estate would show.

The largest swings come from the recorded on premises cost, the Azure run cost and the share of on premises cost that is actually removed (each moves the three year difference by roughly GBP 400,000 to 500,000 for a 20 percent change). That is where verification effort should go.

## Reproducing and checking

The test suite re-runs the plan and compares every output file byte for byte with `examples/output/`, so the numbers above cannot drift from the tool.
