# Sources and verification

Facts about Microsoft guidance and product names were checked on **11 November 2026** against Microsoft Learn and Microsoft lifecycle pages, fetched at that date. The text of those pages is not reproduced here. Everything is paraphrased. Pages carry their own "last updated" dates, quoted below where the page displayed one. Microsoft changes names and guidance often, so check the current pages before relying on any detail.

## What was checked

| Topic | What this repository says | Source (Microsoft Learn unless stated) | Page's own date |
|---|---|---|---|
| Cloud Adoption Framework phases | Seven: Strategy, Plan, Ready, Adopt, Govern, Secure, Manage. Adopt covers migrating, modernising and building workloads | Cloud Adoption Framework overview | 2026-09-04 |
| Azure landing zone design areas | Eight: Azure billing and tenant; Identity and access management; Resource organization; Network topology and connectivity; Security; Management; Governance; Platform automation and DevOps. The task for this repository listed seven (without platform automation and DevOps), so the checklist includes all eight | Landing zone design areas | 2025-12-19 |
| Landing zone structure | A platform landing zone plus workload landing zones; Microsoft provides accelerators and also allows a custom build. Links on that page still use the earlier "enterprise-scale" path, which suggests that was the earlier name (an inference, not stated on the page) | Azure landing zone overview | 2026-10-01 |
| Migration strategies | Microsoft lists eight: rehost, replatform, refactor, rearchitect, retire, replace, rebuild, retain. This tool uses six and maps them in [six-rs.md](six-rs.md) | Cloud rationalization (5 Rs) page, and "Migrate to Azure" page | 2025-07-25 and 2026-04-23 |
| Other providers' lists | AWS Prescriptive Guidance lists seven (retire, retain, rehost, relocate, repurchase, replatform, refactor or re-architect) and advises large migrations to favour rehost, relocate, replatform and retire, modernising afterwards | AWS Prescriptive Guidance, large migrations guide (no date shown) | not shown |
| Migration journey | The CAF "Migrate" content describes five steps: plan, prepare workloads, execute, optimise, decommission the source. The Azure migration overview describes plan, prepare, execute, evaluate, decommission. The wording differs slightly between pages | CAF Migrate overview, "Migrate to Azure" | 2025-08-01 and 2026-04-23 |
| Wave planning guidance | Group by dependency, start with simpler and lower risk workloads, non-production before production, schedule critical systems after the team has proved itself, include representative complex workloads early, avoid business-critical periods, plan the next wave in detail only, size by complexity and team capacity (no numeric limit is given), review at milestones | CAF migration wave planning | 2025-08-01 |
| Workload assessment topics | Architecture, performance and usage, security and identity, compatibility and remediation, dependencies, compliance and operations, application code, databases, risk | CAF assess workloads for cloud migration | 2025-12-10 |
| Azure Migrate | A free service (as described on the page) covering discovery, assessment (readiness, right-sizing, cost estimates, dependency analysis), a business case comparing on premises and Azure cost, migration, and modernisation. Covers servers, databases, web apps and offline data transfer. Tools include Discovery and Assessment, Migrate and Modernize, Data Migration Assistant, Database Migration Service, App Service Migration Assistant and Data Box. An appliance (recommended) or a Collector can discover. Movere is marked retired | Azure Migrate overview | 2026-05-19 |
| Security design area | Names Microsoft Entra ID, Conditional Access, Privileged Identity Management, Microsoft Defender for Cloud, Azure Policy, Log Analytics and Azure Monitor Logs, among others | Landing zone security design area | 2025-12-19 |
| Network design area | Names Virtual WAN, ExpressRoute, Azure Firewall, private DNS zones | Landing zone network design area | 2025-12-19 |
| Management design area | Operations baseline: inventory and visibility, protect and recover (backup and disaster recovery, with recovery time and point objectives captured early), operational compliance (patching, drift, cost) | Landing zone management design area | 2026-06-01 |
| End-of-support dates used in the example inventory | Windows Server 2016 extended support ends 12 January 2027. SQL Server 2016 extended support ended in July 2026. Windows Server 2019, 2012 R2 and 2008 R2 and SQL Server 2019 dates match the lifecycle pages to within a day (the pages display a time zone conversion) | Microsoft lifecycle pages for each product, and the Windows Server extended security updates page | not applicable |

## What was not verified

- **Product names not on the pages fetched.** Azure Key Vault, Azure Backup, Azure Site Recovery, Microsoft Cost Management and Azure Hybrid Benefit are named from general knowledge (Azure Hybrid Benefit is mentioned in the assessment page). Check current names.
- **The history of the "Rs".** This repository does not claim who first used the term. The six used are the common core, and Microsoft and AWS each list more.
- **No Azure tenant was used.** Nothing here was run against Azure, Azure Migrate or a real inventory export. Azure Migrate's output formats are not read by this tool.
- **No prices.** None were looked up or used. Cost inputs are supplied by the user.
- **Whether any particular Azure service supports a particular application.** That is for the vendor and for Azure Migrate's assessment.
- **Extended Security Updates terms.** The Windows Server lifecycle page lists extended security update dates, and Microsoft's page offers extended security updates for Windows Server and SQL Server in Azure for a limited period. The terms, eligibility and cost were not checked. The tool only tells the reader to check them.
- **Wave size, criticality thresholds, scores and points.** These are design choices in this tool, not Microsoft guidance. Microsoft's page gives no numeric wave size.

## Why this matters

A planning tool that states confident facts it has not checked is worse than no tool. Where a claim here is a judgement (a score, a threshold, a rule of thumb) the documents say so, and the rules are in a file you can edit.
