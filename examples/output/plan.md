# Azure migration plan

> **Illustrative cost assumptions.** The cost figures in this plan come from placeholder numbers, not from quotes or an Azure Migrate assessment. They show how the model works and must not be used for a decision.

> **Planning aid only.** This plan comes from a rule-based tool working on the inventory it was given. It does not replace Azure Migrate discovery and assessment, a vendor quote, or the judgement of the application owners. Cost results are only as good as the inputs.

## Inputs

| Item | Value |
|---|---|
| Inventory | inventory.csv (sha256 3e8cc0d5c4c4) |
| Rules | sha256 514b5efec22c |
| Assessed as at | 2026-11-11 |
| Tool version | 0.1.0 |
| Cost assumptions | ILLUSTRATIVE ASSUMPTIONS for the fictional Wexcombe estate. These are invented placeholder numbers, not real prices or quotes. |

## Summary

| Disposition | Meaning | Applications | Current annual cost |
|---|---|---|---|
| rehost | move as it is to Azure virtual machines | 21 | 893,500 |
| replatform | move with limited changes, for example to a managed database or file service | 9 | 291,000 |
| refactor | change the code to suit the cloud | 1 | 46,000 |
| repurchase | replace with a different product, usually SaaS | 1 | 18,000 |
| retire | switch off | 2 | 11,500 |
| retain | keep where it is, or already SaaS | 8 | 459,000 |
| total |  | 42 | 1,719,000 |

42 applications assessed. 19 need a human decision before the plan is relied on (listed below). 8 migration wave(s) are proposed for 32 application(s), and 2 circular dependency group(s) were found.

On the assumptions supplied, following the plan costs GBP 534,260 (9.3 percent) more than staying as is over 3 years (GBP 6,300,291 against GBP 5,766,030). Cumulative cost does not break even within the horizon. Recurring run cost in the final year is GBP 61,832 lower on the plan.

## Decisions that need a human

| ID | Application | Proposed | Confidence | Why it needs review | Suggested next step |
|---|---|---|---|---|---|
| APP001 | Directory services (domain controllers) | rehost | low | close call, data_protection_review | Complete a data protection review and confirm region, residency and access controls before cutover. |
| APP002 | DNS and DHCP | rehost | low | close call |  |
| APP003 | Internal certificate authority | rehost | low | close call, tie, end_of_support_soon, data_protection_review | Complete a data protection review and confirm region, residency and access controls before cutover. |
| APP004 | Backup platform | rehost | low | close call |  |
| APP005 | Monitoring and alerting | rehost | low | close call, tie |  |
| APP007 | SFTP and EDI gateway | rehost | low | close call, tie, end_of_support_soon |  |
| APP010 | ERP test and training environment | rehost | low | close call, end_of_support_soon |  |
| APP014 | Fixed asset register (old) | retire | high |  | Confirm with the owner that nobody needs the function, and agree what happens to the data (archive or delete). Confirm with the owner and check for hidden dependants before retiring. |
| APP020 | Manufacturing execution system | retain | low | close call, site_bound_equipment, end_of_support_soon | Measure round-trip latency and loss to the equipment before deciding to move it. |
| APP021 | Furnace scheduling (legacy) | retain | low | close call, tie, site_bound_equipment, vendor_no_cloud_support, end_of_support_passed | Measure round-trip latency and loss to the equipment before deciding to move it. Get the vendor position in writing and ask what route they offer (hosted, SaaS or a newer version). If a stopgap is unavoidable, check Microsoft's current terms for Extended Security Updates and record a dated exit. |
| APP024 | CAD licence server | retain | low | close call, licence_restriction | Read the licence with the vendor: some licences tied to hardware or a dongle cannot move. |
| APP028 | Handheld scanner service | retain | low | close call, site_bound_equipment, end_of_support_soon | Measure round-trip latency and loss to the equipment before deciding to move it. |
| APP030 | Customer portal and order entry | refactor | low | close call, end_of_support_soon | Confirm the problem with the owner and size the refactor separately. Avoid doing it during the move itself. |
| APP031 | Supplier portal | replatform | low | close call, end_of_support_passed | If a stopgap is unavoidable, check Microsoft's current terms for Extended Security Updates and record a dated exit. |
| APP035 | Demand planning | rehost | low | close call, tie, vendor_support_unknown, end_of_support_soon | Ask the vendor in writing whether the product is supported on Azure, on which versions, and under what licence terms. |
| APP036 | Business intelligence and reporting | replatform | low | close call, data_protection_review | Complete a data protection review and confirm region, residency and access controls before cutover. |
| APP037 | Credit control | replatform | low | close call, tie, vendor_support_unknown, end_of_support_passed | Ask the vendor in writing whether the product is supported on Azure, on which versions, and under what licence terms. If a stopgap is unavoidable, check Microsoft's current terms for Extended Security Updates and record a dated exit. |
| APP038 | Time and attendance | rehost | low | close call, end_of_support_soon, data_protection_review | Complete a data protection review and confirm region, residency and access controls before cutover. |
| APP039 | Old intranet | retire | high |  | Confirm with the owner that nobody needs the function, and agree what happens to the data (archive or delete). Confirm with the owner and check for hidden dependants before retiring. |

## Dispositions

| ID | Application | Criticality | Disposition | Confidence | Score | Runner-up |
|---|---|---|---|---|---|---|
| APP001 | Directory services (domain controllers) | 5 | rehost | low | rehost 4 | replatform 3 |
| APP002 | DNS and DHCP | 5 | rehost | low | rehost 4 | replatform 3 |
| APP003 | Internal certificate authority | 4 | rehost | low | rehost 4 | replatform 4 |
| APP004 | Backup platform | 4 | rehost | low | rehost 4 | replatform 3 |
| APP005 | Monitoring and alerting | 3 | rehost | low | rehost 3 | replatform 3 |
| APP006 | Print servers | 2 | replatform | medium | replatform 6 | rehost 3 |
| APP007 | SFTP and EDI gateway | 4 | rehost | low | rehost 4 | replatform 4 |
| APP008 | ERP application tier | 5 | rehost | medium | rehost 4 | replatform 2 |
| APP009 | ERP database | 5 | replatform | medium | replatform 7 | rehost 4 |
| APP010 | ERP test and training environment | 2 | rehost | low | rehost 3 | replatform 2 |
| APP011 | Group consolidation and reporting | 4 | rehost | medium | rehost 4 | replatform 2 |
| APP012 | Payroll | 5 | retain | high | set by rule |  |
| APP013 | Treasury and bank connectivity | 5 | rehost | medium | rehost 4 | replatform 1 |
| APP014 | Fixed asset register (old) | 1 | retire | high | retire 12 | replatform 2 |
| APP015 | Head office file server | 4 | replatform | medium | replatform 7 | rehost 4 |
| APP016 | Castings plant file server | 3 | replatform | high | replatform 7 | rehost 3 |
| APP017 | Distribution centre file server | 3 | replatform | medium | replatform 5 | rehost 3 |
| APP018 | Engineering drawings vault | 4 | rehost | medium | rehost 4 | replatform 2 |
| APP019 | Shop floor controller gateway | 5 | retain | high | retain 9 | repurchase 3 |
| APP020 | Manufacturing execution system | 5 | retain | low | retain 4 | rehost 3 |
| APP021 | Furnace scheduling (legacy) | 3 | retain | low | retain 5 | repurchase 5 |
| APP022 | Quality management | 3 | repurchase | medium | repurchase 5 | rehost 3 |
| APP023 | Maintenance management | 3 | rehost | medium | rehost 3 | replatform 1 |
| APP024 | CAD licence server | 3 | retain | low | retain 2 | rehost 1 |
| APP025 | Costing database | 2 | rehost | medium | rehost 4 | retire 2 |
| APP026 | Warehouse management system | 5 | rehost | medium | rehost 4 | replatform 1 |
| APP027 | Transport management system | 4 | rehost | medium | rehost 4 | replatform 1 |
| APP028 | Handheld scanner service | 4 | retain | low | retain 4 | rehost 3 |
| APP029 | Carrier label printing | 3 | replatform | medium | replatform 4 | rehost 2 |
| APP030 | Customer portal and order entry | 3 | refactor | low | refactor 6 | replatform 5 |
| APP031 | Supplier portal | 2 | replatform | low | replatform 4 | rehost 3 |
| APP032 | Pricing engine | 4 | rehost | medium | rehost 4 | replatform 2 |
| APP033 | Contracts and rebates | 3 | rehost | medium | rehost 4 | replatform 2 |
| APP034 | Customer master data service | 4 | rehost | medium | rehost 4 | replatform 1 |
| APP035 | Demand planning | 3 | rehost | low | rehost 1 | retain 1 |
| APP036 | Business intelligence and reporting | 3 | replatform | low | replatform 4 | rehost 3 |
| APP037 | Credit control | 3 | replatform | low | replatform 2 | repurchase 2 |
| APP038 | Time and attendance | 3 | rehost | low | rehost 3 | replatform 2 |
| APP039 | Old intranet | 1 | retire | high | retire 12 | repurchase 5 |
| APP040 | Customer relationship management | 4 | retain | high | set by rule |  |
| APP041 | Email and collaboration | 5 | retain | high | set by rule |  |
| APP042 | Public website | 2 | rehost | medium | rehost 3 | replatform 1 |

Scores are the sum of the rule points for each disposition. The reasons for every decision are in the appendix.

## Waves

Settings: at most 8 applications per wave; applications with criticality 4 or higher are not placed before wave 2; a dependency is placed in an earlier wave than the application that needs it.

| Wave | Apps | Mix | Highest criticality | Shared services | Links across the on premises and Azure boundary after the wave |
|---|---|---|---|---|---|
| 1 | 3 | 3 rehost | 2 | none | 0 |
| 2 | 1 | 1 rehost | 5 | APP001 | 25 |
| 3 | 8 | 4 rehost, 4 replatform | 5 | APP002, APP003, APP004, APP006, APP009 | 24 |
| 4 | 3 | 2 rehost, 1 replatform | 4 | APP005, APP007 | 22 |
| 5 | 2 | 2 rehost | 5 | APP008 | 31 |
| 6 | 8 | 6 rehost, 1 replatform, 1 repurchase | 5 | APP026, APP027 | 24 |
| 7 | 6 | 2 rehost, 3 replatform, 1 refactor | 5 | none | 9 |
| 8 | 1 | 1 rehost | 3 | none | 7 |

### Wave 1

- APP010 ERP test and training environment: rehost, criticality 2
- APP025 Costing database: rehost, criticality 2
- APP042 Public website: rehost, criticality 2

### Wave 2

- APP001 Directory services (domain controllers): rehost, criticality 5 (shared service)

### Wave 3

- APP002 DNS and DHCP: rehost, criticality 5 (shared service); depends on APP001
- APP003 Internal certificate authority: rehost, criticality 4 (shared service); depends on APP001
- APP004 Backup platform: rehost, criticality 4 (shared service); depends on APP001
- APP006 Print servers: replatform, criticality 2 (shared service); depends on APP001
- APP009 ERP database: replatform, criticality 5 (shared service); depends on APP001
- APP016 Castings plant file server: replatform, criticality 3; depends on APP001
- APP017 Distribution centre file server: replatform, criticality 3; depends on APP001
- APP038 Time and attendance: rehost, criticality 3; depends on APP001, APP012

### Wave 4

- APP005 Monitoring and alerting: rehost, criticality 3 (shared service); depends on APP001, APP002
- APP007 SFTP and EDI gateway: rehost, criticality 4 (shared service); depends on APP001, APP002
- APP015 Head office file server: replatform, criticality 4; depends on APP001, APP002

### Wave 5

- APP008 ERP application tier: rehost, criticality 5 (shared service); depends on APP001, APP007, APP009
- APP018 Engineering drawings vault: rehost, criticality 4; depends on APP001, APP015

### Wave 6

- APP022 Quality management: repurchase, criticality 3; depends on APP001, APP008
- APP023 Maintenance management: rehost, criticality 3; depends on APP001, APP008
- APP026 Warehouse management system: rehost, criticality 5 (shared service, CYC-1); depends on APP001, APP007, APP008, APP027
- APP027 Transport management system: rehost, criticality 4 (shared service, CYC-1); depends on APP001, APP008, APP026
- APP031 Supplier portal: replatform, criticality 2; depends on APP001, APP008
- APP032 Pricing engine: rehost, criticality 4 (CYC-2); depends on APP033
- APP033 Contracts and rebates: rehost, criticality 3 (CYC-2); depends on APP008, APP034
- APP034 Customer master data service: rehost, criticality 4 (CYC-2); depends on APP008, APP032

### Wave 7

- APP011 Group consolidation and reporting: rehost, criticality 4; depends on APP008, APP009
- APP013 Treasury and bank connectivity: rehost, criticality 5; depends on APP007, APP008
- APP029 Carrier label printing: replatform, criticality 3; depends on APP026
- APP030 Customer portal and order entry: refactor, criticality 3; depends on APP001, APP008, APP026, APP032
- APP036 Business intelligence and reporting: replatform, criticality 3; depends on APP001, APP008, APP009, APP026, APP027
- APP037 Credit control: replatform, criticality 3; depends on APP001, APP008

### Wave 8

- APP035 Demand planning: rehost, criticality 3; depends on APP008, APP036

### Not in the waves

- APP012 Payroll: not in scope (already SaaS or otherwise unchanged)
- APP014 Fixed asset register (old): retire (decommission task, not a migration)
- APP019 Shop floor controller gateway: retained on premises
- APP020 Manufacturing execution system: retained on premises
- APP021 Furnace scheduling (legacy): retained on premises
- APP024 CAD licence server: retained on premises
- APP028 Handheld scanner service: retained on premises
- APP039 Old intranet: retire (decommission task, not a migration)
- APP040 Customer relationship management: not in scope (already SaaS or otherwise unchanged)
- APP041 Email and collaboration: not in scope (already SaaS or otherwise unchanged)

### Dependency warnings

- Circular dependency CYC-1: APP026 -> APP027 -> APP026. These 2 applications are scheduled together in one wave and must be cut over together. Check whether every link is a real runtime dependency: a reporting feed or file extract can often be treated as loosely coupled, which would let them move separately.
- Circular dependency CYC-2: APP032 -> APP033 -> APP034 -> APP032. These 3 applications are scheduled together in one wave and must be cut over together. Check whether every link is a real runtime dependency: a reporting feed or file extract can often be treated as loosely coupled, which would let them move separately.
- APP019 stays on premises but depends on APP001 (wave 2). Once those move it calls into Azure across the hybrid connection: test latency and bandwidth.
- APP020 stays on premises but depends on APP001 (wave 2), APP008 (wave 5), APP009 (wave 3). Once those move it calls into Azure across the hybrid connection: test latency and bandwidth.
- APP024 stays on premises but depends on APP001 (wave 2). Once those move it calls into Azure across the hybrid connection: test latency and bandwidth.
- APP028 stays on premises but depends on APP001 (wave 2), APP026 (wave 6). Once those move it calls into Azure across the hybrid connection: test latency and bandwidth.

## Cost comparison

Currency: GBP. Horizon: 3 years. Discount rate: 5.0%. Nothing here is a price list: every figure is derived from the inventory and the assumptions file.

| Measure | Stay on premises | Follow the plan | Difference (plan minus stay) |
|---|---|---|---|
| Total over the horizon | GBP 5,766,030 | GBP 6,300,291 | GBP 534,260 |
| Year 1 | GBP 1,719,000 | GBP 2,251,478 | GBP 532,478 |
| Year 2 | GBP 2,187,760 | GBP 2,251,373 | GBP 63,613 |
| Year 3 | GBP 1,859,270 | GBP 1,797,439 | -GBP 61,832 |
| Recurring run cost in the final year | GBP 1,859,270 | GBP 1,797,439 | -GBP 61,832 |
| Present value | GBP 5,344,065 | GBP 5,874,175 | GBP 530,110 |

Break even: not within the horizon. On a discounted basis: not within the horizon. It is the first month after which cumulative spend on the plan stays at or below cumulative spend on staying.

The final-year recurring figure matters as much as the total: a plan can cost more over the horizon yet be cheaper to run once the migration is finished, or the reverse.

### Where the money goes

| Category | Stay on premises | Follow the plan |
|---|---|---|
| On premises run cost | GBP 5,366,030 | GBP 3,148,988 |
| Azure run cost (and archive) | GBP 0 | GBP 1,988,015 |
| Landing zone and connectivity running cost | GBP 0 | GBP 269,798 |
| Other recurring costs supplied | GBP 0 | GBP 37,500 |
| Migration effort | GBP 0 | GBP 387,952 |
| Landing zone build and programme management | GBP 0 | GBP 300,000 |
| Other one-off costs supplied | GBP 0 | GBP 25,000 |
| Hardware refresh | GBP 400,000 | GBP 143,037 |

Timing used: landing zone 3 month(s), then 2 month(s) per wave, 1 month(s) of parallel running after each cutover. The last cutover is in month 19.

### Sensitivity

Each key assumption moved by 20 percent, one at a time, then all together. A case is adverse when it makes the plan look worse.

| Assumption | Change | Saving over horizon | Change in saving | Break-even month |
|---|---|---|---|---|
| Current on premises run cost | adverse (-20%) | -GBP 977,669 | -GBP 443,409 | none |
| Current on premises run cost | favourable (+20%) | -GBP 90,852 | GBP 443,409 | none |
| Azure run cost | adverse (+20%) | -GBP 931,863 | -GBP 397,603 | none |
| Azure run cost | favourable (-20%) | -GBP 136,657 | GBP 397,603 | none |
| Migration effort | adverse (+20%) | -GBP 611,851 | -GBP 77,590 | none |
| Migration effort | favourable (-20%) | -GBP 456,670 | GBP 77,590 | none |
| Share of on premises cost actually removed | adverse (-20%) | -GBP 1,029,061 | -GBP 494,801 | none |
| Share of on premises cost actually removed | favourable (+20%) | -GBP 259,371 | GBP 274,890 | none |
| Months per wave (programme speed) | adverse (+20%) | -GBP 599,536 | -GBP 65,276 | none |
| Months per wave (programme speed) | favourable (-20%) | -GBP 504,463 | GBP 29,797 | none |
| Landing zone and connectivity running cost | adverse (+20%) | -GBP 588,220 | -GBP 53,960 | none |
| Landing zone and connectivity running cost | favourable (-20%) | -GBP 480,300 | GBP 53,960 | none |
| All of the above together | all adverse | -GBP 1,870,398 | -GBP 1,336,137 | none |
| All of the above together | all favourable | GBP 887,127 | GBP 1,421,387 | 21 |

### Warnings about these figures

- These assumptions are marked illustrative. The figures are not real prices and must not be used for a decision.
- 2 application(s) are planned to move although vendor support in the cloud is not confirmed (APP035, APP037). Their cost is modelled as if the move succeeds as planned.
- 5 retained application(s) stay on premises and cost the same in both scenarios. Any saving depends on the shared costs behind them (hosting, hardware, licences) actually shrinking.
- Repurchased applications use the run cost factor because no saas_per_user_per_year was supplied.
- The migration scenario does not break even within 3 years on these assumptions.

### What is not modelled

- Data egress and data transfer charges, including moving data into Azure and traffic between Azure and the remaining on premises estate.
- Licensing changes: whether existing licences can be reused (for example through Azure Hybrid Benefit), vendor uplifts for cloud use, true-ups, and the cost of any licences that become unnecessary.
- Skills, training, hiring and any change in the size or cost of the IT team. People cost is only included where it is inside the supplied unit costs.
- Network: new or upgraded circuits, internet breakout and bandwidth needed for hybrid running, beyond the single connectivity figure supplied.
- Commitment discounts (reservations, savings plans), support plans and enterprise agreement terms, unless already reflected in the run cost factors you supplied.
- Right-sizing, growth, seasonality and performance. Azure run cost follows the factors supplied, not a measured sizing.
- Backup, disaster recovery and security tooling differences between today and Azure, unless included in the factors or in 'other_costs'.
- Exit costs on existing contracts, early termination fees, data centre or lease exit, and one-off write-offs of assets.
- Business disruption, downtime, lost productivity and the cost of delay or failure.
- Tax, VAT, foreign exchange and the accounting treatment of capital and operating spend.

## Warnings from reading the inventory

None.

## Appendix: reasons for every decision

### APP001 Directory services (domain controllers)

Disposition: **rehost** (score 4, runner-up replatform 3, confidence low).

- Supported in the cloud, which keeps the lower-change routes open. [R07: rehost +1, replatform +1]
- Business criticality is 5. A critical application favours the route with the least change, and it is not a retirement candidate. [R13: rehost +1, refactor -2, repurchase -1, retire -4]
- Refactoring needs source code the organisation controls. This is not recorded as in-house custom code. [R14: refactor -4]
- A shared platform service. These usually move to the cloud equivalent, and the landing zone design depends on them, so they are scheduled early. [R20: replatform +2]
- Data sensitivity is high. That does not stop a move, but it needs a data protection review, region and residency checks and tighter access design first. [R21: retain +1]
- 26 other applications depend on it, so a change in behaviour ripples out. Prefer a route that keeps interfaces the same. [R23: refactor -1, repurchase -1]

Next steps: Complete a data protection review and confirm region, residency and access controls before cutover.

### APP002 DNS and DHCP

Disposition: **rehost** (score 4, runner-up replatform 3, confidence low).

- Supported in the cloud, which keeps the lower-change routes open. [R07: rehost +1, replatform +1]
- Business criticality is 5. A critical application favours the route with the least change, and it is not a retirement candidate. [R13: rehost +1, refactor -2, repurchase -1, retire -4]
- Refactoring needs source code the organisation controls. This is not recorded as in-house custom code. [R14: refactor -4]
- A shared platform service. These usually move to the cloud equivalent, and the landing zone design depends on them, so they are scheduled early. [R20: replatform +2]

### APP003 Internal certificate authority

Disposition: **rehost** (score 4, runner-up replatform 4, confidence low).

- Supported in the cloud, which keeps the lower-change routes open. [R07: rehost +1, replatform +1]
- Support ends on 2027-01-12, within the next 12 months. Plan the remediation as part of the move rather than after it. [R09: replatform +1, repurchase +1]
- Business criticality is 4. A critical application favours the route with the least change, and it is not a retirement candidate. [R13: rehost +1, refactor -2, repurchase -1, retire -4]
- Refactoring needs source code the organisation controls. This is not recorded as in-house custom code. [R14: refactor -4]
- A shared platform service. These usually move to the cloud equivalent, and the landing zone design depends on them, so they are scheduled early. [R20: replatform +2]
- Data sensitivity is high. That does not stop a move, but it needs a data protection review, region and residency checks and tighter access design first. [R21: retain +1]
- Two dispositions scored the same, so the tie was broken by the configured order. Treat rehost and replatform as equally open.

Next steps: Complete a data protection review and confirm region, residency and access controls before cutover.

### APP004 Backup platform

Disposition: **rehost** (score 4, runner-up replatform 3, confidence low).

- Supported in the cloud, which keeps the lower-change routes open. [R07: rehost +1, replatform +1]
- Business criticality is 4. A critical application favours the route with the least change, and it is not a retirement candidate. [R13: rehost +1, refactor -2, repurchase -1, retire -4]
- Refactoring needs source code the organisation controls. This is not recorded as in-house custom code. [R14: refactor -4]
- A shared platform service. These usually move to the cloud equivalent, and the landing zone design depends on them, so they are scheduled early. [R20: replatform +2]

### APP005 Monitoring and alerting

Disposition: **rehost** (score 3, runner-up replatform 3, confidence low).

- Supported in the cloud, which keeps the lower-change routes open. [R07: rehost +1, replatform +1]
- Refactoring needs source code the organisation controls. This is not recorded as in-house custom code. [R14: refactor -4]
- A shared platform service. These usually move to the cloud equivalent, and the landing zone design depends on them, so they are scheduled early. [R20: replatform +2]
- Two dispositions scored the same, so the tie was broken by the configured order. Treat rehost and replatform as equally open.

### APP006 Print servers

Disposition: **replatform** (score 6, runner-up rehost 3, confidence medium).

- Supported in the cloud, which keeps the lower-change routes open. [R07: rehost +1, replatform +1]
- Support for the operating system or product ended on 2023-10-10. Staying as it is is not a durable answer. Moving the machine unchanged only changes where the risk sits, so the platform should change or the application should be replaced or retired. [R08: replatform +3, refactor +1, repurchase +2, retire +1, retain -2]
- Refactoring needs source code the organisation controls. This is not recorded as in-house custom code. [R14: refactor -4]
- A shared platform service. These usually move to the cloud equivalent, and the landing zone design depends on them, so they are scheduled early. [R20: replatform +2]

Next steps: If a stopgap is unavoidable, check Microsoft's current terms for Extended Security Updates and record a dated exit.

### APP007 SFTP and EDI gateway

Disposition: **rehost** (score 4, runner-up replatform 4, confidence low).

- Supported in the cloud, which keeps the lower-change routes open. [R07: rehost +1, replatform +1]
- Support ends on 2027-01-12, within the next 12 months. Plan the remediation as part of the move rather than after it. [R09: replatform +1, repurchase +1]
- Business criticality is 4. A critical application favours the route with the least change, and it is not a retirement candidate. [R13: rehost +1, refactor -2, repurchase -1, retire -4]
- Refactoring needs source code the organisation controls. This is not recorded as in-house custom code. [R14: refactor -4]
- A shared platform service. These usually move to the cloud equivalent, and the landing zone design depends on them, so they are scheduled early. [R20: replatform +2]
- Two dispositions scored the same, so the tie was broken by the configured order. Treat rehost and replatform as equally open.

### APP008 ERP application tier

Disposition: **rehost** (score 4, runner-up replatform 2, confidence medium).

- Supported in the cloud, which keeps the lower-change routes open. [R07: rehost +1, replatform +1]
- Support ends on 2027-01-12, within the next 12 months. Plan the remediation as part of the move rather than after it. [R09: replatform +1, repurchase +1]
- Business criticality is 5. A critical application favours the route with the least change, and it is not a retirement candidate. [R13: rehost +1, refactor -2, repurchase -1, retire -4]
- Refactoring needs source code the organisation controls. This is not recorded as in-house custom code. [R14: refactor -4]
- Data sensitivity is high. That does not stop a move, but it needs a data protection review, region and residency checks and tighter access design first. [R21: retain +1]
- 15 other applications depend on it, so a change in behaviour ripples out. Prefer a route that keeps interfaces the same. [R23: refactor -1, repurchase -1]

Next steps: Complete a data protection review and confirm region, residency and access controls before cutover.

### APP009 ERP database

Disposition: **replatform** (score 7, runner-up rehost 4, confidence medium).

- Supported in the cloud, which keeps the lower-change routes open. [R07: rehost +1, replatform +1]
- Support for the operating system or product ended on 2026-07-14. Staying as it is is not a durable answer. Moving the machine unchanged only changes where the risk sits, so the platform should change or the application should be replaced or retired. [R08: replatform +3, refactor +1, repurchase +2, retire +1, retain -2]
- Business criticality is 5. A critical application favours the route with the least change, and it is not a retirement candidate. [R13: rehost +1, refactor -2, repurchase -1, retire -4]
- Refactoring needs source code the organisation controls. This is not recorded as in-house custom code. [R14: refactor -4]
- A database often benefits from a managed service, which removes patching and backup work. Check engine version and feature compatibility first. [R18: replatform +3]
- Data sensitivity is high. That does not stop a move, but it needs a data protection review, region and residency checks and tighter access design first. [R21: retain +1]

Next steps: If a stopgap is unavoidable, check Microsoft's current terms for Extended Security Updates and record a dated exit. Complete a data protection review and confirm region, residency and access controls before cutover.

### APP010 ERP test and training environment

Disposition: **rehost** (score 3, runner-up replatform 2, confidence low).

- Supported in the cloud, which keeps the lower-change routes open. [R07: rehost +1, replatform +1]
- Support ends on 2027-01-12, within the next 12 months. Plan the remediation as part of the move rather than after it. [R09: replatform +1, repurchase +1]
- Refactoring needs source code the organisation controls. This is not recorded as in-house custom code. [R14: refactor -4]

### APP011 Group consolidation and reporting

Disposition: **rehost** (score 4, runner-up replatform 2, confidence medium).

- Supported in the cloud, which keeps the lower-change routes open. [R07: rehost +1, replatform +1]
- Support ends on 2027-01-12, within the next 12 months. Plan the remediation as part of the move rather than after it. [R09: replatform +1, repurchase +1]
- Business criticality is 4. A critical application favours the route with the least change, and it is not a retirement candidate. [R13: rehost +1, refactor -2, repurchase -1, retire -4]
- Refactoring needs source code the organisation controls. This is not recorded as in-house custom code. [R14: refactor -4]
- Data sensitivity is high. That does not stop a move, but it needs a data protection review, region and residency checks and tighter access design first. [R21: retain +1]

Next steps: Complete a data protection review and confirm region, residency and access controls before cutover.

### APP012 Payroll

Disposition: **retain** (decided by rule, confidence high).

- Already delivered as SaaS, so there is nothing to migrate. It is left out of the waves and out of the cost comparison. Check that its integrations still work after the apps around it move. [R01: decides: retain]
- Supported in the cloud, which keeps the lower-change routes open. [R07: rehost +1, replatform +1]
- Business criticality is 5. A critical application favours the route with the least change, and it is not a retirement candidate. [R13: rehost +1, refactor -2, repurchase -1, retire -4]
- Refactoring needs source code the organisation controls. This is not recorded as in-house custom code. [R14: refactor -4]
- Data sensitivity is restricted. That does not stop a move, but it needs a data protection review, region and residency checks and tighter access design first. [R21: retain +1]

### APP013 Treasury and bank connectivity

Disposition: **rehost** (score 4, runner-up replatform 1, confidence medium).

- Supported in the cloud, which keeps the lower-change routes open. [R07: rehost +1, replatform +1]
- Business criticality is 5. A critical application favours the route with the least change, and it is not a retirement candidate. [R13: rehost +1, refactor -2, repurchase -1, retire -4]
- Refactoring needs source code the organisation controls. This is not recorded as in-house custom code. [R14: refactor -4]
- Data sensitivity is restricted. That does not stop a move, but it needs a data protection review, region and residency checks and tighter access design first. [R21: retain +1]

Next steps: Complete a data protection review and confirm region, residency and access controls before cutover.

### APP014 Fixed asset register (old)

Disposition: **retire** (score 12, runner-up replatform 2, confidence high).

- Vendor support in the cloud has not been confirmed. The score is held back until it is, because moving an application on an assumption is how migrations fail. [R05: rehost -1, replatform -1, retain +1]
- Support for the operating system or product ended on 2023-10-10. Staying as it is is not a durable answer. Moving the machine unchanged only changes where the risk sits, so the platform should change or the application should be replaced or retired. [R08: replatform +3, refactor +1, repurchase +2, retire +1, retain -2]
- Only 2 user(s) and business criticality 1. Low use and low criticality make this a retirement candidate. [R10: retire +5]
- The notes suggest the application is duplicated, superseded or no longer used. [R11: retire +4]
- Nobody changes it, few people use it and it is not critical. [R12: retire +2]
- Refactoring needs source code the organisation controls. This is not recorded as in-house custom code. [R14: refactor -4]

Next steps: Confirm with the owner that nobody needs the function, and agree what happens to the data (archive or delete). Confirm with the owner and check for hidden dependants before retiring.

### APP015 Head office file server

Disposition: **replatform** (score 7, runner-up rehost 4, confidence medium).

- Supported in the cloud, which keeps the lower-change routes open. [R07: rehost +1, replatform +1]
- Support for the operating system or product ended on 2023-10-10. Staying as it is is not a durable answer. Moving the machine unchanged only changes where the risk sits, so the platform should change or the application should be replaced or retired. [R08: replatform +3, refactor +1, repurchase +2, retire +1, retain -2]
- Business criticality is 4. A critical application favours the route with the least change, and it is not a retirement candidate. [R13: rehost +1, refactor -2, repurchase -1, retire -4]
- Refactoring needs source code the organisation controls. This is not recorded as in-house custom code. [R14: refactor -4]
- File services usually move to a managed file or collaboration service rather than a like-for-like virtual machine. Check permissions, long paths and applications that use drive letters. [R19: replatform +3]
- Data sensitivity is high. That does not stop a move, but it needs a data protection review, region and residency checks and tighter access design first. [R21: retain +1]

Next steps: If a stopgap is unavoidable, check Microsoft's current terms for Extended Security Updates and record a dated exit. Complete a data protection review and confirm region, residency and access controls before cutover.

### APP016 Castings plant file server

Disposition: **replatform** (score 7, runner-up rehost 3, confidence high).

- Supported in the cloud, which keeps the lower-change routes open. [R07: rehost +1, replatform +1]
- Support for the operating system or product ended on 2023-10-10. Staying as it is is not a durable answer. Moving the machine unchanged only changes where the risk sits, so the platform should change or the application should be replaced or retired. [R08: replatform +3, refactor +1, repurchase +2, retire +1, retain -2]
- Refactoring needs source code the organisation controls. This is not recorded as in-house custom code. [R14: refactor -4]
- File services usually move to a managed file or collaboration service rather than a like-for-like virtual machine. Check permissions, long paths and applications that use drive letters. [R19: replatform +3]

Next steps: If a stopgap is unavoidable, check Microsoft's current terms for Extended Security Updates and record a dated exit.

### APP017 Distribution centre file server

Disposition: **replatform** (score 5, runner-up rehost 3, confidence medium).

- Supported in the cloud, which keeps the lower-change routes open. [R07: rehost +1, replatform +1]
- Support ends on 2027-01-12, within the next 12 months. Plan the remediation as part of the move rather than after it. [R09: replatform +1, repurchase +1]
- Refactoring needs source code the organisation controls. This is not recorded as in-house custom code. [R14: refactor -4]
- File services usually move to a managed file or collaboration service rather than a like-for-like virtual machine. Check permissions, long paths and applications that use drive letters. [R19: replatform +3]

### APP018 Engineering drawings vault

Disposition: **rehost** (score 4, runner-up replatform 2, confidence medium).

- Supported in the cloud, which keeps the lower-change routes open. [R07: rehost +1, replatform +1]
- Support ends on 2027-01-12, within the next 12 months. Plan the remediation as part of the move rather than after it. [R09: replatform +1, repurchase +1]
- Business criticality is 4. A critical application favours the route with the least change, and it is not a retirement candidate. [R13: rehost +1, refactor -2, repurchase -1, retire -4]
- Refactoring needs source code the organisation controls. This is not recorded as in-house custom code. [R14: refactor -4]
- Data sensitivity is high. That does not stop a move, but it needs a data protection review, region and residency checks and tighter access design first. [R21: retain +1]

Next steps: Complete a data protection review and confirm region, residency and access controls before cutover.

### APP019 Shop floor controller gateway

Disposition: **retain** (score 9, runner-up repurchase 3, confidence high).

- The description points to equipment or response times tied to a physical site (machine control, scanners, label printing or similar). These are usually kept near the site, or moved only after a network and latency test. [R03: rehost -1, retain +4]
- The vendor does not support this application in the cloud. Running it there anyway risks losing vendor support, so the choices are to keep it, replace it, or rebuild it. [R04: rehost -3, replatform -3, refactor +1, repurchase +3, retain +3]
- Business criticality is 5. A critical application favours the route with the least change, and it is not a retirement candidate. [R13: rehost +1, refactor -2, repurchase -1, retire -4]
- Refactoring needs source code the organisation controls. This is not recorded as in-house custom code. [R14: refactor -4]
- The licence terms (oem) may not allow the software to run on shared cloud hosts. [R22: rehost -2, replatform -2, repurchase +1, retain +2]

Next steps: Measure round-trip latency and loss to the equipment before deciding to move it. Get the vendor position in writing and ask what route they offer (hosted, SaaS or a newer version). Read the licence with the vendor: some licences tied to hardware or a dongle cannot move.

### APP020 Manufacturing execution system

Disposition: **retain** (score 4, runner-up rehost 3, confidence low).

- The description points to equipment or response times tied to a physical site (machine control, scanners, label printing or similar). These are usually kept near the site, or moved only after a network and latency test. [R03: rehost -1, retain +4]
- Supported in the cloud, which keeps the lower-change routes open. [R07: rehost +1, replatform +1]
- Support ends on 2027-01-12, within the next 12 months. Plan the remediation as part of the move rather than after it. [R09: replatform +1, repurchase +1]
- Business criticality is 5. A critical application favours the route with the least change, and it is not a retirement candidate. [R13: rehost +1, refactor -2, repurchase -1, retire -4]
- Refactoring needs source code the organisation controls. This is not recorded as in-house custom code. [R14: refactor -4]

Next steps: Measure round-trip latency and loss to the equipment before deciding to move it.

### APP021 Furnace scheduling (legacy)

Disposition: **retain** (score 5, runner-up repurchase 5, confidence low).

- The description points to equipment or response times tied to a physical site (machine control, scanners, label printing or similar). These are usually kept near the site, or moved only after a network and latency test. [R03: rehost -1, retain +4]
- The vendor does not support this application in the cloud. Running it there anyway risks losing vendor support, so the choices are to keep it, replace it, or rebuild it. [R04: rehost -3, replatform -3, refactor +1, repurchase +3, retain +3]
- Support for the operating system or product ended on 2020-01-14. Staying as it is is not a durable answer. Moving the machine unchanged only changes where the risk sits, so the platform should change or the application should be replaced or retired. [R08: replatform +3, refactor +1, repurchase +2, retire +1, retain -2]
- Refactoring needs source code the organisation controls. This is not recorded as in-house custom code. [R14: refactor -4]
- Two dispositions scored the same, so the tie was broken by the configured order. Treat retain and repurchase as equally open.

Next steps: Measure round-trip latency and loss to the equipment before deciding to move it. Get the vendor position in writing and ask what route they offer (hosted, SaaS or a newer version). If a stopgap is unavoidable, check Microsoft's current terms for Extended Security Updates and record a dated exit.

### APP022 Quality management

Disposition: **repurchase** (score 5, runner-up rehost 3, confidence medium).

- Supported in the cloud, which keeps the lower-change routes open. [R07: rehost +1, replatform +1]
- Support ends on 2027-01-12, within the next 12 months. Plan the remediation as part of the move rather than after it. [R09: replatform +1, repurchase +1]
- Refactoring needs source code the organisation controls. This is not recorded as in-house custom code. [R14: refactor -4]
- The notes say a SaaS or hosted version of the product exists, which makes repurchase a real option. [R15: repurchase +4]

### APP023 Maintenance management

Disposition: **rehost** (score 3, runner-up replatform 1, confidence medium).

- Supported in the cloud, which keeps the lower-change routes open. [R07: rehost +1, replatform +1]
- Refactoring needs source code the organisation controls. This is not recorded as in-house custom code. [R14: refactor -4]

### APP024 CAD licence server

Disposition: **retain** (score 2, runner-up rehost 1, confidence low).

- Supported in the cloud, which keeps the lower-change routes open. [R07: rehost +1, replatform +1]
- Refactoring needs source code the organisation controls. This is not recorded as in-house custom code. [R14: refactor -4]
- The licence terms (perpetual, hardware dongle) may not allow the software to run on shared cloud hosts. [R22: rehost -2, replatform -2, repurchase +1, retain +2]

Next steps: Read the licence with the vendor: some licences tied to hardware or a dongle cannot move.

### APP025 Costing database

Disposition: **rehost** (score 4, runner-up retire 2, confidence medium).

- Supported in the cloud, which keeps the lower-change routes open. [R07: rehost +1, replatform +1]
- Nobody changes it, few people use it and it is not critical. [R12: retire +2]
- Stable in-house code rarely repays the cost of refactoring. Move it first and revisit once it is running in Azure. [R17: rehost +1, refactor -2]

### APP026 Warehouse management system

Disposition: **rehost** (score 4, runner-up replatform 1, confidence medium).

- Supported in the cloud, which keeps the lower-change routes open. [R07: rehost +1, replatform +1]
- Business criticality is 5. A critical application favours the route with the least change, and it is not a retirement candidate. [R13: rehost +1, refactor -2, repurchase -1, retire -4]
- Refactoring needs source code the organisation controls. This is not recorded as in-house custom code. [R14: refactor -4]
- 5 other applications depend on it, so a change in behaviour ripples out. Prefer a route that keeps interfaces the same. [R23: refactor -1, repurchase -1]

### APP027 Transport management system

Disposition: **rehost** (score 4, runner-up replatform 1, confidence medium).

- Supported in the cloud, which keeps the lower-change routes open. [R07: rehost +1, replatform +1]
- Business criticality is 4. A critical application favours the route with the least change, and it is not a retirement candidate. [R13: rehost +1, refactor -2, repurchase -1, retire -4]
- Refactoring needs source code the organisation controls. This is not recorded as in-house custom code. [R14: refactor -4]

### APP028 Handheld scanner service

Disposition: **retain** (score 4, runner-up rehost 3, confidence low).

- The description points to equipment or response times tied to a physical site (machine control, scanners, label printing or similar). These are usually kept near the site, or moved only after a network and latency test. [R03: rehost -1, retain +4]
- Supported in the cloud, which keeps the lower-change routes open. [R07: rehost +1, replatform +1]
- Support ends on 2027-01-12, within the next 12 months. Plan the remediation as part of the move rather than after it. [R09: replatform +1, repurchase +1]
- Business criticality is 4. A critical application favours the route with the least change, and it is not a retirement candidate. [R13: rehost +1, refactor -2, repurchase -1, retire -4]
- Refactoring needs source code the organisation controls. This is not recorded as in-house custom code. [R14: refactor -4]

Next steps: Measure round-trip latency and loss to the equipment before deciding to move it.

### APP029 Carrier label printing

Disposition: **replatform** (score 4, runner-up rehost 2, confidence medium).

- The description points to equipment or response times tied to a physical site (machine control, scanners, label printing or similar). These are usually kept near the site, or moved only after a network and latency test. [R03: rehost -1, retain +4]
- Supported in the cloud, which keeps the lower-change routes open. [R07: rehost +1, replatform +1]
- Support for the operating system or product ended on 2023-10-10. Staying as it is is not a durable answer. Moving the machine unchanged only changes where the risk sits, so the platform should change or the application should be replaced or retired. [R08: replatform +3, refactor +1, repurchase +2, retire +1, retain -2]
- Refactoring needs source code the organisation controls. This is not recorded as in-house custom code. [R14: refactor -4]

Next steps: Measure round-trip latency and loss to the equipment before deciding to move it. If a stopgap is unavoidable, check Microsoft's current terms for Extended Security Updates and record a dated exit.

### APP030 Customer portal and order entry

Disposition: **refactor** (score 6, runner-up replatform 5, confidence low).

- Supported in the cloud, which keeps the lower-change routes open. [R07: rehost +1, replatform +1]
- Support ends on 2027-01-12, within the next 12 months. Plan the remediation as part of the move rather than after it. [R09: replatform +1, repurchase +1]
- In-house code that changes often gains from modernisation, and the team is already working in it. Moving to a managed platform is the usual first step. [R16: replatform +3, refactor +2]
- The notes describe limits in how the in-house application is built (for example scaling or accumulated technical debt), which is what refactoring addresses. [R24: refactor +4]

Next steps: Confirm the problem with the owner and size the refactor separately. Avoid doing it during the move itself.

### APP031 Supplier portal

Disposition: **replatform** (score 4, runner-up rehost 3, confidence low).

- Supported in the cloud, which keeps the lower-change routes open. [R07: rehost +1, replatform +1]
- Support for the operating system or product ended on 2023-10-10. Staying as it is is not a durable answer. Moving the machine unchanged only changes where the risk sits, so the platform should change or the application should be replaced or retired. [R08: replatform +3, refactor +1, repurchase +2, retire +1, retain -2]

Next steps: If a stopgap is unavoidable, check Microsoft's current terms for Extended Security Updates and record a dated exit.

### APP032 Pricing engine

Disposition: **rehost** (score 4, runner-up replatform 2, confidence medium).

- Supported in the cloud, which keeps the lower-change routes open. [R07: rehost +1, replatform +1]
- Support ends on 2027-01-12, within the next 12 months. Plan the remediation as part of the move rather than after it. [R09: replatform +1, repurchase +1]
- Business criticality is 4. A critical application favours the route with the least change, and it is not a retirement candidate. [R13: rehost +1, refactor -2, repurchase -1, retire -4]

### APP033 Contracts and rebates

Disposition: **rehost** (score 4, runner-up replatform 2, confidence medium).

- Supported in the cloud, which keeps the lower-change routes open. [R07: rehost +1, replatform +1]
- Support ends on 2027-01-12, within the next 12 months. Plan the remediation as part of the move rather than after it. [R09: replatform +1, repurchase +1]
- Stable in-house code rarely repays the cost of refactoring. Move it first and revisit once it is running in Azure. [R17: rehost +1, refactor -2]

### APP034 Customer master data service

Disposition: **rehost** (score 4, runner-up replatform 1, confidence medium).

- Supported in the cloud, which keeps the lower-change routes open. [R07: rehost +1, replatform +1]
- Business criticality is 4. A critical application favours the route with the least change, and it is not a retirement candidate. [R13: rehost +1, refactor -2, repurchase -1, retire -4]
- Data sensitivity is high. That does not stop a move, but it needs a data protection review, region and residency checks and tighter access design first. [R21: retain +1]

Next steps: Complete a data protection review and confirm region, residency and access controls before cutover.

### APP035 Demand planning

Disposition: **rehost** (score 1, runner-up retain 1, confidence low).

- Vendor support in the cloud has not been confirmed. The score is held back until it is, because moving an application on an assumption is how migrations fail. [R05: rehost -1, replatform -1, retain +1]
- Support ends on 2027-01-12, within the next 12 months. Plan the remediation as part of the move rather than after it. [R09: replatform +1, repurchase +1]
- Refactoring needs source code the organisation controls. This is not recorded as in-house custom code. [R14: refactor -4]
- Two dispositions scored the same, so the tie was broken by the configured order. Treat rehost and retain as equally open.

Next steps: Ask the vendor in writing whether the product is supported on Azure, on which versions, and under what licence terms.

### APP036 Business intelligence and reporting

Disposition: **replatform** (score 4, runner-up rehost 3, confidence low).

- Supported in the cloud, which keeps the lower-change routes open. [R07: rehost +1, replatform +1]
- Refactoring needs source code the organisation controls. This is not recorded as in-house custom code. [R14: refactor -4]
- A database often benefits from a managed service, which removes patching and backup work. Check engine version and feature compatibility first. [R18: replatform +3]
- Data sensitivity is high. That does not stop a move, but it needs a data protection review, region and residency checks and tighter access design first. [R21: retain +1]

Next steps: Complete a data protection review and confirm region, residency and access controls before cutover.

### APP037 Credit control

Disposition: **replatform** (score 2, runner-up repurchase 2, confidence low).

- Vendor support in the cloud has not been confirmed. The score is held back until it is, because moving an application on an assumption is how migrations fail. [R05: rehost -1, replatform -1, retain +1]
- Support for the operating system or product ended on 2023-10-10. Staying as it is is not a durable answer. Moving the machine unchanged only changes where the risk sits, so the platform should change or the application should be replaced or retired. [R08: replatform +3, refactor +1, repurchase +2, retire +1, retain -2]
- Refactoring needs source code the organisation controls. This is not recorded as in-house custom code. [R14: refactor -4]
- Two dispositions scored the same, so the tie was broken by the configured order. Treat replatform and repurchase as equally open.

Next steps: Ask the vendor in writing whether the product is supported on Azure, on which versions, and under what licence terms. If a stopgap is unavoidable, check Microsoft's current terms for Extended Security Updates and record a dated exit.

### APP038 Time and attendance

Disposition: **rehost** (score 3, runner-up replatform 2, confidence low).

- Supported in the cloud, which keeps the lower-change routes open. [R07: rehost +1, replatform +1]
- Support ends on 2027-01-12, within the next 12 months. Plan the remediation as part of the move rather than after it. [R09: replatform +1, repurchase +1]
- Refactoring needs source code the organisation controls. This is not recorded as in-house custom code. [R14: refactor -4]
- Data sensitivity is restricted. That does not stop a move, but it needs a data protection review, region and residency checks and tighter access design first. [R21: retain +1]

Next steps: Complete a data protection review and confirm region, residency and access controls before cutover.

### APP039 Old intranet

Disposition: **retire** (score 12, runner-up repurchase 5, confidence high).

- The vendor does not support this application in the cloud. Running it there anyway risks losing vendor support, so the choices are to keep it, replace it, or rebuild it. [R04: rehost -3, replatform -3, refactor +1, repurchase +3, retain +3]
- Support for the operating system or product ended on 2020-01-14. Staying as it is is not a durable answer. Moving the machine unchanged only changes where the risk sits, so the platform should change or the application should be replaced or retired. [R08: replatform +3, refactor +1, repurchase +2, retire +1, retain -2]
- Only 0 user(s) and business criticality 1. Low use and low criticality make this a retirement candidate. [R10: retire +5]
- The notes suggest the application is duplicated, superseded or no longer used. [R11: retire +4]
- Nobody changes it, few people use it and it is not critical. [R12: retire +2]
- Stable in-house code rarely repays the cost of refactoring. Move it first and revisit once it is running in Azure. [R17: rehost +1, refactor -2]

Next steps: Confirm with the owner that nobody needs the function, and agree what happens to the data (archive or delete). Confirm with the owner and check for hidden dependants before retiring.

### APP040 Customer relationship management

Disposition: **retain** (decided by rule, confidence high).

- Already delivered as SaaS, so there is nothing to migrate. It is left out of the waves and out of the cost comparison. Check that its integrations still work after the apps around it move. [R01: decides: retain]
- Supported in the cloud, which keeps the lower-change routes open. [R07: rehost +1, replatform +1]
- Business criticality is 4. A critical application favours the route with the least change, and it is not a retirement candidate. [R13: rehost +1, refactor -2, repurchase -1, retire -4]
- Refactoring needs source code the organisation controls. This is not recorded as in-house custom code. [R14: refactor -4]

### APP041 Email and collaboration

Disposition: **retain** (decided by rule, confidence high).

- Already delivered as SaaS, so there is nothing to migrate. It is left out of the waves and out of the cost comparison. Check that its integrations still work after the apps around it move. [R01: decides: retain]
- Supported in the cloud, which keeps the lower-change routes open. [R07: rehost +1, replatform +1]
- Business criticality is 5. A critical application favours the route with the least change, and it is not a retirement candidate. [R13: rehost +1, refactor -2, repurchase -1, retire -4]
- Refactoring needs source code the organisation controls. This is not recorded as in-house custom code. [R14: refactor -4]
- Data sensitivity is high. That does not stop a move, but it needs a data protection review, region and residency checks and tighter access design first. [R21: retain +1]

### APP042 Public website

Disposition: **rehost** (score 3, runner-up replatform 1, confidence medium).

- Supported in the cloud, which keeps the lower-change routes open. [R07: rehost +1, replatform +1]
